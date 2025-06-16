-- Prozedur: GET_RUECKL_BUCHUNGEN_RLA
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE GET_RUECKL_BUCHUNGEN_RLA
DECLARE VARIABLE ICOUNT Integer;
 DECLARE VARIABLE KSOLL Integer;
 DECLARE VARIABLE KHABEN Integer;
BEGIN
 IF (IS_WDATUM=0) THEN
  BEGIN
   FOR SELECT NR, KNR from rueckbkt where RUECKPOS=:IRUECKPOS
   INTO :NR, :KONTO do
    BEGIN
     ICOUNT=0;
     FOR select KSOLL, KHABEN, Datum, Text, Betrag
     FROM buchung
     WHERE ((ONRSOLL=:IONR and KSOLL=:KONTO) OR (ONRHABEN=:IONR and KHABEN=:KONTO))
     and (Datum>=:DTVON and Datum<=:DTBIS)
     order by Datum
     INTO KSOLL, KHABEN, Datum,Text,Betrag
     DO
      BEGIN
       IF (KHABEN=KONTO) THEN  /*Abgang*/
        BETRAG=-BETRAG;
       ICOUNT=ICOUNT+1;
       SUSPEND;
      END
     /* mindestens 1 Buchung sonst nicht gedruckt */
     IF (ICOUNT=0) THEN
      BEGIN
       DATUM=NULL;
       KONTO=NULL;
       TEXT='Keine Buchungen im Zeitraum';
       BETRAG=NULL;
       SUSPEND;
      END
    END
  END
 ELSE
  BEGIN
  FOR SELECT NR, KNR from rueckbkt where RUECKPOS=:IRUECKPOS
   INTO :NR, :KONTO do
    BEGIN
     ICOUNT=0;
     FOR select KSOLL, KHABEN, WDatum, Text, Betrag
     FROM buchung
     WHERE ((ONRSOLL=:IONR and KSOLL=:KONTO) OR (ONRHABEN=:IONR and KHABEN=:KONTO))
     and (WDatum>=:DTVON and WDatum<=:DTBIS)
     order by WDatum
     INTO KSOLL, KHABEN, Datum,Text,Betrag
     DO
      BEGIN
       IF (KHABEN=KONTO) THEN  /*Abgang*/
        BETRAG=-BETRAG;
       ICOUNT=ICOUNT+1;
       SUSPEND;
      END
     /* mindestens 1 Buchung sonst nicht gedruckt */
     IF (ICOUNT=0) THEN
      BEGIN
       DATUM=NULL;
       KONTO=NULL;
       TEXT='Keine Buchungen im Zeitraum';
       BETRAG=NULL;
       SUSPEND;
      END
    END
  END
END
