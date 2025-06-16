-- Prozedur: ENTWICKLUNG_GELDKONTEN
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE ENTWICKLUNG_GELDKONTEN
DECLARE VARIABLE GIRO_ALT NUMERIC(15, 2);
DECLARE VARIABLE GIRO_NEU NUMERIC(15, 2);
DECLARE VARIABLE BETRAG_SOLL NUMERIC(15, 2);
DECLARE VARIABLE BETRAG_HABEN NUMERIC(15, 2);
DECLARE VARIABLE BETRAG_NETTO NUMERIC(15, 2);
DECLARE VARIABLE TEMPNR INTEGER;
DECLARE VARIABLE KNR INTEGER;
DECLARE VARIABLE KKLASSE INTEGER;
DECLARE VARIABLE KBEZ VARCHAR(188);
DECLARE VARIABLE BANKART INTEGER;
DECLARE VARIABLE BANKKURZBEZ VARCHAR(40);
DECLARE VARIABLE POS1NAME VARCHAR(30);
DECLARE VARIABLE POS2NAME VARCHAR(30);
DECLARE VARIABLE POS3NAME VARCHAR(30);
DECLARE VARIABLE POS4NAME VARCHAR(30);
DECLARE VARIABLE POS5NAME VARCHAR(30);
DECLARE VARIABLE POS6NAME VARCHAR(30);
DECLARE VARIABLE POS7NAME VARCHAR(30);
DECLARE VARIABLE POS8NAME VARCHAR(30);
DECLARE VARIABLE POS9NAME VARCHAR(30);
DECLARE VARIABLE POS10NAME VARCHAR(30);
DECLARE VARIABLE RLPOS INTEGER;
DECLARE VARIABLE POSNR INTEGER;
DECLARE VARIABLE BETRAGEIN NUMERIC(15, 2);
DECLARE VARIABLE BETRAGAUS NUMERIC(15, 2);
DECLARE VARIABLE ANZEIN INTEGER;
DECLARE VARIABLE ANZAUS INTEGER;
DECLARE VARIABLE GIROANZALT INTEGER;
DECLARE VARIABLE GIROANZNEU INTEGER;
DECLARE VARIABLE RLTEXT VARCHAR(30);
/* NEUE PROCEDURE */
DECLARE VARIABLE IANZ INTEGER;
DECLARE VARIABLE RTMP NUMERIC(15, 2);
DECLARE VARIABLE RSALDO NUMERIC(15, 2);
DECLARE VARIABLE ITMP INTEGER;
DECLARE VARIABLE IGIROLAUFNR INTEGER;
DECLARE VARIABLE ITMP2 INTEGER;
DECLARE VARIABLE INR INTEGER;
DECLARE VARIABLE IKLASSE INTEGER;
BEGIN
 NR = 1;
 FOR SELECT BANKNR FROM OBJBANKEN WHERE ONR = :ONR
 INTO :GKONTO
 DO
  BEGIN
   IANZ = 0;
   RSALDO = 0;
   ILAUFNR = 1;
   /* BEZ Bank/Kasse */
   select KURZBEZ, ART from banken where NR=:GKONTO INTO :BANKKURZBEZ, :BANKART;
   IF (BANKART=0) THEN
    BANKKURZBEZ='Girokonto "' || BANKKURZBEZ || '"';
   ELSE
    BANKKURZBEZ='Kasse "' || BANKKURZBEZ || '"';
   /* Saldo alt */
   select saldo from BANKSALDO_ALT (:GKONTO,:DTVON) INTO GIRO_ALT;
   IGIROLAUFNR = ILAUFNR;
   /*  */
   /* 98000 - Konto */
   RTMP = 0;
   ILAUFNR = 1;
   for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -BETRAG from buchung where
    ksoll=98000 and banknrhaben=:GKONTO
    and (Datum>=:DTVON and Datum<=:DTBIS)
    union
    select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
    khaben=98000 and banknrsoll=:GKONTO
    and (Datum>=:DTVON and Datum<=:DTBIS)
   into :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG
   do
    begin
     IANZ = IANZ + 1;
     RTMP = RTMP + EBETRAG;
     /* Eintrag */
     TEXT = '';
     BETRAG = NULL;
     RLKONTO = NULL;
     BILANZ = NULL;
     ISMASTER = '2';
     SUSPEND;
    end
   /* Master-Eintrag */
   DATUM = NULL;
   BELEGNR = NULL;
   BTEXT = NULL;
   KONTOS = NULL;
   KONTOH = NULL;
   EBETRAG = NULL;
   ISMASTER = '1';
   BETRAG = RTMP;
   RLKONTO = NULL;
   BILANZ = NULL;
   if (RTMP > 0) THEN
    TEXT = 'zzgl. Anfangsbestand (EB-Wert)';
   else
    if (RTMP < 0) THEN
     TEXT = 'abzgl. Anfangsbestand (EB-Wert)';
   RSALDO = RSALDO + BETRAG;
   if (BETRAG <> 0) then
    SUSPEND;
   ILAUFNR = ILAUFNR + 1;
   /*  */
   /* 99990 - Durchlaufkonto */
   RTMP = 0;
   for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, -BETRAG from buchung where
    ksoll=99990 and banknrhaben=:GKONTO
    and (Datum>=:DTVON and Datum<=:DTBIS)
    union
    select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
    khaben=99990 and banknrsoll=:GKONTO
    and (Datum>=:DTVON and Datum<=:DTBIS)
   into :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG
   do
    begin
     IANZ = IANZ + 1;
     RTMP = RTMP + EBETRAG;
     /* Eintrag */
     TEXT = '';
     BETRAG = NULL;
     RLKONTO = NULL;
     BILANZ = NULL;
     ISMASTER = '2';
     SUSPEND;
    end
   /* Master-Eintrag */
   DATUM = NULL;
   BELEGNR = NULL;
   BTEXT = NULL;
   KONTOS = NULL;
   KONTOH = NULL;
   EBETRAG = NULL;
   ISMASTER = '1';
   BETRAG = RTMP;
   RLKONTO = NULL;
   BILANZ = NULL;
   if (RTMP > 0) THEN
    TEXT = 'zzgl. Durchlaufkonto';
   else
    if (RTMP < 0) THEN
     TEXT = 'abzgl. Durchlaufkonto';
   RSALDO = RSALDO + BETRAG;
   if (BETRAG <> 0) then
    SUSPEND;
   ILAUFNR = ILAUFNR + 1;
   /*  */
   /* Hausgeld im WDATUM KLASSE 15 */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 15, ' ','HausgeldvorschÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼sse')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     if (BETRAG > 0) then
      TEXT = 'zzgl. ' || TEXT;
     else
      TEXT = 'abgl. ' || TEXT;
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* RL1 bis RL48 */   
   INR=1;
   WHILE (INR <= 48) do
    begin
     IKLASSE=(100 + (10 * INR));
     for select bez from vorausz where onr=:onr and kklasse=:IKLASSE into RLTEXT do
      begin
       FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, :IKLASSE, ' ', :RLTEXT)
       into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
       DO
        BEGIN
         if (BETRAG > 0) then
          TEXT = 'zzgl. ' || TEXT;
         else
          TEXT = 'abgl. ' || TEXT;
         ITMP2 = ILAUFNR;
         ILAUFNR = ILAUFNR + ITMP;
         IANZ = IANZ + 1;
         RLKONTO = NULL;
         BILANZ = NULL;
         if (ISMASTER = '1') then
          begin
           RSALDO = RSALDO + BETRAG;
           ITMP2 = ILAUFNR;
          end
         SUSPEND;
         ILAUFNR = ITMP2;
        END
       ILAUFNR = ILAUFNR+1; 
      end
     INR=INR+1;
    end
   /* Sonderumlage */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 17, ' ',' Sonderumlage')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     if (BETRAG > 0) then
      TEXT = 'zzgl. ' || TEXT;
     else
      TEXT = 'abgl. ' || TEXT;
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* Sonstige Einnahmen im WDATUM KLASSE 19 */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 19, ' ','sonstige Einnahmen')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     if (BETRAG > 0) then
      TEXT = 'zzgl. ' || TEXT;
     else
      TEXT = 'abgl. ' || TEXT;
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* MIETE im WDatum */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 10, ' ','Einnahmen Mieten')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     if (BETRAG > 0) then
      TEXT = 'zzgl. ' || TEXT;
     else
      TEXT = 'abgl. ' || TEXT;
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* BK im WDatum */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 11, ' ','Einnahmen Betriebskosten-VZ')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     if (BETRAG > 0) then
      TEXT = 'zzgl. ' || TEXT;
     else
      TEXT = 'abgl. ' || TEXT;    
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* HK im WDatum */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 12, ' ','Einnahmen Heizkosten-VZ')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     if (BETRAG > 0) then
      TEXT = 'zzgl. ' || TEXT;
     else
      TEXT = 'abgl. ' || TEXT;    
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* Nachzahlungen EIG */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 18,'N','zzgl. Ausgleich NachschÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼sse (Nachzahlungen, EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer)')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* Nachzahlungen BEW */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 13,'N','zzgl. Ausgleich Nachzahlungen (Bewohner)')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* Guthaben EIG */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 18,'G','abzgl. Ausgleich Anpassung beschl. VorschÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼sse (Guthaben, EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer)')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /* Guthaben BEW */
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 13,'G','abzgl. Ausgleich Guthaben (Bewohner)')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       RSALDO = RSALDO + BETRAG;
       ITMP2 = ILAUFNR;
      end
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /***************************/
   /**** Umbuchung von RLA auf Bank RLA ***/
   /**************************/
   RTMP = 0;
   for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
    arthaben=22 and banknrsoll=:GKONTO and (Datum>=:DTVON and Datum<=:DTBIS)
   into :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG
   do
    begin
     IANZ = IANZ + 1;
     RTMP = RTMP + EBETRAG;
     /* Eintrag */
     TEXT = '';
     BETRAG = NULL;
     RLKONTO = NULL;
     BILANZ = NULL;
     ISMASTER = '2';
     SUSPEND;
    end
   /* Master-Eintrag */
   DATUM = NULL;
   BELEGNR = NULL;
   BTEXT = NULL;
   KONTOS = NULL;
   KONTOH = NULL;
   EBETRAG = NULL;
   ISMASTER = '1';
   BETRAG = RTMP;
   RLKONTO = NULL;
   BILANZ = NULL;
   TEXT = 'zzgl. ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrag von Festgeldkonten (ErhaltungsrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen) auf Girokonto';
   RSALDO = RSALDO + BETRAG;
   if (BETRAG <> 0) then
    SUSPEND;
   ILAUFNR = ILAUFNR + 1;
   /**********************/
   /****AUSGABEN  1,71 ***/
   /**********************/
   FOR SELECT BETRAG, TEXT, DATUM, BELEGNR, BTEXT, KONTOS, KONTOH, EBETRAG, ISMASTER, NR from ENTW_SALDO_WDATUM(:GKONTO, :DTVON, :DTBIS, 0, 'K','')
   into :BETRAG, :TEXT, :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG, :ISMASTER, :ITMP
   DO
    BEGIN
     ITMP2 = ILAUFNR;
     ILAUFNR = ILAUFNR + ITMP;
     IANZ = IANZ + 1;
     RLKONTO = NULL;
     BILANZ = NULL;
     if (ISMASTER = '1') then
      begin
       /*ITMP2 = ITMP2 + 1;*/
       ITMP2 = ILAUFNR;
       BETRAG = -BETRAG;
       RSALDO = RSALDO + BETRAG;
      end
     else
      EBETRAG = -EBETRAG;
     SUSPEND;
     ILAUFNR = ITMP2;
    END
   ILAUFNR = ILAUFNR + 1;
   /***************************/
   /**** Umbuchung auf RLA ***/
   /**************************/
   RTMP = 0;
   for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
    artsoll=22 and banknrhaben=:GKONTO and (Datum>=:DTVON and Datum<=:DTBIS)
   into :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG
   do
    begin
     IANZ = IANZ + 1;
     EBETRAG = -EBETRAG;
     RTMP = RTMP + EBETRAG;
     /* Eintrag */
     TEXT = '';
     BETRAG = NULL;
     RLKONTO = NULL;
     BILANZ = NULL;
     ISMASTER = '2';
     SUSPEND;
    end
   /* Master-Eintrag */
   DATUM = NULL;
   BELEGNR = NULL;
   BTEXT = NULL;
   KONTOS = NULL;
   KONTOH = NULL;
   EBETRAG = NULL;
   ISMASTER = '1';
   BETRAG = RTMP;
   RLKONTO = NULL;
   BILANZ = NULL;
   TEXT = 'abzgl. ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrag an Festgeldkonten (ErhaltungsrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen)';
   RSALDO = RSALDO + BETRAG;
   if (BETRAG <> 0) then
    SUSPEND;
   ILAUFNR = ILAUFNR + 1;
   /***********************************/
   /**** Buchungen auf sonstige A/P ***/
   /***********************************/
   for select knr, kklasse, kbez from konten
    where onr=:onr and (kklasse=22 or kklasse=24 or kklasse=27 or kklasse=20) and rlpos is null and (banknr<>:GKONTO or banknr is null)
   into :KNR, :KKLasse, :KBEZ
   do
    begin
     :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
     /* sonstiges A/P im Soll, Bank im Haben = abgang */
     RTMP = 0;
     for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
      KSOLL=:KNR and banknrhaben=:GKONTO and (Datum>=:DTVON and Datum<=:DTBIS)
     into :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG
     do
      begin
       IANZ = IANZ + 1;
       RTMP = RTMP + EBETRAG;
       /* Eintrag */
       TEXT = '';
       BETRAG = NULL;
       RLKONTO = NULL;
       BILANZ = NULL;
       ISMASTER = '2';
       SUSPEND;
      end
     /* Master-Eintrag */
     DATUM = NULL;
     BELEGNR = NULL;
     BTEXT = NULL;
     KONTOS = NULL;
     KONTOH = NULL;
     EBETRAG = NULL;
     ISMASTER = '1';
     RLKONTO = NULL;
     BILANZ = NULL;
     BETRAG = RTMP;
     IF (BETRAG >= 0) THEN
      begin
       TEXT = 'abzgl. Abgang ' || :KBEZ;
       BETRAG = -BETRAG;
      end
     else
      begin
       TEXT = 'zzgl. Zugang ' || :KBEZ;
      end
     RSALDO = RSALDO + BETRAG;
     if (BETRAG <> 0) then
      SUSPEND;
     ILAUFNR = ILAUFNR + 1;
     /* Bank im Soll, sonstiges A/P im Haben = zugang */
     RTMP = 0;
     for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
      KHABEN=:KNR and banknrsoll=:GKONTO and (Datum>=:DTVON and Datum<=:DTBIS)
     into :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG
     do
      begin
       IANZ = IANZ + 1;
       RTMP = RTMP + EBETRAG;
       /* Eintrag */
       TEXT = '';
       BETRAG = NULL;
       RLKONTO = NULL;
       BILANZ = NULL;
       ISMASTER = '2';
       SUSPEND;
      end
     /* Master-Eintrag */
     DATUM = NULL;
     BELEGNR = NULL;
     BTEXT = NULL;
     KONTOS = NULL;
     KONTOH = NULL;
     EBETRAG = NULL;
     ISMASTER = '1';
     RLKONTO = NULL;
     BILANZ = NULL;
     BETRAG = RTMP;
     IF (BETRAG >= 0) THEN
      begin
       TEXT = 'zzgl. Zugang ' || :KBEZ;
      end
     else
      BEGIN
       TEXT = 'abzgl. Abgang ' || :KBEZ;
       BETRAG = -BETRAG;
      END
     RSALDO = RSALDO + BETRAG;
     if (BETRAG <> 0) then
      SUSPEND;
     ILAUFNR = ILAUFNR + 1;
    end  /* buchungen auf sonstige A/P */
   /* Endsaldo */
   if ((IANZ > 0) or (GIRO_ALT <> 0)) then
    begin
     select saldo from BANKSALDO_ALT (:GKONTO,:DTBIS_PLUSEINS) INTO GIRO_NEU;
     TEXT='Saldo ' || BANKKURZBEZ || ' per ' || DTBISTEXT;
     SALDO = GIRO_NEU;
     BILANZ = 'EB';
     ISMASTER = '3';
     SUSPEND;
     TEXT = 'Saldo ' || BANKKURZBEZ || ' per ' || DTVONTEXT;
     SALDO = GIRO_ALT;
     BILANZ = 'AB';
     ISMASTER = '0';
     ILAUFNR = IGIROLAUFNR;
     SUSPEND;
     SALDO = 0;
    end
   BILANZ=NULL;
   NR=NR+1;
  END /* was auf der Bank gebucht */
 /*************/
 /* RLA       */
 /*************/
 for select knr, kklasse, kbez from konten
  where onr=:onr and kklasse=22
 into :KNR, :KKLasse, :KBEZ
 do
  begin
   :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
   RSALDO = 0;
   GKONTO = -1;   
   select NR from rueckbkt where ONR=:ONR and KNR=:KNR into RLKONTO;
   /* Angfangsstand */
   EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTVON, 'J','N') RETURNING_VALUES :GIRO_ALT;
   EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTBIS_PLUSEINS, 'J','N') RETURNING_VALUES :GIRO_NEU;
   IF (GIRO_ALT<>0 or GIRO_NEU<>0) THEN
    BEGIN
     /* Anfangssaldo */
     TEXT = 'Saldo ' || KBEZ || ' per ' || DTVONTEXT;
     BETRAG = null;
     SALDO = GIRO_ALT;
     BILANZ = 'AB';
     ISMASTER = '0';
     SUSPEND;
     BILANZ = NULL;
     SALDO = null;
     RSALDO = RSALDO + GIRO_ALT;
     /* SOLL = ZUF */
     RTMP = 0;
     for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
      ONRSOLL=:ONR and ksoll=:KNR AND ARTOP IS NULL and (Datum>=:DTVON and Datum<=:DTBIS)
     into :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG
     do
      begin
       IANZ = IANZ + 1;
       RTMP = RTMP + EBETRAG;
       /* Eintrag */
       TEXT = '';
       BETRAG = NULL;
       RLKONTO = NULL;
       BILANZ = NULL;
       ISMASTER = '2';
       SUSPEND;
      end
     /* Master-Eintrag */
     DATUM = NULL;
     BELEGNR = NULL;
     BTEXT = NULL;
     KONTOS = NULL;
     KONTOH = NULL;
     EBETRAG = NULL;
     ISMASTER = '1';
     BETRAG = RTMP;
     RLKONTO = NULL;
     BILANZ = NULL;
     IF (BETRAG >= 0) THEN
      TEXT = 'zzgl. ZufÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung ErhaltungsrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen';
     else
      TEXT = 'abzgl. Entnahme ErhaltungsrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen';
     RSALDO = RSALDO + BETRAG;
     if (BETRAG <> 0) then
      SUSPEND;
     ILAUFNR = ILAUFNR + 1;
     /* HABEN = Entnahme */
     RTMP = 0;
     for select DATUM, BELEGNR, TEXT, KSTRSOLL, KSTRHABEN, BETRAG from buchung where
      onrhaben=:ONR and khaben=:KNR and ARTOP IS NULL and (Datum>=:DTVON and Datum<=:DTBIS)
     into :DATUM, :BELEGNR, :BTEXT, :KONTOS, :KONTOH, :EBETRAG
     do
      begin
       IANZ = IANZ + 1;
       RTMP = RTMP + EBETRAG;
       /* Eintrag */
       TEXT = '';
       BETRAG = NULL;
       RLKONTO = NULL;
       BILANZ = NULL;
       ISMASTER = '2';
       SUSPEND;
      end
     /* Master-Eintrag */
     DATUM = NULL;
     BELEGNR = NULL;
     BTEXT = NULL;
     KONTOS = NULL;
     KONTOH = NULL;
     EBETRAG = NULL;
     ISMASTER = '1';
     BETRAG = RTMP;
     RLKONTO = NULL;
     BILANZ = NULL;
     IF (BETRAG >= 0) THEN
      BEGIN
       TEXT = 'abzgl. Entnahme ErhaltungsrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen';
      END
     else
      begin
       TEXT = 'zzgl. Entnahme ErhaltungsrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen';
      end
     BETRAG=-BETRAG;
     RSALDO = RSALDO + BETRAG;
     if (BETRAG <> 0) then
      SUSPEND;
     ILAUFNR = ILAUFNR + 1;
     /* ZINSEN POS bis POS 6 Extra ausweisen */
     select POS1NAME,POS2NAME,POS3NAME,POS4NAME,POS5NAME,POS6NAME,POS7NAME,POS8NAME,POS9NAME,POS10NAME from rueckpos, RUECKBKT
     where (RUECKBKT.onr=:ONR and RUECKBKT.knr=:KNR) and rueckpos.nr=rueckbkt.rueckpos
     into :POS1NAME,:POS2NAME,:POS3NAME,:POS4NAME,:POS5NAME,:POS6NAME,:POS7NAME,:POS8NAME,:POS9NAME,:POS10NAME;
     /* Zinsen etc. */
     DATUM = NULL;
     BELEGNR = NULL;
     BTEXT = NULL;
     KONTOS = NULL;
     KONTOH = NULL;
     EBETRAG = NULL;
     ISMASTER = '1';
     BETRAG = RTMP;
     RLKONTO = NULL;
     BILANZ = NULL;
     for select sum(betrag), artop from buchzahl where BNR IN (
     select BNR from buchung where ONRSOLL=:ONR and ksoll=:KNR and artop=0 and (Datum>=:DTVON and Datum<=:DTBIS))
     group by artop order by artop
     into :BETRAG, :POSNR do
      BEGIN
       IF (BETRAG>=0) THEN
        TEXT='zzgl. ';
       ELSE
        TEXT='abzgl. ';
       IF (POSNR=1) THEN
        TEXT=TEXT || POS1NAME;
       ELSE
        IF (POSNR=2) THEN
         TEXT=TEXT || POS2NAME;
        ELSE
         IF (POSNR=3) THEN
          TEXT=TEXT || POS3NAME;
         ELSE
          IF (POSNR=4) THEN
           TEXT=TEXT || POS4NAME;
          ELSE
           IF (POSNR=5) THEN
            TEXT=TEXT || POS5NAME;
           ELSE
            IF (POSNR=6) THEN
             TEXT=TEXT || POS6NAME;
            ELSE
             IF (POSNR=7) THEN
              TEXT=TEXT || POS7NAME;
             ELSE
              IF (POSNR=8) THEN
               TEXT=TEXT || POS8NAME;
              ELSE
               IF (POSNR=9) THEN
                TEXT=TEXT || POS9NAME; 
               ELSE
                IF (POSNR=10) THEN
                 TEXT=TEXT || POS10NAME;   
       RSALDO = RSALDO + BETRAG;
       IF (BETRAG<>0) THEN
        SUSPEND;
      END
     /* Endstand */
     TEXT = 'Saldo ' || KBEZ || ' per ' || DTBISTEXT;
     SALDO = RSALDO;
     BETRAG = NULL;
     BILANZ = 'EB';
     ISMASTER = '3';
     SUSPEND;
     BILANZ = NULL;
     SALDO = NULL;
     NR = NR + 1;
    end /* Anf Ende <> 0 */
  end /* RLA */
END
