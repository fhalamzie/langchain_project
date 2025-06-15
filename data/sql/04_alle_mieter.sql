-- ============================================================================
-- QUERY 2B: ALLE MIETER Layer 4 - Historische und aktuelle Mietverhältnisse
-- ============================================================================
/*
GESCHÄFTSZWECK: Vollständige Mieterhistorie für Analysen und Nachverfolgung
UNTERSCHIED ZU 2A: Zeigt auch beendete Mietverhältnisse mit Auszugsdatum
VERWENDUNG: 
  - Mieterfluktuation analysieren
  - Historische Belegung nachvollziehen
  - Kündigungsfristen überwachen
LAYER 4 ENHANCEMENT: DATEADD auf Firebird 5.0 Syntax angepasst
*/

SELECT
  -- === MIETER-IDENTIFIKATION ===
  B.KNR,                                  -- Kontonummer (INTEGER): Eindeutige Mieter-Kontonummer
  B.ONR,                                  -- Objektnummer (SMALLINT): Gebäude-Referenz
  B.ENR,                                  -- Einheitsnummer (SMALLINT): Wohnungs-Referenz
  
  -- === PRIMÄRE KONTAKTDATEN ===
  B.BNAME AS NACHNAME,                    -- Nachname (VARCHAR): Hauptmieter Familienname
  B.BVNAME AS VORNAME,                    -- Vorname (VARCHAR): Hauptmieter Vorname
  B.BSTR AS STRASSE,                      -- Straße (VARCHAR): Letzte bekannte Anschrift
  B.BPLZORT AS PLZ_ORT,                   -- PLZ/Ort (VARCHAR): Kombiniert "45147 Essen"
  
  -- === ERWEITERTE KONTAKTDATEN ===
  B.BNAME2 AS NACHNAME2,                  -- Nachname 2 (VARCHAR): Zweiter Mieter/Partner
  B.BVNAME2 AS VORNAME2,                  -- Vorname 2 (VARCHAR): Zweiter Mieter/Partner
  B.BTEL AS TELEFON,                      -- Telefon (VARCHAR): Kontaktnummer
  B.BEMAIL AS EMAIL,                      -- E-Mail (VARCHAR): E-Mail-Adresse
  
  -- === MIETVERTRAGSDATEN MIT HISTORIE ===
  B.VBEGINN AS VERTRAGSBEGINN,            -- Vertragsbeginn (DATE): Einzugsdatum
  B.VENDE AS VERTRAGSENDE,                -- Vertragsende (DATE): Auszugsdatum oder NULL
  B.Z1 AS NETTOKALTMIETE,                 -- Nettokaltmiete (NUMERIC): Letzte Grundmiete
  B.Z3 AS NEBENKOSTEN,                    -- Nebenkosten (NUMERIC): Letzte NK-Vorauszahlung
  B.MIETE1 AS WARMMIETE,                  -- Warmmiete (NUMERIC): Letzte Gesamtmiete
  
  -- === STATUS-KATEGORISIERUNG (LAYER 4: FIREBIRD 5.0 SYNTAX) ===
  CASE 
    WHEN B.VENDE IS NULL THEN 'AKTIV'
    WHEN B.VENDE > CURRENT_DATE THEN 'KUENDIGUNG'
    WHEN B.VENDE >= CURRENT_DATE - 90 THEN 'KUERZLICH BEENDET'
    WHEN B.VENDE >= CURRENT_DATE - 365 THEN 'BEENDET'
    ELSE 'HISTORISCH'
  END AS MIETSTATUS,                      -- Mietstatus: Detaillierte Statuskategorien
  
  -- === WOHNUNGSDETAILS ===
  W.EBEZ AS WOHNUNGSBEZEICHNUNG,          -- Wohnungsbezeichnung (VARCHAR): Lage in Gebäude
  W.ART AS WOHNUNGSTYP,                   -- Wohnungstyp (VARCHAR): "Wohnung", "Garage", etc.
  
  -- === OBJEKT-KONTEXT ===
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel (VARCHAR): Gebäude-Kürzel
  O.OSTRASSE AS OBJEKT_STRASSE            -- Objektstraße (VARCHAR): Gebäudeadresse

FROM BEWOHNER B
  INNER JOIN WOHNUNG W ON (B.ONR = W.ONR AND B.ENR = W.ENR)
  INNER JOIN OBJEKTE O ON (B.ONR = O.ONR)
WHERE 
  B.ONR < 890  -- Ausschluss von Testobjekten
ORDER BY 
  B.ONR, 
  B.ENR, 
  B.VENDE DESC NULLS FIRST,  -- Aktuelle Mieter zuerst
  B.BNAME;

/*
LAYER 4 ENHANCEMENTS SUMMARY:
=== SYNTAX-ANPASSUNGEN ===
+ DATEADD(MONTH, -3, CURRENT_DATE) ersetzt durch CURRENT_DATE - 90
+ DATEADD(YEAR, -1, CURRENT_DATE) ersetzt durch CURRENT_DATE - 365
+ Firebird 5.0 native Datums-Arithmetik verwendet

=== TECHNISCHE VERBESSERUNGEN ===
- Keine DATEADD-Funktion mehr nötig
- Einfache Integer-Subtraktion für Tage
- Kompatibel mit Firebird 5.0 Standard

ERWARTETES ERGEBNIS:
- Alle Mietverträge (aktiv + historisch)
- VENDE-Spalte zeigt Auszugsdaten
- Status-Kategorisierung für Analysen:
  - AKTIV: Laufende Verträge
  - KUENDIGUNG: Zukünftiges Vertragsende
  - KUERZLICH BEENDET: Letzte 3 Monate
  - BEENDET: Letztes Jahr
  - HISTORISCH: Älter als 1 Jahr

GESCHÄFTSNUTZEN:
[OK] Vollständige Mieterhistorie pro Wohnung
[OK] Fluktuationsanalyse möglich
[OK] Kündigungsfristen im Blick
[OK] Leerstandszeiten identifizierbar
[OK] Wiedervermietungspotenzial erkennbar
*/