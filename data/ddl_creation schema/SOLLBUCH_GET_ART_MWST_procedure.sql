-- Prozedur: SOLLBUCH_GET_ART_MWST
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE SOLLBUCH_GET_ART_MWST
DECLARE VARIABLE MWSTAUS CHAR(1);
 DECLARE VARIABLE MWSTS INTEGER;
BEGIN
  /* HOLT ILASTSCHR, MWST und GKONTO FÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“R SOLLSTELLUNGS-BUCHUNG */
  /* ZUERST GKONTO */
  IF (IKNR<200000) THEN
   SELECT LEVBankNR FROM objekte
   WHERE ONR=:IONR
   INTO :GKONTO;
  ELSE
   SELECT LEVBankNR2 FROM objekte
   WHERE ONR=:IONR
   INTO :GKONTO;
  IF (IKNR<200000) THEN
   SELECT BLASTJA, BMWSTAUSW, BMWSTSATZ FROM bewohner
   WHERE ONR=:IONR and KNR=:IKNR
   INTO :ISLASTSCHR, :ISGEWERBLICH, :MWSTSATZ;
  ELSE  /* EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer */
   SELECT ELASTJA, EMWSTAUSW, EMWSTSATZ FROM eigentuemer
    WHERE ONR=:IONR and KNR=:IKNR
    INTO :ISLASTSCHR, :ISGEWERBLICH, :MWSTSATZ;
 SUSPEND;
END
