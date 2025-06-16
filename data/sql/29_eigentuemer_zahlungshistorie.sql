-- ============================================================================
-- QUERY 21: EIGENTÜMER-ZAHLUNGSHISTORIE - SIMPLIFIED & PARAMETERIZABLE VERSION
-- ============================================================================
/*
GESCHÄFTSZWECK: Zahlungshistorie für WEG-Eigentümer (vereinfacht & parametrisierbar)
OPTIMIERUNGEN:
  - UNION statt OR-JOIN (verhindert kartesisches Produkt)
  - Zeitraum-Parameter: Standard 1 Jahr (anpassbar)
  - Optional: Einzelner Eigentümer filterbar
  - Reduzierte Felder für bessere Performance
*/

-- === PARAMETER-SEKTION (anpassbar) ===
-- Zeitraum: Tage zurück von heute (365 = 1 Jahr, 730 = 2 Jahre)
-- Eigentümer: NULL = alle, oder spezifische EIGNR
-- Beispiel für Anpassung:
--   WHERE B.DATUM >= CURRENT_DATE - 180  -- Letzte 6 Monate
--   AND (@EIGNR IS NULL OR E.EIGNR = @EIGNR)

WITH zahlungen AS (
  -- Zahlungseingänge (HABEN-Buchungen)
  SELECT 
    K.KNR,
    K.ONR,
    K.ENR,
    B.BNR,
    B.DATUM,
    B.BELEGNR,
    B.TEXT,
    B.BETRAG AS BETRAG_ORIGINAL,
    B.BETRAG AS EINGANG,
    CAST(0 AS NUMERIC(15,2)) AS AUSGANG,
    'ZAHLUNG' AS RICHTUNG
  FROM BUCHUNG B
    INNER JOIN KONTEN K ON B.KHABEN = K.KNR
  WHERE K.KKLASSE = 62  -- Eigentümerkonten
    AND B.DATUM >= CURRENT_DATE - 365  -- Standard: 1 Jahr
    
  UNION ALL
  
  -- Belastungen (SOLL-Buchungen)
  SELECT 
    K.KNR,
    K.ONR,
    K.ENR,
    B.BNR,
    B.DATUM,
    B.BELEGNR,
    B.TEXT,
    B.BETRAG AS BETRAG_ORIGINAL,
    CAST(0 AS NUMERIC(15,2)) AS EINGANG,
    B.BETRAG AS AUSGANG,
    'BELASTUNG' AS RICHTUNG
  FROM BUCHUNG B
    INNER JOIN KONTEN K ON B.KSOLL = K.KNR
  WHERE K.KKLASSE = 62  -- Eigentümerkonten
    AND B.DATUM >= CURRENT_DATE - 365  -- Standard: 1 Jahr
)
SELECT 
  -- === EIGENTÜMER ===
  E.EIGNR,
  E.ENAME || ', ' || E.EVNAME AS ENAME,
  
  -- === BUCHUNGSDATEN ===
  Z.BNR,
  Z.DATUM,
  Z.BELEGNR,
  Z.TEXT AS BUCHUNGSTEXT,
  Z.RICHTUNG,
  
  -- === BETRÄGE ===
  CAST(Z.EINGANG AS NUMERIC(15,2)) AS EINGANG,
  CAST(Z.AUSGANG AS NUMERIC(15,2)) AS AUSGANG,
  CAST(Z.EINGANG - Z.AUSGANG AS NUMERIC(15,2)) AS SALDO_BEWEGUNG,
  
  -- === OBJEKT/EINHEIT ===
  Z.ONR,
  O.OBEZ AS OBJEKT_KURZ,
  Z.ENR,
  W.EBEZ AS WOHNUNG,
  
  -- === KATEGORISIERUNG (vereinfacht) ===
  CASE 
    WHEN Z.TEXT LIKE '%Hausgeld%' THEN 'HAUSGELD'
    WHEN Z.TEXT LIKE '%Sonderumlage%' THEN 'SONDERUMLAGE'
    WHEN Z.TEXT LIKE '%Rücklage%' OR Z.TEXT LIKE '%Ruecklage%' THEN 'RUECKLAGE'
    WHEN Z.TEXT LIKE '%Abrechnung%' THEN 'ABRECHNUNG'
    WHEN Z.TEXT LIKE '%Nachzahlung%' THEN 'NACHZAHLUNG'
    ELSE 'SONSTIGE'
  END AS KATEGORIE,
  
  -- === ZEITLICHE GRUPPIERUNG ===
  EXTRACT(YEAR FROM Z.DATUM) AS JAHR,
  EXTRACT(MONTH FROM Z.DATUM) AS MONAT,
  'Q' || CAST((EXTRACT(MONTH FROM Z.DATUM) + 2) / 3 AS INTEGER) AS QUARTAL
  
FROM zahlungen Z
  -- Join über EIGENTUEMER mit ONR und ENR für korrekte Zuordnung
  INNER JOIN EIGADR ET ON Z.ONR = ET.ONR AND Z.ENR = ET.ENR AND Z.KNR = ET.KNR
  INNER JOIN EIGADR E ON ET.EIGNR = E.EIGNR
  LEFT JOIN OBJEKTE O ON Z.ONR = O.ONR
  LEFT JOIN WOHNUNG W ON Z.ONR = W.ONR AND Z.ENR = W.ENR
WHERE 
  Z.ONR < 890  -- Keine Testobjekte
  -- Optionaler Filter für einzelnen Eigentümer:
  -- AND E.EIGNR = 123
ORDER BY 
  E.EIGNR,
  Z.DATUM DESC,
  Z.BNR DESC;

/*
PARAMETER-BEISPIELE:
1. Letzte 6 Monate: WHERE B.DATUM >= CURRENT_DATE - 180
2. Jahr 2023: WHERE B.DATUM BETWEEN '2023-01-01' AND '2023-12-31'
3. Einzelner Eigentümer: AND E.EIGNR = 123
4. Mehrere Eigentümer: AND E.EIGNR IN (123, 456, 789)

PERFORMANCE:
- Durch UNION statt OR-JOIN deutlich weniger Rows
- CTE für bessere Lesbarkeit und Wartbarkeit
- Indexe auf BUCHUNG(DATUM), KONTEN(KKLASSE,KNR) empfohlen
*/