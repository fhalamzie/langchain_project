-- Prozedur: BANKSALDO_ALT
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE BANKSALDO_ALT
declare variable BetragEin NUMERIC (15, 2);
declare variable BetragAus NUMERIC (15, 2);
BEGIN
 /* SOLL */
 SELECT SUM(BETRAG) from buchung
 WHERE BANKNRSOLL=:GKONTO
 AND Datum<:DTBIS
 INTO :BetragEin;
 /* HABEN */
 SELECT SUM(BETRAG) from buchung
 WHERE BANKNRHABEN=:GKONTO
 AND Datum<:DTBIS
 INTO :BetragAus;
 if (BetragEin IS Null) then
  BetragEin=0;
 if (BetragAus IS Null) then
  BetragAus=0;
 SALDO=BetragEin-BetragAus;
 SUSPEND;
END
