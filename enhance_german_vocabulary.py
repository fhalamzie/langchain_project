#!/usr/bin/env python3
"""
Enhance WINCASA German Business Vocabulary
Expand from basic vocabulary to comprehensive German property management terminology
"""

import json
from pathlib import Path

def get_enhanced_german_vocabulary():
    """Return comprehensive German property management vocabulary"""
    
    return {
        # Core Business Entities (Enhanced)
        "eigentümer": {
            "primary_table": "EIGADR",
            "description": "Immobilieneigentümer / Vermieter",
            "aliases": ["eigentuemer", "owner", "vermieter", "landlord", "besitzer", "immobilienbesitzer", "weg-eigentümer"],
            "key_fields": ["EIGNR", "ENAME", "EVNAME", "ENOTIZ", "ESTRASSE", "EPLZORT"],
            "german_variations": ["eigentuemer", "eigentümerin", "vermieter", "vermieterin", "besitzer", "besitzerin"]
        },
        "mieter": {
            "primary_table": "BEWADR", 
            "description": "Wohnungsmieter / Bewohner",
            "aliases": ["bewohner", "tenant", "pächter", "mietpartei", "hauptmieter", "untermieter"],
            "key_fields": ["BEWNR", "BNAME", "BVNAME", "BSTR", "BPLZORT"],
            "german_variations": ["mieter", "mieterin", "bewohner", "bewohnerin", "pächter", "pächterin"]
        },
        "wohnung": {
            "primary_table": "WOHNUNG",
            "description": "Mieteinheit / Apartment",
            "aliases": ["apartment", "einheit", "unit", "mietobjekt", "wohneinheit", "mieteinheit", "zimmer"],
            "key_fields": ["ENR", "ETYP", "EFLAECHE", "EBEZ"],
            "german_variations": ["wohnung", "apartment", "einheit", "wohneinheit", "mieteinheit"]
        },
        "objekt": {
            "primary_table": "OBJEKTE",
            "description": "Gebäude / Liegenschaft",
            "aliases": ["gebäude", "immobilie", "liegenschaft", "property", "haus", "wohnhaus", "mehrfamilienhaus"],
            "key_fields": ["ONR", "OBEZ", "OSTRASSE", "OPLZORT"],
            "german_variations": ["objekt", "gebäude", "immobilie", "liegenschaft", "haus", "wohnhaus"]
        },
        
        # Financial Terms (Comprehensive)
        "kaltmiete": {
            "primary_field": "BEWOHNER.Z1",
            "description": "Nettomiete ohne Nebenkosten",
            "aliases": ["nettomiete", "grundmiete", "net rent", "grundmiete", "miete netto"],
            "related_table": "BEWOHNER",
            "german_variations": ["kaltmiete", "nettomiete", "grundmiete", "mietgrundlage"]
        },
        "nebenkosten": {
            "primary_field": "BEWOHNER.Z3", 
            "description": "Betriebskosten-Vorauszahlung",
            "aliases": ["betriebskosten", "NK", "operating costs", "umlagen", "hausnebenkosten"],
            "related_table": "BEWOHNER",
            "german_variations": ["nebenkosten", "betriebskosten", "umlagen", "NK", "betriebskostenumlage"]
        },
        "warmmiete": {
            "computed": "BEWOHNER.Z1 + BEWOHNER.Z2 + BEWOHNER.Z3 + BEWOHNER.Z4",
            "description": "Gesamtmiete inkl. aller Nebenkosten",
            "aliases": ["bruttomiete", "gesamtmiete", "gross rent", "vollmiete", "inklusivmiete"],
            "related_table": "BEWOHNER",
            "german_variations": ["warmmiete", "bruttomiete", "gesamtmiete", "vollmiete"]
        },
        "kaution": {
            "primary_field": "BEWOHNER.KAUT_VEREINBART",
            "description": "Mietkaution / Sicherheitsleistung",
            "aliases": ["sicherheit", "deposit", "pfand", "mietsicherheit", "bürgschaft"],
            "related_table": "BEWOHNER",
            "german_variations": ["kaution", "sicherheit", "mietsicherheit", "mietbürgschaft"]
        },
        
        # WEG & Legal Terms
        "weg": {
            "primary_table": "OBJEKTE",
            "description": "Wohnungseigentümergemeinschaft",
            "aliases": ["wohnungseigentümergemeinschaft", "eigentumsgemeinschaft", "hausgemeinschaft"],
            "key_fields": ["ONR", "OBEZ"],
            "german_variations": ["weg", "wohnungseigentümergemeinschaft", "eigentumsgemeinschaft"]
        },
        "beirat": {
            "primary_table": "BEIRAETE",
            "description": "WEG-Beirat / Verwaltungsbeirat",
            "aliases": ["verwaltungsbeirat", "beiratsmitglied", "board", "advisory board"],
            "key_fields": ["BEIRAT_ID", "BNAME", "BVORNAME"],
            "german_variations": ["beirat", "verwaltungsbeirat", "beiratsmitglied"]
        },
        "beschluss": {
            "primary_table": "BESCHLUESSE",
            "description": "WEG-Beschluss / Eigentümerversammlung",
            "aliases": ["resolution", "entscheidung", "votum", "mehrheitsbeschluss"],
            "key_fields": ["BESCHLUSS_ID", "TITEL", "DATUM"],
            "german_variations": ["beschluss", "mehrheitsbeschluss", "einstimmiger beschluss"]
        },
        "versammlung": {
            "primary_table": "VERSAMMLUNGEN",
            "description": "Eigentümerversammlung",
            "aliases": ["eigentümerversammlung", "assembly", "meeting", "hauptversammlung"],
            "key_fields": ["VERSAMMLUNG_ID", "DATUM", "VERSAMMLUNG_ART"],
            "german_variations": ["versammlung", "eigentümerversammlung", "hauptversammlung"]
        },
        "miteigentumsanteil": {
            "primary_field": "EIGENTUEMER.Z1",
            "description": "Miteigentumsanteil nach WEG",
            "aliases": ["eigentumsanteil", "anteil", "ownership share", "weg-anteil"],
            "related_table": "EIGENTUEMER",
            "german_variations": ["miteigentumsanteil", "eigentumsanteil", "weg-anteil"]
        },
        
        # Property Management Terms
        "verwaltung": {
            "primary_table": "VERWALTER",
            "description": "Hausverwaltung / Property Management",
            "aliases": ["hausverwaltung", "property management", "verwaltung", "verwalter"],
            "key_fields": ["VERWALTER_ID", "VERWALTUNG_NAME"],
            "german_variations": ["verwaltung", "hausverwaltung", "immobilienverwaltung"]
        },
        "hausmeister": {
            "primary_table": "HAUSMEISTER",
            "description": "Hausmeister / Facility Manager",
            "aliases": ["facility manager", "caretaker", "janitor", "gebäudeverwalter"],
            "key_fields": ["HAUSMEISTER_ID", "NAME"],
            "german_variations": ["hausmeister", "hausmeisterin", "gebäudeverwalter"]
        },
        "instandhaltung": {
            "primary_table": "BUCHUNG",
            "description": "Instandhaltung / Wartung",
            "aliases": ["wartung", "maintenance", "reparatur", "sanierung", "modernisierung"],
            "key_fields": ["BNR", "KATEGORIE", "BETRAG"],
            "german_variations": ["instandhaltung", "wartung", "instandsetzung", "reparatur"]
        },
        "rücklage": {
            "primary_table": "RUECKPOS", 
            "description": "Instandhaltungsrücklage",
            "aliases": ["ruecklage", "reserve", "rückstellung", "reserves", "maintenance fund"],
            "key_fields": ["RPNR", "ANFSTAND", "ENDSTAND", "ZUF", "ENTN"],
            "german_variations": ["rücklage", "ruecklage", "instandhaltungsrücklage", "reserve"]
        },
        
        # Cost & Accounting Terms
        "betriebskosten": {
            "primary_table": "KONTEN",
            "description": "Betriebskosten nach BetrKV",
            "aliases": ["nebenkosten", "operating costs", "umlagen", "NK", "hausnebenkosten"],
            "key_fields": ["KNR", "KBEZ", "KKLASSE"],
            "german_variations": ["betriebskosten", "nebenkosten", "umlagen", "betriebskostenumlage"]
        },
        "heizkosten": {
            "primary_field": "BEWOHNER.Z4",
            "description": "Heizkosten nach HeizkostenV",
            "aliases": ["heizung", "heating costs", "heizkosten-vorauszahlung"],
            "related_table": "BEWOHNER", 
            "german_variations": ["heizkosten", "heizungskosten", "brennstoffkosten"]
        },
        "umlageschlüssel": {
            "primary_table": "KONTEN",
            "description": "Kostenumlage-Schlüssel",
            "aliases": ["allocation key", "verteilerschlüssel", "abrechnungsschlüssel"],
            "key_fields": ["UMLAGEBASIS", "UMLAGE_PROZENT"],
            "german_variations": ["umlageschlüssel", "verteilerschlüssel", "abrechnungsschlüssel"]
        },
        "nebenkostenabrechnung": {
            "primary_table": "KONTEN",
            "description": "Jährliche Nebenkostenabrechnung",
            "aliases": ["NK-abrechnung", "utility settlement", "betriebskostenabrechnung"],
            "key_fields": ["ABRECHNUNGSJAHR", "SOLL", "HABEN"],
            "german_variations": ["nebenkostenabrechnung", "betriebskostenabrechnung", "NK-abrechnung"]
        },
        
        # Market & Investment Terms
        "leerstand": {
            "primary_table": "WOHNUNG",
            "description": "Leere Wohneinheiten / Vacancy",
            "aliases": ["vacancy", "leere wohnung", "unvermietete einheit"],
            "key_fields": ["ENR", "LEERSTAND_SEIT", "LEERSTAND_GRUND"],
            "german_variations": ["leerstand", "leerstehend", "unvermietete wohnung"]
        },
        "vermietungsgrad": {
            "computed": "(VERMIETETE_EINHEITEN / GESAMT_EINHEITEN) * 100",
            "description": "Auslastungsgrad / Occupancy Rate",
            "aliases": ["auslastung", "occupancy rate", "belegungsgrad"],
            "german_variations": ["vermietungsgrad", "auslastungsgrad", "belegungsgrad"]
        },
        "mietausfall": {
            "computed": "SOLLMIETE - ISTMIETE",
            "description": "Verlust durch Leerstand / Rental Loss",
            "aliases": ["rental loss", "vacancy loss", "mietverlust"],
            "german_variations": ["mietausfall", "mietverlust", "ausfallmiete"]
        },
        "marktmiete": {
            "primary_field": "MARKTDATEN.MARKTMIETE",
            "description": "Ortsübliche Vergleichsmiete",
            "aliases": ["vergleichsmiete", "market rent", "ortsübliche miete"],
            "german_variations": ["marktmiete", "vergleichsmiete", "ortsübliche miete"]
        },
        
        # German Legal & Regulatory
        "mietpreisbremse": {
            "computed": "MARKTMIETE * 1.1",
            "description": "Mietpreisbremse-Obergrenze",
            "aliases": ["rent cap", "mietobergrenze", "preisbremse"],
            "german_variations": ["mietpreisbremse", "mietobergrenze", "preisbremse"]
        },
        "kündigungsschutz": {
            "computed": "CASE WHEN MIETDAUER_JAHRE >= 5 THEN 'VERSTÄRKT' ELSE 'STANDARD' END",
            "description": "Mieterschutz nach BGB",
            "aliases": ["tenant protection", "mieterschutz", "kündigungsfristen"],
            "german_variations": ["kündigungsschutz", "mieterschutz", "kündigungsfristen"]
        },
        "sozialwohnung": {
            "primary_field": "WOHNUNG.SOZIAL_GEBUNDEN",
            "description": "Sozial gebundene Wohnung",
            "aliases": ["social housing", "geförderte wohnung", "wbs-wohnung"],
            "german_variations": ["sozialwohnung", "geförderte wohnung", "wbs-wohnung"]
        },
        "wohnberechtigungsschein": {
            "primary_field": "MIETER.WBS_ERFORDERLICH",
            "description": "Wohnberechtigungsschein für Sozialwohnungen",
            "aliases": ["wbs", "housing permit", "sozialer wohnungsnachweis"],
            "german_variations": ["wohnberechtigungsschein", "wbs", "sozialer wohnungsnachweis"]
        },
        
        # Technology & Modern Terms
        "smart_home": {
            "primary_field": "WOHNUNG.SMART_HOME_AUSSTATTUNG",
            "description": "Intelligente Wohnungsausstattung",
            "aliases": ["intelligente wohnung", "smart apartment", "digitale ausstattung"],
            "german_variations": ["smart home", "intelligente wohnung", "digitale ausstattung"]
        },
        "energieausweis": {
            "primary_field": "OBJEKTE.ENERGIEAUSWEIS_KLASSE",
            "description": "Gebäude-Energieeffizienz-Ausweis",
            "aliases": ["energy certificate", "energieeffizienz", "verbrauchsausweis"],
            "german_variations": ["energieausweis", "energieeffizienzausweis", "verbrauchsausweis"]
        },
        "digitalisierung": {
            "computed": "CASE WHEN ONLINE_SERVICES + SMART_METER >= 2 THEN 'HOCH' ELSE 'NIEDRIG' END",
            "description": "Digitalisierungsgrad der Verwaltung",
            "aliases": ["digitalization", "digitale transformation", "online services"],
            "german_variations": ["digitalisierung", "digitale transformation", "online-verwaltung"]
        },
        
        # Sustainability & ESG
        "nachhaltigkeit": {
            "computed": "CASE WHEN ENERGIEEFFIZIENZ_KLASSE IN ('A+','A','B') THEN 'HOCH' ELSE 'NIEDRIG' END",
            "description": "Nachhaltigkeitsbewertung",
            "aliases": ["sustainability", "umweltfreundlichkeit", "green building"],
            "german_variations": ["nachhaltigkeit", "umweltfreundlichkeit", "ökologisch"]
        },
        "co2_fußabdruck": {
            "primary_field": "OBJEKTE.CO2_AUSSTOSS_JAEHRLICH",
            "description": "CO2-Ausstoß des Gebäudes",
            "aliases": ["carbon footprint", "co2 emissions", "klimabilanz"],
            "german_variations": ["co2-fußabdruck", "co2-ausstoß", "klimabilanz"]
        },
        
        # Quality & Performance
        "kundenzufriedenheit": {
            "computed": "(POSITIVE_BEWERTUNGEN / GESAMT_BEWERTUNGEN) * 100",
            "description": "Mieter-/Kundenzufriedenheit",
            "aliases": ["customer satisfaction", "tenant satisfaction", "bewertung"],
            "german_variations": ["kundenzufriedenheit", "mieterzufriedenheit", "zufriedenheitsgrad"]
        },
        "servicequalität": {
            "computed": "(REAKTIONSZEIT + LÖSUNGSQUOTE + FREUNDLICHKEIT) / 3",
            "description": "Qualität der Hausverwaltung",
            "aliases": ["service quality", "verwaltungsqualität", "betreuungsqualität"],
            "german_variations": ["servicequalität", "verwaltungsqualität", "betreuungsqualität"]
        },
        
        # Risk Management
        "ausfallrisiko": {
            "computed": "CASE WHEN MAHNSTUFE >= 2 AND SALDO < -1000 THEN 'HOCH' ELSE 'NIEDRIG' END",
            "description": "Risiko für Mietausfälle",
            "aliases": ["default risk", "zahlungsrisiko", "inkassorisiko"],
            "german_variations": ["ausfallrisiko", "zahlungsrisiko", "inkassorisiko"]
        },
        "investitionsrisiko": {
            "computed": "CASE WHEN GEBAEUDEALTER > 40 AND WARTUNGSRUECKSTAND > 10000 THEN 'HOCH' ELSE 'NIEDRIG' END",
            "description": "Risiko für hohe Investitionen",
            "aliases": ["investment risk", "sanierungsrisiko", "instandhaltungsrisiko"],
            "german_variations": ["investitionsrisiko", "sanierungsrisiko", "instandhaltungsrisiko"]
        }
    }

def get_additional_synonyms():
    """Additional German synonym mappings for common variations"""
    
    return {
        # Regional variations
        "erdgeschoss": ["parterre", "ebenerdig", "zu ebener erde"],
        "dachgeschoss": ["dachboden", "mansarde", "unter dem dach"],
        "keller": ["untergeschoss", "souterrain", "kellergeschoss"],
        
        # Professional terminology
        "hausgeld": ["wohngeld", "eigentümergeld", "wohngeldumlage"],
        "sondereigentum": ["teileigentum", "individuelles eigentum"],
        "gemeinschaftseigentum": ["gemeinsames eigentum", "allgemeineigentum"],
        
        # Financial variations
        "mietschulden": ["rückstände", "ausstände", "offene posten"],
        "vorauszahlung": ["abschlag", "akontozahlung", "anzahlung"],
        "abrechnung": ["jahresabrechnung", "endabrechnung", "kostenabrech"],
        
        # Legal variations
        "befristung": ["zeitbegrenzung", "laufzeitbegrenzung"],
        "unbefristet": ["auf unbestimmte zeit", "dauerhaft"],
        "ordentliche kündigung": ["reguläre kündigung", "fristgerechte kündigung"],
        "außerordentliche kündigung": ["fristlose kündigung", "sofortige kündigung"]
    }

def main():
    knowledge_base_path = "data/knowledge_base"
    vocab_file = Path(knowledge_base_path) / "business_vocabulary.json"
    
    print("🔄 Enhancing German Business Vocabulary...")
    
    # Load current vocabulary
    if vocab_file.exists():
        with open(vocab_file, 'r', encoding='utf-8') as f:
            current_vocab = json.load(f)
    else:
        current_vocab = {}
    
    initial_count = len([k for k, v in current_vocab.items() if not k.startswith('_')])
    print(f"📊 Current vocabulary terms: {initial_count}")
    
    # Get enhanced vocabulary
    enhanced_vocab = get_enhanced_german_vocabulary()
    additional_synonyms = get_additional_synonyms()
    
    # Merge vocabularies
    merged_vocab = {**current_vocab, **enhanced_vocab}
    
    # Add metadata
    merged_vocab["_metadata"] = {
        "description": "Comprehensive German Property Management Vocabulary",
        "last_updated": "2025-06-15",
        "coverage": "WEG law, property management, financial terms, legal compliance",
        "total_terms": len([k for k, v in merged_vocab.items() if not k.startswith('_')]),
        "categories": [
            "Core Business Entities", "Financial Terms", "WEG & Legal Terms",
            "Property Management", "Cost & Accounting", "Market & Investment",
            "German Legal & Regulatory", "Technology & Modern", "Sustainability & ESG",
            "Quality & Performance", "Risk Management"
        ]
    }
    
    merged_vocab["_synonyms"] = additional_synonyms
    
    final_count = len([k for k, v in merged_vocab.items() if not k.startswith('_')])
    new_additions = final_count - initial_count
    
    print(f"➕ Adding {new_additions} enhanced terms")
    print(f"📊 Final total: {final_count} vocabulary terms")
    
    # Save enhanced vocabulary
    with open(vocab_file, 'w', encoding='utf-8') as f:
        json.dump(merged_vocab, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 Enhanced Categories:")
    print(f"   • Core Business Entities: Extended aliases and variations")
    print(f"   • Financial Terms: Comprehensive rent, cost, and payment terminology")
    print(f"   • WEG & Legal Terms: Complete WEG law and governance vocabulary")
    print(f"   • Property Management: Professional management terminology")
    print(f"   • Cost & Accounting: BetrKV-compliant cost classifications")
    print(f"   • Market & Investment: Rental market and investment terminology")
    print(f"   • German Legal & Regulatory: BGB, rent control, social housing")
    print(f"   • Technology & Modern: Smart home, digitalization, energy efficiency")
    print(f"   • Sustainability & ESG: Environmental and sustainability terms")
    print(f"   • Quality & Performance: Satisfaction and service quality metrics")
    print(f"   • Risk Management: Financial and investment risk terminology")
    print(f"   • Regional Variations: Common German property terminology variations")
    
    print(f"\n✅ T12.003 COMPLETED: German business vocabulary enhanced to {final_count} terms")
    print(f"🎯 Quality Focus: Comprehensive German property management terminology achieved")

if __name__ == "__main__":
    main()