-- Prozedur: VZ_BE_DETAIL
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE VZ_BE_DETAIL
DECLARE VARIABLE DTVONBDATUM DATE;
DECLARE VARIABLE DTBISBDATUM DATE;
DECLARE VARIABLE DTVONWDATUM DATE;
DECLARE VARIABLE DTBISWDATUM DATE;
BEGIN

/* TEMP 
  IONR=998;
  DTVON = '1.1.2019';
  DTBIS = '31.12.2019';
  VONKTO = 200100;
  BISKTO = 209900; 
  WDATUM = 'J'; */
  
 /* W-Datum oder B-Datum */
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
 /*  VZ-IST = Alle Buchungen mit W-Datum im Abrechnungszeitraum
 /* 
 /*            */
 /* KEIN SPLIT */
 /*            */
 FOR SELECT -sum(betrag), -SUM((BETRAG*100) / (100+MWSTOP)), KSOLL, ARTOP, GN from buchung 
 WHERE ONRSOLL=:IONR 
 AND (KSOLL>=:VONKTO AND KSOLL<=:BISKTO)
 AND ARTOP <> 0   /* kein SPLIT */
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 GROUP BY KSOLL, ARTOP, GN
 having sum(betrag) <> 0
 INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
 DO 
   begin
    SUM_VZ = -:SUM_VZ;
    SUM_VZ_NETTO = -:SUM_VZ_NETTO; 
    SUM_VZ_SOLL =0;
    SUM_VZ_NETTO_SOLL =0;        
    SUSPEND;
  end
 /* HABEN */
 FOR SELECT SUM(BETRAG), SUM((BETRAG*100) / (100+MWSTOP)), KHABEN, ARTOP, GN from buchung
 WHERE ONRHABEN=:IONR 
 AND (KHABEN>=:VONKTO AND KHABEN<=:BISKTO)
 AND ARTOP <> 0   /* kein SPLIT */
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 GROUP BY KHABEN, ARTOP, GN
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
 for select -Sum(buchzahl.Betrag), -SUM((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP)), KSOLL, buchzahl.ARTOP, GN from buchung, buchzahl
 where  ONRSOLL=:IONR 
 AND (KSOLL>=:VONKTO and KSOLL<=:BISKTO)
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 and buchung.artop=0
 and buchung.bnr=buchzahl.bnr
 GROUP BY KSOLL, buchzahl.ARTOP, GN
 having sum(buchzahl.betrag) <> 0
 INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
 DO 
  begin
   SUM_VZ = -:SUM_VZ;
   SUM_VZ_NETTO = -:SUM_VZ_NETTO; 
   SUM_VZ_SOLL =0;
   SUM_VZ_NETTO_SOLL =0;      
   SUSPEND;
  end 
 /* Konto im Haben */
 for select Sum(buchzahl.Betrag), SUM((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP)), KHABEN, buchzahl.ARTOP, GN from buchung, buchzahl
 where  ONRHABEN=:IONR 
 AND (KHABEN>=:VONKTO and KHABEN<=:BISKTO)
 AND ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
 and buchung.artop=0
 and buchung.bnr=buchzahl.bnr
 GROUP BY KHABEN, buchzahl.ARTOP, GN
 having sum(buchzahl.betrag) <> 0   
 INTO :SUM_VZ, SUM_VZ_NETTO, KNR, VZPOS, GN
 DO
  BEGIN
   SUM_VZ_SOLL =0;
   SUM_VZ_NETTO_SOLL =0;  
   SUSPEND;   
  END 
 /*
  SOLL VZ NICHT nach WDATUM, immer DATUM!
 */
 for WITH cteB
  AS
  (
  SELECT b.BETRAG, b.MWST, b.KSOLL, b.ARTHABEN, b.GN,
  CASE when b.Datum >= :DTVON 
  then b.Datum
  else ''
  end as Datum
  FROM buchung b
  WHERE b.ONRSOLL = :IONR 
  AND b.ONRHABEN = :IONR
  AND b.OPNR IS NOT NULL
  AND b.OPBETRAG IS NOT NULL
  AND b.Datum <= :DTBIS
  AND b.KSOLL >= :VONKTO
  AND b.KSOLL <= :BISKTO
  )
  SELECT SUM(q.BETRAG), SUM((q.BETRAG * 100) / (100 + q.MWST)), q.KSOLL, q.ARTHABEN, q.GN
  FROM cteB q
  WHERE  q.Datum <> ''
  GROUP BY q.KSOLL, q.ARTHABEN, q.GN
  having sum(q.betrag) <> 0
 INTO  :SUM_VZ_SOLL, SUM_VZ_NETTO_SOLL, KNR, VZPOS, GN
 do
  BEGIN
   SUM_VZ =0;
   SUM_VZ_NETTO =0;  
   SUSPEND;
  END 
 /* HABEN */
 for WITH cteB
  AS
  (
  SELECT b.BETRAG, b.MWST, b.KHABEN, b.ARTSOLL, b.GN,
  CASE when b.Datum >= :DTVON 
  then b.Datum
  else ''
  end as Datum
  FROM buchung b
  WHERE b.ONRSOLL = :IONR 
  AND b.ONRHABEN = :IONR
  AND b.OPNR IS NOT NULL
  AND b.OPBETRAG IS NOT NULL
  AND b.Datum <= :DTBIS
  AND b.KHABEN >= :VONKTO
  AND b.KHABEN <= :BISKTO
  )
  SELECT SUM(q.BETRAG), SUM((q.BETRAG * 100) / (100 + q.MWST)), q.KHABEN, q.ARTSOLL, q.GN
  FROM cteB q
  WHERE  q.Datum <> ''
  GROUP BY q.KHABEN, q.ARTSOLL, q.GN
  having sum(q.betrag) <> 0
 INTO  :SUM_VZ_SOLL, SUM_VZ_NETTO_SOLL, KNR, VZPOS, GN
 do
  BEGIN
   SUM_VZ =0;
   SUM_VZ_NETTO =0;  
   SUSPEND;
  END 
END
