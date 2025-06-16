-- Prozedur: GET_HAUSLIST
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE GET_HAUSLIST
BEGIN
 IF (IGKONTO=-1) THEN
  BEGIN
   IF (IVERWNR=-1) THEN
    BEGIN
     FOR
      SELECT ONR, OBEZ, OSTRASSE, OPLZORT, ARCHIVIERT FROM OBJEKTE WHERE ONR>0 ORDER BY ONR
     INTO ONR, OBEZ, OSTRASSE, OPLZORT, ARCHIVIERT
     DO
      BEGIN
       SUSPEND;
      END
    END
   ELSE
    BEGIN
     FOR
      SELECT ONR, OBEZ, OSTRASSE, OPLZORT, ARCHIVIERT FROM OBJEKTE WHERE ONR>0 AND VERWNR=:IVERWNR ORDER BY ONR
     INTO ONR, OBEZ, OSTRASSE, OPLZORT, ARCHIVIERT
     DO
      BEGIN
       SUSPEND;
      END
    END
  END
 ELSE
  BEGIN  /* HÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤user fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r ein bestimmtes Bankkonto */
   FOR
    SELECT ONR, OBEZ, OSTRASSE, OPLZORT, ARCHIVIERT FROM OBJEKTE WHERE ONR IN(select ONR from objbanken where BANKNR=:IGKONTO) ORDER BY ONR
   INTO ONR, OBEZ, OSTRASSE, OPLZORT, ARCHIVIERT
   DO
    BEGIN
     SUSPEND;
    END
  END
END
