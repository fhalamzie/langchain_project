-- Prozedur: KONTOSTAENDE_AKTUALISIERENOBJ
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE KONTOSTAENDE_AKTUALISIERENOBJ
declare variable INR Integer;
declare variable IONR Integer;
declare variable SUMSOLL NUMERIC (15,2);
declare variable SUMHABEN NUMERIC (15,2);
declare variable KSTAND NUMERIC (15,2);
declare variable IKNR Integer;
declare variable IKKLASSE Integer;
declare variable DVON DATE;
declare variable DBIS DATE;
BEGIN
/* Kontostand aktualisieren */
For Select ONR, KNR, KKLASSE from konten where ONR=:SOLLONR
INTO :IONR, :IKNR, :IKKLASSE
do
begin
 Select Sum(Betrag) from buchung
 where ONRSOLL=:IONR and KSOLL=:IKNR
 INTO :SUMSOLL;
 Select Sum(Betrag) from buchung
 where ONRHABEN=:IONR and KHABEN=:IKNR
 INTO :SUMHABEN;
 IF (SUMSOLL IS NULL) then
  SUMSOLL=0;
 IF (SUMHABEN IS NULL) then
  SUMHABEN=0;
 IF (IKKLASSE=27 OR IKKLASSE=71 OR (IKKLASSE>=10 and IKKLASSE<=19)) THEN
  KSTAND=SUMHABEN-SUMSOLL;
 ELSE
  KSTAND=SUMSOLL-SUMHABEN;
 Update konten set KBrutto=:KSTAND, KBRUTTOWJ=:KSTAND where ONR=:IONR and KNR=:IKNR;
end
/* Kontostand WS aktualisieren -> Sachkonten  BK-Zeitraum*/
For Select ONR, KNR, KKLASSE from konten where ONR=:SOLLONR and KKLASSE <= 19 and KKSTNR<>2
INTO :IONR, :IKNR, :IKKLASSE
do
begin
 Select BKVON, BKBIS from Objekte
 where ONR=:IONR
 INTO :DVON, :DBIS;
 Select Sum(Betrag) from buchung
 where ONRSOLL=:IONR and KSOLL=:IKNR and (Datum>=:DVON and Datum<=:DBIS)
 INTO SUMSOLL;
 IF (SUMSOLL IS NULL) then
  SUMSOLL=0;
 Select Sum(Betrag) from buchung
 where ONRHABEN=:IONR and KHABEN=:IKNR and (Datum>=:DVON and Datum<=:DBIS)
 INTO SUMHABEN;
 IF (SUMHABEN IS NULL) then
  SUMHABEN=0;
 IF (IKKLASSE=27 OR IKKLASSE=71 OR (IKKLASSE>=10 and IKKLASSE<=19)) THEN
  KSTAND=SUMHABEN-SUMSOLL;
 ELSE
  KSTAND=SUMSOLL-SUMHABEN;
 Update konten set KBruttoWJ=:KSTAND where ONR=:IONR and KNR=:IKNR;
end
/* Kontostand WS aktualisieren -> Sachkonten  HK-Zeitraum*/
For Select ONR, KNR, KKLASSE from konten where ONR=:SOLLONR and KKLASSE <= 19 and KKSTNR=2
INTO :IONR, :IKNR, :IKKLASSE
do
begin
 Select HKVON, HKBIS from Objekte
 where ONR=:IONR
 INTO :DVON, :DBIS;
 Select Sum(Betrag) from buchung
 where ONRSOLL=:IONR and KSOLL=:IKNR and (Datum>=:DVON and Datum<=:DBIS)
 INTO SUMSOLL;
 IF (SUMSOLL IS NULL) then
  SUMSOLL=0;
 Select Sum(Betrag) from buchung
 where ONRHABEN=:IONR and KHABEN=:IKNR and (Datum>=:DVON and Datum<=:DBIS)
 INTO SUMHABEN;
 IF (SUMHABEN IS NULL) then
  SUMHABEN=0;
 IF (IKKLASSE=27 OR IKKLASSE=71 OR (IKKLASSE>=10 and IKKLASSE<=19)) THEN
  KSTAND=SUMHABEN-SUMSOLL;
 ELSE
  KSTAND=SUMSOLL-SUMHABEN;
 Update konten set KBruttoWJ=:KSTAND where ONR=:IONR and KNR=:IKNR;
end
/* BANKEN */
for select sum(kbrutto), banknr from konten where banknr is not null group by banknr
into :KSTAND, :IKNR do
 begin
  update banken set KSTAND=:KSTAND where NR=:IKNR;
 end
END
