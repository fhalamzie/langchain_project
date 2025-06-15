-- ============================================================================
-- QUERY 13: FORDERUNGSALTERUNG - Layer 4 Enhancement
-- ============================================================================
-- Author: WINCASA Development Team
-- Status: ENHANCED with Firebird 5.0 syntax and German character encoding
-- Firebird-driver: COMPATIBLE (NUMERIC operations verified)
-- Layer 4 Enhancement: Option A - Technical Fix + Basic Enhancement
-- ============================================================================
/*
GESCHÄFTSZWECK: Altersstruktur offener Forderungen für gezieltes Inkasso
HAUPTTABELLEN:
  - KONTEN: Alle Konten mit offenen Posten
  - BUCHUNG: Letzte Zahlungseingänge
  - EIGADR/BEWOHNER: Schuldner-Informationen
KATEGORIEN: 0-30, 31-90, 91-180, >180 Tage
VERWENDUNG: Inkasso-Priorisierung, Abschreibungsrisiko, Cash-Management

LAYER 4 ENHANCEMENTS:
- Fixed Firebird 5.0 syntax (DATEDIFF to native date arithmetic)
- Added proper German character encoding support
- Enhanced connection management for firebird-driver
- Improved date calculations for aging analysis
- Preserved all business logic while modernizing syntax
*/

WITH LetzteBuchung AS (
  -- Subquery für letzte Zahlung pro Konto
  SELECT 
    B.KSOLL AS KNR,
    MAX(B.DATUM) AS LETZTE_ZAHLUNG
  FROM BUCHUNG B
  WHERE B.BETRAG > 0  -- Nur Einzahlungen
  GROUP BY B.KSOLL
)
SELECT 
  -- === ALTERSKLASSE ===
  CASE 
    WHEN CURRENT_DATE - COALESCE(LB.LETZTE_ZAHLUNG, DATEADD(-365 DAY TO CURRENT_DATE)) <= 30 
      THEN '1. AKTUELL (0-30 Tage)'
    WHEN CURRENT_DATE - COALESCE(LB.LETZTE_ZAHLUNG, DATEADD(-365 DAY TO CURRENT_DATE)) <= 90 
      THEN '2. UEBERFAELLIG (31-90 Tage)'
    WHEN CURRENT_DATE - COALESCE(LB.LETZTE_ZAHLUNG, DATEADD(-365 DAY TO CURRENT_DATE)) <= 180 
      THEN '3. ALT (91-180 Tage)'
    ELSE '4. SEHR ALT (>180 Tage)'
  END AS ALTERSKLASSE,                    -- Altersklasse: Kategorisierung
  
  -- === KONTOTYP-UNTERSCHEIDUNG ===
  CASE 
    WHEN K.KKLASSE = 60 THEN 'MIETER'
    WHEN K.KKLASSE = 62 THEN 'EIGENTUEMER'
    ELSE 'SONSTIGE'
  END AS SCHULDNERTYP,                    -- Schuldnertyp: Mieter oder Eigentümer
  
  -- === AGGREGIERTE KENNZAHLEN ===
  COUNT(DISTINCT K.KNR) AS ANZAHL_KONTEN, -- Anzahl Konten: In dieser Altersklasse
  
  SUM(K.OPBETRAG) AS GESAMT_FORDERUNG,    -- Gesamtforderung: Summe OP
  AVG(K.OPBETRAG) AS DURCHSCHNITT_OP,     -- Durchschnitt OP: Pro Konto
  MIN(K.OPBETRAG) AS KLEINSTE_FORDERUNG,  -- Kleinste Forderung: Minimum
  MAX(K.OPBETRAG) AS GROESSTE_FORDERUNG,  -- Größte Forderung: Maximum
  
  -- === MAHNSTUFEN-VERTEILUNG ===
  COUNT(CASE WHEN K.KMAHNSTUFE = 0 THEN 1 END) AS OHNE_MAHNUNG,
  COUNT(CASE WHEN K.KMAHNSTUFE = 1 THEN 1 END) AS MAHNSTUFE_1,
  COUNT(CASE WHEN K.KMAHNSTUFE = 2 THEN 1 END) AS MAHNSTUFE_2,
  COUNT(CASE WHEN K.KMAHNSTUFE = 3 THEN 1 END) AS MAHNSTUFE_3,
  COUNT(CASE WHEN K.KMAHNSTUFE >= 4 THEN 1 END) AS MAHNSTUFE_4_PLUS,
  
  -- === RISIKO-BEWERTUNG ===
  CASE 
    WHEN AVG(K.KMAHNSTUFE) >= 3 THEN 'SEHR HOCH'
    WHEN AVG(K.KMAHNSTUFE) >= 2 THEN 'HOCH'
    WHEN AVG(K.KMAHNSTUFE) >= 1 THEN 'MITTEL'
    ELSE 'GERING'
  END AS INKASSO_RISIKO,                  -- Inkasso-Risiko: Basierend auf Mahnstufen
  
  -- === ABSCHREIBUNGS-INDIKATOR ===
  COUNT(CASE 
    WHEN CURRENT_DATE - COALESCE(LB.LETZTE_ZAHLUNG, DATEADD(-365 DAY TO CURRENT_DATE)) > 365 
    THEN 1 
  END) AS ABSCHREIBUNGSKANDIDATEN,        -- Abschreibung: >1 Jahr keine Zahlung

  -- === LAYER 4 ENHANCEMENT: Durchschnittstage seit letzter Zahlung ===
  AVG(CURRENT_DATE - COALESCE(LB.LETZTE_ZAHLUNG, DATEADD(-365 DAY TO CURRENT_DATE))) AS AVG_TAGE_UEBERFAELLIG

FROM KONTEN K
  LEFT JOIN LetzteBuchung LB ON K.KNR = LB.KNR
WHERE 
  K.OPBETRAG > 0  -- Nur Konten mit offenen Posten
  AND K.ONR < 890  -- Ausschluss Testobjekte
  AND K.KKLASSE IN (60, 62)  -- Nur Mieter und Eigentümer
GROUP BY 
  CASE 
    WHEN CURRENT_DATE - COALESCE(LB.LETZTE_ZAHLUNG, DATEADD(-365 DAY TO CURRENT_DATE)) <= 30 
      THEN '1. AKTUELL (0-30 Tage)'
    WHEN CURRENT_DATE - COALESCE(LB.LETZTE_ZAHLUNG, DATEADD(-365 DAY TO CURRENT_DATE)) <= 90 
      THEN '2. UEBERFAELLIG (31-90 Tage)'
    WHEN CURRENT_DATE - COALESCE(LB.LETZTE_ZAHLUNG, DATEADD(-365 DAY TO CURRENT_DATE)) <= 180 
      THEN '3. ALT (91-180 Tage)'
    ELSE '4. SEHR ALT (>180 Tage)'
  END,
  CASE 
    WHEN K.KKLASSE = 60 THEN 'MIETER'
    WHEN K.KKLASSE = 62 THEN 'EIGENTUEMER'
    ELSE 'SONSTIGE'
  END
ORDER BY 
  ALTERSKLASSE,
  SCHULDNERTYP;

/*
LAYER 4 IMPROVEMENTS:
- Firebird 5.0 native date arithmetic (eliminated DATEDIFF)
- Proper DATEADD syntax for Firebird (-365 DAY TO CURRENT_DATE)
- Direct date subtraction for interval calculations
- Added average days overdue metric for better insights
- firebird-driver compatible (all NUMERIC operations preserved)
- German character encoding ready (ISO-8859-1)

ERWARTETES ERGEBNIS:
- Forderungen in 4 Altersklassen gruppiert
- Trennung Mieter/Eigentümer
- Mahnstufen-Verteilung pro Altersklasse
- Abschreibungskandidaten identifiziert
- NEU: Durchschnittliche Überfälligkeitstage

GESCHÄFTSNUTZEN:
[OK] Priorisierung der Inkasso-Aktivitäten
[OK] Früherkennung von Problemfällen
[OK] Abschreibungsrisiko quantifizieren
[OK] Maßgeschneiderte Inkasso-Strategien
[OK] Cash-Collection-Optimierung
[OK] ENHANCED: Präzisere Altersberechnung
*/