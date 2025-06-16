-- Prozedur: JOURNAL_HD
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE JOURNAL_HD
DECLARE VARIABLE BANKNRSOLL INTEGER;
 DECLARE VARIABLE BANKNRHABEN INTEGER;
 DECLARE VARIABLE ARTSOLL INTEGER;
 DECLARE VARIABLE ARTHABEN INTEGER;
 DECLARE VARIABLE LEVBANKSTR VARCHAR(15);
 DECLARE VARIABLE LEVBANK2STR VARCHAR(15);
 DECLARE VARIABLE LEVBANKNR INTEGER;
 DECLARE VARIABLE LEVBANK2NR INTEGER;
 DECLARE VARIABLE TEMPSTR VARCHAR(15);
 DECLARE VARIABLE KNR INTEGER;
 DECLARE VARIABLE IKUSCHLNR1 INTEGER;
 DECLARE VARIABLE IKUSCHLNR2 INTEGER;
 DECLARE VARIABLE IKUSCHLPROZ1 SMALLINT;
 DECLARE VARIABLE IKUSCHLPROZ2 SMALLINT;
 DECLARE VARIABLE KBEW CHAR(1);
 DECLARE VARIABLE HEIZEXTERN CHAR(1);
 DECLARE VARIABLE BHEIZ CHAR(1);
 DECLARE VARIABLE KVERTEILUNG CHAR(1);
 DECLARE VARIABLE BETRAG1 NUMERIC (15,2);
 DECLARE VARIABLE BETRAG2 NUMERIC (15,2);
 DECLARE VARIABLE BETRAG3 NUMERIC (15,2);
 DECLARE VARIABLE BETRAG4 NUMERIC (15,2);
 DECLARE VARIABLE BETRAG5 NUMERIC (15,2);
 DECLARE VARIABLE HAUSTYP INTEGER;
 DECLARE VARIABLE IHEIZK INTEGER;
 DECLARE VARIABLE KWUSCHL INTEGER;
 DECLARE VARIABLE BUSCHL1 INTEGER;
 DECLARE VARIABLE BUSCHL2 INTEGER;
 DECLARE VARIABLE WUSCHL1 INTEGER;
 DECLARE VARIABLE WUSCHL2 INTEGER;
 DECLARE VARIABLE BUSCHLPROZ1 FLOAT;
 DECLARE VARIABLE BUSCHLPROZ2 FLOAT;
 DECLARE VARIABLE WUSCHLPROZ1 FLOAT;
 DECLARE VARIABLE WUSCHLPROZ2 FLOAT;
 DECLARE VARIABLE KKSTNR INTEGER;

BEGIN
 SELECT NR, KURZBEZ FROM BANKEN WHERE NR IN (SELECT LEVBANKNR FROM OBJEKTE WHERE ONR=:IONR) INTO :LEVBANKNR, :LEVBANKSTR;
 SELECT NR, KURZBEZ FROM BANKEN WHERE NR IN (SELECT LEVBANKNR2 FROM OBJEKTE WHERE ONR=:IONR) INTO :LEVBANK2NR, :LEVBANK2STR;
 /*         */
 /* JOURNAL der Haushaltsnahen Dienstleistungen */
 /*         */
 SELECT ONR, BSONST, VERWNR, HEIZEXTERN, KWUSCHL, BUSCHL1, BUSCHL2, WUSCHL1, WUSCHL2, BUSCHLPROZ1, BUSCHLPROZ2, WUSCHLPROZ1, WUSCHLPROZ2
 from objekte where ONR=:IONR
 into ONR, HAUSTYP, VERWNR, HEIZEXTERN,:KWUSCHL, :BUSCHL1, :BUSCHL2, :WUSCHL1, :WUSCHL2, :BUSCHLPROZ1, :BUSCHLPROZ2, :WUSCHLPROZ1, :WUSCHLPROZ2;
 /* KONTEN */
 FOR select KNR, KUSCHLNR1, KUSCHLNR2, KUSCHLPROZ1, KUSCHLPROZ2, KBEW, KVERTEILUNG, BHEIZ, IHEIZK, KKSTNR from konten
 where ONR=:IONR and (KKSTNr<3 or BHEIZ='J' or IHEIZK>0) AND KKLASSE=1
 into :KNR, :IKUSCHLNR1, :IKUSCHLNR2, :IKUSCHLPROZ1, :IKUSCHLPROZ2, :KBEW, :KVERTEILUNG, :BHEIZ, :IHEIZK, :KKSTNR
 do
  begin
   IF (BHEIZ IS NULL) THEN
    BHEIZ='N';
   ELSE
    IF (BHEIZ='J' and HEIZEXTERN='N') THEN
     IHEIZK=1;
   IF (NOT (HEIZEXTERN='J' AND KKSTNR=3)) THEN /* EXTERNE HEIZKOSTEN: NICHT ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“BERNEHMEN */
    BEGIN
     IF (IHEIZK>0) THEN
      BEGIN /* interne HK */
       IF (IHEIZK=1 OR IHEIZK=2) THEN
        BEGIN
         IKUSCHLNR1=BUSCHL1;
         IKUSCHLNR2=BUSCHL2;
         IKUSCHLPROZ1=BUSCHLPROZ1 * 100;
         IKUSCHLPROZ2=BUSCHLPROZ2 * 100;
        END
       ELSE
        IF (IHEIZK=3) THEN /* WW */
         BEGIN
          IKUSCHLNR1=WUSCHL1;
          IKUSCHLNR2=WUSCHL2;
          IKUSCHLPROZ1=WUSCHLPROZ1 * 100;
          IKUSCHLPROZ2=WUSCHLPROZ2 * 100;
         END
       ELSE /* Kaltwasser */
        BEGIN
         IKUSCHLNR1=KWUSCHL;
         IKUSCHLNR2=0;
         IKUSCHLPROZ1=10000;
         IKUSCHLPROZ2=0;
        END
      END /* interne HK */
   IF (HAUSTYP=0 OR HAUSTYP=2) THEN
    BEGIN
     IF (IKUSCHLNR1>=50) THEN
      BEW=0;
     ELSE
      BEW=1;
     END
    ELSE
     BEGIN /* reine WEG */
      IF (KVERTEILUNG='J') THEN
       BEW=1;
      ELSE
       BEW=0;
     END
   IF (BWDATUM='N') THEN
    BEGIN
     /* Ausgabekont im SOLL + */
     for select betrag1, betrag2, betrag3, betrag4,
     buchung.BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, KSTRHABEN, KSTRSOLL, ARTSOLL, ARTHABEN
     from hdbuchung, buchung where hdbuchung.bnr=buchung.bnr
     and ONRSOLL=:IONR AND KSOLL=:KNR and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
     INTO :BETRAG1, :BETRAG2, :BETRAG3, :BETRAG4,
          :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :KSTRHABEN, :KSTRSOLL, :ARTSOLL, :ARTHABEN
     DO
      BEGIN
       IF (BETRAG1 IS NULL) THEN
        BETRAG1=0;
       IF (BETRAG2 IS NULL) THEN
        BETRAG2=0;
       IF (BETRAG3 IS NULL) THEN
        BETRAG3=0;
       IF (BETRAG4 IS NULL) THEN
        BETRAG4=0;
       IF (BETRAG1<>0 OR BETRAG2<>0 OR BETRAG3<>0 or BETRAG4<>0) THEN
        BEGIN
         IF (BANKNRHABEN IS NOT NULL) THEN
          BEGIN
           IF (BANKNRHABEN=LEVBANKNR) THEN
            KSTRHABEN=KSTRHABEN || ' ' || LEVBANKSTR;
           ELSE
            IF (BANKNRHABEN=LEVBANK2NR) THEN
             KSTRHABEN=KSTRHABEN || ' ' || LEVBANKSTR;
           ELSE
            BEGIN
             SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :TEMPSTR;
             KSTRHABEN=KSTRHABEN || ' ' || TEMPSTR;
            END
          END
         ELSE
          BEGIN
           IF (:ARTHABEN<>71) THEN
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRHABEN;
           ELSE
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KSOLL INTO :KSTRHABEN;
           END
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRSOLL;
         IF (IKUSCHLPROZ1>0) THEN
          BEGIN
           USCHL=IKUSCHLNR1;
           USCHLPROZ=IKUSCHLPROZ1;
           IF (BETRAG1<>0) THEN
            BEGIN
             PARAGRAF=1;
             BETRAG_ANT=BETRAG1 * IKUSCHLPROZ1 / 10000;
             SUSPEND;
            END
           IF (BETRAG2<>0) THEN
            BEGIN
             PARAGRAF=2;
             BETRAG_ANT=BETRAG2 * IKUSCHLPROZ1 / 10000;
             SUSPEND;
            END
           IF (BETRAG3<>0) THEN
            BEGIN
             PARAGRAF=3;
             BETRAG_ANT=BETRAG3 * IKUSCHLPROZ1 / 10000;
             SUSPEND;
            END
           IF (BETRAG4<>0) THEN
            BEGIN
             PARAGRAF=4;
             BETRAG_ANT=BETRAG4 * IKUSCHLPROZ1 / 10000;
             SUSPEND;
            END
          END /* KUSCHLPROZ > 0 */
         IF (IKUSCHLPROZ2>0) THEN
          BEGIN
           USCHL=IKUSCHLNR2;
           USCHLPROZ=IKUSCHLPROZ2;
           IF (BETRAG1<>0) THEN
            BEGIN
             PARAGRAF=1;
             BETRAG_ANT=BETRAG1 * IKUSCHLPROZ2 / 10000;
             SUSPEND;
            END
           IF (BETRAG2<>0) THEN
            BEGIN
             PARAGRAF=2;
             BETRAG_ANT=BETRAG2 * IKUSCHLPROZ2 / 10000;
             SUSPEND;
            END
           IF (BETRAG3<>0) THEN
            BEGIN
             PARAGRAF=3;
             BETRAG_ANT=BETRAG3 * IKUSCHLPROZ2 / 10000;
             SUSPEND;
            END
           IF (BETRAG4<>0) THEN
            BEGIN
             PARAGRAF=4;
             BETRAG_ANT=BETRAG4 * IKUSCHLPROZ2 / 10000;
             SUSPEND;
            END
          END /* KUSCHLPROZ > 0 */
        END /* ein Betrag1..4 <>0 */
      END  /* for select */
     /* Ausgabekonten im HABEN */
     for select betrag1, betrag2, betrag3, betrag4,
     buchung.BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, KSTRHABEN, KSTRSOLL, ARTSOLL, ARTHABEN
     from hdbuchung, buchung where hdbuchung.bnr=buchung.bnr
     and ONRHABEN=:IONR AND KHABEN=:KNR and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
     INTO :BETRAG1, :BETRAG2, :BETRAG3, :BETRAG4,
          :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :KSTRHABEN, :KSTRSOLL, :ARTSOLL, :ARTHABEN
     DO
      BEGIN
       IF (BETRAG1 IS NULL) THEN
        BETRAG1=0;
       IF (BETRAG2 IS NULL) THEN
        BETRAG2=0;
       IF (BETRAG3 IS NULL) THEN
        BETRAG3=0;
       IF (BETRAG4 IS NULL) THEN
        BETRAG4=0;
       IF (BETRAG1<>0 OR BETRAG2<>0 OR BETRAG3<>0 or BETRAG4<>0) THEN
        BEGIN
         IF (BANKNRHABEN IS NOT NULL) THEN
          BEGIN
           IF (BANKNRHABEN=LEVBANKNR) THEN
            KSTRHABEN=KSTRHABEN || ' ' || LEVBANKSTR;
           ELSE
            IF (BANKNRHABEN=LEVBANK2NR) THEN
             KSTRHABEN=KSTRHABEN || ' ' || LEVBANKSTR;
           ELSE
            BEGIN
             SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :TEMPSTR;
             KSTRHABEN=KSTRHABEN || ' ' || TEMPSTR;
            END
          END
         ELSE
          BEGIN
           IF (:ARTHABEN<>71) THEN
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRHABEN;
           ELSE
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KSOLL INTO :KSTRHABEN;
           END
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRSOLL;
        END
       BETRAG=-BETRAG;
       BETRAG1=-BETRAG1;
       BETRAG2=-BETRAG2;
       BETRAG3=-BETRAG3;
       BETRAG4=-BETRAG4;
       IF (IKUSCHLPROZ1>0) THEN
        BEGIN
         USCHL=IKUSCHLNR1;
         USCHLPROZ=IKUSCHLPROZ1;
         IF (BETRAG1<>0) THEN
          BEGIN
           PARAGRAF=1;
           BETRAG_ANT=BETRAG1 * IKUSCHLPROZ1 / 10000;
           SUSPEND;
          END
         IF (BETRAG2<>0) THEN
          BEGIN
           PARAGRAF=2;
           BETRAG_ANT=BETRAG2 * IKUSCHLPROZ1 / 10000;
           SUSPEND;
          END
         IF (BETRAG3<>0) THEN
          BEGIN
           PARAGRAF=3;
           BETRAG_ANT=BETRAG3 * IKUSCHLPROZ1 / 10000;
           SUSPEND;
          END
         IF (BETRAG4<>0) THEN
          BEGIN
           PARAGRAF=4;
           BETRAG_ANT=BETRAG4 * IKUSCHLPROZ1 / 10000;
           SUSPEND;
          END
        END  /* KUSCHLPROZ > 0 */
       IF (IKUSCHLPROZ2>0) THEN
        BEGIN
         USCHL=IKUSCHLNR2;
         USCHLPROZ=IKUSCHLPROZ2;
         IF (BETRAG1<>0) THEN
          BEGIN
           PARAGRAF=1;
           BETRAG_ANT=BETRAG1 * IKUSCHLPROZ2 / 10000;
           SUSPEND;
          END
         IF (BETRAG2<>0) THEN
          BEGIN
           PARAGRAF=2;
           BETRAG_ANT=BETRAG2 * IKUSCHLPROZ2 / 10000;
           SUSPEND;
          END
         IF (BETRAG3<>0) THEN
          BEGIN
           PARAGRAF=3;
           BETRAG_ANT=BETRAG3 * IKUSCHLPROZ2 / 10000;
           SUSPEND;
          END
         IF (BETRAG4<>0) THEN
          BEGIN
           PARAGRAF=4;
           BETRAG_ANT=BETRAG4 * IKUSCHLPROZ2 / 10000;
           SUSPEND;
          END
        END  /* KUSCHLPROZ > 0 */
      END /* FOR SELECT */
     END /*BDATUM */
    ELSE
 BEGIN /* WDATUM */
/* Ausgabekont im SOLL + */
     for select betrag1, betrag2, betrag3, betrag4,
     buchung.BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, KSTRHABEN, KSTRSOLL, ARTSOLL, ARTHABEN
     from hdbuchung, buchung where hdbuchung.bnr=buchung.bnr
     and ONRSOLL=:IONR AND KSOLL=:KNR and (buchung.wdatum>=:DTVON and buchung.wdatum<=:DTBIS)
     INTO :BETRAG1, :BETRAG2, :BETRAG3, :BETRAG4,
          :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :KSTRHABEN, :KSTRSOLL, :ARTSOLL, :ARTHABEN
     DO
      BEGIN
       IF (BETRAG1 IS NULL) THEN
        BETRAG1=0;
       IF (BETRAG2 IS NULL) THEN
        BETRAG2=0;
       IF (BETRAG3 IS NULL) THEN
        BETRAG3=0;
       IF (BETRAG4 IS NULL) THEN
        BETRAG4=0;
       IF (BETRAG1<>0 OR BETRAG2<>0 OR BETRAG3<>0 or BETRAG4<>0) THEN
        BEGIN
         IF (BANKNRHABEN IS NOT NULL) THEN
          BEGIN
           IF (BANKNRHABEN=LEVBANKNR) THEN
            KSTRHABEN=KSTRHABEN || ' ' || LEVBANKSTR;
           ELSE
            IF (BANKNRHABEN=LEVBANK2NR) THEN
             KSTRHABEN=KSTRHABEN || ' ' || LEVBANKSTR;
           ELSE
            BEGIN
             SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :TEMPSTR;
             KSTRHABEN=KSTRHABEN || ' ' || TEMPSTR;
            END
          END
         ELSE
          BEGIN
           IF (:ARTHABEN<>71) THEN
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRHABEN;
           ELSE
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KSOLL INTO :KSTRHABEN;
           END
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRSOLL;
         IF (IKUSCHLPROZ1>0) THEN
          BEGIN
           USCHL=IKUSCHLNR1;
           USCHLPROZ=IKUSCHLPROZ1;
           IF (BETRAG1<>0) THEN
            BEGIN
             PARAGRAF=1;
             BETRAG_ANT=BETRAG1 * IKUSCHLPROZ1 / 10000;
             SUSPEND;
            END
           IF (BETRAG2<>0) THEN
            BEGIN
             PARAGRAF=2;
             BETRAG_ANT=BETRAG2 * IKUSCHLPROZ1 / 10000;
             SUSPEND;
            END
           IF (BETRAG3<>0) THEN
            BEGIN
             PARAGRAF=3;
             BETRAG_ANT=BETRAG3 * IKUSCHLPROZ1 / 10000;
             SUSPEND;
            END
           IF (BETRAG4<>0) THEN
            BEGIN
             PARAGRAF=4;
             BETRAG_ANT=BETRAG4 * IKUSCHLPROZ1 / 10000;
             SUSPEND;
            END
          END /* KUSCHLPROZ > 0 */
         IF (IKUSCHLPROZ2>0) THEN
          BEGIN
           USCHL=IKUSCHLNR2;
           USCHLPROZ=IKUSCHLPROZ2;
           IF (BETRAG1<>0) THEN
            BEGIN
             PARAGRAF=1;
             BETRAG_ANT=BETRAG1 * IKUSCHLPROZ2 / 10000;
             SUSPEND;
            END
           IF (BETRAG2<>0) THEN
            BEGIN
             PARAGRAF=2;
             BETRAG_ANT=BETRAG2 * IKUSCHLPROZ2 / 10000;
             SUSPEND;
            END
           IF (BETRAG3<>0) THEN
            BEGIN
             PARAGRAF=3;
             BETRAG_ANT=BETRAG3 * IKUSCHLPROZ2 / 10000;
             SUSPEND;
            END
           IF (BETRAG4<>0) THEN
            BEGIN
             PARAGRAF=4;
             BETRAG_ANT=BETRAG4 * IKUSCHLPROZ2 / 10000;
             SUSPEND;
            END
          END /* KUSCHLPROZ > 0 */
        END /* ein Betrag1..4 <>0 */
      END  /* for select */
     /* Ausgabekonten im HABEN */
     for select betrag1, betrag2, betrag3, betrag4,
     buchung.BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, KSTRHABEN, KSTRSOLL, ARTSOLL, ARTHABEN
     from hdbuchung, buchung where hdbuchung.bnr=buchung.bnr
     and ONRHABEN=:IONR AND KHABEN=:KNR and (buchung.wdatum>=:DTVON and buchung.wdatum<=:DTBIS)
     INTO :BETRAG1, :BETRAG2, :BETRAG3, :BETRAG4,
          :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :KSTRHABEN, :KSTRSOLL, :ARTSOLL, :ARTHABEN
     DO
      BEGIN
       IF (BETRAG1 IS NULL) THEN
        BETRAG1=0;
       IF (BETRAG2 IS NULL) THEN
        BETRAG2=0;
       IF (BETRAG3 IS NULL) THEN
        BETRAG3=0;
       IF (BETRAG4 IS NULL) THEN
        BETRAG4=0;
       IF (BETRAG1<>0 OR BETRAG2<>0 OR BETRAG3<>0 or BETRAG4<>0) THEN
        BEGIN
         IF (BANKNRHABEN IS NOT NULL) THEN
          BEGIN
           IF (BANKNRHABEN=LEVBANKNR) THEN
            KSTRHABEN=KSTRHABEN || ' ' || LEVBANKSTR;
           ELSE
            IF (BANKNRHABEN=LEVBANK2NR) THEN
             KSTRHABEN=KSTRHABEN || ' ' || LEVBANKSTR;
           ELSE
            BEGIN
             SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :TEMPSTR;
             KSTRHABEN=KSTRHABEN || ' ' || TEMPSTR;
            END
          END
         ELSE
          BEGIN
           IF (:ARTHABEN<>71) THEN
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRHABEN;
           ELSE
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KSOLL INTO :KSTRHABEN;
           END
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRSOLL;
        END
       BETRAG=-BETRAG;
       BETRAG1=-BETRAG1;
       BETRAG2=-BETRAG2;
       BETRAG3=-BETRAG3;
       BETRAG4=-BETRAG4;
       IF (IKUSCHLPROZ1>0) THEN
        BEGIN
         USCHL=IKUSCHLNR1;
         USCHLPROZ=IKUSCHLPROZ1;
         IF (BETRAG1<>0) THEN
          BEGIN
           PARAGRAF=1;
           BETRAG_ANT=BETRAG1 * IKUSCHLPROZ1 / 10000;
           SUSPEND;
          END
         IF (BETRAG2<>0) THEN
          BEGIN
           PARAGRAF=2;
           BETRAG_ANT=BETRAG2 * IKUSCHLPROZ1 / 10000;
           SUSPEND;
          END
         IF (BETRAG3<>0) THEN
          BEGIN
           PARAGRAF=3;
           BETRAG_ANT=BETRAG3 * IKUSCHLPROZ1 / 10000;
           SUSPEND;
          END
         IF (BETRAG4<>0) THEN
          BEGIN
           PARAGRAF=4;
           BETRAG_ANT=BETRAG4 * IKUSCHLPROZ1 / 10000;
           SUSPEND;
          END
        END  /* KUSCHLPROZ > 0 */
       IF (IKUSCHLPROZ2>0) THEN
        BEGIN
         USCHL=IKUSCHLNR2;
         USCHLPROZ=IKUSCHLPROZ2;
         IF (BETRAG1<>0) THEN
          BEGIN
           PARAGRAF=1;
           BETRAG_ANT=BETRAG1 * IKUSCHLPROZ2 / 10000;
           SUSPEND;
          END
         IF (BETRAG2<>0) THEN
          BEGIN
           PARAGRAF=2;
           BETRAG_ANT=BETRAG2 * IKUSCHLPROZ2 / 10000;
           SUSPEND;
          END
         IF (BETRAG3<>0) THEN
          BEGIN
           PARAGRAF=3;
           BETRAG_ANT=BETRAG3 * IKUSCHLPROZ2 / 10000;
           SUSPEND;
          END
         IF (BETRAG4<>0) THEN
          BEGIN
           PARAGRAF=4;
           BETRAG_ANT=BETRAG4 * IKUSCHLPROZ2 / 10000;
           SUSPEND;
          END
        END  /* KUSCHLPROZ > 0 */
      END /* FOR SELECT */
     END   /* WDATUM */
   END    /* HEIZEXTERN */
  END /* FOR KONTEN */
 END
