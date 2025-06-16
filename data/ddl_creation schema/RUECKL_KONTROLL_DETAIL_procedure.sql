-- Prozedur: RUECKL_KONTROLL_DETAIL
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE RUECKL_KONTROLL_DETAIL
DECLARE VARIABLE KSOLL NUMERIC(18, 2);
DECLARE VARIABLE ARTHABEN INTEGER;
DECLARE VARIABLE DTABRVON DATE;
DECLARE VARIABLE DTABRBIS DATE;
BEGIN

 /* SOLL_IST 1=SOLL,
             2=IST, 
             3=SOLL und IST */
 
  /* ART = 0 im WIPL */
  /* ART = 1 Nachzahlungen */
  /* ART = 2 Abgrenzung */

 /* TEMP 
  ONR = 998;
  KNRVON = 200100;
  KNRBIS = 209900;
  DTVON = '1.1.0001';
  DTBIS = '31.12.9999';
  DTWVON = '1.1.2019';
  DTWBIS = '31.12.2019';
  ZPOS=110;
  SOLL_IST=3; 
  ART = 0; */
 /* 
 /* Berechnung 
 */
 
   /*
   /* SOLL
   /*                      */
   IF ((SOLL_IST = 1 OR SOLL_IST = 3) AND (ART=0))  THEN
    BEGIN
    /* Sollstellungen KHABEN = VZART  BNR = OPNR nach BDATUM!*/
    if (ISTVZ_WDATUM = 'N') THEN
     BEGIN
      DTABRVON=DTVON; 
      DTABRBIS=DTBIS;
     END
    ELSE
     BEGIN /* nach WDATUM auswerten */
      DTABRVON=DTWVON;
      DTABRBIS=DTWBIS;
     END 
     for
      select OPNR, BETRAG, OPBETRAG from buchung
      where ((onrsoll=:onr) or (onrhaben=:onr)) 
       and (ksoll>=:knrvon and ksoll <= :knrbis)  
       AND (Datum >= :DTABRVON and Datum <= :DTABRBIS) 
      and Betrag<>0 and opbetrag is not null
      and  ARTHABEN = :ZPOS     
      into :BNR, :BETRAG_RL, BETRAG_RL_OFFEN
       DO
        begin
          SUSPEND;
        end
      END  
      
   /*   
   /* ZAHLUNGEN SPLIT */    
   /*                 */
   IF (SOLL_IST = 2 OR SOLL_IST = 3)  THEN
    BEGIN  
     for
      select buchung.BNR, buchzahl.BETRAG, KSOLL from buchung,buchzahl
      where (buchzahl.bnr=buchung.bnr) and ((onrsoll=:ONR) or (onrhaben=:ONR)) and  
      ((ksoll>=:knrvon and ksoll<=:knrbis) or (khaben>=:knrvon and khaben<=:knrbis)) 
       AND (Datum >= :DTVON and Datum <= :DTBIS) AND (WDATUM>=:DTWVON and WDatum <= :DTWBIS) 
       and buchzahl.Betrag<>0
      and  buchzahl.artop = :ZPOS     
      into :BNR, :BETRAG_RL, :KSOLL
       DO
        begin
         if (ksoll>=:knrvon and ksoll<=:knrbis) then
          BETRAG_RL = - BETRAG_RL;
         BETRAG_RL_OFFEN = 0;
         SUSPEND;
        end    
      /* ZAHLUNGEN KEIN SPLIT */    
      for select BNR, BETRAG, KSOLL from buchung
      where ((onrsoll=:onr) or (onrhaben=:onr)) and  ((ksoll>=:knrvon and ksoll<=:knrbis) or (khaben>=:knrvon and khaben<=:knrbis))
       AND (Datum >= :DTVON and Datum <= :DTBIS) AND (WDATUM>=:DTWVON and WDatum <= :DTWBIS) 
       and Betrag<>0 and opbetrag is null and splitnr is null and artop is not null and artop<>0 
      and  artop = :ZPOS     
      into :BNR, :BETRAG_RL,:KSOLL
       DO
        begin
         if (ksoll>=:knrvon and ksoll<=:knrbis) then
          BETRAG_RL = - BETRAG_RL;
         BETRAG_RL_OFFEN = 0;          
         SUSPEND;
        end   
    END 
END
