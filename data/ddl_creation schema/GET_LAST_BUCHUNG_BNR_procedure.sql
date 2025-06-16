-- Prozedur: GET_LAST_BUCHUNG_BNR
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE GET_LAST_BUCHUNG_BNR
DECLARE VARIABLE KSOLL INTEGER;
DECLARE VARIABLE KHABEN INTEGER;
DECLARE VARIABLE BANKNRSOLL INTEGER;
DECLARE VARIABLE BANKNRHABEN INTEGER;
DECLARE VARIABLE BSTRSOLL VARCHAR(15);
DECLARE VARIABLE BSTRHABEN VARCHAR(15);
DECLARE VARIABLE SPLITNR INTEGER;
DECLARE VARIABLE ONRSOLL INTEGER;
DECLARE VARIABLE ONRHABEN INTEGER;
DECLARE VARIABLE STR_LEN INTEGER;
BEGIN
 SELECT
  BNR,DATUM,WDATUM,ONRSOLL, ONRHABEN, BELEGNR, KSOLL, TEXT, BETRAG, OPBETRAG, MWST, KHABEN, BANKNRSOLL, BANKNRHABEN, BSTRSOLL, BSTRHABEN, SPLITNR, LBNR FROM BUCHUNG WHERE BNR=:BNR_IN
 INTO
  :BNR, :DATUM, :WDATUM, :ONRSOLL, :ONRHABEN, :BELEGNR, :KSOLL,:TEXT, :BETRAG, :OPBETRAG, :MWST, :KHABEN, :BANKNRSOLL, :BANKNRHABEN, :BSTRSOLL, :BSTRHABEN, :SPLITNR, :LBNR;
 IF (BNR IS NOT NULL) THEN
  BEGIN
   IF (LBNR IS NULL) THEN
    BEGIN
     IF (ANZEIGE='2') THEN      /* Anzeige doppelte BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung alle = split*/
      BEGIN
       /*IF (SPLITNR IS NULL) THEN*/
        BEGIN
         SELECT SUBSTRING(KNRSTR || ' ' || KBEZ FROM 1 FOR 120) from konten where ONR=:ONRSOLL AND KNR=:KSOLL into :KSOLLSTR;
         SELECT SUBSTRING(KNRSTR || ' ' || KBEZ FROM 1 FOR 120) from konten where ONR=:ONRHABEN AND KNR=:KHABEN into :KHABENSTR;
         IF (:BANKNRSOLL IS NOT NULL) THEN
          KSOLLSTR = KSOLLSTR || ' ' || BSTRSOLL;
         IF (:BANKNRHABEN IS NOT NULL) THEN
          KHABENSTR = KHABENSTR || ' ' || BSTRHABEN;
         IF (ONRSOLL = 0) THEN
          ONR=ONRHABEN;
         ELSE
          ONR=ONRSOLL;
         IF (ONR=0) THEN
          ONR = NULL;
         IF (:OPBETRAG IS NOT NULL) THEN
          BEGIN
           IF (:SPLITNR IS NULL) THEN
            BEMERKUNG='OP';
           else
            BEMERKUNG='OP..';
          END
         ELSE
          BEMERKUNG=NULL;
         SUSPEND;
        end
      END
     ELSE
      IF (ANZEIGE=1) THEN       /* DOPPELTE BUCHFÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“HRUNG SPLIT ZUSAMMENGEFASST */
       BEGIN
        IF (SPLITNR IS NOT NULL) THEN
         SELECT splitbuch.BETRAG, splitbuch.OPBETRAG from splitbuch  where bnr=:bnr into :BETRAG, :OPBETRAG;
        SELECT SUBSTRING(KNRSTR || ' ' || KBEZ FROM 1 FOR 120) from konten where ONR=:ONRSOLL AND KNR=:KSOLL into :KSOLLSTR;
        SELECT SUBSTRING(KNRSTR || ' ' || KBEZ FROM 1 FOR 120) from konten where ONR=:ONRHABEN AND KNR=:KHABEN into :KHABENSTR;
        IF (:BANKNRSOLL IS NOT NULL) THEN
         KSOLLSTR = KSOLLSTR || ' ' || BSTRSOLL;
        IF (:BANKNRHABEN IS NOT NULL) THEN
         KHABENSTR = KHABENSTR || ' ' || BSTRHABEN;
        IF (ONRSOLL = 0) THEN
         ONR=ONRHABEN;
        ELSE
         ONR=ONRSOLL;
        IF (ONR=0) THEN
         ONR=NULL;
        IF (:OPBETRAG IS NOT NULL) THEN
         BEGIN
          IF (:SPLITNR IS NULL) THEN
           BEMERKUNG='OP';
          else
           BEMERKUNG='OP..';
         END
        ELSE
         BEGIN
          IF (:SPLITNR IS NOT NULL) THEN
           BEMERKUNG='..';
          ELSE
           BEMERKUNG=NULL;
         END
        /**/
        IF (SPLITNR IS NOT NULL) THEN
         BEGIN
          IF (SPLITNR=BNR) THEN
           BEGIN
            STR_LEN = CHAR_LENGTH(TEXT);
            IF (STR_LEN > 62) THEN
             TEXT = SUBSTRING (TEXT FROM 1 FOR 62);
            TEXT = TEXT || ' (Split)';
            SUSPEND;
           END 
         END
        ELSE
         SUSPEND;
       END   /* DOPPELTE BUCHFÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“HRUNG SPLIT ZUSAMMENGEFASST */
      ELSE
       IF (ANZEIGE=0) THEN       /* EINFACHE BUCHFÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“HRUNG nur Bankbuchungen ANZEIGEN */
        BEGIN
         IF (BANKNRSOLL IS NOT NULL OR BANKNRHABEN IS NOT NULL) THEN
          BEGIN
           IF (BANKNRSOLL IS NOT NULL AND BANKNRHABEN IS NOT NULL) THEN
            BEGIN
             KSOLLSTR=:BSTRSOLL;
             KHABENSTR=:BSTRHABEN;
            END
           ELSE
            IF (BANKNRSOLL IS NOT NULL) THEN
             BEGIN
              KHABENSTR=:BSTRSOLL;
              SELECT SUBSTRING(KNRSTR || ' ' || KBEZ FROM 1 FOR 120) from konten where ONR=:ONRHABEN AND KNR=:KHABEN into :KSOLLSTR;
              ONR=:ONRHABEN;
             END
            ELSE
             IF (BANKNRHABEN IS NOT NULL) THEN
              BEGIN
               KHABENSTR=:BSTRHABEN;
               SELECT SUBSTRING(KNRSTR || ' ' || KBEZ FROM 1 FOR 120) from konten where ONR=:ONRSOLL AND KNR=:KSOLL into :KSOLLSTR;
               ONR=:ONRSOLL;
              END
           IF (ONR = 0) THEN
            ONR=NULL;
           IF (:OPBETRAG IS NOT NULL) THEN
            BEGIN
             IF (:SPLITNR IS NULL) THEN
              BEMERKUNG='OP';
             else
              BEMERKUNG='OP..';
            END
           ELSE
            BEGIN
             IF (:SPLITNR IS NOT NULL) THEN
              BEMERKUNG='..';
             ELSE
              BEMERKUNG=NULL;
            END
           SUSPEND;
          END /* BANKBUCHUNG */
        END
    END
   ELSE
    BEGIN
     /* Sammler */
     SELECT DATUM, BELEGNR, TEXT, BETRAG, BANKNR FROM SLEVBUCH WHERE LBNR=:LBNR INTO :DATUM, BELEGNR, :TEXT, :BETRAG, :BANKNRHABEN;
     BNR=LBNR;
     SELECT KURZBEZ from banken where NR=:BANKNRHABEN into :BSTRSOLL;
     IF (ANZEIGE=0) THEN
      BEGIN
       KHABENSTR = BSTRSOLL;
       KSOLLSTR='(Sammler)';
      END
     ELSE
      BEGIN
       KSOLLSTR = BSTRSOLL;
       KHABENSTR='(Sammler)';
      END
     ONR=ONRHABEN;
     BEMERKUNG='SLE';
     WDATUM=DATUM;
     SUSPEND;
    END  /* SAMMLER */
  END /* BNR not NULL */
END
