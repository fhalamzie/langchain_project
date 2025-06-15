-- ============================================================================
-- QUERY 08: BEIRÄTE (Enhanced) - Vollständiger Verwaltungsbeirat mit Kontakten
-- Layer 4 Version - Fixed BLOB field conversion and German encoding
-- ============================================================================
/*
BUSINESS PURPOSE: Komplette Verwaltungsbeirats-Verwaltung mit allen Positionen und Kontaktdaten
MAIN TABLES: OBJEKTE + EIGADR
KEY RELATIONSHIPS: OBJEKTE.VBR_NR* -> EIGADR.EIGNR (n:1 - Beirat-Referenzen)
LEGAL CONTEXT: § 29 WEG - Verwaltungsbeirat, Aufsichtsfunktion, Entscheidungsbefugnisse
*/

SELECT 
  -- === OBJEKTKONTEXT ===
  OBJEKTE.ONR,                            -- PK: Objekt-Nummer (SMALLINT)
  OBJEKTE.OPLZORT,                        -- Objekt PLZ/Ort (VARCHAR): Liegenschaftsadresse
  OBJEKTE.OSTRASSE,                       -- Objekt-Straße (VARCHAR): Liegenschaftsadresse
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- Liegenschafts-Kürzel (VARCHAR): Interne Referenz
  
  -- === BEIRATS-STRUKTUR (Alle 7 möglichen Positionen) ===
  OBJEKTE.VBR_NR1,                        -- Beirat 1 (INTEGER): Erstes Beiratsmitglied
  OBJEKTE.VBR_NR2,                        -- Beirat 2 (INTEGER): Zweites Beiratsmitglied
  OBJEKTE.VBR_NR3,                        -- Beirat 3 (INTEGER): Drittes Beiratsmitglied
  OBJEKTE.VBR_NR4,                        -- Beirat 4 (INTEGER): Viertes Beiratsmitglied
  OBJEKTE.VBR_NR5,                        -- Beirat 5 (INTEGER): Fünftes Beiratsmitglied
  OBJEKTE.VBR_NR6,                        -- Beirat 6 (INTEGER): Sechstes Beiratsmitglied
  OBJEKTE.VBR_NR_VORSITZ,                 -- Beirats-Vorsitzender (INTEGER): Vorsitzender des Beirats
  
  -- === BEIRATS-KONTAKTDATEN (Direkt aus OBJEKTE) ===
  OBJEKTE.VBR_NAME,                       -- Beirat Name (VARCHAR): Name des Haupt-Ansprechpartners
  OBJEKTE.VBR_FIRMA,                      -- Beirat Firma (VARCHAR): Firmenzugehörigkeit des Beirats
  OBJEKTE.VBR_TEL,                        -- Beirat Telefon (VARCHAR): Haupttelefonnummer Beirat
  OBJEKTE.VBR_EMAIL,                      -- Beirat E-Mail (VARCHAR): Digitale Kommunikation
  OBJEKTE.VBR_STR,                        -- Beirat Straße (VARCHAR): Postanschrift Beirat
  OBJEKTE.VBR_ORT,                        -- Beirat Ort (VARCHAR): Postort Beirat
  
  -- === AKTUELLES BEIRATS-MITGLIED (Detailed Info) ===
  EIGADR.EIGNR,                            -- Eigentümer-Nummer (INTEGER): ID des Beirats-Mitglieds
  EIGADR.EVNAME,                          -- Vorname (VARCHAR): Beirats-Mitglied Vorname
  EIGADR.EVNAME2,                         -- Vorname 2 (VARCHAR): Partner/Ehegatte bei Miteigentum
  EIGADR.ENAME,                           -- Nachname (VARCHAR): Beirats-Mitglied Nachname
  EIGADR.ENAME2,                          -- Nachname 2 (VARCHAR): Partner/Ehegatte bei Miteigentum
  CAST(EIGADR.ENOTIZ AS VARCHAR(2000)) AS EIGENTUEMERKUERZEL,  -- Eigentümer-Kürzel (BLOB->VARCHAR): Interne Referenz
  
  -- === INDIVIDUELLE KONTAKTDATEN BEIRATS-MITGLIEDER ===
  EIGADR.ETEL1,                           -- Telefon 1 (VARCHAR): Persönliche Telefonnummer
  EIGADR.ETEL2,                           -- Telefon 2 (VARCHAR): Alternative Telefonnummer
  EIGADR.EEMAIL,                          -- E-Mail (VARCHAR): Persönliche E-Mail-Adresse
  EIGADR.EHANDY,                          -- Handy (VARCHAR): Mobile Erreichbarkeit
  EIGADR.ESTR,                            -- Straße (VARCHAR): Private Anschrift
  EIGADR.EPLZORT,                         -- PLZ/Ort (VARCHAR): Private Postanschrift
  
  -- === BEIRATS-ROLLE (Calculated Field) ===
  CASE
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR_VORSITZ THEN 'Beiratsvorsitzender'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR1 THEN 'Beiratsmitglied (Position 1)'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR2 THEN 'Beiratsmitglied (Position 2)'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR3 THEN 'Beiratsmitglied (Position 3)'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR4 THEN 'Beiratsmitglied (Position 4)'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR5 THEN 'Beiratsmitglied (Position 5)'
    WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR6 THEN 'Beiratsmitglied (Position 6)'
    ELSE 'Unbekannte Beirats-Position'
  END AS BEIRATS_ROLLE,                   -- Calculated: Spezifische Rolle im Beirat
  
  -- === HAUSBETREUER (Operative Unterstützung) ===
  OBJEKTE.BETREUER_NR1                    -- Hausbetreuer-Nummer (INTEGER): Operative Ansprechpartner

FROM OBJEKTE
  INNER JOIN EIGADR ON (
    OBJEKTE.VBR_NR1 = EIGADR.EIGNR OR 
    OBJEKTE.VBR_NR2 = EIGADR.EIGNR OR 
    OBJEKTE.VBR_NR3 = EIGADR.EIGNR OR
    OBJEKTE.VBR_NR4 = EIGADR.EIGNR OR
    OBJEKTE.VBR_NR5 = EIGADR.EIGNR OR
    OBJEKTE.VBR_NR6 = EIGADR.EIGNR OR
    OBJEKTE.VBR_NR_VORSITZ = EIGADR.EIGNR
  )
WHERE
  ONR NOT LIKE 0                          -- Ausschluss "Nicht zugeordnet"
  AND ONR < 890                           -- Ausschluss Test-Objekte
ORDER BY OBJEKTE.ONR, 
         CASE 
           WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR_VORSITZ THEN 1
           WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR1 THEN 2
           WHEN EIGADR.EIGNR = OBJEKTE.VBR_NR2 THEN 3
           ELSE 4
         END;

/*
EXPECTED RESULTS (basierend auf Beiräte.csv):
- Cassavi Testobjekt: Paul Bauchrowitz (EIGNR=1192)
- KUPFE190_W: Ruhrstadt Immobilien Service GmbH (EIGNR=606)
- Verschiedene Beirats-Strukturen je nach WEG-Größe

BUSINESS VALUE:
[OK] Vollständige Beirats-Struktur (7 Positionen statt nur 3)
[OK] Zentrale Beirats-Kontaktdaten aus OBJEKTE
[OK] Individuelle Kontaktdaten aller Beirats-Mitglieder
[OK] Klare Rollen-Zuordnung mit Hierarchie
[OK] Hausbetreuer-Integration für operative Aufgaben
[OK] BLOB field converted to VARCHAR for cross-driver compatibility
*/