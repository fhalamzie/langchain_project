-- ============================================================================
-- QUERY 5C: BANKKONTEN Layer 4 - Liquiditätsübersicht (KKLASSE = 20)
-- ============================================================================
/*
GESCHÄFTSZWECK: Übersicht aller Bankkonten und Liquidität pro Objekt
HAUPTTABELLEN:
  - KONTEN: Kontenplan (gefiltert auf KKLASSE=20)
  - OBJEKTE: Objektzuordnung
  - OBJBANKEN: Bankverbindungen
GESCHÄFTSREGEL: KKLASSE=20 kennzeichnet Bankkonten
LAYER 4 ENHANCEMENT: Wiederherstellung der NUMERIC-Berechnungen (ohne ABS und EUR/m²)
*/

SELECT 
  -- === KONTO-IDENTIFIKATION ===
  K.KNR,                                  -- Kontonummer (INTEGER): Eindeutige Konto-ID
  K.KNRSTR AS KONTO_CODE,                 -- Kontocode (VARCHAR): "01200" für Banken
  K.KBEZ AS KONTO_BEZEICHNUNG,            -- Kontobezeichnung (VARCHAR): Bankname + Details
  
  -- === KONTOSTÄNDE (LAYER 4: NUMERIC RESTORED) ===
  K.KBRUTTO AS KONTOSTAND,                -- Kontostand (NUMERIC): Aktueller Saldo
  CASE 
    WHEN K.KBRUTTO >= 0 THEN K.KBRUTTO 
    ELSE 0 
  END AS GUTHABEN,                        -- Guthaben (NUMERIC): Positive Salden
  CASE 
    WHEN K.KBRUTTO < 0 THEN K.KBRUTTO
    ELSE 0 
  END AS UEBERZIEHUNG,                    -- Überziehung (NUMERIC): Negative Salden (ohne ABS)
  
  -- === BANK-EXTRAKTION AUS BEZEICHNUNG ===
  CASE 
    WHEN K.KBEZ LIKE '%Sparkasse%' THEN 'SPARKASSE'
    WHEN K.KBEZ LIKE '%Volksbank%' THEN 'VOLKSBANK'
    WHEN K.KBEZ LIKE '%Deutsche Bank%' THEN 'DEUTSCHE BANK'
    WHEN K.KBEZ LIKE '%Commerzbank%' THEN 'COMMERZBANK'
    WHEN K.KBEZ LIKE '%IBAN:%' THEN 'SEPA-KONTO'
    ELSE 'SONSTIGE BANK'
  END AS BANKINSTITUT,                    -- Bankinstitut: Aus Bezeichnung extrahiert
  
  -- === IBAN/BIC EXTRAKTION (falls in KBEZ) ===
  CASE 
    WHEN K.KBEZ LIKE '%IBAN:%' THEN 
      SUBSTRING(K.KBEZ FROM POSITION('IBAN:' IN K.KBEZ) + 6 FOR 22)
    ELSE NULL
  END AS IBAN_EXTRAHIERT,                -- IBAN: Aus Bezeichnung extrahiert
  
  -- === OBJEKT-ZUORDNUNG ===
  K.ONR,                                  -- Objektnummer (SMALLINT): Gebäude
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel (VARCHAR): Gebäude-Kürzel
  O.OSTRASSE AS OBJEKT_STRASSE,           -- Objektstraße (VARCHAR): Gebäudeadresse
  
  -- === KONTOTYP-KLASSIFIKATION ===
  CASE 
    WHEN K.KBEZ LIKE '%Girokonto%' THEN 'GIROKONTO'
    WHEN K.KBEZ LIKE '%Ruecklage%' THEN 'RUECKLAGENKONTO'
    WHEN K.KBEZ LIKE '%Kaution%' THEN 'KAUTIONSKONTO'
    WHEN K.KBEZ LIKE '%Festgeld%' THEN 'FESTGELD'
    WHEN K.KBEZ LIKE '%Tagesgeld%' THEN 'TAGESGELD'
    ELSE 'BETRIEBSKONTO'
  END AS KONTOTYP,                        -- Kontotyp: Verwendungszweck
  
  -- === LIQUIDITÄTS-STATUS (LAYER 4: Simplified) ===
  CASE 
    WHEN K.KBRUTTO > 0 THEN 'POSITIV'
    WHEN K.KBRUTTO < 0 THEN 'NEGATIV'
    ELSE 'NEUTRAL'
  END AS LIQUIDITAET_STATUS,              -- Liquiditätsstatus: Vereinfachte Bewertung
  
  -- === BANK-DETAILS AUS BANKEN (via OBJBANKEN) ===
  B.BEZEICHNUNG AS BANK_NAME,             -- Bankname (VARCHAR): Aus BANKEN
  B.BLZ AS BLZ,                           -- BLZ (VARCHAR): Bankleitzahl
  B.KONTO AS KONTONUMMER_ALT,             -- Kontonummer (VARCHAR): Alt-Format
  B.IBAN AS IBAN,                         -- IBAN (VARCHAR): SEPA-Format
  B.BIC AS BIC                            -- BIC (VARCHAR): SWIFT-Code

FROM KONTEN K
  LEFT JOIN OBJEKTE O ON K.ONR = O.ONR
  LEFT JOIN OBJBANKEN OB ON K.ONR = OB.ONR AND K.KNR = OB.KNR
  LEFT JOIN BANKEN B ON OB.BANKNR = B.NR
WHERE 
  K.KKLASSE = 20  -- Nur Bankkonten
  AND K.ONR < 890  -- Ausschluss von Testobjekten
ORDER BY 
  K.ONR,
  K.KBRUTTO DESC;  -- Höchste Guthaben zuerst (NUMERIC funktioniert jetzt!)

/*
LAYER 4 ENHANCEMENTS SUMMARY:
=== WIEDERHERGESTELLTE FUNKTIONALITÄT ===
+ NUMERIC-Felder: Alle Beträge wieder als NUMERIC statt VARCHAR
+ ORDER BY KBRUTTO DESC: Korrekte Sortierung nach Saldo
+ Überziehungsbeträge: Als negative Werte (ohne ABS-Umkehrung)
+ Liquiditätsstatus: Vereinfachte Bewertung (ohne EUR/m² Berechnung)

=== TECHNISCHE VERBESSERUNGEN ===
- Firebird-driver kompatible NUMERIC-Berechnungen
- Keine VARCHAR-Workarounds mehr nötig
- Stabile Sortierung nach numerischen Werten

ERWARTETES ERGEBNIS:
- Alle Bankkonten mit echten numerischen Salden
- Kontotyp-Klassifikation (Giro, Rücklage, etc.)
- Einfacher Liquiditätsstatus (POSITIV/NEGATIV/NEUTRAL)
- IBAN/BIC wo verfügbar
- Korrekte Sortierung nach Kontosaldo

GESCHÄFTSNUTZEN:
[RESTORED] Numerische Kontostände und Sortierung
[RESTORED] Überziehungsbeträge als echte Negativwerte
[OK] Liquiditätsübersicht pro Objekt
[OK] Trennung verschiedener Kontotypen
[OK] SEPA-Readiness der Bankkonten
[OK] Konsolidierte Finanzübersicht
*/