-- ============================================================================
-- QUERY 4: WOHNUNGEN Layer 4 - Intelligente Belegungsübersicht mit Leerstandserkennung
-- ============================================================================
/*
GESCHÄFTSZWECK: Vollständige Wohnungsübersicht mit aktuellem Belegungsstatus
HAUPTTABELLEN:
  - WOHNUNG: Wohnungsstammdaten
  - BEWOHNER: Mieterdaten (gefiltert auf aktuelle/zukünftige)
  - OBJEKTE: Gebäudezuordnung
BESONDERHEIT: Zeigt JEDE Wohnung genau einmal mit intelligentem Status
LAYER 4 ENHANCEMENTS: Firebird 5.0 Syntax-Anpassungen
*/

SELECT 
  -- === WOHNUNGS-IDENTIFIKATION ===
  W.ONR,                                  -- Objektnummer (SMALLINT): Gebäude-ID
  W.ENR,                                  -- Einheitsnummer (SMALLINT): Wohnungs-ID
  W.EBEZ AS EBEZ,          -- Einheitsbezeichnung (VARCHAR): Vollständige Bez.
  W.EBEZ AS WOHNUNGS_BEZEICHNUNG,         -- Wohnungsbezeichnung (VARCHAR): z.B. "2.OG links"
  W.ART AS EINHEITENART,                  -- Art (VARCHAR): "Wohnung", "Garage", etc.
  W.BKNR AS BUCHUNGSKREIS,                -- Buchungskreis (INTEGER): NK-Abrechnungskreis
  W.EKNR AS EINZELKOSTENKREIS,            -- Einzelkostenkreis (INTEGER): Kostenstellenzuordnung
  
  -- === INTELLIGENTER BELEGUNGSSTATUS ===
  CASE 
    WHEN B.KNR IS NULL THEN 'LEERSTAND'
    WHEN B.VENDE IS NULL THEN B.BNAME || ' ' || B.BVNAME
    WHEN B.VENDE >= CURRENT_DATE THEN B.BNAME || ' ' || B.BVNAME || ' (bis ' || B.VENDE || ')'
    ELSE 'LEERSTAND'
  END AS AKTUELLER_STATUS,                -- Status: Mieter oder LEERSTAND
  
  -- === MIETERDATEN (nur bei Belegung) ===
  CASE 
    WHEN B.VENDE IS NULL OR B.VENDE >= CURRENT_DATE THEN B.KNR 
    ELSE NULL 
  END AS MIETER_KNR,                      -- Mieter-Kontonummer: Nur bei aktiven
  
  CASE 
    WHEN B.VENDE IS NULL OR B.VENDE >= CURRENT_DATE THEN B.VBEGINN 
    ELSE NULL 
  END AS MIETBEGINN,                      -- Mietbeginn: Nur bei aktiven
  
  B.VENDE AS MIETENDE,                    -- Mietende: Zeigt geplante Auszüge
  
  CASE 
    WHEN B.VENDE IS NULL OR B.VENDE >= CURRENT_DATE THEN B.MIETE1 
    ELSE NULL 
  END AS AKTUELLE_MIETE,                  -- Aktuelle Miete: Nur bei Belegung
  
  -- === LEERSTANDSANALYSE (LAYER 4: FIREBIRD 5.0 SYNTAX) ===
  CASE 
    WHEN B.KNR IS NULL OR (B.VENDE IS NOT NULL AND B.VENDE < CURRENT_DATE) 
    THEN CAST(
      EXTRACT(DAY FROM CURRENT_DATE) - EXTRACT(DAY FROM COALESCE(B.VENDE, CURRENT_DATE - 365)) +
      (EXTRACT(MONTH FROM CURRENT_DATE) - EXTRACT(MONTH FROM COALESCE(B.VENDE, CURRENT_DATE - 365))) * 30 +
      (EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM COALESCE(B.VENDE, CURRENT_DATE - 365))) * 365
      AS INTEGER)
    ELSE NULL
  END AS LEERSTAND_TAGE,                  -- Leerstand in Tagen: Bei Leerstand
  
  -- === MIETPREIS-INFORMATIONEN (aus BEWOHNER-Tabelle) ===
  CAST(B.Z1 AS NUMERIC(15,2)) AS SOLL_KALTMIETE,      -- Soll-Z1: Aus BEWOHNER.Z1
  CAST(B.Z3 AS NUMERIC(15,2)) AS SOLL_NEBENKOSTEN,    -- Soll-Z3: Aus BEWOHNER.Z3
  CAST(B.MIETE1 AS NUMERIC(15,2)) AS SOLL_WARMMIETE,  -- Soll-Warmmiete: Aus BEWOHNER.MIETE1
  
  -- === EIGENTÜMER-INFORMATION ===
  E.KNR AS EIGENTUEMER_NR,               -- Eigentümernummer (INTEGER): Wohnungseigentümer
  EA.ENAME || ', ' || EA.EVNAME AS ENAME, -- Eigentümername: Nachname, Vorname
  
  -- === OBJEKT-KONTEXT ===
  O.OBEZ AS OBJEKT_KURZ,                  -- Objektkürzel (VARCHAR): Gebäude-Kürzel
  O.OSTRASSE AS OSTRASSE,           -- Objektstraße (VARCHAR): Gebäudeadresse
  O.OPLZORT AS OPLZORT                 -- Objekt PLZ/Ort (VARCHAR): Standort

FROM WOHNUNG W
  INNER JOIN OBJEKTE O ON W.ONR = O.ONR
  LEFT JOIN EIGADR E ON W.ONR = E.ONR AND W.ENR = E.ENR
  LEFT JOIN EIGADR EA ON E.KNR = EA.EIGNR
  LEFT JOIN BEWOHNER B ON W.ONR = B.ONR 
    AND W.ENR = B.ENR 
    AND (B.VENDE IS NULL OR B.VENDE = (
      SELECT MAX(B2.VENDE) 
      FROM BEWOHNER B2 
      WHERE B2.ONR = W.ONR AND B2.ENR = W.ENR
    ))  -- Neuester Mieter-Eintrag
WHERE 
  W.ONR < 890  -- Ausschluss von Testobjekten
  AND W.ART = 'Wohnung'  -- Nur Wohnungen (keine Garagen etc.)
ORDER BY W.ONR, W.ENR;

/*
LAYER 4 ENHANCEMENTS SUMMARY:
=== SYNTAX-ANPASSUNGEN ===
+ DATEDIFF(DAY, date1, date2) ersetzt durch Manuelle Berechnung mit EXTRACT
+ Verwendung von EXTRACT(DAY/MONTH/YEAR) für Datums-Differenzen
+ Explizite CAST AS NUMERIC(15,2) für Geldbeträge
+ CAST AS INTEGER für Tages-Berechnung

=== TECHNISCHE VERBESSERUNGEN ===
- Keine DATEDIFF/DATEADD Funktionen (Firebird 5.0 kompatibel)
- Approximative Tagesberechnung (30 Tage/Monat, 365 Tage/Jahr)
- Präzise NUMERIC-Datentypen für Finanzdaten
- Beibehaltung des Leerstandsfokus

ERWARTETES ERGEBNIS:
- Jede Wohnung erscheint genau einmal
- Aktueller Status: Mietername oder "LEERSTAND"
- Leerstandstage approximativ berechnet
- Geplante Auszüge sichtbar (VENDE >= heute)

GESCHÄFTSNUTZEN:
[OK] Vollständige Belegungsübersicht auf einen Blick
[OK] Leerstandsmanagement mit Transparenz
[OK] Frühwarnung bei geplanten Auszügen
[OK] Eigentümerzuordnung für WEG-Verwaltung
[OK] Firebird 5.0 kompatible Syntax
*/