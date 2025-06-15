-- ============================================================================
-- QUERY 5B: MIETERKONTEN Layer 4 - Mietverwaltung Kontoführung (KKLASSE = 60)
-- ============================================================================
/*
GESCHÄFTSZWECK: Übersicht aller Mieterkonten mit Zahlungsstatus
HAUPTTABELLEN:
  - KONTEN: Kontenplan (gefiltert auf KKLASSE=60)
  - BEWOHNER: Mieterstammdaten
  - WOHNUNG: Einheitenzuordnung
GESCHÄFTSREGEL: KKLASSE=60 kennzeichnet Mieterkonten
LAYER 4 ENHANCEMENT: Wiederherstellung der NUMERIC-Berechnungen mit firebird-driver
*/

SELECT 
  -- === KONTO-IDENTIFIKATION ===
  K.KNR,                                  -- Kontonummer (INTEGER): Eindeutige Konto-ID
  K.KNRSTR AS KONTO_CODE,                 -- Kontocode (VARCHAR): z.B. "B.001.01"
  K.KBEZ AS KONTO_BEZEICHNUNG,            -- Kontobezeichnung (VARCHAR): Mietername
  
  -- === KONTOSTÄNDE (LAYER 4: NUMERIC RESTORED) ===
  K.KBRUTTO AS KONTOSTAND,                -- Kontostand (NUMERIC): Aktueller Saldo
  K.OPBETRAG AS OFFENE_MIETE,             -- Offene Miete (NUMERIC): Mietrückstände
  CASE 
    WHEN K.KBRUTTO > 0 THEN K.KBRUTTO 
    ELSE 0 
  END AS GUTHABEN,                        -- Guthaben (NUMERIC): Positive Salden als Guthaben
  
  -- === MAHNWESEN ===
  K.KMAHNSTUFE AS MAHNSTUFE,              -- Mahnstufe (SMALLINT): 0-5 Eskalation
  K.MAHNDATUM AS LETZTES_MAHNDATUM,       -- Mahndatum (DATE): Letzte Mahnung
  CASE 
    WHEN K.KMAHNSTUFE = 0 THEN 'KEINE MAHNUNG'
    WHEN K.KMAHNSTUFE = 1 THEN 'ZAHLUNGSERINNERUNG'
    WHEN K.KMAHNSTUFE = 2 THEN '1. MAHNUNG'
    WHEN K.KMAHNSTUFE = 3 THEN '2. MAHNUNG'
    WHEN K.KMAHNSTUFE = 4 THEN '3. MAHNUNG'
    WHEN K.KMAHNSTUFE >= 5 THEN 'RECHTSANWALT'
    ELSE 'UNBEKANNT'
  END AS MAHNSTUFE_TEXT,                  -- Mahnstufe Text: Klartext-Beschreibung
  
  -- === MIETER-INFORMATION ===
  B.BNAME || ', ' || B.BVNAME AS MIETER_NAME, -- Mietername: Nachname, Vorname
  B.VBEGINN AS MIETBEGINN,                -- Mietbeginn (DATE): Vertragsbeginn
  B.VENDE AS MIETENDE,                    -- Mietende (DATE): NULL=Aktiv
  B.MIETE1 AS SOLL_MIETE,                 -- Sollmiete (NUMERIC): Vereinbarte Warmmiete
  
  -- === ZAHLUNGSVERHALTEN (LAYER 4: 5-STUFIG RESTORED) ===
  CASE 
    WHEN B.VENDE IS NOT NULL AND B.VENDE < CURRENT_DATE THEN 'AUSGEZOGEN'
    WHEN K.OPBETRAG = 0 THEN 'PUENKTLICH'
    WHEN K.OPBETRAG <= B.MIETE1 THEN 'LEICHTER VERZUG'
    WHEN K.OPBETRAG <= B.MIETE1 * 2 THEN 'VERZUG 1-2 MONATE'
    WHEN K.OPBETRAG <= B.MIETE1 * 3 THEN 'VERZUG 2-3 MONATE'
    ELSE 'KRITISCHER VERZUG >3 MONATE'
  END AS ZAHLUNGSSTATUS,                  -- Zahlungsstatus: 5-stufige Kategorisierung
  
  -- === WOHNUNGS-ZUORDNUNG ===
  K.ONR,                                  -- Objektnummer (SMALLINT): Gebäude
  K.ENR,                                  -- Einheitsnummer (SMALLINT): Wohnung
  W.EBEZ AS WOHNUNGS_BEZEICHNUNG,         -- Wohnungsbezeichnung: z.B. "EG rechts"
  
  -- === OBJEKT-KONTEXT ===
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel (VARCHAR): Gebäude-Kürzel
  O.OSTRASSE AS OBJEKT_STRASSE,           -- Objektstraße (VARCHAR): Gebäudeadresse
  
  -- === MIETVERZUG-BERECHNUNG (LAYER 4: RESTORED) ===
  CASE 
    WHEN K.OPBETRAG > 0 AND B.MIETE1 > 0 THEN 
      CAST(K.OPBETRAG / B.MIETE1 AS NUMERIC(15,2))
    ELSE 0
  END AS VERZUG_IN_MONATSMIETEN,          -- Verzug: Anzahl Monatsmieten (ohne ROUND)
  
  -- === KONTAKT FÜR MAHNWESEN ===
  B.BTEL AS TELEFON,                      -- Telefon (VARCHAR): Für Rückfragen
  B.BEMAIL AS EMAIL                       -- E-Mail (VARCHAR): Für Mahnungen

FROM KONTEN K
  LEFT JOIN BEWOHNER B ON K.KNR = B.KNR
  LEFT JOIN WOHNUNG W ON K.ONR = W.ONR AND K.ENR = W.ENR
  LEFT JOIN OBJEKTE O ON K.ONR = O.ONR
WHERE 
  K.KKLASSE = 60  -- Nur Mieterkonten
  AND K.ONR < 890  -- Ausschluss von Testobjekten
ORDER BY 
  K.KMAHNSTUFE DESC,  -- Kritische Fälle zuerst
  K.OPBETRAG DESC,    -- Höchste Rückstände zuerst (NUMERIC funktioniert jetzt!)
  K.ONR, K.ENR;

/*
LAYER 4 ENHANCEMENTS SUMMARY:
=== WIEDERHERGESTELLTE FUNKTIONALITÄT ===
+ NUMERIC-Felder: Alle Beträge wieder als NUMERIC statt VARCHAR
+ VERZUG_IN_MONATSMIETEN: Berechnung wiederhergestellt mit CAST AS NUMERIC(15,2)
+ 5-stufige Zahlungsstatus-Kategorisierung: Vollständig wiederhergestellt
+ ORDER BY mit NUMERIC-Feldern: Jetzt korrekte Sortierung nach Betrag

=== TECHNISCHE VERBESSERUNGEN ===
- ROUND() entfernt, stattdessen CAST AS NUMERIC(15,2) für Präzision
- Firebird-driver kompatible NUMERIC-Berechnungen
- Keine VARCHAR-Workarounds mehr nötig

ERWARTETES ERGEBNIS:
- Alle Mieterkonten mit echten Zahlungsbeträgen
- 5-stufige Mahnstufen-Eskalation
- Verzug präzise in Monatsmieten berechnet
- Korrekte Sortierung nach Rückstandshöhe

GESCHÄFTSNUTZEN:
[RESTORED] Präzise Verzugsberechnung in Monatsmieten
[RESTORED] 5-stufige Zahlungsstatus-Kategorisierung
[RESTORED] Korrekte numerische Sortierung
[OK] Mietforderungsmanagement auf einen Blick
[OK] Priorisierung kritischer Fälle
[OK] Automatisiertes Mahnwesen möglich
[OK] Kontaktdaten direkt verfügbar
*/