-- Prozedur: RUECKL_KONTROLL
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE RUECKL_KONTROLL
DECLARE VARIABLE LBNR INTEGER;
DECLARE VARIABLE OPBETRAG NUMERIC(18, 2);
DECLARE VARIABLE DTWVON DATE;
DECLARE VARIABLE DTWBIS DATE;
DECLARE VARIABLE DTTEMPVON DATE;
DECLARE VARIABLE DTTEMPBIS DATE;
DECLARE VARIABLE KENTN INTEGER;
DECLARE VARIABLE KSONDERZUF INTEGER;
DECLARE VARIABLE KSONDERENTN INTEGER;
DECLARE VARIABLE KNRP INTEGER;
DECLARE VARIABLE KNRA INTEGER;
DECLARE VARIABLE RUECKPOSNR INTEGER;
BEGIN

  /* ART = 0 im WIPL */
  /* ART = 1 Nachzahlungen */
  /* ART = 2 Abgrenzung */
  
  /* SOLL_IST 1=SOLLstellungen, 
              2=IST Zahlungen, 
              3=beides */

 /* TEMP 
  ONR = 998;
  KNRVON = 200100;
  KNRBIS = 299999;
  DTVON = '1.1.2020';
  DTBIS = '31.12.2020';
  ZPOS=110;
  SOLL_IST=3; 
  ISTVZ_WDATUM = 'J'; */
  
  if (ISTVZ_WDATUM = 'N') THEN
   BEGIN
    DTWVON='1.1.0001';
    DTWBIS='31.12.9999';
    DTTEMPVON=DTVON; 
    DTTEMPBIS=DTBIS;
   END
  ELSE
   BEGIN /* nach WDATUM auswerten */
    DTWVON=DTVON;
    DTWBIS=DTBIS;
    DTTEMPVON='1.1.0001';
    DTTEMPBIS='31.12.9999';
   END 

   /* Im Abrechnungszeitraum = ART =0 */  
   for select BETRAG_RL, BNR, BETRAG_RL_OFFEN  
   from RUECKL_KONTROLL_DETAIL(:ONR,:KNRVON,:KNRBIS,:DTTEMPVON,:DTTEMPBIS,:DTWVON, :DTWBIS, :ZPOS, :SOLL_IST,0,:ISTVZ_WDATUM) 
   into BETRAG_RL, BNR, BETRAG_RL_OFFEN 
   DO
    BEGIN
     ART =0;  /* im Abrechnungszeitraum */
     select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung where BNR=:BNR 
      INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN;
     IF (OPBETRAG IS NOT NULL) THEN
      BEGIN
       /* GESAMTBETRAG aktualisieren */
       SELECT BETRAG from SPLITBUCH where BNR=:BNR
       INTO 
        BETRAG_GES;
       BEMERKUNG='SOLL';
       ISOP = 1;
      end
     ELSE
      BEGIN
       ISOP =0; 
       BEMERKUNG='IST';
      END 
     SUSPEND;
    END 
    
 /* ABGRENZUNGEN */   
 if (ISTVZ_WDATUM = 'J') THEN  
  begin
   /* SOLL_IST = 2;  Abgrenzungen sind nur IST-Zahlungen */
   /* 
   /* WDATUM < Abrechnungszeitraum = Nachzahlungen, BDATUM im Abrechnungszeitraum   */ 
   /*       */  
   ART =1;  /* Nachzahlung */
   for select BETRAG_RL, BNR, BETRAG_RL_OFFEN  
   from RUECKL_KONTROLL_DETAIL(:ONR,:KNRVON,:KNRBIS,:DTVON,:DTBIS, '01.01.0001', :DTVON-1, :ZPOS, 2,:ART,:ISTVZ_WDATUM) 
   into BETRAG_RL, BNR, BETRAG_RL_OFFEN 
   DO
    BEGIN
     select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung where BNR=:BNR 
      INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN;
     ISOP=0; 
     BEMERKUNG='IST';
     SUSPEND;
    END   
   /* 
   /* WDATUM < Abrechnungszeitraum = Nachzahlungen, BDATUM > DTBIS   */ 
   /*                                                */
   ART =1;  /* Nachzahlung */
   for select BETRAG_RL, BNR, BETRAG_RL_OFFEN  
   from RUECKL_KONTROLL_DETAIL(:ONR,:KNRVON,:KNRBIS,:DTBIS+1,'31.12.9999', '01.01.0001', :DTVON-1, :ZPOS, 2,:ART,:ISTVZ_WDATUM) 
   into BETRAG_RL, BNR, BETRAG_RL_OFFEN 
   DO
    BEGIN
     select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung where BNR=:BNR 
      INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN;
     ISOP=0; 
     BEMERKUNG='IST';
     SUSPEND;
    END  
   /* 
   /* WDATUM > Abrechnungszeitraum d.h. im Abrechnungszeitraum fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤chstes Jahr schon erhalten   */ 
   /*                              */
   ART =2;  /* Abgrenzung */
   for select BETRAG_RL, BNR, BETRAG_RL_OFFEN  
   from RUECKL_KONTROLL_DETAIL(:ONR,:KNRVON,:KNRBIS,:DTVON,:DTBIS, :DTBIS+1, '31.12.9999', :ZPOS, 2,:ART,:ISTVZ_WDATUM) 
   into BETRAG_RL, BNR, BETRAG_RL_OFFEN 
   DO
    BEGIN
     select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung where BNR=:BNR 
      INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN;
     ISOP=0; 
     BEMERKUNG='IST';
     SUSPEND;
    END  
   /* 
   /* BDATUM < Abrechnungszeitraum, W-DATUM im Abrechnungszeitraum  */ 
   /*                              */
  ART =2;  /* Abgrenzung - */
  for select BETRAG_RL, BNR, BETRAG_RL_OFFEN  
   from RUECKL_KONTROLL_DETAIL(:ONR,:KNRVON,:KNRBIS,'01.01.0001',:DTVON-1, :DTVON, :DTBIS, :ZPOS, 2,:ART,:ISTVZ_WDATUM) 
   into BETRAG_RL, BNR, BETRAG_RL_OFFEN 
   DO
    BEGIN
     select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung where BNR=:BNR 
      INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN;
     ISOP=0; 
     BEMERKUNG='IST';
     BETRAG_GES = - BETRAG_GES;
     BETRAG_RL = - BETRAG_RL;   
     SUSPEND;
    END 
   /* 
   /* BDATUM > Abrechnungszeitraum, W-DATUM im Abrechnungszeitraum oder davor  */ 
   /*                              */
  ART =2;  /* Abgrenzung -  */
  for select BETRAG_RL, BNR, BETRAG_RL_OFFEN  
   from RUECKL_KONTROLL_DETAIL(:ONR,:KNRVON,:KNRBIS,:DTBIS+1,'31.12.9999', '01.01.0001', :DTBIS, :ZPOS, 2,:ART,:ISTVZ_WDATUM) 
   into BETRAG_RL, BNR, BETRAG_RL_OFFEN 
   DO
    BEGIN
     select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung where BNR=:BNR 
      INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN;
     ISOP=0; 
     BEMERKUNG='IST';
     BETRAG_GES = - BETRAG_GES;
     BETRAG_RL = - BETRAG_RL;     
     SUSPEND;
    END 
    
   /* ABGRENZUNGEN KZUF, KENTN, KSONDERZUF...*/
   select KENTN,KSONDERZUF,KSONDERENTN,KNRP, NR from rueckpos where KONTO_VZ = 60000 + :ZPOS and ONR=:ONR
    into :KENTN,:KSONDERZUF,:KSONDERENTN,:KNRP, :RUECKPOSNR;   
   /* ABGRENZUNG + fuer KENTN und KSONDERENT */ 
   for select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung 
   where ONRSOLL=:ONR and (KHABEN = :KENTN OR KHABEN = :KSONDERENTN) and KSOLL = :KNRP 
   and (WDatum<:DTVON or WDatum>:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS) and ARTOP IS NULL
   INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN
    DO
     BEGIN
      ISOP=0; 
      BETRAG_RL = BETRAG_GES;
      BETRAG_GES = - BETRAG_GES;
      BETRAG_RL = - BETRAG_RL;   
      BEMERKUNG='IST';
      IF (SOLL_IST>1) THEN
       SUSPEND;     
      BEMERKUNG='SOLL';
      ISOP=1;
      IF (SOLL_IST=1 or SOLL_IST=3) THEN
       SUSPEND;     
     END
   /*  
   /* ABGRENZUNG - fuer KENTN und KSONDERENT */    
   /*                                        */
   for select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung 
   where ONRSOLL=:ONR and (KHABEN = :KENTN OR KHABEN = :KSONDERENTN) and KSOLL = :KNRP 
   and (Datum<:DTVON or Datum>:DTBIS) and (WDatum>=:DTVON and WDatum<=:DTBIS) and ARTOP IS NULL
   INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN
    DO
     BEGIN
      ISOP=0; 
      BETRAG_RL = BETRAG_GES;
     /* BETRAG_GES = - BETRAG_GES;
      BETRAG_RL = - BETRAG_RL;     */
      BEMERKUNG='IST';
      IF (SOLL_IST>1) THEN
       SUSPEND;     
      BEMERKUNG='SOLL';
      ISOP=1;
      IF (SOLL_IST=1 or SOLL_IST=3) THEN
       SUSPEND;     
     END
   /* ABGRENZUNG + fuer KSONDERZUF */ 
   for select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung 
   where ONRSOLL=:ONR and (KSOLL = :KSONDERZUF OR KSOLL = :KSONDERZUF) and KHABEN = :KNRP 
   and (WDatum<:DTVON or WDatum>:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS) and ARTOP IS NULL
   INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN
    DO
     BEGIN
      ISOP=0;
      BETRAG_RL = BETRAG_GES; 
      BEMERKUNG='IST';
      IF (SOLL_IST>1) THEN
       SUSPEND;     
      BEMERKUNG='SOLL';
      ISOP=1;
      IF (SOLL_IST=1 or SOLL_IST=3) THEN      
       SUSPEND;     
     END
   /* ABGRENZUNG - fuer KSONDERZUF */    
   for select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung 
   where ONRSOLL=:ONR and (KSOLL = :KSONDERZUF OR KSOLL = :KSONDERZUF) and KHABEN = :KNRP 
   and (Datum<:DTVON or Datum>:DTBIS) and (WDatum>=:DTVON and WDatum<=:DTBIS) and ARTOP IS NULL
   INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN
    DO
     BEGIN
      ISOP=0; 
      BETRAG_RL = BETRAG_GES;
      BETRAG_GES = - BETRAG_GES;
      BETRAG_RL = - BETRAG_RL;     
      BEMERKUNG='IST';
      IF (SOLL_IST>1) THEN
       SUSPEND;     
      BEMERKUNG='SOLL';
      ISOP=1;
      IF (SOLL_IST=1 or SOLL_IST=3) THEN
       SUSPEND;     
     END     
   
   /*                                        */  
   /* ABGRENZUNGEN ZINSEN, ZAST, SOLI...     */  
   /*                                        */
   for select KNR from rueckbkt where RUECKPOS=:RUECKPOSNR
   INTO :KNRA DO
    BEGIN
     /* + */
     for select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung
                   where onrsoll=:ONR and ksoll=:KNRA and khaben=:KNRP
                   and (WDatum<:DTVON or WDatum>:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS)
      INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN                   
     DO
      BEGIN
       ISOP=0; 
       BETRAG_RL = BETRAG_GES;
       BEMERKUNG='IST';
       IF (SOLL_IST>1) THEN
        SUSPEND;     
       BEMERKUNG='SOLL';
       ISOP=1;
       IF (SOLL_IST=1 or SOLL_IST=3) THEN
        SUSPEND;     
      END       
     /* - */
     for select DATUM, WDATUM, TEXT, BELEGNR, BETRAG, OPBETRAG, GN, KSOLL, KHABEN from buchung
                   where onrsoll=:ONR and ksoll=:KNRA and khaben=:KNRP
                   and (Datum<:DTVON or Datum>:DTBIS) and (WDatum>=:DTVON and WDatum<=:DTBIS)
      INTO :DATUM, :WDATUM, :TEXT, :BELEGNR, :BETRAG_GES, :OPBETRAG, :GN, :KSOLL, :KHABEN                   
     DO
      BEGIN
       ISOP=0; 
       BETRAG_RL = BETRAG_GES;
       BETRAG_GES = - BETRAG_GES;
       BETRAG_RL = - BETRAG_RL; 
       BEMERKUNG='IST';
       IF (SOLL_IST>1) THEN
        SUSPEND;     
       BEMERKUNG='SOLL';
       ISOP=1;
       IF (SOLL_IST=1 or SOLL_IST=3) THEN
        SUSPEND;     
      END       
      
      
  END    
      
             
    
  end /* abgrenzungen */
   

   

END
