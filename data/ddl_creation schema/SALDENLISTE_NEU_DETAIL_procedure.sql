-- Prozedur: SALDENLISTE_NEU_DETAIL
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE SALDENLISTE_NEU_DETAIL
DECLARE VARIABLE KKLASSE INTEGER;
DECLARE VARIABLE SUMSOLL NUMERIC(15, 2);
DECLARE VARIABLE SUMHABEN NUMERIC(15, 2);
DECLARE VARIABLE SUMSOLL_NETTO NUMERIC(15, 2);
DECLARE VARIABLE SUMHABEN_NETTO NUMERIC(15, 2);
DECLARE VARIABLE DTVONBDATUM DATE;
DECLARE VARIABLE DTBISBDATUM DATE;
DECLARE VARIABLE DTVONWDATUM DATE;
DECLARE VARIABLE DTBISWDATUM DATE;
DECLARE VARIABLE VONKTO INTEGER;
DECLARE VARIABLE BISKTO INTEGER;
BEGIN

/* muss mit 
   select SUM(SUM_VZ) as SUM_VZ, SUM(SUM_VZ_NETTO),KNR,VZPOS,GN from SALDENLISTE_NEU(....)   
   group by KNR, VZPOS, GN 
   aufgerufen werden */

/* TEMP 
  IONR = 7;
  DTVON = '1.1.2018';
  DTBIS = '31.12.2018';
  BISTVZ = 'N';
  BBEW= 'N';
  WDATUM = 'J';
  TEMP */

 /* W_Datum abfragen */
 if (WDATUM = 'N') then
  begin
   DTVONBDATUM = DTVON;
   DTBISBDATUM = DTBIS;
   DTVONWDATUM = '01.01.1980';
   DTBISWDATUM = '01.01.1980';
  end
 else
  begin
   DTVONBDATUM = '01.01.1980';
   DTBISBDATUM = '01.01.1980';
   DTVONWDATUM = DTVON;
   DTBISWDATUM = DTBIS;
  end
 if (BBEW  = 'J') then  
  BEGIN
   VONKTO = 100000;
   BISKTO = 199999;
  END
 if (BBEW  = 'N') then  
  BEGIN
   VONKTO = 200000;
   BISKTO = 299999;
  END
 IF (BISTVZ='J') THEN
  BEGIN
   /*            */
   /* KEIN SPLIT */
   /*            */
   /* SOLL */
   FOR SELECT -sum(betrag), -SUM((BETRAG*100) / (100+MWSTOP)), KSOLL, KNROP, GN from buchung 
   WHERE ONRSOLL=:IONR 
   AND (KSOLL>:VONKTO AND KSOLL<=:BISKTO)
   AND ARTOP <> 0   /* kein SPLIT */
   AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
   GROUP BY KSOLL, KNROP, GN
   having sum(betrag) <> 0
   INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
   DO 
     begin
      SUM_VZ = -:SUM_VZ;
      SUM_VZ_NETTO = - :SUM_VZ;     
      SUSPEND;
    end
   /* HABEN */
   FOR SELECT SUM(BETRAG), SUM((BETRAG*100) / (100+MWSTOP)), KHABEN, KNROP, GN from buchung
   WHERE ONRHABEN=:IONR 
   AND (KHABEN>:VONKTO AND KHABEN<=:BISKTO)
   AND ARTOP <> 0   /* kein SPLIT */
   AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
   GROUP BY KHABEN, KNROP, GN
   having sum(betrag) <> 0
   INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
   DO 
    SUSPEND;
   /*            */
   /*   SPLIT    */
   /*            */
   /* SOLL */
   for select -Sum(buchzahl.Betrag), -SUM((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP)), KSOLL, buchzahl.KNR, GN from buchung, buchzahl
   where  ONRSOLL=:IONR 
   AND (KSOLL>:VONKTO and KSOLL<=:BISKTO)
   AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
   and buchung.artop=0
   and buchung.bnr=buchzahl.bnr
   GROUP BY KSOLL, buchzahl.KNR, GN
   having sum(buchzahl.betrag) <> 0
   INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
   DO 
    begin
     SUM_VZ = -:SUM_VZ;
     SUM_VZ_NETTO = -:SUM_VZ;     
     SUSPEND;
    end 
   /* Haben */
   for select Sum(buchzahl.Betrag), SUM((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP)), KHABEN, buchzahl.KNR, GN from buchung, buchzahl
   where  ONRHABEN=:IONR AND KHABEN>:VONKTO and KHABEN<=:BISKTO
   AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
   and buchung.artop=0
   and buchung.bnr=buchzahl.bnr
   GROUP BY KHABEN, buchzahl.KNR, GN
   having sum(buchzahl.betrag) <> 0   
   INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
   DO
    SUSPEND;   
   END
 ELSE
  BEGIN
   /* SOLL VZ */
   for SELECT SUM(BETRAG), SUM((BETRAG*100) / (100+MWST)), KSOLL, KHABEN, GN from buchung
   WHERE ONRSOLL=:IONR AND ONRHABEN=:IONR
   AND OPNR IS NOT NULL and OPBETRAG IS NOT NULL 
   AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
   AND (KSOLL>:VONKTO and KSOLL<=:BISKTO)
   GROUP BY KSOLL, KHABEN, GN
   having sum(betrag) <> 0
   INTO  :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
   do
    SUSPEND;
   /* HABEN */
   for SELECT SUM(BETRAG), SUM((BETRAG*100) / (100+MWST)), KHABEN, KSOLL, GN from buchung
   WHERE (ONRHABEN=:IONR AND ONRSOLL=:IONR)
   AND OPNR IS NOT NULL and OPBETRAG IS NOT NULL 
   AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
   AND (KHABEN>:VONKTO and KHABEN<=:BISKTO)
   GROUP BY KHABEN, KSOLL, GN
   having sum(betrag) <> 0
   INTO  :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
   do
    SUSPEND;
  END    /* SOLL VZ */
END
