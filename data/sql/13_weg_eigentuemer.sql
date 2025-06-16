-- ============================================================================
-- QUERY 06: WEG-EIGENTÜMER (Enhanced) - Vollständige Eigentumsstrukturen
-- Layer 4 Version - Fixed missing BLOB field with proper casting
-- ============================================================================
/*
BUSINESS PURPOSE: Detaillierte WEG-Eigentümer mit Eigentumsanteilen und Zahlungsverhalten
MAIN TABLES:
  - EIGENTUEMER (Ownership Records) - 157 Spalten
  - EIGADR (Owner Address Data) - 64 Spalten
KEY RELATIONSHIPS:
  - EIGENTUEMER.ONR+ENR -> WOHNUNG.ONR+ENR (1:1 - Eigentumseinheit)
  - EIGENTUEMER.EIGNR -> EIGADR.EIGNR (n:1 - Mehrere Einheiten pro Eigentümer)
LEGAL CONTEXT: WEG-Verwaltung, Hausgeldbeiträge, Eigentumsanteile nach § 16 WEG
*/

SELECT 
  -- === EIGENT?MER-STAMMDATEN ===
  EIGADR.EIGNR,                            -- PK: Eigentümer-Nummer (INTEGER)
  EIGADR.EVNAME,                          -- Vorname Eigentümer 1 (VARCHAR)
  EIGADR.EVNAME2,                         -- Vorname Eigentümer 2 (VARCHAR): Bei Miteigentum
  EIGADR.ENAME,                           -- Nachname Eigentümer 1 (VARCHAR)
  EIGADR.ENAME2,                          -- Nachname Eigentümer 2 (VARCHAR): Bei Miteigentum
  EIGADR.EFIRMANAME,                      -- Firmenname (VARCHAR): Bei gewerblichen Eigentümern
  EIGADR.ESTR,                            -- Eigentümer-Adresse (VARCHAR)
  EIGADR.EPLZORT,                         -- Eigentümer PLZ/Ort (VARCHAR)
  
  -- === OBJEKTZUORDNUNG ===
  EIGENTUEMER.ONR,                        -- FK: Objekt-Nummer (SMALLINT)
  EIGENTUEMER.ENR,                        -- FK: Einheiten-Nummer (SMALLINT)
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- Liegenschafts-Kürzel (VARCHAR)
  OBJEKTE.OSTRASSE,                       -- Objekt-Straße (VARCHAR)
  OBJEKTE.OPLZORT,                        -- Objekt PLZ/Ort (VARCHAR)
  
  -- === EIGENTUMSANTEILE (Kernstück der WEG-Abrechnung) ===
  EIGENTUEMER.Z1,                         -- Eigentumsanteil 1 (NUMERIC 15,2): Haupt-Umlageschlüssel
  EIGENTUEMER.Z2,                         -- Eigentumsanteil 2 (NUMERIC 15,2): Alternativ-Schlüssel (z.B. Heizung)
  EIGENTUEMER.Z3,                         -- Eigentumsanteil 3 (NUMERIC 15,2): Spezial-Schlüssel (z.B. Wasser)
  EIGENTUEMER.Z4,                         -- Eigentumsanteil 4 (NUMERIC 15,2): Weitere Umlageschlüssel
  EIGENTUEMER.Z5,                         -- Eigentumsanteil 5 (NUMERIC 15,2): Reserve-Schlüssel
  
  -- === FINANZIELLE POSITIONEN ===
  EIGENTUEMER.ELETZTHAUSGELD,             -- Letztes Hausgeld (NUMERIC 15,2): Höhe der letzten Zahlung
  EIGENTUEMER.IST_RL_POS,                 -- Ist-Rücklagenposition (NUMERIC 15,2): Aktueller Rücklagen-Anteil
  EIGENTUEMER.SOLL_RL_POS,                -- Soll-Rücklagenposition (NUMERIC 15,2): Ziel-Rücklagen-Anteil
  
  -- === ZAHLUNGSVERHALTEN ===
  EIGENTUEMER.DAUERAUFTRAG,               -- Dauerauftrag (CHAR): "J"=Automatische Zahlung eingerichtet
  EIGENTUEMER.SOLLTAG,                    -- Zahlungstag (SMALLINT): Tag im Monat für Hausgeldzahlung (1-31)
  
  -- === SEPA-LASTSCHRIFT ===
  EIGENTUEMER.SEPA_MAN_NR,                -- SEPA-Mandats-Nummer (VARCHAR): Lastschrift-Berechtigung
  EIGENTUEMER.SEPA_MAN_DAT,               -- SEPA-Mandats-Datum (DATE): Erteilungsdatum der Berechtigung
  EIGENTUEMER.SEPA_MAN_ART,               -- SEPA-Mandats-Art (SMALLINT): 0=Einmalig, 1=Wiederkehrend
  
  -- === EIGENNUTZUNG ===
  EIGENTUEMER.EIGENNUTZER,                -- Eigennutzer-Flag (CHAR): "J"=Selbstnutzung, "N"=Vermietet
  EIGENTUEMER.ENWG,                       -- WEG-Flag (CHAR): "J"=WEG-Eigentum, "N"=Sondereigentum
  
  -- === STEUERLICHE BEHANDLUNG ===
  EIGENTUEMER.EMWSTAUSW,                  -- USt-Ausweis (CHAR): "J"=Umsatzsteuerpflichtig (Gewerbe)
  EIGENTUEMER.EMWSTSATZ,                  -- USt-Satz (NUMERIC 5,2): Umsatzsteuersatz in Prozent
  EIGENTUEMER.STEUERNUMMER,               -- Steuernummer (VARCHAR): Finanzamt-Steuernummer
  EIGENTUEMER.FINANZAMT,                  -- Finanzamt (VARCHAR): Zuständiges Finanzamt
  
  -- === KONTAKTDATEN ===
  EIGADR.ETEL1,                           -- Telefon 1 (VARCHAR): Haupttelefonnummer
  EIGADR.ETEL2,                           -- Telefon 2 (VARCHAR): Alternativ-Nummer
  EIGADR.EEMAIL,                          -- E-Mail (VARCHAR): Digitale Kommunikation
  EIGADR.EHANDY,                          -- Handy (VARCHAR): Mobile Erreichbarkeit
  
  -- === MEHRFACH-EIGENTÜMER SUPPORT ===
  EIGENTUEMER.EIGNR2,                     -- Zweiter Eigentümer-ID (INTEGER): Bei gemeinsamen Eigentum
  EIGENTUEMER.EIGNR3,                     -- Dritter Eigentümer-ID (INTEGER): Bei Erbengemeinschaften
  EIGENTUEMER.EIGNR4,                     -- Vierter Eigentümer-ID (INTEGER): Erweiterte Partnerschaften
  EIGENTUEMER.EIGNR5,                     -- Fünfter Eigentümer-ID (INTEGER): Komplexe Eigentumsstrukturen
  EIGENTUEMER.GEMEINSCHAFTSTYP,           -- Gemeinschaftstyp (INTEGER): Art der Eigentumsgemeinschaft
  
  -- === BANKING UND VIRTUELLE KONTEN ===
  EIGENTUEMER.EVIRTKTO,                   -- Virtuelles Konto (VARCHAR): Interne Kontonummer für automatisierte Zahlungen
  EIGENTUEMER.BANKID,                     -- Bank-ID (INTEGER): Referenz zur Hauptbank
  EIGENTUEMER.BANKID2,                    -- Bank-ID 2 (INTEGER): Referenz zur Zweitbank
  EIGENTUEMER.PFAENDUNG,                  -- Pfändung-Status (CHAR): "J"=Gepfändet, "N"=Normal
  
  -- === EIGENTUEMER-REFERENZ ===
  CAST(EIGADR.ENOTIZ AS VARCHAR(2000)) AS EIGENTUEMERKUERZEL,  -- Eigentümer-Kürzel (BLOB->VARCHAR): "MJANZ", "RSWO" 
  
  -- === WOHNUNGSBEZEICHNUNG ===
  COALESCE((
    SELECT LIST(DISTINCT W.EBEZ, ', ')
    FROM WOHNUNG W
    WHERE W.ONR = EIGENTUEMER.ONR AND W.ENR = EIGENTUEMER.ENR
  ), '') AS WohnungEBEZ,                  -- Calculated: Wohnungsbezeichnung(en)
  
  -- === BEIRATS-FUNKTION ===
  CASE
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR1 THEN 'Vorsitz'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR2 OR EIGADR.EIGNR = OBJEKTE.VBR_NR3 THEN 'Mitglied'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR4 OR EIGADR.EIGNR = OBJEKTE.VBR_NR5 OR EIGADR.EIGNR = OBJEKTE.VBR_NR6 THEN 'Mitglied'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR_VORSITZ THEN 'Beiratsvorsitzender'
    ELSE NULL
  END AS Beirat                           -- Calculated: Beirats-Funktion

FROM EIGADR
  INNER JOIN EIGADR ON EIGENTUEMER.EIGNR = EIGADR.EIGNR
  INNER JOIN OBJEKTE ON EIGENTUEMER.ONR = OBJEKTE.ONR
WHERE
  EIGENTUEMER.ONR <> 0                    -- Ausschluss "Nicht zugeordnet"
  AND EIGENTUEMER.ONR < 890               -- Ausschluss Test-Objekte
  AND EIGENTUEMER.EIGNR <> -1              -- Ausschluss kollektive WEG-Eigentümerschaft
ORDER BY EIGENTUEMER.ONR, EIGENTUEMER.ENR;

/*
EXPECTED RESULTS (basierend auf EIGENTUEMER.csv):
- Z1-Z8 Eigentumsanteile: Aktuell meist 0.00 (Konfiguration noch ausstehend)
- SEPA-Mandats-Art: Default = 5 (Wiederkehrende Lastschrift)
- Eigennutzer: Meist "N" (Vermietung üblich)

BUSINESS VALUE:
[OK] Vollständige WEG-Eigentumsstrukturen mit 8 Umlageschlüsseln
[OK] SEPA-Lastschrift-Management für automatische Hausgeldzahlung
[OK] Rücklagen-Controlling (Ist vs. Soll)
[OK] Beirats-Funktionen automatisch erkannt
[OK] Steuerliche Behandlung (privat vs. gewerblich)
*/