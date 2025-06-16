-- Prozedur: ZAHLUNGSUEBERSICHT
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE ZAHLUNGSUEBERSICHT
DECLARE VARIABLE datum DATE;
DECLARE VARIABLE betrag NUMERIC(15, 2);
DECLARE VARIABLE kklasse INTEGER;
DECLARE VARIABLE ksoll INTEGER;
DECLARE VARIABLE khaben INTEGER;
DECLARE VARIABLE banknrsoll INTEGER;
DECLARE VARIABLE banknrhaben INTEGER;
DECLARE VARIABLE splitnr INTEGER;
DECLARE VARIABLE banknr INTEGER;
DECLARE VARIABLE onrsoll INTEGER;
DECLARE VARIABLE onrhaben INTEGER;
DECLARE VARIABLE kstrsoll VARCHAR(15);
DECLARE VARIABLE kstrhaben VARCHAR(15);
DECLARE VARIABLE levbankstr VARCHAR(15);
DECLARE VARIABLE levbank2str VARCHAR(15);
DECLARE VARIABLE levbanknr INTEGER;
DECLARE VARIABLE levbank2nr INTEGER;
DECLARE VARIABLE sollvorhanden INTEGER;
DECLARE VARIABLE solldatum DATE;
DECLARE VARIABLE LBNR INTEGER;
DECLARE VARIABLE test VARCHAR(10);
DECLARE VARIABLE artsoll INTEGER;
BEGIN
 KONTO_=KONTO;
 SELECT NR, KURZBEZ FROM BANKEN WHERE NR IN (SELECT LEVBANKNR FROM OBJEKTE WHERE ONR=:ONR) INTO :LEVBANKNR, :LEVBANKSTR;
 SELECT NR, KURZBEZ FROM BANKEN WHERE NR IN (SELECT LEVBANKNR2 FROM OBJEKTE WHERE ONR=:ONR) INTO :LEVBANK2NR, :LEVBANK2STR;
 IF (BDATUM='N') THEN
  BEGIN /* NACH SOLL und dazugehÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶rige Zahlungen */
   /* Sollstellungen */
   FOR select OPNR, DATUM, BELEGNR, TEXT, MWST, SUM(BETRAG) as BETRAG, SUM(OPBETRAG) as OPBETRAG, SPLITNR from buchung
    where (onrsoll=:ONR or onrhaben=:ONR) and (ksoll=:KONTO or khaben=:KONTO) and ((betrag <> 0) or ((betrag=0) and (OPBETRAG<>0))) and opbetrag is not null AND (Datum >= :FROMDATUM and Datum <= :TODATUM)
    group by OPNR, DATUM, BELEGNR, TEXT, MWST, SPLITNR
    order by 1, 3
   into
    :OPNR, :DATUM, :BELEGNR, :TEXT, :MWST, :BETRAG, :OPBETRAG, :SPLITNR
   DO
    BEGIN
     DATUMS = DATUM;
     DATUMH = NULL;
     BETRAGS = BETRAG;
     BETRAGH = NULL;
     OPBETRAG = OPBETRAG;
     BNR = OPNR;
     SSORT = DATUM || '_' || OPNR || '_1_' || DATUM;
     BEMERKUNG = '';
     IF (OPBETRAG = 0) THEN
      BEGIN
       IF (SPLITNR IS NULL) THEN
        BEMERKUNG = 'SO';
       ELSE
        BEMERKUNG = 'SO..';
      END
     ELSE
      BEGIN
       IF (SPLITNR IS NULL) THEN
        BEMERKUNG = 'OP';
       ELSE
        BEMERKUNG = 'OP..';
      END
     IF (OPBETRAG > 0) THEN
      SH = 'S';
     ELSE
      IF (OPBETRAG < 0) THEN
       BEGIN
        SH = 'H';
        OPBETRAG = -OPBETRAG;
       END
      ELSE
       BEGIN
        OPBETRAG=NULL;
        SH='';
       END       
     GKONTOSTR = '';
     TEST = '01.' || EXTRACT(MONTH FROM CAST(DATUM AS DATE)) || '.' || EXTRACT(YEAR FROM CAST(DATUM AS DATE));
     DATUMSORT = CAST(TEST AS DATE);
     SUSPEND;
    END
   /* Zahlungen */
   FOR select OPNR, BNR, DATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, ONRSOLL, ONRHABEN, KSTRSOLL, KSTRHABEN, LBNR, ARTSOLL from buchung
    where (onrsoll=:ONR or onrhaben=:ONR) and (ksoll=:KONTO or khaben=:KONTO) and opbetrag is null and betrag <> 0 AND (Datum >= :FROMDATUM and Datum <= :TODATUM)
    order by 1, 3
   into
    :OPNR, :BNR, :DATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :ONRSOLL, :ONRHABEN, :KSTRSOLL, :KSTRHABEN, :LBNR, :ARTSOLL 
   DO
    BEGIN
     DATUMH = DATUM;
     DATUMS = NULL;
     BETRAGS = NULL;
     SH = '';
     BEMERKUNG = '';
     OPBETRAG = NULL;
     /* */
     select datum from buchung where bnr=:opnr into :solldatum;
     IF (SOLLDATUM IS NULL) THEN
      SOLLDATUM = '1900-01-01';
     SSORT = SOLLDATUM || '_' || OPNR || '_2_' || DATUM;
     IF (BANKNRSOLL IS NULL AND BANKNRHABEN IS NULL) THEN
      BEGIN /* VERRECHNUNG */
       IF ((ARTSOLL = 24) OR (ARTSOLL = 27) or (ARTSOLL = 1)) THEN
        BEGIN
         BETRAGH = BETRAG;
        END
       ELSE
        BEGIN         
         BETRAGH = -BETRAG;
        END
      END
     ELSE
      BEGIN /* ZAhlung */       
       BETRAGH = BETRAG;
       IF (LBNR IS NOT NULL) then
        BEMERKUNG = 'LEV';
      END
     GKONTOSTR='';
     IF (BANKNRSOLL IS NOT NULL) THEN
      BEGIN
       IF (BANKNRSOLL = LEVBANKNR) THEN
        GKONTOSTR = LEVBANKSTR;
       ELSE
        IF (BANKNRSOLL = LEVBANK2NR) THEN
         GKONTOSTR = LEVBANK2STR;
        ELSE
         SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :GKONTOSTR;
      END
     ELSE
      BEGIN
       IF (BANKNRHABEN = LEVBANKNR) THEN
        GKONTOSTR = LEVBANKSTR;
       ELSE
        IF (BANKNRHABEN = LEVBANK2NR) THEN
         GKONTOSTR = LEVBANK2STR;
        ELSE
         SELECT KURZBEZ from Banken where NR=:BANKNRHABEN into :GKONTOSTR;
      END
     TEST = '01.' || EXTRACT(MONTH FROM CAST(DATUM AS DATE)) || '.' || EXTRACT(YEAR FROM CAST(DATUM AS DATE));
     DATUMSORT = CAST(TEST AS DATE);
     SUSPEND;
    END   
  END
 ELSE
  BEGIN  /* chronologisch */
   FOR SELECT BNR, DATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, ONRSOLL, ONRHABEN,LBNR,ARTSOLL from buchung
     WHERE ((ONRSOLL = :ONR AND KSOLL = :KONTO) OR (ONRHABEN = :ONR AND KHABEN = :KONTO))
     AND (Datum >= :FROMDATUM and Datum <= :TODATUM)
     AND SPLITNR IS NULL and ((betrag <> 0) or ((betrag=0) and (OPBETRAG<>0)))
     UNION
     SELECT buchung.BNR, DATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, splitbuch.BETRAG, BANKNRSOLL, BANKNRHABEN, buchung.OPBETRAG, SPLITNR, ONRSOLL, ONRHABEN,LBNR,ARTSOLL from buchung, splitbuch
     WHERE ((ONRSOLL = :ONR AND KSOLL = :KONTO) OR (ONRHABEN = :ONR AND KHABEN = :KONTO))
     AND (Datum >= :FROMDATUM and Datum <= :TODATUM)
     AND SPLITNR IS NOT NULL and ((splitbuch.betrag <> 0) or ((splitbuch.betrag=0) and (splitbuch.OPBETRAG<>0)))
     AND BUCHUNG.BNR = SPLITBUCH.BNR
     ORDER BY 2, 1
    INTO :BNR, :DATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :ONRSOLL, :ONRHABEN, :LBNR,:ARTSOLL
    DO
     BEGIN
      BEMERKUNG='';
      SSORT = DATUM;
      IF (OPBETRAG IS NOT NULL) THEN
       BEGIN
        IF (SPLITNR IS NOT NULL) THEN
         SELECT SUM(OPBETRAG) from splitbuch where BNR=:SPLITNR into :OPBETRAG;
        DATUMS=DATUM;
        BETRAGS=BETRAG;
        DATUMH=NULL;
        BETRAGH=NULL;
        IF (OPBETRAG=0) THEN
         BEGIN
          IF (SPLITNR IS NULL) THEN
           BEMERKUNG='SO';
          ELSE
           BEMERKUNG='SO..';
         END
        ELSE
         BEGIN
          IF (SPLITNR IS NULL) THEN
           BEMERKUNG='OP';
          ELSE
           BEMERKUNG='OP..';
         END
        IF (OPBETRAG>0) THEN
         SH='S';
        ELSE
         IF (OPBETRAG<0) THEN
          BEGIN
           SH='H';
           OPBETRAG=-OPBETRAG;
          END
         ELSE
          BEGIN
           OPBETRAG=NULL;
           SH='';
          END
       END
      ELSE
       BEGIN /* ZAHLUNG */
        DATUMH=DATUM;
        IF (KSOLL=KONTO) THEN /* Bank im Haben = - */
         BETRAGH=-BETRAG;
        ELSE
         BETRAGH=BETRAG;
        DATUMS=NULL;
        BETRAGS=NULL;
        SH='';
        IF (LBNR IS NOT NULL) then
         BEMERKUNG='LEV';
        ELSE
         BEMERKUNG='';
       END
      GKONTOSTR='';
      /*IF (BETRAG<>0) THEN  Sollstellung Betrag=0 nicht anzeigen */
       BEGIN
        IF (BANKNRSOLL IS NOT NULL) THEN
         BEGIN
          IF (BANKNRSOLL=LEVBANKNR) THEN
           GKONTOSTR=LEVBANKSTR;
          ELSE
           IF (BANKNRSOLL=LEVBANK2NR) THEN
            GKONTOSTR=LEVBANK2STR;
           ELSE
            SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :GKONTOSTR;
         END
        ELSE
         BEGIN
          IF (BANKNRHABEN=LEVBANKNR) THEN
           GKONTOSTR=LEVBANKSTR;
          ELSE
           IF (BANKNRHABEN=LEVBANK2NR) THEN
            GKONTOSTR=LEVBANK2STR;
           ELSE
            SELECT KURZBEZ from Banken where NR=:BANKNRHABEN into :GKONTOSTR;
         END
        TEST='01.' || EXTRACT(MONTH FROM CAST(DATUM AS DATE)) || '.' || EXTRACT(YEAR FROM CAST(DATUM AS DATE));
        DATUMSORT=CAST(TEST AS DATE)/*DATUMS*/;
        SUSPEND;
       END
     END
  END
END
