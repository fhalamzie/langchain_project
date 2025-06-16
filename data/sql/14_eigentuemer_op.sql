-- ============================================================================
-- QUERY 07: EIGENTÜMER OFFENE POSTEN (Enhanced) - Detailliertes Forderungsmanagement
-- Layer 4 Version - Added missing ENOTIZ field with proper casting
-- ============================================================================
/*
BUSINESS PURPOSE: Professionelles Forderungsmanagement für WEG-Eigentümer
MAIN TABLES: KONTEN + EIGENTUEMER + EIGADR
KEY RELATIONSHIPS: Kombiniert Konten-Salden mit Eigentümer-Stammdaten
LEGAL CONTEXT: WEG-Beitragszahlungen, Mahnverfahren, Vollstreckung
*/

SELECT DISTINCT 
  -- === OBJEKTZUORDNUNG ===
  KONTEN.ONR,                             -- FK: Objekt-Nummer (SMALLINT)
  KONTEN.KNR,                             -- FK: Konto-Nummer (INTEGER)
  KONTEN.ENR,                             -- FK: Einheiten-Nummer (SMALLINT) - Wichtig für Einheiten-spezifische OPs
  
  -- === KONTOBESCHREIBUNG ===
  KONTEN.KBEZ AS WOHNUNG,                 -- Kontobeschreibung (VARCHAR): "Mustermann, Max EG"
  KONTEN.KNRSTR,                          -- Konto-String (VARCHAR): "E.001.00" - Lesbare Konto-Referenz
  
  -- === FORDERUNGSDETAILS ===
  KONTEN.KBRUTTO AS OffenerPosten,        -- Hauptsaldo (NUMERIC 15,2): Gesamtschuld/Guthaben
  KONTEN.OPBETRAG,                        -- OP-Betrag (NUMERIC 15,2): Spezifischer offener Posten
  
  -- === MAHNWESEN ===
  KONTEN.KMAHNSTUFE,                      -- Mahnstufe (SMALLINT): 0-3 Eskalationsstufe
  KONTEN.MAHNDATUM,                       -- Mahndatum (DATE): Letztes Mahndatum
  KONTEN.MAHNGEDRUCKT,                    -- Mahnung versendet (CHAR): "J"/"N"
  
  -- === EIGENT?MER-INFORMATION ===
  EIGADR.EIGNR,                            -- Eigentümer-Nummer (INTEGER)
  EIGADR.ENAME,                           -- Eigentümer Nachname (VARCHAR): Haupteigentümer
  EIGADR.EVNAME,                          -- Eigentümer Vorname (VARCHAR): Haupteigentümer
  EIGADR.ENAME2,                          -- Eigentümer 2 Nachname (VARCHAR): Miteigentum
  EIGADR.EVNAME2,                         -- Eigentümer 2 Vorname (VARCHAR): Miteigentum
  EIGADR.EFIRMANAME,                      -- Firmenname (VARCHAR): Bei gewerblichen Eigentümern
  
  -- === EIGENT?MER-KONTAKT ===
  EIGADR.ETEL1,                           -- Telefon 1 (VARCHAR): Für Mahnkontakt
  EIGADR.EEMAIL,                          -- E-Mail (VARCHAR): Digitale Mahnung
  EIGADR.ESTR,                            -- Straße (VARCHAR): Postanschrift für Mahnungen
  EIGADR.EPLZORT,                         -- PLZ/Ort (VARCHAR): Vollständige Postanschrift
  
  -- === EIGENTUEMER-REFERENZ ===
  CAST(EIGADR.ENOTIZ AS VARCHAR(2000)) AS EIGENTUEMERKUERZEL,  -- Eigentümer-Kürzel (BLOB->VARCHAR): "MJANZ", "RSWO"
  
  -- === OBJEKTKONTEXT ===
  OBJEKTE.OBEZ AS Liegenschaftskuerzel,   -- Liegenschafts-Kürzel (VARCHAR)
  OBJEKTE.OSTRASSE,                       -- Objekt-Straße (VARCHAR)
  OBJEKTE.OPLZORT,                        -- Objekt PLZ/Ort (VARCHAR)
  
  -- === RISIKOBEWERTUNG (Calculated Fields) ===
  CASE 
    WHEN KONTEN.KBRUTTO > 0 AND KONTEN.KMAHNSTUFE = 0 THEN 'Zahlungsverzug ohne Mahnung'
    WHEN KONTEN.KBRUTTO > 0 AND KONTEN.KMAHNSTUFE = 1 THEN 'Erste Mahnung erfolgt'
    WHEN KONTEN.KBRUTTO > 0 AND KONTEN.KMAHNSTUFE = 2 THEN 'Zweite Mahnung - Risiko erhoeht'
    WHEN KONTEN.KBRUTTO > 0 AND KONTEN.KMAHNSTUFE = 3 THEN 'Letzte Mahnung - Inkasso-Gefahr'
    WHEN KONTEN.KBRUTTO < 0 THEN 'Guthaben (UEberzahlung)'
    ELSE 'Konto ausgeglichen'
  END AS RISIKOSTATUS,                    -- Calculated: Risiko-Klassifikation
  
  -- === TAGE ?BERF?LLIG (Simplified Calculation) ===
  CASE 
    WHEN KONTEN.MAHNDATUM IS NOT NULL AND KONTEN.KBRUTTO > 0 
    THEN CURRENT_DATE - KONTEN.MAHNDATUM
    ELSE 0
  END AS TAGE_SEIT_MAHNUNG                -- Calculated: Tage seit letzter Mahnung

FROM EIGADR
  INNER JOIN EIGADR ON (EIGENTUEMER.EIGNR = EIGADR.EIGNR)
  INNER JOIN KONTEN ON (EIGENTUEMER.ONR = KONTEN.ONR 
                       AND EIGENTUEMER.KNR = KONTEN.KNR 
                       AND EIGENTUEMER.ENR = KONTEN.ENR)
  INNER JOIN OBJEKTE ON (OBJEKTE.ONR = KONTEN.ONR)
WHERE
  EIGENTUEMER.ONR NOT LIKE 0              -- Ausschluss "Nicht zugeordnet"
  AND EIGENTUEMER.ONR < 890               -- Ausschluss Test-Objekte
  AND EIGENTUEMER.EIGNR NOT LIKE -1        -- Ausschluss kollektive WEG-Eigentümerschaft
  AND KONTEN.KUSCHLNR1 = -1               -- Standard-Umlageschlüssel
  AND KONTEN.KUST = 0                     -- Ausschluss USt-Konten
  AND KONTEN.KKLASSE = 62                 -- Nur Eigentümer-Konten (nicht Mieter/Sachkonten)
ORDER BY KONTEN.KBRUTTO DESC, KONTEN.KMAHNSTUFE DESC;

/*
EXPECTED RESULTS (basierend auf WEG_EIGENTUEMER_OP_SQL.csv):
- Sundeki Immobilien: -17.136,69 EUR (Guthaben/Überzahlung)
- Weitere Eigentümer: Meist ausgeglichene Konten (0.00 EUR)

BUSINESS VALUE:
[OK] Vollständiges Forderungsmanagement mit Mahnstatus
[OK] Eigentümer-Kontaktdaten für Mahnwesen
[OK] Risiko-Klassifikation für Portfoliomanagement
[OK] Einheiten-spezifische Zuordnung (ENR-Feld hinzugefügt)
[OK] Unterscheidung zwischen Schulden und Guthaben
*/