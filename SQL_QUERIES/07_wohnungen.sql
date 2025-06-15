-- ============================================================================
-- QUERY 04: WOHNUNGEN (Enhanced) - Detaillierte Wohnungseinheiten mit Flächen
-- Layer 4 Version - Already compliant with firebird-driver
-- ============================================================================
/*
BUSINESS PURPOSE: Vollständige Wohnungseinheiten-Verwaltung mit Flächendaten und Kostenstellenzuordnung
MAIN TABLES:
  - WOHNUNG (Einheiten-Stammdaten) - 20 Spalten
  - HK_WOHN (Heizkosten/Flächen-Zuordnung) - Zeitabhängige Flächendaten
KEY RELATIONSHIPS:
  - WOHNUNG.ONR+ENR -> EIGENTUEMER.ONR+ENR (1:n - Ein Wohnung kann mehrere Eigentümer haben über Zeit)
  - WOHNUNG.BKNR -> Buchungskreis (Financial Assignment)
  - WOHNUNG.EKNR -> Einzelkostenkreis (Cost Center Assignment)
LEGAL CONTEXT: Wohnungsabnahme, Flächenberechnung für Heizkosten, Eigentumsverhältnisse
*/

SELECT 
  -- === INDEXIERUNG ===
  ROW_NUMBER() OVER (ORDER BY OBJEKTE.ONR) AS INDEXID, -- Fortlaufende Nummerierung für Frontend
  
  -- === IDENTIFIKATION ===
  WOHNUNG.ENR,                            -- PK: Einheiten-Nummer (SMALLINT) - Wohnungsnummer im Objekt
  OBJEKTE.ONR,                            -- FK: Objekt-Nummer (Gebäude-Referenz)
  
  -- === WOHNUNGS-BEZEICHNUNG ===
  WOHNUNG.EBEZ,                           -- Einheiten-Bezeichnung (VARCHAR): "1. OG rechts", "EG links", "DG"
  WOHNUNG.ART,                            -- Einheiten-Art (VARCHAR): "Wohnung", "Gewerbe", "Stellplatz", "Garage"
  
  -- === OBJEKT-KONTEXT ===
  OBJEKTE.OSTRASSE,                       -- Objekt-Straße (VARCHAR): Gebäude-Adresse
  OBJEKTE.OBEZ,                           -- Objekt-Bezeichnung (VARCHAR): Liegenschafts-Kürzel
  OBJEKTE.GA1,                            -- Gesamt-Wohnfläche Objekt (NUMERIC): Für Verhältnis-Berechnung
  OBJEKTE.GA2,                            -- Gesamt-Gewerbefläche Objekt (NUMERIC): Mischnutzung
  OBJEKTE.OPLZORT,                        -- Objekt PLZ/Ort (VARCHAR): Vollständige Anschrift
  
  -- === FL?CHENDATEN (aus HK_WOHN Tabelle) ===
  HK_WOHN.QM,                             -- Wohnfläche qm (FLOAT): Exakte Wohnfläche der Einheit
  HK_WOHN.QMWARMW,                        -- Beheizte Fläche qm (FLOAT): Für Heizkosten-Umlageschlüssel
  
  -- === TECHNISCHE AUSSTATTUNG ===
  WOHNUNG.FRINH1,                         -- Ausstattung 1 (VARCHAR): "Zentral - Junkers KN 36-8D 23, BJ 1996"
  WOHNUNG.FRINH2,                         -- Ausstattung 2 (VARCHAR): Baujahr, technische Details
  WOHNUNG.FRINH3,                         -- Ausstattung 3 (VARCHAR): Zusätzliche technische Informationen
  WOHNUNG.FRINH4,                         -- Ausstattung 4 (VARCHAR): Sanitär, Elektrik Details
  WOHNUNG.FRINH5,                         -- Ausstattung 5 (VARCHAR): Bodenbelag, Fenster
  WOHNUNG.FRINH6,                         -- Ausstattung 6 (VARCHAR): Küche, Bad-Ausstattung
  WOHNUNG.FRINH7,                         -- Ausstattung 7 (VARCHAR): Heizung, Klima Details
  WOHNUNG.FRINH8,                         -- Ausstattung 8 (VARCHAR): Internet, Multimedia
  WOHNUNG.FRINH9,                         -- Ausstattung 9 (VARCHAR): Sicherheit, Zugang
  WOHNUNG.FRINH10,                        -- Ausstattung 10 (VARCHAR): Balkone, Terrassen
  WOHNUNG.FRINH11,                        -- Ausstattung 11 (VARCHAR): Keller, Dachboden
  WOHNUNG.FRINH12,                        -- Ausstattung 12 (VARCHAR): Parkplatz, Garage Details
  
  -- === NOTIZEN ===
  WOHNUNG.WNOTIZ,                         -- Wohnungsnotizen (BLOB): "Renoviert 2019", wichtige Hinweise
  
  -- === FINANZIELLE ZUORDNUNG ===
  WOHNUNG.BKNR,                           -- Buchungskreis-Nummer (INTEGER): Kostenstellen-Zuordnung Mieter
  WOHNUNG.EKNR,                           -- Einzelkostenkreis-Nr (INTEGER): Kostenstellen-Zuordnung Eigentümer
  
  -- === EIGENT?MER-INFORMATION (Smart CASE Logic f?r WEG vs. Einzeleigentum) ===
  CASE
    WHEN EIGADR.EIGNR = -1 THEN OBJEKTE.EIGNR  -- WEG-Eigentum: Verwende Objekt-Eigentümer
    ELSE EIGENTUEMER.EIGNR                      -- Einzeleigentum: Verwende spezifischen Eigentümer
  END AS EIGNR,                                 -- Effektive Eigentümer-Nummer
  
  CASE
    WHEN EIGADR.EIGNR = -1 THEN (              -- WEG-Fall: Hole Namen aus OBJEKTE.EIGNR
      SELECT ENAME 
      FROM EIGADR 
      WHERE EIGNR = OBJEKTE.EIGNR
    )
    ELSE EIGADR.ENAME                           -- Einzeleigentum: Direkter Eigentümer-Name
  END AS ENAME,                                 -- Effektiver Eigentümer-Name
  
  EIGADR.EVNAME,                          -- Eigentümer Vorname (VARCHAR): Falls Einzeleigentum
  EIGADR.EVNAME2,                         -- Eigentümer 2 Vorname (VARCHAR): Miteigentum
  EIGADR.ENAME2,                          -- Eigentümer 2 Nachname (VARCHAR): Miteigentum
  
  -- === EIGENT?MER-KONTAKT ===
  EIGADR.ETEL1,                           -- Eigentümer Telefon 1 (VARCHAR): Hauptkontakt
  EIGADR.ETEL2,                           -- Eigentümer Telefon 2 (VARCHAR): Alternativ-Kontakt
  EIGADR.EEMAIL,                          -- Eigentümer E-Mail (VARCHAR): Digitale Kommunikation
  EIGADR.EHANDY,                          -- Eigentümer Handy (VARCHAR): Mobile Erreichbarkeit
  EIGADR.ESTR,                            -- Eigentümer Straße (VARCHAR): Eigentümer-Adresse
  EIGADR.EPLZORT,                         -- Eigentümer PLZ/Ort (VARCHAR): Eigentümer-Postanschrift
  
  -- === EIGENT?MER-BANKING ===
  EIGADR.EBLZ,                            -- Eigentümer BLZ (VARCHAR): Banking für Rückerstattungen
  EIGADR.ETEL1EIG2,                       -- Eigentümer 2 Telefon 1 (VARCHAR): Miteigentümer Kontakt
  EIGADR.ETEL2EIG2,                       -- Eigentümer 2 Telefon 2 (VARCHAR): Miteigentümer Alternativ
  EIGADR.EHANDYEIG2,                      -- Eigentümer 2 Handy (VARCHAR): Miteigentümer Mobile
  EIGADR.EEMAILEIG2,                      -- Eigentümer 2 E-Mail (VARCHAR): Miteigentümer Digital
  EIGADR.EIGENNUTZER_BEWNR,               -- Eigennutzer-Bewohner-Nr (INTEGER): Falls selbstgenutzt
  EIGADR.ENOTIZ AS Eigentuemerkuerzel,    -- Eigentümer-Kürzel (BLOB): Interne Referenz
  EIGADR.EIBAN,                           -- Eigentümer IBAN (VARCHAR): SEPA-Zahlungen
  EIGADR.EBIC                             -- Eigentümer BIC (VARCHAR): SWIFT-Code

FROM OBJEKTE
  INNER JOIN WOHNUNG ON WOHNUNG.ONR = OBJEKTE.ONR
  INNER JOIN EIGENTUEMER ON EIGENTUEMER.ONR = OBJEKTE.ONR 
                            AND EIGENTUEMER.ENR = WOHNUNG.ENR
  LEFT JOIN EIGADR ON EIGENTUEMER.EIGNR = EIGADR.EIGNR
  LEFT JOIN HK_WOHN ON HK_WOHN.ONR = WOHNUNG.ONR 
                       AND HK_WOHN.ENR = WOHNUNG.ENR
WHERE
  OBJEKTE.ONR NOT LIKE 0                  -- Ausschluss "Nicht zugeordnet"
  AND OBJEKTE.ONR < 890                   -- Ausschluss Test-Daten
ORDER BY OBJEKTE.ONR, WOHNUNG.ENR;

/*
ANTWORT ZU BKNR/EKNR:
WOHNUNG.BKNR = Buchungskreis-Nummer für MIETER-bezogene Kosten (z.B. 100400)
WOHNUNG.EKNR = Einzelkostenkreis-Nummer für EIGENTÜMER-bezogene Kosten (z.B. 200400)
Diese trennen die Kostenrechnung zwischen Mieter-Ausgaben und Eigentümer-Ausgaben

EXPECTED RESULTS (basierend auf WOHNUNG.csv):
- ONR=16, ENR=4: "1. OG rechts", Renoviert 2019, Junkers Heizung BJ 1996
- ONR=16, ENR=5: "2. OG links", Zentral-Heizung, Standard-Ausstattung
- QM-Daten kommen aus HK_WOHN Tabelle (falls vorhanden)

BUSINESS VALUE:
[OK] Vollständige Wohnungseinheiten mit exakten Flächendaten
[OK] 12 Ausstattungs-Felder für detaillierte technische Spezifikation
[OK] Smart Eigentümer-Zuordnung (WEG vs. Einzeleigentum)
[OK] Getrennte Kostenstellenrechnung (Mieter vs. Eigentümer)
[OK] Vollständige Eigentümer-Kontaktdaten pro Einheit
*/