-- ============================================================================
-- WINCASA Phase 2.1 - Core View: vw_objekte_details
-- Business-optimierte Objekt-Sicht mit Vermietungs- und Finanz-Status
-- ============================================================================
/*
BUSINESS PURPOSE:
Vollständige Objektverwaltung mit Vermietungsgrad, Finanz-Status und Verwalter-Info.
Löst kritisches Problem der falschen Leerstand-Analyse aus Query 08.

ERSETZT PROBLEMATISCHE QUERIES:
- 05_objekte.sql (zu technisch)
- 08_wohnungen_leerstand.sql (FALSCHE LOGIK!)
- 06_objekte_portfolio.sql (fehlender Context)

TARGET USE CASES:
- Template: "Objekte in [Stadt]"
- Template: "Vermietungsgrad von Objekt [Adresse]"
- RAG Lookup: Objektdaten und Status
- Template: "Objekte mit Leerstand"

CRITICAL FIX: Korrekte Leerstand-Berechnung
*/

CREATE VIEW vw_objekte_details AS
SELECT 
  -- === IDENTIFIKATION (Business-friendly) ===
  OBJEKTE.ONR,                            -- Eindeutige Objekt-ID
  OBJEKTE.OSTRASSE AS GEBAEUDE_ADRESSE,   -- "Bergstraße 15"
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- "RSWO", "KUPFE190"
  
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
  
  -- === TECHNISCHE DATEN (Business Context) ===
  OBJEKTE.OANZEINH AS ANZAHL_EINHEITEN_TOTAL,  -- Gesamte Wohnungen im Gebäude
  COALESCE(OBJEKTE.GA1, 0) AS WOHNFLAECHE_QM,  -- Gesamte Wohnfläche m²
  COALESCE(OBJEKTE.GA2, 0) AS GEWERBEFLAECHE_QM, -- Gewerbefläche m²
  OBJEKTE.ART AS OBJEKTART,                     -- "Wohnhaus", "Mischnutzung"
  
  -- === VERMIETUNGS-STATUS (KORREKTE BERECHNUNG!) ===
  -- Problem Query 08 lösen: Echte Leerstand-Logik
  COUNT(CASE 
    WHEN BEWOHNER.VENDE IS NULL                    -- Unbefristeter aktiver Vertrag
         OR BEWOHNER.VENDE > CURRENT_DATE          -- Oder befristeter aber noch gültiger Vertrag
    THEN 1 
  END) AS EINHEITEN_VERMIETET,
  
  (OBJEKTE.OANZEINH - COUNT(CASE 
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE 
    THEN 1 
  END)) AS EINHEITEN_LEERSTAND,
  
  -- Vermietungsgrad in Prozent (Business-KPI)
  CASE 
    WHEN OBJEKTE.OANZEINH > 0 
    THEN ROUND(
      (COUNT(CASE WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN 1 END) * 100.0) 
      / OBJEKTE.OANZEINH, 1)
    ELSE 0
  END AS VERMIETUNGSGRAD_PROZENT,
  
  -- Leerstand-Kategorisierung (für Templates)
  CASE 
    WHEN OBJEKTE.OANZEINH = 0 THEN 'Keine Einheiten'
    WHEN COUNT(CASE WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN 1 END) = OBJEKTE.OANZEINH 
         THEN 'Vollvermietet'
    WHEN COUNT(CASE WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN 1 END) = 0 
         THEN 'Komplett leer'
    ELSE 'Teilvermietet'
  END AS VERMIETUNGSSTATUS,
  
  -- === FINANZ-STATUS (Business Intelligence) ===
  COALESCE(OBJEKTE.KTOSTAND, 0) AS HAUSGELD_KONTOSTAND,     -- Aktueller Kontostand
  COALESCE(OBJEKTE.RKTOSTAND, 0) AS RUECKLAGEN_KONTOSTAND,  -- Rücklagen-Saldo
  OBJEKTE.KTOASTAND AS KONTOSTAND_DATUM,                    -- Stand-Datum
  OBJEKTE.RKTOASTAND AS RUECKLAGEN_DATUM,                   -- Rücklagen Stand-Datum
  
  -- Finanz-Status Bewertung
  CASE 
    WHEN OBJEKTE.KTOSTAND > 5000 THEN 'Hohes Guthaben'
    WHEN OBJEKTE.KTOSTAND > 1000 THEN 'Positiv'
    WHEN OBJEKTE.KTOSTAND BETWEEN -1000 AND 1000 THEN 'Ausgeglichen'
    WHEN OBJEKTE.KTOSTAND < -5000 THEN 'Kritisch'
    ELSE 'Negativ'
  END AS FINANZSTATUS,
  
  -- === VERWALTER-INFORMATION (Business Context) ===
  OBJEKTE.VERWNAME AS VERWALTER_NAME,          -- Ansprechpartner
  OBJEKTE.VERWFIRMA AS VERWALTER_FIRMA,        -- Verwaltungsunternehmen
  OBJEKTE.VERWTEL AS VERWALTER_TELEFON,        -- Kontakt
  OBJEKTE.VERWEMAIL AS VERWALTER_EMAIL,        -- E-Mail
  
  -- Verwaltungsperiode Status
  CASE 
    WHEN OBJEKTE.VERWALTUNGSENDE IS NULL THEN 'Unbefristet'
    WHEN OBJEKTE.VERWALTUNGSENDE > CURRENT_DATE THEN 'Aktiv bis ' || CAST(OBJEKTE.VERWALTUNGSENDE AS VARCHAR(10))
    ELSE 'Beendet am ' || CAST(OBJEKTE.VERWALTUNGSENDE AS VARCHAR(10))
  END AS VERWALTUNGSSTATUS,
  
  -- === EIGENTÜMER-KONTEXT ===
  EIGADR.EIGNR,                                -- Eigentümer-ID
  CAST(EIGADR.EVNAME || ' ' || EIGADR.ENAME AS VARCHAR(100)) AS EIGENTUEMER_NAME,
  CASE 
    WHEN EIGADR.EFIRMA = 'J' THEN 'Gewerblich'
    ELSE 'Privatperson'  
  END AS EIGENTUEMER_TYP,
  EIGADR.ENOTIZ AS EIGENTUEMER_KUERZEL,        -- Interne Referenz
  
  -- === MIETEINNAHMEN (Geschätzt basierend auf aktiven Verträgen) ===
  SUM(CASE 
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE
    THEN COALESCE(BEWOHNER.Z1, 0) + COALESCE(BEWOHNER.Z2, 0) + 
         COALESCE(BEWOHNER.Z3, 0) + COALESCE(BEWOHNER.Z4, 0)
    ELSE 0
  END) AS MIETEINNAHMEN_MONATLICH,
  
  -- === OBJEKTBESCHREIBUNG ===
  SUBSTRING(COALESCE(OBJEKTE.FRINH1, '') FROM 1 FOR 200) AS OBJEKTBESCHREIBUNG

FROM OBJEKTE
  INNER JOIN EIGADR ON (OBJEKTE.EIGNR = EIGADR.EIGNR)
  LEFT JOIN WOHNUNG ON (OBJEKTE.ONR = WOHNUNG.ONR)
  LEFT JOIN BEWOHNER ON (WOHNUNG.ONR = BEWOHNER.ONR AND WOHNUNG.ENR = BEWOHNER.ENR)
WHERE
  OBJEKTE.ONR <> 0                        -- Ausschluss "Nicht zugeordnet"
  AND OBJEKTE.ONR < 890                   -- Ausschluss Test-/System-Objekte
GROUP BY 
  OBJEKTE.ONR, OBJEKTE.OSTRASSE, OBJEKTE.OBEZ, OBJEKTE.OPLZORT,
  OBJEKTE.OANZEINH, OBJEKTE.GA1, OBJEKTE.GA2, OBJEKTE.ART,
  OBJEKTE.KTOSTAND, OBJEKTE.RKTOSTAND, OBJEKTE.KTOASTAND, OBJEKTE.RKTOASTAND,
  OBJEKTE.VERWNAME, OBJEKTE.VERWFIRMA, OBJEKTE.VERWTEL, OBJEKTE.VERWEMAIL,
  OBJEKTE.VERWALTUNGSENDE, OBJEKTE.FRINH1,
  EIGADR.EIGNR, EIGADR.EVNAME, EIGADR.ENAME, EIGADR.EFIRMA, EIGADR.ENOTIZ
ORDER BY 
  VERMIETUNGSGRAD_PROZENT ASC,            -- Problematische Objekte zuerst
  OBJEKTE.OSTRASSE;

/*
EXPECTED RESULTS:
- ~77 Objekte mit korrektem Vermietungsstatus
- Korrekte Leerstand-Berechnung (fixes Query 08 Problem!)
- Business-ready Finanz- und Vermietungs-KPIs
- Self-contained mit Eigentümer- und Verwalter-Context

TEMPLATE EXAMPLES:
1. "Objekte in Hamburg"
   → WHERE STADT = 'Hamburg'

2. "Vermietungsgrad von Bergstraße 15"  
   → WHERE GEBAEUDE_ADRESSE = 'Bergstraße 15'

3. "Objekte mit Leerstand"
   → WHERE VERMIETUNGSSTATUS IN ('Teilvermietet', 'Komplett leer')

4. "Vollvermietete Objekte"
   → WHERE VERMIETUNGSSTATUS = 'Vollvermietet'

5. "Finanziell kritische Objekte"
   → WHERE FINANZSTATUS = 'Kritisch'

CRITICAL FIX VALIDATION:
Query 08 Problem: 
- ALT: "VENDE IS NULL" = AKTIVE Mieter (falsch als "Leerstand" interpretiert)
- NEU: "VENDE IS NULL OR VENDE > CURRENT_DATE" = Aktive Verträge
- Leerstand = Total - Aktive (korrekte Berechnung)

INDEX RECOMMENDATIONS:
- OBJEKTE.OSTRASSE (Address searches)
- OBJEKTE.OPLZORT (City searches)  
- BEWOHNER.VENDE (Status calculations)
- OBJEKTE.ONR (Join performance)
*/