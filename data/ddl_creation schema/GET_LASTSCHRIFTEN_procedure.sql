-- Prozedur: GET_LASTSCHRIFTEN
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE GET_LASTSCHRIFTEN
DECLARE VARIABLE IANZ INTEGER;
DECLARE VARIABLE BANKID INTEGER;
DECLARE VARIABLE ISZNR INTEGER;
DECLARE VARIABLE ENR INTEGER;
DECLARE VARIABLE IEIGNR INTEGER;
DECLARE VARIABLE NAME VARCHAR(80);
DECLARE VARIABLE MWSTAUSW CHAR(1);
DECLARE VARIABLE LASTJA CHAR(1);
DECLARE VARIABLE BETRAG1 NUMERIC(15, 12);
DECLARE VARIABLE BUDATUM DATE;
DECLARE VARIABLE SEVSEPA_CI VARCHAR(35);
DECLARE VARIABLE SEPA_CI2 VARCHAR(35);
DECLARE VARIABLE IOBJART SMALLINT;
BEGIN
/*
 L_DATUM='21.10.2019';
 A_BLZ = '';
 A_KONTO = '8';
 IS_DTA = 'J';  */

 IF (A_BLZ<>'') THEN     /* PRO BLZ */
  FOR
   SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, TEXT, BNR, LASTBANK, LBNR, OPBetrag, Betrag, SPLITNR, LastErzeugt, sepa_ci, sepa_ci2, bsonst from buchung, objekte
   WHERE onrsoll=onr and (ARTSOLL=60 or ARTSOLL=62) and OPBETRAG>0.001 and LBNR IS NULL and SPLITNR IS NULL and LASTBANK IN (SELECT BANKEN.NR FROM BANKEN 
   WHERE ((BANKEN.BLZ=:A_BLZ) or (BANKEN.BIC=:A_BLZ)) AND BANKEN.ART=0)
   UNION
   SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, TEXT, splitbuch.BNR, LASTBANK, LBNR, splitbuch.OPBetrag, splitbuch.Betrag, SPLITNR, LastErzeugt, sepa_ci, sepa_ci2, bsonst
   from buchung, splitbuch, objekte WHERE onrsoll=onr and (ARTSOLL=60 or ARTSOLL=62) and splitbuch.OPBETRAG>0.001 and LBNR IS NULL and LASTBANK IN 
   (SELECT BANKEN.NR FROM BANKEN  WHERE ((BANKEN.BLZ=:A_BLZ) or (BANKEN.BIC=:A_BLZ)) AND BANKEN.ART=0) and SPLITNR IS  NOT NULL AND buchung.bnr=splitbuch.bnr
   order by 7, 1, 3
  INTO :BUDATUM, :ONR, KHABEN, :KSTRHABEN, :VZWECK1, :BNR, :BANKNR, :LBNR, :BETRAG, :BETRAG1, :SPLITNR, :LASTERZEUGT, :SEPA_CI, :SEPA_CI2, :IOBJART
  DO
   BEGIN
    DATUM=:BUDATUM; B2B = 5;
    AGEBER  = ''; AGEBERBANK  = ''; AGEBERKONTO  = ''; AGEBERBLZ  = ''; EMPF  = ''; EMPFBANK  = ''; EMPFKONTO  = '';
    EMPFBLZ  = ''; AGEBERSTR  = ''; AGEBERPLZORT  = ''; EMPFSTR  = ''; EMPFPLZORT  = ''; AGEBERBIC  = ''; AGEBERIBAN  = ''; EMPFBIC  = ''; EMPFIBAN  = '';
    SEPA_MAN_NR  = '';
    IF (LASTERZEUGT IS NULL) THEN
     LASTERZEUGT=0;
    IF (KHABEN < 200000) THEN
     BEGIN   /* Bewohner */
      SELECT ba.BBANK, ba.BBLZ, ba.BKONTO, ba.BKONTOINH, ba.BNAME, BMWSTAUSW, BMWSTSATZ, BLASTJA, ba.BSTR, ba.BPLZORT, ba.BBIC, ba.BIBAN, SEPA_MAN_DAT,
      SEPA_MAN_NR,SEPA_LS_TEXTSCHL from bewohner b, bewadr ba WHERE b.bewnr=ba.bewnr and ONR=:ONR AND KNR=:KHABEN
      INTO :EmpfBank, :EmpfBLZ, :EmpfKonto, :Empf, :NAME, :MWSTAUSW, MWSTSATZ, :LASTJA, :EmpfStr, :EmpfPLZOrt,:EMPFBIC,:EMPFIBAN,:SEPA_MAN_DAT,:SEPA_MAN_NR,:B2B;
      /* */
      IF (EMPF='') THEN
       EMPF=SUBSTRING(:NAME from 1 for 50);
      IF (MWSTAUSW='N') THEN
       MWSTSATZ=-1;
      /* SEV */ 
      SEVSEPA_CI='';
      select sepa_ci from severtrag where onr=:onr and sevknr=(:KHABEN+200000) into :SEVSEPA_CI;
      IF (SEVSEPA_CI IS NULL) THEN
       SEVSEPA_CI='';
      IF (SEVSEPA_CI<>'') THEN
       SEPA_CI=SEVSEPA_CI; 
     END     /* Bewohner */
    ELSE
     BEGIN  /* EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer */
      IF (IOBJART=2) THEN
       BEGIN
        IF ((SEPA_CI2 <> '') and (SEPA_CI2 IS NOT NULL)) THEN
         SEPA_CI = SEPA_CI2;
       END
      /*  */
      SELECT EIGNR, EMWSTAUSW, EMWSTSATZ, ELASTJA, SEPA_MAN_DAT, SEPA_MAN_NR,SEPA_LS_TEXTSCHL, BANKID from eigentuemer WHERE ONR=:ONR AND KNR=:KHABEN
      INTO :IEIGNR, :MWSTAUSW, MWSTSATZ, :LASTJA, :SEPA_MAN_DAT, :SEPA_MAN_NR, :B2B, :BANKID;
      /* */
      IF (MWSTAUSW='N') THEN
       MWSTSATZ=-1;
      IF ((LASTJA='J') AND ((IEIGNR IS NOT NULL) AND (BANKID IS NOT NULL))) THEN
       BEGIN
        SELECT eb.BANK, eb.BLZ, eb.KONTO, eb.KONTOINH, eb.BIC, eb.IBAN, ea.ENAME, ea.ESTR, ea.EPLZORT from eigbanken eb, eigadr ea WHERE eb.ID=:BANKID and ea.EIGNR=:IEIGNR
        INTO :EmpfBank, :EmpfBLZ, :EmpfKonto, :Empf, :EMPFBIC, :EMPFIBAN, :NAME, :EmpfStr, :EmpfPLZOrt;
        IF (EMPF='') THEN
         EMPF=SUBSTRING(:NAME from 1 for 50);
       END
     END    /* EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer */
    IF (LASTJA='J') THEN
     BEGIN
      SELECT Bezeichnung, BLZ, Inhaber, Konto, Str, PLZOrt, bic, iban from banken WHERE NR=:BANKNR
      INTO :AGEBERBANK, :AGEBERBLZ, :AGEBER, :AGEBERKONTO, :AGEBERSTR, :AGEBERPLZORT, :AGEBERBIC, :AGEBERIBAN;
      /*           */
      IF ((IS_DTA='N') OR (IS_DTA='J' and :LASTERZEUGT<>1)) THEN
       begin
        SUSPEND;
       end  
     END
   END
 ELSE
  BEGIN
   /* PRO KONTO */
   /*           */
   FOR
    with cteA
    as
    (
    SELECT b.ONRSOLL, b.KSOLL, b.KSTRSOLL, b.TEXT, b.BNR, b.LASTBANK,
    CASE WHEN b.LBNR IS NULL 
    then NULL
    else b.LBNR
    end as LBNR,
    b.OPBetrag, b.Betrag, b.Datum,
    CASE WHEN b.SPLITNR IS NULL 
    then NULL
    else b.SPLITNR
    end as SPLITNR,
    b.LastErzeugt, o.sepa_ci, o.sepa_ci2, o.bsonst
    FROM buchung b, objekte o
    WHERE b.onrsoll = o.onr 
    AND (b.ARTSOLL = 60 OR b.ARTSOLL = 62)
    AND b.OPBETRAG > 0.001
    AND (b.LASTBANK = :A_KONTO OR :A_KONTO = -1)
    ),

    cteB
    as
    (
    SELECT b.ONRSOLL, b.KSOLL, b.KSTRSOLL, b.TEXT, s.BNR, b.LASTBANK,
    CASE WHEN b.LBNR IS NULL 
    then NULL
    else b.LBNR
    end as LBNR,
    s.OPBetrag, s.Betrag, b.Datum,
    CASE WHEN b.SPLITNR IS NULL 
    then NULL
    else b.SPLITNR
    end as SPLITNR,
    b.LastErzeugt, o.sepa_ci, o.sepa_ci2, o.bsonst
    FROM buchung b, splitbuch s, objekte o
    WHERE b.onrsoll = o.onr
    AND (b.ARTSOLL = 60 OR b.ARTSOLL = 62)
    AND s.OPBETRAG > 0.001
    AND (b.LASTBANK = :A_KONTO OR :A_KONTO = -1)
    AND b.bnr = s.bnr
    ),

    cteL
    AS
    (
    select a.ONRSOLL, a.KSOLL, a.KSTRSOLL, a.TEXT, a.BNR, a.LASTBANK, a.LBNR, a.OPBetrag, a.Betrag, a.Datum, a.SPLITNR, a.LastErzeugt, a.sepa_ci, a.sepa_ci2, a.bsonst 
    from cteA a 
    where a.SPLITNR IS NULL
    and a.LBNR IS NULL
    UNION
    select b.ONRSOLL, b.KSOLL, b.KSTRSOLL, b.TEXT, b.BNR, b.LASTBANK, b.LBNR, b.OPBetrag, b.Betrag, b.Datum, b.SPLITNR, b.LastErzeugt, b.sepa_ci, b.sepa_ci2, b.bsonst 
    from cteB b
    where b.SPLITNR IS NOT NULL
    and b.LBNR IS NULL
    )
    select q.ONRSOLL, q.KSOLL, q.KSTRSOLL, q.TEXT, q.BNR, q.LASTBANK, q.LBNR, q.OPBetrag, q.Betrag, q.Datum, q.SPLITNR, q.LastErzeugt, q.sepa_ci, q.sepa_ci2, q.bsonst 
    from cteL q
    order by 10, 1, 2
   INTO :ONR, :KHABEN, :KSTRHABEN, :VZWECK1, :BNR, :BANKNR, :LBNR, :BETRAG, :BETRAG1, :BUDATUM, :SPLITNR, :LASTERZEUGT, :SEPA_CI, :SEPA_CI2, :IOBJART
   DO
    BEGIN
     DATUM=:BUDATUM; B2B = 5;
     AGEBERBANK  = ''; AGEBERKONTO  = ''; AGEBERBLZ  = ''; EMPF  = ''; EMPFBANK  = ''; EMPFKONTO  = '';
     EMPFBLZ  = ''; AGEBERSTR  = ''; AGEBERPLZORT  = ''; EMPFSTR  = ''; EMPFPLZORT  = ''; AGEBERBIC  = ''; AGEBERIBAN  = ''; EMPFBIC  = ''; EMPFIBAN  = '';
     SEPA_MAN_NR  = '';    
     IF (LASTERZEUGT IS NULL) THEN
      LASTERZEUGT=0;
     IF (KHABEN < 200000) THEN
      BEGIN   /* Bewohner */
       SELECT ba.BBANK, ba.BBLZ, ba.BKONTO, ba.BKONTOINH, ba.BNAME, BMWSTAUSW, BMWSTSATZ, BLASTJA, ba.BSTR, ba.BPLZORT, ba.BBIC, ba.BIBAN, SEPA_MAN_DAT, 
       SEPA_MAN_NR,SEPA_LS_TEXTSCHL from bewohner b, bewadr ba WHERE b.bewnr=ba.bewnr and ONR=:ONR AND KNR=:KHABEN
       INTO :EmpfBank, :EmpfBLZ, :EmpfKonto, :Empf, :NAME, :MWSTAUSW, MWSTSATZ, :LASTJA, :EmpfStr, :EmpfPLZOrt, :EMPFBIC, :EMPFIBAN, :SEPA_MAN_DAT, :SEPA_MAN_NR, :B2B;
       /*  */
       IF (EMPF='') THEN
        EMPF=SUBSTRING(:NAME from 1 for 50);
       IF (MWSTAUSW='N') THEN
        MWSTSATZ=-1;
       /* SEV */ 
       SEVSEPA_CI='';
       select sepa_ci from severtrag where onr=:onr and sevknr=(:KHABEN+200000) into :SEVSEPA_CI;
       IF (SEVSEPA_CI IS NULL) THEN
        SEVSEPA_CI='';
       IF (SEVSEPA_CI<>'') THEN
        SEPA_CI=SEVSEPA_CI; 
      END     /* Bewohner */
     ELSE
      BEGIN  /* EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer */
       IF (IOBJART=2) THEN
        BEGIN
         IF ((SEPA_CI2 <> '') and (SEPA_CI2 IS NOT NULL)) THEN
          SEPA_CI = SEPA_CI2;
        END
       /*  */
       SELECT EIGNR, EMWSTAUSW, EMWSTSATZ, ELASTJA, SEPA_MAN_DAT, SEPA_MAN_NR, SEPA_LS_TEXTSCHL, BANKID from eigentuemer WHERE ONR=:ONR AND KNR=:KHABEN
       INTO :IEIGNR, :MWSTAUSW, MWSTSATZ, :LASTJA, :SEPA_MAN_DAT, :SEPA_MAN_NR, :B2B, :BANKID;
       /* */
       IF (MWSTAUSW='N') THEN
        MWSTSATZ=-1;
       IF ((LASTJA='J') AND ((IEIGNR IS NOT NULL) AND (BANKID IS NOT NULL))) THEN
        BEGIN
         SELECT eb.BANK, eb.BLZ, eb.KONTO, eb.KONTOINH, eb.BIC, eb.IBAN, ea.ENAME, ea.ESTR, ea.EPLZORT from eigbanken eb, eigadr ea WHERE eb.ID=:BANKID and ea.EIGNR=:IEIGNR
         INTO :EmpfBank, :EmpfBLZ, :EmpfKonto, :Empf, :EMPFBIC, :EMPFIBAN, :NAME, :EmpfStr, :EmpfPLZOrt;
         IF (EMPF='') THEN
          EMPF=SUBSTRING(:NAME from 1 for 50);
        END
      END    /* EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer */
     IF (LASTJA='J') THEN
      BEGIN
       SELECT Bezeichnung, BLZ, Inhaber, Konto, Str, PLZOrt, bic, iban from banken WHERE NR=:BANKNR
       INTO :AGEBERBANK, :AGEBERBLZ, :AGEBER, :AGEBERKONTO, :AGEBERSTR, :AGEBERPLZORT, :AGEBERBIC, :AGEBERIBAN;
       /*           */
       IF ((IS_DTA='N') OR (IS_DTA='J' and :LASTERZEUGT<>1)) THEN
        begin
         SUSPEND;
        end   
      END
    END
  END /* PRO KONTO */
END
