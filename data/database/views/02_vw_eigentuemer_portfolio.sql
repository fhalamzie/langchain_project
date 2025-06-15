-- ============================================================================
-- WINCASA Phase 2.1 - Core View: vw_eigentuemer_portfolio  
-- Business-optimierte Eigentümer-Sicht mit Portfolio-Übersicht
-- ============================================================================
/*
BUSINESS PURPOSE:
Eigentümer-Verwaltung mit automatischer Portfolio-Aggregation und Business-Context.
Löst Problem der separaten Objekt-Lookups und fehlenden Portfolio-Metriken.

ERSETZT PROBLEMATISCHE QUERIES:
- 01_eigentuemer.sql (zu detailliert für Overview)
- 13_weg_eigentuemer.sql (nur WEG-spezifisch)
- 15_eigentuemer_op.sql (missverständlicher Name)

TARGET USE CASES:
- Template: "Portfolio von Eigentümer [Name]"
- Template: "Eigentümer mit > X Objekten"
- RAG Lookup: Eigentümer-Kontaktdaten
- Template: "Größte Eigentümer nach Portfolio"

PERFORMANCE: Optimiert für NAME und PORTFOLIO Analysen
*/

CREATE VIEW vw_eigentuemer_portfolio AS
SELECT 
  -- === IDENTIFIKATION (Business-friendly) ===
  EIGADR.EIGNR,                           -- Eindeutige Eigentümer-ID
  CAST(
    CASE 
      WHEN EIGADR.EVNAME2 IS NOT NULL AND EIGADR.ENAME2 IS NOT NULL
      THEN EIGADR.EVNAME || ' ' || EIGADR.ENAME || ' & ' || EIGADR.EVNAME2 || ' ' || EIGADR.ENAME2
      ELSE EIGADR.EVNAME || ' ' || EIGADR.ENAME
    END AS VARCHAR(150)
  ) AS EIGENTUEMER_NAME,                  -- "Max Mustermann" oder "Max & Anna Mustermann"
  
  -- Firma vs. Privatperson
  CASE 
    WHEN EIGADR.EFIRMA = 'J' THEN 'Gewerblich'
    ELSE 'Privatperson'
  END AS EIGENTUEMER_TYP,
  EIGADR.EFIRMANAME AS FIRMENNAME,        -- NULL bei Privatpersonen
  
  -- === KONTAKTDATEN (Template-Ready) ===
  EIGADR.ESTR AS STRASSE,                 -- Eigentümer-Adresse  
  EIGADR.EPLZORT AS PLZ_ORT,              -- "45127 Essen"
  EIGADR.ETEL1 AS TELEFON,                -- Haupttelefonnummer
  EIGADR.EEMAIL AS EMAIL,                 -- E-Mail Adresse
  EIGADR.EHANDY AS HANDY,                 -- Mobile Nummer
  
  -- === BANKING (SEPA-Ready) ===
  EIGADR.EBANK AS BANK_NAME,              -- Hausbank
  EIGADR.EIBAN AS IBAN,                   -- SEPA-Kontonummer
  EIGADR.EBIC AS BIC,                     -- SWIFT-Code
  EIGADR.EKONTOINH AS KONTOINHABER,       -- Rechtlicher Kontoinhaber
  
  -- SEPA-Mandate Status
  CASE 
    WHEN EIGADR.SEPA_MAN_NR IS NOT NULL THEN 'Aktiv'
    ELSE 'Fehlend'
  END AS SEPA_MANDAT_STATUS,
  EIGADR.SEPA_MAN_DAT AS SEPA_MANDAT_DATUM,
  
  -- === PORTFOLIO-METRIKEN (Business Intelligence) ===
  COUNT(DISTINCT OBJEKTE.ONR) AS ANZAHL_OBJEKTE,           -- Anzahl verschiedene Gebäude
  COUNT(DISTINCT EIGENTUEMER.ONR || '-' || EIGENTUEMER.ENR) AS ANZAHL_EINHEITEN, -- Gesamte Wohnungen/Einheiten
  
  -- Portfolio-Wert Indikatoren
  SUM(COALESCE(OBJEKTE.GA1, 0)) AS GESAMTE_WOHNFLAECHE,    -- m² Wohnfläche total
  SUM(COALESCE(OBJEKTE.GA2, 0)) AS GESAMTE_GEWERBEFLAECHE, -- m² Gewerbefläche total
  
  -- Finanz-Metriken
  SUM(COALESCE(OBJEKTE.KTOSTAND, 0)) AS GESAMT_KONTOSTAND,     -- Summe aller Hausgeld-Konten
  SUM(COALESCE(OBJEKTE.RKTOSTAND, 0)) AS GESAMT_RUECKLAGEN,    -- Summe aller Rücklagen
  
  -- === PORTFOLIO-KLASSIFIKATION (für Templates) ===
  CASE 
    WHEN COUNT(DISTINCT OBJEKTE.ONR) >= 10 THEN 'Groß-Investor'
    WHEN COUNT(DISTINCT OBJEKTE.ONR) >= 5 THEN 'Portfolio-Eigentümer'  
    WHEN COUNT(DISTINCT OBJEKTE.ONR) >= 2 THEN 'Multi-Objekt'
    WHEN COUNT(DISTINCT OBJEKTE.ONR) = 1 THEN 'Einzel-Eigentümer'
    ELSE 'Kein Objekt'
  END AS PORTFOLIO_KATEGORIE,
  
  -- === OBJEKT-LISTE (für Details) ===
  STRING_AGG(OBJEKTE.OSTRASSE, '; ') AS OBJEKT_ADRESSEN,   -- "Bergstraße 15; Hauptstraße 20"
  STRING_AGG(OBJEKTE.OBEZ, ', ') AS OBJEKT_KUERZEL,        -- "RSWO, KUPFE190"
  
  -- === BUSINESS-STATUS ===
  CASE 
    WHEN EIGADR.EEMAIL IS NULL OR TRIM(EIGADR.EEMAIL) = '' THEN 'E-Mail fehlt'
    WHEN EIGADR.SEPA_MAN_NR IS NULL THEN 'SEPA-Mandat fehlt'
    WHEN COUNT(DISTINCT OBJEKTE.ONR) = 0 THEN 'Keine Objekte'
    ELSE 'Vollständig'
  END AS DATENVOLLSTAENDIGKEIT,
  
  -- === INTERNE REFERENZ ===
  EIGADR.ENOTIZ AS EIGENTUEMER_KUERZEL    -- Interne Codes wie "MJANZ", "RSWO"

FROM EIGADR
  LEFT JOIN EIGENTUEMER ON (EIGADR.EIGNR = EIGENTUEMER.EIGNR)
  LEFT JOIN OBJEKTE ON (EIGENTUEMER.ONR = OBJEKTE.ONR AND OBJEKTE.ONR < 890)  -- Exclude test data
WHERE 
  EIGADR.EIGNR <> -1                      -- Ausschluss kollektive WEG-Eigentümerschaft
  AND EIGADR.EIGNR > 0                    -- Nur gültige Eigentümer-IDs
GROUP BY 
  EIGADR.EIGNR,
  EIGADR.EVNAME, EIGADR.ENAME, EIGADR.EVNAME2, EIGADR.ENAME2,
  EIGADR.EFIRMA, EIGADR.EFIRMANAME,
  EIGADR.ESTR, EIGADR.EPLZORT, EIGADR.ETEL1, EIGADR.EEMAIL, EIGADR.EHANDY,
  EIGADR.EBANK, EIGADR.EIBAN, EIGADR.EBIC, EIGADR.EKONTOINH,
  EIGADR.SEPA_MAN_NR, EIGADR.SEPA_MAN_DAT, EIGADR.ENOTIZ
ORDER BY 
  ANZAHL_OBJEKTE DESC,                    -- Größte Portfolios zuerst
  EIGENTUEMER_NAME;

/*
EXPECTED RESULTS:
- ~311 Eigentümer mit Portfolio-Aggregation
- Self-contained Business-Context in jeder Zeile
- Portfolio-Klassifikation für Template-Routing
- SEPA-Status für Payment-Processing

TEMPLATE EXAMPLES:
1. "Portfolio von Eigentümer Schmidt"
   → WHERE EIGENTUEMER_NAME LIKE '%Schmidt%'

2. "Eigentümer mit mehr als 3 Objekten"  
   → WHERE ANZAHL_OBJEKTE > 3

3. "Größte Eigentümer nach Portfolio"
   → ORDER BY ANZAHL_OBJEKTE DESC LIMIT 10

4. "Eigentümer ohne E-Mail"
   → WHERE DATENVOLLSTAENDIGKEIT = 'E-Mail fehlt'

5. "Gewerbliche Eigentümer in Hamburg"
   → WHERE EIGENTUEMER_TYP = 'Gewerblich' AND PLZ_ORT LIKE '%Hamburg%'

INDEX RECOMMENDATIONS:
- EIGADR.ENAME + EIGADR.EVNAME (Name searches)
- EIGADR.EPLZORT (Location searches)
- EIGADR.EFIRMA (Type filtering)
- EIGENTUEMER.ONR (Portfolio aggregation)
*/