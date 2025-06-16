-- Prozedur: WEG_VERMOEGENSSTATUS
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE WEG_VERMOEGENSSTATUS
DECLARE VARIABLE FESTBETRAG NUMERIC(15, 2);
DECLARE VARIABLE BETRAG1 NUMERIC(15, 2);
DECLARE VARIABLE BETRAG2 NUMERIC(15, 2);
DECLARE VARIABLE KBRUTTO NUMERIC(15, 2);
DECLARE VARIABLE BETRAG_HABEN NUMERIC(15, 2);
DECLARE VARIABLE TEMPNR INTEGER;
DECLARE VARIABLE KNR INTEGER;
DECLARE VARIABLE TEMPONR INTEGER;
DECLARE VARIABLE KKLASSE INTEGER;
DECLARE VARIABLE KBEZ VARCHAR(188);
DECLARE VARIABLE BANKART INTEGER;
DECLARE VARIABLE BANKKURZBEZ VARCHAR(40);
DECLARE VARIABLE RLPOS INTEGER;
DECLARE VARIABLE KSTAND NUMERIC(15, 2);
BEGIN



 /* Salden Bankkonten/Kassen bestimmen */
 SALDO=0;
 FOR SELECT BANKNR
 FROM OBJBANKEN
 WHERE ONR = :ONR
 INTO :GKONTO
 DO
  BEGIN
   NR=1;
   /* BEZ Bank/Kasse */
   select KURZBEZ, ART from banken where NR=:GKONTO
   INTO :BANKKURZBEZ, :BANKART;
   IF (BANKART=0) THEN
    BANKKURZBEZ='Girokonto ' || BANKKURZBEZ;
   ELSE
    BANKKURZBEZ='Kasse ''' || BANKKURZBEZ || '''';
   /* Endsaldo */
   EXECUTE PROCEDURE BANKSALDO_ALT(:GKONTO, DTBIS_PLUSEINS) RETURNING_VALUES :BETRAG;
   IF (BETRAG<>0 and BETRAG IS NOT NULL) THEN
    BEGIN
     /* Endsaldo */
     TEXT='Saldo ' || BANKKURZBEZ || ' per ' || DTBISTEXT;
     SALDO=SALDO+BETRAG;
     ART=1;
     SUSPEND;
     NR=NR+1;
    end
  /* RAP */
  /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ckstÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤ndige Zahlungen EigetÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer, Bewohner BK/HK */
   Betrag=0;
   for
   select SUM(BETRAG) from buchung where
   banknrsoll=:GKONTO and (artop=15 or artop=11 or artop=12)  and WDatum<:DTVON
   and (Datum>=:DTVON and Datum<=:DTBIS)
   union
   SELECT SUM(BETRAG) from buchzahl
   where (artop=15 or artop=11 or artop=12) and BNR IN (select bnr from buchung where banknrsoll=:GKONTO and ARTOP=0 and (WDatum<:DTVON) and (Datum>=:DTVON and Datum<=:DTBIS))
   into Betrag1
   do
    begin
     if (BETRAG1 IS NOT NULL and BETRAG1<>0) THEN
      BETRAG=BETRAG-BETRAG1;
    end
   if (BETRAG<>0) then
    begin
     TEXT='rÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ckstÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤ndige Hausgeldvorauszahlungen';
     SALDO=SALDO+BETRAG;
     ART=3;
     SUSPEND;
     NR=NR+1;
    END
    
 /* Guthaben/Nachzahlungen aus Vorjahr EigetÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer + Bewohner*/
   select SUM(BETRAG) from buchung where
   banknrsoll=:GKONTO and (artop=18 or artop=13) and WDatum<:DTVON
   and (Datum>=:DTVON and Datum<=:DTBIS)
   into Betrag;
   if (BETRAG IS NOT NULL AND BETRAG<>0) THEN
    BEGIN
     IF (BETRAG<0) then
      begin
       BETRAG=-BETRAG;
       TEXT='Guthaben aus Vorjahresabrechnungen';
       SALDO=SALDO+BETRAG;
       ART=2;
       SUSPEND;
       NR=NR+1;
      END
     ELSE
      IF(BETRAG>0) THEN
       begin
        BETRAG=-BETRAG;
        TEXT='Nachzahlungen aus Vorjahresabrechnungen';
        SALDO=SALDO+BETRAG;
        ART=3;
        SUSPEND;
        NR=NR+1;
      end
    END
    
   /* Zahlungen fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Folgejahr EigetÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer, BK/HK */
   Betrag=0;
   for
   select SUM(BETRAG) from buchung where
   banknrsoll=:GKONTO and (artop=15 or ARTOP=18) and WDatum>:DTBIS
   and (Datum>=:DTVON and Datum<=:DTBIS)
   union
   SELECT SUM(BETRAG) from buchzahl
   where (artop=11 or artop=12) and BNR IN (select bnr from buchung where banknrsoll=:GKONTO and ARTOP=0 and (WDatum>:DTBIS) and (Datum>=:DTVON and Datum<=:DTBIS))
   into Betrag1
   do
    Betrag=Betrag-Betrag1;
   if (BETRAG<>0) THEN
    BEGIN
     BETRAG=-BETRAG;
     TEXT='Zahlungen der EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Folgejahr im Abrechnungszeitraum vereinnahmt';
     SALDO=SALDO+BETRAG;
     ART=3;
     SUSPEND;
     NR=NR+1;
    END
    
  /* umlagefÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤hige kosten im nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤chten Jahr gebucht, W-Datum Abrechnungszeitraum */
   select SUM(BETRAG) from buchung where
   banknrsoll=:GKONTO and arthaben=71 and (WDatum>=:DTVON and WDATUM<=:DTBIS)
     and Datum>:DTBIS
     into Betrag1;
     if (BETRAG1 IS NULL) THEN
      BETRAG1=0;
     select SUM(BETRAG) from buchung where
     banknrhaben=:GKONTO and artsoll=71 and (WDatum>=:DTVON and WDATUM<=:DTBIS)
     and (Datum>:DTBIS)
     into Betrag2;
     if (BETRAG2 IS NULL) THEN
      BETRAG2=0;
     BETRAG=BETRAG2-BETRAG1;
     /* DIREKT gebucht */
     select SUM(BETRAG) from buchung where
     banknrsoll=:GKONTO and arthaben=1 and (WDatum>=:DTVON and WDATUM<=:DTBIS)
     and (Datum>:DTBIS)
     into Betrag1;
     if (BETRAG1 IS NULL) THEN
      BETRAG1=0;
     BETRAG=BETRAG-BETRAG1;
     select SUM(BETRAG) from buchung where
     banknrhaben=:GKONTO and artsoll=1 and (WDatum>=:DTVON and WDATUM<=:DTBIS)
     and Datum>:DTBIS
     into Betrag2;
     if (BETRAG2 IS NULL) THEN
      BETRAG2=0;
     BETRAG=BETRAG+BETRAG2;
     IF (BETRAG<>0) THEN
      begin
       BETRAG=-BETRAG;
       SALDO=SALDO+BETRAG;
       TEXT='Kosten fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Abrechnungszeitraum im Folgejahr gebucht';
       ART=3;
       SUSPEND;
       NR=NR+1;
      end
      
  /* umlagefÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤hige kosten im Abrechnungszeitraum, noch nicht bezahlt */
  for select OPBetrag, Text, ONRSOLL, KSOLL from buchung
  where ARTSOLL=1 and OPBETRAG <> 0 and lastbank=:gkonto and (wdatum>=:DTVON and wdatum<=:DTBIS)
  into Betrag, TEXT, TEMPONR, KNR do
   begin
    BETRAG=-Betrag;
    SALDO=SALDO+BETRAG;
    select KBEZ from konten where ONR=:TEMPONR and KNR=:KNR into :KBEZ;
    :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
    TEXT=KBEZ || ' ' || TEXT;
    ART=3;
    SUSPEND;
    NR=NR+1;
   end
   
  /* umlagefÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤hige einnahmen im Abrechnungszeitraum, noch nicht erhalten */
  for select OPBetrag, Text, ONRHABEN, KHABEN from buchung
  where ARTHABEN=19 and OPBETRAG <> 0 and lastbank=:gkonto and (wdatum>=:DTVON and wdatum<=:DTBIS)
  into Betrag, TEXT, TEMPONR, KNR do
   begin
    SALDO=SALDO+BETRAG;
    select KBEZ from konten where ONR=:TEMPONR and KNR=:KNR into :KBEZ;
    :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
    TEXT=KBEZ || ' ' || TEXT;
    ART=2;
    SUSPEND;
    NR=NR+1;
   end

      
 /* umlagefÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤hige Einnahmen  im nÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤chten Jahr gebucht, W-Datum Abrechnungszeitraum */
   select SUM(BETRAG) from buchung where
   banknrsoll=:GKONTO and (arthaben=60 or arthaben=62 or arthaben=64) and (WDatum>=:DTVON and WDATUM<=:DTBIS)
     and Datum>:DTBIS
     into Betrag1;
     if (BETRAG1 IS NULL) THEN
      BETRAG1=0;
     select SUM(BETRAG) from buchung where
     banknrhaben=:GKONTO and (artsoll=60 or artsoll=62 or arthaben=64) and (WDatum>=:DTVON and WDATUM<=:DTBIS)
     and (Datum>:DTBIS)
     into Betrag2;
     if (BETRAG2 IS NULL) THEN
      BETRAG2=0;
     BETRAG=BETRAG1-BETRAG2;
     /* DIREKT gebucht */
     select SUM(BETRAG) from buchung where
     banknrsoll=:GKONTO and (arthaben=19) and (WDatum>=:DTVON and WDATUM<=:DTBIS)
     and (Datum>:DTBIS)
     into Betrag1;
     if (BETRAG1 IS NULL) THEN
      BETRAG1=0;
     BETRAG=BETRAG+BETRAG1;
     select SUM(BETRAG) from buchung where
     banknrhaben=:GKONTO and (artsoll=19) and (WDatum>=:DTVON and WDATUM<=:DTBIS)
     and Datum>:DTBIS
     into Betrag2;
     if (BETRAG2 IS NULL) THEN
      BETRAG2=0;
     BETRAG=BETRAG-BETRAG2;
     IF (BETRAG<>0) THEN
      begin
       SALDO=SALDO+BETRAG;
       TEXT='Einnahmen fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r Folgejahr im Abrechnungszeitraum gebucht';
       ART=2;
       SUSPEND;
       NR=NR+1;
      end
      
      

/* abzgl reine miete */
     Betrag=0;
     for
     select SUM(BETRAG) from buchung where
     banknrsoll=:GKONTO and artop=10 and (Datum>=:DTVON and Datum<=:DTBIS)
     union
     SELECT SUM(BETRAG) from buchzahl
     where artop=10 and BNR IN (select bnr from buchung where banknrsoll=:GKONTO and ARTOP=0 and (Datum>=:DTVON and Datum<=:DTBIS))
     into :Betrag1
     do
      begin
       if (BETRAG1 IS NOT NULL and BETRAG1<>0) THEN
        BETRAG=BETRAG-BETRAG1;
      end
     if (BETRAG<>0) then
      begin
       TEXT='vereinnahmte Mieten';
       SALDO=SALDO+BETRAG;
       ART=2;
       SUSPEND;
       NR=NR+1;
      END
      
   /* BUCHUNG auf andere Bestandskonten Bank im Soll abzgl */
      for select sum(betrag), onrhaben, khaben from buchung
      where banknrsoll=:gkonto and (arthaben=27 or arthaben=24)
      and (datum>=:DTVON and datum<=:DTBIS)
      group by onrhaben, khaben
      into :Betrag, :TEMPONR, :KNR
      do
       begin
        IF (BETRAG IS NOT NULL and BETRAg<>0) THEN
         BEGIN
          BETRAG=-BETRAG;
          select KBEZ from konten where ONR=:TEMPONR and KNR=:KNR into :KBEZ;
          :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
          TEXT=KBEZ;
          SALDO=SALDO+BETRAG;
          ART=3;
          SUSPEND;
          NR=NR+1;
         END
       end
       
   /* BUCHUNG auf andere Bestandskonten Bank im Haben zzgl */
      for select sum(betrag), onrsoll, ksoll from buchung
      where banknrhaben=:gkonto and (artsoll=27 or artsoll=24)
      and (datum>=:DTVON and datum<=:DTBIS)
      group by onrsoll, ksoll
      into :Betrag, :TEMPONR, :KNR
      do
       begin
        IF (BETRAG IS NOT NULL and BETRAg<>0) THEN
         BEGIN
          select KBEZ from konten where ONR=:TEMPONR and KNR=:KNR into :KBEZ;
          :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
          TEXT=KBEZ;
          SALDO=SALDO+BETRAG;
          ART=2;
          SUSPEND;
          NR=NR+1;
         END
       end
       
  END /* SALDEN Banken/Kassen */

/*         */
/*         */


/* Nicht umlagefÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤hige Kosten */
  for select onr, knr, kbez from konten where kkstnr=3 and onr=:ONR and KKLASSE=1
  into :TEMPONR, :KNR, :TEXT do
   begin
    EXECUTE PROCEDURE KONTOSALDO_ALT (:TEMPONR, :KNR, :DTBIS_PLUSEINS, 'J','N') RETURNING_VALUES :BETRAG;
    IF (BETRAG IS NOT NULL and BETRAg<>0) THEN
     BEGIN
      SALDO=SALDO+BETRAG;
      ART=2;
      SUSPEND;
      NR=NR+1;
     END
   end
  
/* G/N * /
/* Ergebnis Abrechnung */
 SELECT SUM(GESERG) FROM NKMASTER WHERE ONR=:ONR INTO BETRAG;
 IF (BETRAG IS NOT NULL) THEN
  BEGIN
   BETRAG=-BETRAG;
   SALDO=SALDO+BETRAG;
   IF (BETRAG>0) THEN
    BEGIN
     TEXT='Nachzahlungen aus Abrechnung (Abrechnungsergebnis)';
     ART=2;
     SUSPEND;
     NR=NR+1;
    END
   ELSE
    IF (BETRAG<0) THEN
     BEGIN
      TEXT='Guthaben aus Abrechnung (Abrechnungsergebnis)';
      ART=3;
      SUSPEND;
      NR=NR+1;
     END
  END
  
  
 /* Abgrenzung FestbetrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤ge */
 /* alle Konten nach Festbetrag */
 for select konten.knr, kbrutto, opbetrag, KBEZ from konten,euschlu
  where konten.onr=:ONR and KNR<100000
  and konten.onr = euschlu.onr
  and (konten.kuschlnr1 = euschlu.nr or konten.kuschlnr2 = euschlu.nr)
  and (euschlu.art=3 or euschlu.art=4)
  union
  select konten.knr, kbrutto, opbetrag, KBEZ from konten,buschlu
  where konten.onr=:ONR and KNR<100000
  and konten.onr = buschlu.onr
  and (konten.kuschlnr1 = buschlu.nr or konten.kuschlnr2 = buschlu.nr)
  and (buschlu.art=3 or buschlu.art=4)
  into :KNR, :KBRUTTO, :FESTBETRAG, :KBEZ
  do
   begin
    :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
    IF (KBRUTTO<>FESTBETRAG) THEN
     begin
      TEXT='Abgrenzung '|| KBEZ || ' (Kosten: ' || KBRUTTO || ' , Verbrauch: ' || FESTBETRAG ||')';
      BETRAG=KBRUTTO-FESTBETRAG;
      SALDO=SALDO+BETRAG;
      IF (BETRAG>=0) THEN
       ART=2;
      ELSE
       ART=3;
      SUSPEND;
      NR=NR+1;
     end
   end
   
   
    /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“CKLAGEN RLA */
 for select knr, kklasse, kbez from konten
  where onr=:onr and kklasse=22
  into :KNR, :KKLasse, :KBEZ
  do
   begin
    :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
    EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTBIS_PLUSEINS, 'J','N') RETURNING_VALUES :BETRAG;
    IF (BETRAG<>0 and BETRAG IS NOT NULL) THEN
     BEGIN
      ART=1;
      /* Endsaldo */
      SALDO=SALDO+BETRAG;
      TEXT='Saldo ' || KBEZ || ' per ' || DTBISTEXT;
      SUSPEND;
      NR=NR+1;
     END
   end
   

/***********************************/
/***********************************/
/***********************************/
/***********************************/
   
 /* abgestimmtes VermÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶gen */
 ART=4;
 BETRAG=SALDO;
 TEXT='Abgestimmtes VermÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶gen';
 SUSPEND;
 NR=NR+1;
 /* Vergleich mir RL 840 */
 /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“CKLAGEN RLP */
 SALDO_RL=0;
 for select knr, kklasse, kbez from konten
  where onr=:onr and kklasse=27 and RLPOS IS NOT NULL
  into :KNR, :KKLasse, :KBEZ
  do
   begin
    :KBEZ = SUBSTRING(:KBEZ FROM 1 FOR 88);
    EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTBIS_PLUSEINS, 'J','N') RETURNING_VALUES :BETRAG;
    IF (BETRAG<>0 and BETRAG IS NOT NULL) THEN
     BEGIN
      /* Endsaldo */
      SALDO_RL=SALDO_RL+BETRAG;
     END
   end
 BETRAG=SALDO_RL;
 TEXT='RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagenvermÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶gen per ' || DTBISTEXT;
 SUSPEND;
 NR=NR+1;
 DIFF=SALDO-SALDO_RL;
 BETRAG=DIFF;
 TEXT='Abstimmungsdifferenz';
 SUSPEND;
 NR=NR+1;



END
