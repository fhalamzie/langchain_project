-- ============================================================================
-- QUERY 19: KONTEN-SALDENLISTE - Enhanced with financial fields
-- ============================================================================
/*
GESCHÄFTSZWECK: Saldenliste aller NK-relevanten Konten mit Finanzwerten
HAUPTTABELLEN:
  - KONTEN: Aktuelle Kontostände (KBRUTTO field added)
  - BUCHUNG: Bewegungsdaten für Zeitraumanalyse (BETRAG sums added)
VERWENDUNG: Jahresabschluss, NK-Abrechnung, Kostenkontrolle
ENHANCEMENTS: 
  - Added KBRUTTO (current balance) from KONTEN table
  - Added SUM(BETRAG) with proper CAST for firebird-driver
  - Added actual financial amounts instead of just counts
*/

SELECT 
  -- === KONTO-IDENTIFIKATION ===
  K.ONR,                                  -- Objektnummer: Gebäude-ID
  K.KNR,                                  -- Kontonummer: Account-ID
  K.KBEZ AS KONTOBEZEICHNUNG,            -- Kontoname: Vollständige Bezeichnung
  
  -- === FINANZIELLE STAMMDATEN (ENHANCED) ===
  K.KBRUTTO AS AKTUELLER_SALDO,          -- Aktueller Kontosaldo
  K.OPBETRAG AS OFFENE_POSTEN,           -- Offene Posten Betrag
  K.KUST AS UMSATZSTEUER,                 -- USt-Satz falls vorhanden
  
  -- === OBJEKT-KONTEXT ===
  O.OBEZ AS OBJEKT_KURZ,                 -- Objektkürzel: Gebäude
  O.OSTRASSE AS OBJEKT_STRASSE,          -- Objektstraße: Adresse
  O.OANZEINH AS ANZAHL_EINHEITEN,        -- Einheiten: Anzahl Wohnungen
  
  -- === BUCHUNGSAKTIVITAET MIT BETRAEGEN (ENHANCED) ===
  COUNT(DISTINCT B.BNR) AS ANZAHL_BUCHUNGEN_2024,     -- Buchungen 2024
  CAST(COALESCE(SUM(B.BETRAG), 0) AS NUMERIC(15,2)) AS SUMME_2024,  -- Summe 2024
  
  COUNT(DISTINCT B2.BNR) AS ANZAHL_BUCHUNGEN_2023,    -- Buchungen 2023
  CAST(COALESCE(SUM(B2.BETRAG), 0) AS NUMERIC(15,2)) AS SUMME_2023, -- Summe 2023
  
  -- === JAHRESVERGLEICH (ENHANCED) ===
  CAST(COALESCE(SUM(B.BETRAG), 0) - COALESCE(SUM(B2.BETRAG), 0) AS NUMERIC(15,2)) AS DIFFERENZ_2024_2023,
  
  -- === KOSTENKATEGORIE ===
  CASE 
    WHEN K.KBEZ LIKE '%Wasser%' OR K.KBEZ LIKE '%Abwasser%' THEN 'WASSER/ABWASSER'
    WHEN K.KBEZ LIKE '%Muell%' OR K.KBEZ LIKE '%Müll%' THEN 'MUELLENTSORGUNG'
    WHEN K.KBEZ LIKE '%Strom%' OR K.KBEZ LIKE '%Elektr%' THEN 'STROMKOSTEN'
    WHEN K.KBEZ LIKE '%Heiz%' OR K.KBEZ LIKE '%Waerm%' THEN 'HEIZKOSTEN'
    WHEN K.KBEZ LIKE '%Hausmeister%' OR K.KBEZ LIKE '%Hauswart%' THEN 'HAUSMEISTERKOSTEN'
    WHEN K.KBEZ LIKE '%Reinigung%' THEN 'REINIGUNGSKOSTEN'
    WHEN K.KBEZ LIKE '%Garten%' OR K.KBEZ LIKE '%Gruen%' THEN 'GARTENPFLEGE'
    WHEN K.KBEZ LIKE '%Versicher%' THEN 'VERSICHERUNGEN'
    WHEN K.KBEZ LIKE '%Verwalt%' THEN 'VERWALTUNGSKOSTEN'
    ELSE 'SONSTIGE_NK'
  END AS KOSTENKATEGORIE,                 -- Kategorie: NK-Zuordnung
  
  -- === TREND-ANALYSE MIT BETRAEGEN (ENHANCED) ===
  CASE 
    WHEN COALESCE(SUM(B.BETRAG), 0) > COALESCE(SUM(B2.BETRAG), 0) THEN 'KOSTEN GESTIEGEN'
    WHEN COALESCE(SUM(B.BETRAG), 0) < COALESCE(SUM(B2.BETRAG), 0) THEN 'KOSTEN GESUNKEN'
    ELSE 'KOSTEN STABIL'
  END AS KOSTENTREND,                    -- Trend: Kostenentwicklung
  
  -- === ZEITRAUM-ANALYSE ===
  MIN(COALESCE(B.DATUM, B2.DATUM)) AS ERSTE_BUCHUNG,  -- Erste Buchung
  MAX(COALESCE(B.DATUM, B2.DATUM)) AS LETZTE_BUCHUNG, -- Letzte Buchung
  
  -- === KOSTEN PRO EINHEIT (ENHANCED) ===
  CASE 
    WHEN O.OANZEINH > 0 THEN 
      CAST(COALESCE(SUM(B.BETRAG), 0) / O.OANZEINH AS NUMERIC(15,2))
    ELSE NULL
  END AS KOSTEN_PRO_EINHEIT_2024,        -- Kosten je Wohnung 2024
  
  -- === AKTIVITAETS-BEWERTUNG ===
  CASE 
    WHEN COUNT(DISTINCT B.BNR) = 0 THEN 'INAKTIV'
    WHEN COUNT(DISTINCT B.BNR) <= 5 THEN 'WENIG AKTIV'
    WHEN COUNT(DISTINCT B.BNR) <= 20 THEN 'NORMAL AKTIV'
    ELSE 'SEHR AKTIV'
  END AS AKTIVITAETSBEWERTUNG            -- Bewertung: Aktivitätslevel

FROM KONTEN K
  INNER JOIN OBJEKTE O ON K.ONR = O.ONR
  LEFT JOIN BUCHUNG B ON (B.KSOLL = K.KNR OR B.KHABEN = K.KNR)
    AND B.DATUM >= '2024-01-01' 
    AND B.DATUM <= '2024-12-31'
  LEFT JOIN BUCHUNG B2 ON (B2.KSOLL = K.KNR OR B2.KHABEN = K.KNR)
    AND B2.DATUM >= '2023-01-01' 
    AND B2.DATUM <= '2023-12-31'
WHERE 
  K.KKLASSE = 1  -- Nur Sachkonten
  AND K.ONR < 890  -- Ausschluss Testobjekte
  AND (K.KBEZ LIKE '%Wasser%' 
    OR K.KBEZ LIKE '%Abwasser%'
    OR K.KBEZ LIKE '%Muell%'
    OR K.KBEZ LIKE '%Müll%'
    OR K.KBEZ LIKE '%Strom%'
    OR K.KBEZ LIKE '%Heiz%'
    OR K.KBEZ LIKE '%Hausmeister%'
    OR K.KBEZ LIKE '%Reinigung%'
    OR K.KBEZ LIKE '%Garten%'
    OR K.KBEZ LIKE '%Versicher%'
    OR K.KBEZ LIKE '%Verwalt%')
GROUP BY 
  K.ONR, K.KNR, K.KBEZ, K.KBRUTTO, K.OPBETRAG, K.KUST, 
  O.OBEZ, O.OSTRASSE, O.OANZEINH
ORDER BY 
  K.ONR,
  CASE 
    WHEN K.KBEZ LIKE '%Wasser%' OR K.KBEZ LIKE '%Abwasser%' THEN 'WASSER/ABWASSER'
    WHEN K.KBEZ LIKE '%Muell%' OR K.KBEZ LIKE '%Müll%' THEN 'MUELLENTSORGUNG'
    WHEN K.KBEZ LIKE '%Strom%' OR K.KBEZ LIKE '%Elektr%' THEN 'STROMKOSTEN'
    WHEN K.KBEZ LIKE '%Heiz%' OR K.KBEZ LIKE '%Waerm%' THEN 'HEIZKOSTEN'
    WHEN K.KBEZ LIKE '%Hausmeister%' OR K.KBEZ LIKE '%Hauswart%' THEN 'HAUSMEISTERKOSTEN'
    WHEN K.KBEZ LIKE '%Reinigung%' THEN 'REINIGUNGSKOSTEN'
    WHEN K.KBEZ LIKE '%Garten%' OR K.KBEZ LIKE '%Gruen%' THEN 'GARTENPFLEGE'
    WHEN K.KBEZ LIKE '%Versicher%' THEN 'VERSICHERUNGEN'
    WHEN K.KBEZ LIKE '%Verwalt%' THEN 'VERWALTUNGSKOSTEN'
    ELSE 'SONSTIGE_NK'
  END,
  COALESCE(SUM(B.BETRAG), 0) DESC;

/*
ERWARTETES ERGEBNIS:
- Saldenliste aller NK-relevanten Konten MIT finanziellen Werten
- Jahresvergleich mit tatsächlichen Beträgen
- Aktuelle Kontostände aus KONTEN.KBRUTTO
- Kosten pro Einheit für Budgetplanung
- Trend-Analyse basierend auf tatsächlichen Kosten

GESCHÄFTSNUTZEN:
[OK] Jahresabschluss-Vorbereitung mit echten Salden
[OK] NK-Abrechnungs-Grundlage mit Beträgen
[OK] Kostenkontrolle und Budgetplanung
[OK] Trend-Erkennung basierend auf Kosten, nicht nur Aktivität
[ENHANCED] Mit BETRAG-Aggregationen und KBRUTTO-Salden
*/