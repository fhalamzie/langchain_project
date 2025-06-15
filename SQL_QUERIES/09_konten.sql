-- ============================================================================
-- QUERY 5: KONTEN (Enhanced Layer 4) - Financial Enhanced Version
-- ============================================================================
/*
BUSINESS PURPOSE: Umfassender Kontenplan mit erweiterten Finanzfeldern
MAIN TABLE: KONTEN (Chart of Accounts) - Enhanced mit 7 kritischen Business-Feldern
KEY RELATIONSHIPS:
  - KONTEN.ONR -> OBJEKTE.ONR (n:1 - Mehrere Konten pro Objekt)
  - KONTEN.ENR -> WOHNUNG.ENR (n:1 - Konten können einheitenspezifisch sein)
  - KONTEN.KKLASSE -> Kontenklassifikation (1=Sachkonten, 60=Mieterkonten, 62=Eigentümerkonten)
LEGAL CONTEXT: Buchhaltung nach HGB, WEG-Abrechnung, Mahnwesen, NK-Abrechnung
*/

SELECT 
  -- === IDENTIFIKATION ===
  KONTEN.ONR,                             -- FK: Objekt-Nummer (SMALLINT)
  KONTEN.KNR,                             -- PK: Konto-Nummer (INTEGER)
  KONTEN.ENR,                             -- FK: Einheiten-Nummer (SMALLINT) - NULL bei Sachkonten
  KONTEN.ONR * KONTEN.KNR AS ONRKNR,      -- Calculated: Eindeutige Referenz für Berichte
  
  -- === KONTEN-KLASSIFIKATION ===
  KONTEN.KKLASSE,                         -- Kontenklasse (SMALLINT): 1=Sachkonten, 60=Mieter, 62=Eigentümer
  CASE 
    WHEN KONTEN.KKLASSE = 1 THEN 'Sachkonto (Ausgaben/Einnahmen)'
    WHEN KONTEN.KKLASSE = 60 THEN 'Mieterkonto (Persoenliche Konten)'
    WHEN KONTEN.KKLASSE = 62 THEN 'Eigentuemerkonto (WEG-Konten)'
    ELSE 'Sonstige Kontenklasse'
  END AS KKLASSE_BEZEICHNUNG,             -- Calculated: User-friendly Klassifikation
  
  -- === KONTOBESCHREIBUNG ===
  KONTEN.KBEZ,                            -- Kontobezeichnung (VARCHAR): "Mustermann, Max EG", "Heizkosten"
  KONTEN.KNRSTR,                          -- Konto-String (VARCHAR): "B.001.00", "E.002.00" - Lesbare Darstellung
  
  -- === FINANZSTATUS (Layer 3 Basis) ===
  KONTEN.KBRUTTO,                         -- Kontosaldo Brutto (NUMERIC 15,2): Aktueller Gesamtsaldo
  KONTEN.OPBETRAG,                        -- Offener Posten Betrag (NUMERIC 15,2): Unbeglichene Forderungen
  KONTEN.KUST,                            -- USt-Betrag (NUMERIC 15,2): Umsatzsteuer-Anteil
  
  -- === LAYER 4 ENHANCED: ERWEITERTE FINANZFELDER ===
  KONTEN.KVERTEILUNG,                     -- Kostenverteilung (CHAR): "J"/"N" - Kritisch für NK-Abrechnung
  KONTEN.USTVOR,                          -- Vorsteuer-Satz (NUMERIC 5,2): Input VAT (zusätzlich zu STSATZ)
  KONTEN.KWBRUTTO,                        -- Alternativer Brutto-Saldo (NUMERIC 15,2): Spezielle Berechnungen
  KONTEN.KWBRUTTOALT,                     -- Alt-Brutto-Saldo (NUMERIC 15,2): Historische Werte
  KONTEN.KBRUTTOWJ,                       -- Jahresend-Saldo (NUMERIC 15,2): Für Bilanzierung und Vorjahresvergleich
  KONTEN.INAKTIV,                         -- Aktiv/Inaktiv Status (CHAR): "J"=inaktiv, "N"=aktiv
  KONTEN.BUTEXT4,                         -- Buchungstext 4 (VARCHAR): Zusätzliche Beschreibung
  KONTEN.BUTEXT5,                         -- Buchungstext 5 (VARCHAR): Vollständige Beschreibungsfelder
  
  -- === LAYER 4 ENHANCED: FESTBETRÄGE UND PROZENTSÄTZE ===
  KONTEN.FESTB,                           -- Festbetrag (NUMERIC 15,2): Feste Umlagen pro Periode
  KONTEN.FESTBPROZ,                       -- Festprozent (NUMERIC 5,2): Prozentualer Anteil für Verteilung
  
  -- === MAHNWESEN (Forderungsmanagement) ===
  KONTEN.KMAHNSTUFE,                      -- Mahnstufe (SMALLINT): 0=keine, 1=erste, 2=zweite, 3=letzte Mahnung
  KONTEN.MAHNDATUM,                       -- Mahndatum (DATE): Datum der letzten Mahnung
  KONTEN.MAHNGEDRUCKT,                    -- Mahnung gedruckt (CHAR): "J"=versendet, "N"=offen
  CASE 
    WHEN KONTEN.KMAHNSTUFE = 0 THEN 'Keine Mahnung'
    WHEN KONTEN.KMAHNSTUFE = 1 THEN 'Erste Mahnung'
    WHEN KONTEN.KMAHNSTUFE = 2 THEN 'Zweite Mahnung'
    WHEN KONTEN.KMAHNSTUFE = 3 THEN 'Letzte Mahnung vor Inkasso'
    ELSE 'Unbekannte Mahnstufe'
  END AS MAHNSTATUS,                      -- Calculated: Mahnstatus-Beschreibung
  
  -- === STEUERLICHE BEHANDLUNG ===
  KONTEN.STSATZ,                          -- Steuersatz (NUMERIC 5,2): USt-Satz in Prozent (19.00, 7.00)
  KONTEN.DATEVKNR,                        -- DATEV-Kontonummer (VARCHAR): Externe Buchführungs-Software
  
  -- === OBJEKTZUORDNUNG ===
  OBJEKTE.OSTRASSE,                       -- Objekt-Straße (VARCHAR): Gebäude-Adresse
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- Liegenschafts-Kürzel (VARCHAR): Interne Objekt-Referenz
  
  -- === ERWEITERTE KONTOINFORMATIONEN ===
  KONTEN.BUTEXT1,                         -- Buchungstext 1 (VARCHAR): Zusätzliche Kontobeschreibung
  KONTEN.BUTEXT2,                         -- Buchungstext 2 (VARCHAR): Erweiterte Beschreibung
  KONTEN.BUTEXT3,                         -- Buchungstext 3 (VARCHAR): Weitere Details
  
  -- === ABRECHNUNGSSTEUERUNG ===
  KONTEN.KABRECHNEN,                      -- Abrechnen (SMALLINT): Wird in Abrechnung berücksichtigt
  KONTEN.IHRABRVON,                       -- Abrechnungsperiode Von (DATE): Start-Datum für Abrechnung
  KONTEN.IHRABRBIS                        -- Abrechnungsperiode Bis (DATE): End-Datum für Abrechnung

FROM KONTEN
  INNER JOIN OBJEKTE ON (KONTEN.ONR = OBJEKTE.ONR)
WHERE
  KONTEN.KNR NOT LIKE 0                   -- Ausschluss ungültiger Konten
  AND KONTEN.ONR NOT LIKE 0               -- Ausschluss "Nicht zugeordnet"
  AND KONTEN.ONR < 890                    -- Ausschluss Test-Objekte
ORDER BY KONTEN.KKLASSE, KONTEN.ONR, KONTEN.KNR;

/*
LAYER 4 ENHANCEMENTS SUMMARY:
=== NEUE FINANZFELDER ===
+ KVERTEILUNG: Kostenverteilungs-Flag für NK-Abrechnung
+ USTVOR: Vorsteuer-Behandlung (Input VAT)
+ KWBRUTTO/KWBRUTTOALT: Alternative Saldierungsmodelle
+ KBRUTTOWJ: Jahresendstände für Bilanzvergleiche
+ INAKTIV: Account-Status für Filterung
+ BUTEXT4/BUTEXT5: Vollständige Beschreibungsfelder
+ FESTB/FESTBPROZ: Festbeträge und Prozentsätze für Umlagen

EXPECTED RESULTS (basierend auf KONTEN.csv):
- KKLASSE=60: Mieterkonten mit detaillierter Kostenverteilung
- KKLASSE=62: Eigentümerkonten mit WEG-spezifischen Festbeträgen
- KKLASSE=1: Sachkonten mit Vor-/Umsatzsteuer-Differenzierung
- INAKTIV="N": Nur aktive Konten in Standardauswertungen
- KVERTEILUNG="J": Konten die in NK-Verteilung eingehen

BUSINESS VALUE ENHANCEMENTS:
[NEW] Kostenverteilungs-Steuerung für NK-Abrechnung
[NEW] Vollständige Vor-/Umsatzsteuer-Behandlung
[NEW] Alternative Saldierungsmodelle für komplexe Berechnungen
[NEW] Jahresend-Salden für Bilanzierung und Vorjahresvergleiche
[NEW] Account-Status-Management (aktiv/inaktiv)
[NEW] Vollständige Beschreibungsfelder (5 statt 3)
[NEW] Festbeträge und Prozentsätze für automatische Umlagen
[OK] Vollständiger Kontenplan aller Kontenklassen (Layer 3)
[OK] Mahnwesen-Integration mit Status-Tracking (Layer 3)
[OK] Steuerliche Zuordnung für DATEV-Export (Layer 3)
[OK] Offene-Posten-Verwaltung (Layer 3)
[OK] Abrechnungsperioden-Steuerung (Layer 3)
*/