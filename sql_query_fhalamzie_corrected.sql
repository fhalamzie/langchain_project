-- Korrigierte SQL-Abfrage für Kaltmieten von FHALAMZIE
-- Basierend auf verifizierten Feld-Mappings aus 02_mieter.sql

-- Mapping-Übersicht:
-- KALTMIETE = BEWOHNER.Z1
-- EIGENTUEMERKUERZEL = EIGADR.ENOTIZ  
-- VERTRAGSSTATUS: Aktiv wenn VENDE IS NULL OR VENDE >= CURRENT_DATE

SELECT 
    SUM(COALESCE(B.Z1, 0)) AS Kaltmiete_Monatlich,
    COUNT(*) AS Anzahl_Mieter
FROM 
    EIGADR E
    JOIN OBJEKTE O ON E.EIGNR = O.EIGNR
    JOIN BEWOHNER B ON O.ONR = B.ONR
WHERE 
    E.ENOTIZ = 'FHALAMZIE'  -- EIGENTUEMERKUERZEL
    AND (B.VENDE IS NULL OR B.VENDE >= CURRENT_DATE);  -- Nur aktive Verträge

-- Alternative mit ENAME statt ENOTIZ, falls ENOTIZ nicht gefüllt ist:
/*
SELECT 
    SUM(COALESCE(B.Z1, 0)) AS Kaltmiete_Monatlich,
    COUNT(*) AS Anzahl_Mieter
FROM 
    EIGADR E
    JOIN OBJEKTE O ON E.EIGNR = O.EIGNR
    JOIN BEWOHNER B ON O.ONR = B.ONR
WHERE 
    E.ENAME = 'FHALAMZIE'
    AND (B.VENDE IS NULL OR B.VENDE >= CURRENT_DATE);
*/

-- Erwartetes Ergebnis basierend auf JSON-Verifikation:
-- Kaltmiete_Monatlich: 9891.67 EUR
-- Anzahl_Mieter: 23