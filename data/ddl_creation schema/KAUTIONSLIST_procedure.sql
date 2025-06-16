-- Prozedur: KAUTIONSLIST
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE KAUTIONSLIST
DECLARE VARIABLE IAKTONR INTEGER;
DECLARE VARIABLE EINZUG DATE;
DECLARE VARIABLE BFIRMA VARCHAR(1);
DECLARE VARIABLE BFIRMANAME VARCHAR(80);
DECLARE VARIABLE BBRIEFAN VARCHAR(40);
DECLARE VARIABLE STR VARCHAR(161);
BEGIN
 IAKTONR=0;
 FOR
  select b.onr, knr, ba.bname || ' ' || ba.bvname, ba.btel, ba.bfax, ba.bemail, kaut_abgerechnet, kaut_bez_konto, kaut_bank, kaut_blz,
  kaut_konto, kaut_vereinbart, ba.bstr || ', ' || ba.bplzort, vende, bewstatus, kaut_bic, kaut_iban, ebez, sepa_format, 
  ba.bblz, ba.bkonto, ba.bbic, ba.biban, ba.bbank, vbeginn, BFirma, BFirmaName,ba.BBriefan 
  from bewohner b, bewadr ba, wohnung w, objekte o, status
  where b.bewnr=ba.bewnr and b.onr=w.onr and b.enr=w.enr and b.onr=o.onr and (b.onr>=:IONRVON AND b.onr<=:IONRBIS) and bsonst<>1
  order by b.onr, knr
 INTO
  :ONR, :KNR, :NAME, :TEL, :FAX, :EMAIL, :ABGERECHNET, :KONTOART,:BANK, :BLZ, :KONTO, :VEREINBART, :ANSCHRIFT, :AUSZUG, :BEWSTATUS, :BIC, :IBAN, :WHGBEZ, :SEPA, :BBLZ, :BKONTO, :BBIC, :BIBAN, :BBANK, :EINZUG, :BFirma, :BFirmaName,:BBriefan
 DO
  BEGIN
  
   if (bfirma = 'J') then
    begin
     if (BBriefAn = 'Sehr geehrte Damen und Herren') then
      Name = BFirmaName;
     else
      begin
       str = BFirmaName;
       if (NAME <> '') then
         str = str || '; ' || Trim(Name);
       Name = str;  
       end
    end 
 
  
   /* 0=Alle, 1=Abgerechnet, 2=Nicht abgerechnet */
   IF (IAKTONR <> ONR) THEN
    IAKTONR=ONR;
   /* */
   IF (AUSZUG < '01.01.1901') then
    AUSZUG = NULL;
   IF (EINZUG < '01.01.1901') then
    EINZUG = NULL;    
   IF (ABGERECHNET < '01.01.1901') then
    ABGERECHNET = NULL;
   IF (IABGERECHNET = 0 OR (IABGERECHNET = 1 AND ABGERECHNET IS NOT NULL)
    OR (IABGERECHNET = 2 AND ABGERECHNET IS NULL)) THEN
    BEGIN
     IF ((EINZUG IS NULL AND AUSZUG IS NULL) OR
     (EINZUG IS NULL AND AUSZUG >= DTVON) OR
     (EINZUG <= DTBIS AND AUSZUG IS NULL) OR
     ((AUSZUG>=DTVON AND AUSZUG<=DTBIS) OR (EINZUG>=DTVON AND EINZUG<=DTBIS))) THEN
      BEGIN
       EXECUTE PROCEDURE GET_KNRSTR(:KNR) RETURNING_VALUES :KNRSTR;
       SELECT Sum(Betrag) from BUCHKAUT WHERE ONR=:ONR and KNR=:KNR INTO :STAND;
       SELECT Sum(Betrag) from BUCHKAUT WHERE ONR=:ONR and KNR=:KNR and EINZAHLUNG='J' INTO :ERHALTEN;
       IF (ERHALTEN < VEREINBART) THEN
        OFFEN = ERHALTEN - VEREINBART;
       ELSE
        IF (ERHALTEN IS NULL) THEN
         OFFEN = -VEREINBART;
        ELSE
         OFFEN = NULL;
       /* */
       IF (NOT (ART_BEWSTATUS = 1 AND BEWSTATUS = 1)) THEN  /* Option Leerstand nicht anzeigen */
        SUSPEND;
      END
    END
  END
END
