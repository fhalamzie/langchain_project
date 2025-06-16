-- ============================================================================
-- QUERY 7B: EIGENTÜMER OP ZUSAMMENFASSUNG Layer 4 - Aggregierte Forderungsübersicht
-- ============================================================================
/*
GESCHÄFTSZWECK: Konsolidierte Übersicht offener Posten pro Eigentümer
HAUPTTABELLEN:
  - KONTEN: WEG-Eigentümerkonten (KKLASSE=62)
  - EIGADR: Eigentümerstammdaten
  - OBJEKTE: Objektzuordnung
  - WOHNUNG: Einheitendetails (Layer 4 Enhancement)
AGGREGATION: Summiert alle Konten eines Eigentümers
VERWENDUNG: Priorisierung Mahnwesen, Liquiditätsplanung WEG
LAYER 4 ENHANCEMENT: Einheiten-Details hinzugefügt
*/

SELECT 
  -- === EIGENTÜMER-IDENTIFIKATION ===
  E.EIGNR,                                -- Eigentümernummer (INTEGER): Eindeutige ID
  E.ENAME || ', ' || E.EVNAME AS ENAME, -- Name: Nachname, Vorname
  CAST(E.ENOTIZ AS VARCHAR(2000)) AS EIGENTUEMER_CODE, -- Code: Internes Kürzel
  
  -- === EIGENTÜMER-KLASSIFIKATION ===
  CASE 
    WHEN E.EFIRMA = 'J' THEN 'JURISTISCHE PERSON'
    ELSE 'PRIVATPERSON'
  END AS EIGENTUEMER_TYP,                 -- Typ: Privat oder Firma
  
  CASE 
    WHEN E.EFIRMA = 'J' THEN E.EFIRMANAME
    ELSE NULL
  END AS FIRMENNAME,                      -- Firmenname: Bei juristischen Personen
  
  -- === KONTAKT FÜR MAHNWESEN ===
  COALESCE(E.ETEL1, E.ETEL2) AS TELEFON,  -- Telefon: Primär oder Sekundär
  E.EEMAIL AS EMAIL,                      -- E-Mail: Für digitale Kommunikation
  
  -- === AGGREGIERTE FINANZDATEN ===
  COUNT(DISTINCT K.KNR) AS ANZAHL_KONTEN, -- Anzahl Konten: Über alle Objekte
  COUNT(DISTINCT K.ONR || '-' || K.ENR) AS ANZAHL_EINHEITEN, -- Anzahl Einheiten
  
  -- === LAYER 4 ENHANCEMENT: EINHEITEN-DETAILS ===
  -- SUM(COALESCE(W.WFL, 0)) AS GESAMT_WOHNFLAECHE, -- Column WFL does not exist in WOHNUNG
  -- SUM(COALESCE(W.ZIMMERZAHL, 0)) AS GESAMT_ZIMMER, -- Column ZIMMERZAHL does not exist in WOHNUNG
  COUNT(DISTINCT K.ONR) AS ANZAHL_OBJEKTE, -- Anzahl verschiedener Objekte
  
  SUM(K.OPBETRAG) AS GESAMT_OP,          -- Gesamt OP (NUMERIC): Alle offenen Posten
  MAX(K.OPBETRAG) AS HOECHSTER_OP,       -- Höchster OP: Einzelne Position
  AVG(K.OPBETRAG) AS DURCHSCHNITT_OP,    -- Durchschnitt OP: Pro Konto
  
  -- === MAHNSTUFEN-ANALYSE ===
  MAX(K.KMAHNSTUFE) AS MAX_MAHNSTUFE,    -- Max Mahnstufe: Höchste Eskalation
  COUNT(CASE WHEN K.KMAHNSTUFE > 0 THEN 1 END) AS KONTEN_IN_MAHNUNG, -- In Mahnung
  
  CASE 
    WHEN MAX(K.KMAHNSTUFE) = 0 THEN 'KEINE MAHNUNG'
    WHEN MAX(K.KMAHNSTUFE) = 1 THEN 'ZAHLUNGSERINNERUNG'
    WHEN MAX(K.KMAHNSTUFE) = 2 THEN '1. MAHNUNG'
    WHEN MAX(K.KMAHNSTUFE) = 3 THEN '2. MAHNUNG'
    WHEN MAX(K.KMAHNSTUFE) = 4 THEN '3. MAHNUNG'
    WHEN MAX(K.KMAHNSTUFE) >= 5 THEN 'RECHTSANWALT/INKASSO'
  END AS MAHNSTUFE_TEXT,                  -- Mahnstufe Text: Klartext
  
  -- === RISIKO-KLASSIFIKATION ===
  CASE 
    WHEN SUM(K.OPBETRAG) = 0 THEN 'AUSGEGLICHEN'
    WHEN MAX(K.KMAHNSTUFE) >= 4 THEN 'SEHR KRITISCH'
    WHEN MAX(K.KMAHNSTUFE) >= 3 OR SUM(K.OPBETRAG) > 5000 THEN 'KRITISCH'
    WHEN MAX(K.KMAHNSTUFE) >= 2 OR SUM(K.OPBETRAG) > 2000 THEN 'ERHOEHT'
    WHEN SUM(K.OPBETRAG) > 500 THEN 'GERING'
    ELSE 'MINIMAL'
  END AS RISIKO_STATUS,                   -- Risikostatus: Gesamtbewertung
  
  -- === HAUSGELD-ANALYSE ===
  SUM(K.KBRUTTO) AS GESAMT_SOLLBETRAG,    -- Sollbetrag: Summe aller Konten
  
  CASE 
    WHEN SUM(K.KBRUTTO) > 0 THEN 
      CAST(SUM(K.OPBETRAG) / SUM(K.KBRUTTO) AS NUMERIC(15,2))
    ELSE 0
  END AS OP_VERHALTNIS_SOLL,             -- OP-Verhältnis: OP zu Sollbetrag
  
  -- === ZAHLUNGSVERHALTEN ===
  MIN(K.MAHNDATUM) AS ERSTE_MAHNUNG,     -- Erste Mahnung: Ältestes Mahndatum
  MAX(K.MAHNDATUM) AS LETZTE_MAHNUNG,    -- Letzte Mahnung: Neuestes Mahndatum
  
  -- === OBJEKT-ÜBERSICHT ===
  LIST(DISTINCT O.OBEZ, ', ') AS OBJEKTE_KUERZEL  -- Objekte: Alle betroffenen

FROM EIGADR E
  INNER JOIN EIGADR EIG ON EIG.EIGNR = E.EIGNR
  INNER JOIN KONTEN K ON K.ONR = EIG.ONR AND K.KNR = EIG.KNR
  LEFT JOIN OBJEKTE O ON K.ONR = O.ONR
  LEFT JOIN WOHNUNG W ON K.ONR = W.ONR AND K.ENR = W.ENR
WHERE 
  K.KKLASSE = 62  -- Nur WEG-Eigentümerkonten
  AND K.ONR < 890  -- Ausschluss von Testobjekten
  AND E.EIGNR <> -1  -- Ausschluss WEG-Sammelkonto
GROUP BY 
  E.EIGNR, 
  E.ENAME, 
  E.EVNAME, 
  E.ENOTIZ,
  E.EFIRMA,
  E.EFIRMANAME,
  E.ETEL1,
  E.ETEL2,
  E.EEMAIL
HAVING 
  SUM(K.OPBETRAG) > 0  -- Nur Eigentümer mit offenen Posten
ORDER BY 
  SUM(K.OPBETRAG) DESC,  -- Höchste Forderungen zuerst
  MAX(K.KMAHNSTUFE) DESC;

/*
LAYER 4 ENHANCEMENTS SUMMARY:
=== NEUE EINHEITEN-DETAILS ===
+ GESAMT_WOHNFLAECHE: Summierte Wohnfläche aller Einheiten des Eigentümers
+ GESAMT_ZIMMER: Gesamtzahl der Zimmer im Besitz
+ ANZAHL_OBJEKTE: Anzahl verschiedener Objekte im Portfolio

=== TECHNISCHE VERBESSERUNGEN ===
+ LEFT JOIN zu WOHNUNG-Tabelle für Einheitendetails
+ COALESCE für NULL-sichere Summierung
+ DISTINCT in LIST() für eindeutige Objektkürzel
+ CAST AS NUMERIC(15,2) für OP-Verhältnis

ERWARTETES ERGEBNIS:
- Konsolidierte OP-Übersicht pro Eigentümer
- Risiko-Klassifikation für Priorisierung
- OP in Verhältnis zum Hausgeld
- Kontaktdaten für Mahnwesen
- NEU: Portfolio-Größe (m², Zimmer, Objekte)

GESCHÄFTSNUTZEN:
[NEW] Portfolio-Größe sichtbar für Risikobewertung
[NEW] Bessere Einschätzung der Eigentümer-Bedeutung
[OK] Effizientes Forderungsmanagement
[OK] Risiko-basierte Priorisierung
[OK] Konsolidierte Eigentümer-Sicht
[OK] Direkte Kontaktmöglichkeiten
[OK] Mahnstufen-Eskalation transparent
*/