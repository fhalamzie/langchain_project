-- Prozedur: SALDENLISTE_NEU_DETAIL2
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE SALDENLISTE_NEU_DETAIL2
DECLARE VARIABLE DTVONBDATUM DATE;
DECLARE VARIABLE DTBISBDATUM DATE;
DECLARE VARIABLE DTVONWDATUM DATE;
DECLARE VARIABLE DTBISWDATUM DATE;
BEGIN

/* TEMP 

  IONR=7;
  DTVON = '1.1.2018';
  DTBIS = '31.12.2018';
  VONKTO = 200200;
  BISKTO = 200200;
  WDATUM = 'N';       */

 /* W_Datum abfragen */
 if (WDATUM = 'N') then
  begin
   DTVONBDATUM = DTVON;
   DTBISBDATUM = DTBIS;
   DTVONWDATUM = '01.01.0001';
   DTBISWDATUM = '01.01.0001'; 
  end
 else
  begin
   DTVONBDATUM = '01.01.0001';
   DTBISBDATUM = '01.01.0001';
   DTVONWDATUM = DTVON;
   DTBISWDATUM = DTBIS;
  end
  
 /*
 /*  VZ (IST)
 /* 
 /*            */
 /* KEIN SPLIT */
 /*            */
 /* Konto im SOLL */
 FOR SELECT sum(betrag), SUM((BETRAG*100) / (100+MWSTOP)), KSOLL, KNROP, GN from buchung 
 WHERE ONRSOLL=:IONR 
 AND (KSOLL>=:VONKTO AND KSOLL<=:BISKTO)
 AND ARTOP <> 0 and Betrag<>0 and opbetrag is null and splitnr is null and artop is not null   /* kein SPLIT */
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 GROUP BY KSOLL, KNROP, GN
 having sum(betrag) <> 0
 INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
 DO 
   begin
    SUM_VZ = -:SUM_VZ;
    SUM_VZ_NETTO = - :SUM_VZ; 
    SUM_VZ_SOLL =0;
    SUM_VZ_NETTO_SOLL =0;        
    SUSPEND;
  end
 /* HABEN */
 FOR SELECT SUM(BETRAG), SUM((BETRAG*100) / (100+MWSTOP)), KHABEN, KNROP, GN from buchung
 WHERE ONRHABEN=:IONR 
 AND (KHABEN>=:VONKTO AND KHABEN<=:BISKTO)
 AND ARTOP <> 0 and Betrag<>0 and opbetrag is null and splitnr is null and artop is not null   /* kein SPLIT */
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 GROUP BY KHABEN, KNROP, GN
 having sum(betrag) <> 0
 INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
 DO 
  BEGIN
   SUM_VZ_SOLL =0;
   SUM_VZ_NETTO_SOLL =0;  
   SUSPEND;
  END 
 /*            */
 /*   SPLIT    */
 /*            */
 /* KONTO im SOLL */
 for select Sum(buchzahl.Betrag), SUM((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP)), KSOLL, buchzahl.KNR, GN from buchung, buchzahl
 where  ONRSOLL=:IONR 
 AND (KSOLL>=:VONKTO and KSOLL<=:BISKTO)
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 and buchzahl.Betrag<>0
 and buchung.bnr=buchzahl.bnr
 GROUP BY KSOLL, buchzahl.KNR, GN
 having sum(buchzahl.betrag) <> 0
 INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
 DO 
  begin
   SUM_VZ = -:SUM_VZ;
   SUM_VZ_NETTO = -:SUM_VZ; 
   SUM_VZ_SOLL =0;
   SUM_VZ_NETTO_SOLL =0;      
   SUSPEND;
  end 
 /* Konto im Haben */
 for select Sum(buchzahl.Betrag), SUM((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP)), KHABEN, buchzahl.KNR, GN from buchung, buchzahl
 where  ONRHABEN=:IONR 
 AND (KHABEN>=:VONKTO and KHABEN<=:BISKTO)
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 and buchzahl.Betrag<>0
 and buchung.bnr=buchzahl.bnr
 GROUP BY KHABEN, buchzahl.KNR, GN
 having sum(buchzahl.betrag) <> 0   
 INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
 DO
  BEGIN
   SUM_VZ_SOLL =0;
   SUM_VZ_NETTO_SOLL =0;  
   SUSPEND;   
  END 
 /*
  SOLL VZ 
 */
 for SELECT SUM(BETRAG), SUM((BETRAG*100) / (100+MWST)), KSOLL, KHABEN, GN from buchung
 WHERE ONRSOLL=:IONR AND ONRHABEN=:IONR
 AND OPNR IS NOT NULL and OPBETRAG IS NOT NULL 
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 AND (KSOLL>=:VONKTO and KSOLL<=:BISKTO)
 GROUP BY KSOLL, KHABEN, GN
 having sum(betrag) <> 0
 INTO  :SUM_VZ_SOLL, SUM_VZ_NETTO_SOLL, KNR, VZPOS, GN
 do
  BEGIN
   SUM_VZ =0;
   SUM_VZ_NETTO =0;  
   SUSPEND;
  END 
 /* HABEN */
 for SELECT SUM(BETRAG), SUM((BETRAG*100) / (100+MWST)), KHABEN, KSOLL, GN from buchung
 WHERE (ONRHABEN=:IONR AND ONRSOLL=:IONR)
 AND OPNR IS NOT NULL and OPBETRAG IS NOT NULL 
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 AND (KHABEN>=:VONKTO and KHABEN<=:BISKTO)
 GROUP BY KHABEN, KSOLL, GN
 having sum(betrag) <> 0
 INTO  :SUM_VZ_SOLL, SUM_VZ_NETTO_SOLL, KNR, VZPOS, GN
 do
  BEGIN
   SUM_VZ =0;
   SUM_VZ_NETTO =0;  
   SUSPEND;
  END 
  
  
END
