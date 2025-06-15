-- ============================================================================
-- WINCASA Phase 2.1 - Core View: vw_mieter_komplett
-- Business-optimierte Mieter-Sicht für Templates und RAG
-- ============================================================================
/*
BUSINESS PURPOSE: 
Vereinfachte Mieter-Abfrage mit allen relevanten Business-Kontexten in einer View.
Löst Problem der technischen IDs und fehlenden Kontexte aus Raw-Queries.

ERSETZT PROBLEMATISCHE QUERIES:
- 02_mieter.sql (zu komplex für einfache Suchen)
- 11_mieter_konten.sql (nur IDs ohne Namen)
- 03_aktuelle_mieter.sql (Status unklar)

TARGET USE CASES:
- Template: "Wer wohnt in [Adresse]?"
- Template: "Kontakt von Mieter [Name]"  
- RAG Lookup: Mieter-Informationen
- Template: "Mieter mit Zahlungsrückständen"

PERFORMANCE: Optimiert für ADDRESS und NAME Lookups
*/

CREATE VIEW vw_mieter_komplett AS
SELECT 
  -- === IDENTIFIKATION (Business-friendly) ===
  BEWADR.BEWNR,                           -- Eindeutige Mieter-ID
  CAST(BEWADR.BVNAME || ' ' || BEWADR.BNAME AS VARCHAR(100)) AS MIETER_NAME,  -- "Max Mustermann"
  CASE 
    WHEN BEWADR.BVNAME2 IS NOT NULL AND BEWADR.BNAME2 IS NOT NULL
    THEN CAST(BEWADR.BVNAME2 || ' ' || BEWADR.BNAME2 AS VARCHAR(100))
    ELSE NULL 
  END AS PARTNER_NAME,                    -- "Anna Mustermann" oder NULL
  
  -- === VOLLSTÄNDIGE ANSCHRIFT (Template-Ready) ===
  OBJEKTE.OSTRASSE AS GEBAEUDE_ADRESSE,   -- "Bergstraße 15" 
  WOHNUNG.EBEZ AS WOHNUNG,                -- "1. OG rechts"
  CAST(OBJEKTE.OSTRASSE || ', ' || WOHNUNG.EBEZ AS VARCHAR(200)) AS VOLLSTAENDIGE_ADRESSE, -- "Bergstraße 15, 1. OG rechts"
  
  -- Aufgeteilte PLZ/ORT für Template-Parameter
  CASE 
    WHEN POSITION(' ' IN OBJEKTE.OPLZORT) > 0 
    THEN SUBSTRING(OBJEKTE.OPLZORT FROM 1 FOR POSITION(' ' IN OBJEKTE.OPLZORT) - 1)
    ELSE OBJEKTE.OPLZORT
  END AS PLZ,
  CASE 
    WHEN POSITION(' ' IN OBJEKTE.OPLZORT) > 0 
    THEN TRIM(SUBSTRING(OBJEKTE.OPLZORT FROM POSITION(' ' IN OBJEKTE.OPLZORT) + 1))
    ELSE ''
  END AS STADT,
  
  -- === KONTAKTDATEN (Template-Ready) ===
  BEWADR.BTEL AS TELEFON,                 -- Haupttelefonnummer
  BEWADR.BEMAIL AS EMAIL,                 -- E-Mail Adresse
  BEWADR.BHANDY AS HANDY,                 -- Mobile Nummer
  
  -- === VERTRAGSSTATUS (Business Logic) ===
  BEWOHNER.VBEGINN AS MIETBEGINN,
  BEWOHNER.VENDE AS MIETENDE,
  CASE 
    WHEN BEWOHNER.VENDE IS NULL THEN 'Unbefristet'
    WHEN BEWOHNER.VENDE > CURRENT_DATE THEN 'Aktiv bis ' || CAST(BEWOHNER.VENDE AS VARCHAR(10))
    ELSE 'Beendet am ' || CAST(BEWOHNER.VENDE AS VARCHAR(10))
  END AS MIETSTATUS,
  
  -- Mietdauer in Jahren (für Templates wie "Mieter mit > 5 Jahre Mietdauer")
  CASE 
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE
    THEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, BEWOHNER.VBEGINN))
    ELSE EXTRACT(YEAR FROM AGE(BEWOHNER.VENDE, BEWOHNER.VBEGINN))
  END AS MIETDAUER_JAHRE,
  
  -- === FINANZIELLE SITUATION (Business Context) ===
  COALESCE(BEWOHNER.Z1, 0) + COALESCE(BEWOHNER.Z2, 0) + 
  COALESCE(BEWOHNER.Z3, 0) + COALESCE(BEWOHNER.Z4, 0) AS WARMMIETE_AKTUELL,
  BEWOHNER.Z1 AS KALTMIETE,
  BEWOHNER.Z3 AS BETRIEBSKOSTEN_VORAUSZAHLUNG,
  BEWOHNER.Z4 AS HEIZKOSTEN_VORAUSZAHLUNG,
  
  -- Kontosaldo mit Business-Context
  COALESCE(KONTEN.KBRUTTO, 0) AS KONTOSALDO,
  CASE 
    WHEN KONTEN.KBRUTTO > 10 THEN 'Rückstand'
    WHEN KONTEN.KBRUTTO BETWEEN -10 AND 10 THEN 'Ausgeglichen'  
    WHEN KONTEN.KBRUTTO < -10 THEN 'Guthaben'
    ELSE 'Unbekannt'
  END AS ZAHLUNGSSTATUS,
  
  -- === EIGENTÜMER-KONTEXT ===
  CAST(EIGADR.EVNAME || ' ' || EIGADR.ENAME AS VARCHAR(100)) AS EIGENTUEMER_NAME,
  EIGADR.ENOTIZ AS EIGENTUEMER_KUERZEL,   -- Für interne Referenz
  
  -- === TECHNISCHE REFERENZEN (für Joins) ===
  BEWOHNER.ONR,                           -- Objekt-Referenz
  BEWOHNER.ENR,                           -- Einheiten-Referenz
  BEWOHNER.KNR,                           -- Konto-Referenz
  OBJEKTE.EIGNR                           -- Eigentümer-Referenz

FROM BEWADR
  RIGHT OUTER JOIN BEWOHNER ON (BEWADR.BEWNR = BEWOHNER.BEWNR)
  LEFT OUTER JOIN WOHNUNG ON (BEWOHNER.ONR = WOHNUNG.ONR AND BEWOHNER.ENR = WOHNUNG.ENR)
  LEFT OUTER JOIN OBJEKTE ON (BEWOHNER.ONR = OBJEKTE.ONR)
  LEFT OUTER JOIN EIGADR ON (OBJEKTE.EIGNR = EIGADR.EIGNR)
  LEFT OUTER JOIN KONTEN ON (BEWOHNER.ONR = KONTEN.ONR 
                             AND BEWOHNER.KNR = KONTEN.KNR 
                             AND BEWOHNER.ENR = KONTEN.ENR
                             AND KONTEN.KUSCHLNR1 = -1)  -- Standard-Umlageschlüssel
WHERE
  BEWADR.BEWNR >= 0                       -- Gültige Mieter-IDs
  AND OBJEKTE.ONR < 890                   -- Ausschluss Test-Objekte
  AND (BEWOHNER.VENDE IS NULL             -- Unbefristete Verträge
       OR BEWOHNER.VENDE >= CURRENT_DATE  -- Oder noch nicht abgelaufene Verträge
      );

/*
EXPECTED RESULTS:
- ~189 aktive Mieter (basierend auf current data)
- Jede Zeile ist self-contained mit Business-Context
- Optimiert für Address-Lookups und Name-Searches
- Template-ready für alle Mieter-bezogenen Intents

TEMPLATE EXAMPLES:
1. "Wer wohnt in der Bergstraße 15?"
   → WHERE GEBAEUDE_ADRESSE LIKE '%Bergstraße 15%'

2. "Kontakt von Herrn Müller"  
   → WHERE MIETER_NAME LIKE '%Müller%'

3. "Mieter mit Zahlungsrückständen"
   → WHERE ZAHLUNGSSTATUS = 'Rückstand'

4. "Alle Mieter in Hamburg"
   → WHERE STADT = 'Hamburg'

INDEX RECOMMENDATIONS:
- OBJEKTE.OSTRASSE (Address lookups)
- BEWADR.BNAME + BEWADR.BVNAME (Name searches)  
- BEWOHNER.VENDE (Status filtering)
*/