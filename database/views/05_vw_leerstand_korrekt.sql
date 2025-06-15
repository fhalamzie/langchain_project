-- ============================================================================
-- WINCASA Phase 2.1 - Core View: vw_leerstand_korrekt
-- KRITISCHER FIX: Korrekte Leerstand-Berechnung (ersetzt fehlerhafte Query 08)
-- ============================================================================
/*
BUSINESS PURPOSE:
🚨 CRITICAL FIX für Query 08_wohnungen_leerstand.sql
Die Original-Query hat eine FALSCHE LOGIK: "VENDE IS NULL" sind AKTIVE Mieter, nicht Leerstand!

PROBLEM IN ORIGINAL QUERY 08:
- WHERE VENDE IS NULL → Das sind aktive, unbefristete Mietverträge  
- Wurde fälschlicherweise als "Leerstand" interpretiert
- Führt zu komplett falschen Geschäftsentscheidungen!

KORREKTE LOGIK:
- Leerstand = Wohnungen OHNE aktiven Mietvertrag
- Aktiv = VENDE IS NULL (unbefristet) OR VENDE > CURRENT_DATE (befristet, aber noch gültig)
- Leer = Alle anderen Wohnungen

TARGET USE CASES:
- Template: "Freie Wohnungen in [Stadt]"
- Template: "Leerstandsquote von Objekt [Adresse]"
- RAG Lookup: Verfügbare Wohnungen
- Business Intelligence: Vermietungsgrad-Analyse

ERSETZT: 08_wohnungen_leerstand.sql (GEFÄHRLICH FALSCHE LOGIK!)
*/

CREATE VIEW vw_leerstand_korrekt AS
SELECT 
  -- === OBJEKT-INFORMATION ===
  OBJEKTE.ONR,
  OBJEKTE.OSTRASSE AS GEBAEUDE_ADRESSE,   -- "Bergstraße 15"
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- "RSWO"
  
  -- PLZ/Stadt für Template-Parameter
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
  
  -- === WOHNUNGS-INFORMATION ===
  WOHNUNG.ENR,                            -- Einheiten-Nummer
  WOHNUNG.EBEZ AS WOHNUNG_BEZEICHNUNG,    -- "1. OG rechts", "EG links"
  CAST(OBJEKTE.OSTRASSE || ', ' || WOHNUNG.EBEZ AS VARCHAR(200)) AS VOLLSTAENDIGE_ADRESSE,
  
  -- Wohnungsgröße (wenn verfügbar)
  COALESCE(WOHNUNG.GA1, 0) AS WOHNFLAECHE_QM,
  COALESCE(WOHNUNG.GA2, 0) AS NEBENFLAECHE_QM,
  
  -- === VERMIETUNGS-STATUS (KORREKTE LOGIK!) ===
  CASE 
    WHEN BEWOHNER.BEWNR IS NULL THEN 'LEER - Kein Mietvertrag'
    WHEN BEWOHNER.VENDE IS NULL THEN 'VERMIETET - Unbefristet'  
    WHEN BEWOHNER.VENDE > CURRENT_DATE THEN 'VERMIETET - Befristet bis ' || CAST(BEWOHNER.VENDE AS VARCHAR(10))
    WHEN BEWOHNER.VENDE <= CURRENT_DATE THEN 'LEER - Vertrag beendet am ' || CAST(BEWOHNER.VENDE AS VARCHAR(10))
    ELSE 'UNBEKANNT'
  END AS VERMIETUNGSSTATUS,
  
  -- Vereinfachter Status für Templates
  CASE 
    WHEN BEWOHNER.BEWNR IS NULL THEN 'LEER'
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN 'VERMIETET'
    ELSE 'LEER'
  END AS STATUS_EINFACH,
  
  -- === AKTUELLER MIETER (falls vorhanden) ===
  CASE 
    WHEN BEWOHNER.BEWNR IS NOT NULL AND (BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE)
    THEN CAST(BEWADR.BVNAME || ' ' || BEWADR.BNAME AS VARCHAR(100))
    ELSE NULL
  END AS AKTUELLER_MIETER,
  
  CASE 
    WHEN BEWOHNER.BEWNR IS NOT NULL AND (BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE)
    THEN BEWADR.BEMAIL
    ELSE NULL  
  END AS MIETER_EMAIL,
  
  CASE 
    WHEN BEWOHNER.BEWNR IS NOT NULL AND (BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE)
    THEN BEWADR.BTEL
    ELSE NULL
  END AS MIETER_TELEFON,
  
  -- === MIETVERTRAG-DETAILS (falls aktiv) ===
  BEWOHNER.VBEGINN AS MIETBEGINN,
  BEWOHNER.VENDE AS MIETENDE,
  
  -- Aktuelle Miete (falls vermietet)
  CASE 
    WHEN BEWOHNER.BEWNR IS NOT NULL AND (BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE)
    THEN COALESCE(BEWOHNER.Z1, 0) + COALESCE(BEWOHNER.Z2, 0) + 
         COALESCE(BEWOHNER.Z3, 0) + COALESCE(BEWOHNER.Z4, 0)
    ELSE NULL
  END AS AKTUELLE_WARMMIETE,
  
  -- === EIGENTÜMER-INFORMATION ===
  EIGADR.EIGNR,
  CAST(EIGADR.EVNAME || ' ' || EIGADR.ENAME AS VARCHAR(100)) AS EIGENTUEMER_NAME,
  EIGADR.ETEL1 AS EIGENTUEMER_TELEFON,
  EIGADR.EEMAIL AS EIGENTUEMER_EMAIL,
  
  -- === LEERSTAND-ANALYSE ===
  -- Wie lange ist die Wohnung bereits leer? (für Business Intelligence)
  CASE 
    WHEN BEWOHNER.BEWNR IS NULL THEN 'Nie vermietet'
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN NULL  -- Aktuell vermietet
    WHEN BEWOHNER.VENDE <= CURRENT_DATE 
    THEN CAST(EXTRACT(DAY FROM (CURRENT_DATE - BEWOHNER.VENDE)) AS VARCHAR(10)) || ' Tage'
    ELSE 'Unbekannt'
  END AS LEERSTAND_SEIT,
  
  -- Leerstand-Kategorisierung (für Prioritäts-Templates)
  CASE 
    WHEN BEWOHNER.BEWNR IS NULL THEN 'Nie vermietet'
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN 'Vermietet'
    WHEN BEWOHNER.VENDE <= CURRENT_DATE AND BEWOHNER.VENDE > CURRENT_DATE - 30 THEN 'Neu frei'
    WHEN BEWOHNER.VENDE <= CURRENT_DATE AND BEWOHNER.VENDE > CURRENT_DATE - 90 THEN 'Kurzer Leerstand'  
    WHEN BEWOHNER.VENDE <= CURRENT_DATE AND BEWOHNER.VENDE > CURRENT_DATE - 180 THEN 'Mittlerer Leerstand'
    WHEN BEWOHNER.VENDE <= CURRENT_DATE THEN 'Langer Leerstand'
    ELSE 'Unbekannt'
  END AS LEERSTAND_KATEGORIE

FROM OBJEKTE
  INNER JOIN WOHNUNG ON (OBJEKTE.ONR = WOHNUNG.ONR)
  LEFT JOIN BEWOHNER ON (WOHNUNG.ONR = BEWOHNER.ONR AND WOHNUNG.ENR = BEWOHNER.ENR)
  LEFT JOIN BEWADR ON (BEWOHNER.BEWNR = BEWADR.BEWNR)  
  INNER JOIN EIGADR ON (OBJEKTE.EIGNR = EIGADR.EIGNR)
WHERE
  OBJEKTE.ONR <> 0                        -- Ausschluss "Nicht zugeordnet"
  AND OBJEKTE.ONR < 890                   -- Ausschluss Test-/System-Objekte
ORDER BY 
  LEERSTAND_KATEGORIE DESC,               -- Problematische Leerstände zuerst
  OBJEKTE.OSTRASSE,
  WOHNUNG.EBEZ;

/*
EXPECTED RESULTS:
- Alle Wohnungen mit korrektem Vermietungsstatus
- ✅ Aktuell vermietete Wohnungen als "VERMIETET" (nicht als Leerstand!)
- ✅ Tatsächlich leere Wohnungen als "LEER"
- Business-Intelligence für Leerstand-Management

TEMPLATE EXAMPLES:
1. "Freie Wohnungen in Hamburg"
   → WHERE STADT = 'Hamburg' AND STATUS_EINFACH = 'LEER'

2. "Vermietungsgrad Bergstraße 15"  
   → WHERE GEBAEUDE_ADRESSE = 'Bergstraße 15'
   → Aggregate: COUNT(*) vs COUNT(CASE WHEN STATUS_EINFACH = 'VERMIETET' THEN 1 END)

3. "Längerer Leerstand (> 3 Monate)"
   → WHERE LEERSTAND_KATEGORIE IN ('Mittlerer Leerstand', 'Langer Leerstand')

4. "Kontakt zu Eigentümern mit Leerstand"
   → WHERE STATUS_EINFACH = 'LEER' AND EIGENTUEMER_EMAIL IS NOT NULL

5. "Neu freie Wohnungen (letzten 30 Tage)"
   → WHERE LEERSTAND_KATEGORIE = 'Neu frei'

CRITICAL VALIDATION:
Original Query 08 Problem:
❌ "WHERE VENDE IS NULL" → Aktive Mieter (falsch als Leerstand klassifiziert)
✅ "WHERE (VENDE IS NULL OR VENDE > CURRENT_DATE)" → Aktive Mieter (korrekt)  
✅ "WHERE VENDE <= CURRENT_DATE OR BEWOHNER IS NULL" → Echter Leerstand

INDEX RECOMMENDATIONS:
- BEWOHNER.VENDE (Status calculations)
- OBJEKTE.OPLZORT (City filtering)
- WOHNUNG.ONR + WOHNUNG.ENR (Join performance)
- OBJEKTE.OSTRASSE (Address searches)

BUSINESS IMPACT:
🚨 Behebt kritischen Fehler in Leerstand-Analyse
💰 Ermöglicht korrekte Vermietungs-KPIs
📊 Basis für verlässliche Business Intelligence
⚡ Template-ready für alle Leerstand-bezogenen Abfragen
*/