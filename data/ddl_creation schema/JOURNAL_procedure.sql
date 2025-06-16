-- Prozedur: JOURNAL
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE JOURNAL
DECLARE VARIABLE BANKNRSOLL INTEGER;
DECLARE VARIABLE IBANKNRAKT INTEGER;
DECLARE VARIABLE BANKNRHABEN INTEGER;
DECLARE VARIABLE ARTSOLL INTEGER;
DECLARE VARIABLE ARTHABEN INTEGER;
DECLARE VARIABLE KLASSEGS INTEGER;
DECLARE VARIABLE KLASSEGH INTEGER;
DECLARE VARIABLE SPLITNR INTEGER;
DECLARE VARIABLE BANKSTR VARCHAR(15);
DECLARE VARIABLE BETRAG NUMERIC(15, 2);
DECLARE VARIABLE USTSATZ NUMERIC(15, 4);
DECLARE VARIABLE KLASSEBIS INTEGER;
DECLARE VARIABLE LBNR INTEGER;
DECLARE VARIABLE ITKLASSE INTEGER;
DECLARE VARIABLE IKAUSZUGBLATT SMALLINT;
DECLARE VARIABLE IKAUSZUGNR INTEGER;
BEGIN
 IBANKNRAKT=-1;
 BANKSTR='';
 ITKLASSE = KLASSE;
 HDBETRAG = 0; HDTEXT = ''; HDART = 0;
 IF (BNACHKONTEN='N') THEN
  BEGIN
   /*         */
   /* JOURNAL */
   /*         */
   IF (BWDATUM='N') THEN
    BEGIN
     FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, KSTRHABEN, KSTRSOLL, ARTSOLL, ARTHABEN,LBNR from buchung
      WHERE (ONRSOLL=:IONR OR ONRHABEN=:IONR)
      AND ((KSOLL>=:KNRVON AND KSOLL <=:KNRBIS) OR (KHABEN>=:KNRVON AND KHABEN <=:KNRBIS))
      AND (Datum>=:DTVON and Datum<=:DTBIS)
      AND BETRAG<>0
     INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :KSTRHABEN, :KSTRSOLL, :ARTSOLL, :ARTHABEN, :LBNR
     DO
      BEGIN
       HDBETRAG = 0; HDTEXT = ''; HDART = 0;
       IF ((ARTSOLL=1) or (ARTHABEN=1)) THEN
        BEGIN
	 select sum(betrag) from hdbuch where bnr=:bnr into :HDBETRAG;  
         select first 1 text, art from hdbuch where bnr=:bnr into HDTEXT, HDART; 
         if (HDBETRAG is null) then
          HDBETRAG = 0;
         if (HDART is null) then
          HDART = 0;
         if (HDTEXT is null) then
          HDTEXT = '';  
        END
       /* */      
       ONR=:IONR;
       IF (ARTSOLL=1) THEN
        KLASSEGS=1; /* K */
       ELSE
        IF ((ARTSOLL>=10 AND ARTSOLL<=19) or (ARTSOLL>=110 and ARTSOLL<=580)) THEN
         KLASSEGS=2;  /* E*/
        ELSE
         IF ((ARTSOLL>=20 AND ARTSOLL<=24) OR (ARTSOLL=30)) THEN
          KLASSEGS=4; /* A*/
         ELSE
          IF (ARTSOLL=27) THEN
           KLASSEGS=3;  /* P*/
          ELSE
           IF (ARTSOLL=71) THEN
            KLASSEGS=7;   /* KRED*/
           ELSE
            KLASSEGS=6;  /* DEB*/
       IF (ARTHABEN=1) THEN
        KLASSEGH=1; /* K */
       ELSE
        IF ((ARTHABEN>=10 AND ARTHABEN<=19) or (ARTHABEN>=110 and ARTHABEN<=580)) THEN
         KLASSEGH=2;  /* E*/
        ELSE
         IF ((ARTHABEN>=20 AND ARTHABEN<=24) OR (ARTHABEN=30)) THEN
          KLASSEGH=4; /* A*/
         ELSE
          IF (ARTHABEN=27) THEN
           KLASSEGH=3;  /* P*/
          ELSE
           IF (ARTHABEN=71) THEN
            KLASSEGH=7;   /* KRED*/
           ELSE
            KLASSEGH=6;  /* DEB*/
       IF (OPBETRAG IS NOT NULL) THEN
        BEGIN
         IF (OPBETRAG=0) THEN
          BEMERKUNG='SO';
         ELSE
          BEMERKUNG='OP';
        END
       ELSE
        IF (LBNR IS NOT NULL) THEN
         BEMERKUNG='LEV';
        ELSE
         BEMERKUNG='';
       IF (BANKNRSOLL IS NOT NULL) THEN
        BEGIN
         IF (BANKNRSOLL=IBANKNRAKT) THEN
          KSTRSOLL=KSTRSOLL || ' ' || BANKSTR;
         ELSE
           BEGIN
            SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :BANKSTR;
            KSTRSOLL=KSTRSOLL || ' ' || BANKSTR;
            IBANKNRAKT=BANKNRSOLL;
           END
        END
       ELSE
        BEGIN
         IF (:ARTSOLL<>71) THEN
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRSOLL;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KSOLL INTO :KSTRSOLL;
        END
       IF (BANKNRHABEN IS NOT NULL) THEN
        BEGIN
         IF (BANKNRHABEN=IBANKNRAKT) THEN
          KSTRHABEN=KSTRHABEN || ' ' || BANKSTR;
         ELSE
           BEGIN
            SELECT KURZBEZ from Banken where NR=:BANKNRHABEN into :BANKSTR;
            KSTRHABEN=KSTRHABEN || ' ' || BANKSTR;
            IBANKNRAKT=BANKNRHABEN;
           END
        END
       ELSE
        BEGIN
         IF (:ARTHABEN<>71) THEN
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KHABEN INTO :KSTRHABEN;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KHABEN INTO :KSTRHABEN;
        END
       /*Steuer*/
       IF (MWST<>0) THEN
        BEGIN
         USTSATZ=100+MWST;/*1+(MWST/100);*/
         IF ((ARTSOLL>=10 AND ARTSOLL<=19) OR (ARTSOLL=1) or (ARTSOLL>=110 and ARTSOLL<=580)) THEN
          BEGIN
           IF (BDOPPBU='J') THEN
            BEGIN
             BETRAGS=BETRAG;
             USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
             BETRAGH=BETRAG;
             USTHABEN=NULL;
            END
           ELSE
            BEGIN /* Einfache Buch Steuer berechnen */
             BETRAGS=BETRAG;
             BETRAGH=BETRAG;
             USTHABEN=NULL;
             USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
            END
          END
         ELSE
          /* Steuer im Haben?*/
          IF ((ARTHABEN>=10 AND ARTHABEN<=19) OR (ARTHABEN=1) or (ARTHABEN>=110 and ARTHABEN<=580)) THEN
           BEGIN
            IF (BDOPPBU='J') THEN
             BEGIN
              BETRAGH=BETRAG;
              USTHABEN=BETRAG - ((BETRAG * 100) / USTSATZ);
              BETRAGS=BETRAG;
              USTSOLL=NULL;
             END
            ELSE
             BEGIN /* Einfache Buch Steuer berechnen */
              BETRAGS=BETRAG;
              BETRAGH=BETRAG;
              USTHABEN=NULL;
              USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
             END
           END
          ELSE
           BEGIN /* PlausibilitÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤t: Steuer nur auf Aufwand/Ertrag */
            BETRAGS=BETRAG;
            BETRAGH=BETRAG;
            USTSOLL=NULL;
            USTHABEN=NULL;
            MWST=NULL;
           END
        END
       ELSE
        BEGIN /* keine Steuer + einfache BuchFÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung Brutto*/
         BETRAGS=BETRAG;
         BETRAGH=BETRAG;
         USTSOLL=NULL;
         USTHABEN=NULL;
         MWST=NULL;
        END
       IF (KLASSE=6) THEN  /* steht fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle BEW/EIG */
        BEGIN
 /* BETRAG S = OPBETRAG */
         IF (BEMERKUNG<>'' AND BEMERKUNG<>'LEV') THEN
          BEGIN
           if (ARTSOLL=1) then /* gegen Ausgabe gebucht Rene 02.14*/
            BEGIN
             BETRAGH = -BETRAGH;
             USTHABEN = -USTHABEN;
            END
           BETRAGS=BETRAGH;
           USTSOLL=USTHABEN;
           BETRAGH=NULL;
           USTHABEN=NULL;
          END
         ELSE
          BEGIN
           if (ARTSOLL=1) then /* gegen Ausgabe gebucht Rene 02.14*/
            BEGIN
             BETRAGS = -BETRAGS;
             USTSOLL = -USTSOLL;
            END
           BETRAGH=BETRAGS;
           USTHABEN=USTSOLL;
           BETRAGS=NULL;
           USTSOLL=NULL;
          END
         /*Rene Verrechnungen*/
         IF (BANKNRSOLL IS NULL AND BANKNRHABEN IS NULL) THEN
          BEGIN /* VERRECHNUNG */
           IF ((ARTSOLL=24) OR (ARTSOLL=27)) THEN
            BEGIN
             BETRAGH=BETRAGH;
            END
           ELSE
            BEGIN
             BETRAGH=-BETRAGH;
            END
          END
        END
       ELSE
        IF (KLASSE=7) THEN  /* steht fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle KRED */
         BEGIN
          /* BETRAG S = OPBETRAG */
            IF (BEMERKUNG<>'' AND BEMERKUNG<>'LEV') THEN
             BEGIN
              if (KHABEN=GROUPKNR) then
               BEGIN
                if (ITKLASSE = 0) then
                 begin
                  BETRAGH = BETRAGS;
                  BETRAGS = NULL;
                 END
                else
                 begin
                  BETRAGS = BETRAGH; 
                  BETRAGH = NULL;                                  
                 end 
               END
              ELSE
               BEGIN
                BETRAGH=NULL;
               END
             END
            ELSE
             BEGIN
              if (KSOLL=GROUPKNR) then
               BEGIN
                if (ITKLASSE = 0) then
                 begin
                  BETRAGS = BETRAGH;
                  BETRAGH = NULL;
                 end
                else
                 begin
                  BETRAGH = BETRAGS;
                  BETRAGS = NULL;                
                 end  
               END
              ELSE
               BEGIN
                BETRAGS=NULL;
               END
             END
         END
       IF (BDOPPBU='J') THEN
        BEGIN  /* doppelte buchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung ansicht */
         IF (KLASSE<>6 AND KLASSE<>7) THEN
          BEGIN
           IF (KNRVON=KNRBIS) THEN /* nur ein Konto */
            BEGIN
             IF (KSOLL=KNRVON) THEN
              BEGIN
               BETRAGH=NULL;
               USTHABEN=NULL;
              END
             ELSE
              BEGIN
               BETRAGS=NULL;
               USTSOLL=NULL;
              END
            END
           ELSE  /* mehrere Konten */
            BEGIN
             /* S und H ungleiche Klassen? */
             IF (NOT (KLASSEGS=KLASSE AND KLASSEGH=KLASSE)) THEN
              IF (KLASSEGS=KLASSE) THEN
               BEGIN
                BETRAGH=NULL;
                USTHABEN=NULL;
               END
              ELSE
               IF (KLASSEGH=KLASSE) THEN
                BEGIN
                 BETRAGS=NULL;
                 USTSOLL=NULL;
                END
            END
          END
        END /* doppelte BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
       ELSE
        BEGIN /* einfache BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
         IF (KLASSE<>6 AND KLASSE<>7) THEN
          BEGIN
           IF (KNRVON=KNRBIS) THEN /* nur ein Konto */
            BEGIN
             IF (KLASSE=1 OR KLASSE=4) THEN
              BEGIN
               if ((KNRVON=KNRBIS) AND (KHABEN=KNRVON)) then
                HDBETRAG = -HDBETRAG;
               IF ((KLASSEGH=KLASSE) and (KSOLL<>KNRVON)) THEN
                BEGIN
                 BETRAGS=-BETRAGH;
                 USTSOLL=-USTSOLL;
                END
              END
             ELSE
              IF (KLASSE=2 OR KLASSE=3) THEN
               IF (KLASSEGS=KLASSE) THEN
                BEGIN
                 BETRAGS=-BETRAGS;
                 USTSOLL=-USTSOLL;
                END
            END
           ELSE  /* mehrere Konten */
            BEGIN
             /* S und H ungleiche Klassen? */
             IF (NOT (KLASSEGS=KLASSE AND KLASSEGH=KLASSE)) THEN
              BEGIN
               IF (KLASSE=1 OR KLASSE=4) THEN
                BEGIN
                 IF (KLASSEGH=KLASSE) THEN
                  BEGIN
                   BETRAGS=-BETRAGH;
                   USTSOLL=-USTSOLL;
                  END
                END
               ELSE
                IF (KLASSE=2 OR KLASSE=3) THEN
                 IF (KLASSEGS=KLASSE) THEN
                  BEGIN
                   BETRAGS=-BETRAGS;
                   USTSOLL=-USTSOLL;
                  END
              END
             ELSE
              BEGIN  /* gleiche Klasse */
               IF ((ARTSOLL=1 AND ARTHABEN=1) OR (ARTSOLL=20 AND ARTHABEN=20) OR (ARTSOLL=19 AND ARTHABEN=19)) then /* umbuchung K oder A-Bank duplizieren */
                BEGIN
                 SUSPEND;
                 BETRAGS=-BETRAGS;
                 USTSOLL=-USTSOLL;
                 HDBETRAG = -HDBETRAG;
                END
              END /* gleiche Klasse = doppelt anzeigen! */
            END /* mehrere Konten */
          END /* nicht DEB KRED */
        END /* einfache BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
       SUSPEND;
      END
    END
   ELSE
    BEGIN /* WDATUM */
     FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, KSTRHABEN, KSTRSOLL, ARTSOLL, ARTHABEN, LBNR from buchung
      WHERE (ONRSOLL=:IONR OR ONRHABEN=:IONR)
      AND ((KSOLL>=:KNRVON AND KSOLL <=:KNRBIS) OR (KHABEN>=:KNRVON AND KHABEN <=:KNRBIS))
      AND (WDatum>=:DTVON and WDatum<=:DTBIS)
      and BETRAG<>0
     INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :KSTRHABEN, :KSTRSOLL, :ARTSOLL, :ARTHABEN, :LBNR
     DO
      BEGIN
       HDBETRAG = 0; HDTEXT = ''; HDART = 0;
       IF ((ARTSOLL=1) or (ARTHABEN=1)) THEN
        BEGIN
         select sum(betrag) from hdbuch where bnr=:bnr into :HDBETRAG;  
         select first 1 text, art from hdbuch where bnr=:bnr into HDTEXT, HDART; 
         if (HDBETRAG is null) then
          HDBETRAG = 0;
         if (HDART is null) then
          HDART = 0;
         if (HDTEXT is null) then
          HDTEXT = '';           
        END
       /* */        
       ONR=:IONR;
       IF (ARTSOLL=1) THEN
        KLASSEGS=1; /* K */
       ELSE
        IF ((ARTSOLL>=10 AND ARTSOLL<=19) or (ARTSOLL>=110 and ARTSOLL<=580)) THEN
         KLASSEGS=2;  /* E*/
        ELSE
         IF ((ARTSOLL>=20 AND ARTSOLL<=24) OR (ARTSOLL=30)) THEN
          KLASSEGS=4; /* A*/
         ELSE
          IF (ARTSOLL=27) THEN
           KLASSEGS=3;  /* P*/
          ELSE
           IF (ARTSOLL=71) THEN
            KLASSEGS=7;   /* KRED*/
           ELSE
            KLASSEGS=6;  /* DEB*/
       IF (ARTHABEN=1) THEN
        KLASSEGH=1; /* K */
       ELSE
        IF ((ARTHABEN>=10 AND ARTHABEN<=19) or (ARTHABEN>=110 and ARTHABEN<=580)) THEN
         KLASSEGH=2;  /* E*/
        ELSE
         IF ((ARTHABEN>=20 AND ARTHABEN<=24) OR (ARTHABEN=30)) THEN
          KLASSEGH=4; /* A*/
         ELSE
          IF (ARTHABEN=27) THEN
           KLASSEGH=3;  /* P*/
          ELSE
           IF (ARTHABEN=71) THEN
            KLASSEGH=7;   /* KRED*/
           ELSE
            KLASSEGH=6;  /* DEB*/
       IF (OPBETRAG IS NOT NULL) THEN
        BEGIN
         IF (OPBETRAG=0) THEN
          BEMERKUNG='SO';
         ELSE
          BEMERKUNG='OP';
        END
       ELSE
        IF (LBNR IS NOT NULL) THEN
         BEMERKUNG='LEV';
        ELSE
         BEMERKUNG='';
       IF (BANKNRSOLL IS NOT NULL) THEN
        BEGIN
         IF (IBANKNRAKT=BANKNRSOLL) THEN
          KSTRSOLL=KSTRSOLL || ' ' || BANKSTR;
          ELSE
           BEGIN
            SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :BANKSTR;
            KSTRSOLL=KSTRSOLL || ' ' || BANKSTR;
            IBANKNRAKT=BANKNRSOLL;
           END
        END
       ELSE
        BEGIN
         IF (:ARTSOLL<>71) THEN
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRSOLL;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KSOLL INTO :KSTRSOLL;
        END
       IF (BANKNRHABEN IS NOT NULL) THEN
        BEGIN
         IF (IBANKNRAKT=BANKNRHABEN) THEN
          KSTRHABEN=KSTRHABEN || ' ' || BANKSTR;
          ELSE
           BEGIN
            SELECT KURZBEZ from Banken where NR=:BANKNRHABEN into :BANKSTR;
            KSTRHABEN=KSTRHABEN || ' ' || BANKSTR;
            IBANKNRAKT=BANKNRHABEN;
           END
        END
       ELSE
        BEGIN
         IF (:ARTHABEN<>71) THEN
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KHABEN INTO :KSTRHABEN;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KHABEN INTO :KSTRHABEN;
        END
       /*Steuer*/
       IF (MWST<>0) THEN
        BEGIN
         USTSATZ=100+MWST;/*1+(MWST/100);*/
         IF ((ARTSOLL>=10 AND ARTSOLL<=19) OR (ARTSOLL=1) or (ARTSOLL>=110 and ARTSOLL<=580)) THEN
          BEGIN
           IF (BDOPPBU='J') THEN
            BEGIN
             BETRAGS=BETRAG;
             USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
             BETRAGH=BETRAG;
             USTHABEN=NULL;
            END
           ELSE
            BEGIN /* Einfache Buch Steuer berechnen */
             BETRAGS=BETRAG;
             BETRAGH=BETRAG;
             USTHABEN=NULL;
             USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
            END
          END
         ELSE
          /* Steuer im Haben?*/
          IF ((ARTHABEN>=10 AND ARTHABEN<=19) OR (ARTHABEN=1) or (ARTHABEN>=110 and ARTHABEN<=580)) THEN
           BEGIN
            IF (BDOPPBU='J') THEN
             BEGIN
              BETRAGH=BETRAG;
              USTHABEN=BETRAG - ((BETRAG * 100) / USTSATZ);
              BETRAGS=BETRAG;
              USTSOLL=NULL;
             END
            ELSE
             BEGIN /* Einfache Buch Steuer berechnen */
              BETRAGS=BETRAG;
              BETRAGH=BETRAG;
              USTHABEN=NULL;
              USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
             END
           END
          ELSE
           BEGIN /* PlausibilitÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤t: Steuer nur auf Aufwand/Ertrag */
            BETRAGS=BETRAG;
            BETRAGH=BETRAG;
            USTSOLL=NULL;
            USTHABEN=NULL;
            MWST=NULL;
           END
        END
       ELSE
        BEGIN /* keine Steuer + einfache BuchFÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung Brutto*/
         BETRAGS=BETRAG;
         BETRAGH=BETRAG;
         USTSOLL=NULL;
         USTHABEN=NULL;
         MWST=NULL;
        END
       IF (KLASSE=6) THEN  /* steht fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle BEW/EIG */
        BEGIN
         /* BETRAG S = OPBETRAG */
         IF (BEMERKUNG<>'' AND BEMERKUNG<>'LEV') THEN
          BEGIN
           if (ARTSOLL=1) then /* gegen Ausgabe gebucht Rene 02.14*/
            BEGIN
             BETRAGH = -BETRAGH;
             USTHABEN = -USTHABEN;
            END
           BETRAGS=BETRAGH;
           USTSOLL=USTHABEN;
           BETRAGH=NULL;
           USTHABEN=NULL;
          END
         ELSE
          BEGIN
           if (ARTSOLL=1) then /* gegen Ausgabe gebucht Rene 02.14*/
            BEGIN
             BETRAGS = -BETRAGS;
             USTSOLL = -USTSOLL;
            END
           BETRAGH=BETRAGS;
           USTHABEN=USTSOLL;
           BETRAGS=NULL;
           USTSOLL=NULL;
          END
         /*Rene Verrechnungen*/
         IF (BANKNRSOLL IS NULL AND BANKNRHABEN IS NULL) THEN
          BEGIN /* VERRECHNUNG */
           IF ((ARTSOLL=24) OR (ARTSOLL=27)) THEN
            BEGIN
             BETRAGH=BETRAGH;
            END
           ELSE
            BEGIN
             BETRAGH=-BETRAGH;
            END
          END
        END
       ELSE
        IF (KLASSE=7) THEN  /* steht fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle KRED */
         BEGIN
          /* BETRAG S = OPBETRAG */
            IF (BEMERKUNG<>'' AND BEMERKUNG<>'LEV') THEN
             BEGIN
              if (KHABEN=GROUPKNR) then
               BEGIN
                if (ITKLASSE = 0) then
                 begin
                  BETRAGH = BETRAGS;
                  BETRAGS = NULL;
                 END
                else
                 begin
                  BETRAGS = BETRAGH; 
                  BETRAGH = NULL;                                  
                 end 
               END
              ELSE
               BEGIN
                BETRAGH=NULL;
               END
             END
            ELSE
             BEGIN
              if (KSOLL=GROUPKNR) then
               BEGIN
                if (ITKLASSE = 0) then
                 begin
                  BETRAGS = BETRAGH;
                  BETRAGH = NULL;
                 end
                else
                 begin
                  BETRAGH = BETRAGS;
                  BETRAGS = NULL;                
                 end  
               END
              ELSE
               BEGIN
                BETRAGS=NULL;
               END
             END
         END
       IF (BDOPPBU='J') THEN
        BEGIN  /* doppelte buchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung ansicht */
         IF (KLASSE<>6 AND KLASSE<>7) THEN
          BEGIN
           IF (KNRVON=KNRBIS) THEN /* nur ein Konto */
            BEGIN
             IF (KSOLL=KNRVON) THEN
              BEGIN
               BETRAGH=NULL;
               USTHABEN=NULL;
              END
             ELSE
              BEGIN
               BETRAGS=NULL;
               USTSOLL=NULL;
              END
            END
           ELSE  /* mehrere Konten */
            BEGIN
             /* S und H ungleiche Klassen? */
             IF (NOT (KLASSEGS=KLASSE AND KLASSEGH=KLASSE)) THEN
              IF (KLASSEGS=KLASSE) THEN
               BEGIN
                BETRAGH=NULL;
                USTHABEN=NULL;
               END
              ELSE
               IF (KLASSEGH=KLASSE) THEN
                BEGIN
                 BETRAGS=NULL;
                 USTSOLL=NULL;
                END
            END
          END
        END /* doppelte BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
       ELSE
        BEGIN /* einfache BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
         IF (KLASSE<>6 AND KLASSE<>7) THEN
          BEGIN
           IF (KNRVON=KNRBIS) THEN /* nur ein Konto */
            BEGIN
             IF (KLASSE=1 OR KLASSE=4) THEN
              BEGIN
               if ((KNRVON=KNRBIS) AND (KHABEN=KNRVON)) then
                HDBETRAG = -HDBETRAG;              
               IF ((KLASSEGH=KLASSE) and (KSOLL<>KNRVON)) THEN
                BEGIN
                 BETRAGS=-BETRAGH;
                 USTSOLL=-USTSOLL;
                END
              END
             ELSE
              IF (KLASSE=2 OR KLASSE=3) THEN
               IF (KLASSEGS=KLASSE) THEN
                BEGIN
                 BETRAGS=-BETRAGS;
                 USTSOLL=-USTSOLL;
                END
            END
           ELSE  /* mehrere Konten */
            BEGIN
             /* S und H ungleiche Klassen? */
             IF (NOT (KLASSEGS=KLASSE AND KLASSEGH=KLASSE)) THEN
              BEGIN
               IF (KLASSE=1 OR KLASSE=4) THEN
                BEGIN
                 IF (KLASSEGH=KLASSE) THEN
                  BEGIN
                   BETRAGS=-BETRAGH;
                   USTSOLL=-USTSOLL;
                  END
                END
               ELSE
                IF (KLASSE=2 OR KLASSE=3) THEN
                 IF (KLASSEGS=KLASSE) THEN
                  BEGIN
                   BETRAGS=-BETRAGS;
                   USTSOLL=-USTSOLL;
                  END
              END
             ELSE
              BEGIN  /* gleiche Klasse = doppelt anzeigen! */
               IF ((ARTSOLL=1 AND ARTHABEN=1) OR (ARTSOLL=20 AND ARTHABEN=20) OR (ARTSOLL=19 AND ARTHABEN=19)) then /* umbuchung K oder A-Bank duplizieren */
                BEGIN
                 SUSPEND;
                 BETRAGS=-BETRAGS;
                 USTSOLL=-USTSOLL;
                 HDBETRAG = -HDBETRAG;
                END               
              END /* gleiche Klasse = doppelt anzeigen! */
            END /* mehrere Konten */
          END /* nicht DEB KRED */
        END /* einfache BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
       suspend;
      END
    END /* WDATUM */
  END
 ELSE
  /*                               */
  /* BUCHUNGSÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“BERSICHT NACH KONTEN */
  /*                               */
  BEGIN
   IF (BWDATUM='N') THEN
    BEGIN
     /* KLASSEBIS setzen */
     IF (KLASSE=1) THEN
      KLASSEBIS=1;
     ELSE
      IF (KLASSE=10) THEN
       KLASSEBIS=19;
      ELSE
       IF (KLASSE=20) THEN
        KLASSEBIS=24;
       ELSE
        IF (KLASSE=27) THEN
         KLASSEBIS=27;
        ELSE
         IF (KLASSE=60) THEN
          KLASSEBIS=64;
         ELSE
          IF (KLASSE=71) THEN
           KLASSEBIS=71;
          ELSE
           IF (KLASSE=0) THEN  /* alle Klassen */
            KLASSEBIS=580;
           ELSE
            IF (KLASSE=110) THEN
             KLASSEBIS=580;
     /* alle Konten einzeln */
     FOR SELECT KNR, KKLASSE from konten
      where ((ONR=:IONR) OR (ONR=0 AND (KKLASSE=71 OR KKLASSE=30)))
      and ((KKLASSE>=:KLASSE AND KKLASSE<=:KLASSEBIS) or (KKLASSE>=110))
      and (KNR>=:KNRVON AND KNR<=:KNRBIS)
      ORDER BY KKLASSE
     INTO :GROUPKNR, :KLASSE
     do
      begin /* for Konten */
       IF (KLASSE=1) THEN
        KLASSE=1;  /* P*/
       ELSE
        IF ((KLASSE>=10 AND KLASSE<=19) or (KLASSE>=110 and KLASSE<=580)) THEN
         KLASSE=2;  /* E*/
        ELSE
         IF ((KLASSE>=20 AND KLASSE<=24) OR (KLASSE=30)) THEN
          KLASSE=4; /* A*/
         ELSE
          IF (KLASSE=27) THEN
           KLASSE=3;  /* P*/
          ELSE
           IF (KLASSE=71) THEN
            KLASSE=7;   /* KRED*/
           ELSE
            KLASSE=6;  /* DEB*/
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, KSTRHABEN, KSTRSOLL, ARTSOLL, ARTHABEN,LBNR, KAUSZUGBLATT, KAUSZUGNR from buchung    
        WHERE (ONRSOLL=:IONR OR ONRHABEN=:IONR)                                                                                                                                              
        AND ((KSOLL=:GROUPKNR) OR (KHABEN=:GROUPKNR))
        AND (Datum>=:DTVON and Datum<=:DTBIS)
        and BETRAG<>0
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :KSTRHABEN, :KSTRSOLL, :ARTSOLL, :ARTHABEN,:LBNR, :iKAUSZUGBLATT, :iKAUSZUGNR
       DO
        BEGIN /* for buchungen */
        KAUSZUGBLATT=:iKAUSZUGBLATT; KAUSZUGNR= :iKAUSZUGNR;
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF ((ARTSOLL=1) or (ARTHABEN=1)) THEN
          BEGIN
           select sum(betrag) from hdbuch where bnr=:bnr into :HDBETRAG;  
           select first 1 text, art from hdbuch where bnr=:bnr into HDTEXT, HDART; 
           if (HDBETRAG is null) then
            HDBETRAG = 0;
           if (HDART is null) then
            HDART = 0;
           if (HDTEXT is null) then
            HDTEXT = '';             
           if ((KHABEN=GROUPKNR) and (ARTSOLL=ARTHABEN)) then
            begin
             HDBETRAG = -HDBETRAG;
            end  
          END
         /* */        
         ONR=:IONR;
         IF (ARTSOLL=1) THEN
          KLASSEGS=1; /* K */
         ELSE
          IF ((ARTSOLL>=10 AND ARTSOLL<=19) or (ARTSOLL>=110 and ARTSOLL<=580)) THEN
           KLASSEGS=2;  /* E*/
          ELSE
           IF ((ARTSOLL>=20 AND ARTSOLL<=24) OR (ARTSOLL=30)) THEN
            KLASSEGS=4; /* A*/
           ELSE
            IF (ARTSOLL=27) THEN
             KLASSEGS=3;  /* P*/
            ELSE
             IF (ARTSOLL=71) THEN
              KLASSEGS=7;   /* KRED*/
             ELSE
              KLASSEGS=6;  /* DEB*/
         IF (ARTHABEN=1) THEN
          KLASSEGH=1; /* K */
         ELSE
          IF ((ARTHABEN>=10 AND ARTHABEN<=19) or (ARTHABEN>=110 and ARTHABEN<=580)) THEN
           KLASSEGH=2;  /* E*/
          ELSE
           IF ((ARTHABEN>=20 AND ARTHABEN<=24) OR (ARTHABEN=30)) THEN
            KLASSEGH=4; /* A*/
           ELSE
            IF (ARTHABEN=27) THEN
             KLASSEGH=3;  /* P*/
            ELSE
             IF (ARTHABEN=71) THEN
              KLASSEGH=7;   /* KRED*/
             ELSE
              KLASSEGH=6;  /* DEB*/
         IF (OPBETRAG IS NOT NULL) THEN
          BEGIN
           IF (OPBETRAG=0) THEN
            BEMERKUNG='SO';
           ELSE
            BEMERKUNG='OP';
          END
         ELSE
          IF (LBNR IS NOT NULL) THEN
           BEMERKUNG='LEV';
          ELSE
           BEMERKUNG='';
         IF (BANKNRSOLL IS NOT NULL) THEN
          BEGIN
           IF (IBANKNRAKT=BANKNRSOLL) THEN
            KSTRSOLL=KSTRSOLL || ' ' || BANKSTR;
           ELSE
            BEGIN
             SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :BANKSTR;
             KSTRSOLL=KSTRSOLL || ' ' || BANKSTR;
             IBANKNRAKT=BANKNRSOLL;
            END
          END
         ELSE
          BEGIN
           IF (:ARTSOLL<>71) THEN
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRSOLL;
           ELSE
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KSOLL INTO :KSTRSOLL;
          END
         IF (BANKNRHABEN IS NOT NULL) THEN
          BEGIN
         IF (IBANKNRAKT=BANKNRHABEN) THEN
          KSTRHABEN=KSTRHABEN || ' ' || BANKSTR;
          ELSE
           BEGIN
            SELECT KURZBEZ from Banken where NR=:BANKNRHABEN into :BANKSTR;
            KSTRHABEN=KSTRHABEN || ' ' || BANKSTR;
            IBANKNRAKT=BANKNRHABEN;
           END
          END
         ELSE
          BEGIN
           IF (:ARTHABEN<>71) THEN
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KHABEN INTO :KSTRHABEN;
           ELSE
            SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KHABEN INTO :KSTRHABEN;
          END
         /*Steuer*/
         IF (MWST<>0) THEN
          BEGIN
           USTSATZ=100+MWST;/*1+(MWST/100);*/
           IF ((ARTSOLL>=10 AND ARTSOLL<=19) OR (ARTSOLL=1) or (ARTSOLL>=110 and ARTSOLL<=580)) THEN
            BEGIN
             IF (BDOPPBU='J') THEN
              BEGIN
               BETRAGS=BETRAG;
               USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
               BETRAGH=BETRAG;
               USTHABEN=NULL;
              END
             ELSE
              BEGIN /* Einfache Buch Steuer berechnen */
               BETRAGS=BETRAG;
               BETRAGH=BETRAG;
               USTHABEN=NULL;
               USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
              END
            END
           ELSE
            /* Steuer im Haben?*/
            IF ((ARTHABEN>=10 AND ARTHABEN<=19) OR (ARTHABEN=1) or (ARTHABEN>=110 and ARTHABEN<=580)) THEN
             BEGIN
              IF (BDOPPBU='J') THEN
               BEGIN
                BETRAGH=BETRAG;
                USTHABEN=BETRAG - ((BETRAG * 100) / USTSATZ);
                BETRAGS=BETRAG;
                USTSOLL=NULL;
               END
              ELSE
               BEGIN /* Einfache Buch Steuer berechnen */
                BETRAGS=BETRAG;
                BETRAGH=BETRAG;
                USTHABEN=NULL;
                USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
               END
             END
            ELSE
             BEGIN /* PlausibilitÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤t: Steuer nur auf Aufwand/Ertrag */
              BETRAGS=BETRAG;
              BETRAGH=BETRAG;
              USTSOLL=NULL;
              USTHABEN=NULL;
              MWST=NULL;
             END
          END
         ELSE
          BEGIN /* keine Steuer + einfache BuchFÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung Brutto*/
           BETRAGS=BETRAG;
           BETRAGH=BETRAG;
           USTSOLL=NULL;
           USTHABEN=NULL;
           MWST=NULL;
          END
         IF (KLASSE=6) THEN  /* steht fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle BEW/EIG */
          BEGIN
            /* BETRAG S = OPBETRAG */
           IF (BEMERKUNG<>'' AND BEMERKUNG<>'LEV') THEN
            BEGIN
             if (ARTSOLL=1) then /* gegen Ausgabe gebucht Rene 02.14*/
              BEGIN
               BETRAGH = -BETRAGH;
               USTHABEN = -USTHABEN;
              END
             BETRAGS=BETRAGH;
             USTSOLL=USTHABEN;
             BETRAGH=NULL;
             USTHABEN=NULL;
            END
           ELSE
            BEGIN
             if (ARTSOLL=1) then /* gegen Ausgabe gebucht Rene 02.14*/
              BEGIN
               BETRAGS = -BETRAGS;
               USTSOLL = -USTSOLL;
              END
             BETRAGH=BETRAGS;
             USTHABEN=USTSOLL;
             BETRAGS=NULL;
             USTSOLL=NULL;
            END
           /*Rene Verrechnungen*/
           IF (BANKNRSOLL IS NULL AND BANKNRHABEN IS NULL) THEN
            BEGIN /* VERRECHNUNG */
             IF ((ARTSOLL=24) OR (ARTSOLL=27)) THEN
              BEGIN
               BETRAGH=BETRAGH;
              END
             ELSE
              BEGIN
               BETRAGH=-BETRAGH;
              END
            END
          END
         ELSE
          IF (KLASSE=7) THEN  /* steht fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle KRED */
           BEGIN
            /* BETRAG S = OPBETRAG */
            IF (BEMERKUNG<>'' AND BEMERKUNG<>'LEV') THEN
             BEGIN
              if (KHABEN=GROUPKNR) then
               BEGIN
                if (ITKLASSE = 0) then
                 begin
                  BETRAGH = BETRAGS;
                  BETRAGS = NULL;
                 END
                else
                 begin
                  BETRAGS = BETRAGH; 
                  BETRAGH = NULL;                                  
                 end 
               END
              ELSE
               BEGIN
                BETRAGH=NULL;
               END
             END
            ELSE
             BEGIN
              if (KSOLL=GROUPKNR) then
               BEGIN
                if (ITKLASSE = 0) then
                 begin
                  BETRAGS = BETRAGH;
                  BETRAGH = NULL;
                 end
                else
                 begin
                  BETRAGH = BETRAGS;
                  BETRAGS = NULL;                
                 end  
               END
              ELSE
               BEGIN
                BETRAGS=NULL;
               END
             END
           END
         IF (BDOPPBU='J') THEN
          BEGIN  /* doppelte buchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung ansicht */
           IF (KLASSE<>6 AND KLASSE<>7) THEN
            BEGIN
             IF (KSOLL=GROUPKNR) THEN
              BEGIN
               BETRAGH=NULL;
               USTHABEN=NULL;
              END
             ELSE
              IF (KHABEN=GROUPKNR) THEN
               BEGIN
                BETRAGS=NULL;
                USTSOLL=NULL;
               END
            END /* KLASSE <>6 Klasse <>7 */
          END /* doppelte BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
         ELSE
          BEGIN /* einfache BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
           IF (KLASSE<>6 AND KLASSE<>7) THEN
            BEGIN
             IF (KLASSE=1 OR KLASSE=4) THEN
              BEGIN
               IF (ARTSOLL=1 AND ARTHABEN=1) THEN /* UMBUCHUNG */
                BEGIN
                 IF (GROUPKNR=KHABEN) THEN
                  BEGIN
                   BETRAGS=-BETRAGH;
                   USTSOLL=-USTSOLL;
                  END
                END
               ELSE
                BEGIN
                 IF (KLASSEGH=KLASSE AND KSOLL<>GROUPKNR) THEN
                  BEGIN
                   BETRAGS=-BETRAGH;
                   USTSOLL=-USTSOLL;
                  END
                END
              END
             ELSE
              IF (KLASSE=2 OR KLASSE=3) THEN
               BEGIN
                IF (ARTSOLL=19 AND ARTHABEN=19) THEN /* UMBUCHUNG */
                 BEGIN
                  IF (GROUPKNR=KSOLL) THEN
                   BEGIN
                    BETRAGS=-BETRAGH;
                    USTSOLL=-USTSOLL;
                   END
                 END
                ELSE
                 BEGIN
                  IF (KLASSEGS=KLASSE) THEN
                   BEGIN
                    BETRAGS=-BETRAGS;
                    USTSOLL=-USTSOLL;
                    if ((KLASSE = 3) and (GROUPKNR=KHABEN)) THEN
                     BEGIN
                      BETRAGS=-BETRAGS;
                      USTSOLL=-USTSOLL;
                     END
                   END
                 END
               END
            END /* nicht DEB KRED */
          END /* einfache BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
         suspend;
        END /* for Buchungen */
      END /* for Konten */
    END /* nicht W-Datum */
   ELSE
  BEGIN /* WDATUM */
   /* KLASSEBIS setzen */
   IF (KLASSE=1) THEN
    KLASSEBIS=1;
   ELSE
    IF (KLASSE=10) THEN
     KLASSEBIS=19;
    ELSE
     IF (KLASSE=20) THEN
      KLASSEBIS=24;
     ELSE
      IF (KLASSE=27) THEN
       KLASSEBIS=27;
      ELSE
       IF (KLASSE=60) THEN
        KLASSEBIS=64;
       ELSE
        IF (KLASSE=71) THEN
         KLASSEBIS=71;
        ELSE
         IF (KLASSE=0) THEN  /* alle Klassen */
          KLASSEBIS=580;
         ELSE
          IF (KLASSE=110) THEN
           KLASSEBIS=580;
    /* alle Konten einzeln */
     FOR SELECT KNR, KKLASSE from konten
      where ((ONR=:IONR) OR (ONR=0 AND (KKLASSE=71 OR KKLASSE=30)))
      and ((KKLASSE>=:KLASSE AND KKLASSE<=:KLASSEBIS) or (KKLASSE>=110))
      and (KNR>=:KNRVON AND KNR<=:KNRBIS)
      ORDER BY KKLASSE
     INTO :GROUPKNR, :KLASSE
   do
    begin /* for Konten */
     IF (KLASSE=1) THEN 
       KLASSE=1;  /* P*/
     ELSE
      IF ((KLASSE>=10 AND KLASSE<=19) or (KLASSE>=110 and KLASSE<=580)) THEN
       KLASSE=2;  /* E*/
      ELSE
       IF ((KLASSE>=20 AND KLASSE<=24) OR (KLASSE=30)) THEN
        KLASSE=4; /* A*/
       ELSE
        IF (KLASSE=27) THEN
         KLASSE=3;  /* P*/
        ELSE
         IF (KLASSE=71) THEN
          KLASSE=7;   /* KRED*/
         ELSE
          KLASSE=6;  /* DEB*/
     FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, KSTRHABEN, KSTRSOLL, ARTSOLL, ARTHABEN, LBNR,  KAUSZUGBLATT,KAUSZUGNR from buchung
      WHERE (ONRSOLL=:IONR OR ONRHABEN=:IONR)
      AND ((KSOLL=:GROUPKNR) OR (KHABEN=:GROUPKNR))
      AND (WDatum>=:DTVON and WDatum<=:DTBIS)
      and BETRAG<>0
     INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :KSTRHABEN, :KSTRSOLL, :ARTSOLL, :ARTHABEN, :LBNR, :iKAUSZUGBLATT,:iKAUSZUGNR
     DO
      BEGIN /* for buchungen */
       KAUSZUGBLATT=:iKAUSZUGBLATT; KAUSZUGNR= :iKAUSZUGNR;
       HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF ((ARTSOLL=1) or (ARTHABEN=1)) THEN
          BEGIN
		   select sum(betrag) from hdbuch where bnr=:bnr into :HDBETRAG;  
           select first 1 text, art from hdbuch where bnr=:bnr into HDTEXT, HDART; 
           if (HDBETRAG is null) then
            HDBETRAG = 0;
           if (HDART is null) then
            HDART = 0;
           if (HDTEXT is null) then
            HDTEXT = '';             
           if ((KHABEN=GROUPKNR) and (ARTSOLL=ARTHABEN)) then
            begin
             HDBETRAG = -HDBETRAG;
            end
          END
         /* */      
       ONR=:IONR;
       IF (ARTSOLL=1) THEN
        KLASSEGS=1; /* K */
       ELSE
        IF ((ARTSOLL>=10 AND ARTSOLL<=19) or (ARTSOLL>=110 and ARTSOLL<=580)) THEN
         KLASSEGS=2;  /* E*/
        ELSE
         IF ((ARTSOLL>=20 AND ARTSOLL<=24) OR (ARTSOLL=30)) THEN
          KLASSEGS=4; /* A*/
         ELSE
          IF (ARTSOLL=27) THEN
           KLASSEGS=3;  /* P*/
          ELSE
           IF (ARTSOLL=71) THEN
            KLASSEGS=7;   /* KRED*/
           ELSE
            KLASSEGS=6;  /* DEB*/
       IF (ARTHABEN=1) THEN
        KLASSEGH=1; /* K */
       ELSE
        IF ((ARTHABEN>=10 AND ARTHABEN<=19) or (ARTHABEN>=110 and ARTHABEN<=580)) THEN
         KLASSEGH=2;  /* E*/
        ELSE
         IF ((ARTHABEN>=20 AND ARTHABEN<=24) OR (ARTHABEN=30)) THEN
          KLASSEGH=4; /* A*/
         ELSE
          IF (ARTHABEN=27) THEN
           KLASSEGH=3;  /* P*/
          ELSE
           IF (ARTHABEN=71) THEN
            KLASSEGH=7;   /* KRED*/
           ELSE
            KLASSEGH=6;  /* DEB*/
       IF (OPBETRAG IS NOT NULL) THEN
        BEGIN
         IF (OPBETRAG=0) THEN
          BEMERKUNG='SO';
         ELSE
          BEMERKUNG='OP';
        END
       ELSE
        IF (LBNR IS NOT NULL) THEN
         BEMERKUNG='LEV';
        ELSE
         BEMERKUNG='';
       IF (BANKNRSOLL IS NOT NULL) THEN
        BEGIN
         IF (IBANKNRAKT=BANKNRSOLL) THEN
          KSTRSOLL=KSTRSOLL || ' ' || BANKSTR;
          ELSE
           BEGIN
            SELECT KURZBEZ from Banken where NR=:BANKNRSOLL into :BANKSTR;
            KSTRSOLL=KSTRSOLL || ' ' || BANKSTR;
            IBANKNRAKT=BANKNRSOLL;
           END
        END
       ELSE
        BEGIN
         IF (:ARTSOLL<>71) THEN
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KSOLL INTO :KSTRSOLL;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KSOLL INTO :KSTRSOLL;
        END
       IF (BANKNRHABEN IS NOT NULL) THEN
        BEGIN
         IF (IBANKNRAKT=BANKNRHABEN) THEN
          KSTRHABEN=KSTRHABEN || ' ' || BANKSTR;
          ELSE
           BEGIN
            SELECT KURZBEZ from Banken where NR=:BANKNRHABEN into :BANKSTR;
            KSTRHABEN=KSTRHABEN || ' ' || BANKSTR;
            IBANKNRAKT=BANKNRHABEN;
           END
        END
       ELSE
        BEGIN
         IF (:ARTHABEN<>71) THEN
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:IONR AND KNR=:KHABEN INTO :KSTRHABEN;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=0 AND KNR=:KHABEN INTO :KSTRHABEN;
        END
       /*Steuer*/
       IF (MWST<>0) THEN
        BEGIN
         USTSATZ=100+MWST;/*1+(MWST/100);*/
         IF ((ARTSOLL>=10 AND ARTSOLL<=19) OR (ARTSOLL=1) or (ARTSOLL>=110 and ARTSOLL<=580)) THEN
          BEGIN
           IF (BDOPPBU='J') THEN
            BEGIN
             BETRAGS=BETRAG;
             USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
             BETRAGH=BETRAG;
             USTHABEN=NULL;
            END
           ELSE
            BEGIN /* Einfache Buch Steuer berechnen */
             BETRAGS=BETRAG;
             BETRAGH=BETRAG;
             USTHABEN=NULL;
             USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
            END
          END
         ELSE
          /* Steuer im Haben?*/
          IF ((ARTHABEN>=10 AND ARTHABEN<=19) OR (ARTHABEN=1) or (ARTHABEN>=110 and ARTHABEN<=580)) THEN
           BEGIN
            IF (BDOPPBU='J') THEN
             BEGIN
              BETRAGH=BETRAG; /* RENE 05.08 =BETRAGS */
              USTHABEN=BETRAG - ((BETRAG * 100) / USTSATZ);
              BETRAGS=BETRAG;
              USTSOLL=NULL;
             END
            ELSE
             BEGIN /* Einfache Buch Steuer berechnen */
              BETRAGS=BETRAG;
              BETRAGH=BETRAG;
              USTHABEN=NULL;
              USTSOLL=BETRAG - ((BETRAG * 100) / USTSATZ);
             END
           END
          ELSE
           BEGIN /* PlausibilitÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤t: Steuer nur auf Aufwand/Ertrag */
            BETRAGS=BETRAG;
            BETRAGH=BETRAG;
            USTSOLL=NULL;
            USTHABEN=NULL;
            MWST=NULL;
           END
        END
       ELSE
        BEGIN /* keine Steuer + einfache BuchFÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung Brutto*/
         BETRAGS=BETRAG;
         BETRAGH=BETRAG;
         USTSOLL=NULL;
         USTHABEN=NULL;
         MWST=NULL;
        END
       IF (KLASSE=6) THEN  /* steht fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle BEW/EIG */
        BEGIN
         /* BETRAG S = OPBETRAG */
         IF (BEMERKUNG<>'' AND BEMERKUNG<>'LEV') THEN
          BEGIN
           if (ARTSOLL=1) then /* gegen Ausgabe gebucht Rene 02.14*/
            BEGIN
             BETRAGH = -BETRAGH;
             USTHABEN = -USTHABEN;
            END
           BETRAGS=BETRAGH;
           USTSOLL=USTHABEN;
           BETRAGH=NULL;
           USTHABEN=NULL;
          END
         ELSE
          BEGIN
           if (ARTSOLL=1) then /* gegen Ausgabe gebucht Rene 02.14*/
            BEGIN
             BETRAGS = -BETRAGS;
             USTSOLL = -USTSOLL;
            END
           BETRAGH=BETRAGS;
           USTHABEN=USTSOLL;
           BETRAGS=NULL;
           USTSOLL=NULL;
          END
         /*Rene Verrechnungen*/
         IF (BANKNRSOLL IS NULL AND BANKNRHABEN IS NULL) THEN
          BEGIN /* VERRECHNUNG */
           IF ((ARTSOLL=24) OR (ARTSOLL=27)) THEN
            BEGIN
             BETRAGH=BETRAGH;
            END
           ELSE
            BEGIN
             BETRAGH=-BETRAGH;
            END
          END
        END
       ELSE
        IF (KLASSE=7) THEN  /* steht fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r alle KRED */
         BEGIN
          /* BETRAG S = OPBETRAG */
            IF (BEMERKUNG<>'' AND BEMERKUNG<>'LEV') THEN
             BEGIN
              if (KHABEN=GROUPKNR) then
               BEGIN
                if (ITKLASSE = 0) then
                 begin
                  BETRAGH = BETRAGS;
                  BETRAGS = NULL;
                 END
                else
                 begin
                  BETRAGS = BETRAGH; 
                  BETRAGH = NULL;                                  
                 end 
               END
              ELSE
               BEGIN
                BETRAGH=NULL;
               END
             END
            ELSE
             BEGIN
              if (KSOLL=GROUPKNR) then
               BEGIN
                if (ITKLASSE = 0) then
                 begin
                  BETRAGS = BETRAGH;
                  BETRAGH = NULL;
                 end
                else
                 begin
                  BETRAGH = BETRAGS;
                  BETRAGS = NULL;                
                 end  
               END
              ELSE
               BEGIN
                BETRAGS=NULL;
               END
             END
         END
       IF (BDOPPBU='J') THEN
        BEGIN  /* doppelte buchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung ansicht */
         IF (KLASSE<>6 AND KLASSE<>7) THEN
          BEGIN
           IF (KSOLL=GROUPKNR) THEN
            BEGIN
             BETRAGH=NULL;
             USTHABEN=NULL;
            END
           ELSE
            IF (KHABEN=GROUPKNR) THEN
             BEGIN
              BETRAGS=NULL;
              USTSOLL=NULL;
             END
          END /* KLASSE <>6 Klasse <>7 */
        END /* doppelte BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
       ELSE
        BEGIN /* einfache BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
         IF (KLASSE<>6 AND KLASSE<>7) THEN
          BEGIN
           IF (KLASSE=1 OR KLASSE=4) THEN
            BEGIN
             IF (ARTSOLL=1 AND ARTHABEN=1) THEN /* UMBUCHUNG */
              BEGIN
               IF (GROUPKNR=KHABEN) THEN
                BEGIN
                 BETRAGS=-BETRAGH;
                 USTSOLL=-USTSOLL;
                END
              END
             ELSE
              BEGIN
               IF (KLASSEGH=KLASSE AND KSOLL<>GROUPKNR) THEN
                BEGIN
                 BETRAGS=-BETRAGH;
                 USTSOLL=-USTSOLL;
                END
              END
            END
           ELSE
            IF (KLASSE=2 OR KLASSE=3) THEN
             BEGIN
              IF (ARTSOLL=19 AND ARTHABEN=19) THEN /* UMBUCHUNG */
               BEGIN
                IF (GROUPKNR=KSOLL) THEN
                 BEGIN
                  BETRAGS=-BETRAGH;
                  USTSOLL=-USTSOLL;
                 END
               END
              ELSE
               BEGIN
                IF (KLASSEGS=KLASSE) THEN
                 BEGIN
                  BETRAGS=-BETRAGS;
                  USTSOLL=-USTSOLL;
                  if ((KLASSE = 3) and (GROUPKNR=KHABEN)) THEN
                   BEGIN
                    BETRAGS=-BETRAGS;
                    USTSOLL=-USTSOLL;
                   END
                 END
               END
             END
          END /* nicht DEB KRED */
        END /* einfache BuchfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung */
       suspend;
      END /* for Buchungen */
     END /* for Konten */
    END /* WDATUM */
  END  /* BUCHUNGSÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“BERSICHT NACH KONTEN */
END
