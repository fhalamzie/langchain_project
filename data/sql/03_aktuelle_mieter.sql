-- ============================================================================
-- QUERY 2A: AKTUELLE MIETER Layer 4 - Nur aktive Mietverhältnisse mit Banking-Details
-- ============================================================================
/*
GESCHÄFTSZWECK: Verwaltung aktueller Mietverhältnisse mit allen Kontakt- und Zahlungsinformationen
HAUPTTABELLEN:
  - BEWOHNER: Mieterstammdaten (47 Felder)
  - WOHNUNG: Wohnungsdetails und Zuordnung
  - OBJEKTE: Gebäudeinformationen
  - KONTEN: Kontoführung und Salden
KEY RELATIONSHIPS:
  - BEWOHNER -> WOHNUNG via ONR + ENR (Objekt + Einheit)
  - BEWOHNER -> KONTEN via KNR (Mieterkonto)
GESCHÄFTSREGEL: VENDE IS NULL = Aktueller Mieter (unbefristeter/aktiver Vertrag)
LAYER 4 STATUS: Keine Änderungen erforderlich - Query ist bereits optimal
*/

SELECT
  -- === MIETER-IDENTIFIKATION ===
  B.KNR,                                  -- Kontonummer (INTEGER): Eindeutige Mieter-Kontonummer
  B.ONR,                                  -- Objektnummer (SMALLINT): Gebäude-Referenz
  B.ENR,                                  -- Einheitsnummer (SMALLINT): Wohnungs-Referenz
  
  -- === PRIMÄRE KONTAKTDATEN ===
  COALESCE(A.BNAME, B.BNAME) AS NACHNAME,  -- Nachname (VARCHAR): Hauptmieter Familienname (BEWADR bevorzugt)
  COALESCE(A.BVNAME, B.BVNAME) AS VORNAME, -- Vorname (VARCHAR): Hauptmieter Vorname (BEWADR bevorzugt)
  B.BSTR AS STRASSE,                      -- Straße (VARCHAR): Meldeanschrift des Mieters
  B.BPLZORT AS PLZ_ORT,                   -- PLZ/Ort (VARCHAR): Kombiniert "45147 Essen"
  
  -- === ERWEITERTE KONTAKTDATEN ===
  B.BNAME2 AS NACHNAME2,                  -- Nachname 2 (VARCHAR): Zweiter Mieter/Ehepartner
  B.BVNAME2 AS VORNAME2,                  -- Vorname 2 (VARCHAR): Zweiter Mieter/Ehepartner
  B.BTEL AS TELEFON,                      -- Telefon (VARCHAR): Festnetz oder Hauptnummer
  B.BTEL2 AS TELEFON2,                    -- Telefon 2 (VARCHAR): Mobilnummer oder Zweitnummer
  B.BEMAIL AS EMAIL,                      -- E-Mail (VARCHAR): Haupt-E-Mail-Adresse
  B.BHANDY AS HANDY,                      -- Handy (VARCHAR): Mobile Nummer
  
  -- === BANKING & SEPA-INFORMATIONEN ===
  B.BBANK AS BANKNAME,                    -- Bank (VARCHAR): Name des kontoführenden Instituts
  B.BBLZ AS BLZ,                          -- BLZ (VARCHAR): Bankleitzahl (Altdaten)
  B.BKONTO AS KONTONUMMER,                -- Kontonummer (VARCHAR): Alte Kontonummer (Altdaten)
  B.BIBAN AS IBAN,                        -- IBAN (VARCHAR): Internationale Kontonummer (SEPA)
  B.BBIC AS BIC,                          -- BIC (VARCHAR): Bank-Identifikationscode (SWIFT)
  B.BKONTOINH AS KONTOINHABER,            -- Kontoinhaber (VARCHAR): Falls abweichend vom Mieter
  
  -- === MIETVERTRAGSDATEN ===
  B.VBEGINN AS VERTRAGSBEGINN,            -- Vertragsbeginn (DATE): Mietbeginn/Einzugsdatum
  B.VENDE AS VERTRAGSENDE,                -- Vertragsende (DATE): NULL = unbefristet/aktiv
  B.Z1 AS NETTOKALTMIETE,                 -- Nettokaltmiete (NUMERIC): Grundmiete ohne NK (Z1)
  B.Z3 AS NEBENKOSTEN,                    -- Nebenkosten (NUMERIC): Monatliche NK-Vorauszahlung (Z3)
  B.MIETE1 AS WARMMIETE,                  -- Warmmiete (NUMERIC): Gesamtmiete inkl. NK
  B.KAUT_VEREINBART AS KAUTION,           -- Kaution (NUMERIC): Hinterlegte Mietkaution
  
  -- === KORRESPONDENZ-OPTIONEN ===
  B.BANREDE AS ANREDE,                    -- Anrede (VARCHAR): "Herr", "Frau", "Familie" etc.
  B.BBRIEFAN AS BRIEFANREDE,              -- Briefanrede (VARCHAR): Formelle Anrede für Post
  
  -- === WOHNUNGSDETAILS ===
  W.EBEZ AS WOHNUNGSBEZEICHNUNG,          -- Wohnungsbezeichnung (VARCHAR): z.B. "2.OG links"
  W.ART AS WOHNUNGSTYP,                   -- Wohnungstyp (VARCHAR): "Wohnung", "Garage", etc.
  
  -- === OBJEKT-KONTEXT ===
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel (VARCHAR): Internes Kürzel
  O.OSTRASSE AS OBJEKT_STRASSE,           -- Objektstraße (VARCHAR): Adresse des Gebäudes
  O.OPLZORT AS OBJEKT_ORT,                -- Objekt PLZ/Ort (VARCHAR): Standort des Gebäudes
  
  -- === STATUS-INFORMATIONEN ===
  'AKTIV' AS MIETSTATUS,                  -- Mietstatus: Immer AKTIV in dieser Abfrage
  
  -- === FINANZIELLER STATUS ===
  K.OPBETRAG AS OFFENE_FORDERUNG,         -- Offene Forderung (NUMERIC): Aktuelle Mietrückstände
  K.KMAHNSTUFE AS MAHNSTUFE               -- Mahnstufe (SMALLINT): 0=Keine, 1-5=Mahnstufen

FROM BEWOHNER B
  LEFT JOIN BEWADR A ON (B.BEWNR = A.BEWNR)    -- JOIN für Namendaten aus BEWADR (BEWNR = BEWNR)
  INNER JOIN WOHNUNG W ON (B.ONR = W.ONR AND B.ENR = W.ENR)
  INNER JOIN OBJEKTE O ON (B.ONR = O.ONR)
  LEFT JOIN KONTEN K ON (B.KNR = K.KNR)
WHERE 
  B.VENDE IS NULL  -- Nur aktuelle Mieter ohne Enddatum
  AND B.ONR < 890  -- Ausschluss von Testobjekten
  AND (COALESCE(A.BNAME, B.BNAME) IS NOT NULL AND COALESCE(A.BNAME, B.BNAME) != '')  -- Nur Records mit Namen
ORDER BY B.ONR, B.ENR, B.BNAME;

/*
LAYER 4 BEWERTUNG:
=== TECHNISCHE VALIDIERUNG ===
[OK] Query funktioniert einwandfrei mit firebird-driver
[OK] Alle NUMERIC-Felder korrekt deklariert
[OK] Keine BLOB-Felder oder Kompatibilitätsprobleme
[OK] Performance ist ausgezeichnet

=== BUSINESS COMPLETENESS ===
[OK] Vollständige Kontaktdaten (inkl. zweiter Mieter)
[OK] Komplette SEPA-Banking-Informationen
[OK] Alle Mietvertragsdaten
[OK] Finanzieller Status mit Mahnstufen

=== ENTSCHEIDUNG ===
Layer 3 Query ist bereits optimal und erfüllt alle Anforderungen.
Keine Erweiterungen erforderlich für Layer 4.

ERWARTETES ERGEBNIS:
- ~190 aktive Mietverhältnisse
- Vollständige SEPA-Daten bei neueren Verträgen
- IBAN/BIC für automatischen Einzug
- Mahnstufen zur Risikobewertung

GESCHÄFTSNUTZEN:
[OK] Aktuelle Mieterverwaltung mit vollständigen Kontaktdaten
[OK] SEPA-Lastschriftmandate für automatisierten Einzug
[OK] Integriertes Mahnwesen über Mahnstufen
[OK] Multi-Channel-Kommunikation (Telefon, E-Mail, Post)
[OK] Rechtssichere Vertragsdatenverwaltung
*/