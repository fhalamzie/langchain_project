-- Prozedur: OFFENE_POSTEN_LISTE
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE OFFENE_POSTEN_LISTE
DECLARE VARIABLE ONRSOLL INTEGER;
DECLARE VARIABLE ONRHABEN INTEGER;
DECLARE VARIABLE KSOLL INTEGER;
DECLARE VARIABLE KHABEN INTEGER;
DECLARE VARIABLE ARTSOLL INTEGER;
DECLARE VARIABLE ARTHABEN INTEGER;
DECLARE VARIABLE KSTRSOLL VARCHAR(15);
DECLARE VARIABLE KSTRHABEN VARCHAR(15);
BEGIN
 if (IONR=-1) then
  begin
   FOR SELECT
    Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, BNR, LBNR, OPBetrag, Betrag, 
      Mwst, SPLITNR, LASTERZEUGT, BELEGNR, ZZDATUM, MAHNSTUFE, ZULETZT_GEMAHNT from buchung
    WHERE (Datum>=:DTVON and Datum<=:DTBIS)
    AND (SPLITNR IS NULL)
    AND (OPBETRAG<>0)
   UNION
    SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, splitbuch.BNR, LBNR, splitbuch.OPBetrag, 
     splitbuch.Betrag, Mwst, SPLITNR, LASTERZEUGT, BELEGNR, ZZDATUM, MAHNSTUFE, ZULETZT_GEMAHNT from buchung, splitbuch
    WHERE (Datum>=:DTVON and Datum<=:DTBIS)
    AND (SPLITNR IS NOT NULL)
    AND (splitbuch.OPBETRAG<>0)
    and buchung.bnr=splitbuch.bnr
    INTO :DATUM, :ONRSOLL, :KSOLL, :KSTRSOLL, :ARTSOLL, :ONRHABEN, :KHABEN, :KSTRHABEN, :ARTHABEN, :TEXT, :BNR, :LBNR, :OPBETRAG, 
     :OPGESBETRAG, :MWST, :SPLITNR, :LASTERZEUGT, :BELEGNR, :ZZDATUM, :MAHNSTUFE, :ZULETZT_GEMAHNT
    DO
     BEGIN
      ZAHLUNG=OPGESBETRAG-OPBETRAG;
      IF (LASTERZEUGT IS NULL) THEN
       LASTERZEUGT=0;
      IF (MWST IS NULL) THEN
       MWST=0;       
      IF ((ARTSOLL>=60 AND ARTSOLL<=62) or (ARTHABEN>=60 AND ARTHABEN<=62)) THEN
       BEGIN
        ISDEBITOR=1;
        IF (ARTSOLL>=60 AND ARTSOLL<=62) THEN
         BEGIN
          ONR=ONRSOLL;
          KNR=KSOLL;
          KNRSTR=KSTRSOLL;
          KKLASSE=ARTSOLL;
         END
        ELSE
         BEGIN
          ONR=ONRHABEN;
          KNR=KHABEN;
          KNRSTR=KSTRHABEN;
          KKLASSE=ARTHABEN;
         END
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
      IF ((ARTSOLL=71 or ARTHABEN=71) and ((KSOLL>=:KNRVON and KSOLL<=:KNRBIS) or (KHABEN>=:KNRVON and KHABEN<=:KNRBIS))) THEN
       BEGIN
        ISDEBITOR=2;
        IF (ARTSOLL=71) THEN 
         BEGIN
          ONR=ONRHABEN;
          KNR=KSOLL;
          KNRSTR=KSTRSOLL;
          KKLASSE=ARTSOLL;
         END
        ELSE
         BEGIN
          ONR=ONRSOLL;
          KNR=KHABEN;
          KNRSTR=KSTRHABEN;
          KKLASSE=ARTHABEN;
         END
        LASTERZEUGT=-1;
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
       END /* KREDITOREN OP */
     END
  end
 else
  begin
   FOR SELECT
    Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, BNR, LBNR, OPBetrag, 
     Betrag, Mwst, SPLITNR, LASTERZEUGT, BELEGNR, ZZDATUM, MAHNSTUFE, ZULETZT_GEMAHNT from buchung
    WHERE (ONRSOLL=:IONR OR ONRHABEN=:IONR)
    AND ((KSOLL>=:KNRVON AND KSOLL <=:KNRBIS) OR (KHABEN>=:KNRVON AND KHABEN <=:KNRBIS))
    AND (Datum>=:DTVON and Datum<=:DTBIS)
    AND (SPLITNR IS NULL)
    AND (OPBETRAG<>0)
   UNION
    SELECT Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, splitbuch.BNR, 
    LBNR, splitbuch.OPBetrag, splitbuch.Betrag, Mwst, SPLITNR, LASTERZEUGT, BELEGNR, ZZDATUM, MAHNSTUFE, ZULETZT_GEMAHNT from buchung, splitbuch
    WHERE (ONRSOLL=:IONR OR ONRHABEN=:IONR)
    AND ((KSOLL>=:KNRVON AND KSOLL <=:KNRBIS) OR (KHABEN>=:KNRVON AND KHABEN <=:KNRBIS))
    AND (Datum>=:DTVON and Datum<=:DTBIS)
    AND (SPLITNR IS NOT NULL)
    AND (splitbuch.OPBETRAG<>0)
    and buchung.bnr=splitbuch.bnr
    INTO :DATUM, :ONRSOLL, :KSOLL, :KSTRSOLL, :ARTSOLL, :ONRHABEN, :KHABEN, :KSTRHABEN, :ARTHABEN, :TEXT, :BNR, :LBNR, :OPBETRAG, 
      :OPGESBETRAG, :MWST, :SPLITNR, :LASTERZEUGT, :BELEGNR, :ZZDATUM, :MAHNSTUFE, :ZULETZT_GEMAHNT
    DO
     BEGIN
      ZAHLUNG=OPGESBETRAG-OPBETRAG;
      IF (LASTERZEUGT IS NULL) THEN
       LASTERZEUGT=0;
      IF (MWST IS NULL) THEN
       MWST=0;       
      IF ((ARTSOLL>=60 AND ARTSOLL<=62) or (ARTHABEN>=60 AND ARTHABEN<=62)) THEN
       BEGIN
        ISDEBITOR=1;
        IF (ARTSOLL>=60 AND ARTSOLL<=62) THEN
         BEGIN
          ONR=ONRSOLL;
          KNR=KSOLL;
          KNRSTR=KSTRSOLL;
          KKLASSE=ARTSOLL;
         END
        ELSE
         BEGIN
          ONR=ONRHABEN;
          KNR=KHABEN;
          KNRSTR=KSTRHABEN;
          KKLASSE=ARTHABEN;
         END
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
         END
        ELSE
         BEGIN
          ONR=ONRSOLL;
          KNR=KHABEN;
          KNRSTR=KSTRHABEN;
          KKLASSE=ARTHABEN;
         END
        LASTERZEUGT=-1;
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
       END /* KREDITOREN OP */
     END
  end
END
