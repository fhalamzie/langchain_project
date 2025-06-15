-- ============================================================================
-- QUERY 03: OBJEKTE (Enhanced) - Vollständige Objekt-Verwaltung mit Finanzen
-- Layer 4 Version - Already compliant with firebird-driver
-- ============================================================================
/*
BUSINESS PURPOSE: Umfassende Objektverwaltung mit Finanzdaten, Verwalter-Info und technischen Specs
MAIN TABLE: OBJEKTE (Property Master Data) - 361 Spalten total!
KEY RELATIONSHIPS:
  - OBJEKTE.ONR -> WOHNUNG.ONR (1:n - Ein Objekt hat mehrere Wohneinheiten)
  - OBJEKTE.EIGNR -> EIGADR.EIGNR (n:1 - Mehrere Objekte pro Eigentümer möglich)
  - OBJEKTE.VERWNR -> VERWALTER.NR (n:1 - Verwalter-Zuordnung)
LEGAL CONTEXT: WEG-Verwaltung, Rücklagen-Verwaltung, Verwalterbestellung
*/

SELECT 
  -- === IDENTIFIKATION ===
  OBJEKTE.ONR,                            -- PK: Objekt-Nummer (SMALLINT) - Eindeutige Gebäude-ID
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- Objekt-Bezeichnung (VARCHAR): "RSWO", "KUPFE190" - Interne Referenz
  
  -- === ADRESSE ===
  OBJEKTE.OSTRASSE,                       -- Straße (VARCHAR): Vollständige Gebäude-Adresse
  OBJEKTE.OPLZORT,                        -- PLZ/Ort (VARCHAR): Postleitzahl und Ortsbezeichnung
  
  -- === TECHNISCHE DATEN ===
  OBJEKTE.OANZEINH,                       -- Anzahl Einheiten (INTEGER): Gesamtzahl Wohneinheiten im Gebäude
  OBJEKTE.GA1 AS WOHNFLAECHE,             -- Wohnfläche gesamt (NUMERIC): Gesamte Wohnfläche aller Einheiten
  OBJEKTE.GA2 AS GEWERBE_TEILWEISE,       -- Gewerbefläche (NUMERIC): Gewerblich genutzte Fläche
  OBJEKTE.ART,                            -- Objektart (VARCHAR): "Wohnhaus", "Mischnutzung", "Gewerbe"
  
  -- === FINANZKONTEN (Objektspezifische Banking) ===
  OBJEKTE.BANK,                           -- Bank Name (VARCHAR): Hausbank für Objektfinanzen
  OBJEKTE.KTO,                            -- Konto-Nummer (VARCHAR): Hausgeld-Sammelkonto
  OBJEKTE.BLZ,                            -- Bankleitzahl (VARCHAR): BLZ der Objektbank
  OBJEKTE.KTOSTAND,                       -- Kontostand (NUMERIC 15,2): Aktueller Kontostand Hausgeld-Konto
  OBJEKTE.KTOASTAND,                      -- Kontostand Datum (DATE): Stand-Datum der Kontosaldo-Information
  
  -- === R?CKLAGEN (WEG-Pflicht R?cklagen-Verwaltung) ===
  OBJEKTE.RKTOSTAND,                      -- Rücklagen-Kontostand (NUMERIC 15,2): Aktueller Rücklagen-Saldo
  OBJEKTE.RKTOASTAND,                     -- Rücklagen Stand-Datum (DATE): Datum der Rücklagen-Information
  
  -- === VERWALTER-INFORMATION (Professionelle Verwaltung) ===
  OBJEKTE.VERWNR,                         -- Verwalter-Nummer (INTEGER): FK zu VERWALTER Tabelle
  OBJEKTE.VERWNAME,                       -- Verwalter Name (VARCHAR): Ansprechpartner Name
  OBJEKTE.VERWFIRMA,                      -- Verwalter Firma (VARCHAR): Verwaltungsunternehmen
  OBJEKTE.VERWTEL,                        -- Verwalter Telefon (VARCHAR): Haupttelefonnummer Verwaltung
  OBJEKTE.VERWEMAIL,                      -- Verwalter E-Mail (VARCHAR): Kontakt E-Mail Verwaltung
  
  -- === VERWALTUNGSPERIODE (Vertrags-Management) ===
  OBJEKTE.VERWALTUNGSBEGINN,              -- Verwaltung Start (DATE): Beginn der Verwaltungsbestellung
  OBJEKTE.VERWALTUNGSENDE,                -- Verwaltung Ende (DATE): Ende der Verwaltungsbestellung
  
  -- === FREITEXT-FELDER (Objektspezifische Informationen) ===
  OBJEKTE.FRINH1 AS OBJEKTFREITEXT1,      -- Freitext 1 (VARCHAR): Zusätzliche Objektbeschreibung
  OBJEKTE.FRINH2 AS OBJEKTFREITEXT2,      -- Freitext 2 (VARCHAR): Technische Details, Besonderheiten
  OBJEKTE.FRINH3 AS OBJEKTFREITEXT3,      -- Freitext 3 (VARCHAR): Historische Informationen
  OBJEKTE.FRINH4 AS OBJEKTFREITEXT4,      -- Freitext 4 (VARCHAR): Wartungshinweise
  OBJEKTE.FRINH5 AS OBJEKTFREITEXT5,      -- Freitext 5 (VARCHAR): Sondervereinbarungen
  OBJEKTE.FRINH6 AS OBJEKTFREITEXT6,      -- Freitext 6 (VARCHAR): Versicherungsdetails
  OBJEKTE.FRINH7 AS OBJEKTFREITEXT7,      -- Freitext 7 (VARCHAR): Energieausweis-Informationen
  OBJEKTE.FRINH8 AS OBJEKTFREITEXT8,      -- Freitext 8 (VARCHAR): Umwelt-/Nachhaltigkeits-Info
  OBJEKTE.FRINH9 AS OBJEKTFREITEXT9,      -- Freitext 9 (VARCHAR): Modernisierungsplanung
  OBJEKTE.FRINH10 AS OBJEKTFREITEXT10,    -- Freitext 10 (VARCHAR): Rechtliche Hinweise
  OBJEKTE.FRINH11 AS OBJEKTFREITEXT11,    -- Freitext 11 (VARCHAR): Mietrecht-Spezialitäten
  OBJEKTE.FRINH12 AS OBJEKTFREITEXT12,    -- Freitext 12 (VARCHAR): WEG-Besonderheiten
  
  -- === EIGENT?MER-ZUORDNUNG ===
  EIGADR.EIGNR,                           -- Eigentümer-Nummer (INTEGER): Haupt-Eigentümer des Objekts
  EIGADR.EVNAME,                          -- Eigentümer Vorname (VARCHAR): Bei Einzeleigentum
  EIGADR.EVNAME2,                         -- Eigentümer 2 Vorname (VARCHAR): Bei Miteigentum
  EIGADR.ENAME,                           -- Eigentümer Nachname (VARCHAR): Haupteigentümer
  EIGADR.ENAME2,                          -- Eigentümer 2 Nachname (VARCHAR): Miteigentümer
  CAST(EIGADR.ENOTIZ AS VARCHAR(2000)) AS EIGENTUEMERKUERZEL -- Eigentümer-Kürzel (BLOB->VARCHAR): Interne Eigentümer-Referenz

FROM OBJEKTE
  INNER JOIN EIGADR ON (OBJEKTE.EIGNR = EIGADR.EIGNR)
WHERE
  OBJEKTE.ONR <> 0                        -- Ausschluss der "0" (Nicht zugeordnet)
  AND OBJEKTE.ONR < 890                   -- Ausschluss von Test-/System-Objekten (ONR >= 890)
ORDER BY OBJEKTE.ONR;

/*
EXPECTED RESULTS (basierend auf OBJEKTE.csv Sample):
ONR=0 wird ausgeschlossen (Nicht zugeordnet)
Reale Objekte haben umfangreiche Finanz- und Verwaltungsstrukturen

BUSINESS VALUE:
[OK] Vollständige Objektfinanzen (Hausgeld + Rücklagen)
[OK] Verwalter-Integration mit Kontaktdaten
[OK] Technische Gebäudedaten für Wartungsplanung
[OK] 12 Freitext-Felder für objektspezifische Details
[OK] WEG-konforme Rücklagen-Verwaltung
[OK] Verwaltungsvertrags-Management mit Laufzeiten
*/