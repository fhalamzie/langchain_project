-- ============================================================================
-- QUERY 02: MIETER (Enhanced) - Vollständige Mieter-Stammdaten mit Verträgen
-- Layer 4 Version - Optimized for firebird-driver
-- ============================================================================
/*
BUSINESS PURPOSE: Komplette Mieter-Verwaltung mit Vertragsdaten, Banking und Miethistorie
MAIN TABLES: 
  - BEWADR (Bewohner-Adressdaten) - 56 Spalten
  - BEWOHNER (Mietverträge und Konditionen) - 208 Spalten
KEY RELATIONSHIPS:
  - BEWADR.BEWNR = BEWOHNER.BEWNR (1:1 - Adresse zu Vertrag)
  - BEWOHNER.ONR+ENR -> WOHNUNG.ONR+ENR (n:1 - Mehrere Verträge pro Wohnung über Zeit)
  - BEWOHNER.ONR+KNR+ENR = KONTEN.ONR+KNR+ENR (1:1 - Mieter-Konto-Zuordnung)
LEGAL CONTEXT: Mietrechtskonforme Datenverarbeitung, Kündigungsfristen, Kautionsmanagement
*/

SELECT 
  -- === IDENTIFIKATION ===
  BEWADR.BEWNR,                           -- PK: Eindeutige Bewohner-ID (INTEGER)
  BEWOHNER.ONR,                           -- FK: Objekt-Nummer (Gebäude-Referenz)
  BEWOHNER.KNR,                           -- FK: Konto-Nummer (Finanz-Referenz)  
  BEWOHNER.ENR,                           -- FK: Einheiten-Nummer (Wohnungs-Referenz)
  BEWOHNER.ID,                            -- Interne ID (INTEGER): System-interne Vertrags-ID
  
  -- === NAMEN UND ANREDE (Beide Mieter bei Partnerschaft) ===
  BEWADR.BANREDE,                         -- Anrede Mieter 1 (VARCHAR): "Herr", "Frau", "Firma"
  BEWADR.BANREDE2,                        -- Anrede Mieter 2 (VARCHAR): Partner/Ehegatte Anrede
  BEWADR.BBRIEFAN,                        -- Briefanrede Mieter 1 (VARCHAR): "Sehr geehrter Herr Müller"
  BEWADR.BBRIEFAN2,                       -- Briefanrede Mieter 2 (VARCHAR): "Sehr geehrte Frau Müller"
  BEWADR.BTITEL,                          -- Titel Mieter 1 (VARCHAR): Akademische Grade
  BEWADR.BTITEL2,                         -- Titel Mieter 2 (VARCHAR): Partner Titel
  BEWADR.BVNAME,                          -- Vorname Mieter 1 (VARCHAR): Hauptmieter Vorname
  BEWADR.BNAME,                           -- Nachname Mieter 1 (VARCHAR): Hauptmieter Nachname
  BEWADR.BVNAME2,                         -- Vorname Mieter 2 (VARCHAR): Partner/Ehegatte Vorname
  BEWADR.BNAME2,                          -- Nachname Mieter 2 (VARCHAR): Partner/Ehegatte Nachname
  BEWADR.BZUSATZ,                         -- Zusatz Mieter 1 (VARCHAR): Zusätzliche Adressierung
  BEWADR.BZUSATZ2,                        -- Zusatz Mieter 2 (VARCHAR): Partner-Zusatzinformation
  
  -- === FIRMEN-INFORMATION (Gewerbemieter) ===
  BEWADR.BFIRMA,                          -- Firmen-Flag (CHAR): "J"=Gewerbe, "N"=Privatmieter
  BEWADR.BFIRMANAME,                      -- Firmenname (VARCHAR): Bei gewerblicher Anmietung
  
  -- === ADRESSE ===
  BEWADR.BSTR,                            -- Straße Mieter 1 (VARCHAR): Meldeadresse (kann von Wohnadresse abweichen)
  BEWADR.BPLZORT,                         -- PLZ/Ort Mieter 1 (VARCHAR): Meldeadresse PLZ und Ort
  BEWADR.BSTR2,                           -- Straße Mieter 2 (VARCHAR): Separate Meldeadresse Partner
  
  -- === KONTAKTDATEN (Alle Kommunikationskanäle für beide Mieter) ===
  BEWADR.BTEL,                            -- Telefon 1 Mieter 1 (VARCHAR): Haupttelefonnummer
  BEWADR.BTEL2,                           -- Telefon 2 Mieter 1 (VARCHAR): Alternativ-/Büronummer
  BEWADR.BEMAIL,                          -- E-Mail Mieter 1 (VARCHAR): Hauptkommunikation E-Mail
  BEWADR.BHANDY,                          -- Handy Mieter 1 (VARCHAR): Mobile Nummer für Notfälle
  BEWADR.BTELBEW2,                        -- Telefon 1 Mieter 2 (VARCHAR): Partner Haupttelefon
  BEWADR.BTEL2BEW2,                       -- Telefon 2 Mieter 2 (VARCHAR): Partner Alternativnummer
  BEWADR.BEMAILBEW2,                      -- E-Mail Mieter 2 (VARCHAR): Partner E-Mail
  BEWADR.BHANDYBEW2,                      -- Handy Mieter 2 (VARCHAR): Partner Mobile
  
  -- === BANKING (Mieter-Zahlungsabwicklung) ===
  BEWADR.BBANK,                           -- Bank Name (VARCHAR): "Sparkasse Essen" - Hausbank des Mieters
  BEWADR.BBLZ,                            -- Bankleitzahl (VARCHAR): Deutsche BLZ für Rückzahlungen/Kaution
  BEWADR.BKONTO,                          -- Kontonummer (VARCHAR): Bankkonto für Rückerstattungen
  BEWADR.BBIC,                            -- BIC Code (VARCHAR): SWIFT Code für SEPA-Überweisungen
  BEWADR.BIBAN,                           -- IBAN (VARCHAR): Internationale Kontonummer
  BEWADR.BKONTOINH,                       -- Kontoinhaber (VARCHAR): Name auf Bankkonto (Rechtssicherheit!)
  
  -- === VERTRAGSDATEN (Mietvertrag-Kerninfo) ===
  BEWOHNER.VABSCHLUS,                     -- Vertragsabschluss (DATE): Datum der Vertragsunterzeichnung
  BEWOHNER.VBEGINN,                       -- Mietbeginn (DATE): Start des Mietverhältnisses
  BEWOHNER.VENDE,                         -- Mietende (DATE): Ende-Datum (NULL = unbefristet/aktiv)
  CAST(
    CASE 
      WHEN BEWOHNER.VENDE IS NULL THEN 'Unbefristet'
      WHEN BEWOHNER.VENDE < CURRENT_DATE THEN 'Beendet'
      ELSE 'Aktiv bis ' || CAST(BEWOHNER.VENDE AS VARCHAR(10))
    END AS VARCHAR(50)
  ) AS VERTRAGSSTATUS,                    -- Berechneter Vertragsstatus
  
  -- === MIETKOSTEN (Aktuelle Miete und Aufschlüsselung) ===
  BEWOHNER.Z1 AS KALTMIETE,               -- Kaltmiete (NUMERIC 15,2): Nettomiete ohne Nebenkosten
  BEWOHNER.Z2 AS GARAGENMIETE,            -- Garage/Stellplatz (NUMERIC 15,2): Zusätzliche Stellplatzkosten
  BEWOHNER.Z3 AS BETRIEBSKOSTEN,          -- Betriebskosten (NUMERIC 15,2): Nebenkosten-Vorauszahlung
  BEWOHNER.Z4 AS HEIZKOSTEN,              -- Heizkosten (NUMERIC 15,2): Heiz-/Warmwasser-Vorauszahlung
  (COALESCE(BEWOHNER.Z1, 0) + COALESCE(BEWOHNER.Z2, 0) + 
   COALESCE(BEWOHNER.Z3, 0) + COALESCE(BEWOHNER.Z4, 0)) AS WARMMIETE_AKTUELL,  -- Gesamtmiete
  BEWOHNER.MIETE1,                        -- Aktuelle Miete 1 (NUMERIC 15,2): Erste Mietstufe
  BEWOHNER.MIETE2,                        -- Miete 2 (NUMERIC 15,2): Zweite Mietstufe
  BEWOHNER.MIETE3,                        -- Miete 3 (NUMERIC 15,2): Dritte Mietstufe
  BEWOHNER.MIETE4,                        -- Miete 4 (NUMERIC 15,2): Vierte Mietstufe
  BEWOHNER.MIETDATUM1,                    -- Mietdatum 1 (DATE): Gültigkeitsdatum der aktuellen Miete
  BEWOHNER.MIETDATUM2,                    -- Mietdatum 2 (DATE): Zweite Mietstufe
  BEWOHNER.MIETDATUM3,                    -- Mietdatum 3 (DATE): Dritte Mietstufe
  BEWOHNER.MIETDATUM4,                    -- Mietdatum 4 (DATE): Vierte Mietstufe
  
  -- === PERSÖNLICHE DATEN ===
  BEWADR.GEBURTSDATUM,                    -- Geburtsdatum Mieter 1 (DATE): Altersverifikation
  BEWADR.GEBURTSDATUM2,                   -- Geburtsdatum Mieter 2 (DATE): Partner Geburtsdatum
  
  -- === KONTOSTAND (Aktuelle Forderungen/Guthaben) ===
  KONTEN.KBRUTTO AS MIETSCHULDEN,         -- Kontosaldo (NUMERIC 15,2): Aktueller Saldo (positiv=Schulden)
  CASE 
    WHEN KONTEN.KBRUTTO > 0 THEN 'Schulden'
    WHEN KONTEN.KBRUTTO < 0 THEN 'Guthaben'
    ELSE 'Ausgeglichen'
  END AS ZAHLUNGSSTATUS,                  -- Zahlungsstatus-Indikator
  
  -- === VERTRAGSZUSATZINFO ===
  CAST(BEWOHNER.VNOTIZ AS VARCHAR(2000)) AS VERTRAGSNOTIZ,  -- Vertragsnotizen (BLOB->VARCHAR)
  
  -- === OBJEKTZUORDNUNG ===
  WOHNUNG.EBEZ AS LAGE,                   -- Lage-Bezeichnung (VARCHAR): "1. OG rechts", "EG links"
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- Liegenschafts-Kürzel (VARCHAR): "RSWO", "KUPFE190"
  EIGADR.ENOTIZ AS EIGENTUEMERKUERZEL     -- Eigentümer-Kürzel: Zugehöriger Eigentümer

FROM BEWADR
  RIGHT OUTER JOIN BEWOHNER ON (BEWADR.BEWNR = BEWOHNER.BEWNR)
  LEFT OUTER JOIN KONTEN ON (BEWOHNER.ONR = KONTEN.ONR 
                             AND BEWOHNER.KNR = KONTEN.KNR 
                             AND BEWOHNER.ENR = KONTEN.ENR)
  LEFT OUTER JOIN WOHNUNG ON (BEWOHNER.ONR = WOHNUNG.ONR 
                              AND BEWOHNER.ENR = WOHNUNG.ENR)
  LEFT OUTER JOIN OBJEKTE ON (BEWOHNER.ONR = OBJEKTE.ONR)
  LEFT OUTER JOIN EIGADR ON (OBJEKTE.EIGNR = EIGADR.EIGNR)
WHERE
  BEWADR.BEWNR >= 0                       -- Gültige Bewohner-Nummern
  AND KONTEN.KUSCHLNR1 = -1              -- Standard-Umlageschlüssel
  AND (BEWOHNER.VENDE >= CURRENT_DATE     -- Aktive Verträge (Ende in Zukunft)
       OR BEWOHNER.VENDE IS NULL)         -- oder unbefristete Verträge
ORDER BY BEWADR.BEWNR;

/*
EXPECTED RESULTS (basierend auf BEWADR.csv + BEWOHNER Sample):
- Row 1: Anojan Vallipuram (BEWNR=291, Aktiv, Handy: 015221881973)
- Row 2: Christoph Otten (BEWNR=292, Sparkasse Banking, Handy: 017698438539)
- Row 3: Ljubica Sijakovic (BEWNR=293, E-Mail: mag.sijako@gmx.de, SEPA Banking)

BUSINESS VALUE:
[OK] Vollständige Mieter-Verwaltung mit Vertragsstatus
[OK] Banking-Integration für Kautionsrückzahlungen
[OK] Aktuelle Mietkosten und Aufschlüsselung mit Warmmiete
[OK] Professionelle Korrespondenz durch Briefanreden
[OK] Partnerschaft/Ehepaar vollständig abgebildet
[OK] Erweiterte Felder aus Layer 2 wiederhergestellt
[OK] NUMERIC-Berechnungen für firebird-driver optimiert
*/