-- Prozedur: BERECHNE_MAHNLISTE
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE BERECHNE_MAHNLISTE
DECLARE VARIABLE RSOLL NUMERIC(15,2);
 DECLARE VARIABLE IKNR integer;
 DECLARE VARIABLE IONR integer;
 DECLARE VARIABLE IHAUSTYP integer;
 DECLARE VARIABLE IKNRVON integer;
 DECLARE VARIABLE IKNRBIS integer;
BEGIN
 /* ERST MAL OPBETRAG berechnen */
 FOR
  select ONR, BSONST from objekte
  where (ONR>=:ONRVON and ONR<=:ONRBIS)
  into :IONR, :IHAUSTYP
 DO
  BEGIN
   IF (IHAUSTYP=0) THEN
    BEGIN
     IKNRVON=100000;
     IKNRBIS=199999;
    END
   ELSE
    IF (IHAUSTYP=1) THEN
     BEGIN
      IKNRVON=200000;
      IKNRBIS=300000;
     END
    ELSE
     IF (IHAUSTYP=2) THEN
      BEGIN
       IKNRVON=100000;
       IKNRBIS=300000;
      END
   /* KBRUTTO2 zurÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cksetzen, KBRUTTO2 fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle neu berechnen */
   UPDATE KONTEN SET OPBETRAG=0 where ONR=:IONR and KNR>=100000;
   FOR
    select sum(OPBetrag), KSOLL from buchung
    where ONRSOLL=:IONR AND (KSOLL>=:IKNRVON AND KSOLL<=:IKNRBIS)
    and Datum<=:TODAY
    group by KSOLL
    into :RSOLL, :IKNR
   DO
    BEGIN
     IF (RSOLL IS NULL) THEN
      RSOLL=0;
     IF (RSOLL>0) THEN
       BEGIN
        UPDATE KONTEN SET OPBETRAG=:RSOLL where ONR=:IONR and KNR=:IKNR;
        UPDATE KONTEN SET KMAHNSTUFE=1 where ONR=:IONR and KNR=:IKNR AND (KMAHNSTUFE<1 or KMAHNSTUFE IS NULL);
       END
    END
  /* Mahnstufen zurÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cksetzen wenn OPBETRAG = 0 */
  UPDATE KONTEN SET KMAHNSTUFE=0 where ONR=:IONR and (KNR>=:IKNRVON and KNR<=:IKNRBIS) and OPBETRAG<=0;
  /* Mahnsperre? */
  IF (IKNRVON=100000) THEN
   UPDATE KONTEN SET KMAHNSTUFE=0 where ONR=:IONR and KNR IN (select KNR from Bewohner where ONR=:IONR and BMAHNSPERRE='J');
  IF (IKNRBIS=300000) THEN
   UPDATE KONTEN SET KMAHNSTUFE=0 where ONR=:IONR and KNR IN (select KNR from Eigentuemer where ONR=:IONR and EMAHNSPERRE='J');
 END /* Alle HÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤user */
END
