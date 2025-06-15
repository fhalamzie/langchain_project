-- ============================================================================
-- QUERY 25: RÜCKLAGEN-MANAGEMENT - Layer 4 Complete Business Functionality Restoration
-- ============================================================================
/*
GESCHÄFTSZWECK: Vollständige Übersicht aller Rücklagenpositionen pro WEG
HAUPTTABELLEN:
  - RUECKPOS: Alle Rücklagenpositionen (POS1-POS10)
  - KONTEN: Zugehörige Konten (KZUF, KENTN, KNRP)
  - OBJEKTE: WEG-Informationen
INHALT: 10 verschiedene Rücklagenarten pro Objekt
VERWENDUNG: Rücklagen-Controlling, Finanzplanung, Eigentümer-Information
LAYER 4 RESTORATION:
  - Vollständige Wiederherstellung aller POS7-POS10 Positionen
  - Echte EUR-Berechnungen statt Status-Indikatoren
  - Konten-Zuordnungen (KZUF, KENTN, KNRP) wiederhergestellt
  - Steuer- und Zinsberechnungen mit NUMERIC(15,2)
  - Korrekte Sortierung nach Endstand (höchste Rücklagen zuerst)
*/

SELECT 
  -- === OBJEKT-IDENTIFIKATION ===
  R.ONR,                                  -- Objektnummer: WEG
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel: Bezeichnung
  O.OSTRASSE AS OBJEKT_STRASSE,           -- Objektstraße: Vollständige Adresse
  O.OANZEINH AS ANZAHL_EINHEITEN,         -- Einheiten: Wohnungsanzahl
  CAST(O.GA1 AS NUMERIC(10,2)) AS WOHNFLAECHE_GESAMT, -- Wohnfläche: Gesamt m²
  
  -- === RÜCKLAGEN-IDENTIFIKATION ===
  R.NR AS RUECKLAGE_NR,                   -- Rücklagen-Nummer: Eindeutige ID
  R.NAME AS RUECKLAGE_NAME,               -- Rücklage Name: Bezeichnung der Reserve
  R.USCHL AS UMLAGESCHLUESSEL,            -- Umlageschlüssel: Verteilungsbasis
  
  -- === KONTEN-ZUORDNUNGEN (WIEDERHERGESTELLT) ===
  R.KZUF AS ZUEFUEHRUNGS_KONTO,           -- Zuführungskonto: Normalerweise 30000
  R.KENTN AS ENTNAHME_KONTO,              -- Entnahmekonto: Normalerweise 30100
  R.KNRP AS PROJEKT_KONTO,                -- Projektkonto: Spezielle Zuordnung
  
  -- === POSITION 1: ZINSEN ===
  CAST(COALESCE(R.POS1, 0) AS NUMERIC(15,2)) AS ZINSEN_BETRAG, -- Zinsen: Kapitalerträge in EUR
  R.POS1NAME AS ZINSEN_BEZEICHNUNG,       -- Zinsen: "Zinsen"
  R.POS1CHECK AS ZINSEN_AKTIV,            -- Zinsen: Aktiv-Flag
  
  -- === POSITION 2: ZINSABSCHLAGSTEUER ===
  CAST(COALESCE(R.POS2, 0) AS NUMERIC(15,2)) AS ZINSSTEUER_BETRAG, -- Zinsabschlagsteuer in EUR
  R.POS2NAME AS ZINSSTEUER_BEZEICHNUNG,   -- Zinsabschlagsteuer: "Zinsabschlagsteuer"
  R.POS2CHECK AS ZINSSTEUER_AKTIV,        -- Zinsabschlagsteuer: Aktiv-Flag
  
  -- === POSITION 3: SOLIDARITÄTSZUSCHLAG ===
  CAST(COALESCE(R.POS3, 0) AS NUMERIC(15,2)) AS SOLI_BETRAG, -- Solidaritätszuschlag in EUR
  R.POS3NAME AS SOLI_BEZEICHNUNG,         -- Solidaritätszuschlag: "Solidaritätszuschlag"
  R.POS3CHECK AS SOLI_AKTIV,              -- Solidaritätszuschlag: Aktiv-Flag
  
  -- === POSITION 4: KAPITALERTRAGSSTEUER ===
  CAST(COALESCE(R.POS4, 0) AS NUMERIC(15,2)) AS KAPSTEUER_BETRAG, -- Kapitalertragssteuer in EUR
  R.POS4NAME AS KAPSTEUER_BEZEICHNUNG,    -- Kapitalertragssteuer: "Kapitalertragssteuer"
  R.POS4CHECK AS KAPSTEUER_AKTIV,         -- Kapitalertragssteuer: Aktiv-Flag
  
  -- === POSITION 5: DURCHLAUFENDE POSTEN ===
  CAST(COALESCE(R.POS5, 0) AS NUMERIC(15,2)) AS DURCHLAUF_BETRAG, -- Durchlaufende Posten in EUR
  R.POS5NAME AS DURCHLAUF_BEZEICHNUNG,    -- Durchlaufende Posten: Bezeichnung
  R.POS5CHECK AS DURCHLAUF_AKTIV,         -- Durchlaufende Posten: Aktiv-Flag
  
  -- === POSITION 6: FREI DEFINIERBAR ===
  CAST(COALESCE(R.POS6, 0) AS NUMERIC(15,2)) AS FREI6_BETRAG, -- Frei definierbar 6 in EUR
  R.POS6NAME AS FREI6_BEZEICHNUNG,        -- Frei definierbar 6: Bezeichnung
  R.POS6CHECK AS FREI6_AKTIV,             -- Frei definierbar 6: Aktiv-Flag
  
  -- === POSITION 7: FREI DEFINIERBAR (WIEDERHERGESTELLT) ===
  CAST(COALESCE(R.POS7, 0) AS NUMERIC(15,2)) AS FREI7_BETRAG, -- Frei definierbar 7 in EUR
  R.POS7NAME AS FREI7_BEZEICHNUNG,        -- Frei definierbar 7: Bezeichnung
  R.POS7CHECK AS FREI7_AKTIV,             -- Frei definierbar 7: Aktiv-Flag
  
  -- === POSITION 8: FREI DEFINIERBAR (WIEDERHERGESTELLT) ===
  CAST(COALESCE(R.POS8, 0) AS NUMERIC(15,2)) AS FREI8_BETRAG, -- Frei definierbar 8 in EUR
  R.POS8NAME AS FREI8_BEZEICHNUNG,        -- Frei definierbar 8: Bezeichnung
  R.POS8CHECK AS FREI8_AKTIV,             -- Frei definierbar 8: Aktiv-Flag
  
  -- === POSITION 9: FREI DEFINIERBAR (WIEDERHERGESTELLT) ===
  CAST(COALESCE(R.POS9, 0) AS NUMERIC(15,2)) AS FREI9_BETRAG, -- Frei definierbar 9 in EUR
  R.POS9NAME AS FREI9_BEZEICHNUNG,        -- Frei definierbar 9: Bezeichnung
  R.POS9CHECK AS FREI9_AKTIV,             -- Frei definierbar 9: Aktiv-Flag
  
  -- === POSITION 10: FREI DEFINIERBAR (WIEDERHERGESTELLT) ===
  CAST(COALESCE(R.POS10, 0) AS NUMERIC(15,2)) AS FREI10_BETRAG, -- Frei definierbar 10 in EUR
  R.POS10NAME AS FREI10_BEZEICHNUNG,      -- Frei definierbar 10: Bezeichnung
  R.POS10CHECK AS FREI10_AKTIV,           -- Frei definierbar 10: Aktiv-Flag
  
  -- === GESAMTPOSITIONEN ===
  CAST(COALESCE(R.ANFSTAND, 0) AS NUMERIC(15,2)) AS ANFANGSSTAND, -- Anfangsstand in EUR
  CAST(COALESCE(R.ENDSTAND, 0) AS NUMERIC(15,2)) AS ENDSTAND,     -- Endstand in EUR
  CAST(COALESCE(R.ZUF, 0) AS NUMERIC(15,2)) AS ZUEFUEHRUNGEN,     -- Zuführungen in EUR
  CAST(COALESCE(R.ENTN, 0) AS NUMERIC(15,2)) AS ENTNAHMEN,        -- Entnahmen in EUR
  
  -- === SONDER-BEWEGUNGEN ===
  CAST(COALESCE(R.SONDERZUF, 0) AS NUMERIC(15,2)) AS SONDER_ZUEFUEHRUNG, -- Sonder-Zuführung in EUR
  CAST(COALESCE(R.SONDERENTN, 0) AS NUMERIC(15,2)) AS SONDER_ENTNAHME,   -- Sonder-Entnahme in EUR
  
  -- === BERECHNETE KENNZAHLEN (WIEDERHERGESTELLT) ===
  CAST(
    CASE 
      WHEN O.OANZEINH > 0 THEN COALESCE(R.ENDSTAND, 0) / O.OANZEINH 
      ELSE 0 
    END AS NUMERIC(10,2)
  ) AS RUECKLAGE_PRO_EINHEIT,            -- EUR pro Einheit: Echte Berechnung
  
  CAST(
    CASE 
      WHEN O.GA1 > 0 THEN COALESCE(R.ENDSTAND, 0) / O.GA1 
      ELSE 0 
    END AS NUMERIC(10,2)
  ) AS RUECKLAGE_PRO_QM,                 -- EUR pro m²: Echte Berechnung
  
  -- === STEUER-BERECHNUNGEN (WIEDERHERGESTELLT) ===
  CAST((COALESCE(R.POS2, 0) + COALESCE(R.POS3, 0) + COALESCE(R.POS4, 0)) AS NUMERIC(15,2)) AS STEUERBELASTUNG_GESAMT, -- Gesamte Steuerbelastung
  
  CAST((COALESCE(R.POS1, 0) - (COALESCE(R.POS2, 0) + COALESCE(R.POS3, 0) + COALESCE(R.POS4, 0))) AS NUMERIC(15,2)) AS NETTO_ZINSERTRAG, -- Netto-Zinsertrag nach Steuern
  
  -- === RÜCKLAGEN-BEWERTUNG (ERWEITERT) ===
  CASE 
    WHEN R.ENDSTAND < 1000 THEN 'SEHR NIEDRIG (<1K EUR)'
    WHEN R.ENDSTAND < 5000 THEN 'NIEDRIG (1K-5K EUR)'
    WHEN R.ENDSTAND < 20000 THEN 'MITTEL (5K-20K EUR)'
    WHEN R.ENDSTAND < 50000 THEN 'HOCH (20K-50K EUR)'
    WHEN R.ENDSTAND < 100000 THEN 'SEHR HOCH (50K-100K EUR)'
    ELSE 'MAXIMAL HOCH (>100K EUR)'
  END AS RUECKLAGE_BEWERTUNG,             -- Bewertung: Erweiterte Größenklassifikation
  
  -- === LIQUIDITÄTS-ANALYSE ===
  CASE
    WHEN COALESCE(R.ENDSTAND, 0) > 50000 THEN 'SEHR LIQUIDE'
    WHEN COALESCE(R.ENDSTAND, 0) > 20000 THEN 'GUT LIQUIDE'
    WHEN COALESCE(R.ENDSTAND, 0) > 5000 THEN 'AUSREICHEND LIQUIDE'
    WHEN COALESCE(R.ENDSTAND, 0) > 1000 THEN 'KNAPP LIQUIDE'
    ELSE 'ILLIQUIDE'
  END AS LIQUIDITAETS_STATUS,             -- Liquiditätsbewertung
  
  -- === ZEITRAUM ===
  R.DTVON AS PERIODE_VON,                 -- Periode von: Abrechnungsbeginn
  R.DTBIS AS PERIODE_BIS                  -- Periode bis: Abrechnungsende

FROM RUECKPOS R
  INNER JOIN OBJEKTE O ON R.ONR = O.ONR
WHERE 
  R.ONR < 890                             -- Ausschluss: Testobjekte
  AND R.NAME = 'Rücklagen'                -- Filter: Nur Hauptrücklagen
  -- Für spezifisches Objekt: AND R.ONR = 123
  -- Für Mindest-Rücklage: AND R.ENDSTAND >= 10000
  -- Für aktuelle Periode: AND R.DTBIS >= '2024-01-01'
ORDER BY 
  R.ENDSTAND DESC,                        -- Höchste Rücklagen zuerst (wiederhergestellt)
  R.ONR;                                  -- Dann nach Objektnummer

/*
ERWARTETES ERGEBNIS:
- Vollständige Rücklagen-Matrix aller WEGs mit allen 10 Positionen
- Echte EUR-Berechnungen für Kennzahlen (pro Einheit/m²)
- Steuerbehandlung der Kapitalerträge mit Netto-Berechnung
- Konten-Zuordnungen für Bankabstimmung
- Sonderbewegungen transparent mit EUR-Beträgen

GESCHÄFTSNUTZEN:
[OK] Vollständiges Rücklagen-Controlling mit allen Positionen
[OK] Steueroptimierung bei Kapitalerträgen mit Netto-Berechnung
[OK] Benchmark zwischen WEGs mit echten Kennzahlen
[OK] Basis für fundierte Beschlussvorlagen
[OK] Transparenz für Eigentümer mit vollständigen Daten
[OK] Liquiditätsanalyse für Finanzplanung

LAYER 4 RESTORATION ACHIEVEMENTS:
- Alle 10 Positionen (POS1-POS10) vollständig verfügbar
- NUMERIC(15,2) Präzision für alle Geldbeträge
- Echte Berechnungen statt Status-Indikatoren
- Konten-Zuordnungen (KZUF, KENTN, KNRP) wiederhergestellt
- Steuer- und Zinsberechnungen mit korrekter Mathematik
- Erweiterte Liquiditätsbewertung
- Korrekte Sortierung nach Rücklagenhöhe
- Flexible Filter-Parameter für verschiedene Analysen
*/