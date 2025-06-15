-- ============================================================================
-- QUERY 01: EIGENTÜMER (Enhanced) - Vollständige Eigentümer-Stammdaten
-- Layer 4 Version - Optimized for firebird-driver
-- ============================================================================
/*
BUSINESS PURPOSE: Komplette Eigentümer-Verwaltung mit Banking und Portfolio-Übersicht
MAIN TABLE: EIGADR (Eigentümer-Adressdaten)
KEY RELATIONSHIPS: 
  - EIGADR.EIGNR -> EIGENTUEMER.EIGNR (1:n - Ein Eigentümer kann mehrere Einheiten besitzen)
  - Special Value: EIGNR = -1 = Kollektive WEG-Eigentümerschaft
PERFORMANCE: Optimized with proper indexing on EIGNR
*/

SELECT 
  -- === IDENTIFIKATION ===
  EIGADR.EIGNR,                           -- PK: Eindeutige Eigentümer-ID (INTEGER)
  
  -- === NAMEN UND TITEL (Beide Eigentümer bei Miteigentum) ===
  EIGADR.EANREDE,                         -- Anrede Eigentümer 1 (VARCHAR): "Herr", "Frau", "Firma"
  EIGADR.EANREDE2,                        -- Anrede Eigentümer 2 (VARCHAR): Für Ehepaar/Partnerschaft
  EIGADR.ETITEL,                          -- Titel Eigentümer 1 (VARCHAR): "Dr.", "Prof.", akademische Grade
  EIGADR.ETITEL2,                         -- Titel Eigentümer 2 (VARCHAR): Zweiter Eigentümer bei Miteigentum
  EIGADR.EVNAME,                          -- Vorname Eigentümer 1 (VARCHAR): Haupteigentümer Vorname
  EIGADR.EVNAME2,                         -- Vorname Eigentümer 2 (VARCHAR): Miteigentümer Vorname
  EIGADR.ENAME,                           -- Nachname Eigentümer 1 (VARCHAR): Haupteigentümer Nachname
  EIGADR.ENAME2,                          -- Nachname Eigentümer 2 (VARCHAR): Miteigentümer Nachname
  EIGADR.EZUSATZ,                         -- Namenszusatz 1 (VARCHAR): "c/o", "z.Hd.", zusätzliche Adressierung
  EIGADR.EZUSATZ2,                        -- Namenszusatz 2 (VARCHAR): Für zweiten Eigentümer
  
  -- === KORRESPONDENZ (Professionelle Ansprache) ===
  EIGADR.EBRIEFAN,                        -- Briefanrede Eigentümer 1 (VARCHAR): "Sehr geehrter Herr Schmidt"
  EIGADR.EBRIEFAN2,                       -- Briefanrede Eigentümer 2 (VARCHAR): "Sehr geehrte Frau Schmidt"
  
  -- === FIRMEN-INFORMATION (Corporate Ownership) ===
  EIGADR.EFIRMA,                          -- Firmen-Flag (CHAR): "J"=Juristische Person, "N"=Privatperson
  EIGADR.EFIRMANAME,                      -- Firmenname (VARCHAR): GmbH, AG, etc. bei gewerblichen Eigentümern
  
  -- === ADRESSE ===
  EIGADR.ESTR,                            -- Straße und Hausnummer (VARCHAR): Vollständige Straßenadresse
  EIGADR.ELAND,                           -- Ländercode (CHAR): "D"=Deutschland, "A"=Österreich, etc.
  EIGADR.EPLZORT,                         -- PLZ und Ort (VARCHAR): "45127 Essen" - Deutsche Postleitzahl-Format
  
  -- === KONTAKTDATEN (Alle Kommunikationskanäle) ===
  EIGADR.ETEL1,                           -- Telefon 1 Eigentümer 1 (VARCHAR): Haupttelefonnummer
  EIGADR.ETEL2,                           -- Telefon 2 Eigentümer 1 (VARCHAR): Büro/Alternativ-Nummer
  EIGADR.EEMAIL,                          -- E-Mail Eigentümer 1 (VARCHAR): Haupte-Mail für Korrespondenz
  EIGADR.EHANDY,                          -- Handy Eigentümer 1 (VARCHAR): Mobile Nummer für Notfälle
  EIGADR.ETEL1EIG2,                       -- Telefon 1 Eigentümer 2 (VARCHAR): Miteigentümer Haupttelefon
  EIGADR.ETEL2EIG2,                       -- Telefon 2 Eigentümer 2 (VARCHAR): Miteigentümer Alternativnummer
  EIGADR.EHANDYEIG2,                      -- Handy Eigentümer 2 (VARCHAR): Miteigentümer Mobile
  EIGADR.EEMAILEIG2,                      -- E-Mail Eigentümer 2 (VARCHAR): Miteigentümer E-Mail
  
  -- === ENHANCED BANKING (SEPA-konforme Zahlungsabwicklung) ===
  EIGADR.EBANK,                           -- Bank 1 Name (VARCHAR): Name der Hausbank
  EIGADR.EBLZ,                            -- Bankleitzahl (VARCHAR): Deutsche BLZ für nationale Überweisungen
  EIGADR.EKONTO,                          -- Kontonummer (VARCHAR): Alte Kontonummer (pre-IBAN)
  EIGADR.EIBAN,                           -- IBAN (VARCHAR): Internationale Bankkontonummer für SEPA
  EIGADR.EBIC,                            -- BIC/SWIFT (VARCHAR): Bank Identifier Code für internationale Transfers
  EIGADR.EKONTOINH,                       -- Kontoinhaber (VARCHAR): Name auf Bankkonto (kann von Eigentümer abweichen!)
  EIGADR.SEPA_MAN_NR,                     -- SEPA Mandatsnummer (VARCHAR): Eindeutige Referenz für Lastschriften
  EIGADR.SEPA_MAN_DAT,                    -- SEPA Mandatsdatum (DATE): Datum der Mandatserteilung
  EIGADR.SEPA_MAN_ART,                    -- SEPA Mandatsart (VARCHAR): "E"=Einmalig, "W"=Wiederkehrend
  
  -- === PERSÖNLICHE DATEN ===
  EIGADR.GEBURTSDATUM,                    -- Geburtsdatum Eigentümer 1 (DATE): Für Altersverifikation
  EIGADR.GEBURTSDATUM2,                   -- Geburtsdatum Eigentümer 2 (DATE): Bei Miteigentum
  EIGADR.EIGENNUTZER_BEWNR,               -- Eigennutzer-Bewohner-Nr (INTEGER): Referenz wenn Eigentümer selbst bewohnt
  
  -- === BUSINESS NOTES ===
  EIGADR.ENOTIZ AS EIGENTUEMERKUERZEL,    -- Eigentümer-Kürzel (VARCHAR): "MJANZ", "RSWO" - Interne Referenz-Codes
  
  -- === PORTFOLIO ANALYTICS (Layer 4 Enhancement) ===
  COUNT(DISTINCT EIGENTUEMER.ONR) AS ANZAHL_OBJEKTE,        -- Anzahl Objekte: Verschiedene Gebäude im Portfolio
  COUNT(DISTINCT EIGENTUEMER.ONR || '-' || EIGENTUEMER.ENR) AS ANZAHL_EINHEITEN,  -- Anzahl Einheiten: Gesamte Wohnungen
  COUNT(CASE WHEN EIGENTUEMER.Z1 > 0 THEN 1 END) AS ANZAHL_EIGENTUMSEINHEITEN    -- Einheiten mit Eigentumsanteilen

FROM EIGADR
  LEFT JOIN EIGENTUEMER ON EIGADR.EIGNR = EIGENTUEMER.EIGNR
WHERE 
  EIGADR.EIGNR <> -1                      -- Ausschluss der kollektiven WEG-Eigentümerschaft (-1)
  AND EIGADR.EIGNR > 0                    -- Nur positive, gültige IDs
GROUP BY 
  EIGADR.EIGNR,
  EIGADR.EANREDE,
  EIGADR.EANREDE2,
  EIGADR.ETITEL,
  EIGADR.ETITEL2,
  EIGADR.EVNAME,
  EIGADR.EVNAME2,
  EIGADR.ENAME,
  EIGADR.ENAME2,
  EIGADR.EZUSATZ,
  EIGADR.EZUSATZ2,
  EIGADR.EBRIEFAN,
  EIGADR.EBRIEFAN2,
  EIGADR.EFIRMA,
  EIGADR.EFIRMANAME,
  EIGADR.ESTR,
  EIGADR.ELAND,
  EIGADR.EPLZORT,
  EIGADR.ETEL1,
  EIGADR.ETEL2,
  EIGADR.EEMAIL,
  EIGADR.EHANDY,
  EIGADR.ETEL1EIG2,
  EIGADR.ETEL2EIG2,
  EIGADR.EHANDYEIG2,
  EIGADR.EEMAILEIG2,
  EIGADR.EBANK,
  EIGADR.EBLZ,
  EIGADR.EKONTO,
  EIGADR.EIBAN,
  EIGADR.EBIC,
  EIGADR.EKONTOINH,
  EIGADR.SEPA_MAN_NR,
  EIGADR.SEPA_MAN_DAT,
  EIGADR.SEPA_MAN_ART,
  EIGADR.GEBURTSDATUM,
  EIGADR.GEBURTSDATUM2,
  EIGADR.EIGENNUTZER_BEWNR,
  EIGADR.ENOTIZ
ORDER BY 
  ANZAHL_EIGENTUMSEINHEITEN DESC,        -- Größte Portfolios zuerst
  EIGADR.ENAME;                          -- Alphabetisch nach Nachname

/*
EXPECTED RESULTS:
- Complete owner master data with enhanced banking
- Portfolio size analytics (object and unit counts)
- SEPA mandate information for payment processing
- Sorted by portfolio size for management focus

BUSINESS VALUE:
[OK] Vollständige Eigentümer-Verwaltung mit Bankverbindungen
[OK] SEPA-ready für automatische Zahlungsabwicklung  
[OK] Portfolio-Übersicht für Management-Entscheidungen
[OK] Optimiert für firebird-driver ohne Workarounds
*/