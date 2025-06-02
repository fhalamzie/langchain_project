#!/usr/bin/env python3
# check_license.py - Skript zum Prüfen der Lizenzdaten in der Wincasa-Datenbank

import os
import sys
from datetime import datetime, date

# Füge den aktuellen Pfad zum Systempfad hinzu, um lokale Module zu importieren
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importiere Module für Datenbankabfragen
try:
    from db_executor import execute_sql
except ImportError:
    try:
        from query_router import execute_safe_sql as execute_sql
    except ImportError:
        print("Kritischer Fehler: Datenbankmodule nicht verfügbar.")
        sys.exit(1)

def format_date(date_obj):
    """Formatiert ein Datum für die Anzeige"""
    if date_obj is None:
        return "Kein Datum"
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except ValueError:
            return date_obj
    
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
        
    return date_obj.strftime("%d.%m.%Y")

def get_status_text(status_code):
    """Liefert einen lesbaren Status-Text"""
    if status_code == 'T':
        return "Aktiv"
    elif status_code == 'F':
        return "Inaktiv"
    else:
        return str(status_code)

def check_expiry(date_val):
    """Prüft, ob ein Datum abgelaufen ist und gibt einen Status-Text zurück"""
    if date_val is None:
        return "Kein Ablaufdatum"
        
    if isinstance(date_val, str):
        try:
            date_obj = datetime.strptime(date_val, "%Y-%m-%d").date()
        except ValueError:
            return "Ungültiges Datum"
    elif isinstance(date_val, datetime):
        date_obj = date_val.date()
    else:
        date_obj = date_val
        
    today = datetime.now().date()
    if date_obj > today:
        days_left = (date_obj - today).days
        if days_left > 365:
            return f"Gültig (noch {days_left} Tage)"
        elif days_left > 30:
            return f"Gültig (noch {days_left} Tage) ⚠️"
        else:
            return f"Läuft bald ab! Noch {days_left} Tage ⚠️⚠️"
    else:
        days_expired = (today - date_obj).days
        return f"ABGELAUFEN (seit {days_expired} Tagen) ❌"

def check_module_licenses():
    """Überprüft Lizenzinformationen in der MODULE-Tabelle"""
    print("\n=== LIZENZINFORMATIONEN - MODULE ===\n")
    
    # SQL-Abfrage für MODULE-Tabelle
    sql = """
    SELECT 
        MODULEID, 
        STATUS, 
        LIMITDATE
    FROM 
        MODULE
    ORDER BY 
        MODULEID
    """
    
    try:
        # Führe die Abfrage aus
        print("Führe Abfrage auf MODULE-Tabelle aus...")
        result = execute_sql(sql)
        
        # Prüfe ob wir ein Tupel mit (success, data) bekommen haben
        if isinstance(result, tuple):
            success, data = result
            if not success:
                print(f"Fehler bei der Abfrage: {data}")
                return
            results = data
        else:
            results = result
        
        # Zeige die Ergebnisse an
        if not results:
            print("Keine Module gefunden.")
            return
        
        # Formatiere die Ausgabe in Tabellenform
        print("\nLizenzstatus der Module:\n")
        print(f"{'Modul-ID':<20} {'Status':<10} {'Ablaufdatum':<15} {'Lizenzstatus':<30}")
        print("-" * 75)
        
        # Zähler für die Zusammenfassung
        total_count = len(results)
        active_count = 0
        expired_count = 0
        warning_count = 0
        
        # Verarbeite jede Zeile
        for row in results:
            module_id = str(row.get('MODULEID', 'N/A'))
            status_code = row.get('STATUS')
            status_text = get_status_text(status_code)
            limitdate = row.get('LIMITDATE')
            
            # Zähle aktive Module
            if status_code == 'T':
                active_count += 1
            
            # Formatiere das Datum
            formatted_date = format_date(limitdate) if limitdate else "Kein Datum"
            
            # Prüfe den Lizenzstatus
            license_status = check_expiry(limitdate)
            
            # Zähle abgelaufene und bald ablaufende Lizenzen
            if "ABGELAUFEN" in license_status:
                expired_count += 1
            elif "⚠️" in license_status:
                warning_count += 1
            
            # Gib die Zeile aus
            print(f"{module_id:<20} {status_text:<10} {formatted_date:<15} {license_status:<30}")
        
        # Gib die Zusammenfassung aus
        print("\nZusammenfassung:")
        print(f"- Gesamtzahl Module: {total_count}")
        print(f"- Aktive Module: {active_count}")
        print(f"- Inaktive Module: {total_count - active_count}")
        print(f"- Abgelaufene Lizenzen: {expired_count}")
        print(f"- Bald ablaufende Lizenzen: {warning_count}")
        
    except Exception as e:
        print(f"Fehler bei der Lizenzprüfung: {e}")

def check_tech_data_licenses():
    """Überprüft mögliche Lizenzinformationen in der TECHDATA-Tabelle"""
    print("\n=== MÖGLICHE LIZENZINFORMATIONEN - TECHDATA ===\n")
    
    # SQL-Abfrage für TECHDATA-Tabelle mit Fokus auf potenzielle Lizenzinformationen
    sql = """
    SELECT 
        ID, 
        FREITEXT1, 
        FREITEXT2, 
        FREITEXT3, 
        FREITEXT4, 
        FREIWERT1, 
        FREIWERT2 
    FROM 
        TECHDATA 
    WHERE 
        UPPER(FREITEXT1) LIKE '%LIZENZ%' OR 
        UPPER(FREITEXT2) LIKE '%LIZENZ%' OR 
        UPPER(FREITEXT3) LIKE '%LIZENZ%' OR 
        UPPER(FREITEXT4) LIKE '%LIZENZ%' OR
        UPPER(FREITEXT1) LIKE '%LICENSE%' OR 
        UPPER(FREITEXT2) LIKE '%LICENSE%' OR 
        UPPER(FREITEXT3) LIKE '%LICENSE%' OR 
        UPPER(FREITEXT4) LIKE '%LICENSE%'
    """
    
    try:
        # Führe die Abfrage aus
        print("Suche nach Lizenzinformationen in TECHDATA...")
        result = execute_sql(sql)
        
        # Prüfe ob wir ein Tupel mit (success, data) bekommen haben
        if isinstance(result, tuple):
            success, data = result
            if not success:
                print(f"Fehler bei der Abfrage: {data}")
                return
            results = data
        else:
            results = result
            
        # Zeige die Ergebnisse an
        if not results:
            print("Keine Lizenzinformationen in TECHDATA gefunden.")
            return
            
        # Formatiere die Ausgabe in Tabellenform
        print("\nGefundene Lizenzinformationen:\n")
        
        # Zeige die Spaltenüberschriften an
        headers = list(results[0].keys())
        header_format = ""
        separator = ""
        
        for header in headers:
            header_width = max(len(str(header)), 15)
            header_format += f"{header:<{header_width}} "
            separator += "-" * header_width + " "
            
        print(header_format)
        print(separator)
        
        # Zeige die Daten an
        for row in results:
            row_format = ""
            for header in headers:
                value = row.get(header, "")
                header_width = max(len(str(header)), 15)
                row_format += f"{str(value)[:header_width]:<{header_width}} "
            print(row_format)
            
    except Exception as e:
        print(f"Fehler bei der TECHDATA-Prüfung: {e}")

def check_status_licenses():
    """Überprüft Lizenzinformationen in der STATUS-Tabelle"""
    print("\n=== LIZENZINFORMATIONEN - STATUS ===\n")
    
    # SQL-Abfrage für STATUS-Tabelle
    sql = """
    SELECT
        LIZENZNR,
        MODULELASTCHECK,
        PRODID
    FROM
        STATUS
    """
    # Es gibt oft nur einen Eintrag in der STATUS Tabelle, daher kein ORDER BY oder LIMIT
    
    try:
        # Führe die Abfrage aus
        print("Führe Abfrage auf STATUS-Tabelle aus...")
        result = execute_sql(sql)
        
        if isinstance(result, tuple):
            success, data = result
            if not success:
                print(f"Fehler bei der Abfrage der STATUS-Tabelle: {data}")
                return
            results = data
        else:
            results = result
            
        if not results:
            print("Keine Einträge in der STATUS-Tabelle gefunden.")
            return
            
        print("\nLizenzdetails aus STATUS-Tabelle:\n")
        print(f"{'Lizenznummer':<30} {'Letzte Modulprüfung':<20} {'Produkt-ID':<15}")
        print("-" * 75)
        
        for row in results:
            lizenznr = str(row.get('LIZENZNR', 'N/A'))
            module_last_check = format_date(row.get('MODULELASTCHECK'))
            prod_id = str(row.get('PRODID', 'N/A'))
            
            print(f"{lizenznr:<30} {module_last_check:<20} {prod_id:<15}")
            
    except Exception as e:
        print(f"Fehler bei der Prüfung der STATUS-Tabelle: {e}")

def check_datev_license_key(license_key_to_find):
    """Sucht nach einem spezifischen Lizenzkey in der DATEVMAN-Tabelle."""
    print(f"\n=== SUCHE NACH DATEV LIZENZKEY: {license_key_to_find} ===\n")
    
    # Spalten, in denen gesucht werden soll
    search_columns = ['NAME', 'ZUSATZ', 'STR', 'PLZORT', 'TEL', 'FAX', 'MOBIL', 'EMAIL', 'INTERNET',
                      'STEUERBERATER', 'SACHBEARB', 'PFAD', 'DATEVOBE', 'DATUMDRUCK', 'KENNWORT',
                      'OBJEKTE', 'ONRTEXT']
    
    # Erstelle die WHERE-Klausel dynamisch
    where_clauses = []
    for col in search_columns:
        # Für numerische Spalten exakten Vergleich, für Textspalten LIKE
        # Da wir den Key als String suchen, verwenden wir LIKE für alle relevanten Spalten
        # und stellen sicher, dass die Spalte existiert und ein String-Typ ist (implizit durch VARCHAR/CHAR)
        where_clauses.append(f"UPPER({col}) LIKE '%{license_key_to_find.upper()}%'")
    
    # Die Spalten BERATERNR und MANDANTENNR sind INTEGER, daher direkter Vergleich, falls der Key numerisch ist
    if license_key_to_find.isdigit():
        where_clauses.append(f"BERATERNR = {license_key_to_find}")
        where_clauses.append(f"MANDANTENNR = {license_key_to_find}")

    sql = f"""
    SELECT
        NR, {', '.join(search_columns)}, BERATERNR, MANDANTENNR
    FROM
        DATEVMAN
    WHERE
        {' OR '.join(where_clauses)}
    """
    
    try:
        print(f"Führe Abfrage auf DATEVMAN-Tabelle aus, um nach Key '{license_key_to_find}' zu suchen...")
        result = execute_sql(sql)
        
        if isinstance(result, tuple):
            success, data = result
            if not success:
                print(f"Fehler bei der Abfrage der DATEVMAN-Tabelle: {data}")
                return
            results = data
        else:
            results = result
            
        if not results:
            print(f"Lizenzkey '{license_key_to_find}' wurde in der DATEVMAN-Tabelle nicht gefunden.")
            return
            
        print(f"\nEinträge in DATEVMAN, die den Lizenzkey '{license_key_to_find}' enthalten könnten:\n")
        
        headers = ['NR'] + search_columns + ['BERATERNR', 'MANDANTENNR']
        col_widths = {header: max(len(header), 10) for header in headers} # Mindestbreite 10

        # Spaltenbreiten anpassen basierend auf den längsten Werten
        for row in results:
            for header in headers:
                col_widths[header] = max(col_widths[header], len(str(row.get(header, ''))))
        
        header_line = " | ".join([f"{h:<{col_widths[h]}}" for h in headers])
        separator_line = "-+-".join(["-" * col_widths[h] for h in headers])
        
        print(header_line)
        print(separator_line)
        
        for row in results:
            row_line = " | ".join([f"{str(row.get(h, '')):<{col_widths[h]}}" for h in headers])
            print(row_line)
            
    except Exception as e:
        print(f"Fehler bei der Suche nach dem DATEV-Lizenzkey: {e}")

def main():
    """Hauptfunktion"""
    print("=== WINCASA LIZENZPRÜFUNG ===")
    print("Dieses Skript prüft Lizenzinformationen in der Wincasa-Datenbank.")
    print("Stand: " + datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    
    try:
        # Prüfe Module-Tabelle
        check_module_licenses()
        
        # Prüfe TECHDATA-Tabelle
        check_tech_data_licenses()

        # Prüfe STATUS-Tabelle
        check_status_licenses()

        # Suche nach spezifischem DATEV Lizenzkey
        datev_key = "131716"
        check_datev_license_key(datev_key)
        
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")
        
    print("\n=== LIZENZPRÜFUNG ABGESCHLOSSEN ===")

if __name__ == "__main__":
    main()