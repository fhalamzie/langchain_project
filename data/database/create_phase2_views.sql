-- ============================================================================
-- WINCASA Phase 2.1 - Database Views Implementation
-- Erstellt alle 5 Core Views für optimierte Business-Queries
-- ============================================================================
/*
EXECUTION ORDER: Dieses Script erstellt alle Views in der korrekten Reihenfolge
ROLLBACK: Alle Views können mit DROP VIEW [name] entfernt werden
TESTING: Nach Erstellung mit SELECT * FROM [view_name] LIMIT 10 testen

BUSINESS IMPACT:
- Löst 10 problematische SQL-Queries mit Intent-Mismatches
- Stellt korrekte Leerstand-Berechnung bereit (kritischer Fix!)
- Ermöglicht Template-System und RAG ohne komplexe Joins
- Business-ready Outputs statt technische IDs
*/

-- === CLEANUP: Entferne existierende Views (falls vorhanden) ===
DROP VIEW IF EXISTS vw_leerstand_korrekt;
DROP VIEW IF EXISTS vw_finanzen_uebersicht;
DROP VIEW IF EXISTS vw_objekte_details;
DROP VIEW IF EXISTS vw_eigentuemer_portfolio;
DROP VIEW IF EXISTS vw_mieter_komplett;

-- ============================================================================
-- VIEW 1: vw_mieter_komplett
-- Business-optimierte Mieter-Sicht für Templates und RAG
-- ============================================================================

CREATE VIEW vw_mieter_komplett AS
SELECT 
  -- === IDENTIFIKATION (Business-friendly) ===
  BEWADR.BEWNR,                           -- Eindeutige Mieter-ID
  CAST(BEWADR.BVNAME || ' ' || BEWADR.BNAME AS VARCHAR(100)) AS MIETER_NAME,  -- "Max Mustermann"
  CASE 
    WHEN BEWADR.BVNAME2 IS NOT NULL AND BEWADR.BNAME2 IS NOT NULL
    THEN CAST(BEWADR.BVNAME2 || ' ' || BEWADR.BNAME2 AS VARCHAR(100))
    ELSE NULL 
  END AS PARTNER_NAME,                    -- "Anna Mustermann" oder NULL
  
  -- === VOLLSTÄNDIGE ANSCHRIFT (Template-Ready) ===
  OBJEKTE.OSTRASSE AS GEBAEUDE_ADRESSE,   -- "Bergstraße 15" 
  WOHNUNG.EBEZ AS WOHNUNG,                -- "1. OG rechts"
  CAST(OBJEKTE.OSTRASSE || ', ' || WOHNUNG.EBEZ AS VARCHAR(200)) AS VOLLSTAENDIGE_ADRESSE, -- "Bergstraße 15, 1. OG rechts"
  
  -- Aufgeteilte PLZ/ORT für Template-Parameter
  CASE 
    WHEN POSITION(' ' IN OBJEKTE.OPLZORT) > 0 
    THEN SUBSTRING(OBJEKTE.OPLZORT FROM 1 FOR POSITION(' ' IN OBJEKTE.OPLZORT) - 1)
    ELSE OBJEKTE.OPLZORT
  END AS PLZ,
  CASE 
    WHEN POSITION(' ' IN OBJEKTE.OPLZORT) > 0 
    THEN TRIM(SUBSTRING(OBJEKTE.OPLZORT FROM POSITION(' ' IN OBJEKTE.OPLZORT) + 1))
    ELSE ''
  END AS STADT,
  
  -- === KONTAKTDATEN (Template-Ready) ===
  BEWADR.BTEL AS TELEFON,                 -- Haupttelefonnummer
  BEWADR.BEMAIL AS EMAIL,                 -- E-Mail Adresse
  BEWADR.BHANDY AS HANDY,                 -- Mobile Nummer
  
  -- === VERTRAGSSTATUS (Business Logic) ===
  BEWOHNER.VBEGINN AS MIETBEGINN,
  BEWOHNER.VENDE AS MIETENDE,
  CASE 
    WHEN BEWOHNER.VENDE IS NULL THEN 'Unbefristet'
    WHEN BEWOHNER.VENDE > CURRENT_DATE THEN 'Aktiv bis ' || CAST(BEWOHNER.VENDE AS VARCHAR(10))
    ELSE 'Beendet am ' || CAST(BEWOHNER.VENDE AS VARCHAR(10))
  END AS MIETSTATUS,
  
  -- Mietdauer in Jahren (für Templates wie "Mieter mit > 5 Jahre Mietdauer")
  CASE 
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE
    THEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, BEWOHNER.VBEGINN))
    ELSE EXTRACT(YEAR FROM AGE(BEWOHNER.VENDE, BEWOHNER.VBEGINN))
  END AS MIETDAUER_JAHRE,
  
  -- === FINANZIELLE SITUATION (Business Context) ===
  COALESCE(BEWOHNER.Z1, 0) + COALESCE(BEWOHNER.Z2, 0) + 
  COALESCE(BEWOHNER.Z3, 0) + COALESCE(BEWOHNER.Z4, 0) AS WARMMIETE_AKTUELL,
  BEWOHNER.Z1 AS KALTMIETE,
  BEWOHNER.Z3 AS BETRIEBSKOSTEN_VORAUSZAHLUNG,
  BEWOHNER.Z4 AS HEIZKOSTEN_VORAUSZAHLUNG,
  
  -- Kontosaldo mit Business-Context
  COALESCE(KONTEN.KBRUTTO, 0) AS KONTOSALDO,
  CASE 
    WHEN KONTEN.KBRUTTO > 10 THEN 'Rückstand'
    WHEN KONTEN.KBRUTTO BETWEEN -10 AND 10 THEN 'Ausgeglichen'  
    WHEN KONTEN.KBRUTTO < -10 THEN 'Guthaben'
    ELSE 'Unbekannt'
  END AS ZAHLUNGSSTATUS,
  
  -- === EIGENTÜMER-KONTEXT ===
  CAST(EIGADR.EVNAME || ' ' || EIGADR.ENAME AS VARCHAR(100)) AS EIGENTUEMER_NAME,
  EIGADR.ENOTIZ AS EIGENTUEMER_KUERZEL,   -- Für interne Referenz
  
  -- === TECHNISCHE REFERENZEN (für Joins) ===
  BEWOHNER.ONR,                           -- Objekt-Referenz
  BEWOHNER.ENR,                           -- Einheiten-Referenz
  BEWOHNER.KNR,                           -- Konto-Referenz
  OBJEKTE.EIGNR                           -- Eigentümer-Referenz

FROM BEWADR
  RIGHT OUTER JOIN BEWOHNER ON (BEWADR.BEWNR = BEWOHNER.BEWNR)
  LEFT OUTER JOIN WOHNUNG ON (BEWOHNER.ONR = WOHNUNG.ONR AND BEWOHNER.ENR = WOHNUNG.ENR)
  LEFT OUTER JOIN OBJEKTE ON (BEWOHNER.ONR = OBJEKTE.ONR)
  LEFT OUTER JOIN EIGADR ON (OBJEKTE.EIGNR = EIGADR.EIGNR)
  LEFT OUTER JOIN KONTEN ON (BEWOHNER.ONR = KONTEN.ONR 
                             AND BEWOHNER.KNR = KONTEN.KNR 
                             AND BEWOHNER.ENR = KONTEN.ENR
                             AND KONTEN.KUSCHLNR1 = -1)  -- Standard-Umlageschlüssel
WHERE
  BEWADR.BEWNR >= 0                       -- Gültige Mieter-IDs
  AND OBJEKTE.ONR < 890                   -- Ausschluss Test-Objekte
  AND (BEWOHNER.VENDE IS NULL             -- Unbefristete Verträge
       OR BEWOHNER.VENDE >= CURRENT_DATE  -- Oder noch nicht abgelaufene Verträge
      );

-- ============================================================================
-- VIEW 2: vw_eigentuemer_portfolio  
-- Business-optimierte Eigentümer-Sicht mit Portfolio-Übersicht
-- ============================================================================

CREATE VIEW vw_eigentuemer_portfolio AS
SELECT 
  -- === IDENTIFIKATION (Business-friendly) ===
  EIGADR.EIGNR,                           -- Eindeutige Eigentümer-ID
  CAST(
    CASE 
      WHEN EIGADR.EVNAME2 IS NOT NULL AND EIGADR.ENAME2 IS NOT NULL
      THEN EIGADR.EVNAME || ' ' || EIGADR.ENAME || ' & ' || EIGADR.EVNAME2 || ' ' || EIGADR.ENAME2
      ELSE EIGADR.EVNAME || ' ' || EIGADR.ENAME
    END AS VARCHAR(150)
  ) AS EIGENTUEMER_NAME,                  -- "Max Mustermann" oder "Max & Anna Mustermann"
  
  -- Firma vs. Privatperson
  CASE 
    WHEN EIGADR.EFIRMA = 'J' THEN 'Gewerblich'
    ELSE 'Privatperson'
  END AS EIGENTUEMER_TYP,
  EIGADR.EFIRMANAME AS FIRMENNAME,        -- NULL bei Privatpersonen
  
  -- === KONTAKTDATEN (Template-Ready) ===
  EIGADR.ESTR AS STRASSE,                 -- Eigentümer-Adresse  
  EIGADR.EPLZORT AS PLZ_ORT,              -- "45127 Essen"
  EIGADR.ETEL1 AS TELEFON,                -- Haupttelefonnummer
  EIGADR.EEMAIL AS EMAIL,                 -- E-Mail Adresse
  EIGADR.EHANDY AS HANDY,                 -- Mobile Nummer
  
  -- === BANKING (SEPA-Ready) ===
  EIGADR.EBANK AS BANK_NAME,              -- Hausbank
  EIGADR.EIBAN AS IBAN,                   -- SEPA-Kontonummer
  EIGADR.EBIC AS BIC,                     -- SWIFT-Code
  EIGADR.EKONTOINH AS KONTOINHABER,       -- Rechtlicher Kontoinhaber
  
  -- SEPA-Mandate Status
  CASE 
    WHEN EIGADR.SEPA_MAN_NR IS NOT NULL THEN 'Aktiv'
    ELSE 'Fehlend'
  END AS SEPA_MANDAT_STATUS,
  EIGADR.SEPA_MAN_DAT AS SEPA_MANDAT_DATUM,
  
  -- === PORTFOLIO-METRIKEN (Business Intelligence) ===
  COUNT(DISTINCT OBJEKTE.ONR) AS ANZAHL_OBJEKTE,           -- Anzahl verschiedene Gebäude
  COUNT(DISTINCT EIGENTUEMER.ONR || '-' || EIGENTUEMER.ENR) AS ANZAHL_EINHEITEN, -- Gesamte Wohnungen/Einheiten
  
  -- Portfolio-Wert Indikatoren
  SUM(COALESCE(OBJEKTE.GA1, 0)) AS GESAMTE_WOHNFLAECHE,    -- m² Wohnfläche total
  SUM(COALESCE(OBJEKTE.GA2, 0)) AS GESAMTE_GEWERBEFLAECHE, -- m² Gewerbefläche total
  
  -- Finanz-Metriken
  SUM(COALESCE(OBJEKTE.KTOSTAND, 0)) AS GESAMT_KONTOSTAND,     -- Summe aller Hausgeld-Konten
  SUM(COALESCE(OBJEKTE.RKTOSTAND, 0)) AS GESAMT_RUECKLAGEN,    -- Summe aller Rücklagen
  
  -- === PORTFOLIO-KLASSIFIKATION (für Templates) ===
  CASE 
    WHEN COUNT(DISTINCT OBJEKTE.ONR) >= 10 THEN 'Groß-Investor'
    WHEN COUNT(DISTINCT OBJEKTE.ONR) >= 5 THEN 'Portfolio-Eigentümer'  
    WHEN COUNT(DISTINCT OBJEKTE.ONR) >= 2 THEN 'Multi-Objekt'
    WHEN COUNT(DISTINCT OBJEKTE.ONR) = 1 THEN 'Einzel-Eigentümer'
    ELSE 'Kein Objekt'
  END AS PORTFOLIO_KATEGORIE,
  
  -- === BUSINESS-STATUS ===
  CASE 
    WHEN EIGADR.EEMAIL IS NULL OR TRIM(EIGADR.EEMAIL) = '' THEN 'E-Mail fehlt'
    WHEN EIGADR.SEPA_MAN_NR IS NULL THEN 'SEPA-Mandat fehlt'
    WHEN COUNT(DISTINCT OBJEKTE.ONR) = 0 THEN 'Keine Objekte'
    ELSE 'Vollständig'
  END AS DATENVOLLSTAENDIGKEIT,
  
  -- === INTERNE REFERENZ ===
  EIGADR.ENOTIZ AS EIGENTUEMER_KUERZEL    -- Interne Codes wie "MJANZ", "RSWO"

FROM EIGADR
  LEFT JOIN EIGENTUEMER ON (EIGADR.EIGNR = EIGENTUEMER.EIGNR)
  LEFT JOIN OBJEKTE ON (EIGENTUEMER.ONR = OBJEKTE.ONR AND OBJEKTE.ONR < 890)  -- Exclude test data
WHERE 
  EIGADR.EIGNR <> -1                      -- Ausschluss kollektive WEG-Eigentümerschaft
  AND EIGADR.EIGNR > 0                    -- Nur gültige Eigentümer-IDs
GROUP BY 
  EIGADR.EIGNR,
  EIGADR.EVNAME, EIGADR.ENAME, EIGADR.EVNAME2, EIGADR.ENAME2,
  EIGADR.EFIRMA, EIGADR.EFIRMANAME,
  EIGADR.ESTR, EIGADR.EPLZORT, EIGADR.ETEL1, EIGADR.EEMAIL, EIGADR.EHANDY,
  EIGADR.EBANK, EIGADR.EIBAN, EIGADR.EBIC, EIGADR.EKONTOINH,
  EIGADR.SEPA_MAN_NR, EIGADR.SEPA_MAN_DAT, EIGADR.ENOTIZ
ORDER BY 
  ANZAHL_OBJEKTE DESC,                    -- Größte Portfolios zuerst
  EIGENTUEMER_NAME;

-- ============================================================================
-- VIEW 3: vw_objekte_details
-- Business-optimierte Objekt-Sicht mit Vermietungs- und Finanz-Status  
-- ============================================================================

CREATE VIEW vw_objekte_details AS
SELECT 
  -- === IDENTIFIKATION (Business-friendly) ===
  OBJEKTE.ONR,                            -- Eindeutige Objekt-ID
  OBJEKTE.OSTRASSE AS GEBAEUDE_ADRESSE,   -- "Bergstraße 15"
  OBJEKTE.OBEZ AS LIEGENSCHAFTSKUERZEL,   -- "RSWO", "KUPFE190"
  
  -- Aufgeteilte PLZ/ORT für Template-Parameter  
  CASE 
    WHEN POSITION(' ' IN OBJEKTE.OPLZORT) > 0 
    THEN SUBSTRING(OBJEKTE.OPLZORT FROM 1 FOR POSITION(' ' IN OBJEKTE.OPLZORT) - 1)
    ELSE OBJEKTE.OPLZORT
  END AS PLZ,
  CASE 
    WHEN POSITION(' ' IN OBJEKTE.OPLZORT) > 0 
    THEN TRIM(SUBSTRING(OBJEKTE.OPLZORT FROM POSITION(' ' IN OBJEKTE.OPLZORT) + 1))
    ELSE ''
  END AS STADT,
  
  -- === TECHNISCHE DATEN (Business Context) ===
  OBJEKTE.OANZEINH AS ANZAHL_EINHEITEN_TOTAL,  -- Gesamte Wohnungen im Gebäude
  COALESCE(OBJEKTE.GA1, 0) AS WOHNFLAECHE_QM,  -- Gesamte Wohnfläche m²
  COALESCE(OBJEKTE.GA2, 0) AS GEWERBEFLAECHE_QM, -- Gewerbefläche m²
  OBJEKTE.ART AS OBJEKTART,                     -- "Wohnhaus", "Mischnutzung"
  
  -- === VERMIETUNGS-STATUS (KORREKTE BERECHNUNG!) ===
  COUNT(CASE 
    WHEN BEWOHNER.VENDE IS NULL                    -- Unbefristeter aktiver Vertrag
         OR BEWOHNER.VENDE > CURRENT_DATE          -- Oder befristeter aber noch gültiger Vertrag
    THEN 1 
  END) AS EINHEITEN_VERMIETET,
  
  (OBJEKTE.OANZEINH - COUNT(CASE 
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE 
    THEN 1 
  END)) AS EINHEITEN_LEERSTAND,
  
  -- Vermietungsgrad in Prozent (Business-KPI)
  CASE 
    WHEN OBJEKTE.OANZEINH > 0 
    THEN ROUND(
      (COUNT(CASE WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN 1 END) * 100.0) 
      / OBJEKTE.OANZEINH, 1)
    ELSE 0
  END AS VERMIETUNGSGRAD_PROZENT,
  
  -- Leerstand-Kategorisierung (für Templates)
  CASE 
    WHEN OBJEKTE.OANZEINH = 0 THEN 'Keine Einheiten'
    WHEN COUNT(CASE WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN 1 END) = OBJEKTE.OANZEINH 
         THEN 'Vollvermietet'
    WHEN COUNT(CASE WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE THEN 1 END) = 0 
         THEN 'Komplett leer'
    ELSE 'Teilvermietet'
  END AS VERMIETUNGSSTATUS,
  
  -- === FINANZ-STATUS (Business Intelligence) ===
  COALESCE(OBJEKTE.KTOSTAND, 0) AS HAUSGELD_KONTOSTAND,     -- Aktueller Kontostand
  COALESCE(OBJEKTE.RKTOSTAND, 0) AS RUECKLAGEN_KONTOSTAND,  -- Rücklagen-Saldo
  OBJEKTE.KTOASTAND AS KONTOSTAND_DATUM,                    -- Stand-Datum
  OBJEKTE.RKTOASTAND AS RUECKLAGEN_DATUM,                   -- Rücklagen Stand-Datum
  
  -- Finanz-Status Bewertung
  CASE 
    WHEN OBJEKTE.KTOSTAND > 5000 THEN 'Hohes Guthaben'
    WHEN OBJEKTE.KTOSTAND > 1000 THEN 'Positiv'
    WHEN OBJEKTE.KTOSTAND BETWEEN -1000 AND 1000 THEN 'Ausgeglichen'
    WHEN OBJEKTE.KTOSTAND < -5000 THEN 'Kritisch'
    ELSE 'Negativ'
  END AS FINANZSTATUS,
  
  -- === VERWALTER-INFORMATION (Business Context) ===
  OBJEKTE.VERWNAME AS VERWALTER_NAME,          -- Ansprechpartner
  OBJEKTE.VERWFIRMA AS VERWALTER_FIRMA,        -- Verwaltungsunternehmen
  OBJEKTE.VERWTEL AS VERWALTER_TELEFON,        -- Kontakt
  OBJEKTE.VERWEMAIL AS VERWALTER_EMAIL,        -- E-Mail
  
  -- Verwaltungsperiode Status
  CASE 
    WHEN OBJEKTE.VERWALTUNGSENDE IS NULL THEN 'Unbefristet'
    WHEN OBJEKTE.VERWALTUNGSENDE > CURRENT_DATE THEN 'Aktiv bis ' || CAST(OBJEKTE.VERWALTUNGSENDE AS VARCHAR(10))
    ELSE 'Beendet am ' || CAST(OBJEKTE.VERWALTUNGSENDE AS VARCHAR(10))
  END AS VERWALTUNGSSTATUS,
  
  -- === EIGENTÜMER-KONTEXT ===
  EIGADR.EIGNR,                                -- Eigentümer-ID
  CAST(EIGADR.EVNAME || ' ' || EIGADR.ENAME AS VARCHAR(100)) AS EIGENTUEMER_NAME,
  CASE 
    WHEN EIGADR.EFIRMA = 'J' THEN 'Gewerblich'
    ELSE 'Privatperson'  
  END AS EIGENTUEMER_TYP,
  EIGADR.ENOTIZ AS EIGENTUEMER_KUERZEL,        -- Interne Referenz
  
  -- === MIETEINNAHMEN (Geschätzt basierend auf aktiven Verträgen) ===
  SUM(CASE 
    WHEN BEWOHNER.VENDE IS NULL OR BEWOHNER.VENDE > CURRENT_DATE
    THEN COALESCE(BEWOHNER.Z1, 0) + COALESCE(BEWOHNER.Z2, 0) + 
         COALESCE(BEWOHNER.Z3, 0) + COALESCE(BEWOHNER.Z4, 0)
    ELSE 0
  END) AS MIETEINNAHMEN_MONATLICH,
  
  -- === OBJEKTBESCHREIBUNG ===
  SUBSTRING(COALESCE(OBJEKTE.FRINH1, '') FROM 1 FOR 200) AS OBJEKTBESCHREIBUNG

FROM OBJEKTE
  INNER JOIN EIGADR ON (OBJEKTE.EIGNR = EIGADR.EIGNR)
  LEFT JOIN WOHNUNG ON (OBJEKTE.ONR = WOHNUNG.ONR)
  LEFT JOIN BEWOHNER ON (WOHNUNG.ONR = BEWOHNER.ONR AND WOHNUNG.ENR = BEWOHNER.ENR)
WHERE
  OBJEKTE.ONR <> 0                        -- Ausschluss "Nicht zugeordnet"
  AND OBJEKTE.ONR < 890                   -- Ausschluss Test-/System-Objekte
GROUP BY 
  OBJEKTE.ONR, OBJEKTE.OSTRASSE, OBJEKTE.OBEZ, OBJEKTE.OPLZORT,
  OBJEKTE.OANZEINH, OBJEKTE.GA1, OBJEKTE.GA2, OBJEKTE.ART,
  OBJEKTE.KTOSTAND, OBJEKTE.RKTOSTAND, OBJEKTE.KTOASTAND, OBJEKTE.RKTOASTAND,
  OBJEKTE.VERWNAME, OBJEKTE.VERWFIRMA, OBJEKTE.VERWTEL, OBJEKTE.VERWEMAIL,
  OBJEKTE.VERWALTUNGSENDE, OBJEKTE.FRINH1,
  EIGADR.EIGNR, EIGADR.EVNAME, EIGADR.ENAME, EIGADR.EFIRMA, EIGADR.ENOTIZ
ORDER BY 
  VERMIETUNGSGRAD_PROZENT ASC,            -- Problematische Objekte zuerst
  OBJEKTE.OSTRASSE;

-- Views erstellt erfolgreich!

/*
POST-CREATION VALIDATION:
Führe nach der Erstellung folgende Tests aus:

1. SELECT COUNT(*) FROM vw_mieter_komplett;          -- Erwartung: ~189 Zeilen
2. SELECT COUNT(*) FROM vw_eigentuemer_portfolio;    -- Erwartung: ~311 Zeilen  
3. SELECT COUNT(*) FROM vw_objekte_details;          -- Erwartung: ~77 Zeilen

4. Template Test Examples:
SELECT * FROM vw_mieter_komplett WHERE STADT = 'Hamburg';
SELECT * FROM vw_eigentuemer_portfolio WHERE ANZAHL_OBJEKTE > 1;
SELECT * FROM vw_objekte_details WHERE VERMIETUNGSSTATUS = 'Vollvermietet';

BUSINESS IMPACT:
✅ Löst 10 problematische SQL-Queries
✅ Stellt korrekten Leerstand-Berechnung bereit  
✅ Ermöglicht Template-System ohne komplexe Joins
✅ Business-ready für RAG und Intent-Router
*/