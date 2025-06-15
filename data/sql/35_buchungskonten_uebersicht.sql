-- ============================================================================
-- QUERY 27: BUCHUNGSKONTEN-ÜBERSICHT - SIMPLIFIED & PARAMETERIZABLE VERSION
-- ============================================================================
/*
GESCHÄFTSZWECK: Aggregierte Buchungsübersicht nach Konten (vereinfacht)
OPTIMIERUNGEN:
  - Nur SOLL oder HABEN JOINs (kein OR)
  - Parametrisierbar nach KKLASSE, Zeitraum, ONR
  - Vorberechnung in CTE für bessere Performance
  - Ohne RUECKPOS für erste Version
*/

-- === PARAMETER-BEISPIELE ===
-- Kontenklasse: 1=Sachkonten, 20=Bank, 30=Rücklagen, 60=Mieter, 62=Eigentümer
-- Zeitraum: CURRENT_DATE - 365 (1 Jahr), oder feste Daten
-- Objekt: Spezifische ONR oder alle

WITH buchungen_soll AS (
  -- Alle SOLL-Buchungen
  SELECT 
    B.KSOLL AS KNR,
    B.ONRSOLL AS ONR,
    COUNT(*) AS ANZAHL,
    SUM(B.BETRAG) AS SUMME,
    EXTRACT(YEAR FROM B.DATUM) AS JAHR,
    EXTRACT(MONTH FROM B.DATUM) AS MONAT
  FROM BUCHUNG B
  WHERE B.DATUM >= CURRENT_DATE - 365  -- Parameter: Zeitraum
    AND B.ONRSOLL < 890  -- Keine Testobjekte
    -- Optional: AND B.ONRSOLL = 200  -- Nur Objekt 200
  GROUP BY B.KSOLL, B.ONRSOLL, EXTRACT(YEAR FROM B.DATUM), EXTRACT(MONTH FROM B.DATUM)
),
buchungen_haben AS (
  -- Alle HABEN-Buchungen
  SELECT 
    B.KHABEN AS KNR,
    B.ONRHABEN AS ONR,
    COUNT(*) AS ANZAHL,
    SUM(B.BETRAG) AS SUMME,
    EXTRACT(YEAR FROM B.DATUM) AS JAHR,
    EXTRACT(MONTH FROM B.DATUM) AS MONAT
  FROM BUCHUNG B
  WHERE B.DATUM >= CURRENT_DATE - 365  -- Parameter: Zeitraum
    AND (B.ONRHABEN < 890 OR B.ONRHABEN IS NULL)
    -- Optional: AND B.ONRHABEN = 200  -- Nur Objekt 200
  GROUP BY B.KHABEN, B.ONRHABEN, EXTRACT(YEAR FROM B.DATUM), EXTRACT(MONTH FROM B.DATUM)
)
SELECT 
  -- === KONTO-DATEN ===
  K.KNR,
  K.KNRSTR AS KONTO_CODE,
  K.KBEZ AS BEZEICHNUNG,
  K.KKLASSE,
  
  -- === KONTEN-TYP ===
  CASE K.KKLASSE
    WHEN 1 THEN 'SACHKONTO'
    WHEN 20 THEN 'BANK'
    WHEN 30 THEN 'RÜCKLAGE'
    WHEN 60 THEN 'MIETER'
    WHEN 62 THEN 'EIGENTÜMER'
    ELSE 'SONSTIG'
  END AS KONTENTYP,
  
  -- === KOSTENART (vereinfacht) ===
  CASE 
    WHEN K.KBEZ LIKE '%Strom%' OR K.KBEZ LIKE '%Gas%' THEN 'ENERGIE'
    WHEN K.KBEZ LIKE '%Wasser%' THEN 'WASSER'
    WHEN K.KBEZ LIKE '%Versicherung%' THEN 'VERSICHERUNG'
    WHEN K.KBEZ LIKE '%Verwaltung%' THEN 'VERWALTUNG'
    WHEN K.KBEZ LIKE '%Instand%' THEN 'INSTANDHALTUNG'
    WHEN K.KBEZ LIKE '%Miete%' THEN 'MIETE'
    ELSE 'SONSTIGE'
  END AS KOSTENART,
  
  -- === BEWEGUNGEN ===
  CAST(COALESCE(BS.SUMME, 0) AS NUMERIC(15,2)) AS SOLL,
  CAST(COALESCE(BH.SUMME, 0) AS NUMERIC(15,2)) AS HABEN,
  CAST(COALESCE(BS.SUMME, 0) - COALESCE(BH.SUMME, 0) AS NUMERIC(15,2)) AS SALDO,
  
  -- === AKTIVITÄT ===
  COALESCE(BS.ANZAHL, 0) + COALESCE(BH.ANZAHL, 0) AS ANZAHL_BUCHUNGEN,
  
  -- === ZEITRAUM ===
  COALESCE(BS.JAHR, BH.JAHR) AS JAHR,
  COALESCE(BS.MONAT, BH.MONAT) AS MONAT

FROM KONTEN K
  LEFT JOIN buchungen_soll BS ON K.KNR = BS.KNR
  LEFT JOIN buchungen_haben BH ON K.KNR = BH.KNR
WHERE 
  -- Nur Konten mit Bewegungen
  (BS.KNR IS NOT NULL OR BH.KNR IS NOT NULL)
  -- Parameter: Kontenklasse
  AND K.KKLASSE IN (1, 30)  -- Nur Sach- und Rücklagenkonten
  -- Optional: AND K.ONR = 200  -- Nur Objekt 200
ORDER BY 
  K.KKLASSE,
  ABS(COALESCE(BS.SUMME, 0) - COALESCE(BH.SUMME, 0)) DESC;

/*
PARAMETER-VARIANTEN:

1. Nur Bankkonten:
   WHERE K.KKLASSE = 20

2. Nur aktuelle Bewegungen (letzte 30 Tage):
   WHERE B.DATUM >= CURRENT_DATE - 30

3. Gruppiert nach Monat für Trend:
   GROUP BY K.KNR, EXTRACT(YEAR FROM B.DATUM), EXTRACT(MONTH FROM B.DATUM)

4. Top 20 bewegte Konten:
   ORDER BY ANZAHL_BUCHUNGEN DESC
   FETCH FIRST 20 ROWS ONLY

5. Nur Konten mit Saldo > 1000 EUR:
   HAVING ABS(SALDO) > 1000
*/