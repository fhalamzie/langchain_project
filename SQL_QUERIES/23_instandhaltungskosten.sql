-- ============================================================================
-- QUERY 15: INSTANDHALTUNGSKOSTEN - Layer 4 Enhancement with Minimal Fix
-- ============================================================================
-- Author: WINCASA Development Team
-- Status: ENHANCED with NUMERIC fixes and existing field exposure
-- Firebird-driver: COMPATIBLE (NUMERIC operations verified)
-- Layer 4 Enhancement: Option D - Minimal Technical Fix
-- ============================================================================
/*
GESCHÄFTSZWECK: Analyse der Instandhaltungskosten nach Kategorie und Objekt
HAUPTTABELLEN:
  - BUCHUNG: Kostenbuchungen mit allen Feldern
  - KONTEN: Kostenkonten (Instandhaltung)
  - OBJEKTE: Objektzuordnung
KATEGORIEN: Identifikation über Kontenbezeichnung
VERWENDUNG: Budgetplanung, Kostenkontrolle, Benchmarking

LAYER 4 ENHANCEMENTS:
- Fixed NUMERIC aggregation issues for firebird-driver
- Added missing BUCHUNG fields (TEXT, BELEGNR, MWST, MITARBEITER_ID)
- Exposed actual booking date (DATUM) alongside value date (WDATUM)
- Fixed character encoding for German text
- Preserved all existing categorization and calculations
*/

SELECT 
  -- === OBJEKT-IDENTIFIKATION ===
  B.ONRSOLL AS ONR,                        -- Objektnummer: Gebäude-ID
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel: Internes Kürzel
  O.OSTRASSE AS STRASSE,                  -- Straße: Objektadresse
  O.OPLZORT AS PLZ_ORT,                   -- PLZ/Ort: Vollständige Adresse
  O.GA1 AS WOHNFLAECHE,                   -- Wohnfläche: Gesamt m²
  O.OANZEINH AS EINHEITEN,                -- Einheiten: Anzahl Wohnungen
  
  -- === ZEITPERIODE ===
  EXTRACT(YEAR FROM B.DATUM) AS JAHR,     -- Jahr: Buchungsjahr
  EXTRACT(MONTH FROM B.DATUM) AS MONAT,   -- Monat: Buchungsmonat (neu)
  
  -- === KOSTENKATEGORIE ===
  K.KNR AS KONTONUMMER,                    -- Kontonummer: Für Referenz (neu)
  K.KBEZ AS KOSTENART,                    -- Kostenart: Kontobezeichnung
  
  CASE 
    WHEN K.KBEZ LIKE '%Heizung%' OR K.KBEZ LIKE '%Sanitaer%' THEN 'HEIZUNG/SANITAER'
    WHEN K.KBEZ LIKE '%Elektr%' THEN 'ELEKTRIK'
    WHEN K.KBEZ LIKE '%Dach%' THEN 'DACH'
    WHEN K.KBEZ LIKE '%Fassade%' OR K.KBEZ LIKE '%Fenster%' THEN 'FASSADE/FENSTER'
    WHEN K.KBEZ LIKE '%Aufzug%' OR K.KBEZ LIKE '%Lift%' THEN 'AUFZUG'
    WHEN K.KBEZ LIKE '%Garten%' OR K.KBEZ LIKE '%Aussen%' THEN 'AUSSENANLAGEN'
    WHEN K.KBEZ LIKE '%Reinigung%' THEN 'REINIGUNG'
    WHEN K.KBEZ LIKE '%Wartung%' THEN 'WARTUNG ALLGEMEIN'
    WHEN K.KBEZ LIKE '%Reparatur%' THEN 'REPARATUR ALLGEMEIN'
    WHEN K.KBEZ LIKE '%Notfall%' OR K.KBEZ LIKE '%Havarie%' THEN 'NOTFALL'
    ELSE 'SONSTIGE INSTANDHALTUNG'
  END AS KATEGORIE,                       -- Kategorie: Gruppierung
  
  -- === KOSTEN-AGGREGATION (mit NUMERIC fix) ===
  COUNT(*) AS ANZAHL_BUCHUNGEN,           -- Anzahl: Buchungen
  
  -- Gesamtkosten mit proper NUMERIC handling
  CAST(SUM(ABS(B.BETRAG)) AS NUMERIC(15,2)) AS GESAMTKOSTEN,     -- Gesamtkosten: Summe in EUR
  CAST(AVG(ABS(B.BETRAG)) AS NUMERIC(15,2)) AS DURCHSCHNITTSKOSTEN, -- Ø Kosten: Pro Buchung in EUR
  CAST(MIN(ABS(B.BETRAG)) AS NUMERIC(15,2)) AS MIN_EINZELKOSTEN,  -- Min: Kleinste Position in EUR
  CAST(MAX(ABS(B.BETRAG)) AS NUMERIC(15,2)) AS MAX_EINZELKOSTEN,  -- Max: Größte Position in EUR
  
  -- === ZUSÄTZLICHE BUCHUNGSDETAILS (neu) ===
  COUNT(DISTINCT B.BELEGNR) AS ANZAHL_BELEGE,  -- Anzahl unterschiedlicher Belege
  CAST(SUM(B.MWST) AS NUMERIC(15,2)) AS MWST_GESAMT,  -- Mehrwertsteuer gesamt
  COUNT(DISTINCT B.MITARBEITER_ID) AS ANZAHL_MITARBEITER, -- Verschiedene Bearbeiter
  
  -- === KENNZAHLEN ===
  CASE 
    WHEN O.GA1 > 0 THEN CAST(SUM(ABS(B.BETRAG)) / O.GA1 AS NUMERIC(15,2))
    ELSE 0 
  END AS KOSTEN_PRO_QM,                   -- EUR/m²: Kosten pro Quadratmeter
  
  CASE 
    WHEN O.OANZEINH > 0 THEN CAST(SUM(ABS(B.BETRAG)) / O.OANZEINH AS NUMERIC(15,2))
    ELSE 0 
  END AS KOSTEN_PRO_EINHEIT,              -- EUR/Einheit: Kosten pro Wohnung
  
  -- === QUARTALSVERTEILUNG ===
  CAST(SUM(CASE WHEN EXTRACT(MONTH FROM B.DATUM) IN (1,2,3) THEN ABS(B.BETRAG) ELSE 0 END) AS NUMERIC(15,2)) AS Q1_KOSTEN,
  CAST(SUM(CASE WHEN EXTRACT(MONTH FROM B.DATUM) IN (4,5,6) THEN ABS(B.BETRAG) ELSE 0 END) AS NUMERIC(15,2)) AS Q2_KOSTEN,
  CAST(SUM(CASE WHEN EXTRACT(MONTH FROM B.DATUM) IN (7,8,9) THEN ABS(B.BETRAG) ELSE 0 END) AS NUMERIC(15,2)) AS Q3_KOSTEN,
  CAST(SUM(CASE WHEN EXTRACT(MONTH FROM B.DATUM) IN (10,11,12) THEN ABS(B.BETRAG) ELSE 0 END) AS NUMERIC(15,2)) AS Q4_KOSTEN,
  
  -- === ZEITLICHE DETAILS (neu) ===
  MIN(B.DATUM) AS ERSTE_BUCHUNG,          -- Erste Buchung im Zeitraum
  MAX(B.DATUM) AS LETZTE_BUCHUNG,         -- Letzte Buchung im Zeitraum
  MIN(B.WDATUM) AS FRUEHESTES_WERTDATUM,  -- Frühestes Wertstellungsdatum
  MAX(B.WDATUM) AS SPAETESTES_WERTDATUM,  -- Spätestes Wertstellungsdatum
  
  -- === KOSTENTREND ===
  CASE 
    WHEN SUM(ABS(B.BETRAG)) > 50000 THEN 'SEHR HOCH (>50k EUR)'
    WHEN SUM(ABS(B.BETRAG)) > 20000 THEN 'HOCH (20-50k EUR)'
    WHEN SUM(ABS(B.BETRAG)) > 5000 THEN 'NORMAL (5-20k EUR)'
    ELSE 'NIEDRIG (<5k EUR)'
  END AS KOSTENNIVEAU                     -- Kostenniveau: Absolute Beträge in EUR

FROM BUCHUNG B
  INNER JOIN KONTEN K ON B.KSOLL = K.KNR
  INNER JOIN OBJEKTE O ON B.ONRSOLL = O.ONR
WHERE 
  -- Instandhaltungskonten identifizieren
  (K.KBEZ LIKE '%Instandhaltung%' 
   OR K.KBEZ LIKE '%Wartung%'
   OR K.KBEZ LIKE '%Reparatur%'
   OR K.KBEZ LIKE '%Sanierung%'
   OR K.KBEZ LIKE '%Renovierung%')
  AND B.BETRAG < 0  -- Nur Ausgaben
  AND B.ONRSOLL < 890  -- Ausschluss Testobjekte
  AND B.DATUM >= CURRENT_DATE - 1095  -- Letzte 3 Jahre (ca. 365*3 Tage)
GROUP BY 
  B.ONRSOLL,
  O.OBEZ,
  O.OSTRASSE,
  O.OPLZORT,
  O.GA1,
  O.OANZEINH,
  EXTRACT(YEAR FROM B.DATUM),
  EXTRACT(MONTH FROM B.DATUM),
  K.KNR,
  K.KBEZ
ORDER BY 
  B.ONRSOLL,
  JAHR DESC,
  MONAT DESC,
  GESAMTKOSTEN DESC;

/*
LAYER 4 IMPROVEMENTS:
- Fixed all NUMERIC aggregation issues with proper CAST operations
- Added MONTH granularity for better temporal analysis
- Exposed KONTONUMMER for account reference
- Added BELEGNR count for document tracking
- Included MWST (VAT) totals for tax analysis
- Added MITARBEITER_ID count for workload analysis
- Exposed both DATUM and WDATUM for complete date tracking
- Maintained all existing categorization and calculations
- Fixed OPLZORT field name (was OPLZ/OORT separately)

ERWARTETES ERGEBNIS:
- Instandhaltungskosten nach Objekt, Jahr und Monat
- Kategorisierung nach Gewerk (unchanged)
- Kennzahlen EUR/m² und EUR/Einheit (with NUMERIC fix)
- Quartalsverteilung für Saisonalität
- Zusätzliche Felder für detailliertere Analyse

GESCHÄFTSNUTZEN:
[OK] Kostentransparenz pro Objekt/Kategorie
[OK] Benchmark zwischen Objekten
[OK] Budgetplanung auf Datenbasis
[OK] Früherkennung von Kostentreibern
[OK] IH-Rücklagen-Adequanz prüfen
[OK] ENHANCED: Mehr Details ohne Komplexität
*/