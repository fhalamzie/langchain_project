-- Prozedur: KONTOSALDO_ALT
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE KONTOSALDO_ALT
DECLARE VARIABLE KKLASSE INTEGER;
 DECLARE VARIABLE SUMSOLL NUMERIC(15,2);
 DECLARE VARIABLE SUMHABEN NUMERIC(15,2);
BEGIN
 IF (IKNR=98000 or IKNR=99990) THEN
  BEGIN
   IF (BWDATUM<>'J') THEN
    BEGIN
     SELECT SUM(BETRAG) from buchung
     WHERE ONRSOLL=0 and KSOLL=:IKNR and ONRHABEN=:IONR
     AND Datum<:DTBIS
     INTO :SUMSOLL;
     SELECT SUM(BETRAG) from buchung
     WHERE ONRHABEN=0 and KHABEN=:IKNR and ONRSOLL=:IONR
     AND Datum<:DTBIS
     INTO :SUMHABEN;
    END /* DATUM */
   ELSE
    BEGIN /* WDATUM */
     SELECT SUM(BETRAG) from buchung
     WHERE ONRSOLL=0 and KSOLL=:IKNR and ONRHABEN=:IONR
     AND WDatum<:DTBIS
     INTO :SUMSOLL;
     SELECT SUM(BETRAG) from buchung
     WHERE ONRHABEN=0 and KHABEN=:IKNR and ONRSOLL=:IONR
     AND WDatum<:DTBIS
     INTO :SUMHABEN;
    END /* WDATUM */
   IF (SUMSOLL IS NULL) THEN
    SUMSOLL=0;
   IF (SUMHABEN IS NULL) THEN
    SUMHABEN=0;
   SALDO=SUMSOLL-SUMHABEN;
   SUSPEND;
  END /* 98000, 99990 */
 ELSE
  BEGIN
 select KKLASSE from konten where ONR=:IONR and KNR=:IKNR INTO KKLASSE;
 IF (KKLASSE<60) THEN
  BEGIN
   /*DATUM*/
   IF (BWDATUM<>'J') THEN
    BEGIN
     SELECT SUM(BETRAG) from buchung
     WHERE ONRSOLL=:IONR and KSOLL=:IKNR
     AND Datum<:DTBIS
     INTO :SUMSOLL;
     SELECT SUM(BETRAG) from buchung
     WHERE ONRHABEN=:IONR and KHABEN=:IKNR
     AND Datum<:DTBIS
     INTO :SUMHABEN;
    END
   ELSE
    BEGIN
     SELECT SUM(BETRAG) from buchung
     WHERE ONRSOLL=:IONR and KSOLL=:IKNR
     AND WDatum<:DTBIS
     INTO :SUMSOLL;
     SELECT SUM(BETRAG) from buchung
     WHERE ONRHABEN=:IONR and KHABEN=:IKNR
     AND WDatum<:DTBIS
     INTO :SUMHABEN;
    END
   IF (SUMSOLL IS NULL) THEN
    SUMSOLL=0;
   IF (SUMHABEN IS NULL) THEN
    SUMHABEN=0;
  IF ((KKLASSE>=10 AND KKLASSE<=19) OR KKLASSE=27) THEN
   SALDO=SUMHABEN-SUMSOLL;
  ELSE
   SALDO=SUMSOLL-SUMHABEN;
  SUSPEND;
  END
 ELSE  /* DEB/KRED */
  BEGIN
   /*DATUM*/
   IF (BWDATUM<>'J') THEN
    BEGIN
     IF (BSOLL='J') THEN
      BEGIN /* Sollstelungen */
       SELECT SUM(BETRAG) from buchung
       WHERE ONRSOLL=:IONR and KSOLL=:IKNR
       AND Datum<:DTBIS
       INTO :SUMSOLL;
       SELECT SUM(BETRAG) from buchung
       WHERE ONRHABEN=:IONR and KHABEN=:IKNR
       AND Datum<:DTBIS
       INTO :SUMHABEN;
     END /* Sollstelungen */
    ELSE
     BEGIN /* keine Sollstelungen */
       SELECT SUM(BETRAG) from buchung
       WHERE ONRSOLL=:IONR and KSOLL=:IKNR
       AND Datum<:DTBIS
       AND OPBETRAG IS NULL
       INTO :SUMSOLL;
       SELECT SUM(BETRAG) from buchung
       WHERE ONRHABEN=:IONR and KHABEN=:IKNR
       AND Datum<:DTBIS
       AND OPBETRAG IS NULL
       INTO :SUMHABEN;
     END   /* keine Sollstelungen */
    END
   ELSE
    BEGIN /* WDATUM */
     IF (BSOLL='J') THEN
      BEGIN /* Sollstelungen */
       SELECT SUM(BETRAG) from buchung
       WHERE ONRSOLL=:IONR and KSOLL=:IKNR
       AND WDatum<:DTBIS
       INTO :SUMSOLL;
       SELECT SUM(BETRAG) from buchung
       WHERE ONRHABEN=:IONR and KHABEN=:IKNR
       AND WDatum<:DTBIS
       INTO :SUMHABEN;
     END /* Sollstelungen */
    ELSE
     BEGIN /* keine Sollstelungen */
       SELECT SUM(BETRAG) from buchung
       WHERE ONRSOLL=:IONR and KSOLL=:IKNR
       AND WDatum<:DTBIS
       AND OPBETRAG IS NULL
       INTO :SUMSOLL;
       SELECT SUM(BETRAG) from buchung
       WHERE ONRHABEN=:IONR and KHABEN=:IKNR
       AND WDatum<:DTBIS
       AND OPBETRAG IS NULL
       INTO :SUMHABEN;
     END   /* keine Sollstelungen */
    END   /* WDATUM */
   IF (SUMSOLL IS NULL) THEN
    SUMSOLL=0;
   IF (SUMHABEN IS NULL) THEN
    SUMHABEN=0;
  IF (KKLASSE=71) THEN
   SALDO=SUMSOLL-SUMHABEN;
  ELSE
   SALDO=SUMHABEN-SUMSOLL;
  SUSPEND;
  END /* DEB / KRED */
 END /* nicht 98000... */
END
