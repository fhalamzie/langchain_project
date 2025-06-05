#!/usr/bin/env python3
"""
TAG GEN (Generation) Module - Natural Language Response Formatting

Purpose: Convert raw SQL results into contextual German responses
with business terminology and proper formatting.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class GenerationResult:
    """Result of response generation process"""

    response: str
    query_type: str
    formatted_data: Optional[Dict] = None
    metadata: Optional[Dict] = None


class ResponseGenerator:
    """
    TAG GEN implementation - formats SQL results into natural language

    Features:
    - Query-type-specific response formatting
    - German language support with business terminology
    - Context-aware error messages
    - Structured data presentation
    """

    # German response templates per query type
    RESPONSE_TEMPLATES = {
        "address_lookup": {
            "single_result": "In der {address} wohnt: {name}",
            "multiple_results": (
                "In der {address} wohnen {count} Personen:\n{residents}"
            ),
            "no_results": (
                "Es wurden keine Bewohner für die Adresse '{address}' gefunden."
            ),
            "partial_address": (
                "Für '{query}' wurden {count} Bewohner gefunden:\n{residents}"
            ),
        },
        "owner_lookup": {
            "single_result": "Eigentümer: {name}",
            "multiple_results": "Es gibt {count} Eigentümer:\n{owners}",
            "no_results": "Es wurden keine Eigentümer gefunden.",
            "city_filter": "Eigentümer in {city}: {count} gefunden:\n{owners}",
        },
        "property_queries": {
            "count_result": "Es gibt insgesamt {count} Wohnungen.",
            "apartment_list": "Wohnungen:\n{apartments}",
            "no_results": "Keine Wohnungen gefunden.",
            "building_info": "Objekt {building}: {count} Wohnungen",
        },
        "financial_queries": {
            "average_result": "Die durchschnittliche Miete beträgt {amount} Euro.",
            "total_result": "Gesamtbetrag: {amount} Euro.",
            "no_results": "Keine Finanzdaten verfügbar.",
            "calculation_error": "Berechnung konnte nicht durchgeführt werden.",
        },
        "business_entity_queries": {
            "relationship_result": "Gefunden: {count} Datensätze mit Beziehungen",
            "complex_result": "Ergebnis der komplexen Abfrage:\n{data}",
            "no_results": "Keine Ergebnisse für die komplexe Abfrage gefunden.",
        },
    }

    # Business terminology mappings
    BUSINESS_TERMS = {
        "BWO": "Bewohner-ID",
        "ENR": "Eigentümer-ID",
        "ONR": "Objekt-ID",
        "WNR": "Wohnungs-ID",
        "KNR": "Konto-ID",
        "BNAME": "Nachname",
        "BVNAME": "Vorname",
        "ENAME": "Nachname (Eigentümer)",
        "EVNAME": "Vorname (Eigentümer)",
        "BSTR": "Straße",
        "BPLZORT": "PLZ und Ort",
        "OBEZEICHNUNG": "Objektbezeichnung",
        "WBEZEICHNUNG": "Wohnungsbezeichnung",
        "BBETRAG": "Betrag",
        "BDATUM": "Datum",
    }

    def __init__(self):
        """Initialize response generator"""
        pass

    def generate(
        self,
        sql_results: List[Dict],
        query_type: str,
        original_query: str,
        synthesis_info: Optional[Dict] = None,
    ) -> GenerationResult:
        """
        Main generation method - converts SQL results to natural language

        Args:
            sql_results: Raw SQL query results
            query_type: Type of query from TAG SYN
            original_query: Original user query
            synthesis_info: Additional context from synthesis

        Returns:
            GenerationResult with formatted response
        """

        if not sql_results:
            return self._generate_empty_response(query_type, original_query)

        # Route to appropriate formatter based on query type
        formatter_map = {
            "address_lookup": self._format_address_lookup,
            "owner_lookup": self._format_owner_lookup,
            "property_queries": self._format_property_queries,
            "financial_queries": self._format_financial_queries,
            "business_entity_queries": self._format_business_entity_queries,
        }

        formatter = formatter_map.get(query_type, self._format_generic)

        try:
            response = formatter(sql_results, original_query, synthesis_info)

            return GenerationResult(
                response=response,
                query_type=query_type,
                formatted_data=self._extract_formatted_data(sql_results),
                metadata={
                    "result_count": len(sql_results),
                    "query_type": query_type,
                    "has_results": len(sql_results) > 0,
                },
            )

        except Exception as e:
            return GenerationResult(
                response=f"Fehler bei der Ergebnisformatierung: {str(e)}",
                query_type=query_type,
                metadata={"error": str(e)},
            )

    def _format_address_lookup(
        self, results: List[Dict], query: str, synthesis_info: Optional[Dict] = None
    ) -> str:
        """Format address lookup results"""

        if len(results) == 1:
            result = results[0]
            name = self._format_name(result)
            address = self._format_address(result)

            template = self.RESPONSE_TEMPLATES["address_lookup"]["single_result"]
            return template.format(address=address, name=name)

        else:
            residents = []
            for result in results:
                name = self._format_name(result)
                address = self._format_address(result)
                residents.append(f"- {name} ({address})")

            residents_text = "\n".join(residents)

            # Extract address from synthesis info if available
            address_from_query = self._extract_address_from_query(query)

            if address_from_query:
                template = self.RESPONSE_TEMPLATES["address_lookup"]["multiple_results"]
                return template.format(
                    address=address_from_query,
                    count=len(results),
                    residents=residents_text,
                )
            else:
                template = self.RESPONSE_TEMPLATES["address_lookup"]["partial_address"]
                return template.format(
                    query=query, count=len(results), residents=residents_text
                )

    def _format_owner_lookup(
        self, results: List[Dict], query: str, synthesis_info: Optional[Dict] = None
    ) -> str:
        """Format owner lookup results"""

        if len(results) == 1:
            result = results[0]
            name = self._format_owner_name(result)
            template = self.RESPONSE_TEMPLATES["owner_lookup"]["single_result"]
            return template.format(name=name)

        else:
            owners = []
            for result in results:
                name = self._format_owner_name(result)
                # Include address if available
                if "ESTR" in result and "EPLZORT" in result:
                    address = f"{result.get('ESTR', '')}, {result.get('EPLZORT', '')}"
                    owners.append(f"- {name} ({address})")
                else:
                    owners.append(f"- {name}")

            owners_text = "\n".join(owners)

            # Check if city filter was applied
            city_match = re.search(r"\b(köln|essen|duisburg)\b", query.lower())
            if city_match:
                city = city_match.group(1).capitalize()
                template = self.RESPONSE_TEMPLATES["owner_lookup"]["city_filter"]
                return template.format(
                    city=city, count=len(results), owners=owners_text
                )
            else:
                template = self.RESPONSE_TEMPLATES["owner_lookup"]["multiple_results"]
                return template.format(count=len(results), owners=owners_text)

    def _format_property_queries(
        self, results: List[Dict], query: str, synthesis_info: Optional[Dict] = None
    ) -> str:
        """Format property query results"""

        # Handle count queries
        if len(results) == 1 and len(results[0]) == 1:
            # Likely a COUNT(*) query
            count_value = list(results[0].values())[0]
            if isinstance(count_value, (int, float)):
                template = self.RESPONSE_TEMPLATES["property_queries"]["count_result"]
                return template.format(count=int(count_value))

        # Handle apartment listings
        apartments = []
        for result in results:
            if "WBEZEICHNUNG" in result:
                designation = result["WBEZEICHNUNG"]
                if "ONR" in result:
                    apartments.append(f"- {designation} (Objekt {result['ONR']})")
                else:
                    apartments.append(f"- {designation}")
            elif "WNR" in result:
                apartments.append(f"- Wohnung ID {result['WNR']}")

        if apartments:
            apartments_text = "\n".join(apartments)
            template = self.RESPONSE_TEMPLATES["property_queries"]["apartment_list"]
            return template.format(apartments=apartments_text)

        # Generic property result
        return f"Gefunden: {len(results)} Immobilien-Datensätze"

    def _format_financial_queries(
        self, results: List[Dict], query: str, synthesis_info: Optional[Dict] = None
    ) -> str:
        """Format financial query results"""

        # Handle average calculations
        if len(results) == 1 and len(results[0]) == 1:
            value = list(results[0].values())[0]
            if isinstance(value, (int, float)):
                if "durchschnitt" in query.lower():
                    template = self.RESPONSE_TEMPLATES["financial_queries"][
                        "average_result"
                    ]
                    return template.format(amount=f"{value:.2f}")
                else:
                    template = self.RESPONSE_TEMPLATES["financial_queries"][
                        "total_result"
                    ]
                    return template.format(amount=f"{value:.2f}")

        # Handle multiple financial records
        return f"Finanzdaten: {len(results)} Einträge gefunden"

    def _format_business_entity_queries(
        self, results: List[Dict], query: str, synthesis_info: Optional[Dict] = None
    ) -> str:
        """Format complex business entity query results"""

        if len(results) <= 5:
            # Format detailed results for small result sets
            formatted_results = []
            for result in results:
                formatted_result = self._format_business_entity_row(result)
                formatted_results.append(formatted_result)

            data_text = "\n".join(formatted_results)
            template = self.RESPONSE_TEMPLATES["business_entity_queries"][
                "complex_result"
            ]
            return template.format(data=data_text)
        else:
            # Summary for large result sets
            template = self.RESPONSE_TEMPLATES["business_entity_queries"][
                "relationship_result"
            ]
            return template.format(count=len(results))

    def _format_generic(
        self, results: List[Dict], query: str, synthesis_info: Optional[Dict] = None
    ) -> str:
        """Generic formatter for unhandled query types"""

        if len(results) == 1:
            return f"Ergebnis: {self._format_single_row(results[0])}"
        else:
            return f"Gefunden: {len(results)} Datensätze"

    def _generate_empty_response(self, query_type: str, query: str) -> GenerationResult:
        """Generate response for empty results"""

        templates = self.RESPONSE_TEMPLATES.get(query_type, {})
        no_results_template = templates.get("no_results", "Keine Ergebnisse gefunden.")

        # Customize based on query content
        if query_type == "address_lookup":
            address = self._extract_address_from_query(query)
            if address:
                response = templates["no_results"].format(address=address)
            else:
                response = f"Es wurden keine Bewohner für '{query}' gefunden."
        else:
            response = no_results_template

        return GenerationResult(
            response=response,
            query_type=query_type,
            metadata={"result_count": 0, "has_results": False},
        )

    def _format_name(self, result: Dict) -> str:
        """Format person name from result"""

        first_name = result.get("BVNAME", result.get("EVNAME", ""))
        last_name = result.get("BNAME", result.get("ENAME", ""))

        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif last_name:
            return last_name
        elif first_name:
            return first_name
        else:
            return "Unbekannt"

    def _format_owner_name(self, result: Dict) -> str:
        """Format owner name from result"""

        first_name = result.get("EVNAME", "")
        last_name = result.get("ENAME", "")

        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif last_name:
            return last_name
        else:
            return "Unbekannt"

    def _format_address(self, result: Dict) -> str:
        """Format address from result"""

        street = result.get("BSTR", result.get("ESTR", ""))
        plz_ort = result.get("BPLZORT", result.get("EPLZORT", ""))

        if street and plz_ort:
            return f"{street}, {plz_ort}"
        elif street:
            return street
        elif plz_ort:
            return plz_ort
        else:
            return "Adresse unbekannt"

    def _extract_address_from_query(self, query: str) -> Optional[str]:
        """Extract address from original query"""

        # Look for street patterns
        street_match = re.search(
            r"\b(\w+(?:str\.?|straße|weg|platz))\s*(\d+)?", query, re.IGNORECASE
        )
        postal_match = re.search(r"\b(\d{5})\s*(\w+)", query)

        parts = []
        if street_match:
            street = street_match.group(1)
            number = street_match.group(2)
            if number:
                parts.append(f"{street} {number}")
            else:
                parts.append(street)

        if postal_match:
            postal = postal_match.group(1)
            city = postal_match.group(2)
            parts.append(f"{postal} {city}")

        return ", ".join(parts) if parts else None

    def _format_business_entity_row(self, result: Dict) -> str:
        """Format a single business entity result row"""

        # Pick the most relevant fields
        relevant_fields = []

        # Names
        if "BNAME" in result:
            name = self._format_name(result)
            relevant_fields.append(f"Bewohner: {name}")

        if "ENAME" in result:
            owner_name = self._format_owner_name(result)
            relevant_fields.append(f"Eigentümer: {owner_name}")

        # Designations
        if "OBEZEICHNUNG" in result:
            relevant_fields.append(f"Objekt: {result['OBEZEICHNUNG']}")

        if "WBEZEICHNUNG" in result:
            relevant_fields.append(f"Wohnung: {result['WBEZEICHNUNG']}")

        return " | ".join(relevant_fields) if relevant_fields else str(result)

    def _format_single_row(self, result: Dict) -> str:
        """Format a single result row generically"""

        formatted_fields = []
        for key, value in result.items():
            if value is not None:
                # Translate technical field names to business terms
                field_name = self.BUSINESS_TERMS.get(key, key)
                formatted_fields.append(f"{field_name}: {value}")

        return " | ".join(formatted_fields)

    def _extract_formatted_data(self, results: List[Dict]) -> Dict:
        """Extract formatted data for potential API use"""

        return {
            "raw_results": results,
            "count": len(results),
            "has_data": len(results) > 0,
        }


def test_response_generator():
    """Test the response generator with sample data"""

    generator = ResponseGenerator()

    # Test cases with mock SQL results
    test_cases = [
        {
            "query": "Wer wohnt in der Marienstr. 26, 45307 Essen",
            "query_type": "address_lookup",
            "results": [
                {
                    "BNAME": "Müller",
                    "BVNAME": "Hans",
                    "BSTR": "Marienstraße 26",
                    "BPLZORT": "45307 Essen",
                }
            ],
        },
        {
            "query": "Wie viele Wohnungen gibt es insgesamt?",
            "query_type": "property_queries",
            "results": [{"COUNT": 517}],
        },
        {
            "query": "Alle Eigentümer aus Köln",
            "query_type": "owner_lookup",
            "results": [
                {
                    "ENAME": "Schmidt",
                    "EVNAME": "Peter",
                    "ESTR": "Kölner Str. 1",
                    "EPLZORT": "50667 Köln",
                },
                {
                    "ENAME": "Weber",
                    "EVNAME": "Maria",
                    "ESTR": "Domstraße 5",
                    "EPLZORT": "50667 Köln",
                },
            ],
        },
        {
            "query": "Durchschnittliche Miete in Essen",
            "query_type": "financial_queries",
            "results": [{"AVG": 650.50}],
        },
    ]

    print("📝 TESTING TAG GEN (Generation) Module")
    print("=" * 60)
    print("Goal: Convert SQL results to contextual German responses")
    print()

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['query']}")

        result = generator.generate(
            sql_results=test_case["results"],
            query_type=test_case["query_type"],
            original_query=test_case["query"],
        )

        print(f"  Response: {result.response}")
        print(f"  Type: {result.query_type}")
        print(f"  Metadata: {result.metadata}")
        print()


if __name__ == "__main__":
    test_response_generator()
