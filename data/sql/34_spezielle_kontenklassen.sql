-- ============================================================================
-- QUERY 26: SPEZIELLE KONTENKLASSEN - Layer 4 Enhanced with Modern Firebird Features
-- ============================================================================
/*
GESCHÄFTSZWECK: Übersicht aller speziellen Kontenklassen und -arten
HAUPTTABELLEN:
  - KONTEN: Alle Konten mit speziellen Klassifikationen
  - OBJEKTE: Objektzuordnung
FILTER: Fokus auf Sonderkonten außerhalb Standard-Kategorien
VERWENDUNG: Vollständige Kontensicht, Audit, Systemverständnis
LAYER 4 ENHANCEMENTS:
  - NUMERIC(15,2) CAST für alle Geldbeträge
  - Erweiterte Kommentierung für bessere Verständlichkeit
  - Performance-optimierte Abfragen
  - Zusätzliche Geschäftslogik-Kategorien
  - Flexible Filter-Parameter
*/

SELECT 
  -- === KONTEN-KLASSIFIKATION ===
  K.KKLASSE,                              -- Kontenklasse: Numerischer Code
  
  CASE K.KKLASSE
    WHEN 1 THEN 'SACHKONTO (Ausgaben/Einnahmen)'
    WHEN 20 THEN 'BANKKONTO (Liquidität)'
    WHEN 30 THEN 'RÜCKLAGENKONTO (Reserven)'
    WHEN 40 THEN 'ANLAGENKONTO (Vermögen)'
    WHEN 50 THEN 'VERBINDLICHKEITEN'
    WHEN 60 THEN 'MIETERKONTO (Persönliche Konten)'
    WHEN 61 THEN 'EIGENTÜMER Z3'
    WHEN 62 THEN 'EIGENTÜMERKONTO (WEG-Konten)'
    WHEN 70 THEN 'ABGRENZUNGSKONTEN'
    WHEN 80 THEN 'STEUERKONTEN'
    WHEN 90 THEN 'STATISTIKKONTEN'
    ELSE 'UNBEKANNTE KONTENKLASSE (' || K.KKLASSE || ')'
  END AS KONTENKLASSE_BEZEICHNUNG,        -- Kontenklasse: Klartext-Beschreibung
  
  -- === KONTEN-DETAILS ===
  K.ONR,                                  -- Objektnummer: Zuordnung zu WEG
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel: Bezeichnung
  K.KNR,                                  -- Kontonummer: Eindeutige ID
  K.KNRSTR AS KONTO_CODE,                 -- Kontocode: Strukturierte Nummer
  K.KBEZ AS KONTO_BEZEICHNUNG,            -- Kontobezeichnung: Vollständiger Name
  
  -- === FINANZIELLE KENNZAHLEN (OPTIMIERT) ===
  CAST(COALESCE(K.KBRUTTO, 0) AS NUMERIC(15,2)) AS KONTOSTAND, -- Kontostand: Aktueller Saldo in EUR
  CAST(COALESCE(K.OPBETRAG, 0) AS NUMERIC(15,2)) AS OFFENE_POSTEN, -- Offene Posten: Unbezahlt in EUR
  K.KMAHNSTUFE AS MAHNSTUFE,              -- Mahnstufe: 0-5 Eskalationsstufe
  
  -- === ERWEITERTE SPEZIAL-KATEGORISIERUNG ===
  CASE 
    -- Rücklagen und Reserven (erweitert)
    WHEN K.KNRSTR LIKE '30%' THEN 'RÜCKLAGEN/RESERVEN'
    WHEN K.KBEZ LIKE '%Rücklage%' OR K.KBEZ LIKE '%Reserve%' THEN 'RÜCKLAGEN/RESERVEN'
    -- Durchlaufende Posten
    WHEN K.KBEZ LIKE '%Durchlauf%' THEN 'DURCHLAUFENDE POSTEN'
    -- Kautionskonten (erweitert)
    WHEN K.KBEZ LIKE '%Kaution%' OR K.KBEZ LIKE '%Sicherheit%' THEN 'KAUTIONSKONTEN'
    -- Anzahlungskonten
    WHEN K.KBEZ LIKE '%Anzahlung%' OR K.KBEZ LIKE '%Vorauszahlung%' THEN 'ANZAHLUNGSKONTEN'
    -- Abgrenzungskonten (erweitert)
    WHEN K.KBEZ LIKE '%Abgrenzung%' OR K.KBEZ LIKE '%RAP%' OR K.KBEZ LIKE '%Rechnungsabgrenz%' THEN 'ABGRENZUNGSKONTEN'
    -- Steuerkonten (erweitert)
    WHEN K.KBEZ LIKE '%Steuer%' OR K.KBEZ LIKE '%USt%' OR K.KBEZ LIKE '%Mehrwertsteuer%' THEN 'STEUERKONTEN'
    -- Darlehenskonten (erweitert)
    WHEN K.KBEZ LIKE '%Darlehen%' OR K.KBEZ LIKE '%Kredit%' OR K.KBEZ LIKE '%Hypothek%' THEN 'DARLEHENSKONTEN'
    -- Verbindlichkeiten (erweitert)
    WHEN K.KBEZ LIKE '%Verbindlichkeit%' OR K.KBEZ LIKE '%Schuld%' THEN 'VERBINDLICHKEITEN'
    -- Versicherungskonten (neu)
    WHEN K.KBEZ LIKE '%Versicherung%' THEN 'VERSICHERUNGSKONTEN'
    -- Instandhaltungskonten (neu)
    WHEN K.KBEZ LIKE '%Instandhalt%' OR K.KBEZ LIKE '%Reparatur%' THEN 'INSTANDHALTUNGSKONTEN'
    -- Hausgeldkonten (neu)
    WHEN K.KBEZ LIKE '%Hausgeld%' OR K.KBEZ LIKE '%Vorauszahlung%' THEN 'HAUSGELDKONTEN'
    -- Sonstige Spezialkonten
    WHEN K.KKLASSE NOT IN (1, 20, 60, 62) THEN 'SONSTIGE SPEZIALKONTEN'
    ELSE 'STANDARDKONTO'
  END AS SPEZIAL_KATEGORIE,               -- Spezialkategorie: Erweiterte funktionale Zuordnung
  
  -- === AKTIVITÄTS-STATUS (ERWEITERT) ===
  CASE 
    WHEN K.INAKTIV = 'J' THEN 'INAKTIV'
    WHEN K.KBRUTTO = 0 AND K.OPBETRAG = 0 THEN 'NULLKONTO (Ohne Bewegung)'
    WHEN ABS(K.KBRUTTO) > 10000 OR ABS(K.OPBETRAG) > 10000 THEN 'HOCHAKTIV (>10K EUR)'
    WHEN ABS(K.KBRUTTO) > 1000 OR ABS(K.OPBETRAG) > 1000 THEN 'AKTIV (>1K EUR)'
    WHEN ABS(K.KBRUTTO) > 0 OR ABS(K.OPBETRAG) > 0 THEN 'NIEDRIG AKTIV (<1K EUR)'
    ELSE 'PASSIV (Kein Saldo)'
  END AS AKTIVITAETS_STATUS,              -- Aktivitätsstatus: Erweiterte Nutzungsanalyse
  
  -- === BUCHUNGSVERHALTEN (ERWEITERT) ===
  CASE 
    WHEN K.NEUTRAL = 1 THEN 'NEUTRALES KONTO (Durchlauf)'
    WHEN K.KABRECHNEN = 1 THEN 'ABRECHNUNGSRELEVANT'
    WHEN K.KABRECHNEN = 2 THEN 'NICHT ABRECHNUNGSRELEVANT'
    WHEN K.KKLASSE = 20 THEN 'BANKKONTO (Liquidität)'
    WHEN K.KKLASSE = 30 THEN 'RÜCKLAGENKONTO (Kapitalerhaltung)'
    ELSE 'STANDARD BUCHUNGSVERHALTEN'
  END AS BUCHUNGSVERHALTEN,               -- Buchungsverhalten: Erweiterte Abrechnungsrelevanz
  
  -- === EINHEIT-ZUORDNUNG ===
  K.ENR AS ENR,                    -- Einheitsnummer: Wohnungs-Zuordnung
  CASE 
    WHEN K.ENR IS NOT NULL AND K.ENR > 0 THEN 'EINHEITSSPEZIFISCH'
    ELSE 'OBJEKTWEIT'
  END AS ZUORDNUNGS_BEREICH,             -- Zuordnungsbereich: Einheit vs. Objekt
  
  -- === VERTEILUNGSLOGIK (ERWEITERT) ===
  K.KUSCHLNR1 AS UMLAGESCHLUESSEL_1,      -- Umlageschlüssel 1: Verteilungsart
  CAST(COALESCE(K.KUSCHLPROZ1, 0) AS NUMERIC(5,2)) AS UMLAGE_PROZENT_1, -- Umlage Prozent 1: Verteilungsgrad
  
  CASE 
    WHEN K.KUSCHLNR1 IS NOT NULL THEN 'HAT UMLAGESCHLÜSSEL'
    ELSE 'KEINE UMLAGE'
  END AS UMLAGE_STATUS,                   -- Umlage-Status: Verteilungsrelevanz
  
  -- === SONDER-FLAGS (ERWEITERT) ===
  CASE 
    WHEN K.SEV = 1 THEN 'SONDEREIGENTUMSVERWALTUNG (SEV)'
    WHEN K.SEV IS NULL OR K.SEV = 0 THEN 'GEMEINSCHAFTSEIGENTUM (WEG)'
    ELSE 'UNBESTIMMT'
  END AS EIGENTUMS_ART,                   -- Eigentumsart: SEV oder Gemeinschaft
  
  -- === RISK ASSESSMENT (NEU) ===
  CASE
    WHEN ABS(K.KBRUTTO) > 50000 THEN 'HOCH (>50K EUR Saldo)'
    WHEN ABS(K.OPBETRAG) > 20000 THEN 'MITTEL (>20K EUR OP)'
    WHEN K.KMAHNSTUFE >= 3 THEN 'MITTEL (Mahnstufe >=3)'
    WHEN ABS(K.KBRUTTO) > 10000 OR ABS(K.OPBETRAG) > 5000 THEN 'NIEDRIG (Überwachung)'
    ELSE 'MINIMAL (Standard)'
  END AS RISIKO_BEWERTUNG,                -- Risiko-Bewertung: Überwachungsintensität
  
  -- === INTEGRATION EXTERNAL SYSTEMS ===
  K.DATEVKNR AS DATEV_KONTONUMMER,        -- DATEV-Kontonummer: Steuerberatung
  CASE 
    WHEN K.DATEVKNR IS NOT NULL AND K.DATEVKNR > 0 THEN 'DATEV INTEGRIERT'
    ELSE 'NICHT EXPORTIERT'
  END AS DATEV_STATUS,                    -- DATEV-Status: Export-Bereitschaft
  
  -- === KONTEXT-INFORMATIONEN ===
  CASE 
    WHEN K.KKLASSE = 20 THEN 'LIQUIDITÄTSMANAGEMENT'
    WHEN K.KKLASSE = 30 THEN 'KAPITALERHALTUNG'
    WHEN K.KKLASSE = 60 THEN 'MIETERBETREUUNG'
    WHEN K.KKLASSE = 62 THEN 'EIGENTÜMERMANAGEMENT'
    WHEN K.KKLASSE = 70 THEN 'PERIODENABGRENZUNG'
    WHEN K.KKLASSE = 80 THEN 'STEUEROPTIMIERUNG'
    ELSE 'ALLGEMEINE BUCHFÜHRUNG'
  END AS GESCHAEFTS_ZWECK                 -- Geschäftszweck: Verwendungskontext

FROM KONTEN K
  LEFT JOIN OBJEKTE O ON K.ONR = O.ONR
WHERE 
  K.ONR < 890                             -- Ausschluss: Testobjekte
  AND (K.KKLASSE NOT IN (1, 20, 60, 62)  -- Spezialkonten
    OR K.KBEZ LIKE '%Durchlauf%'         -- Oder Durchlaufende Posten
    OR K.KBEZ LIKE '%Kaution%'           -- Oder Kautionskonten
    OR K.KBEZ LIKE '%Abgrenzung%'        -- Oder Abgrenzungskonten
    OR K.KBEZ LIKE '%Steuer%'            -- Oder Steuerkonten
    OR K.KBEZ LIKE '%Darlehen%'          -- Oder Darlehenskonten
    OR K.KBEZ LIKE '%Rücklage%'          -- Oder Rücklagenkonten
    OR K.KBEZ LIKE '%Versicherung%'      -- Oder Versicherungskonten
    OR K.KNRSTR LIKE '30%'               -- Oder 30000er Konten
    OR K.KNRSTR LIKE '40%'               -- Oder 40000er Konten
    OR K.KNRSTR LIKE '50%'               -- Oder 50000er Konten
    OR K.KNRSTR LIKE '70%'               -- Oder 70000er Konten
    OR K.KNRSTR LIKE '80%'               -- Oder 80000er Konten
    OR K.KNRSTR LIKE '90%')              -- Oder 90000er Konten
  -- Für spezifische Klasse: AND K.KKLASSE = 30
  -- Für aktive Konten nur: AND K.INAKTIV <> 'J'
  -- Für Mindest-Saldo: AND ABS(K.KBRUTTO) >= 1000
ORDER BY 
  K.KKLASSE,                              -- Primär nach Kontenklasse
  ABS(K.KBRUTTO) DESC,                    -- Sekundär nach Saldohöhe (Performance-relevant zuerst)
  K.ONR,                                  -- Dann nach Objekt
  K.KNRSTR;                               -- Schließlich nach Kontonummer

/*
ERWARTETES ERGEBNIS:
- Alle speziellen Kontenarten kategorisiert mit EUR-Beträgen
- Durchlaufende Posten identifiziert
- Rücklagen- und Reservekonten mit Salden
- Sondereigentumsverwaltung erkennbar
- Risiko-Bewertung für Überwachung
- DATEV-Integration sichtbar
- Erweiterte Geschäftslogik-Kategorien

GESCHÄFTSNUTZEN:
[OK] Vollständige Kontensystemsicht mit Geldbeträgen
[OK] Audit-Vorbereitung mit Risiko-Bewertung
[OK] Spezialkonten-Controlling mit Performance-Kennzahlen
[OK] DATEV-Integration transparent
[OK] Systemverständnis für Buchhalter erweitert
[OK] Compliance-Unterstützung für WEG-Verwaltung

LAYER 4 IMPROVEMENTS:
- NUMERIC(15,2) Präzision für alle Geldbeträge
- Erweiterte Spezial-Kategorisierung (10+ Kategorien)
- Neue Risiko-Bewertung für Überwachungsintensität
- Aktivitätsstatus mit EUR-Schwellenwerten
- Performance-optimierte Sortierung nach Relevanz
- Zusätzliche Geschäftslogik für WEG-Compliance
- Flexible Filter-Parameter für verschiedene Analysen
*/