#!/usr/bin/env python3
"""
WINCASA Phase 2.1 - Golden Set Generator
Erstellt 100 repräsentative User-Queries für Baseline-Testing
"""

import json
import random
from datetime import datetime
from pathlib import Path

# Golden Set - 100 repräsentative WINCASA User-Queries
GOLDEN_QUERIES = [
    # === MIETER-QUERIES (30 Queries) ===
    # Basis Mieter-Suche
    {"id": "M001", "query": "Wer wohnt in der Bergstraße 15?", "category": "mieter_suche", "intent": "lookup", "expected_data": "mieter_komplett"},
    {"id": "M002", "query": "Zeige mir alle Mieter in Hamburg", "category": "mieter_suche", "intent": "lookup", "expected_data": "mieter_komplett"},
    {"id": "M003", "query": "Kontaktdaten von Herrn Müller", "category": "kontakt_lookup", "intent": "lookup", "expected_data": "mieter_komplett"},
    {"id": "M004", "query": "Telefonnummer von Familie Schmidt", "category": "kontakt_lookup", "intent": "lookup", "expected_data": "mieter_komplett"},
    {"id": "M005", "query": "Email-Adresse der Mieterin in Wohnung 12", "category": "kontakt_lookup", "intent": "lookup", "expected_data": "mieter_komplett"},
    
    # Erweiterte Mieter-Suche
    {"id": "M006", "query": "Alle aktuellen Mieter mit Mietdauer über 5 Jahre", "category": "mieter_analyse", "intent": "complex", "expected_data": "mieter_komplett"},
    {"id": "M007", "query": "Mieter ohne Email-Adresse", "category": "mieter_analyse", "intent": "complex", "expected_data": "mieter_komplett"},
    {"id": "M008", "query": "Welche Wohnungen sind vermietet?", "category": "vermietung_status", "intent": "template", "expected_data": "wohnungen"},
    {"id": "M009", "query": "Freie Wohnungen in Hamburg", "category": "leerstand", "intent": "template", "expected_data": "wohnungen_leerstand"},
    {"id": "M010", "query": "Mieterwechsel im letzten Jahr", "category": "mieter_historie", "intent": "complex", "expected_data": "mieter_komplett"},
    
    # Spezifische Mieter-Fragen
    {"id": "M011", "query": "Wie lange wohnt Familie Weber schon in der Wohnung?", "category": "mietdauer", "intent": "lookup", "expected_data": "mieter_komplett"},
    {"id": "M012", "query": "Mieter mit ausstehenden Zahlungen", "category": "zahlungen", "intent": "complex", "expected_data": "mieter_konten"},
    {"id": "M013", "query": "Alle Bewohner im Objekt Hauptstraße 20", "category": "objekt_bewohner", "intent": "template", "expected_data": "mieter_komplett"},
    {"id": "M014", "query": "Wer ist der Hauptmieter in Wohnung 5?", "category": "hauptmieter", "intent": "lookup", "expected_data": "mieter_komplett"},
    {"id": "M015", "query": "Mieter ohne Telefonnummer", "category": "kontakt_analyse", "intent": "complex", "expected_data": "mieter_komplett"},
    
    # Mieter-Kontodaten
    {"id": "M016", "query": "Kontosaldo von Mieter Müller", "category": "konto_saldo", "intent": "lookup", "expected_data": "mieter_konten"},
    {"id": "M017", "query": "Mieter mit negativem Kontosaldo", "category": "rueckstaende", "intent": "complex", "expected_data": "mieter_konten"},
    {"id": "M018", "query": "Zahlungshistorie der letzten 6 Monate", "category": "zahlungshistorie", "intent": "complex", "expected_data": "eigentuemer_zahlungshistorie"},
    {"id": "M019", "query": "Welche Mieter haben Vorauszahlungen geleistet?", "category": "vorauszahlungen", "intent": "complex", "expected_data": "mieter_konten"},
    {"id": "M020", "query": "Offene Forderungen nach Mieter", "category": "forderungen", "intent": "complex", "expected_data": "mieter_konten"},
    
    # Mieter-Sonderabfragen
    {"id": "M021", "query": "Mieter mit besonderen Vereinbarungen", "category": "sondervereinbarungen", "intent": "complex", "expected_data": "mieter_komplett"},
    {"id": "M022", "query": "Alle Mieter mit Haustieren", "category": "haustiere", "intent": "complex", "expected_data": "mieter_komplett"},
    {"id": "M023", "query": "Gewerbliche Mieter", "category": "gewerbemieter", "intent": "complex", "expected_data": "mieter_komplett"},
    {"id": "M024", "query": "Mieter nach Anzahl Personen im Haushalt", "category": "haushalt_groesse", "intent": "complex", "expected_data": "mieter_komplett"},
    {"id": "M025", "query": "Kündigungen in den letzten 12 Monaten", "category": "kuendigungen", "intent": "complex", "expected_data": "mieter_komplett"},
    
    # Mieter-Reports
    {"id": "M026", "query": "Mieterübersicht für Hausverwaltung", "category": "mieter_report", "intent": "complex", "expected_data": "mieter_komplett"},
    {"id": "M027", "query": "Kontaktliste aller aktuellen Mieter", "category": "kontaktliste", "intent": "template", "expected_data": "mieter_komplett"},
    {"id": "M028", "query": "Mietvertragsdauer Statistik", "category": "statistik", "intent": "complex", "expected_data": "mieter_komplett"},
    {"id": "M029", "query": "Mieter sortiert nach Einzugsdatum", "category": "einzug_chronologie", "intent": "template", "expected_data": "mieter_komplett"},
    {"id": "M030", "query": "Notfallkontakte aller Mieter", "category": "notfallkontakte", "intent": "complex", "expected_data": "mieter_komplett"},

    # === EIGENTÜMER-QUERIES (25 Queries) ===
    # Basis Eigentümer-Suche
    {"id": "E001", "query": "Wem gehört das Gebäude in der Rosenstraße 8?", "category": "eigentuemer_suche", "intent": "lookup", "expected_data": "eigentuemer_portfolio"},
    {"id": "E002", "query": "Kontaktdaten von Eigentümer Hansen", "category": "kontakt_lookup", "intent": "lookup", "expected_data": "eigentuemer_portfolio"},
    {"id": "E003", "query": "Alle Eigentümer mit mehr als 3 Objekten", "category": "portfolio_analyse", "intent": "template", "expected_data": "eigentuemer_portfolio"},
    {"id": "E004", "query": "Eigentümer ohne Email-Adresse", "category": "kontakt_analyse", "intent": "complex", "expected_data": "eigentuemer_portfolio"},
    {"id": "E005", "query": "WEG-Eigentümer der Anlage Musterstraße", "category": "weg_eigentuemer", "intent": "template", "expected_data": "weg_eigentuemer"},
    
    # Eigentümer-Portfolio
    {"id": "E006", "query": "Portfolio von Eigentümer Schmidt", "category": "portfolio_details", "intent": "lookup", "expected_data": "eigentuemer_portfolio"},
    {"id": "E007", "query": "Größte Eigentümer nach Anzahl Objekten", "category": "portfolio_ranking", "intent": "complex", "expected_data": "eigentuemer_portfolio"},
    {"id": "E008", "query": "Eigentümer nur mit gewerblichen Objekten", "category": "gewerbeeigentuemer", "intent": "complex", "expected_data": "eigentuemer_portfolio"},
    {"id": "E009", "query": "Neue Eigentümer in den letzten 2 Jahren", "category": "neue_eigentuemer", "intent": "complex", "expected_data": "eigentuemer_portfolio"},
    {"id": "E010", "query": "Eigentümer mit ausstehenden Zahlungen", "category": "eigentuemer_schulden", "intent": "complex", "expected_data": "eigentuemer_konten"},
    
    # Eigentümer-Finanzen
    {"id": "E011", "query": "Kontosaldo aller Eigentümer", "category": "kontostaende", "intent": "complex", "expected_data": "eigentuemer_konten"},
    {"id": "E012", "query": "Eigentümer mit positivem Kontosaldo", "category": "guthaben", "intent": "complex", "expected_data": "eigentuemer_konten"},
    {"id": "E013", "query": "Rücklagenkonto von Eigentümer Müller", "category": "ruecklagen", "intent": "lookup", "expected_data": "eigentuemer_konten"},
    {"id": "E014", "query": "Hausgeld-Zahlungen der letzten 6 Monate", "category": "hausgeld", "intent": "complex", "expected_data": "eigentuemer_zahlungshistorie"},
    {"id": "E015", "query": "Sonderumlagen nach Eigentümer", "category": "sonderumlagen", "intent": "complex", "expected_data": "eigentuemer_konten"},
    
    # WEG-Verwaltung
    {"id": "E016", "query": "Beiräte der WEG-Anlagen", "category": "beiraete", "intent": "template", "expected_data": "beiraete"},
    {"id": "E017", "query": "Beschlüsse der letzten Eigentümerversammlung", "category": "beschluesse", "intent": "template", "expected_data": "beschluesse"},
    {"id": "E018", "query": "Nächste Eigentümerversammlung", "category": "versammlungen", "intent": "template", "expected_data": "versammlungen"},
    {"id": "E019", "query": "Stimmrechte nach Miteigentumsanteilen", "category": "stimmrechte", "intent": "complex", "expected_data": "weg_eigentuemer"},
    {"id": "E020", "query": "Teilnehmer der letzten Versammlung", "category": "versammlungsteilnahme", "intent": "complex", "expected_data": "versammlungen"},
    
    # Eigentümer-Sonderabfragen
    {"id": "E021", "query": "Eigentümer mit mehreren WEG-Anteilen", "category": "mehrfacheigentuemer", "intent": "complex", "expected_data": "weg_eigentuemer"},
    {"id": "E022", "query": "Bankverbindungen aller Eigentümer", "category": "bankdaten", "intent": "complex", "expected_data": "eigentuemer_portfolio"},
    {"id": "E023", "query": "Eigentümer-Vollmachten und Vertretungen", "category": "vollmachten", "intent": "complex", "expected_data": "eigentuemer_portfolio"},
    {"id": "E024", "query": "Eigentümer nach Postleitzahlen sortiert", "category": "geografische_verteilung", "intent": "template", "expected_data": "eigentuemer_portfolio"},
    {"id": "E025", "query": "Verstorbene Eigentümer / Nachlässe", "category": "nachlaesse", "intent": "complex", "expected_data": "eigentuemer_portfolio"},

    # === OBJEKT-QUERIES (20 Queries) ===
    # Basis Objekt-Information
    {"id": "O001", "query": "Details zum Objekt Hauptstraße 15", "category": "objekt_details", "intent": "lookup", "expected_data": "objekte_details"},
    {"id": "O002", "query": "Alle Objekte in Bremen", "category": "objekte_standort", "intent": "template", "expected_data": "objekte_details"},
    {"id": "O003", "query": "Objekte mit mehr als 10 Wohnungen", "category": "objekt_groesse", "intent": "template", "expected_data": "objekte_details"},
    {"id": "O004", "query": "Baujahr der Objekte", "category": "baujahr_analyse", "intent": "complex", "expected_data": "objekte_details"},
    {"id": "O005", "query": "Sanierungsbedürftige Objekte", "category": "sanierung", "intent": "complex", "expected_data": "objekte_details"},
    
    # Wohnungs-Information
    {"id": "O006", "query": "Alle Wohnungen im Objekt Bergstraße 20", "category": "wohnungen_objekt", "intent": "template", "expected_data": "wohnungen"},
    {"id": "O007", "query": "Freie Wohnungen nach Größe sortiert", "category": "leerstand_groesse", "intent": "template", "expected_data": "wohnungen_leerstand"},
    {"id": "O008", "query": "Wohnungen mit Balkon oder Terrasse", "category": "wohnung_ausstattung", "intent": "complex", "expected_data": "wohnungen"},
    {"id": "O009", "query": "Durchschnittliche Wohnungsgröße pro Objekt", "category": "groessen_statistik", "intent": "complex", "expected_data": "wohnungen"},
    {"id": "O010", "query": "Wohnungen mit besonderen Merkmalen", "category": "sonderausstattung", "intent": "complex", "expected_data": "wohnungen"},
    
    # Objekt-Portfolio
    {"id": "O011", "query": "Portfolio-Übersicht aller verwalteten Objekte", "category": "portfolio_uebersicht", "intent": "template", "expected_data": "objekte_portfolio"},
    {"id": "O012", "query": "Objekte nach Verwaltungstyp", "category": "verwaltungsart", "intent": "complex", "expected_data": "objekte_details"},
    {"id": "O013", "query": "Mieteinnahmen pro Objekt", "category": "mieteinnahmen", "intent": "complex", "expected_data": "monatliche_mieteinnahmen"},
    {"id": "O014", "query": "Instandhaltungskosten nach Objekten", "category": "instandhaltung", "intent": "complex", "expected_data": "instandhaltungskosten"},
    {"id": "O015", "query": "Vermietungsgrad pro Objekt", "category": "vermietungsgrad", "intent": "complex", "expected_data": "leerstandsanalyse"},
    
    # Objekt-Sonderanalysen
    {"id": "O016", "query": "Objekte mit hoher Fluktuation", "category": "fluktuation", "intent": "complex", "expected_data": "leerstandsanalyse"},
    {"id": "O017", "query": "Energetische Bewertung der Objekte", "category": "energiebewertung", "intent": "complex", "expected_data": "objekte_details"},
    {"id": "O018", "query": "Objekte mit Parkplätzen", "category": "parkplaetze", "intent": "complex", "expected_data": "objekte_details"},
    {"id": "O019", "query": "Barrierefreie Objekte und Wohnungen", "category": "barrierefreiheit", "intent": "complex", "expected_data": "objekte_details"},
    {"id": "O020", "query": "Objekte nach Verwaltungsgebühren", "category": "verwaltungsgebuehren", "intent": "complex", "expected_data": "objekte_portfolio"},

    # === FINANZ-QUERIES (15 Queries) ===
    # Basis Finanz-Abfragen
    {"id": "F001", "query": "Aktuelle Kontosalden aller Konten", "category": "kontosalden", "intent": "template", "expected_data": "konten_saldenliste"},
    {"id": "F002", "query": "Buchungen der letzten 30 Tage", "category": "aktuelle_buchungen", "intent": "template", "expected_data": "detaillierte_buchungen"},
    {"id": "F003", "query": "Offene Forderungen Übersicht", "category": "forderungen", "intent": "template", "expected_data": "forderungsalterung"},
    {"id": "F004", "query": "Rücklagen-Management Übersicht", "category": "ruecklagen", "intent": "template", "expected_data": "ruecklagen_management"},
    {"id": "F005", "query": "Bankkonten-Übersicht", "category": "bankkonten", "intent": "template", "expected_data": "bank_konten"},
    
    # Erweiterte Finanz-Analysen
    {"id": "F006", "query": "Nebenkostenabrechnung nach Objekten", "category": "nebenkosten", "intent": "complex", "expected_data": "nebenkostenkonten_matrix"},
    {"id": "F007", "query": "Durchlaufende Posten Analyse", "category": "durchlaufende_posten", "intent": "complex", "expected_data": "durchlaufende_posten"},
    {"id": "F008", "query": "Sonderentnahmen der letzten 12 Monate", "category": "sonderentnahmen", "intent": "complex", "expected_data": "sonderentnahmen"},
    {"id": "F009", "query": "WEG-Zahlungsübersicht nach Eigentümern", "category": "weg_zahlungen", "intent": "complex", "expected_data": "weg_zahlungsuebersicht"},
    {"id": "F010", "query": "Objektbezogene Sachkonten-Analyse", "category": "sachkonten", "intent": "complex", "expected_data": "objektbezogene_sachkonten"},
    
    # Spezielle Finanz-Reports
    {"id": "F011", "query": "Spezielle Kontenklassen Übersicht", "category": "kontenklassen", "intent": "complex", "expected_data": "spezielle_kontenklassen"},
    {"id": "F012", "query": "Buchungskonten-Übersicht komplett", "category": "buchungskonten", "intent": "template", "expected_data": "buchungskonten_uebersicht"},
    {"id": "F013", "query": "Zahlungshistorie pro Eigentümer", "category": "zahlungshistorie_details", "intent": "complex", "expected_data": "eigentuemer_zahlungshistorie"},
    {"id": "F014", "query": "Liquiditätsplanung nächste 6 Monate", "category": "liquiditaetsplanung", "intent": "complex", "expected_data": "konten_saldenliste"},
    {"id": "F015", "query": "Jahresabschluss-Vorbereitung Daten", "category": "jahresabschluss", "intent": "complex", "expected_data": "buchungskonten_uebersicht"},

    # === ALLGEMEINE/KOMPLEXE QUERIES (10 Queries) ===
    # Cross-Entity Abfragen
    {"id": "A001", "query": "Vollständiger Überblick Objekt mit Mietern und Eigentümern", "category": "vollueberblick", "intent": "complex", "expected_data": "multiple"},
    {"id": "A002", "query": "Rentabilitätsanalyse pro Objekt", "category": "rentabilitaet", "intent": "complex", "expected_data": "multiple"},
    {"id": "A003", "query": "Mieter-Fluktuation und Leerstandskosten", "category": "fluktuation_kosten", "intent": "complex", "expected_data": "multiple"},
    {"id": "A004", "query": "Wartungs- und Instandhaltungsplan", "category": "wartungsplan", "intent": "complex", "expected_data": "multiple"},
    {"id": "A005", "query": "Compliance-Report für Behörden", "category": "compliance", "intent": "complex", "expected_data": "multiple"},
    
    # Business Intelligence
    {"id": "A006", "query": "KPIs der Immobilienverwaltung", "category": "kpis", "intent": "complex", "expected_data": "multiple"},
    {"id": "A007", "query": "Risiko-Assessment der Objekte", "category": "risiko_assessment", "intent": "complex", "expected_data": "multiple"},
    {"id": "A008", "query": "Marktvergleich und Potenzialanalyse", "category": "marktanalyse", "intent": "complex", "expected_data": "multiple"},
    {"id": "A009", "query": "Jahresplanung und Budget-Vorschau", "category": "jahresplanung", "intent": "complex", "expected_data": "multiple"},
    {"id": "A010", "query": "360-Grad Objektanalyse komplett", "category": "objektanalyse_komplett", "intent": "complex", "expected_data": "multiple"},
]

def create_golden_set():
    """Erstellt das Golden Set für Phase 2.1 Testing"""
    
    # Verzeichnis erstellen
    golden_dir = Path("golden_set")
    golden_dir.mkdir(exist_ok=True)
    
    # Golden Set strukturieren
    golden_set = {
        "meta": {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "total_queries": len(GOLDEN_QUERIES),
            "description": "WINCASA Phase 2.1 - Golden Set für Baseline Testing",
            "categories": {},
            "intents": {},
            "data_sources": {}
        },
        "queries": GOLDEN_QUERIES
    }
    
    # Statistiken berechnen
    categories = {}
    intents = {}
    data_sources = {}
    
    for query in GOLDEN_QUERIES:
        cat = query["category"]
        intent = query["intent"]
        data = query["expected_data"]
        
        categories[cat] = categories.get(cat, 0) + 1
        intents[intent] = intents.get(intent, 0) + 1
        data_sources[data] = data_sources.get(data, 0) + 1
    
    golden_set["meta"]["categories"] = categories
    golden_set["meta"]["intents"] = intents
    golden_set["meta"]["data_sources"] = data_sources
    
    # Golden Set speichern
    with open(golden_dir / "queries.json", "w", encoding="utf-8") as f:
        json.dump(golden_set, f, indent=2, ensure_ascii=False)
    
    # Zusätzliche Kategorien-Dateien
    for intent in ["lookup", "template", "complex"]:
        intent_queries = [q for q in GOLDEN_QUERIES if q["intent"] == intent]
        with open(golden_dir / f"queries_{intent}.json", "w", encoding="utf-8") as f:
            json.dump(intent_queries, f, indent=2, ensure_ascii=False)
    
    # Summary erstellen
    summary = {
        "total_queries": len(GOLDEN_QUERIES),
        "breakdown": {
            "mieter_queries": 30,
            "eigentuemer_queries": 25,
            "objekt_queries": 20,
            "finanz_queries": 15,
            "allgemeine_queries": 10
        },
        "intent_distribution": intents,
        "category_distribution": categories,
        "data_coverage": data_sources
    }
    
    with open(golden_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Golden Set erstellt: {len(GOLDEN_QUERIES)} Queries")
    print(f"📁 Gespeichert in: {golden_dir}")
    print(f"📊 Intent-Verteilung: {intents}")
    print(f"🎯 Kategorien: {len(categories)}")
    
    return golden_set

if __name__ == "__main__":
    create_golden_set()