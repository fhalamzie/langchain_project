-- Prozedur: OFFENE_SOLLSTELLUNGEN_KONTO
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE OFFENE_SOLLSTELLUNGEN_KONTO
DECLARE VARIABLE ONRSOLL INTEGER;
DECLARE VARIABLE ONRHABEN INTEGER;
DECLARE VARIABLE KSOLL INTEGER;
DECLARE VARIABLE KHABEN INTEGER;
DECLARE VARIABLE ARTSOLL INTEGER;
DECLARE VARIABLE ARTHABEN INTEGER;
DECLARE VARIABLE KSTRSOLL VARCHAR(15);
DECLARE VARIABLE KSTRHABEN VARCHAR(15);
DECLARE VARIABLE IEIGNR INTEGER;
DECLARE VARIABLE IBEWNR INTEGER;
DECLARE VARIABLE OPKONTO_S VARCHAR(204);
DECLARE VARIABLE OPKONTO_H VARCHAR(204);
BEGIN
 SUMMEOP=0;
 /* */
 IF (BALLEEIG='N') THEN
  BEGIN
   /*ein Datensatz*/
   FOR
    SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, BNR, LBNR, buchung.OPBetrag, Betrag, Mwst, SPLITNR, LASTERZEUGT, LASTBANK, GN,WDATUM,(k1.KNRSTR || ' ' || k1.KBEZ) as KTOSTEXT,(k2.KNRSTR || ' ' || k2.KBEZ) as KTOHTEXT from buchung, konten K1, konten K2
    WHERE ((ONRHABEN=:IONR and KHABEN=:IKNR) or (ONRSOLL=:IONR and KSOLL=:IKNR)) AND (((buchung.opbetrag>0) and (:ISPOSITIV='J')) or ((buchung.opbetrag<0) and (:ISPOSITIV='N'))) and (LASTBANK IS NOT NULL) and SPLITNR IS NULL
    and k1.onr=buchung.onrsoll and K1.KNR=buchung.ksoll and k2.onr=buchung.onrhaben and K2.KNR=buchung.khaben
    UNION
    SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, splitbuch.BNR, LBNR, splitbuch.OPBetrag, splitbuch.Betrag, Mwst, SPLITNR, LASTERZEUGT, LASTBANK, GN,buchung.WDATUM,(k1.KNRSTR || ' ' || k1.KBEZ) as KTOSTEXT,(k2.KNRSTR || ' ' || k2.KBEZ) as KTOHTEXT from buchung, splitbuch, konten K1, konten K2
    WHERE ((ONRHABEN=:IONR and KHABEN=:IKNR) or (ONRSOLL=:IONR and KSOLL=:IKNR)) and (((splitbuch.opbetrag>0) and (:ISPOSITIV='J')) or ((splitbuch.opbetrag<0) and (:ISPOSITIV='N'))) AND (SPLITNR IS NOT NULL) and (LASTBANK IS NOT NULL) and buchung.bnr=splitbuch.bnr
    and k1.onr=buchung.onrsoll and K1.KNR=buchung.ksoll and k2.onr=buchung.onrhaben and K2.KNR=buchung.khaben 
   INTO :DATUM, :ONRSOLL, :KSOLL, :KSTRSOLL, :ARTSOLL, :ONRHABEN, :KHABEN, :KSTRHABEN, :ARTHABEN, :TEXT, :BNR, :LBNR, :OPBETRAG, :OPGESBETRAG, :MWST, :SPLITNR, :LASTERZEUGT, :LASTBANK, :GN, :WDATUM, :OPKONTO_S, :OPKONTO_H
   DO
   BEGIN
    OPRESTBETRAG=OPGESBETRAG-OPBETRAG;
    IF (LASTERZEUGT IS NULL) THEN
     LASTERZEUGT=0;
    IF ((ARTSOLL>=60 AND ARTSOLL<=64) or (ARTHABEN>=60 AND ARTHABEN<=64)) THEN
     BEGIN
      ISDEBITOR=1;
      IF (ARTSOLL>=60 AND ARTSOLL<=64) THEN
       BEGIN
        ONR=ONRSOLL;
        KNR=KSOLL;
        KNRSTR=KSTRSOLL;
        KKLASSE=ARTSOLL;
        KNROP=KHABEN;
        ARTOP=ARTHABEN;
       END
      ELSE
       BEGIN
        ONR=ONRHABEN;
        KNR=KHABEN;
        KNRSTR=KSTRHABEN;
        KKLASSE=ARTHABEN;
        KNROP=KSOLL;
        ARTOP=ARTSOLL;
       END
      SUMMEOP=SUMMEOP+OPGESBETRAG;
      IF (LBNR IS NOT NULL) THEN
       BEGIN
        BEMERKUNG='DTA';
        TEXT='[S] ' || TEXT;
       END
      ELSE
       IF (SPLITNR IS NOT NULL) THEN
        BEGIN
         BEMERKUNG='OP..';
        END
       ELSE
        BEMERKUNG='OP';
      SUSPEND;
     END /* DEBITOREN OP */
    ELSE
     /* KREDITOREN OP */
     IF (ARTSOLL=71 or ARTHABEN=71) THEN
      BEGIN
       ISDEBITOR=2;
       IF (ARTSOLL=71) THEN
        BEGIN
         ONR=ONRHABEN;
         KNR=KSOLL;
         KNRSTR=KSTRSOLL;
         KKLASSE=ARTSOLL;
         KNROP=KHABEN;
         ARTOP=ARTHABEN;
         OPKONTO=LEFT(OPKONTO_H, 104);
        END
       ELSE
        BEGIN
         ONR=ONRSOLL;
         KNR=KHABEN;
         KNRSTR=KSTRHABEN;
         KKLASSE=ARTHABEN;
         ARTOP=ARTSOLL;
         KNROP=KSOLL;
         OPKONTO=LEFT(OPKONTO_S, 104);
        END
       LASTERZEUGT=-1;
       SUMMEOP=SUMMEOP+OPGESBETRAG;
       IF (LBNR IS NOT NULL) THEN
        BEGIN
         BEMERKUNG='DTA';
         TEXT='[S] ' || TEXT;
        END
       ELSE
        IF (SPLITNR IS NOT NULL) THEN
         BEGIN
          BEMERKUNG='OP..';
         END
        ELSE
         BEMERKUNG='OP';
       IF (IBANKNR=LASTBANK) THEN
        SUSPEND;
      END /* KREDITOREN OP */ 
   END
  END
 ELSE
  BEGIN
   IF (IKNR >= 200000) THEN
    BEGIN
     SELECT EIGNR from eigentuemer where ONR=:IONR and KNR=:IKNR INTO :IEIGNR;
     FOR
      SELECT onr, knr from eigentuemer where eignr=:IEIGNR and ONR in (select onr from objbanken where BANKNR=:IBANKNR)
      INTO :IONR, :IKNR
     DO 
     BEGIN
      FOR
       SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, BNR, LBNR, buchung.OPBetrag, Betrag, Mwst, SPLITNR, LASTERZEUGT, LASTBANK, GN,WDATUM,(k1.KNRSTR || ' ' || k1.KBEZ) as KTOSTEXT,(k2.KNRSTR || ' ' || k2.KBEZ) as KTOHTEXT from buchung, konten K1, konten K2
       WHERE ((ONRHABEN=:IONR and KHABEN=:IKNR) or (ONRSOLL=:IONR and KSOLL=:IKNR)) AND (((buchung.opbetrag>0) and (:ISPOSITIV='J')) or ((buchung.opbetrag<0) and (:ISPOSITIV='N'))) and (LASTBANK IS NOT NULL) and SPLITNR IS NULL
       and k1.onr=buchung.onrsoll and K1.KNR=buchung.ksoll and k2.onr=buchung.onrhaben and K2.KNR=buchung.khaben
       UNION
       SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, splitbuch.BNR, LBNR, splitbuch.OPBetrag, splitbuch.Betrag, Mwst, SPLITNR, LASTERZEUGT, LASTBANK, GN,buchung.WDATUM,(k1.KNRSTR || ' ' || k1.KBEZ) as KTOSTEXT,(k2.KNRSTR || ' ' || k2.KBEZ) as KTOHTEXT from buchung, splitbuch, konten K1, konten K2
       WHERE ((ONRHABEN=:IONR and KHABEN=:IKNR) or (ONRSOLL=:IONR and KSOLL=:IKNR)) and (((splitbuch.opbetrag>0) and (:ISPOSITIV='J')) or ((splitbuch.opbetrag<0) and (:ISPOSITIV='N'))) AND (SPLITNR IS NOT NULL) and (LASTBANK IS NOT NULL) and buchung.bnr=splitbuch.bnr
       and k1.onr=buchung.onrsoll and K1.KNR=buchung.ksoll and k2.onr=buchung.onrhaben and K2.KNR=buchung.khaben 
      INTO :DATUM, :ONRSOLL, :KSOLL, :KSTRSOLL, :ARTSOLL, :ONRHABEN, :KHABEN, :KSTRHABEN, :ARTHABEN, :TEXT, :BNR, :LBNR, :OPBETRAG, :OPGESBETRAG, :MWST, :SPLITNR, :LASTERZEUGT, :LASTBANK, :GN, :WDATUM, :OPKONTO_S, :OPKONTO_H
      DO
      BEGIN
       OPRESTBETRAG=OPGESBETRAG-OPBETRAG;
       IF (LASTERZEUGT IS NULL) THEN
        LASTERZEUGT=0;
       IF ((ARTSOLL>=60 AND ARTSOLL<=64) or (ARTHABEN>=60 AND ARTHABEN<=64)) THEN
        BEGIN
         ISDEBITOR=1;
         IF (ARTSOLL>=60 AND ARTSOLL<=64) THEN
          BEGIN
           ONR=ONRSOLL;
           KNR=KSOLL;
           KNRSTR=KSTRSOLL;
           KKLASSE=ARTSOLL;
           KNROP=KHABEN;
           ARTOP=ARTHABEN;
          END
         ELSE
          BEGIN
           ONR=ONRHABEN;
           KNR=KHABEN;
           KNRSTR=KSTRHABEN;
           KKLASSE=ARTHABEN;
           KNROP=KSOLL;
           ARTOP=ARTSOLL;
          END
         SUMMEOP=SUMMEOP+OPGESBETRAG;
         IF (LBNR IS NOT NULL) THEN
          BEGIN
           BEMERKUNG='DTA';
           TEXT='[S] ' || TEXT;
          END
         ELSE
          IF (SPLITNR IS NOT NULL) THEN
           BEGIN
            BEMERKUNG='OP..';
           END
          ELSE
           BEMERKUNG='OP';
         SUSPEND;
        END /* DEBITOREN OP */
       ELSE
        /* KREDITOREN OP */
        IF (ARTSOLL=71 or ARTHABEN=71) THEN
         BEGIN
          ISDEBITOR=2;
          IF (ARTSOLL=71) THEN
           BEGIN
            ONR=ONRHABEN;
            KNR=KSOLL;
            KNRSTR=KSTRSOLL;
            KKLASSE=ARTSOLL;
            KNROP=KHABEN;
            ARTOP=ARTHABEN;
            OPKONTO=LEFT(OPKONTO_H, 104);
           END
          ELSE
           BEGIN
            ONR=ONRSOLL;
            KNR=KHABEN;
            KNRSTR=KSTRHABEN;
            KKLASSE=ARTHABEN;
            ARTOP=ARTSOLL;
            KNROP=KSOLL;
            OPKONTO=LEFT(OPKONTO_S, 104);
           END
          LASTERZEUGT=-1;
          SUMMEOP=SUMMEOP+OPGESBETRAG;
          IF (LBNR IS NOT NULL) THEN
           BEGIN
            BEMERKUNG='DTA';
            TEXT='[S] ' || TEXT;
           END
          ELSE
           IF (SPLITNR IS NOT NULL) THEN
            BEGIN
             BEMERKUNG='OP..';
            END
           ELSE
            BEMERKUNG='OP';
          IF (IBANKNR=LASTBANK) THEN
           SUSPEND;
         END /* KREDITOREN OP */ 
      END
     END
    END 
  ELSE
    BEGIN
     SELECT BEWNR from bewohner where ONR=:IONR and KNR=:IKNR INTO :IBEWNR;
     FOR
      SELECT onr, knr from bewohner where bewnr=:IBEWNR and ONR in (select onr from objbanken where BANKNR=:IBANKNR)
      INTO :IONR, :IKNR
     DO 
     BEGIN
      FOR
       SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, BNR, LBNR, buchung.OPBetrag, Betrag, Mwst, SPLITNR, LASTERZEUGT, LASTBANK, GN,WDATUM,(k1.KNRSTR || ' ' || k1.KBEZ) as KTOSTEXT,(k2.KNRSTR || ' ' || k2.KBEZ) as KTOHTEXT from buchung, konten K1, konten K2
       WHERE ((ONRHABEN=:IONR and KHABEN=:IKNR) or (ONRSOLL=:IONR and KSOLL=:IKNR)) AND (((buchung.opbetrag>0) and (:ISPOSITIV='J')) or ((buchung.opbetrag<0) and (:ISPOSITIV='N'))) and (LASTBANK IS NOT NULL) and SPLITNR IS NULL
       and k1.onr=buchung.onrsoll and K1.KNR=buchung.ksoll and k2.onr=buchung.onrhaben and K2.KNR=buchung.khaben
       UNION
       SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, splitbuch.BNR, LBNR, splitbuch.OPBetrag, splitbuch.Betrag, Mwst, SPLITNR, LASTERZEUGT, LASTBANK, GN,buchung.WDATUM,(k1.KNRSTR || ' ' || k1.KBEZ) as KTOSTEXT,(k2.KNRSTR || ' ' || k2.KBEZ) as KTOHTEXT from buchung, splitbuch, konten K1, konten K2
       WHERE ((ONRHABEN=:IONR and KHABEN=:IKNR) or (ONRSOLL=:IONR and KSOLL=:IKNR)) and (((splitbuch.opbetrag>0) and (:ISPOSITIV='J')) or ((splitbuch.opbetrag<0) and (:ISPOSITIV='N'))) AND (SPLITNR IS NOT NULL) and (LASTBANK IS NOT NULL) and buchung.bnr=splitbuch.bnr
       and k1.onr=buchung.onrsoll and K1.KNR=buchung.ksoll and k2.onr=buchung.onrhaben and K2.KNR=buchung.khaben 
      INTO :DATUM, :ONRSOLL, :KSOLL, :KSTRSOLL, :ARTSOLL, :ONRHABEN, :KHABEN, :KSTRHABEN, :ARTHABEN, :TEXT, :BNR, :LBNR, :OPBETRAG, :OPGESBETRAG, :MWST, :SPLITNR, :LASTERZEUGT, :LASTBANK, :GN, :WDATUM, :OPKONTO_S, :OPKONTO_H
      DO
      BEGIN
       OPRESTBETRAG=OPGESBETRAG-OPBETRAG;
       IF (LASTERZEUGT IS NULL) THEN
        LASTERZEUGT=0;
       IF ((ARTSOLL>=60 AND ARTSOLL<=64) or (ARTHABEN>=60 AND ARTHABEN<=64)) THEN
        BEGIN
         ISDEBITOR=1;
         IF (ARTSOLL>=60 AND ARTSOLL<=64) THEN
          BEGIN
           ONR=ONRSOLL;
           KNR=KSOLL;
           KNRSTR=KSTRSOLL;
           KKLASSE=ARTSOLL;
           KNROP=KHABEN;
           ARTOP=ARTHABEN;
          END
         ELSE
          BEGIN
           ONR=ONRHABEN;
           KNR=KHABEN;
           KNRSTR=KSTRHABEN;
           KKLASSE=ARTHABEN;
           KNROP=KSOLL;
           ARTOP=ARTSOLL;
          END
         SUMMEOP=SUMMEOP+OPGESBETRAG;
         IF (LBNR IS NOT NULL) THEN
          BEGIN
           BEMERKUNG='DTA';
           TEXT='[S] ' || TEXT;
          END
         ELSE
          IF (SPLITNR IS NOT NULL) THEN
           BEGIN
            BEMERKUNG='OP..';
           END
          ELSE
           BEMERKUNG='OP';
         SUSPEND;
        END /* DEBITOREN OP */
       ELSE
        /* KREDITOREN OP */
        IF (ARTSOLL=71 or ARTHABEN=71) THEN
         BEGIN
          ISDEBITOR=2;
          IF (ARTSOLL=71) THEN
           BEGIN
            ONR=ONRHABEN;
            KNR=KSOLL;
            KNRSTR=KSTRSOLL;
            KKLASSE=ARTSOLL;
            KNROP=KHABEN;
            ARTOP=ARTHABEN;
            OPKONTO=LEFT(OPKONTO_H, 104);
           END
          ELSE
           BEGIN
            ONR=ONRSOLL;
            KNR=KHABEN;
            KNRSTR=KSTRHABEN;
            KKLASSE=ARTHABEN;
            ARTOP=ARTSOLL;
            KNROP=KSOLL;
            OPKONTO=LEFT(OPKONTO_S, 104);
           END
          LASTERZEUGT=-1;
          SUMMEOP=SUMMEOP+OPGESBETRAG;
          IF (LBNR IS NOT NULL) THEN
           BEGIN
            BEMERKUNG='DTA';
            TEXT='[S] ' || TEXT;
           END
          ELSE
           IF (SPLITNR IS NOT NULL) THEN
            BEGIN
             BEMERKUNG='OP..';
            END
           ELSE
            BEMERKUNG='OP';
          IF (IBANKNR=LASTBANK) THEN
           SUSPEND;
         END /* KREDITOREN OP */ 
      END
     END
    END
  END
END
