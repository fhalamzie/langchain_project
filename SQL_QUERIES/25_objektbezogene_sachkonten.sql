-- ============================================================================
-- QUERY 17: OBJEKTBEZOGENE SACHKONTEN - Layer 4 Enhancement with EA and INAKTIV
-- ============================================================================
-- Author: WINCASA Development Team
-- Status: ENHANCED with EA indicator and INAKTIV flag
-- Firebird-driver: COMPATIBLE
-- Layer 4 Enhancement: Option A with EA and INAKTIV fields
-- ============================================================================
/*
GESCHÄFTSZWECK: Übersicht aller Sachkonten eines Objekts für NK-Abrechnung
HAUPTTABELLEN:
  - KONTEN: Kontenplan pro Objekt
  - OBJEKTE: Objektstammdaten
  - SKR04/SKR03: Kontenrahmen-Referenz
FILTER: Nur Sachkonten (keine Personen-/Bankkonten)
VERWENDUNG: Basis für Nebenkostenabrechnung, Kontenstruktur-Übersicht

LAYER 4 ENHANCEMENTS:
- Added EA field (1=Income, 2=Expense indicator)
- Added INAKTIV flag to identify unused accounts
- Minimal changes per user directive
*/

SELECT 
  -- === OBJEKT-IDENTIFIKATION ===
  K.ONR,                                  -- Objektnummer (SMALLINT): Liegenschafts-ID
  O.OBEZ AS OBJEKT_KURZ,                 -- Objektkürzel (VARCHAR): z.B. "KUPFE190_W"
  O.OSTRASSE AS OBJEKT_STRASSE,          -- Objektstraße (VARCHAR): Liegenschaftsadresse
  
  -- === KONTEN-IDENTIFIKATION ===
  K.KNR,                                  -- Kontonummer (INTEGER): Eindeutige Konto-ID
  K.KNRSTR AS KONTO_CODE,                -- Kontocode (VARCHAR): Strukturierte Nummer
  K.KBEZ AS KONTO_BEZEICHNUNG,           -- Kontobezeichnung (VARCHAR): Beschreibung
  
  -- === KONTEN-KLASSIFIKATION ===
  K.KKLASSE,                             -- Kontenklasse (SMALLINT): Kontotyp
  CASE K.KKLASSE
    WHEN 1 THEN 'SACHKONTO'
    WHEN 20 THEN 'BANKKONTO'
    WHEN 60 THEN 'MIETERKONTO'
    WHEN 62 THEN 'EIGENTUEMERKONTO'
    ELSE 'SONSTIGE'
  END AS KONTENKLASSE_TEXT,              -- Kontenklasse Text: Klartext
  
  -- === NEUE FELDER (Layer 4 Enhancement) ===
  K.EA AS EINNAHME_AUSGABE,              -- EA Indikator: 1=Einnahme, 2=Ausgabe
  CASE K.EA
    WHEN 1 THEN 'EINNAHME'
    WHEN 2 THEN 'AUSGABE'
    ELSE 'UNDEFINIERT'
  END AS EA_TEXT,                        -- EA Text: Klartext für Einnahme/Ausgabe
  
  K.INAKTIV,                             -- Inaktiv Flag: J=Inaktiv, N=Aktiv
  CASE 
    WHEN K.INAKTIV = 'J' THEN 'INAKTIV'
    WHEN K.INAKTIV = 'N' THEN 'AKTIV'
    ELSE 'AKTIV'  -- Default to active if NULL
  END AS KONTO_STATUS,                   -- Konto Status: Klartext
  
  -- === KONTENARTEN FÜR NK-ABRECHNUNG ===
  CASE 
    -- Heizung & Warmwasser
    WHEN K.KBEZ LIKE '%Heiz%' OR K.KBEZ LIKE '%Waerme%' 
      THEN 'HEIZUNG/WARMWASSER'
    -- Wasser & Abwasser
    WHEN K.KBEZ LIKE '%Wasser%' AND K.KBEZ NOT LIKE '%Warm%' 
      THEN 'WASSER/ABWASSER'
    -- Strom
    WHEN K.KBEZ LIKE '%Strom%' OR K.KBEZ LIKE '%Elektr%' 
      THEN 'STROM'
    -- Müllabfuhr
    WHEN K.KBEZ LIKE '%Muell%' OR K.KBEZ LIKE '%Abfall%' 
      THEN 'MUELLABFUHR'
    -- Hausmeister
    WHEN K.KBEZ LIKE '%Hausmeister%' OR K.KBEZ LIKE '%Hauswart%' 
      THEN 'HAUSMEISTER'
    -- Reinigung
    WHEN K.KBEZ LIKE '%Reinigung%' OR K.KBEZ LIKE '%Sauber%' 
      THEN 'REINIGUNG'
    -- Versicherungen
    WHEN K.KBEZ LIKE '%Versicherung%' 
      THEN 'VERSICHERUNG'
    -- Grundsteuer
    WHEN K.KBEZ LIKE '%Grundsteuer%' 
      THEN 'GRUNDSTEUER'
    -- Aufzug
    WHEN K.KBEZ LIKE '%Aufzug%' OR K.KBEZ LIKE '%Lift%' 
      THEN 'AUFZUG'
    -- Gartenpflege
    WHEN K.KBEZ LIKE '%Garten%' 
      THEN 'GARTENPFLEGE'
    -- Verwaltung
    WHEN K.KBEZ LIKE '%Verwaltung%' 
      THEN 'VERWALTUNG'
    -- Instandhaltung
    WHEN K.KBEZ LIKE '%Instand%' OR K.KBEZ LIKE '%Reparatur%' 
      THEN 'INSTANDHALTUNG'
    ELSE 'SONSTIGE'
  END AS KOSTENART,                      -- Kostenart: NK-Kategorie
  
  -- === UMLAGEFÄHIGKEIT ===
  CASE 
    WHEN K.KBEZ LIKE '%Instand%' THEN 'NICHT UMLAGEFAEHIG'
    WHEN K.KBEZ LIKE '%Verwaltung%' THEN 'TEILWEISE UMLAGEFAEHIG'
    WHEN K.KBEZ LIKE '%Grundsteuer%' THEN 'UMLAGEFAEHIG'
    WHEN K.KBEZ LIKE '%Wasser%' THEN 'UMLAGEFAEHIG'
    WHEN K.KBEZ LIKE '%Muell%' THEN 'UMLAGEFAEHIG'
    WHEN K.KBEZ LIKE '%Heiz%' THEN 'UMLAGEFAEHIG'
    WHEN K.KBEZ LIKE '%Reinigung%' THEN 'UMLAGEFAEHIG'
    WHEN K.KBEZ LIKE '%Hausmeister%' THEN 'UMLAGEFAEHIG'
    WHEN K.KBEZ LIKE '%Versicherung%' AND K.KBEZ LIKE '%Gebaeude%' THEN 'UMLAGEFAEHIG'
    ELSE 'ZU PRUEFEN'
  END AS UMLAGEFAEHIGKEIT,               -- Umlagefähigkeit: BetrKV-Konformität
  
  -- === KONTOSTÄNDE ===
  CAST(K.KBRUTTO - K.OPBETRAG AS NUMERIC(15,2)) AS AKTUELLER_SALDO,  -- Kontostand: Aktueller Saldo
  CAST(K.OPBETRAG AS NUMERIC(15,2)) AS OFFENE_POSTEN,                -- Offene Posten: Unbezahlte Beträge
  
  -- === SKR-REFERENZ ===
  CASE 
    WHEN S4.KONTO IS NOT NULL THEN S4.KONTO
    WHEN S3.KONTO IS NOT NULL THEN S3.KONTO
    ELSE NULL
  END AS SKR_BEZEICHNUNG,                -- SKR-Bezeichnung: Standard-Kontenrahmen
  
  -- === BUCHUNGSAKTIVITÄT ===
  CASE 
    WHEN K.INAKTIV = 'J' THEN 'KONTO INAKTIV'
    WHEN K.OPBETRAG > 0 THEN 'MIT OFFENEN POSTEN'
    WHEN K.KBRUTTO <> 0 THEN 'MIT BEWEGUNG'
    ELSE 'KEINE BEWEGUNG'
  END AS KONTOAKTIVITAET                 -- Kontoaktivität: Erweitert um INAKTIV-Status

FROM KONTEN K
  INNER JOIN OBJEKTE O ON K.ONR = O.ONR
  LEFT JOIN SKR04 S4 ON K.KNRSTR = CAST(S4.KNR AS VARCHAR(20))
  LEFT JOIN SKR03 S3 ON K.KNRSTR = CAST(S3.KNR AS VARCHAR(20))
WHERE 
  K.KKLASSE = 1  -- Nur Sachkonten
  AND K.ONR < 890  -- Ausschluss Testobjekte
ORDER BY 
  K.INAKTIV,    -- Aktive Konten zuerst
  K.EA,         -- Einnahmen vor Ausgaben
  KOSTENART,
  K.KNRSTR;

/*
LAYER 4 IMPROVEMENTS:
- Added EA field to distinguish income (1) vs expense (2) accounts
- Added INAKTIV flag to identify unused accounts
- Enhanced KONTOAKTIVITAET to show inactive status
- Added proper CAST for NUMERIC fields
- Improved sorting to show active accounts first

ERWARTETES ERGEBNIS:
- Alle Sachkonten des gewählten Objekts
- EA-Indikator zeigt Einnahme/Ausgabe
- INAKTIV-Status für Kontenbereinigung
- Kategorisierung nach NK-relevanten Kostenarten
- Umlagefähigkeit gemäß BetrKV
- Aktuelle Kontostände

GESCHÄFTSNUTZEN:
[OK] Vollständige Kontenübersicht für NK-Abrechnung
[OK] Unterscheidung Einnahme-/Ausgabekonten
[OK] Identifikation inaktiver Konten
[OK] Umlagefähigkeits-Prüfung
[OK] Kontenaktivität zur Qualitätssicherung
[OK] SKR-Referenz für Standardkonformität
*/