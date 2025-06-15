-- ============================================================================
-- QUERY 22: WEG-ZAHLUNGSÜBERSICHT - SIMPLIFIED & PARAMETERIZABLE VERSION
-- ============================================================================
/*
GESCHÄFTSZWECK: Zahlungsübersicht für WEG-Verwaltung (vereinfacht)
OPTIMIERUNGEN:
  - Aggregation statt Einzelbuchungen
  - Parametrisierbar nach Objekt, Zeitraum, Eigentümer
  - Vorberechnung von Summen
*/

-- === PARAMETER ===
-- Standard: Aktuelles Jahr, alle Objekte
-- Anpassbar: Spezifisches ONR, EIGNR, Zeitraum

WITH zahlungssummen AS (
  SELECT 
    ET.EIGNR,
    K.ONR,
    K.ENR,
    EXTRACT(YEAR FROM B.DATUM) AS JAHR,
    EXTRACT(MONTH FROM B.DATUM) AS MONAT,
    -- Eingänge (Zahlungen von Eigentümern)
    SUM(CASE WHEN B.KHABEN = K.KNR THEN B.BETRAG ELSE 0 END) AS EINGANG,
    -- Ausgänge (Belastungen)
    SUM(CASE WHEN B.KSOLL = K.KNR THEN B.BETRAG ELSE 0 END) AS AUSGANG,
    -- Anzahl Transaktionen
    COUNT(CASE WHEN B.KHABEN = K.KNR THEN 1 END) AS ANZAHL_EINGAENGE,
    COUNT(CASE WHEN B.KSOLL = K.KNR THEN 1 END) AS ANZAHL_AUSGAENGE
  FROM KONTEN K
    INNER JOIN EIGENTUEMER ET ON K.ONR = ET.ONR AND K.ENR = ET.ENR AND K.KNR = ET.KNR
    INNER JOIN BUCHUNG B ON (K.KNR = B.KHABEN OR K.KNR = B.KSOLL)
  WHERE K.KKLASSE = 62  -- WEG-Eigentümerkonten
    AND B.DATUM >= '2024-01-01'  -- Parameter: Jahr 2024
    AND B.DATUM <= '2024-12-31'
    AND K.ONR < 890  -- Keine Testobjekte
    -- Optional: AND K.ONR = 200  -- Nur Objekt 200
    -- Optional: AND K.EIGNR = 123  -- Nur Eigentümer 123
  GROUP BY ET.EIGNR, K.ONR, K.ENR, EXTRACT(YEAR FROM B.DATUM), EXTRACT(MONTH FROM B.DATUM)
)
SELECT 
  -- === OBJEKT ===
  O.ONR,
  O.OBEZ AS OBJEKT,
  O.OSTRASSE,
  
  -- === EIGENTÜMER ===
  E.EIGNR,
  E.ENAME || ', ' || E.EVNAME AS EIGENTUEMER,
  
  -- === EINHEIT ===
  W.ENR,
  W.EBEZ AS WOHNUNG,
  
  -- === ZEITRAUM ===
  Z.JAHR,
  Z.MONAT,
  CASE Z.MONAT
    WHEN 1 THEN 'Januar'
    WHEN 2 THEN 'Februar'
    WHEN 3 THEN 'März'
    WHEN 4 THEN 'April'
    WHEN 5 THEN 'Mai'
    WHEN 6 THEN 'Juni'
    WHEN 7 THEN 'Juli'
    WHEN 8 THEN 'August'
    WHEN 9 THEN 'September'
    WHEN 10 THEN 'Oktober'
    WHEN 11 THEN 'November'
    WHEN 12 THEN 'Dezember'
  END AS MONATSNAME,
  
  -- === FINANZEN ===
  CAST(Z.EINGANG AS NUMERIC(15,2)) AS ZAHLUNGEN_EINGANG,
  CAST(Z.AUSGANG AS NUMERIC(15,2)) AS BELASTUNGEN,
  CAST(Z.EINGANG - Z.AUSGANG AS NUMERIC(15,2)) AS MONATSSALDO,
  
  -- === AKTIVITÄT ===
  Z.ANZAHL_EINGAENGE,
  Z.ANZAHL_AUSGAENGE,
  
  -- === ZAHLUNGSVERHALTEN ===
  CASE 
    WHEN Z.EINGANG > Z.AUSGANG THEN 'ÜBERZAHLUNG'
    WHEN Z.EINGANG = Z.AUSGANG THEN 'AUSGEGLICHEN'
    WHEN Z.EINGANG >= Z.AUSGANG * 0.9 THEN 'FAST AUSGEGLICHEN'
    WHEN Z.EINGANG >= Z.AUSGANG * 0.5 THEN 'TEILZAHLUNG'
    ELSE 'RÜCKSTAND'
  END AS STATUS

FROM zahlungssummen Z
  INNER JOIN OBJEKTE O ON Z.ONR = O.ONR
  INNER JOIN EIGADR E ON Z.EIGNR = E.EIGNR
  LEFT JOIN WOHNUNG W ON Z.ONR = W.ONR AND Z.ENR = W.ENR
ORDER BY 
  O.ONR,
  E.EIGNR,
  Z.JAHR,
  Z.MONAT;

/*
PARAMETER-VARIANTEN:

1. Nur ein Quartal:
   WHERE EXTRACT(QUARTER FROM B.DATUM) = 1

2. Jahresvergleich:
   WHERE B.DATUM >= CURRENT_DATE - 730  -- 2 Jahre
   GROUP BY EXTRACT(YEAR FROM B.DATUM)

3. Nur Rückstände:
   HAVING SUM(EINGANG) < SUM(AUSGANG)

4. Export pro Objekt:
   FOR EACH ONR -> Separate Datei
*/