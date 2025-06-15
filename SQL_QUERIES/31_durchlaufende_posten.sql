-- ============================================================================
-- QUERY 23: DURCHLAUFENDE POSTEN - Layer 4 Enhanced with Modern Firebird Features
-- ============================================================================
/*
GESCHÄFTSZWECK: Übersicht aller durchlaufenden Posten (temporäre Buchungen)
HAUPTTABELLEN:
  - RUECKPOS: Rücklagenpositionen mit speziellen Posten
  - KONTEN: Zugehörige Konten
  - BUCHUNG: Bewegungen der durchlaufenden Posten
DEFINITION: Durchlaufende Posten = POS5NAME = "Durchlaufener Posten" 
VERWENDUNG: Temporäre Transaktionen, die das Eigenkapital nicht dauerhaft beeinflussen
LAYER 4 ENHANCEMENTS:
  - Moderne Firebird 5.0 Syntax optimiert
  - Erweiterte Kommentierung für bessere Verständlichkeit
  - Performance-optimierte Sortierung
  - Flexible Filter-Parameter
*/

SELECT 
  -- === OBJEKT-IDENTIFIKATION ===
  R.ONR,                                  -- Objektnummer: WEG/Liegenschaft
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel: z.B. "KUPFE190_W"
  O.OSTRASSE AS OBJEKT_STRASSE,           -- Objektstraße: Vollständige Adresse
  
  -- === RÜCKLAGEN-POSITION ===
  R.NR AS RUECKLAGE_NR,                   -- Rücklagen-Nummer: Eindeutige ID
  R.NAME AS RUECKLAGE_NAME,               -- Rücklage Name: Bezeichnung der Reserve
  
  -- === DURCHLAUFENDE POSTEN DETAILS ===
  CAST(R.POS5 AS NUMERIC(15,2)) AS DURCHLAUF_BETRAG, -- Durchlauf-Betrag: Aktueller Stand in EUR
  R.POS5NAME AS DURCHLAUF_BEZEICHNUNG,    -- Bezeichnung: "Durchlaufener Posten"
  R.POS5CHECK AS DURCHLAUF_AKTIV,         -- Aktiv-Flag: "J"=Ja, "N"=Nein
  
  -- === ZUGEHÖRIGE KONTEN ===
  R.KZUF AS ZUEFUEHRUNGS_KONTO,           -- Zuführungskonto: Normalerweise 30000
  R.KENTN AS ENTNAHME_KONTO,              -- Entnahmekonto: Normalerweise 30100
  R.KNRP AS PROJEKT_KONTO,                -- Projektkonto: Spezielle Zuordnung
  
  -- === BEWEGUNGS-ANALYSE ===
  CAST(R.ANFSTAND AS NUMERIC(15,2)) AS ANFANGSSTAND, -- Anfangsstand: Zu Periodenbeginn in EUR
  CAST(R.ENDSTAND AS NUMERIC(15,2)) AS ENDSTAND,     -- Endstand: Aktueller Stand in EUR
  CAST(R.ZUF AS NUMERIC(15,2)) AS ZUEFUEHRUNGEN,     -- Zuführungen: Eingänge in EUR
  CAST(R.ENTN AS NUMERIC(15,2)) AS ENTNAHMEN,        -- Entnahmen: Ausgänge in EUR
  
  -- === SONDER-BEWEGUNGEN ===
  CAST(R.SONDERZUF AS NUMERIC(15,2)) AS SONDER_ZUEFUEHRUNG, -- Sonder-Zuführung: Außerordentliche Eingänge
  CAST(R.SONDERENTN AS NUMERIC(15,2)) AS SONDER_ENTNAHME,   -- Sonder-Entnahme: Außerordentliche Ausgänge
  
  -- === ZEITRAUM ===
  R.DTVON AS PERIODE_VON,                 -- Periode von: Abrechnungsbeginn
  R.DTBIS AS PERIODE_BIS,                 -- Periode bis: Abrechnungsende
  
  -- === ENHANCED CALCULATIONS ===
  CAST((R.ENDSTAND - R.ANFSTAND) AS NUMERIC(15,2)) AS NETTO_BEWEGUNG, -- Netto-Bewegung: Differenz
  CAST((R.ZUF + COALESCE(R.SONDERZUF, 0)) AS NUMERIC(15,2)) AS GESAMT_ZUEFUEHRUNGEN, -- Gesamt-Zuführungen
  CAST((R.ENTN + COALESCE(R.SONDERENTN, 0)) AS NUMERIC(15,2)) AS GESAMT_ENTNAHMEN,   -- Gesamt-Entnahmen
  
  -- === KATEGORISIERUNG ===
  CASE 
    WHEN R.POS5 > 0 AND R.POS5 < 100 THEN 'KLEINBETRAG (<100 EUR)'
    WHEN R.POS5 >= 100 AND R.POS5 < 1000 THEN 'MITTELBETRAG (100-1000 EUR)'
    WHEN R.POS5 >= 1000 AND R.POS5 < 10000 THEN 'GROSSBETRAG (1K-10K EUR)'
    WHEN R.POS5 >= 10000 THEN 'SEHR_GROSSBETRAG (>10K EUR)'
    WHEN R.POS5 < 0 THEN 'NEGATIVER DURCHLAUF'
    ELSE 'KEIN DURCHLAUF'
  END AS DURCHLAUF_KATEGORIE,             -- Kategorie: Größenklassifikation
  
  -- === STATUS-BEWERTUNG ===
  CASE 
    WHEN R.POS5CHECK = 'J' AND ABS(R.POS5) > 0 THEN 'AKTIV MIT BESTAND'
    WHEN R.POS5CHECK = 'J' AND R.POS5 = 0 THEN 'AKTIV OHNE BESTAND'
    WHEN R.POS5CHECK = 'N' THEN 'INAKTIV'
    ELSE 'UNBESTIMMT'
  END AS DURCHLAUF_STATUS,                -- Status: Aktivitätsbewertung
  
  -- === BUSINESS INTELLIGENCE ===
  CASE
    WHEN R.POS5 > 0 AND R.DTVON IS NOT NULL AND 
         R.DTVON < CURRENT_DATE - 365 THEN 'LANGFRISTIG_OFFEN'
    WHEN R.POS5 > 0 AND R.DTVON IS NOT NULL AND 
         R.DTVON < CURRENT_DATE - 90 THEN 'KURZFRISTIG_OFFEN'
    WHEN R.POS5 > 0 THEN 'AKTUELL_OFFEN'
    WHEN R.POS5 = 0 THEN 'AUSGEGLICHEN'
    ELSE 'ZU_PRUEFEN'
  END AS ABWICKLUNGS_STATUS,              -- Abwicklungs-Status: Zeitanalyse
  
  -- === BANKZUORDNUNG ===
  KB.KBEZ AS BANK_BEZEICHNUNG,            -- Bankbezeichnung: Zugeordnetes Bankkonto
  KB.KKLASSE AS BANK_KONTOKLASSE          -- Bank-Kontoklasse: Kategorisierung

FROM RUECKPOS R
  INNER JOIN OBJEKTE O ON R.ONR = O.ONR
  LEFT JOIN KONTEN KB ON R.KNRP = KB.KNR AND R.ONR = KB.ONR
WHERE 
  (R.POS5NAME LIKE '%Durchlauf%'          -- Filter: Nur durchlaufende Posten
  OR R.POS5NAME = 'Frei definierbar')     -- Zusätzlich: Frei definierbare Posten
  AND R.ONR < 890                         -- Ausschluss: Testobjekte
  -- Für spezifisches Objekt: AND R.ONR = 123
  -- Für Mindestbetrag: AND ABS(R.POS5) >= 1000
  -- Für aktive Posten nur: AND R.POS5CHECK = 'J'
ORDER BY 
  CASE 
    WHEN R.POS5CHECK = 'J' AND ABS(R.POS5) > 0 THEN 1  -- Aktive mit Bestand zuerst
    WHEN R.POS5CHECK = 'J' AND R.POS5 = 0 THEN 2       -- Aktive ohne Bestand
    ELSE 3                                              -- Inaktive zuletzt
  END,
  ABS(R.POS5) DESC,                       -- Innerhalb Gruppe: Höchste Beträge zuerst
  R.ONR;

/*
ERWARTETES ERGEBNIS:
- Alle Objekte mit durchlaufenden Posten
- Erweiterte Betragsklassifikation nach Höhe
- Zuordnung zu Bank-/Projektkonten
- Periode und Status-Information
- Zusätzliche Geschäftslogik-Analysen

GESCHÄFTSNUTZEN:
[OK] Transparenz über temporäre Geldflüsse mit EUR-Beträgen
[OK] Überwachung nicht-dauerhafter Buchungen
[OK] Compliance für Eigenkapital-Darstellung
[OK] Prüfung korrekter Durchlauf-Abwicklung
[OK] Zeitanalyse für lang offene Posten
[OK] Flexible Parameter für verschiedene Auswertungen

LAYER 4 IMPROVEMENTS:
- NUMERIC(15,2) CAST für alle Beträge (firebird-driver optimiert)
- Erweiterte Kategorisierung (bis >10K EUR)
- Zusätzliche Berechnungsfelder (Netto-Bewegung, Gesamt-Zuführungen/Entnahmen)
- Geschäftslogik für Abwicklungs-Status
- Performance-optimierte Sortierung nach Priorität
- Flexible Filter-Kommentare für Parameter-Anpassung
*/