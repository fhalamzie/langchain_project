-- Prozedur: RUECKLAGEN_GESAMT_ABR
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE RUECKLAGEN_GESAMT_ABR
DECLARE VARIABLE SUM_IST NUMERIC(18, 2);
DECLARE VARIABLE NETTO NUMERIC(18, 2);
DECLARE VARIABLE SUM_SOLL NUMERIC(18, 2);
DECLARE VARIABLE SUM_RLP NUMERIC(18, 2);
DECLARE VARIABLE ERST_DATUM DATE;
DECLARE VARIABLE DTVON_MINUS_1_TAG DATE;
BEGIN

/* TEMP 
IONR=7;
KNR_VZ=60110;
KNR_RLP=840;
DTVON='1.1.2018';
DTBIS='31.12.2018';
WDATUM='N'; 
 TEMP */

ERST_DATUM='01.01.1900';
DTVON_MINUS_1_TAG = :DTVON -1;
ONR = :IONR;
EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR,:KNR_RLP, :DTVON, 'J','N') RETURNING_VALUES :SUM_RLP;
/* Saldenliste von Anfang bis DTVON -1 */
select * from EIGVZ_ZPOS_GES (:ONR,:ERST_DATUM, :DTVON_MINUS_1_TAG, 'N', :KNR_VZ - 60000, :WDATUM) into :SUM_SOLL, NETTO;  /* ISTVZ = N */ 
IF (SUM_SOLL IS NULL) then
 SUM_SOLL = 0;
select * from EIGVZ_ZPOS_GES (:ONR,:ERST_DATUM, :DTVON_MINUS_1_TAG, 'J', :KNR_VZ - 60000, :WDATUM) into :SUM_IST, NETTO;  /* ISTVZ = J */  
IF (SUM_IST IS NULL) then
 SUM_IST = 0;   
/*
   ANFSTAND_SOLL = alle Sollstellungen aller EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer laut Saldenliste
                   zzgl. alle Buchungen auf dem 840er Konto
*/
AB_SOLL_GES = :SUM_SOLL + :SUM_RLP;
/*
  ANFSTAND_IST  = alle Zahlungen der EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r diese RL-Position aus Saldenliste  +  EB-Wert 
*/
AB_IST_GES = :SUM_IST + :SUM_RLP;
AB_RUECKSTAND_GES = AB_SOLL_GES - AB_IST_GES;
/*
  ZUF_SOLL   
  ZUF_IST  =  alle Buchungen der Eigentuemer fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r diese RL-Position aus Saldenliste
*/
select * from EIGVZ_ZPOS_GES (:ONR,:DTVON, :DTBIS, 'N', :KNR_VZ - 60000, :WDATUM) into :ZUF_SOLL_GES, NETTO;  /* ISTVZ = N */ 
IF (ZUF_SOLL_GES IS NULL) then
 ZUF_SOLL_GES = 0;
select * from EIGVZ_ZPOS_GES (:ONR,:DTVON, :DTBIS, 'J', :KNR_VZ - 60000, :WDATUM) into :ZUF_IST_GES, NETTO;  /* ISTVZ = J */  
IF (ZUF_IST_GES IS NULL) then
 ZUF_IST_GES = 0;
ZUF_RUECKSTAND_GES = ZUF_SOLL_GES - ZUF_IST_GES; 
SUSPEND;
END
