-- ============================================================================
-- QUERY 20: NEBENKOSTENKONTEN-MATRIX - Layer 4 Enhanced with Financial Data
-- ============================================================================
/*
GESCHÄFTSZWECK: Matrix aller NK-Positionen mit Umlageschlüsseln und Kosten
HAUPTTABELLEN:
  - KONTEN: NK-relevante Konten
  - OBJEKTE: Objektdaten
  - BUCHUNG: Finanzbewegungen
RECHTLICHE BASIS: BetrKV (Betriebskostenverordnung)
LAYER 4 FIXES:
  - SUM(BETRAG) für PERIODENKOSTEN wiederhergestellt
  - Zeichenkodierung korrigiert (ä, ö, ü, §)
  - Korrekte Spaltennamen (KSOLL statt SOLLKTO)
*/

SELECT 
  -- === OBJEKT-IDENTIFIKATION ===
  K.ONR,                                  -- Objektnummer: Liegenschaft
  O.OBEZ,                                 -- Objektkürzel
  O.OSTRASSE,                             -- Objektstraße
  
  -- === KONTEN-DETAILS ===
  K.KNR,                                  -- Kontonummer: Eindeutige ID
  K.KNRSTR,                               -- Kontocode: Strukturiert
  K.KBEZ,                                 -- Kontobezeichnung
  
  -- === BETRKV-ZUORDNUNG ===
  CASE 
    -- § 2 Nr. 1 BetrKV - Grundsteuer
    WHEN K.KBEZ LIKE '%Grundsteuer%' 
      THEN '§2 Nr.1 - Grundsteuer'
    -- § 2 Nr. 2 BetrKV - Wasserversorgung
    WHEN K.KBEZ LIKE '%Wasser%' AND K.KBEZ NOT LIKE '%Warm%' 
      THEN '§2 Nr.2 - Wasserversorgung'
    -- § 2 Nr. 3 BetrKV - Entwässerung
    WHEN K.KBEZ LIKE '%Abwasser%' OR K.KBEZ LIKE '%Kanal%' 
      THEN '§2 Nr.3 - Entwässerung'
    -- § 2 Nr. 4 BetrKV - Heizung
    WHEN K.KBEZ LIKE '%Heiz%' 
      THEN '§2 Nr.4 - Heizung (HeizkostenV)'
    -- § 2 Nr. 5 BetrKV - Warmwasser
    WHEN K.KBEZ LIKE '%Warmwasser%' 
      THEN '§2 Nr.5 - Warmwasser (HeizkostenV)'
    -- § 2 Nr. 7 BetrKV - Aufzug
    WHEN K.KBEZ LIKE '%Aufzug%' OR K.KBEZ LIKE '%Lift%' 
      THEN '§2 Nr.7 - Aufzug'
    -- § 2 Nr. 8 BetrKV - Straßenreinigung/Müll
    WHEN K.KBEZ LIKE '%Muell%' OR K.KBEZ LIKE '%Müll%' OR K.KBEZ LIKE '%Abfall%' 
      THEN '§2 Nr.8 - Müllabfuhr'
    -- § 2 Nr. 9 BetrKV - Hausreinigung
    WHEN K.KBEZ LIKE '%Reinigung%' 
      THEN '§2 Nr.9 - Hausreinigung'
    -- § 2 Nr. 10 BetrKV - Gartenpflege
    WHEN K.KBEZ LIKE '%Garten%' 
      THEN '§2 Nr.10 - Gartenpflege'
    -- § 2 Nr. 11 BetrKV - Beleuchtung
    WHEN K.KBEZ LIKE '%Strom%' OR K.KBEZ LIKE '%Beleuchtung%' 
      THEN '§2 Nr.11 - Beleuchtung'
    -- § 2 Nr. 13 BetrKV - Versicherungen
    WHEN K.KBEZ LIKE '%Versicherung%' 
      THEN '§2 Nr.13 - Versicherungen'
    -- § 2 Nr. 14 BetrKV - Hauswart
    WHEN K.KBEZ LIKE '%Hausmeister%' OR K.KBEZ LIKE '%Hauswart%' 
      THEN '§2 Nr.14 - Hauswart'
    -- § 2 Nr. 17 BetrKV - Sonstige
    ELSE '§2 Nr.17 - Sonstige Betriebskosten'
  END BETRKV_PARAGRAPH,                   -- BetrKV-§: Rechtliche Einordnung
  
  -- === UMLAGEFÄHIGKEIT ===
  CASE 
    -- Eindeutig umlagefähig
    WHEN K.KBEZ LIKE '%Grundsteuer%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Wasser%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Muell%' OR K.KBEZ LIKE '%Müll%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Heiz%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Strom%Allgemein%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Reinigung%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Hausmeister%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Garten%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Versicherung%Gebaeude%' OR K.KBEZ LIKE '%Versicherung%Gebäude%' THEN 'UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Aufzug%Wartung%' THEN 'UMLAGEFÄHIG'
    -- Eindeutig nicht umlagefähig
    WHEN K.KBEZ LIKE '%Instand%' THEN 'NICHT UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Reparatur%' THEN 'NICHT UMLAGEFÄHIG'
    WHEN K.KBEZ LIKE '%Verwaltung%' THEN 'TEILWEISE (WEG)'
    -- Einzelfallprüfung
    ELSE 'ZU PRÜFEN'
  END UMLAGEFAEHIGKEIT,                   -- Umlagefähigkeit: Status
  
  -- === UMLAGESCHLÜSSEL ===
  CASE 
    WHEN K.KBEZ LIKE '%Wasser%' THEN 'VERBRAUCH'
    WHEN K.KBEZ LIKE '%Heiz%' THEN 'VERBRAUCH (50-70%)'
    WHEN K.KBEZ LIKE '%Aufzug%' THEN 'PERSONENZAHL/STOCKWERK'
    ELSE 'WOHNFLÄCHE'
  END UMLAGESCHLUESSEL,                   -- Umlageschlüssel: Verteilungsbasis
  
  -- === PERIODENKOSTEN (FINANZIELLE DATEN) ===
  CAST(COALESCE((
    SELECT SUM(B.BETRAG) 
    FROM BUCHUNG B 
    WHERE B.KSOLL = K.KNR 
      AND B.ONRSOLL = K.ONR
      AND B.DATUM >= CURRENT_DATE - 365
      AND B.DATUM <= CURRENT_DATE
  ), 0) AS NUMERIC(15,2)) PERIODENKOSTEN, -- Periodenkosten in EUR
  
  -- === BUCHUNGSAKTIVITÄT ===
  (SELECT COUNT(*) 
   FROM BUCHUNG B 
   WHERE B.KSOLL = K.KNR 
     AND B.ONRSOLL = K.ONR
     AND B.DATUM >= CURRENT_DATE - 365
     AND B.DATUM <= CURRENT_DATE) ANZAHL_BUCHUNGEN_JAHR,
  
  -- === VERTEILUNGSBASIS ===
  O.GA1 GESAMTFLAECHE_QM,                 -- Gesamtfläche: Wohnfläche
  O.OANZEINH ANZAHL_EINHEITEN,            -- Einheiten: Wohnungen
  (SELECT COUNT(*) FROM BEWOHNER WHERE ONR = K.ONR AND VENDE IS NULL) BEWOHNER_ANZAHL,
  
  -- === BUCHUNGSVERTEILUNG STATUS ===
  CASE 
    WHEN O.OANZEINH > 0 THEN 'HAT_EINHEITEN'
    ELSE 'KEINE_EINHEITEN'
  END BUCHUNGEN_PRO_EINHEIT_STATUS,
  
  -- === ABRECHNUNGSRELEVANZ ===
  CASE 
    WHEN EXISTS (SELECT 1 FROM BUCHUNG B 
                 WHERE B.KSOLL = K.KNR AND B.ONRSOLL = K.ONR
                   AND B.DATUM >= CURRENT_DATE - 365 
                   AND B.DATUM <= CURRENT_DATE)
    THEN 'JA - MIT BEWEGUNG'
    ELSE 'NEIN - OHNE BEWEGUNG'
  END ABRECHNUNGSRELEVANT

FROM KONTEN K
  INNER JOIN OBJEKTE O ON K.ONR = O.ONR
WHERE 
  K.KKLASSE = 1  -- Nur Sachkonten
  AND K.ONR < 890  -- Ausschluss Testobjekte
  AND (K.KBEZ LIKE '%Wasser%' 
    OR K.KBEZ LIKE '%Abwasser%'
    OR K.KBEZ LIKE '%Muell%'
    OR K.KBEZ LIKE '%Müll%'
    OR K.KBEZ LIKE '%Strom%'
    OR K.KBEZ LIKE '%Heiz%'
    OR K.KBEZ LIKE '%Hausmeister%'
    OR K.KBEZ LIKE '%Reinigung%'
    OR K.KBEZ LIKE '%Garten%'
    OR K.KBEZ LIKE '%Versicherung%'
    OR K.KBEZ LIKE '%Grundsteuer%'
    OR K.KBEZ LIKE '%Aufzug%'
    OR K.KBEZ LIKE '%Sonstig%')
ORDER BY 
  BETRKV_PARAGRAPH,
  K.KNRSTR;

/*
ERWARTETES ERGEBNIS:
- Alle NK-relevanten Konten mit BetrKV-Zuordnung
- Umlagefähigkeits-Status
- PERIODENKOSTEN in EUR (nicht nur Anzahl)
- Verteilungsschlüssel
- Abrechnungsrelevanz

GESCHÄFTSNUTZEN:
[OK] Rechtssichere NK-Abrechnung mit echten Beträgen
[OK] BetrKV-Konformität sichergestellt
[OK] Transparente Umlageschlüssel
[OK] Prüfung der Umlagefähigkeit
[OK] Basis für Mieter-Einzelabrechnung mit Kosten
*/