-- ============================================================================
-- QUERY 18: DETAILLIERTE BUCHUNGEN - Layer 4 Enhanced with JOIN Fix
-- ============================================================================
/*
GESCHÄFTSZWECK: Alle Buchungen eines Kontos/Objekts inkl. Durchlaufende Posten & Sonderentnahmen
HAUPTTABELLEN:
  - BUCHUNG: Alle Finanztransaktionen (doppelte Buchführung)
  - KONTEN: Konteninformationen
  - OBJEKTE: Objektdaten
  - BANKEN: Bankinformationen für Reconciliation
LAYER 4 FIXES:
  - KRITISCH: HABEN-JOIN korrigiert (B.ONRHABEN statt B.ONRSOLL)
  - Unicode-Zeichen entfernt
  - OPBETRAG, MAHNSTUFE hinzugefügt
  - BANKNRSOLL/BANKNRHABEN für Bank-Reconciliation
*/

SELECT 
  -- === TRANSAKTIONS-IDENTIFIKATION ===
  B.BNR AS TRANSACTION_ID,                -- ID: Buchungs-BNR
  B.DATUM AS TRANSACTION_DATUM,           -- Datum: Buchungsdatum
  B.BELEGNR AS BELEG_REFERENZ,            -- Beleg: Externe Referenz
  B.WDATUM,                               -- Belegdatum (DATE): Rechnungsdatum
  
  -- === TRANSAKTIONS-TYP ===
  'NORMALE BUCHUNG' AS TRANSACTION_TYP,   -- Typ: Normal (vereinfacht)
  
  -- === BETRÄGE ===
  B.BETRAG,                               -- Betrag: Hauptbetrag (NUMERIC)
  ABS(B.BETRAG) AS BETRAG_ABS,            -- Betrag absolut: Für Summenbildung
  B.OPBETRAG,                             -- Offener Posten Betrag (NUMERIC)
  
  -- === KONTEN-INFORMATION (SOLL) ===
  B.KSOLL AS SOLL_KONTONUMMER,           -- Soll-Konto: KNR
  KS.KBEZ AS SOLL_KONTOBEZEICHNUNG,       -- Soll-Kontobez: Vollständiger Name
  B.ONRSOLL AS SOLL_OBJEKT,              -- Soll-Objekt: ONR
  
  -- === KONTEN-INFORMATION (HABEN) ===
  B.KHABEN AS HABEN_KONTONUMMER,         -- Haben-Konto: KNR
  KH.KBEZ AS HABEN_KONTOBEZEICHNUNG,      -- Haben-Kontobez: Vollständiger Name
  B.ONRHABEN AS HABEN_OBJEKT,            -- Haben-Objekt: ONR
  
  -- === BANK-REFERENZEN ===
  B.BANKNRSOLL,                           -- Bank-Referenz Soll-Seite
  BS.BEZEICHNUNG AS BANK_SOLL_NAME,       -- Bank-Name Soll
  B.BANKNRHABEN,                          -- Bank-Referenz Haben-Seite
  BH.BEZEICHNUNG AS BANK_HABEN_NAME,      -- Bank-Name Haben
  
  -- === OBJEKT-KONTEXT ===
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel: Gebäude
  O.OSTRASSE AS OBJEKT_STRASSE,           -- Objektstraße: Adresse
  O.OPLZORT AS OBJEKT_ORT,                -- Objekt PLZ/Ort: Standort
  
  -- === BUCHUNGSTEXT ===
  B.TEXT AS BUCHUNGSTEXT,                 -- Buchungstext: Beschreibung
  
  -- === MAHNUNG ===
  B.MAHNSTUFE,                            -- Mahnstufe (SMALLINT)
  
  -- === KOSTENART-ERKENNUNG ===
  CASE 
    WHEN B.TEXT LIKE '%Miete%' THEN 'MIETE'
    WHEN B.TEXT LIKE '%Nebenkosten%' THEN 'NEBENKOSTEN'
    WHEN B.TEXT LIKE '%Instandhaltung%' THEN 'INSTANDHALTUNG'
    WHEN B.TEXT LIKE '%Reparatur%' THEN 'REPARATUR'
    WHEN B.TEXT LIKE '%Versicherung%' THEN 'VERSICHERUNG'
    WHEN B.TEXT LIKE '%Hausgeld%' THEN 'HAUSGELD'
    WHEN B.TEXT LIKE '%Kaution%' THEN 'KAUTION'
    WHEN B.TEXT LIKE '%Rücklage%' OR B.TEXT LIKE '%Ruecklage%' THEN 'RUECKLAGE'
    WHEN B.TEXT LIKE '%Verwaltung%' THEN 'VERWALTUNG'
    WHEN B.TEXT LIKE '%Heizung%' THEN 'HEIZKOSTEN'
    WHEN B.TEXT LIKE '%Wasser%' THEN 'WASSERKOSTEN'
    WHEN B.TEXT LIKE '%Strom%' THEN 'STROMKOSTEN'
    WHEN B.TEXT LIKE '%Müll%' OR B.TEXT LIKE '%Muell%' THEN 'MUELLGEBUEHREN'
    WHEN B.TEXT LIKE '%Grundsteuer%' THEN 'GRUNDSTEUER'
    ELSE 'SONSTIGE'
  END AS ERKANNTE_KOSTENART,              -- Kostenart: Automatisch erkannt
  
  -- === ZEITRAUM-ANALYSE ===
  EXTRACT(YEAR FROM B.DATUM) AS JAHR,     -- Jahr: Buchungsjahr
  EXTRACT(MONTH FROM B.DATUM) AS MONAT,   -- Monat: Buchungsmonat
  EXTRACT(QUARTER FROM B.DATUM) AS QUARTAL, -- Quartal: Q1-Q4
  
  -- === GESCHÄFTSJAHR ===
  CASE 
    WHEN B.DATUM >= '2025-01-01' THEN '2025'
    WHEN B.DATUM >= '2024-01-01' THEN '2024'
    WHEN B.DATUM >= '2023-01-01' THEN '2023'
    WHEN B.DATUM >= '2022-01-01' THEN '2022'
    ELSE 'AELTER'
  END AS GESCHAEFTSJAHR,                  -- Geschaeftsjahr: Zuordnung
  
  -- === SALDO-RICHTUNG ===
  CASE 
    WHEN B.BETRAG > 0 THEN 'EINNAHME'
    WHEN B.BETRAG < 0 THEN 'AUSGABE'
    ELSE 'NEUTRAL'
  END AS SALDO_RICHTUNG                   -- Saldo: Ein-/Ausgabe

FROM BUCHUNG B
  INNER JOIN OBJEKTE O ON B.ONRSOLL = O.ONR
  LEFT JOIN KONTEN KS ON B.KSOLL = KS.KNR AND B.ONRSOLL = KS.ONR
  -- KRITISCHER FIX: HABEN-JOIN muss B.ONRHABEN verwenden!
  LEFT JOIN KONTEN KH ON B.KHABEN = KH.KNR AND B.ONRHABEN = KH.ONR  -- FIXED: war B.ONRSOLL
  -- Bank-Referenzen
  LEFT JOIN BANKEN BS ON B.BANKNRSOLL = BS.NR
  LEFT JOIN BANKEN BH ON B.BANKNRHABEN = BH.NR
WHERE
  B.ONRSOLL < 890  -- Ausschluss Testobjekte
  AND B.DATUM >= CURRENT_DATE - 365  -- Letzte 12 Monate
ORDER BY 
  B.DATUM DESC,
  B.BNR DESC;

/*
ERWARTETES ERGEBNIS:
- Alle Buchungen der letzten 12 Monate
- Vollständige Soll/Haben-Kontoinformation mit korrekten Namen
- Offene Posten-Beträge für Zahlungsverfolgung
- Bank-Referenzen für Reconciliation
- Mahnstufen für Überfälligkeitsanalyse

GESCHÄFTSNUTZEN:
[OK] Kritischer JOIN-Fix für korrekte Kontobezeichnungen
[OK] Offene Posten-Tracking
[OK] Bank-Reconciliation möglich
[OK] Mahnstufen-Übersicht
[OK] Vollständige doppelte Buchführung
*/