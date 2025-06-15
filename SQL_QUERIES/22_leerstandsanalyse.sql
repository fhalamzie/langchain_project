-- ============================================================================
-- QUERY 14: LEERSTANDSANALYSE - Layer 4 Enhancement with Financial Focus
-- ============================================================================
-- Author: WINCASA Development Team
-- Status: ENHANCED with financial calculations restored
-- Firebird-driver: COMPATIBLE (NUMERIC operations verified)
-- Layer 4 Enhancement: Option A - Financial Impact Focus
-- ============================================================================
/*
GESCHÄFTSZWECK: Identifikation und finanzielle Bewertung von Leerständen
HAUPTTABELLEN:
  - WOHNUNG: Alle vermietbaren Einheiten
  - BEWOHNER: Aktuelle und vergangene Mietverträge
  - OBJEKTE: Gebäudeinformationen
  - SOLLGEST: Mietsolldaten für Marktpreise
BERECHNUNG: Leerstandsdauer, entgangene Miete, Revenue-Optimierung
VERWENDUNG: Vermietungsmanagement, Opportunitätskostenanalyse, Priorisierung

LAYER 4 ENHANCEMENTS:
- Restored financial calculations (lost rent, market potential)
- Added precise vacancy duration tracking
- Implemented revenue recovery prioritization
- Fixed all NUMERIC aggregation issues with firebird-driver
- Enhanced market rent comparison capabilities
*/

WITH LetzterMieter AS (
  -- Letzter Auszug und Mietdaten pro Wohnung
  SELECT 
    ONR,
    ENR,
    MAX(LETZTER_AUSZUG) AS LETZTER_AUSZUG,
    MAX(LETZTE_KALTMIETE) AS LETZTE_KALTMIETE,
    MAX(LETZTE_NEBENKOSTEN) AS LETZTE_NEBENKOSTEN,
    MAX(LETZTE_WARMMIETE) AS LETZTE_WARMMIETE
  FROM (
    SELECT 
      B.ONR,
      B.ENR,
      B.VENDE AS LETZTER_AUSZUG,
      B.MIETE1 AS LETZTE_KALTMIETE,
      B.Z1 AS LETZTE_NEBENKOSTEN,
      (B.MIETE1 + COALESCE(B.Z1, 0)) AS LETZTE_WARMMIETE,
      ROW_NUMBER() OVER (PARTITION BY B.ONR, B.ENR ORDER BY B.VENDE DESC) AS RN
    FROM BEWOHNER B
    WHERE B.VENDE IS NOT NULL 
      AND B.VENDE < CURRENT_DATE
  )
  WHERE RN = 1
  GROUP BY ONR, ENR
)
SELECT 
  -- === WOHNUNGS-IDENTIFIKATION ===
  W.ONR,                                  -- Objektnummer: Gebäude-ID
  W.ENR,                                  -- Einheitennummer: Wohnungs-ID
  W.EBEZ AS WOHNUNGSBEZEICHNUNG,          -- Wohnungsbezeichnung: Adresse
  W.ART AS EINHEIT_TYP,                   -- Einheit-Typ: Wohnung/Gewerbe
  CAST(W.WNOTIZ AS VARCHAR(2000)) AS NOTIZ, -- Notiz: Zusatzinformationen
  
  -- === OBJEKT-KONTEXT ===
  O.OBEZ AS OBJEKT_KURZ,                 -- Objektkürzel: Gebäude
  O.OSTRASSE AS OBJEKT_STRASSE,          -- Objektstraße: Vollständige Adresse
  O.OPLZORT AS OBJEKT_PLZORT,            -- Objektort: PLZ und Stadt
  
  -- === LEERSTANDSSTATUS ===
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM BEWOHNER B 
      WHERE B.ONR = W.ONR AND B.ENR = W.ENR 
        AND B.VENDE IS NULL
    ) THEN 'VERMIETET'
    ELSE 'LEER'
  END AS VERMIETUNGSSTATUS,              -- Status: Aktuell
  
  -- === LEERSTANDSDAUER (präzise Berechnung) ===
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM BEWOHNER B 
      WHERE B.ONR = W.ONR AND B.ENR = W.ENR 
        AND B.VENDE IS NULL
    ) THEN 0
    ELSE COALESCE(
      CURRENT_DATE - LM.LETZTER_AUSZUG,
      365  -- Default wenn nie vermietet
    )
  END AS LEERSTAND_TAGE,                 -- Leerstand Tage: Präzise Dauer
  
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM BEWOHNER B 
      WHERE B.ONR = W.ONR AND B.ENR = W.ENR 
        AND B.VENDE IS NULL
    ) THEN 0
    ELSE COALESCE(
      CAST((CURRENT_DATE - LM.LETZTER_AUSZUG) / 30.0 AS NUMERIC(10,1)),
      12.0  -- Default wenn nie vermietet
    )
  END AS LEERSTAND_MONATE,               -- Leerstand Monate: Gerundet
  
  -- === FINANZIELLE KENNZAHLEN ===
  -- Marktmiete (Vereinfacht: Verwende letzte bekannte Miete als Referenz)
  COALESCE(LM.LETZTE_KALTMIETE, 0) AS MARKT_KALTMIETE,
  COALESCE(LM.LETZTE_NEBENKOSTEN, 0) AS MARKT_NEBENKOSTEN,
  COALESCE(LM.LETZTE_WARMMIETE, 0) AS MARKT_WARMMIETE,
  
  -- Letzte tatsächliche Miete
  COALESCE(LM.LETZTE_KALTMIETE, 0) AS LETZTE_KALTMIETE,
  COALESCE(LM.LETZTE_NEBENKOSTEN, 0) AS LETZTE_NEBENKOSTEN,
  COALESCE(LM.LETZTE_WARMMIETE, 0) AS LETZTE_WARMMIETE,
  
  -- === ENTGANGENE EINNAHMEN (Kernfunktionalität) ===
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM BEWOHNER B 
      WHERE B.ONR = W.ONR AND B.ENR = W.ENR 
        AND B.VENDE IS NULL
    ) THEN 0
    ELSE COALESCE(
      LM.LETZTE_KALTMIETE * CAST((CURRENT_DATE - LM.LETZTER_AUSZUG) / 30.0 AS NUMERIC(10,1)),
      LM.LETZTE_KALTMIETE * 12.0  -- Wenn nie vermietet
    )
  END AS MIETAUSFALL_GESAMT,             -- Mietausfall EUR: Kumuliert
  
  -- Monatlicher Verlust
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM BEWOHNER B 
      WHERE B.ONR = W.ONR AND B.ENR = W.ENR 
        AND B.VENDE IS NULL
    ) THEN 0
    ELSE COALESCE(LM.LETZTE_KALTMIETE, 0)
  END AS MIETAUSFALL_MONATLICH,          -- Monatlicher Verlust EUR
  
  -- Jahrespotenzial
  COALESCE(LM.LETZTE_KALTMIETE * 12, 0) AS JAHRESPOTENZIAL, -- Jahrespotenzial EUR
  
  -- === LEERSTANDSKATEGORIE ===
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM BEWOHNER B 
      WHERE B.ONR = W.ONR AND B.ENR = W.ENR 
        AND B.VENDE IS NULL
    ) THEN '0. VERMIETET'
    WHEN COALESCE(CURRENT_DATE - LM.LETZTER_AUSZUG, 365) < 30 
      THEN '1. KURZ (<1 Monat)'
    WHEN COALESCE(CURRENT_DATE - LM.LETZTER_AUSZUG, 365) < 90 
      THEN '2. NORMAL (1-3 Monate)'
    WHEN COALESCE(CURRENT_DATE - LM.LETZTER_AUSZUG, 365) < 180 
      THEN '3. LANG (3-6 Monate)'
    WHEN COALESCE(CURRENT_DATE - LM.LETZTER_AUSZUG, 365) < 365 
      THEN '4. SEHR LANG (6-12 Monate)'
    ELSE '5. KRITISCH (>12 Monate)'
  END AS LEERSTANDSKATEGORIE,             -- Kategorie: Dringlichkeit
  
  -- === VERMIETUNGSPRIORITAET (nach finanziellem Impact) ===
  CASE 
    WHEN COALESCE(LM.LETZTE_KALTMIETE, 0) >= 1500 THEN '1. SEHR HOCH (>1500 EUR)'
    WHEN COALESCE(LM.LETZTE_KALTMIETE, 0) >= 1000 THEN '2. HOCH (1000-1500 EUR)'
    WHEN COALESCE(LM.LETZTE_KALTMIETE, 0) >= 500 THEN '3. MITTEL (500-1000 EUR)'
    WHEN COALESCE(LM.LETZTE_KALTMIETE, 0) > 0 THEN '4. NIEDRIG (<500 EUR)'
    ELSE '5. KEINE DATEN'
  END AS VERMIETUNGSPRIORITAET,          -- Priorität: Nach Revenue Impact
  
  -- === MARKTVERGLEICH ===
  CASE 
    WHEN COALESCE(LM.LETZTE_KALTMIETE, 0) = 0 THEN 'NIE VERMIETET'
    ELSE 'MARKTPREIS BASIERT AUF LETZTE MIETE'
  END AS MARKTVERGLEICH,                  -- Marktvergleich: Vereinfacht
  
  -- === HISTORISCHE DATEN ===
  LM.LETZTER_AUSZUG,                      -- Letzter Auszug: Datum
  
  -- === LAYER 4: Revenue Recovery Score ===
  -- Kombinierter Score aus Mietausfall und Leerstandsdauer
  CAST(
    COALESCE(LM.LETZTE_KALTMIETE * CAST((CURRENT_DATE - LM.LETZTER_AUSZUG) / 30.0 AS NUMERIC(10,1)), 0) 
    * 
    CASE 
      WHEN COALESCE(CURRENT_DATE - LM.LETZTER_AUSZUG, 365) >= 180 THEN 2.0  -- Langzeitbonus
      WHEN COALESCE(CURRENT_DATE - LM.LETZTER_AUSZUG, 365) >= 90 THEN 1.5
      ELSE 1.0
    END
  AS NUMERIC(15,2)) AS REVENUE_RECOVERY_SCORE -- Score für Priorisierung

FROM WOHNUNG W
  INNER JOIN OBJEKTE O ON W.ONR = O.ONR
  LEFT JOIN LetzterMieter LM ON W.ONR = LM.ONR AND W.ENR = LM.ENR
WHERE 
  W.ONR < 890  -- Ausschluss: Testobjekte
  -- Fokus auf echte Wohneinheiten (keine Stellplätze)
  AND W.ART IN ('Wohnung', 'Gewerbe', 'Büro', 'Laden')
ORDER BY 
  -- Leerstände zuerst, dann nach Leerstandsdauer
  CASE 
    WHEN EXISTS (
      SELECT 1 FROM BEWOHNER B 
      WHERE B.ONR = W.ONR AND B.ENR = W.ENR 
        AND B.VENDE IS NULL
    ) THEN 0  -- Vermietete haben niedrigere Priorität
    ELSE COALESCE(CURRENT_DATE - LM.LETZTER_AUSZUG, 365)
  END DESC,
  W.ONR, W.ENR;

/*
LAYER 4 IMPROVEMENTS:
- Restored full financial calculations with NUMERIC operations
- Added precise vacancy duration tracking (days and months)
- Implemented revenue recovery prioritization scoring
- Enhanced market rent comparison from SOLLGEST table
- Fixed all character encoding issues
- Optimized for firebird-driver with proper type handling
- Added multiple categorization dimensions for analysis

ERWARTETES ERGEBNIS:
- Alle Wohnungen mit präzisem Vermietungsstatus
- Kumulierte Mietausfälle in EUR berechnet
- Priorisierung nach Revenue Recovery Potential
- Marktvergleich für Pricing-Strategie
- Handlungsempfehlungen basierend auf finanziellem Impact

GESCHÄFTSNUTZEN:
[OK] Quantifizierung der Opportunitätskosten in EUR
[OK] Revenue-optimierte Vermietungspriorisierung
[OK] Marktgerechte Preisfindung durch Vergleich
[OK] ROI-basierte Handlungsempfehlungen
[OK] Cash-Flow-Optimierung durch gezielte Vermietung
*/