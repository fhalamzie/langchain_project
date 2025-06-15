#!/usr/bin/env python3
"""
JSON Exporter for Layer 4 queries using firebird-driver
Handles Decimal types properly and exports query results to JSON
Enhanced with UTF-8 support, streaming for large datasets, and parameterization
"""

import os
import json
import csv
from datetime import datetime, date, time
from decimal import Decimal
import firebird.driver
import logging
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('json_export.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load path configuration
import json as config_json
with open('config/sql_paths.json', 'r') as f:
    PATH_CONFIG = config_json.load(f)

LAYER4_PATH = PATH_CONFIG['sql_queries_dir']
EXPORT_PATH = PATH_CONFIG['json_exports_dir']

# Queries that need UTF-8 connection
UTF8_QUERIES = [
    '01_eigentuemer.sql',
    '02_mieter.sql',
    '03_aktuelle_mieter.sql',
    '04_alle_mieter.sql',
    '10_eigentuemer_konten.sql',
    '17_beschluesse.sql',
    '18_versammlungen.sql'
]

# Large queries that need special handling
LARGE_QUERIES = [
    '29_eigentuemer_zahlungshistorie.sql',
    '30_weg_zahlungsuebersicht.sql',
    '35_buchungskonten_uebersicht.sql'
]


class FirebirdJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Firebird data types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert Decimal to float, preserving precision
            return float(obj)
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        elif isinstance(obj, bytes):
            # Handle BLOB data
            try:
                return obj.decode('utf-8')
            except:
                return obj.decode('latin-1', errors='replace')
        return super().default(obj)


def get_connection(charset='ISO8859_1'):
    """Get database connection with specified charset"""
    return firebird.driver.connect(
        database=PATH_CONFIG['database_path'],
        user='SYSDBA',
        password='masterkey',
        charset=charset
    )


def clean_sql(sql_content):
    """Clean SQL content for execution"""
    sql_lines = []
    in_final_comment = False
    
    for line in sql_content.split('\n'):
        if line.strip().startswith('/*') and any(word in line for word in ['ERWARTETES', 'EXPECTED', 'PARAMETER']):
            in_final_comment = True
        if not in_final_comment:
            sql_lines.append(line)
    
    sql_query = '\n'.join(sql_lines).strip()
    
    # Remove any trailing semicolons
    while sql_query.endswith(';'):
        sql_query = sql_query[:-1].strip()
    
    return sql_query


def extract_metadata(sql_content):
    """Extract metadata from SQL comments"""
    metadata = {
        'description': '',
        'business_purpose': '',
        'main_tables': [],
        'usage': '',
        'optimizations': []
    }
    
    # Extract from initial comment block
    lines = sql_content.split('\n')
    in_comment = False
    comment_lines = []
    
    for line in lines:
        if line.strip().startswith('/*'):
            in_comment = True
        if in_comment:
            comment_lines.append(line)
        if '*/' in line and in_comment:
            break
    
    comment_text = '\n'.join(comment_lines)
    
    # Parse metadata
    if 'GESCHÄFTSZWECK:' in comment_text:
        metadata['business_purpose'] = comment_text.split('GESCHÄFTSZWECK:')[1].split('\n')[0].strip()
    elif 'BUSINESS PURPOSE:' in comment_text:
        metadata['business_purpose'] = comment_text.split('BUSINESS PURPOSE:')[1].split('\n')[0].strip()
    
    if 'HAUPTTABELLEN:' in comment_text:
        tables_section = comment_text.split('HAUPTTABELLEN:')[1].split('\n\n')[0]
        metadata['main_tables'] = [line.strip().split(':')[0].replace('-', '').strip() 
                                 for line in tables_section.split('\n') 
                                 if line.strip() and '-' in line]
    
    if 'OPTIMIERUNGEN:' in comment_text:
        opt_section = comment_text.split('OPTIMIERUNGEN:')[1].split('\n\n')[0]
        metadata['optimizations'] = [line.strip().replace('-', '').strip()
                                   for line in opt_section.split('\n')
                                   if line.strip() and '-' in line]
    
    return metadata


def export_large_query(sql_file, sql_query, charset='ISO8859_1'):
    """Export large query using streaming approach"""
    logger.info(f"Processing large query {sql_file} with streaming...")
    
    try:
        conn = get_connection(charset)
        cursor = conn.cursor()
        
        # Execute query
        start_time = datetime.now()
        cursor.execute(sql_query)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Create temporary file for streaming
        temp_file = os.path.join(EXPORT_PATH, f"{sql_file}.tmp")
        json_filename = sql_file.replace('.sql', '.json')
        json_path = os.path.join(EXPORT_PATH, json_filename)
        
        row_count = 0
        chunk_size = 1000
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write('{"query_info": ')
            
            # Write metadata
            query_info = {
                'file': sql_file,
                'generated': datetime.now().isoformat(),
                'driver': 'firebird-driver',
                'charset': charset,
                'streaming': True
            }
            json.dump(query_info, f, cls=FirebirdJSONEncoder)
            
            f.write(', "columns": ')
            json.dump(columns, f)
            
            f.write(', "data": [')
            
            # Stream data in chunks
            first_row = True
            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break
                
                for row in rows:
                    if not first_row:
                        f.write(',')
                    first_row = False
                    
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(columns):
                            row_dict[columns[i]] = value
                    
                    json.dump(row_dict, f, cls=FirebirdJSONEncoder)
                    row_count += 1
                
                if row_count % 10000 == 0:
                    logger.info(f"  Processed {row_count} rows...")
                
                # Safety limit to prevent runaway queries
                if row_count >= 100000:
                    logger.warning(f"  Row limit reached (100k), stopping export for safety")
                    break
            
            f.write('], "summary": ')
            
            # Write summary
            execution_time = (datetime.now() - start_time).total_seconds()
            summary = {
                'row_count': row_count,
                'execution_time_seconds': execution_time,
                'success': True,
                'error': None
            }
            json.dump(summary, f, cls=FirebirdJSONEncoder)
            f.write('}')
        
        # Rename temp file to final
        os.rename(temp_file, json_path)
        
        cursor.close()
        conn.close()
        
        logger.info(f"✓ Exported {row_count} rows to {json_filename} in {execution_time:.2f}s")
        return True, row_count
        
    except Exception as e:
        logger.error(f"✗ Failed to export {sql_file}: {str(e)}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return False, 0


def export_query_to_json(sql_file):
    """Export a single query result to JSON"""
    logger.info(f"Processing {sql_file}")
    
    try:
        # Read SQL file
        file_path = os.path.join(LAYER4_PATH, sql_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Extract metadata
        metadata = extract_metadata(sql_content)
        
        # Clean query
        sql_query = clean_sql(sql_content)
        
        # Determine charset
        charset = 'UTF8' if sql_file in UTF8_QUERIES else 'ISO8859_1'
        
        # Handle large queries differently
        if sql_file in LARGE_QUERIES:
            return export_large_query(sql_file, sql_query, charset)
        
        # Regular export for smaller queries
        conn = get_connection(charset)
        cursor = conn.cursor()
        
        start_time = datetime.now()
        cursor.execute(sql_query)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Fetch all results
        rows = cursor.fetchall()
        execution_time = (datetime.now() - start_time).total_seconds()
        
        cursor.close()
        conn.close()
        
        # Convert to list of dicts
        data = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(columns):
                    row_dict[columns[i]] = value
            data.append(row_dict)
        
        # Create export structure
        export_data = {
            'query_info': {
                'file': sql_file,
                'generated': datetime.now().isoformat(),
                'driver': 'firebird-driver',
                'charset': charset,
                'business_purpose': metadata['business_purpose'],
                'main_tables': metadata['main_tables'],
                'total_rows': len(data),
                'execution_time_seconds': execution_time
            },
            'columns': columns,
            'data': data,
            'summary': {
                'row_count': len(data),
                'success': True,
                'error': None
            }
        }
        
        # Write JSON file
        json_filename = sql_file.replace('.sql', '.json')
        json_path = os.path.join(EXPORT_PATH, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, cls=FirebirdJSONEncoder)
        
        logger.info(f"✓ Exported {len(data)} rows to {json_filename}")
        return True, len(data)
        
    except Exception as e:
        logger.error(f"✗ Failed to export {sql_file}: {str(e)}")
        
        # Still create a JSON file with error info
        export_data = {
            'query_info': {
                'file': sql_file,
                'generated': datetime.now().isoformat(),
                'driver': 'firebird-driver',
                'error': str(e)
            },
            'columns': [],
            'data': [],
            'summary': {
                'row_count': 0,
                'success': False,
                'error': str(e)
            }
        }
        
        json_filename = sql_file.replace('.sql', '.json')
        json_path = os.path.join(EXPORT_PATH, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return False, 0


def get_sample_values():
    """Get sample values from top50 CSV files"""
    csv_dir = PATH_CONFIG.get('source_data_dir', 'wincasa_data/source') + "/table_to_csv_with_top_50"
    
    sample_values = {
        'ONR': [],
        'EIGNR': [],
        'KKLASSE': [1]  # Only most common account class
    }
    
    # Read OBJEKTE.csv for ONR values
    try:
        objekte_csv = os.path.join(csv_dir, "OBJEKTE.csv")
        if os.path.exists(objekte_csv):
            with open(objekte_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    try:
                        if row.get('ONR') and int(row['ONR']) > 0 and int(row['ONR']) < 890:
                            sample_values['ONR'].append(int(row['ONR']))
                    except:
                        pass
    except Exception as e:
        logger.warning(f"Could not read OBJEKTE.csv: {e}")
    
    # Read EIGENTUEMER.csv for EIGNR values
    try:
        eigentuemer_csv = os.path.join(csv_dir, "EIGENTUEMER.csv")
        if os.path.exists(eigentuemer_csv):
            with open(eigentuemer_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    try:
                        if row.get('EIGNR') and int(row['EIGNR']) > 0:
                            sample_values['EIGNR'].append(int(row['EIGNR']))
                    except:
                        pass
    except Exception as e:
        logger.warning(f"Could not read EIGENTUEMER.csv: {e}")
    
    # Get only the first most common value
    from collections import Counter
    for key in ['ONR', 'EIGNR']:
        if sample_values[key]:
            counts = Counter(sample_values[key])
            # Only get the single most common value
            most_common = counts.most_common(1)
            sample_values[key] = [most_common[0][0]] if most_common else []
    
    return sample_values


def export_parameterized_query(query_name, sql_template, params, charset='ISO8859_1'):
    """Export a parameterized query with specific values"""
    
    try:
        conn = get_connection(charset)
        cursor = conn.cursor()
        
        # Apply parameters to SQL
        sql = sql_template
        for key, value in params.items():
            sql = sql.replace(f':{key}', str(value))
        
        logger.info(f"  Executing {query_name} with {params}...")
        start_time = datetime.now()
        cursor.execute(sql)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Fetch results with streaming for large datasets
        rows = []
        chunk_size = 1000
        while True:
            chunk = cursor.fetchmany(chunk_size)
            if not chunk:
                break
            rows.extend(chunk)
            if len(rows) >= 10000:  # Limit for parameterized queries
                break
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        cursor.close()
        conn.close()
        
        if len(rows) == 0:
            logger.warning(f"    No data found for {params}")
            return False, 0
        
        # Convert to list of dicts
        data = []
        for row in rows[:1000]:  # Limit JSON to 1000 rows
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(columns):
                    row_dict[columns[i]] = value
            data.append(row_dict)
        
        # Create export structure
        export_data = {
            'query_info': {
                'file': query_name + '.sql',
                'generated': datetime.now().isoformat(),
                'driver': 'firebird-driver',
                'charset': charset,
                'parameters': params,
                'total_rows': len(rows),
                'rows_in_json': len(data),
                'execution_time_seconds': execution_time
            },
            'columns': columns,
            'data': data,
            'summary': {
                'row_count': len(rows),
                'success': True,
                'error': None
            }
        }
        
        # Write JSON file
        param_str = "_".join([f"{k}{v}" for k, v in params.items()])
        json_filename = f"{query_name}_{param_str}.json"
        json_path = os.path.join(EXPORT_PATH, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, cls=FirebirdJSONEncoder)
        
        logger.info(f"✓ Exported {len(rows)} rows to {json_filename} in {execution_time:.2f}s")
        return True, len(rows)
        
    except Exception as e:
        logger.error(f"✗ Failed to export {query_name} with {params}: {str(e)}")
        return False, 0


def export_parameterized_queries():
    """Export parameterized versions of large queries"""
    logger.info("Exporting parameterized queries...")
    
    # Get sample values
    samples = get_sample_values()
    
    if not samples['EIGNR']:
        logger.warning("No sample EIGNR values found for parameterized queries")
        return
    
    # Query 21: Eigentümer-Zahlungshistorie
    sql_21 = """
WITH zahlungen AS (
  SELECT 
    K.KNR, K.ONR, K.ENR,
    B.BNR, B.DATUM, B.BELEGNR, B.TEXT,
    B.BETRAG AS EINGANG,
    CAST(0 AS NUMERIC(15,2)) AS AUSGANG,
    'ZAHLUNG' AS RICHTUNG
  FROM BUCHUNG B
    INNER JOIN KONTEN K ON B.KHABEN = K.KNR
  WHERE K.KKLASSE = 62
    AND B.DATUM >= CURRENT_DATE - 365
    AND K.KNR IN (SELECT KNR FROM EIGENTUEMER WHERE EIGNR = :EIGNR)
    
  UNION ALL
  
  SELECT 
    K.KNR, K.ONR, K.ENR,
    B.BNR, B.DATUM, B.BELEGNR, B.TEXT,
    CAST(0 AS NUMERIC(15,2)) AS EINGANG,
    B.BETRAG AS AUSGANG,
    'BELASTUNG' AS RICHTUNG
  FROM BUCHUNG B
    INNER JOIN KONTEN K ON B.KSOLL = K.KNR
  WHERE K.KKLASSE = 62
    AND B.DATUM >= CURRENT_DATE - 365
    AND K.KNR IN (SELECT KNR FROM EIGENTUEMER WHERE EIGNR = :EIGNR)
)
SELECT 
  E.EIGNR,
  E.ENAME || ', ' || E.EVNAME AS EIGENTUEMER_NAME,
  Z.DATUM,
  Z.TEXT AS BUCHUNGSTEXT,
  Z.RICHTUNG,
  CAST(Z.EINGANG AS NUMERIC(15,2)) AS EINGANG,
  CAST(Z.AUSGANG AS NUMERIC(15,2)) AS AUSGANG,
  Z.ONR,
  O.OBEZ AS OBJEKT
FROM zahlungen Z
  INNER JOIN EIGENTUEMER ET ON Z.KNR = ET.KNR
  INNER JOIN EIGADR E ON ET.EIGNR = E.EIGNR
  LEFT JOIN OBJEKTE O ON Z.ONR = O.ONR
WHERE Z.ONR < 890
ORDER BY Z.DATUM DESC
"""
    
    # Export Query 21 for first Eigentümer only
    if samples['EIGNR']:
        export_parameterized_query(
            "21_eigentuemer_zahlungshistorie_layer4",
            sql_21,
            {'EIGNR': samples['EIGNR'][0]}
        )
    
    # Query 27: Buchungskonten-Übersicht
    sql_27 = """
WITH buchungen AS (
  SELECT 
    B.KSOLL AS KNR,
    SUM(B.BETRAG) AS SOLL_SUMME,
    0 AS HABEN_SUMME
  FROM BUCHUNG B
  WHERE B.DATUM >= CURRENT_DATE - 365
    AND B.KSOLL IN (SELECT KNR FROM KONTEN WHERE KKLASSE = :KKLASSE)
  GROUP BY B.KSOLL
  
  UNION ALL
  
  SELECT 
    B.KHABEN AS KNR,
    0 AS SOLL_SUMME,
    SUM(B.BETRAG) AS HABEN_SUMME
  FROM BUCHUNG B
  WHERE B.DATUM >= CURRENT_DATE - 365
    AND B.KHABEN IN (SELECT KNR FROM KONTEN WHERE KKLASSE = :KKLASSE)
  GROUP BY B.KHABEN
)
SELECT 
  K.KNR,
  K.KBEZ AS BEZEICHNUNG,
  K.KKLASSE,
  CAST(SUM(B.SOLL_SUMME) AS NUMERIC(15,2)) AS SOLL,
  CAST(SUM(B.HABEN_SUMME) AS NUMERIC(15,2)) AS HABEN,
  CAST(SUM(B.SOLL_SUMME) - SUM(B.HABEN_SUMME) AS NUMERIC(15,2)) AS SALDO
FROM KONTEN K
  INNER JOIN buchungen B ON K.KNR = B.KNR
WHERE K.KKLASSE = :KKLASSE
GROUP BY K.KNR, K.KBEZ, K.KKLASSE
HAVING (SUM(B.SOLL_SUMME) > 0 OR SUM(B.HABEN_SUMME) > 0)
ORDER BY ABS(SUM(B.SOLL_SUMME) - SUM(B.HABEN_SUMME)) DESC
"""
    
    # Export Query 27 for most common account class only
    export_parameterized_query(
        "27_buchungskonten_uebersicht_layer4",
        sql_27,
        {'KKLASSE': 1}  # Only Sachkonten
    )


def export_all_queries():
    """Export all Layer 4 queries to JSON"""
    logger.info("Starting JSON export of Layer 4 queries")
    logger.info(f"Source: {LAYER4_PATH}")
    logger.info(f"Destination: {EXPORT_PATH}")
    
    # Create export directory
    os.makedirs(EXPORT_PATH, exist_ok=True)
    
    # Delete all existing JSON files
    logger.info("Deleting existing JSON files...")
    for f in os.listdir(EXPORT_PATH):
        if f.endswith('.json'):
            os.remove(os.path.join(EXPORT_PATH, f))
    
    # Get all SQL files (excluding backups and simplified versions)
    sql_files = sorted([f for f in os.listdir(LAYER4_PATH) 
                       if f.endswith('.sql') 
                       and not f.endswith('.backup')
                       and not '_simplified' in f
                       and not '_by_object' in f])
    
    # Export each query
    success_count = 0
    total_rows = 0
    failed_queries = []
    
    for sql_file in sql_files:
        success, rows = export_query_to_json(sql_file)
        if success:
            success_count += 1
            total_rows += rows
        else:
            failed_queries.append(sql_file)
    
    # Export parameterized queries for large ones
    if any(q in LARGE_QUERIES for q in sql_files):
        logger.info("\nExporting parameterized versions of large queries...")
        export_parameterized_queries()
    
    # Create summary
    summary = {
        'export_time': datetime.now().isoformat(),
        'total_queries': len(sql_files),
        'successful_exports': success_count,
        'failed_exports': len(failed_queries),
        'total_rows_exported': total_rows,
        'failed_queries': failed_queries,
        'export_directory': EXPORT_PATH,
        'notes': {
            'utf8_queries': UTF8_QUERIES,
            'large_queries': LARGE_QUERIES,
            'parameterized_exports': 'See *_EIGNR*.json files for parameterized versions'
        }
    }
    
    summary_path = os.path.join(EXPORT_PATH, '_export_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("="*60)
    logger.info(f"Export completed: {success_count}/{len(sql_files)} queries exported")
    logger.info(f"Total rows: {total_rows}")
    if failed_queries:
        logger.warning(f"Failed queries: {', '.join(failed_queries)}")
    logger.info(f"Summary saved to: {summary_path}")
    
    return summary


def verify_exports(min_rows=10):
    """Verify all exported JSON files meet minimum row requirements"""
    json_files = [f for f in os.listdir(EXPORT_PATH) if f.endswith('.json') and not f.startswith('_')]
    verification_results = {}
    
    for json_file in json_files:
        json_path = os.path.join(EXPORT_PATH, json_file)
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            row_count = data['summary']['row_count']
            success = data['summary']['success']
            meets_min = row_count >= min_rows if success else False
            
            verification_results[json_file] = {
                'success': success,
                'row_count': row_count,
                'meets_minimum': meets_min,
                'error': data['summary'].get('error')
            }
        except Exception as e:
            verification_results[json_file] = {
                'success': False,
                'row_count': 0,
                'meets_minimum': False,
                'error': str(e)
            }
    
    # Create verification summary
    successful_exports = sum(1 for r in verification_results.values() if r['success'])
    meets_minimum = sum(1 for r in verification_results.values() if r['meets_minimum'])
    
    verification_summary = {
        'verification_time': datetime.now().isoformat(),
        'total_files': len(json_files),
        'successful_exports': successful_exports,
        'exports_meeting_minimum': meets_minimum,
        'minimum_rows_required': min_rows,
        'detailed_results': verification_results
    }
    
    summary_path = os.path.join(EXPORT_PATH, '_verification_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(verification_summary, f, indent=2)
    
    logger.info("="*60)
    logger.info(f"Verification Summary:")
    logger.info(f"Total JSON files: {len(json_files)}")
    logger.info(f"Successful exports: {successful_exports}")
    logger.info(f"Exports with ≥{min_rows} rows: {meets_minimum}")
    logger.info(f"Summary saved to: {summary_path}")
    
    return verification_summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Export Layer 4 queries to JSON')
    parser.add_argument('--verify', action='store_true', help='Verify exports after completion')
    parser.add_argument('--min-rows', type=int, default=10, help='Minimum rows for verification (default: 10)')
    parser.add_argument('--single', type=str, help='Export single query file')
    
    args = parser.parse_args()
    
    if args.single:
        # Export single query
        print(f"Exporting single query: {args.single}")
        success, rows = export_query_to_json(args.single)
        if success:
            print(f"✅ Successfully exported {rows} rows")
        else:
            print(f"❌ Export failed")
    else:
        # Export all queries
        print("Starting full JSON export for all Layer 4 queries...")
        summary = export_all_queries()
        
        if args.verify:
            print("\nVerifying exports...")
            verify_exports(args.min_rows)