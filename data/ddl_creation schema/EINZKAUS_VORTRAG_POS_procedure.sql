-- Prozedur: EINZKAUS_VORTRAG_POS
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE EINZKAUS_VORTRAG_POS
DECLARE VARIABLE BETRAG_SOLL NUMERIC(18, 2);
DECLARE VARIABLE BETRAG_BEZ NUMERIC(18, 2);
DECLARE VARIABLE SUM_TEMP NUMERIC(18, 2);
BEGIN
 IF (BMITVORTRAG='N') THEN
  BEGIN
   BETRAG=0;
   SUSPEND;
  END
 ELSE
  BEGIN
   /* Summe Soll DATUM = WDATUM*/
   IF (BWDATUM='N') THEN
    BEGIN
     select SUM(BETRAG) from buchung
      where ONRSOLL=:ONR and KSOLL=:KNR and Datum<:DTVON and ARTHABEN=:POS and OPNR IS NOT NULL AND OPBETRAG IS NOT NULL and (GN=:GN_1 or GN=:GN_2)
     into :BETRAG_SOLL;
     IF (BETRAG_SOLL IS NULL) THEN
      BETRAG_SOLL=0;
    END
   ELSE
    BEGIN
     select SUM(BETRAG) from buchung
      where ONRSOLL=:ONR and KSOLL=:KNR and WDatum<:DTVON and ARTHABEN=:POS and OPNR IS NOT NULL AND OPBETRAG IS NOT NULL and (GN=:GN_1 or GN=:GN_2)
     into :BETRAG_SOLL;
     IF (BETRAG_SOLL IS NULL) THEN
      BETRAG_SOLL=0;
    END
   /*  */
   BETRAG_BEZ=0;
   IF (BWDATUM='N') THEN
    BEGIN
     FOR SELECT SUM(BETRAG) from buchung
     where ONRHABEN=:ONR and KHABEN=:KNR and ARTOP=:POS and Datum<:DTVON  and (GN=:GN_1 or GN=:GN_2)
     union all
     SELECT SUM(BETRAG) from buchzahl
     where ARTOP=:POS and BNR IN (select bnr from buchung where onrhaben=:ONR and khaben=:KNR and ARTOP=0 and Datum<:DTVON and (GN=:GN_1 or GN=:GN_2))
     INTO :SUM_TEMP
     DO
      BEGIN
       IF (SUM_TEMP IS NOT NULL) THEN
        BETRAG_BEZ=BETRAG_BEZ+SUM_TEMP;
      END
     /* ZAHLUNG SOLL - */
     FOR SELECT SUM(BETRAG) from buchung
     where ONRSOLL=:ONR and KSOLL=:KNR and ARTOP=:POS and Datum<:DTVON  and (GN=:GN_1 or GN=:GN_2)
     union all
     SELECT SUM(BETRAG) from buchzahl
     where ARTOP=:POS and BNR IN (select bnr from buchung where onrsoll=:ONR and ksoll=:KNR and ARTOP=0 and Datum<:DTVON and (GN=:GN_1 or GN=:GN_2))
     INTO :SUM_TEMP
     DO
      BEGIN
       IF (SUM_TEMP IS NOT NULL) THEN
        BETRAG_BEZ=BETRAG_BEZ-SUM_TEMP;
      END
   END
  ELSE
   BEGIN  /* WDatum */
    /* SUMME BEZAHLT */
    FOR SELECT SUM(BETRAG) from buchung
    where ONRHABEN=:ONR and KHABEN=:KNR and ARTOP=:POS and WDatum<:DTVON  and (GN=:GN_1 or GN=:GN_2)
     union all
     SELECT SUM(BETRAG) from buchzahl
     where ARTOP=:POS and BNR IN (select bnr from buchung where onrhaben=:ONR and khaben=:KNR and ARTOP=0 and WDatum<:DTVON  and (GN=:GN_1 or GN=:GN_2))
     INTO :SUM_TEMP
     DO
      BEGIN
       IF (SUM_TEMP IS NOT NULL) THEN
        BETRAG_BEZ=BETRAG_BEZ+SUM_TEMP;
      END
     /* ZAHLUNG SOLL - */
     FOR SELECT SUM(BETRAG) from buchung
     where ONRSOLL=:ONR and KSOLL=:KNR and ARTOP=:POS and WDatum<:DTVON and (GN=:GN_1 or GN=:GN_2)
     union all
     SELECT SUM(BETRAG) from buchzahl
     where ARTOP=:POS and BNR IN (select bnr from buchung where onrsoll=:ONR and ksoll=:KNR and ARTOP=0 and WDatum<:DTVON and (GN=:GN_1 or GN=:GN_2))
     INTO :SUM_TEMP
     DO
      BEGIN
       IF (SUM_TEMP IS NOT NULL) THEN
        BETRAG_BEZ=BETRAG_BEZ-SUM_TEMP;
      END
    END /* W-Datum */
   /* ERGEBNIS */
   BETRAG=:BETRAG_BEZ-:BETRAG_SOLL;
   SUSPEND;
  END  /*Vortrag */
END
