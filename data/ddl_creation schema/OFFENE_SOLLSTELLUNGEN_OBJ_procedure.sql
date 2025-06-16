-- Prozedur: OFFENE_SOLLSTELLUNGEN_OBJ
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE OFFENE_SOLLSTELLUNGEN_OBJ
DECLARE VARIABLE ONRSOLL INTEGER;
 DECLARE VARIABLE ONRHABEN INTEGER;
 DECLARE VARIABLE KSTRSOLL VARCHAR(15);
 DECLARE VARIABLE KSTRHABEN VARCHAR(15);
 DECLARE VARIABLE IANZ INTEGER;
BEGIN
 FOR SELECT
  Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, BNR, LBNR, OPBetrag, Betrag, Mwst, SPLITNR, LASTERZEUGT, BANKNRSOLL, BANKNRHABEN, LASTBANK, GN from buchung
  WHERE OPBETRAG<>0 and LBNR IS NULL and SPLITNR IS NULL and (ONRSOLL = :ONR_IN or ONRHABEN=:ONR_IN) and (Datum>=:DTVON and Datum<=:DTBIS)
 UNION
  select Datum, ONRSOLL, KSOLL, KSTRSOLL, ARTSOLL, ONRHABEN, KHABEN, KSTRHABEN, ARTHABEN, TEXT, splitbuch.BNR, LBNR, splitbuch.OPBetrag, splitbuch.Betrag, Mwst, SPLITNR, LASTERZEUGT, BANKNRSOLL, BANKNRHABEN, LASTBANK, GN from buchung, splitbuch
  WHERE splitbuch.OPBETRAG<>0 and LBNR IS NULL and SPLITNR IS NOT NULL and (ONRSOLL = :ONR_IN or ONRHABEN=:ONR_IN) and (Datum>=:DTVON and Datum<=:DTBIS)
  AND buchung.bnr=splitbuch.bnr
  INTO :DATUM, :ONRSOLL, :KSOLL, :KSTRSOLL, :ARTSOLL, :ONRHABEN, :KHABEN, :KSTRHABEN, :ARTHABEN, :TEXT, :BNR, :LBNR, :OPBETRAG, :OPGESBETRAG, :MWST, :SPLITNR, :LASTERZEUGT, :BANKNRSOLL, :BANKNRHABEN, :LASTBANK, :GN
  DO
   BEGIN
    OPRESTBETRAG=OPGESBETRAG-OPBETRAG;
    IF (LASTERZEUGT IS NULL) THEN
     LASTERZEUGT=-1;
    IF ((ARTSOLL>=60 AND ARTSOLL<=64) or (ARTHABEN>=60 AND ARTHABEN<=64)) THEN
     BEGIN
      ISDEBITOR=1;
      IF (ARTSOLL>=60 AND ARTSOLL<=64) THEN
       BEGIN
        ONR=ONRSOLL;
        KNR=KSOLL;
        KKLASSE=ARTSOLL;
        KNROP=KHABEN;
        ARTOP=ARTHABEN;
       END
      ELSE
       BEGIN
        ONR=ONRHABEN;
        KNR=KHABEN;
        KKLASSE=ARTHABEN;
        KNROP=KSOLL;
        ARTOP=ARTSOLL;
       END
      EXECUTE PROCEDURE GET_SOLLSTBEZ(ONR, KNR, ISDEBITOR) RETURNING_VALUES BEZ;
      IF (ARTHABEN=13) THEN /*IF (ARTHABEN=13 OR ARTHABEN=18) THEN*/
       ISGN=1;
      ELSE
       BEGIN
        ISGN=GN;
       end
      SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:ONR AND KNR=:KNR
       into :KNRSTR;
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
        ARTOP=ARTHABEN;
        KNROP=KHABEN;
       END
      ELSE
       BEGIN
        ONR=ONRSOLL;
        KNR=KHABEN;
        KNRSTR=KSTRHABEN;
        KKLASSE=ARTHABEN;
        ARTOP=ARTSOLL;
        KNROP=KSOLL;
       END
      SELECT NAME || ', ' || STRASSE || ' ' || PLZ || ' ' || ORT || TEL1 from lieferan
      where LIEFKNR=:KNR
      INTO
      BEZ;
      LASTERZEUGT=-1;
      SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KNR
       into :KNRSTR;
      SUSPEND;
     END /* KREDITOREN OP */
   END
 /* JETZT NOCH DIE SLEV */
 FOR SELECT
  Datum, Betrag, TEXT, LBNR, ONR, BANKNR  from slevbuch
  WHERE OPBETRAG>0 and (Datum>=:DTVON and Datum<=:DTBIS)
  INTO :DATUM, :OPBETRAG, :TEXT, :LBNR, :ONR, :LASTBANK
  DO
   BEGIN
    BNR=LBNR;
    LASTERZEUGT=1;
    ISDEBITOR=1;
    OPRESTBETRAG=0;
    OPGESBETRAG=OPBETRAG;
    OPRESTBETRAG=OPGESBETRAG-OPBETRAG;
    BEZ='Sammel-Lastschriftseinzug (DTA)';
    IF (ONR IS NULL or ONR=0) then
     begin
      /* feststellen, ob mindestens eine mit ONR_IN vorhanden ist */
      ONR=NULL;
      select count(*) from buchung where LBNR=:LBNR and ((ONRSOLL=:ONR_IN) or (ONRHABEN=:ONR_IN)) into :IANZ;
      if (IANZ>0) then
       begin
        KNR=NULL;
        KNRSTR=NULL;
        KKLASSE=NULL;
        SUSPEND;
       end
     end
    else
     if (ONR=ONR_IN) then
      begin
       KNR=NULL;
       KNRSTR=NULL;
       KKLASSE=NULL;
       SUSPEND;
      end
   END
END
