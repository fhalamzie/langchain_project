-- Prozedur: KONTOAUSZUG
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE KONTOAUSZUG
DECLARE VARIABLE KKLASSE INTEGER;
DECLARE VARIABLE KSOLL INTEGER;
DECLARE VARIABLE KHABEN INTEGER;
DECLARE VARIABLE ARTS INTEGER;
DECLARE VARIABLE ARTH INTEGER;
DECLARE VARIABLE BANKNRSOLL INTEGER;
DECLARE VARIABLE BANKNRHABEN INTEGER;
DECLARE VARIABLE SPLITNR INTEGER;
DECLARE VARIABLE BANKNR INTEGER;
DECLARE VARIABLE TEMPONR INTEGER;
DECLARE VARIABLE ONRSOLL INTEGER;
DECLARE VARIABLE ONRHABEN INTEGER;
DECLARE VARIABLE IAKTOBJ INTEGER;
DECLARE VARIABLE LBNR INTEGER;
BEGIN
 KONTO=IKNR;
 HDBETRAG = 0; HDTEXT = ''; HDART = 0;
 if (IONR<0) then
  IAKTOBJ=-IONR;
 else
  IAKTOBJ=IONR;
 select KKLASSE from konten where ONR=:IAKTOBJ and KNR=:IKNR INTO KKLASSE;
 if (KKLASSE IS NULL) THEN
  BEGIN
   select KKLASSE from konten where ONR=0 and KNR=:IKNR INTO KKLASSE;
   IONR=0;
  END
 IF ((KKLASSE<60) OR (KKLASSE>=110 and KKLASSE<=580)) THEN
  BEGIN
   if ((IONR<0) and ((KKLASSE=1) or (KKLASSE>=19))) then
    begin
     /*DATUM*/
     IF (BWDATUM<>'J') THEN
      BEGIN
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, BRENNSTMENGE, ONRSOLL, ONRHABEN, KAUSZUGNR, KAUSZUGBLATT, BNR, NICHTUMLEGEN, artsoll, arthaben from buchung
        WHERE ((KSOLL=:IKNR) OR (KHABEN=:IKNR))
        AND (Datum>=:DTVON and Datum<=:DTBIS)
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :BRENNSTMENGE, :ONRSOLL, :ONRHABEN, :KAUSZUGNR, :KAUSZUGBLATT, :BNR, :NICHTUMLEGEN, :arts, :arth
       DO
        BEGIN
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF (KKLASSE = 1) THEN
          BEGIN
           select sum(betrag) from hdbuch where bnr=:bnr into :HDBETRAG;  
           select first 1 text, art from hdbuch where bnr=:bnr into HDTEXT, HDART;
           if (HDBETRAG is null) then
            HDBETRAG = 0;
           if (HDTEXT is null) then
            HDTEXT = '';
           if (HDART is null) then
            HDART = 0;  
           if ((KHABEN=IKNR) and (arts=arth)) then
            HDBETRAG = -HDBETRAG;
          END
         ELSE
          BEGIN
           HDBETRAG = 0; HDTEXT = ''; HDART = 0;
          END
         /* */
         IF (KSOLL=IKNR) THEN
          BEGIN
           IF (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KHABEN;
           TEMPONR=ONRHABEN;
           BANKNR=BANKNRHABEN;
          END
         ELSE
          BEGIN
           IF (NOT (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27)) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KSOLL;
           TEMPONR=ONRSOLL;
           BANKNR=BANKNRSOLL;
          END
         ONR=TEMPONR;
         IF (BANKNR IS NOT NULL) THEN
          SELECT KURZBEZ from banken where NR=:BANKNR
          into :GKONTOSTR;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:TEMPONR AND KNR=:GKONTO
          into :GKONTOSTR;
         /* Soll von Lieferanten */
         IF ((IONR<0) and (ARTS=1) and (ARTH=71) and (ONR=0)) THEN
          ONR=ONRSOLL;            
         IF (BETRAG<>0) THEN
          BEGIN
           IF (KKLASSE<>30) THEN
            SUSPEND;
           ELSE
            SUSPEND;
          END
        END
      END
     ELSE
      BEGIN /* WDATUM */
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG,BANKNRSOLL, BANKNRHABEN, BRENNSTMENGE, ONRSOLL, ONRHABEN, KAUSZUGNR, KAUSZUGBLATT, BNR, NICHTUMLEGEN, artsoll, arthaben from buchung
       WHERE ((KSOLL=:IKNR) OR (KHABEN=:IKNR))
       AND (WDatum>=:DTVON and WDatum<=:DTBIS)
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :BRENNSTMENGE, :ONRSOLL, :ONRHABEN, :KAUSZUGNR, :KAUSZUGBLATT, :BNR, :NICHTUMLEGEN, :arts, :arth
       DO
        BEGIN
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF (KKLASSE = 1) THEN
          BEGIN
           select sum(betrag) from hdbuch where bnr=:bnr into :HDBETRAG;  
           select first 1 text, art from hdbuch where bnr=:bnr into HDTEXT, HDART;
           if (HDBETRAG is null) then
            HDBETRAG = 0;
           if (HDTEXT is null) then
            HDTEXT = '';
           if (HDART is null) then
            HDART = 0;             
           if ((KHABEN=IKNR) and (arts=arth)) then
            HDBETRAG = -HDBETRAG;
          END
         ELSE
          BEGIN
           HDBETRAG = 0; HDTEXT = ''; HDART = 0;
          END
         /* */        
         IF (KSOLL=IKNR) THEN
          BEGIN
           IF (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KHABEN;
           TEMPONR=ONRHABEN;
           BANKNR=BANKNRHABEN;
          END
         ELSE
          BEGIN
           IF (NOT (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27)) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
          GKONTO=KSOLL;
          TEMPONR=ONRSOLL;
          BANKNR=BANKNRSOLL;
          END
         ONR=TEMPONR;
         IF (BANKNR IS NOT NULL) THEN
          SELECT KURZBEZ from banken where NR=:BANKNR
          into :GKONTOSTR;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:TEMPONR AND KNR=:GKONTO
          into :GKONTOSTR;
         /* Soll von Lieferanten */
         IF ((IONR<0) and (ARTS=1) and (ARTH=71) and (ONR=0)) THEN
          ONR=ONRSOLL;           
         IF (BETRAG<>0) THEN
          BEGIN
           IF (KKLASSE<>30) THEN
            SUSPEND;
           ELSE
            SUSPEND;
          END
        END
      END
    end
   else /*nich alle objekte oder falsche kontenklasse*/
    begin
     /*DATUM*/
     IF (BWDATUM<>'J') THEN
      BEGIN
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, BRENNSTMENGE, ONRSOLL, ONRHABEN, KAUSZUGNR, KAUSZUGBLATT, BNR, NICHTUMLEGEN, artsoll, arthaben from buchung
        WHERE ((ONRSOLL=:IONR and KSOLL=:IKNR) OR (ONRHABEN=:IONR and KHABEN=:IKNR))
        AND (Datum>=:DTVON and Datum<=:DTBIS)
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :BRENNSTMENGE, :ONRSOLL, :ONRHABEN, :KAUSZUGNR, :KAUSZUGBLATT, :BNR, :NICHTUMLEGEN, :arts, :arth
       DO
        BEGIN
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF (KKLASSE = 1) THEN
          BEGIN
           select sum(betrag) from hdbuch where bnr=:bnr into :HDBETRAG;  
           select first 1 text, art from hdbuch where bnr=:bnr into HDTEXT, HDART;
           if (HDBETRAG is null) then
            HDBETRAG = 0;
           if (HDTEXT is null) then
            HDTEXT = '';
           if (HDART is null) then
            HDART = 0;  
           if ((KHABEN=IKNR) and (arts=arth)) then
            HDBETRAG = -HDBETRAG;
          END
         ELSE
          BEGIN
           HDBETRAG = 0; HDTEXT = ''; HDART = 0;
          END
         /* */        
         IF (KSOLL=IKNR) THEN
          BEGIN
           IF (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KHABEN;
           TEMPONR=ONRHABEN;
           BANKNR=BANKNRHABEN;
          END
         ELSE
          BEGIN
           IF (NOT (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27)) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KSOLL;
           TEMPONR=ONRSOLL;
           BANKNR=BANKNRSOLL;
          END
         ONR=IONR;
         IF (BANKNR IS NOT NULL) THEN
          SELECT KURZBEZ from banken where NR=:BANKNR
          into :GKONTOSTR;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:TEMPONR AND KNR=:GKONTO
          into :GKONTOSTR;
         IF (BETRAG<>0) THEN
          BEGIN
           IF (KKLASSE<>30) THEN
            SUSPEND;
           ELSE
            IF (ONRSOLL=IAKTOBJ OR ONRHABEN=IAKTOBJ) THEN
             SUSPEND;
          END
        END
      END
     ELSE
      BEGIN /* WDATUM */
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG,BANKNRSOLL, BANKNRHABEN, BRENNSTMENGE, ONRSOLL, ONRHABEN, KAUSZUGNR, KAUSZUGBLATT, BNR, NICHTUMLEGEN, artsoll, arthaben from buchung
       WHERE ((ONRSOLL=:IONR and KSOLL=:IKNR) OR (ONRHABEN=:IONR and KHABEN=:IKNR))
       AND (WDatum>=:DTVON and WDatum<=:DTBIS)
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :BRENNSTMENGE, :ONRSOLL, :ONRHABEN, :KAUSZUGNR, :KAUSZUGBLATT, :BNR, :NICHTUMLEGEN, :arts, :arth
       DO
        BEGIN
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF (KKLASSE = 1) THEN
          BEGIN
           select sum(betrag) from hdbuch where bnr=:bnr into :HDBETRAG;  
           select first 1 text, art from hdbuch where bnr=:bnr into HDTEXT, HDART;
           if (HDTEXT is null) then
            HDTEXT = '';
           if (HDART is null) then
            HDART = 0;             
           if (HDBETRAG is null) then
            HDBETRAG = 0;
           if ((KHABEN=IKNR) and (arts=arth)) then
            HDBETRAG = -HDBETRAG;
          END
         ELSE
          BEGIN
           HDBETRAG = 0; HDTEXT = ''; HDART = 0;
          END
         /* */        
         IF (KSOLL=IKNR) THEN
          BEGIN
           IF (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KHABEN;
           TEMPONR=ONRHABEN;
           BANKNR=BANKNRHABEN;
          END
         ELSE
          BEGIN
           IF (NOT (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27)) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
          GKONTO=KSOLL;
          TEMPONR=ONRSOLL;
          BANKNR=BANKNRSOLL;
          END
         ONR=IONR;
         IF (BANKNR IS NOT NULL) THEN
          SELECT KURZBEZ from banken where NR=:BANKNR
          into :GKONTOSTR;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:TEMPONR AND KNR=:GKONTO
          into :GKONTOSTR;
         IF (BETRAG<>0) THEN
          BEGIN
           IF (KKLASSE<>30) THEN
            SUSPEND;
           ELSE
            IF (ONRSOLL=IAKTOBJ OR ONRHABEN=IAKTOBJ) THEN
             SUSPEND;
          END
        END
      END
    end /*alle Objekte*/
  END
 ELSE
 /*          */
 /* DEB/KRED */
 /*          */
  BEGIN
   /*DATUM*/
   IF (BWDATUM<>'J') THEN
    BEGIN
     IF (BSOLL='J') THEN
      BEGIN /* Sollstelungen */
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, ONRSOLL, ONRHABEN, BRENNSTMENGE, KAUSZUGNR, KAUSZUGBLATT,LBNR, NICHTUMLEGEN from buchung
       WHERE ((ONRSOLL=:IONR and KSOLL=:IKNR) OR (ONRHABEN=:IONR and KHABEN=:IKNR))
       AND (Datum>=:DTVON and Datum<=:DTBIS)
       AND SPLITNR IS NULL and BETRAG<>0
       UNION
       SELECT buchung.BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, splitbuch.BETRAG, BANKNRSOLL, BANKNRHABEN, sum(splitbuch.OPBETRAG), SPLITNR, ONRSOLL, ONRHABEN, BRENNSTMENGE, KAUSZUGNR, KAUSZUGBLATT,LBNR, NICHTUMLEGEN from buchung, splitbuch
       WHERE ((ONRSOLL=:IONR and KSOLL=:IKNR) OR (ONRHABEN=:IONR and KHABEN=:IKNR))
       AND (Datum>=:DTVON and Datum<=:DTBIS)
       AND SPLITNR IS NOT NULL and splitbuch.BETRAG<>0
       AND BUCHUNG.BNR = SPLITBUCH.BNR
       GROUP BY buchung.BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, splitbuch.BETRAG, BANKNRSOLL, BANKNRHABEN, SPLITNR, ONRSOLL, ONRHABEN, BRENNSTMENGE, KAUSZUGNR, KAUSZUGBLATT,LBNR, NICHTUMLEGEN
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :ONRSOLL, :ONRHABEN, :BRENNSTMENGE, :KAUSZUGNR, :KAUSZUGBLATT, :LBNR, :NICHTUMLEGEN
       DO
        BEGIN
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF (KSOLL=IKNR) THEN
          BEGIN
           IF (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KHABEN;
           BANKNR=BANKNRHABEN;
           ONR=ONRHABEN;
          END
         ELSE
          BEGIN
           IF (NOT (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27)) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KSOLL;
           BANKNR=BANKNRSOLL;
           ONR=ONRSOLL;
          END
         IF (BANKNR IS NOT NULL) THEN
          SELECT KURZBEZ from banken where NR=:BANKNR
          into :GKONTOSTR;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:ONR AND KNR=:GKONTO
          into :GKONTOSTR;
         IF (OPBETRAG IS NOT NULL) THEN
          BEGIN
           IF (OPBETRAG=0) THEN
            BEGIN
             IF (SPLITNR IS NULL) THEN
              BEMERKUNG='SO';
             ELSE
              BEMERKUNG='SO..';
            END
           ELSE
            BEGIN
             IF (SPLITNR IS NULL) THEN
              BEMERKUNG='OP';
             ELSE
              BEMERKUNG='OP..';
            END
          END
         ELSE
          BEGIN
           IF (LBNR IS NOT NULL) then
            BEMERKUNG='LEV';
           ELSE
            BEMERKUNG='';
          END
         IF (KKLASSE<>71) THEN
          BETRAG=-BETRAG;
         IF (BETRAG<>0) THEN
          SUSPEND;
       END
      END /* Sollstelungen */
     ELSE
      BEGIN /* keine Sollstelungen */
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, ONRSOLL, ONRHABEN, BRENNSTMENGE, KAUSZUGNR, KAUSZUGBLATT,LBNR,NICHTUMLEGEN from buchung
       WHERE ((ONRSOLL=:IONR and KSOLL=:IKNR) OR (ONRHABEN=:IONR and KHABEN=:IKNR))
       AND (Datum>=:DTVON and Datum<=:DTBIS)
       AND OPBETRAG IS NULL and BETRAG<>0
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :ONRSOLL, :ONRHABEN, :BRENNSTMENGE, :KAUSZUGNR, :KAUSZUGBLATT, :LBNR, :NICHTUMLEGEN
       DO
        BEGIN
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF (KSOLL=IKNR) THEN
          BEGIN
           IF (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KHABEN;
           BANKNR=BANKNRHABEN;
           ONR=ONRHABEN;
          END
         ELSE
          BEGIN
           IF (NOT (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27)) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KSOLL;
           BANKNR=BANKNRSOLL;
           ONR=ONRSOLL;
          END
         IF (BANKNR IS NOT NULL) THEN
          SELECT KURZBEZ from banken where NR=:BANKNR
          into :GKONTOSTR;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:ONR AND KNR=:GKONTO
          into :GKONTOSTR;
         IF (OPBETRAG IS NOT NULL) THEN
          BEGIN
           IF (OPBETRAG=0) THEN
            BEGIN
             IF (SPLITNR IS NULL) THEN
              BEMERKUNG='SO';
             ELSE
              BEMERKUNG='SO..';
            END
           ELSE
            BEGIN
             IF (SPLITNR IS NULL) THEN
              BEMERKUNG='OP';
             ELSE
              BEMERKUNG='OP..';
            END
          END
         ELSE
          BEGIN
           IF (LBNR IS NOT NULL) THEN
            BEMERKUNG='LEV';
           ELSE
            BEMERKUNG='';
          END
         IF (KKLASSE<>71) THEN
          BETRAG=-BETRAG;
         IF (BETRAG<>0) THEN
          SUSPEND;
        END
      END   /* keine Sollstelungen */
    END
   ELSE
    BEGIN /* WDATUM */
     IF (BSOLL='J') THEN
      BEGIN /* Sollstelungen */
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, ONRSOLL, ONRHABEN, BRENNSTMENGE, KAUSZUGNR, KAUSZUGBLATT, LBNR, NICHTUMLEGEN from buchung
       WHERE ((ONRSOLL=:IONR and KSOLL=:IKNR) OR (ONRHABEN=:IONR and KHABEN=:IKNR))
       AND (WDatum>=:DTVON and WDatum<=:DTBIS)
       AND SPLITNR IS NULL and BETRAG<>0
       UNION
       SELECT buchung.BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, splitbuch.BETRAG, BANKNRSOLL, BANKNRHABEN, sum(splitbuch.OPBETRAG), SPLITNR, ONRSOLL, ONRHABEN, BRENNSTMENGE, KAUSZUGNR, KAUSZUGBLATT,LBNR,NICHTUMLEGEN from buchung, splitbuch
       WHERE ((ONRSOLL=:IONR and KSOLL=:IKNR) OR (ONRHABEN=:IONR and KHABEN=:IKNR))
       AND (WDatum>=:DTVON and WDatum<=:DTBIS)
       AND SPLITNR IS NOT NULL and splitbuch.BETRAG<>0
       AND BUCHUNG.BNR = SPLITBUCH.BNR
       GROUP BY buchung.BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, splitbuch.BETRAG, BANKNRSOLL, BANKNRHABEN, SPLITNR, ONRSOLL, ONRHABEN, BRENNSTMENGE, KAUSZUGNR, KAUSZUGBLATT,LBNR,NICHTUMLEGEN
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :ONRSOLL, :ONRHABEN, :BRENNSTMENGE, :KAUSZUGNR, :KAUSZUGBLATT,:LBNR,:NICHTUMLEGEN
       DO
        BEGIN
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF (KSOLL=IKNR) THEN
          BEGIN
           IF (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KHABEN;
           BANKNR=BANKNRHABEN;
           ONR=ONRHABEN;
          END
         ELSE
          BEGIN
           IF (NOT (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27)) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KSOLL;
           BANKNR=BANKNRSOLL;
           ONR=ONRSOLL;
          END
         IF (BANKNR IS NOT NULL) THEN
          SELECT KURZBEZ from banken where NR=:BANKNR
          into :GKONTOSTR;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:ONR AND KNR=:GKONTO
          into :GKONTOSTR;
         IF (OPBETRAG IS NOT NULL) THEN
          BEGIN
           IF (OPBETRAG=0) THEN
            BEGIN
             IF (SPLITNR IS NULL) THEN
              BEMERKUNG='SO';
             ELSE
              BEMERKUNG='SO..';
            END
           ELSE
            BEGIN
             IF (SPLITNR IS NULL) THEN
              BEMERKUNG='OP';
             ELSE
              BEMERKUNG='OP..';
            END
          END
         ELSE
          BEGIN
           IF (LBNR IS NOT NULL) then
            BEMERKUNG='LEV';
           ELSE
            BEMERKUNG='';
          END
         IF (KKLASSE<>71) THEN
          BETRAG=-BETRAG;
         IF (BETRAG<>0) THEN
          SUSPEND;
       END
      END /* Sollstelungen */
     ELSE
      BEGIN /* keine Sollstelungen */
       FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN, BELEGNR, TEXT, MWST, BETRAG, BANKNRSOLL, BANKNRHABEN, OPBETRAG, SPLITNR, ONRSOLL, ONRHABEN, BRENNSTMENGE, KAUSZUGNR, KAUSZUGBLATT, LBNR, NICHTUMLEGEN from buchung
       WHERE ((ONRSOLL=:IONR and KSOLL=:IKNR) OR (ONRHABEN=:IONR and KHABEN=:IKNR))
       AND (WDatum>=:DTVON and WDatum<=:DTBIS)
       AND OPBETRAG IS NULL and BETRAG<>0
       INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN, :BELEGNR, :TEXT, :MWST, :BETRAG, :BANKNRSOLL, :BANKNRHABEN, :OPBETRAG, :SPLITNR, :ONRSOLL, :ONRHABEN, :BRENNSTMENGE, :KAUSZUGNR, :KAUSZUGBLATT, :LBNR, :NICHTUMLEGEN
       DO
        BEGIN
         HDBETRAG = 0; HDTEXT = ''; HDART = 0;
         IF (KSOLL=IKNR) THEN
          BEGIN
           IF (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KHABEN;
           BANKNR=BANKNRHABEN;
           ONR=ONRHABEN;
          END
         ELSE
          BEGIN
           IF (NOT (((KKLASSE>=10 AND KKLASSE<=19) OR (KKLASSE>=110 AND KKLASSE<=580)) OR KKLASSE=27)) THEN
            BEGIN
             BETRAG=-BETRAG;
             BRENNSTMENGE=-BRENNSTMENGE;
            END
           GKONTO=KSOLL;
           BANKNR=BANKNRSOLL;
           ONR=ONRSOLL;
          END
         IF (BANKNR IS NOT NULL) THEN
          SELECT KURZBEZ from banken where NR=:BANKNR
          into :GKONTOSTR;
         ELSE
          SELECT KNRSTR || ' ' || KBEZ from konten where ONR=:ONR AND KNR=:GKONTO
          into :GKONTOSTR;
         IF (OPBETRAG IS NOT NULL) THEN
          BEGIN
           IF (OPBETRAG=0) THEN
            BEGIN
             IF (SPLITNR IS NULL) THEN
              BEMERKUNG='SO';
             ELSE
              BEMERKUNG='SO..';
            END
           ELSE
            BEGIN
             IF (SPLITNR IS NULL) THEN
              BEMERKUNG='OP';
             ELSE
              BEMERKUNG='OP..';
            END
          END
         ELSE
          BEGIN
           IF (LBNR IS NOT NULL) THEN
            BEMERKUNG='LEV';
           ELSE
            BEMERKUNG='';
          END
         IF (KKLASSE<>71) THEN
          BETRAG=-BETRAG;
         IF (BETRAG<>0) THEN
          SUSPEND;
        END
      END   /* keine Sollstelungen */
    END   /* WDATUM */
  END /* DEB / KRED */
END
