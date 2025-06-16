-- Prozedur: ENTW_SALDO_WDATUM
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE ENTW_SALDO_WDATUM
DECLARE VARIABLE BETRAG1 NUMERIC(15, 2);
DECLARE VARIABLE BETRAG2 NUMERIC(15, 2);
DECLARE VARIABLE BETRAGT NUMERIC(15, 2);
BEGIN
 IF (TEMPTEXT IS NULL) THEN
  TEMPTEXT = '';
 NR = 0;
 IF (ART = 'N' or ART = 'G' or ART = ' ') THEN
  BEGIN
   /* G/N */
   IF (KLASSE = 13 or KLASSE = 18) THEN
    BEGIN
     /* ZAHLUNG AKTUELLES JAHR */
     IF (ART = 'N' OR ART = ' ') THEN   /* N=NZ, ' ' =BEIDE */
      BEGIN
       IF (KLASSE = 18) THEN
        BEGIN
         BETRAG1 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
          where BANKNRSOLL=:BANKNR and (ARTOP=15 or (ARTOP>=110 and ARTOP<=580)) and (WDatum>=:DTVON and WDatum<=:DTBIS)
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag>=0 and GN=1
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag>=0 and GN=1
          and (buchzahl.ARTOP=15 or (buchzahl.ARTOP>=110 and buchzahl.ARTOP<=580)) and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG1 = BETRAG1 + EBETRAG;
             SUSPEND;
            END
          END
        END
       ELSE
        BEGIN
         BETRAG1=0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
          where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and (WDatum>=:DTVON and WDatum<=:DTBIS)
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag>=0 and GN=0
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag>=0 and GN=0
          and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG1 = BETRAG1 + EBETRAG;
             SUSPEND;
            END
          END
        END
       if (BETRAG1 IS NULL) THEN
        BETRAG1 = 0;
      END
     ELSE
      BETRAG1=0;
     /* Gutschrift */
     IF (ART='G' OR ART=' ') THEN
      BEGIN
       IF (KLASSE=18) THEN
        BEGIN
         BETRAG2 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -BETRAG from buchung
          where BANKNRSOLL=:BANKNR and (ARTOP=15 or (ARTOP>=110 and ARTOP<=580)) and (WDatum>=:DTVON and WDatum<=:DTBIS)
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag<0 and GN=1
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag<0 and GN=1
          and (buchzahl.ARTOP=15 or (buchzahl.ARTOP>=110 and buchzahl.ARTOP<=580)) and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG2 = BETRAG2 + EBETRAG;
             SUSPEND;
            END
          END
        END
       ELSE
        BEGIN
         BETRAG2 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -BETRAG from buchung
          where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and (WDatum>=:DTVON and WDatum<=:DTBIS)
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag<0 and GN=0
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag<0 and GN=0
          and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG2 = BETRAG2 + EBETRAG;
             SUSPEND;
            END
          END
        END
       if (BETRAG2 IS NULL) THEN
        BETRAG2=0;
       END
      ELSE
       BETRAG2=0;
     BETRAG = BETRAG1 - BETRAG2;
     TEXT = :TEMPTEXT;
     DATUM = null;
     BELEGNR = null;
     BTEXT = null;
     KONTOS = null;
     KONTOH = null;
     EBETRAG = null;
     ISMASTER = '1';
     IF (BETRAG<>0) THEN
      SUSPEND;
     NR = NR + 1;
     /* ENDE AKTUELLES JAHR */
     /* ZAHLUNG VORHERIGES JAHR */
     IF (ART = 'N' OR ART = ' ') THEN   /* N=NZ, ' ' =BEIDE */
      BEGIN
       IF (KLASSE = 18) THEN
        BEGIN
         BETRAG1 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
          where BANKNRSOLL=:BANKNR and (ARTOP=15 or (ARTOP>=110 and ARTOP<=580)) and WDatum<:DTVON
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag>=0 and GN=1
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag>=0 and GN=1
          and (buchzahl.ARTOP=15 or (buchzahl.ARTOP>=110 and buchzahl.ARTOP<=580)) and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG1 = BETRAG1 + EBETRAG;
             SUSPEND;
            END
          END
        END
       ELSE
        BEGIN
         BETRAG1=0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
          where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and WDatum<:DTVON
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag>=0 and GN=0
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag>=0 and GN=0
          and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG1 = BETRAG1 + EBETRAG;
             SUSPEND;
            END
          END
        END
       if (BETRAG1 IS NULL) THEN
        BETRAG1 = 0;
      END
     ELSE
      BETRAG1=0;
     /* Gutschrift */
     IF (ART='G' OR ART=' ') THEN
      BEGIN
       IF (KLASSE=18) THEN
        BEGIN
         BETRAG2 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -BETRAG from buchung
          where BANKNRSOLL=:BANKNR and (ARTOP=15 or (ARTOP>=110 and ARTOP<=580)) and WDatum<:DTVON
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag<0 and GN=1
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag<0 and GN=1
          and (buchzahl.ARTOP=15 or (buchzahl.ARTOP>=110 and buchzahl.ARTOP<=580)) and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG2 = BETRAG2 + EBETRAG;
             SUSPEND;
            END
          END
        END
       ELSE
        BEGIN
         BETRAG2 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -BETRAG from buchung
          where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and WDatum<:DTVON
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag<0 and GN=0
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag<0 and GN=0
          and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG2 = BETRAG2 + EBETRAG;
             SUSPEND;
            END
          END
        END
       if (BETRAG2 IS NULL) THEN
        BETRAG2=0;
       END
      ELSE
       BETRAG2=0;
     BETRAG = BETRAG1 - BETRAG2;
     TEXT = :TEMPTEXT || ' fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Vorjahr im Abrechnungszeitraum erhalten';
     DATUM = null;
     BELEGNR = null;
     BTEXT = null;
     KONTOS = null;
     KONTOH = null;
     EBETRAG = null;
     ISMASTER = '1';
     IF (BETRAG<>0) THEN
      SUSPEND;
     NR = NR + 1;
     /* ENDE VORHERIGES JAHR */
     /* ZAHLUNG FOLGE JAHR */
     IF (ART = 'N' OR ART = ' ') THEN   /* N=NZ, ' ' =BEIDE */
      BEGIN
       IF (KLASSE = 18) THEN
        BEGIN
         BETRAG1 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
          where BANKNRSOLL=:BANKNR and (ARTOP=15 or (ARTOP>=110 and ARTOP<=580)) and WDatum>:DTBIS
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag>=0 and GN=1
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag>=0 and GN=1
          and (buchzahl.ARTOP=15 or (buchzahl.ARTOP>=110 and buchzahl.ARTOP<=580)) and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG1 = BETRAG1 + EBETRAG;
             SUSPEND;
            END
          END
        END
       ELSE
        BEGIN
         BETRAG1=0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
          where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and WDatum>:DTBIS
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag>=0 and GN=0
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag>=0 and GN=0
          and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG1 = BETRAG1 + EBETRAG;
             SUSPEND;
            END
          END
        END
       if (BETRAG1 IS NULL) THEN
        BETRAG1 = 0;
      END
     ELSE
      BETRAG1=0;
     /* Gutschrift */
     IF (ART='G' OR ART=' ') THEN
      BEGIN
       IF (KLASSE=18) THEN
        BEGIN
         BETRAG2 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -BETRAG from buchung
          where BANKNRSOLL=:BANKNR and (ARTOP=15 or (ARTOP>=110 and ARTOP<=580)) and WDatum>:DTBIS
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag<0 and GN=1
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag<0 and GN=1
          and (buchzahl.ARTOP=15 or (buchzahl.ARTOP>=110 and buchzahl.ARTOP<=580)) and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG2 = BETRAG2 + EBETRAG;
             SUSPEND;
            END
          END
        END
       ELSE
        BEGIN
         BETRAG2 = 0;
         FOR
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -BETRAG from buchung
          where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and WDatum>:DTBIS
          and (Datum>=:DTVON and Datum<=:DTBIS) and Betrag<0 and GN=0
          union all
          SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -SUM(buchzahl.BETRAG) from buchung,buchzahl
          where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS) and buchung.Betrag<0 and GN=0
          and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
          group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
         INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
         DO
          BEGIN
           IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
            BEGIN
             BETRAG = null;
             TEXT = '';
             ISMASTER = '2';
             BETRAG2 = BETRAG2 + EBETRAG;
             SUSPEND;
            END
          END
        END
       if (BETRAG2 IS NULL) THEN
        BETRAG2=0;
       END
      ELSE
       BETRAG2=0;
     BETRAG = BETRAG1 - BETRAG2;
     TEXT = :TEMPTEXT || ' fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Folgejahr im Abrechnungszeitraum erhalten';
     DATUM = null;
     BELEGNR = null;
     BTEXT = null;
     KONTOS = null;
     KONTOH = null;
     EBETRAG = null;
     ISMASTER = '1';
     IF (BETRAG<>0) THEN
      SUSPEND;
     /* ENDE FOLGE JAHR */
     NR = NR + 1;
    END
   ELSE
    IF (KLASSE=19) THEN  /* Sonstige Einnahmen nur im Zeitraum Datum*/
     BEGIN
      BETRAG1 = 0;
      for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
       banknrsoll=:BANKNR and arthaben=64 and (Datum>=:DTVON and Datum<=:DTBIS)
      into DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
      do
       begin
        IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
         BEGIN
          BETRAG = null;
          TEXT = '';
          ISMASTER = '2';
          BETRAG1 = BETRAG1 + EBETRAG;
          SUSPEND;
         END
       end
      /*  */
      BETRAG2 = 0;
      for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
       banknrhaben=:BANKNR and artsoll=64 and (Datum>=:DTVON and Datum<=:DTBIS)
      into DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
      do
       begin
        IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
         BEGIN
          BETRAG = null;
          TEXT = '';
          ISMASTER = '2';
          BETRAG2 = BETRAG2 + EBETRAG;
          SUSPEND;
         END
       end
      BETRAGT = BETRAG1 - BETRAG2;
      /* DIREKT auf Einnahmekonto Klasse 19 gebucht */
      BETRAG1 = 0;
      for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
       banknrsoll=:BANKNR and arthaben=:KLASSE and (Datum>=:DTVON and Datum<=:DTBIS)
      into DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
      do
       begin
        IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
         BEGIN
          BETRAG = null;
          TEXT = '';
          ISMASTER = '2';
          BETRAG1 = BETRAG1 + EBETRAG;
          SUSPEND;
         END
       end
      BETRAGT = BETRAGT + BETRAG1;
      /*  */
      BETRAG2 = 0;
      for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
       banknrhaben=:BANKNR and artsoll=:KLASSE and (Datum>=:DTVON and Datum<=:DTBIS)
      into DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
      do
       begin
        IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
         BEGIN
          BETRAG = null;
          TEXT = '';
          ISMASTER = '2';
          BETRAG2 = BETRAG2 + EBETRAG;
          SUSPEND;
         END
       end
      BETRAGT = BETRAGT - BETRAG2;
      /*Zahlungen, sonstige Einnahmekonten*/
      BETRAG2 = 0;
      for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
       banknrsoll=:BANKNR and artop=19 and (Datum>=:DTVON and Datum<=:DTBIS)
      into DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
      do
       begin
        IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
         BEGIN
          BETRAG = null;
          TEXT = '';
          ISMASTER = '2';
          BETRAG2 = BETRAG2 + EBETRAG;
          SUSPEND;
         END
       end
      BETRAGT = BETRAGT + BETRAG2;
      /*Zahlung ENDE*/
      BETRAG = BETRAGT;
      TEXT = :TEMPTEXT;
      DATUM = null;
      BELEGNR = null;
      BTEXT = null;
      KONTOS = null;
      KONTOH = null;
      EBETRAG = null;
      ISMASTER = '1';
      IF (BETRAG<>0) THEN
       SUSPEND;
      NR = NR + 1;
     END                /* Sonstige Einnahmen */
    ELSE
     /* SPLIT */
     BEGIN
      /* ZAHLUNG */
      /* AKTUELLES JAHR */
      BETRAG1=0;
      BETRAG2=0;
      BETRAG=0;
      FOR
       SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
       where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and (WDatum>=:DTVON and WDatum<=:DTBIS)
       and (Datum>=:DTVON and Datum<=:DTBIS) and GN=0
       union all
       SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
       where banknrsoll=:BANKNR and buchung.ARTOP=0 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS) and GN=0
       and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
       group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
      INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
      DO
       BEGIN
        IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
         BEGIN
          BETRAG = null;
          TEXT = '';
          ISMASTER = '2';
          BETRAG1 = BETRAG1 + EBETRAG;
          SUSPEND;
         END
       END
      /*  */
      IF (BETRAG1 <> 0) THEN
       BEGIN
        BETRAG = BETRAG1;
        TEXT = :TEMPTEXT;
        DATUM = null;
        BELEGNR = null;
        BTEXT = null;
        KONTOS = null;
        KONTOH = null;
        EBETRAG = null;
        ISMASTER = '1';
        SUSPEND;
        NR = NR + 1;
       END
      /* ENDE AKTUELLES JAHR */
      /* VORHERIGES JAHR */
      BETRAG1=0;
      BETRAG2=0;
      BETRAG=0;
      FOR
       SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
       where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and WDatum<:DTVON
       and (Datum>=:DTVON and Datum<=:DTBIS) and GN=0
       union all
       SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
       where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS) and GN=0
       and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
       group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
      INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
      DO
       BEGIN
        IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
         BEGIN
          BETRAG = null;
          TEXT = '';
          ISMASTER = '2';
          BETRAG1 = BETRAG1 + EBETRAG;
          SUSPEND;
         END
       END
      /*  */
      IF (BETRAG1 <> 0) THEN
       BEGIN
        BETRAG = BETRAG1;
        TEXT = :TEMPTEXT || ' fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Vorjahr im Abrechnungszeitraum erhalten';
        DATUM = null;
        BELEGNR = null;
        BTEXT = null;
        KONTOS = null;
        KONTOH = null;
        EBETRAG = null;
        ISMASTER = '1';
        SUSPEND;
        NR = NR + 1;
       END
      /* ENDE VORHERIGES JAHR */
      /* FOLGE JAHR */
      BETRAG1=0;
      BETRAG2=0;
      BETRAG=0;
      FOR
       SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
       where BANKNRSOLL=:BANKNR and ARTOP=:KLASSE and WDatum>:DTBIS
       and (Datum>=:DTVON and Datum<=:DTBIS) and GN=0
       union all
       SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, SUM(buchzahl.BETRAG) from buchung,buchzahl
       where banknrsoll=:BANKNR and buchung.ARTOP=0 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS) and GN=0
       and buchzahl.ARTOP=:KLASSE and buchzahl.bnr=buchung.bnr
       group by DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN
      INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
      DO
       BEGIN
        IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
         BEGIN
          BETRAG = null;
          TEXT = '';
          ISMASTER = '2';
          BETRAG1 = BETRAG1 + EBETRAG;
          SUSPEND;
         END
       END
      /*  */
      IF (BETRAG1 <> 0) THEN
       BEGIN
        BETRAG = BETRAG1;
        TEXT = :TEMPTEXT || ' fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Folgejahr im Abrechnungszeitraum erhalten';
        DATUM = null;
        BELEGNR = null;
        BTEXT = null;
        KONTOS = null;
        KONTOH = null;
        EBETRAG = null;
        ISMASTER = '1';
        SUSPEND;
        NR = NR + 1;
       END
      /* ENDE FOLGE JAHR */
     END
  END /* SPLIT */
 ELSE
  IF (ART='K') THEN
   BEGIN /* ART = K Kosten */
    /* Noch die Kosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r dieses Jahr */
    BETRAG1 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrsoll=:BANKNR and arthaben=71 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG1 = BETRAG1 + EBETRAG;
        SUSPEND;
       END
     END
    /*  */
    BETRAG2 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrhaben=:BANKNR and artsoll=71 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG2 = BETRAG2 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAG2 - BETRAG1;
    /* DIREKT gebucht */
    BETRAG1 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrsoll=:BANKNR and arthaben=1 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG1 = BETRAG1 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAGT - BETRAG1;
    /*  */
    BETRAG2 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrhaben=:BANKNR and artsoll=1 and (WDatum>=:DTVON and WDatum<=:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG2 = BETRAG2 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAGT + BETRAG2;
    /*  */
    BETRAG = BETRAGT;
    IF (BETRAG>=0) THEN
     TEXT='abzgl. Bewirtschaftungskosten im Abrechnungszeitraum';
    ELSE
     TEXT='zzgl. Bewirtschaftungskosten im Abrechnungszeitraum';
    DATUM = null;
    BELEGNR = null;
    BTEXT = null;
    KONTOS = null;
    KONTOH = null;
    EBETRAG = null;
    ISMASTER = '1';
    IF (BETRAG <>0) THEN
     SUSPEND;
    NR = NR + 1;
    /* Noch die Kosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r dieses Jahr */
    /* Noch die Kosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤chstes Jahr in diesem Jahr */
    BETRAG1 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrsoll=:BANKNR and arthaben=71 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG1 = BETRAG1 + EBETRAG;
        SUSPEND;
       END
     END
    /*  */
    BETRAG2 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrhaben=:BANKNR and artsoll=71 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG2 = BETRAG2 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAG2 - BETRAG1;
    /* DIREKT gebucht */
    BETRAG1 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrsoll=:BANKNR and arthaben=1 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG1 = BETRAG1 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAGT - BETRAG1;
    /*  */
    BETRAG2 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrhaben=:BANKNR and artsoll=1 and WDatum>:DTBIS and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG2 = BETRAG2 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAGT + BETRAG2;
    /*  */
    BETRAG = BETRAGT;
    IF (BETRAG>=0) THEN
     TEXT='abzgl. Bewirtschaftungskosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Folgejahr im Abrechnungszeitraum gebucht';
    ELSE
     TEXT='zzgl. Bewirtschaftungskosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Folgejahr im Abrechnungszeitraum gebucht';
    DATUM = null;
    BELEGNR = null;
    BTEXT = null;
    KONTOS = null;
    KONTOH = null;
    EBETRAG = null;
    ISMASTER = '1';
    IF (BETRAG <>0) THEN
     SUSPEND;
    NR = NR + 1;
    /* Noch die Kosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤chstes Jahr in diesem Jahr */
    /* Noch die Kosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r voriges Jahr in diesem Jahr */
    BETRAG1 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrsoll=:BANKNR and arthaben=71 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG1 = BETRAG1 + EBETRAG;
        SUSPEND;
       END
     END
    /*  */
    BETRAG2 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrhaben=:BANKNR and artsoll=71 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG2 = BETRAG2 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAG2 - BETRAG1;
    /* DIREKT gebucht */
    BETRAG1 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrsoll=:BANKNR and arthaben=1 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG1 = BETRAG1 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAGT - BETRAG1;
    /*  */
    BETRAG2 = 0;
    FOR
     SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
     where banknrhaben=:BANKNR and artsoll=1 and WDatum<:DTVON and (Datum>=:DTVON and Datum<=:DTBIS)
    INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
    DO
     BEGIN
      IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
       BEGIN
        BETRAG = null;
        TEXT = '';
        ISMASTER = '2';
        BETRAG2 = BETRAG2 + EBETRAG;
        SUSPEND;
       END
     END
    BETRAGT = BETRAGT + BETRAG2;
    /*  */
    BETRAG = BETRAGT;
    IF (BETRAG>=0) THEN
     TEXT='abzgl. Bewirtschaftungskosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Vorjahr im Abrechnungszeitraum gebucht';
    ELSE
     TEXT='zzgl. Bewirtschaftungskosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Vorjahr im Abrechnungszeitraum gebucht';
    DATUM = null;
    BELEGNR = null;
    BTEXT = null;
    KONTOS = null;
    KONTOH = null;
    EBETRAG = null;
    ISMASTER = '1';
    IF (BETRAG <>0) THEN
     SUSPEND;
    NR = NR + 1;
    /* Noch die Kosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r voriges Jahr in diesem Jahr */
   END /* Kosten */
  ELSE
   IF (ART='B') THEN
    BEGIN /* ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrag sonstige A/P */
     BETRAG1 = 0;
     FOR
      SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
      where artsoll=:KLASSE and banknrhaben=:BANKNR and (Datum>=:DTVON and Datum<=:DTBIS)
     INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
     DO
      BEGIN
       IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
        BEGIN
         BETRAG = null;
         TEXT = '';
         ISMASTER = '2';
         BETRAG1 = BETRAG1 + EBETRAG;
         SUSPEND;
        END
      END
     /*  */
     IF (BETRAG1 <> 0) THEN
      begin
       BETRAG = -BETRAG1;
       TEXT = :TEMPTEXT;
       DATUM = null;
       BELEGNR = null;
       BTEXT = null;
       KONTOS = null;
       KONTOH = null;
       EBETRAG = null;
       ISMASTER = '1';
       SUSPEND;
       NR = NR + 1;
      end
     /*  */
     BETRAG1 = 0;
     FOR
      SELECT DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung
      where arthaben=:KLASSE and banknrsoll=:BANKNR and (Datum>=:DTVON and Datum<=:DTBIS)
     INTO DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG
     DO
      BEGIN
       IF (EBETRAG IS NOT NULL and EBETRAG<>0) THEN
        BEGIN
         BETRAG = null;
         TEXT = '';
         ISMASTER = '2';
         BETRAG1 = BETRAG1 + EBETRAG;
         SUSPEND;
        END
      END
     /*  */
     IF (BETRAG1 <> 0) THEN
      begin
       BETRAG = BETRAG1;
       TEXT = :TEMPTEXT;
       DATUM = null;
       BELEGNR = null;
       BTEXT = null;
       KONTOS = null;
       KONTOH = null;
       EBETRAG = null;
       ISMASTER = '1';
       SUSPEND;
       NR = NR + 1;
      end
    END /* ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrag sonstige A/P */
END
