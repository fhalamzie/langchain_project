"""
Data Sampler for WINCASA Database

Extracts representative data samples from high-priority tables to enrich
the global context with real patterns and data formats.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import fdb

from fdb_direct_interface import FDBDirectInterface


class WincasaDataSampler:
    """Extract meaningful data samples from WINCASA database tables"""

    def __init__(self, db_path: str = "WINCASA2022.FDB"):
        self.db_path = db_path
        self.fdb_interface = None

        # High-priority tables for sampling based on schema analysis
        self.priority_tables = {
            "core_entities": [
                "BEWOHNER",
                "EIGENTUEMER",
                "OBJEKTE",
                "WOHNUNG",
                "BEWADR",
                "EIGADR",
                "KONTEN",
            ],
            "financial": ["BUCHUNG", "SOLLSTELLUNG", "BANKEN", "VORAUSZ"],
            "management": ["VERWALTER", "SEVERTRAG", "NACHWEIS", "BESCHLUSS"],
            "operational": ["HDBUCH", "ZTERMIN", "VEREIG", "LIEFERAN"],
        }

    def connect(self):
        """Establish database connection"""
        try:
            self.fdb_interface = FDBDirectInterface(dsn=self.db_path)
            print(f"✅ Connected to database via FDBDirectInterface")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.fdb_interface:
            # FDBDirectInterface doesn't have a disconnect method - connections are pooled
            self.fdb_interface = None
            print("✅ Database connection closed")

    def get_table_sample(self, table_name: str, limit: int = 30) -> Dict[str, Any]:
        """
        Extract sample data from a table with metadata
        """
        if not self.fdb_interface:
            raise ValueError("Database not connected")

        sample_info = {
            "table_name": table_name,
            "sample_size": 0,
            "columns": [],
            "data_types": {},
            "sample_data": [],
            "patterns": {},
            "errors": [],
        }

        try:
            # Get table structure first
            schema_query = f"""
                SELECT r.RDB$FIELD_NAME, r.RDB$FIELD_SOURCE, f.RDB$FIELD_TYPE, f.RDB$FIELD_LENGTH
                FROM RDB$RELATION_FIELDS r
                LEFT JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                WHERE r.RDB$RELATION_NAME = '{table_name.upper()}'
                ORDER BY r.RDB$FIELD_POSITION
            """

            columns_result = self.fdb_interface.run_sql(schema_query)
            if not columns_result:
                sample_info["errors"].append(
                    f"Table {table_name} not found or no columns"
                )
                return sample_info

            # Extract column information
            column_names = []
            for col_info in columns_result:
                col_name = col_info[0].strip()
                field_type = col_info[2] if len(col_info) > 2 else None
                field_length = col_info[3] if len(col_info) > 3 else None

                column_names.append(col_name)
                sample_info["data_types"][col_name] = {
                    "firebird_type": field_type,
                    "length": field_length,
                }

            sample_info["columns"] = column_names

            # Get sample data
            columns_str = ", ".join(column_names)
            data_query = f"SELECT FIRST {limit} {columns_str} FROM {table_name}"

            rows = self.fdb_interface.run_sql(data_query)
            sample_info["sample_size"] = len(rows) if rows else 0

            # Convert to list of dictionaries for easier processing
            if rows:
                for row in rows:
                    row_dict = {}
                    for i, col_name in enumerate(column_names):
                        value = row[i] if i < len(row) else None
                        # Convert to JSON-serializable format
                        if value is not None:
                            if hasattr(value, "isoformat"):  # datetime objects
                                value = value.isoformat()
                            elif isinstance(value, (bytes, bytearray)):
                                value = str(value, "utf-8", errors="ignore")
                            elif hasattr(value, "__class__") and "Decimal" in str(
                                value.__class__
                            ):
                                value = float(value)  # Convert Decimal to float
                        row_dict[col_name] = value
                    sample_info["sample_data"].append(row_dict)

            # Analyze patterns
            sample_info["patterns"] = self._analyze_patterns(
                sample_info["sample_data"], column_names
            )

        except Exception as e:
            sample_info["errors"].append(f"Error sampling {table_name}: {str(e)}")

        return sample_info

    def _analyze_patterns(
        self, sample_data: List[Dict], columns: List[str]
    ) -> Dict[str, Any]:
        """Analyze data patterns in the sample"""
        patterns = {}

        if not sample_data:
            return patterns

        for col in columns:
            col_values = [
                row.get(col) for row in sample_data if row.get(col) is not None
            ]

            if not col_values:
                continue

            col_patterns = {
                "non_null_count": len(col_values),
                "unique_count": len(set(str(v) for v in col_values)),
                "sample_values": list(
                    set(str(v) for v in col_values[:10])
                ),  # First 10 unique values
            }

            # Detect common patterns
            if col.upper() in ["ONR", "OBJNR", "OBJEKTNR"]:
                col_patterns["pattern_type"] = "object_number"
            elif col.upper() in ["BEWNR", "BEWOHNERNR"]:
                col_patterns["pattern_type"] = "resident_number"
            elif col.upper() in ["EIGNR", "EIGENTUEMERNR"]:
                col_patterns["pattern_type"] = "owner_number"
            elif col.upper() in ["KNR", "KONTONR"]:
                col_patterns["pattern_type"] = "account_number"
            elif "STR" in col.upper() or "STRASSE" in col.upper():
                col_patterns["pattern_type"] = "street_address"
            elif "PLZ" in col.upper() or "POSTAL" in col.upper():
                col_patterns["pattern_type"] = "postal_code"
            elif "NAME" in col.upper():
                col_patterns["pattern_type"] = "name_field"
            elif "DATUM" in col.upper() or "DATE" in col.upper():
                col_patterns["pattern_type"] = "date_field"
            elif "BETRAG" in col.upper() or "AMOUNT" in col.upper():
                col_patterns["pattern_type"] = "amount_field"

            patterns[col] = col_patterns

        return patterns

    def sample_all_priority_tables(self, limit_per_table: int = 30) -> Dict[str, Any]:
        """Sample all priority tables and return comprehensive data structure"""
        all_samples = {
            "metadata": {
                "database": self.db_path,
                "sample_limit_per_table": limit_per_table,
                "categories": list(self.priority_tables.keys()),
            },
            "samples": {},
            "summary": {
                "total_tables_sampled": 0,
                "successful_samples": 0,
                "failed_samples": 0,
                "total_rows_sampled": 0,
            },
        }

        try:
            self.connect()

            for category, tables in self.priority_tables.items():
                print(f"\n📊 Sampling {category} tables...")
                category_samples = {}

                for table_name in tables:
                    print(f"  Sampling {table_name}...")
                    sample = self.get_table_sample(table_name, limit_per_table)
                    category_samples[table_name] = sample

                    all_samples["summary"]["total_tables_sampled"] += 1
                    if sample["errors"]:
                        all_samples["summary"]["failed_samples"] += 1
                        print(
                            f"    ⚠️  {len(sample['errors'])} errors: {sample['errors'][0][:100]}..."
                        )
                    else:
                        all_samples["summary"]["successful_samples"] += 1
                        all_samples["summary"]["total_rows_sampled"] += sample[
                            "sample_size"
                        ]
                        print(f"    ✅ {sample['sample_size']} rows sampled")

                all_samples["samples"][category] = category_samples

        finally:
            self.disconnect()

        return all_samples

    def save_samples_to_file(
        self, samples: Dict[str, Any], output_path: str = "output/data_samples.json"
    ):
        """Save samples to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)

        print(f"✅ Samples saved to {output_file}")

    def generate_context_summary(self, samples: Dict[str, Any]) -> str:
        """Generate a summary suitable for inclusion in LLM context"""
        summary_lines = []
        summary_lines.append("=== WINCASA DATABASE SAMPLE DATA PATTERNS ===")

        for category, category_samples in samples["samples"].items():
            summary_lines.append(f"\n{category.upper()} TABLES:")

            for table_name, sample in category_samples.items():
                if sample["errors"]:
                    continue

                summary_lines.append(
                    f"\n• {table_name} ({sample['sample_size']} sample rows):"
                )

                # Key patterns
                key_patterns = []
                for col, pattern in sample["patterns"].items():
                    if pattern.get("pattern_type"):
                        key_patterns.append(f"{col}({pattern['pattern_type']})")

                if key_patterns:
                    summary_lines.append(f"  Key fields: {', '.join(key_patterns[:5])}")

                # Sample values for important fields
                important_cols = [
                    "ONR",
                    "BEWNR",
                    "EIGNR",
                    "KNR",
                    "NAME",
                    "VORNAME",
                    "BSTR",
                    "BPLZORT",
                ]
                for col in important_cols:
                    if (
                        col in sample["patterns"]
                        and sample["patterns"][col]["sample_values"]
                    ):
                        values = sample["patterns"][col]["sample_values"][:3]
                        summary_lines.append(f"  {col} examples: {', '.join(values)}")

        summary_lines.append("\n=== END SAMPLE DATA PATTERNS ===")
        return "\n".join(summary_lines)


def main():
    """Main function to run data sampling"""
    sampler = WincasaDataSampler()

    print("🚀 Starting WINCASA data sampling...")
    samples = sampler.sample_all_priority_tables(limit_per_table=30)

    print(f"\n📈 SAMPLING SUMMARY:")
    print(f"  Total tables: {samples['summary']['total_tables_sampled']}")
    print(f"  Successful: {samples['summary']['successful_samples']}")
    print(f"  Failed: {samples['summary']['failed_samples']}")
    print(f"  Total rows: {samples['summary']['total_rows_sampled']}")

    # Save samples
    sampler.save_samples_to_file(samples)

    # Generate context summary
    context_summary = sampler.generate_context_summary(samples)

    # Save context summary
    with open("output/data_context_summary.txt", "w", encoding="utf-8") as f:
        f.write(context_summary)

    print("\n📝 Context summary:")
    print(
        context_summary[:1000] + "..."
        if len(context_summary) > 1000
        else context_summary
    )


if __name__ == "__main__":
    main()
