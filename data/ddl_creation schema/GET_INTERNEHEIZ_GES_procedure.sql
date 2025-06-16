-- Prozedur: GET_INTERNEHEIZ_GES
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE GET_INTERNEHEIZ_GES
DECLARE VARIABLE IKNR INTEGER;
 DECLARE VARIABLE ICOUNTSOLL INTEGER;
 DECLARE VARIABLE ICOUNTHABEN INTEGER;
BEGIN
  /* Procedure body */
  MITTANK=BMITTANK;
  FOR select KNR, KBEZ, BHEIZ, IHEIZK from konten
  where ONR=:IONR
  and (IHeizK > 0 or BHEIZ = 'J') order by BHEIZ,IHEIZK
  INTO IKNR, KBEZ, BHEIZ, IHEIZK DO
   BEGIN
    ICOUNTSOLL=0;
    ICOUNTHABEN=0;
    IF (BHEIZ='J') THEN
     SHEIZK='Brennstoffkosten';
    ELSE
     IF (IHEIZK=1) THEN
      SHEIZK='Heiznebenkosten';
     ELSE
      IF (IHEIZK=2) THEN
       SHEIZK='Zusatzkosten Heizung';
      ELSE
       IF (IHEIZK=3) THEN
        SHEIZK='Zusatzkosten Warmwasser';
       ELSE
        IF (IHEIZK=4) THEN
         SHEIZK='Kalt- und Abwasser';
        ELSE
         IF (IHEIZK=5) THEN
          SHEIZK='NutzerwechselgebÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hr'; 
    /* SOLL */
    FOR SELECT Text, Datum, BrennstMenge, Betrag from buchung
    where ONRSOLL=:IONR and KSOLL=:IKNR and WDATUM>=:DTVON and WDatum<=:DTBIS
    order by WDatum
    into TEXT, DATUM, BRENNSTMENGE, BETRAG
     DO
      BEGIN
       IF (BHEIZ='J') THEN
        ICOUNTSOLL=ICOUNTSOLL+1;
       SUSPEND;
      END
    /* HABEN */
    FOR SELECT Text, Datum, BrennstMenge, Betrag from buchung
    where ONRHABEN=:IONR and KHABEN=:IKNR and WDATUM>=:DTVON and WDatum<=:DTBIS
    order by WDatum    
    into TEXT, DATUM, BRENNSTMENGE, BETRAG
     DO
      BEGIN
       IF (BHEIZ='J') THEN
        ICOUNTHABEN=ICOUNTHABEN+1;
       BETRAG=-BETRAG;
       SUSPEND;
      END
    IF (BHEIZ='J') THEN
     BEGIN
      IF ((ICOUNTSOLL=0) and (ICOUNTHABEN=0)) then
       BEGIN
        TEXT=NULL;
        DATUM=NULL;
        BRENNSTMENGE=NULL;
        BETRAG=NULL;
        SUSPEND;
       END
     END
   END 
END
