-- ============================================================================
-- WINCASA Phase 2.1 - Core View: vw_finanzen_uebersicht
-- Business-optimierte Finanz-Sicht mit Kontext-Anreicherung
-- ============================================================================
/*
BUSINESS PURPOSE:
Löst Problem der technischen Konten-IDs ohne Business-Context.
Vereint Mieter-Konten, Eigentümer-Konten und Bank-Konten mit Namen und Adressen.

ERSETZT PROBLEMATISCHE QUERIES:
- 11_mieter_konten.sql (nur IDs ohne Namen)
- 12_bank_konten.sql (nur Kontonummern ohne Inhaber)
- 25_objektbezogene_sachkonten.sql (keine Objektzuordnung)

TARGET USE CASES:
- Template: "Kontosalden aller Mieter"
- Template: "Bankkonten von Eigentümer [Name]"  
- RAG Lookup: Finanz-Status von Personen/Objekten
- Template: "Rückstände nach Objekt"

CRITICAL FIX: Business-Context zu allen Finanz-Daten
*/

CREATE VIEW vw_finanzen_uebersicht AS
SELECT 
  -- === KONTOIDENTIFIKATION (Business-friendly) ===
  KONTEN.ONR,                             -- Objekt-Referenz
  KONTEN.KNR,                             -- Konto-Nummer  
  KONTEN.ENR,                             -- Einheiten-Referenz
  KONTEN.KKLASSE,                         -- Konten-Klasse (62 = WEG-Eigentümer, etc.)
  
  -- === KONTOINHABER-INFORMATION ===
  CASE 
    WHEN KONTEN.KKLASSE = 62 THEN 'WEG-Eigentümer'      -- WEG-Verwaltung
    WHEN BEWADR.BEWNR IS NOT NULL THEN 'Mieter'         -- Mieter-Konto
    WHEN EIGADR.EIGNR IS NOT NULL THEN 'Eigentümer'     -- Eigentümer-Konto  
    ELSE 'Unbekannt'
  END AS KONTOTYP,
  
  -- Namen je nach Kontoinhaber-Typ
  CASE 
    WHEN BEWADR.BEWNR IS NOT NULL 
    THEN CAST(BEWADR.BVNAME || ' ' || BEWADR.BNAME AS VARCHAR(100))
    WHEN EIGADR.EIGNR IS NOT NULL 
    THEN CAST(EIGADR.EVNAME || ' ' || EIGADR.ENAME AS VARCHAR(100))
    ELSE 'System-Konto'
  END AS KONTOINHABER_NAME,
  
  -- === OBJEKT-KONTEXT (für Zuordnung) ===
  OBJEKTE.OSTRASSE AS GEBAEUDE_ADRESSE,   -- "Bergstraße 15"
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- "RSWO"
  CASE 
    WHEN WOHNUNG.EBEZ IS NOT NULL THEN WOHNUNG.EBEZ
    ELSE 'Objekt-Gesamt'
  END AS EINHEIT_BEZEICHNUNG,             -- "1. OG rechts" oder "Objekt-Gesamt"
  
  -- Vollständige Adressierung für Templates
  CAST(OBJEKTE.OSTRASSE || 
    CASE WHEN WOHNUNG.EBEZ IS NOT NULL THEN ', ' || WOHNUNG.EBEZ ELSE '' END 
    AS VARCHAR(200)) AS VOLLSTAENDIGE_ADRESSE,
  
  -- === FINANZ-DATEN (Business Context) ===
  KONTEN.KBRUTTO AS KONTOSALDO,           -- Aktueller Saldo
  KONTEN.KSOLL AS SOLL_BETRAG,           -- Soll-Buchungen  
  KONTEN.KHABEN AS HABEN_BETRAG,         -- Haben-Buchungen
  
  -- Saldo-Bewertung (für Templates)
  CASE 
    WHEN KONTEN.KBRUTTO > 100 THEN 'Schulden'
    WHEN KONTEN.KBRUTTO BETWEEN -10 AND 10 THEN 'Ausgeglichen'
    WHEN KONTEN.KBRUTTO < -100 THEN 'Guthaben'  
    WHEN KONTEN.KBRUTTO BETWEEN 10 AND 100 THEN 'Geringfügige Schulden'
    WHEN KONTEN.KBRUTTO BETWEEN -100 AND -10 THEN 'Geringfügiges Guthaben'
    ELSE 'Neutral'
  END AS SALDO_BEWERTUNG,
  
  -- Kritikalitäts-Einstufung (für Prioritätentemplates)
  CASE 
    WHEN KONTEN.KBRUTTO > 1000 THEN 'Kritisch'
    WHEN KONTEN.KBRUTTO > 500 THEN 'Hoch'
    WHEN KONTEN.KBRUTTO > 100 THEN 'Mittel'
    WHEN KONTEN.KBRUTTO BETWEEN -100 AND 100 THEN 'Normal'
    ELSE 'Niedrig'
  END AS PRIORITAET,
  
  -- === BANKING-INFORMATION (wenn verfügbar) ===
  CASE 
    WHEN BEWADR.BEWNR IS NOT NULL THEN BEWADR.BBANK    -- Mieter-Bank
    WHEN EIGADR.EIGNR IS NOT NULL THEN EIGADR.EBANK    -- Eigentümer-Bank
    ELSE NULL
  END AS BANK_NAME,
  
  CASE 
    WHEN BEWADR.BEWNR IS NOT NULL THEN BEWADR.BIBAN    -- Mieter-IBAN
    WHEN EIGADR.EIGNR IS NOT NULL THEN EIGADR.EIBAN    -- Eigentümer-IBAN
    ELSE NULL
  END AS IBAN,
  
  -- === KONTAKT-INFORMATION (für Mahnung/Rückzahlung) ===
  CASE 
    WHEN BEWADR.BEWNR IS NOT NULL THEN BEWADR.BEMAIL   -- Mieter-E-Mail
    WHEN EIGADR.EIGNR IS NOT NULL THEN EIGADR.EEMAIL   -- Eigentümer-E-Mail
    ELSE NULL
  END AS EMAIL,
  
  CASE 
    WHEN BEWADR.BEWNR IS NOT NULL THEN BEWADR.BTEL     -- Mieter-Telefon
    WHEN EIGADR.EIGNR IS NOT NULL THEN EIGADR.ETEL1    -- Eigentümer-Telefon
    ELSE NULL
  END AS TELEFON,
  
  -- === ADMINISTRATIVE INFO ===
  BEWADR.BEWNR AS MIETER_ID,              -- NULL wenn kein Mieter-Konto
  EIGADR.EIGNR AS EIGENTUEMER_ID,         -- NULL wenn kein Eigentümer-Konto
  KONTEN.KUSCHLNR1 AS UMLAGESCHLUESSEL,   -- -1 = Standard
  
  -- Konto-Status für Business Logic
  CASE 
    WHEN KONTEN.KBRUTTO = 0 THEN 'Ausgeglichen'
    WHEN KONTEN.KBRUTTO > 0 AND BEWADR.BEWNR IS NOT NULL THEN 'Mieter-Schulden'
    WHEN KONTEN.KBRUTTO > 0 AND EIGADR.EIGNR IS NOT NULL THEN 'Eigentümer-Schulden'
    WHEN KONTEN.KBRUTTO < 0 AND BEWADR.BEWNR IS NOT NULL THEN 'Mieter-Guthaben'
    WHEN KONTEN.KBRUTTO < 0 AND EIGADR.EIGNR IS NOT NULL THEN 'Eigentümer-Guthaben'
    ELSE 'System-Konto'
  END AS KONTO_STATUS

FROM KONTEN
  LEFT JOIN OBJEKTE ON (KONTEN.ONR = OBJEKTE.ONR AND OBJEKTE.ONR < 890)  -- Exclude test objects
  LEFT JOIN WOHNUNG ON (KONTEN.ONR = WOHNUNG.ONR AND KONTEN.ENR = WOHNUNG.ENR)
  LEFT JOIN BEWOHNER ON (KONTEN.ONR = BEWOHNER.ONR 
                         AND KONTEN.KNR = BEWOHNER.KNR 
                         AND KONTEN.ENR = BEWOHNER.ENR)
  LEFT JOIN BEWADR ON (BEWOHNER.BEWNR = BEWADR.BEWNR)
  LEFT JOIN EIGENTUEMER ON (KONTEN.ONR = EIGENTUEMER.ONR AND KONTEN.ENR = EIGENTUEMER.ENR)
  LEFT JOIN EIGADR ON (EIGENTUEMER.EIGNR = EIGADR.EIGNR OR OBJEKTE.EIGNR = EIGADR.EIGNR)
WHERE
  KONTEN.ONR < 890                        -- Ausschluss Test-Konten
  AND (KONTEN.KBRUTTO <> 0                -- Nur Konten mit Bewegung
       OR KONTEN.KKLASSE = 62)            -- Oder WEG-Konten (auch bei 0)
ORDER BY 
  ABS(KONTEN.KBRUTTO) DESC,               -- Höchste Beträge zuerst
  OBJEKTE.OSTRASSE,
  KONTOINHABER_NAME;

/*
EXPECTED RESULTS:
- ~500-1000 Konten mit Business-Context
- Jede Zeile self-contained mit Namen und Adressen
- Banking-Info für SEPA-Verarbeitung verfügbar
- Korrekte Objekt-Zuordnung für alle Sachkonten

TEMPLATE EXAMPLES:
1. "Kontosalden aller Mieter"
   → WHERE KONTOTYP = 'Mieter'

2. "Rückstände in Bergstraße 15"  
   → WHERE GEBAEUDE_ADRESSE = 'Bergstraße 15' AND SALDO_BEWERTUNG = 'Schulden'

3. "Kritische Kontostände"
   → WHERE PRIORITAET = 'Kritisch'

4. "Bankkonten von Eigentümer Schmidt"
   → WHERE KONTOTYP = 'Eigentümer' AND KONTOINHABER_NAME LIKE '%Schmidt%' AND IBAN IS NOT NULL

5. "WEG-Konten mit Guthaben"
   → WHERE KKLASSE = 62 AND SALDO_BEWERTUNG = 'Guthaben'

BUSINESS VALUE:
- Löst Problem der ID-only Exports
- Ermöglicht direkte Finanz-Templates ohne Joins
- Banking-Integration für Payment-Processing
- Objekt-Zuordnung für Kostenstellen-Rechnung

INDEX RECOMMENDATIONS:
- KONTEN.ONR + KONTEN.KNR + KONTEN.ENR (Primary lookups)
- KONTEN.KBRUTTO (Amount-based filtering)
- KONTEN.KKLASSE (Type-based filtering)
- OBJEKTE.OSTRASSE (Address-based grouping)
*/