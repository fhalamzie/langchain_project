-- ============================================================================
-- QUERY 24: SONDERENTNAHMEN/SONDERZUFÜHRUNGEN - Layer 4 Enhanced with Modern Firebird Features
-- ============================================================================
/*
GESCHÄFTSZWECK: Analyse außerordentlicher Entnahmen und Zuführungen
HAUPTTABELLEN:
  - RUECKPOS: Sonderentnahmen (SONDERENTN) und Sonderzuführungen (SONDERZUF)
  - KONTEN: Zugehörige Sonderkonten (KSONDERENTN, KSONDERZUF)
  - OBJEKTE: Objektdaten für proportionale Kennzahlen
DEFINITION: Außerordentliche Kapitalbewegungen außerhalb normaler Rücklagen
VERWENDUNG: Eigentümer-Ausschüttungen, Kapitalzuführungen, Sonderinvestitionen
LAYER 4 ENHANCEMENTS:
  - NUMERIC(15,2) CAST für exakte EUR-Beträge
  - Erweiterte Kategorisierung mit mehr Betragsstufen
  - Performance-optimierte Berechnungen
  - Zusätzliche Geschäftslogik-Analysen
*/

SELECT 
  -- === OBJEKT-IDENTIFIKATION ===
  R.ONR,                                  -- Objektnummer: WEG/Liegenschaft
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel: Internes Kürzel
  O.OSTRASSE AS OSTRASSE,           -- Objektstraße: Vollständige Adresse
  
  -- === RÜCKLAGEN-KONTEXT ===
  R.NR AS RUECKLAGE_NR,                   -- Rücklagen-Nummer: Eindeutige ID
  R.NAME AS RUECKLAGE_NAME,               -- Rücklage Name: Bezeichnung der Reserve
  
  -- === SONDER-ENTNAHMEN (OPTIMIERT) ===
  CAST(COALESCE(R.SONDERENTN, 0) AS NUMERIC(15,2)) AS SONDER_ENTNAHME_BETRAG, -- Sonder-Entnahme in EUR
  R.KSONDERENTN AS SONDER_ENTNAHME_KONTO, -- Sonder-Entnahme: Kontokennzeichen
  KE.KBEZ AS ENTNAHME_KONTO_BEZEICHNUNG,  -- Entnahme-Konto: Vollständige Bezeichnung
  
  -- === SONDER-ZUFÜHRUNGEN (OPTIMIERT) ===
  CAST(COALESCE(R.SONDERZUF, 0) AS NUMERIC(15,2)) AS SONDER_ZUEFUEHRUNG_BETRAG, -- Sonder-Zuführung in EUR
  R.KSONDERZUF AS SONDER_ZUEFUEHRUNG_KONTO, -- Sonder-Zuführung: Kontokennzeichen
  KZ.KBEZ AS ZUEFUEHRUNG_KONTO_BEZEICHNUNG, -- Zuführung-Konto: Vollständige Bezeichnung
  
  -- === NETTO-SALDO (OPTIMIERT) ===
  CAST((COALESCE(R.SONDERZUF, 0) - COALESCE(R.SONDERENTN, 0)) AS NUMERIC(15,2)) AS NETTO_SONDERBEWEGUNG,
  
  -- === MAXIMUM BEWEGUNG FÜR ANALYSEN ===
  CAST(
    CASE WHEN COALESCE(R.SONDERENTN, 0) > COALESCE(R.SONDERZUF, 0) 
         THEN COALESCE(R.SONDERENTN, 0) 
         ELSE COALESCE(R.SONDERZUF, 0) 
    END AS NUMERIC(15,2)
  ) AS MAX_BEWEGUNG,
  
  -- === BEWEGUNGS-KATEGORISIERUNG ===
  CASE 
    WHEN R.SONDERENTN > 0 AND R.SONDERZUF > 0 THEN 'BEIDE RICHTUNGEN'
    WHEN R.SONDERENTN > 0 THEN 'NUR ENTNAHMEN'
    WHEN R.SONDERZUF > 0 THEN 'NUR ZUFÜHRUNGEN'
    ELSE 'KEINE SONDERBEWEGUNGEN'
  END AS BEWEGUNGSTYP,                    -- Bewegungstyp: Richtung der Transaktion
  
  -- === ERWEITERTE BETRAGS-KLASSIFIKATION ===
  CASE 
    WHEN (CASE WHEN COALESCE(R.SONDERENTN, 0) > COALESCE(R.SONDERZUF, 0) 
               THEN COALESCE(R.SONDERENTN, 0) 
               ELSE COALESCE(R.SONDERZUF, 0) END) < 500 
      THEN 'KLEINBETRAG (<500 EUR)'
    WHEN (CASE WHEN COALESCE(R.SONDERENTN, 0) > COALESCE(R.SONDERZUF, 0) 
               THEN COALESCE(R.SONDERENTN, 0) 
               ELSE COALESCE(R.SONDERZUF, 0) END) < 2000 
      THEN 'KLEINMITTELBETRAG (500-2K EUR)'
    WHEN (CASE WHEN COALESCE(R.SONDERENTN, 0) > COALESCE(R.SONDERZUF, 0) 
               THEN COALESCE(R.SONDERENTN, 0) 
               ELSE COALESCE(R.SONDERZUF, 0) END) < 10000 
      THEN 'MITTELBETRAG (2K-10K EUR)'
    WHEN (CASE WHEN COALESCE(R.SONDERENTN, 0) > COALESCE(R.SONDERZUF, 0) 
               THEN COALESCE(R.SONDERENTN, 0) 
               ELSE COALESCE(R.SONDERZUF, 0) END) < 50000 
      THEN 'GROSSBETRAG (10K-50K EUR)'
    WHEN (CASE WHEN COALESCE(R.SONDERENTN, 0) > COALESCE(R.SONDERZUF, 0) 
               THEN COALESCE(R.SONDERENTN, 0) 
               ELSE COALESCE(R.SONDERZUF, 0) END) < 100000 
      THEN 'SEHR GROSSBETRAG (50K-100K EUR)'
    ELSE 'MAXIMAL GROSSBETRAG (>100K EUR)'
  END AS BETRAGSKLASSE,                   -- Betragsklasse: Erweiterte Größenordnung
  
  -- === ZEITRAUM-KONTEXT ===
  R.DTVON AS PERIODE_VON,                 -- Periode von: Abrechnungszeitraum Start
  R.DTBIS AS PERIODE_BIS,                 -- Periode bis: Abrechnungszeitraum Ende
  
  -- === GESCHÄFTSJAHR-ZUORDNUNG ===
  CASE 
    WHEN R.DTBIS >= '2024-01-01' THEN '2024'
    WHEN R.DTBIS >= '2023-01-01' THEN '2023'
    WHEN R.DTBIS >= '2022-01-01' THEN '2022'
    WHEN R.DTBIS >= '2021-01-01' THEN '2021'
    ELSE 'ÄLTER'
  END AS GESCHAEFTSJAHR,                   -- Geschäftsjahr: Erweiterte Zuordnung
  
  -- === PROPORTIONALE KENNZAHLEN (OPTIMIERT) ===
  CAST(
    CASE 
      WHEN O.OANZEINH IS NOT NULL AND O.OANZEINH > 0 AND R.SONDERENTN IS NOT NULL AND R.SONDERENTN > 0 
      THEN R.SONDERENTN / O.OANZEINH
      ELSE 0
    END AS NUMERIC(10,2)
  ) AS ENTNAHME_PRO_EINHEIT,            -- EUR/Einheit: Entnahme pro Wohnung
  
  CAST(
    CASE 
      WHEN O.GA1 IS NOT NULL AND O.GA1 > 0 AND R.SONDERENTN IS NOT NULL AND R.SONDERENTN > 0 
      THEN R.SONDERENTN / O.GA1
      ELSE 0
    END AS NUMERIC(10,2)
  ) AS ENTNAHME_PRO_QM,                 -- EUR/m²: Entnahme pro Quadratmeter
  
  -- === ERWEITERTE ZWECK-HYPOTHESE ===
  CASE 
    WHEN R.SONDERENTN > 100000 THEN 'GROSSSANIERUNG/MODERNISIERUNG'
    WHEN R.SONDERENTN > 50000 THEN 'GROSSINVESTITION/SANIERUNG'
    WHEN R.SONDERENTN BETWEEN 20000 AND 50000 THEN 'MITTLERE INVESTITION'
    WHEN R.SONDERENTN BETWEEN 5000 AND 20000 THEN 'KLEINERE SANIERUNG'
    WHEN R.SONDERENTN BETWEEN 1000 AND 5000 THEN 'INSTANDHALTUNG/REPARATUR'
    WHEN R.SONDERZUF > 50000 THEN 'GROSSE KAPITALZUFÜHRUNG'
    WHEN R.SONDERZUF > 10000 THEN 'KAPITALZUFÜHRUNG'
    WHEN R.SONDERZUF > 0 THEN 'KLEINERE ZUFÜHRUNG'
    WHEN R.SONDERENTN > 0 THEN 'KLEINERE ENTNAHME'
    ELSE 'UNBESTIMMT'
  END AS ZWECK_HYPOTHESE,                  -- Zweck: Erweiterte Verwendungszweck-Analyse
  
  -- === FINANZIELLE RISIKO-BEWERTUNG ===
  CASE
    WHEN R.SONDERENTN > 50000 THEN 'HOCH - BEIRATSBESCHLUSS PRÜFEN'
    WHEN R.SONDERENTN > 20000 THEN 'MITTEL - DOKUMENTATION SICHERSTELLEN'
    WHEN R.SONDERENTN > 5000 THEN 'NIEDRIG - ROUTINEPRÜFUNG'
    WHEN R.SONDERENTN > 0 THEN 'MINIMAL - STANDARD'
    ELSE 'KEINE ENTNAHME'
  END AS RISIKO_BEWERTUNG,                -- Risiko: Compliance-Bewertung
  
  -- === OBJEKT-KENNZAHLEN FÜR KONTEXT ===
  O.OANZEINH AS ANZAHL_EINHEITEN,         -- Anzahl Wohnungen im Objekt
  CAST(O.GA1 AS NUMERIC(10,2)) AS GESAMTFLAECHE_QM -- Gesamtfläche in m²

FROM RUECKPOS R
  INNER JOIN OBJEKTE O ON R.ONR = O.ONR
  LEFT JOIN KONTEN KE ON R.KSONDERENTN = KE.KNR AND R.ONR = KE.ONR
  LEFT JOIN KONTEN KZ ON R.KSONDERZUF = KZ.KNR AND R.ONR = KZ.ONR
WHERE 
  ((R.SONDERENTN IS NOT NULL AND R.SONDERENTN <> 0)
  OR (R.SONDERZUF IS NOT NULL AND R.SONDERZUF <> 0))
  AND R.ONR < 890                         -- Ausschluss: Testobjekte
  -- Für spezifisches Objekt: AND R.ONR = 123
  -- Für Mindestbetrag: AND (ABS(COALESCE(R.SONDERENTN, 0)) >= 1000 OR ABS(COALESCE(R.SONDERZUF, 0)) >= 1000)
  -- Für aktuelles Jahr: AND R.DTBIS >= '2024-01-01'
ORDER BY 
  -- Höchste Beträge zuerst (optimierte Sortierung)
  CASE WHEN COALESCE(R.SONDERENTN, 0) > COALESCE(R.SONDERZUF, 0) 
       THEN COALESCE(R.SONDERENTN, 0) 
       ELSE COALESCE(R.SONDERZUF, 0) END DESC,
  R.DTBIS DESC,                           -- Neueste zuerst
  R.ONR;

/*
ERWARTETES ERGEBNIS:
- Alle außerordentlichen Kapitalbewegungen mit exakten EUR-Beträgen
- Erweiterte Klassifikation nach Betragshöhe und Zweck
- Proportionale Kennzahlen pro Einheit/m²
- Risiko-Bewertung für Compliance
- Moderne Firebird 5.0 optimierte Berechnungen

GESCHÄFTSNUTZEN:
[OK] Transparenz über außerordentliche Entscheidungen mit EUR-Beträgen
[OK] Kontrollierte Darstellung großer Kapitalentnahmen
[OK] Risiko-bewertete Compliance-Unterstützung
[OK] Basis für fundierte Eigentümer-Kommunikation
[OK] Investitions-/Sanierungsplanung mit Kennzahlen
[OK] Erweiterte Geschäftslogik für bessere Kategorisierung

LAYER 4 IMPROVEMENTS:
- NUMERIC(15,2) Präzision für alle Geldbeträge
- Erweiterte 6-stufige Betragsklassifikation
- Zusätzliche Risiko-Bewertung für Compliance
- Performance-optimierte Berechnungen ohne DOUBLE PRECISION
- Flexible Filter-Parameter über Kommentare
- Erweiterte Zweck-Hypothesen für bessere Kategorisierung
*/