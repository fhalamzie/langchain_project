-- Prozedur: GET_RUECKL_BUCHUNGEN
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE GET_RUECKL_BUCHUNGEN
BEGIN

/*TEMP 
IONR=998;
IKNR=840;
DVON = '1.1.2018';
DBIS = '31.12.2018';
ISWDATUM = 0;
KZUF = 30000;
RZUF = 10000;
*/


  /* WDATUM */
  IF (ISWDATUM=1) THEN
   BEGIN
    /* HABEN */
    FOR SELECT ONRHABEN, KHABEN, KSTRHABEN, WDATUM, TEXT, Betrag from buchung
    where ONRHABEN=:IONR and KHABEN=:IKNR and (WDATUM>=:DVON and WDATUM<=:DBIS) and KSOLL<>:KZUF
    order by WDATUM
    INTO ONR, KONTO, KONTOSTR, DATUM, TEXT, BETRAG
    DO
     BEGIN
      ZUF=1;
      SUSPEND;
     END
    /* SOLL */
    FOR SELECT ONRSOLL, KSOLL, KSTRSOLL, WDATUM, TEXT, Betrag from buchung
    where ONRSOLL=:IONR and KSOLL=:IKNR and (WDATUM>=:DVON and WDATUM<=:DBIS) and KHABEN<>:KZUF
    order by WDATUM
    INTO ONR, KONTO, KONTOSTR, DATUM, TEXT, BETRAG
    DO
     BEGIN
      ZUF=2;
      SUSPEND;
     END
   END
  ELSE
   BEGIN  /* DATUM */
    /* HABEN */
    FOR SELECT ONRHABEN, KHABEN, KSTRHABEN, DATUM, TEXT, Betrag from buchung
    where ONRHABEN=:IONR and KHABEN=:IKNR and (DATUM>=:DVON and DATUM<=:DBIS) and KSOLL<>:KZUF
    order by DATUM
    INTO ONR, KONTO, KONTOSTR, DATUM, TEXT, BETRAG
    DO
     BEGIN
      ZUF=1;
      SUSPEND;
     END
    /* SOLL */
    FOR SELECT ONRSOLL, KSOLL, KSTRSOLL, DATUM, TEXT, Betrag from buchung
    where ONRSOLL=:IONR and KSOLL=:IKNR and (DATUM>=:DVON and DATUM<=:DBIS) and KHABEN<>:KZUF
    order by WDATUM
    INTO ONR, KONTO, KONTOSTR, DATUM, TEXT, BETRAG
    DO
     BEGIN
      ZUF=2;
      SUSPEND;
     END
   END
  /* Bereits berechnete ZUF der Eigentuemer */ 
  ONR=:IONR;
  KONTO=:IKNR;
/*  KONTOSTR='RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagenkonto'; */
  DATUM=:DBIS;
  TEXT = 'IST-ZufÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung (Zahlungen aller EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer lt. Wirtschaftsplan)'; 
  BETRAG =:RZUF;
  ZUF=1;
  SUSPEND;
 END
