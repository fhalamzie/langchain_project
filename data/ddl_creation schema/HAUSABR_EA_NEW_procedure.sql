-- Prozedur: HAUSABR_EA_NEW
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE HAUSABR_EA_NEW
DECLARE VARIABLE IGN SMALLINT;
DECLARE VARIABLE SCHLART SMALLINT;
DECLARE VARIABLE SCHL SMALLINT;
DECLARE VARIABLE ART SMALLINT;
DECLARE VARIABLE KKSTNR SMALLINT;
DECLARE VARIABLE TEMP_SUM NUMERIC(18, 2);
DECLARE VARIABLE TEMP_SUM_N NUMERIC(18, 2);
DECLARE VARIABLE RLPOS INTEGER;
DECLARE VARIABLE BHEIZ CHAR(1);
DECLARE VARIABLE ITMP INTEGER;
DECLARE VARIABLE SALDO_FESTG_SUM NUMERIC(18, 2);
DECLARE VARIABLE SALDO_GIROK_SUM NUMERIC(18, 2);
DECLARE VARIABLE SALDO_SONST_SUM NUMERIC(18, 2);
DECLARE VARIABLE SALDO_WDATU_SUM NUMERIC(18, 2);
DECLARE VARIABLE SDATUM VARCHAR(10);
DECLARE VARIABLE IKTO1 SMALLINT;
DECLARE VARIABLE IKTO2 SMALLINT;
DECLARE VARIABLE STMP1 VARCHAR(50);
DECLARE VARIABLE STMP2 VARCHAR(50);
DECLARE VARIABLE SALDO_G_GIROK NUMERIC(18, 2);
DECLARE VARIABLE SALDO_N_GIROK NUMERIC(18, 2);
DECLARE VARIABLE SALDO_G_SONST NUMERIC(18, 2);
DECLARE VARIABLE SALDO_N_SONST NUMERIC(18, 2);
DECLARE VARIABLE IKTOUNEINBR INTEGER;
DECLARE VARIABLE SKBEZ VARCHAR(188);
DECLARE VARIABLE SBEZTMP VARCHAR(200);
DECLARE VARIABLE SBEZTMP2 VARCHAR(200);
BEGIN
 SKBEZ='';
 GRUPPEN_NR = 0;
 IF (MIT_BEW_KTO = 'J') THEN
  BEGIN
   IKTO1 = 0;
   IKTO2 = 1;
  END
 ELSE
  BEGIN
   IKTO1 = 0;
   IKTO2 = 0;
  END
 /* Anfangsbestand */
 /* Anfang - Saldo zum DTVON */
 SDATUM = CAST(DTVON AS VARCHAR(10));
 KBEZ = 'Anfangsbestand per ' || SUBSTRING(SDATUM FROM 9 FOR 2) || '.' || SUBSTRING(SDATUM FROM 6 FOR 2) || '.' || SUBSTRING(SDATUM FROM 1 FOR 4);
 KLASSE = 0; OBJ = ONR; KNR = 0; SALDO_WDATU = 0;
 SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0;
 select KTOUNEINBRINGLICH from objekte where onr=:onr into :IKTOUNEINBR;
 if (IKTOUNEINBR IS NULL) then
  IKTOUNEINBR = 0;
 /* reine Bankkonten*/
 FOR
  select objbanken.banknr from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=0
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.BANKNR
  INTO :ITMP
 DO
  BEGIN
   EXECUTE PROCEDURE BANKSALDO_ALT(ITMP, DTVON) RETURNING_VALUES :TEMP_SUM;
   if (TEMP_SUM IS NULL) then
    TEMP_SUM = 0;
   SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
  END
 /* Kassen */
 FOR
  select objbanken.banknr from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=1
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.BANKNR
  INTO :ITMP
 DO
  BEGIN
   EXECUTE PROCEDURE BANKSALDO_ALT(ITMP, DTVON) RETURNING_VALUES :TEMP_SUM;
   if (TEMP_SUM IS NULL) then
    TEMP_SUM = 0;
   SALDO_SONST = SALDO_SONST + TEMP_SUM;
  END
 /* aktive Ruecklagenbestandskonten */
 FOR
  SELECT KNR from rueckbkt where ONR=:onr group by knr
 INTO :ITMP
 DO
  begin
   EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :ITMP, :DTVON, 'J','N') RETURNING_VALUES :TEMP_SUM;
   if (TEMP_SUM IS NULL) then
    TEMP_SUM = 0;
   SALDO_FESTG = SALDO_FESTG + TEMP_SUM;
  end
 /* sonstige aktive Bestandskonten */
 FOR
  SELECT KNR from konten where onr=:onr and KKLASSE=24 and KNR>0 and knr<>:IKTOUNEINBR group by knr
 INTO :ITMP
 DO
  begin
   EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :ITMP, :DTVON, 'J','N') RETURNING_VALUES :TEMP_SUM;
   if (TEMP_SUM IS NULL) then
    TEMP_SUM = 0;
   SALDO_SONST = SALDO_SONST + TEMP_SUM;
  end

 SALDO_FESTG_SUM = SALDO_FESTG;
 SALDO_GIROK_SUM = SALDO_GIROK;
 SALDO_SONST_SUM = SALDO_SONST;
 SALDO_WDATU_SUM = SALDO_WDATU;
 SUSPEND;
 /* Ende - Saldo zum DTVON */


 /* Anfang - Gebuchte Anfangsbestaende der Banken */
 KLASSE = 0; OBJ = ONR; KNR = 0; KBEZ = 'Anfangsbestand per ' || SDATUM; SALDO_WDATU = 0;
 SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0;
 /* reine Bankkonten*/
 FOR
  select objbanken.knr from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=0
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.KNR
  INTO :ITMP
 DO
  BEGIN
   select sum(betrag) from buchung where ksoll=:ITMP and khaben=98000 and onrsoll=:onr and (Datum >= :DTVON and Datum <= :DTBIS) into :TEMP_SUM;
   if (TEMP_SUM IS NULL) then
    TEMP_SUM = 0;
   SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
  END
 /* Kassen */
 FOR
  select objbanken.knr from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=1
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.KNR
  INTO :ITMP
 DO
  BEGIN
   select sum(betrag) from buchung where ksoll=:ITMP and khaben=98000 and onrsoll=:onr and (Datum >= :DTVON and Datum <= :DTBIS) into :TEMP_SUM;
   if (TEMP_SUM IS NULL) then
    TEMP_SUM = 0;
   SALDO_SONST = SALDO_SONST + TEMP_SUM;
  END
 /* aktive Ruecklagenbestandskonten */
 FOR
  SELECT KNR from rueckbkt where ONR=:onr group by knr
 INTO :ITMP
 DO
  begin
   select sum(betrag) from buchung where ksoll=:ITMP and khaben=98000 and onrsoll=:onr and (Datum >= :DTVON and Datum <= :DTBIS) into :TEMP_SUM;
   if (TEMP_SUM IS NULL) then
    TEMP_SUM = 0;
   SALDO_FESTG = SALDO_FESTG + TEMP_SUM;
  end
 /* sonstige aktive Bestandskonten */
 FOR
  SELECT KNR from konten where onr=:onr and KKLASSE=24 and KNR>0 and knr<>:IKTOUNEINBR group by knr
 INTO :ITMP
 DO
  begin
   select sum(betrag) from buchung where ksoll=:ITMP and khaben=98000 and onrsoll=:onr and (Datum >= :DTVON and Datum <= :DTBIS) into :TEMP_SUM;
   if (TEMP_SUM IS NULL) then
    TEMP_SUM = 0;
   SALDO_SONST = SALDO_SONST + TEMP_SUM;
  end

 IF ((SALDO_GIROK <> 0) or (SALDO_SONST <> 0) or (SALDO_FESTG <> 0)) THEN
  begin
   SALDO_FESTG_SUM = SALDO_FESTG_SUM + SALDO_FESTG;
   SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
   SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
   SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
   SUSPEND;
  end
 /* Ende - Gebuchte Anfangsbestaende der Banken */

 /* Anfang - Gebuchte Umsaetze anderer Objekte auf dem Konto */
 KLASSE = 0; OBJ = ONR; KNR = 0; KBEZ = 'UmsÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤tze anderer Objekte'; SALDO_WDATU = 0;
 SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0;
 /* reine Bankkonten*/
 FOR
  select objbanken.banknr from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=0
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.BANKNR
  INTO :ITMP
 DO
  BEGIN
   for
    select sum(betrag) from buchung where (onrsoll<>:onr and onrsoll<>0) and banknrsoll=:ITMP and (Datum >= :DTVON and Datum <= :DTBIS)
    union all
    select sum(-betrag) from buchung where (onrhaben<>:onr and onrhaben<>0) and banknrhaben=:ITMP and (Datum >= :DTVON and Datum <= :DTBIS)
    into :TEMP_SUM
   do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
    end
  END
 /* Kassen */
 FOR
  select objbanken.banknr from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=1
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.BANKNR
  INTO :ITMP
 DO
  BEGIN
   for
    select sum(betrag) from buchung where (onrsoll<>:onr and onrsoll<>0) and banknrsoll=:ITMP and (Datum >= :DTVON and Datum <= :DTBIS)
    union all
    select sum(-betrag) from buchung where (onrhaben<>:onr and onrhaben<>0) and banknrhaben=:ITMP and (Datum >= :DTVON and Datum <= :DTBIS)
    into :TEMP_SUM
   do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     SALDO_SONST = SALDO_SONST + TEMP_SUM;
    end
  END

 IF ((SALDO_GIROK <> 0) or (SALDO_SONST <> 0)) THEN
  begin
   SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
   SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
   SUSPEND;
  end
 /* Ende - Gebuchte Umsaetze anderer Objekte auf dem Konto */


 /* Anfang - Alle Einnahmen-/Ausgabenkonten */
 FOR
  SELECT KNR, KBEZ, KKLASSE, BHEIZ, KKSTNR, RLPOS, 0 as GN, KUSCHLNR1, EA from konten
  where ONR=:ONR AND (KKLASSE<20 or (KKLASSE>=110 and KKLASSE<=170)) and KNR>0
  union
  SELECT KNR, KBEZ, KKLASSE, BHEIZ, KKSTNR, RLPOS, 1 as GN, KUSCHLNR1, EA from konten
  where ONR=:ONR AND (KKLASSE=15 or (KKLASSE>=110 and KKLASSE<=170)) and KNR>0
  order by 9 desc, 1
 INTO :KNR, :SKBEZ, :KLASSE, :BHEIZ, :KKSTNR, :RLPOS, :IGN, :SCHL, :EA
 DO
  begin  
   KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
   OBJ = :ONR; SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0;
   IF (KBEZ = 'Hausgeld') THEN
    KBEZ = 'Hausgeldvorschuss';
   SBEZTMP = KBEZ;    
   /*  */
   if ((KLASSE = 1) or (KLASSE = 19)) then
    begin
     /* SOLL - Seite auswerten */
     for
      select betrag, art from buchung, konten, banken
      where (ONRSOLL=:onr or ONRHABEN=:onr) and (((KSOLL=:KNR) and ((ARTHABEN=20) or (ARTHABEN=1))) or ((KNROP=:KNR) and ((ARTHABEN=20) or (ARTHABEN=1))) or (GN=71 and KNROP=:KNR)) and (Datum >= :DTVON and Datum <= :DTBIS)
      and buchung.KHABEN=konten.knr and buchung.ONRHABEN=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2)
      union all
      select buchzahl.betrag, art from buchung, buchzahl, konten, banken
      where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=71) and (ARTHABEN=20) and (Datum >= :DTVON and Datum <= :DTBIS)
      and buchung.KHABEN=konten.knr and buchung.ONRHABEN=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2) and buchung.BNR=BUCHZAHL.BNR and buchzahl.knr=:knr
      union all
      select betrag, 2 from buchung, konten
      where (ONRSOLL=:onr or ONRHABEN=:onr) and (KSOLL=:KNR) and (ARTHABEN=24) and (Datum >= :DTVON and Datum <= :DTBIS)
      and buchung.KHABEN=konten.knr and buchung.ONRHABEN=konten.onr
     into :TEMP_SUM, :ART
     do
     begin
      if (TEMP_SUM IS NULL) then
       TEMP_SUM = 0;
      if (TEMP_SUM <> 0) then
       begin
        TEMP_SUM=-TEMP_SUM; /* Bank im Haben, VZ umdrehen */
        IF (ART = 0) THEN
         SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
        ELSE
         SALDO_SONST = SALDO_SONST + TEMP_SUM;
       END
     end

         /* Umbuchungen auswerten aktuelles AUSGABEKONTO im H*/
    select sum(betrag) from buchung
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=1) and (ARTHABEN=1) and (KHABEN=:KNR) and (Datum >= :DTVON and Datum <= :DTBIS)
    into :TEMP_SUM;
    if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
    if (TEMP_SUM<>0) THEN
     SALDO_GIROK = SALDO_GIROK + TEMP_SUM;

    /* Umbuchungen auswerten aktuelles AUSGABEKONTO im S*/
    select sum(betrag) from buchung
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=1) and (ARTHABEN=1) and (KSOLL=:KNR) and (Datum >= :DTVON and Datum <= :DTBIS)
    into :TEMP_SUM;
    if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
    if (TEMP_SUM<>0) THEN
     SALDO_GIROK = SALDO_GIROK - TEMP_SUM;

    /* Umbuchungen auswerten aktuelles EINNAHMEKONTO im H*/
    select sum(betrag) from buchung
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=19) and (ARTHABEN=19) and (KHABEN=:KNR) and (Datum >= :DTVON and Datum <= :DTBIS)
    into :TEMP_SUM;
    if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
    if (TEMP_SUM<>0) THEN
     SALDO_GIROK = SALDO_GIROK + TEMP_SUM;

    /* Umbuchungen auswerten aktuelles EINNAHMEKONTO im S*/
    select sum(betrag) from buchung
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=19) and (ARTHABEN=19) and (KSOLL=:KNR) and (Datum >= :DTVON and Datum <= :DTBIS)
    into :TEMP_SUM;
    if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
    if (TEMP_SUM<>0) THEN
     SALDO_GIROK = SALDO_GIROK - TEMP_SUM;


    /* */
    /* HABEN - Seite auswerten */
     for
      select betrag, art from buchung, konten, banken
      where (ONRSOLL=:onr or ONRHABEN=:onr) and (((KHABEN=:KNR) and ((ARTSOLL=20) or (ARTSOLL=1))) or ((KNROP=:KNR) and ((ARTSOLL=20) or (ARTSOLL=1))) or (GN=71 and KNROP=:KNR)) and (Datum >= :DTVON and Datum <= :DTBIS)
      and buchung.KSOLL=konten.knr and buchung.ONRSOLL=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2)
      union all
      select buchzahl.betrag, art from buchung, buchzahl, konten, banken
      where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTHABEN=71) and (ARTSOLL=20) and (Datum >= :DTVON and Datum <= :DTBIS)
      and buchung.KSOLL=konten.knr and buchung.ONRSOLL=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2) and buchung.BNR=BUCHZAHL.BNR and buchzahl.knr=:knr
      union all
      select betrag, 2 from buchung, konten
      where (ONRSOLL=:onr or ONRHABEN=:onr) and (KHABEN=:KNR) and (ARTSOLL=24) and (Datum >= :DTVON and Datum <= :DTBIS)
      and buchung.KSOLL=konten.knr and buchung.ONRSOLL=konten.onr
     into :TEMP_SUM, :ART
     do
     begin
      if (TEMP_SUM IS NULL) then
       TEMP_SUM = 0;
      if (TEMP_SUM <> 0) then
       begin
        IF (ART = 0) THEN
         SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
        ELSE
         SALDO_SONST = SALDO_SONST + TEMP_SUM;
       END
     end
    /* */
    for
     select max(kbruttogesamt) as gesamt from nkdetail where onr=:onr and kanrs=:knr group by kname
     into :TEMP_SUM
    do
     begin
      if (TEMP_SUM IS NULL) then
       TEMP_SUM = 0;
      SALDO_WDATU = SALDO_WDATU + TEMP_SUM;
     end
    /* */
    IF ((SALDO_GIROK <> 0) or (SALDO_SONST <> 0) or (SALDO_WDATU <> 0)) THEN
     begin
      SALDO_FESTG_SUM = SALDO_FESTG_SUM + SALDO_FESTG;
      SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
      SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
      SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
      IF (KLASSE=1) THEN
       begin
        GRUPPEN_NR=2; /* AUSGABE */
        /* Ausgaben - fuer die berechnung des SUM_SALDO OK */
        /* Ausgaben sind -, sollen aber in Gruppe Ausgaben nicht mit Minus angezeigt werden */
        SALDO_FESTG = - SALDO_FESTG;
        SALDO_GIROK = - SALDO_GIROK;
        SALDO_SONST = - SALDO_SONST;
        /* SALDO_WDATU NICHT UMDREHEN DA FESTBETRAG */
       end
      ELSE
       GRUPPEN_NR=1; /* EINNAHME */
      SUSPEND;
     end
   END
  ELSE
   BEGIN
    SALDO_G_GIROK = 0; SALDO_N_GIROK = 0; SALDO_G_SONST = 0; SALDO_N_SONST = 0;
    /* SOLL - Seite auswerten */
    for
     select betrag, art from buchung, konten, banken
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=20) and (KNROP=:KNR) and (GN=:IGN) and (Datum>=:DTVON and Datum<=:DTBIS) and (WDatum>=:DTVON and WDatum<=:DTBIS)
     and buchung.KSOLL=konten.knr and buchung.ONRSOLL=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2)
     union all
     select buchzahl.betrag, art from buchung, buchzahl, konten, banken
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=20) and (GN=:IGN) and (Datum >= :DTVON and Datum <= :DTBIS) and (WDatum>=:DTVON and WDatum<=:DTBIS)
     and buchung.KSOLL=konten.knr and buchung.ONRSOLL=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2) and buchung.BNR=BUCHZAHL.BNR and buchzahl.knr=:knr
    into :TEMP_SUM, :ART
    do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       /* TEMP_SUM=-TEMP_SUM; */
       IF (ART = 0) THEN
        BEGIN
         SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
         if (TEMP_SUM > 0) then
          SALDO_N_GIROK = SALDO_N_GIROK + TEMP_SUM;
         ELSE
          SALDO_G_GIROK = SALDO_G_GIROK + TEMP_SUM;
        END
       ELSE
        BEGIN
         SALDO_SONST = SALDO_SONST + TEMP_SUM;
         if (TEMP_SUM > 0) then
          SALDO_N_SONST = SALDO_N_SONST + TEMP_SUM;
         ELSE
          SALDO_G_SONST = SALDO_G_SONST + TEMP_SUM;
        END
      END
    end
    /* */
    /* HABEN - Seite auswerten */
    for
     select betrag, art from buchung, konten, banken
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTHABEN=20) and (KNROP=:KNR) and (GN=:IGN) and (Datum>=:DTVON and Datum<=:DTBIS) and (WDatum>=:DTVON and WDatum<=:DTBIS)
     and buchung.KHABEN=konten.knr and buchung.ONRHABEN=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2)
     union all
     select buchzahl.betrag, art from buchung, buchzahl, konten, banken
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTHABEN=20) and (GN=:IGN) and (Datum >= :DTVON and Datum <= :DTBIS) and (WDatum>=:DTVON and WDatum<=:DTBIS)
     and buchung.KHABEN=konten.knr and buchung.ONRHABEN=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2) and buchung.BNR=BUCHZAHL.BNR and buchzahl.knr=:knr
    into :TEMP_SUM, :ART
    do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       TEMP_SUM=-TEMP_SUM;
       IF (ART = 0) THEN
        BEGIN
         SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
         if (TEMP_SUM > 0) then
          SALDO_N_GIROK = SALDO_N_GIROK + TEMP_SUM;
         ELSE
          SALDO_G_GIROK = SALDO_G_GIROK + TEMP_SUM;
        END
       ELSE
        BEGIN
         SALDO_SONST = SALDO_SONST + TEMP_SUM;
         if (TEMP_SUM > 0) then
          SALDO_N_SONST = SALDO_N_SONST + TEMP_SUM;
         ELSE
          SALDO_G_SONST = SALDO_G_SONST + TEMP_SUM;
        END
      END
    end
    /* */
    IF ((SALDO_GIROK <> 0) or (SALDO_SONST <> 0)) THEN
     begin
      IF (KLASSE=1) THEN
       GRUPPEN_NR=2; /* AUSGABE */
      ELSE
       GRUPPEN_NR=1; /* EINNAHME */
      --
      if ((KNR = 60090) or (IGN = 1)) then
       BEGIN
        IF (KNR = 60090) THEN
         STMP1 = 'Bewohner'; 
        ELSE
         STMP1 = 'EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer';
        --
        if ((SALDO_G_GIROK <> 0) or (SALDO_G_SONST <> 0)) then
         begin
          SALDO_GIROK = SALDO_G_GIROK;
          SALDO_SONST = SALDO_G_SONST;
          IF (KNR = 60090) THEN
           SBEZTMP2 = 'Guthaben ' || STMP1 || ' aus Abr. Vj.';
          else
           SBEZTMP2 = 'Anpassung beschlossener VorschÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼sse (Guthaben) ' || STMP1 || ' aus Abr. Vj. (' || SBEZTMP || ')'; 
          KBEZ = SUBSTRING(SBEZTMP2 FROM 1 FOR 88);
          GRUPPEN_NR=2; /* AUSGABE */
          SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
          SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
          SALDO_GIROK = -SALDO_GIROK;
          SALDO_SONST = -SALDO_SONST;
          SUSPEND;
         end
        --
        if ((SALDO_N_GIROK <> 0) or (SALDO_N_SONST <> 0)) then
         begin
          SALDO_GIROK = SALDO_N_GIROK;
          SALDO_SONST = SALDO_N_SONST;
          IF (KNR = 60090) THEN
           SBEZTMP2 = 'Nachzahlung ' || STMP1 || ' aus Abr. Vj.';
          else
           SBEZTMP2 = 'NachschÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼sse (Nachzahlung) ' || STMP1 || ' aus Abr. Vj. (' || SBEZTMP || ')'; 
          KBEZ = SUBSTRING(SBEZTMP2 FROM 1 FOR 88);
          GRUPPEN_NR=1; /* EINNAHME */
          SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
          SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
          SUSPEND;
         end
       END
      ELSE
       BEGIN
        SALDO_FESTG_SUM = SALDO_FESTG_SUM + SALDO_FESTG;
        SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
        SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
        SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
        SUSPEND;
       END
     end
    SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0;
    SALDO_G_GIROK = 0; SALDO_N_GIROK = 0; SALDO_G_SONST = 0; SALDO_N_SONST = 0;

    /* Abgrenzungen SOLL - Seite auswerten */
    for
     select betrag, art from buchung, konten, banken
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=20) and (KNROP=:KNR) and (GN=:IGN) and (Datum>=:DTVON and Datum<=:DTBIS) and (WDatum<:DTVON or WDatum>:DTBIS)
     and buchung.KSOLL=konten.knr and buchung.ONRSOLL=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2)
     union all
     select buchzahl.betrag, art from buchung, buchzahl, konten, banken
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTSOLL=20) and (GN=:IGN) and (Datum >= :DTVON and Datum <= :DTBIS) and (WDatum<:DTVON or WDatum>:DTBIS)
     and buchung.KSOLL=konten.knr and buchung.ONRSOLL=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2) and buchung.BNR=BUCHZAHL.BNR and buchzahl.knr=:knr
    into :TEMP_SUM, :ART
    do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       IF (ART = 0) THEN
        BEGIN
         SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
         if (TEMP_SUM > 0) then
          SALDO_N_GIROK = SALDO_N_GIROK + TEMP_SUM;
         ELSE
          SALDO_G_GIROK = SALDO_G_GIROK + TEMP_SUM;
        END
       ELSE
        BEGIN
         SALDO_SONST = SALDO_SONST + TEMP_SUM;
         if (TEMP_SUM > 0) then
          SALDO_N_SONST = SALDO_N_SONST + TEMP_SUM;
         ELSE
          SALDO_G_SONST = SALDO_G_SONST + TEMP_SUM;
        END
      END
    end
    /* */
    /* Abgrenzungen HABEN - Seite auswerten */
    for
     select betrag, art from buchung, konten, banken
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTHABEN=20) and (KNROP=:KNR) and (GN=:IGN) and (Datum>=:DTVON and Datum<=:DTBIS) and (WDatum<:DTVON or WDatum>:DTBIS)
     and buchung.KHABEN=konten.knr and buchung.ONRHABEN=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2)
     union all
     select buchzahl.betrag, art from buchung, buchzahl, konten, banken
     where (ONRSOLL=:onr or ONRHABEN=:onr) and (ARTHABEN=20) and (GN=:IGN) and (Datum >= :DTVON and Datum <= :DTBIS) and (WDatum<:DTVON or WDatum>:DTBIS)
     and buchung.KHABEN=konten.knr and buchung.ONRHABEN=konten.onr and banken.nr=KONTEN.BANKNR and (BEW=:IKTO1 or BEW=:IKTO2) and buchung.BNR=BUCHZAHL.BNR and buchzahl.knr=:knr
    into :TEMP_SUM, :ART
    do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       TEMP_SUM=-TEMP_SUM;
       IF (ART = 0) THEN
        BEGIN
         SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
         if (TEMP_SUM > 0) then
          SALDO_N_GIROK = SALDO_N_GIROK + TEMP_SUM;
         ELSE
          SALDO_G_GIROK = SALDO_G_GIROK + TEMP_SUM;
        END
       ELSE
        BEGIN
         SALDO_SONST = SALDO_SONST + TEMP_SUM;
         if (TEMP_SUM > 0) then
          SALDO_N_SONST = SALDO_N_SONST + TEMP_SUM;
         ELSE
          SALDO_G_SONST = SALDO_G_SONST + TEMP_SUM;
        END
      END
    end
    /* */
    IF ((SALDO_GIROK <> 0) or (SALDO_SONST <> 0)) THEN
     begin
      IF (KLASSE=1) THEN
       GRUPPEN_NR=2; /* AUSGABE */
      ELSE
       GRUPPEN_NR=1; /* EINNAHME */
      --
      if ((KNR = 60090) or (IGN = 1)) then
       BEGIN
        IF (KNR = 60090) THEN
         STMP1 = 'Bewohner';
        ELSE
         STMP1 = 'EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer';
        --
        if ((SALDO_G_GIROK <> 0) or (SALDO_G_SONST <> 0)) then
         begin
          SALDO_GIROK = SALDO_G_GIROK;
          SALDO_SONST = SALDO_G_SONST;
          IF (KNR = 60090) THEN
           SBEZTMP2 = 'Guthaben ' || STMP1 || ' (Abgr. Vor-/Folgejahre)';
          else
           SBEZTMP2 = 'Anpassung beschlossener VorschÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼sse (Guthaben) ' || STMP1 || ' (Abgr. Vor-/Folgejahre; ' || SBEZTMP || ')';
          KBEZ = SUBSTRING(SBEZTMP2 FROM 1 FOR 88);
          GRUPPEN_NR=2; /* AUSGABE */
          SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
          SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
          SALDO_GIROK = -SALDO_GIROK;
          SALDO_SONST = -SALDO_SONST;
          SUSPEND;
         end
        --
        if ((SALDO_N_GIROK <> 0) or (SALDO_N_SONST <> 0)) then
         begin
          SALDO_GIROK = SALDO_N_GIROK;
          SALDO_SONST = SALDO_N_SONST;
          IF (KNR = 60090) THEN
           SBEZTMP2 = 'Nachzahlung ' || STMP1 || ' (Abgr. Vor-/Folgejahre)';
          else
           SBEZTMP2 = 'NachschÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼sse (Nachzahlung) ' || STMP1 || ' (Abgr. Vor-/Folgejahre; ' || SBEZTMP || ')';
          KBEZ = SUBSTRING(SBEZTMP2 FROM 1 FOR 88); 
          GRUPPEN_NR=1; /* EINNAHME */
          SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
          SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
          SUSPEND;
         end
       END
      ELSE
       BEGIN
        KBEZ = KBEZ || ' (Abgr. Vor-/Folgejahre)';
        SALDO_FESTG_SUM = SALDO_FESTG_SUM + SALDO_FESTG;
        SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
        SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
        SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
        SUSPEND;
       END
     end
   END
  END
 /* Ende - Alle Einnahmen-/Ausgabenkonten */
 
 /* Anfang - Konten BGH-Urteil-Heizkosten */
 GRUPPEN_NR=2; /* AUSGABE */
 KLASSE=1;
 OBJ=:OBJ;
 KNR=0;
 KBEZ='';
 SALDO_FESTG=0;
 SALDO_GIROK=0;
 SALDO_SONST=0;
 SALDO_WDATU=0;
 EA=1;
 for
  select kname, max(kbruttogesamt) as gesamt from nkdetail where onr=:onr and kanrs='99999' and haupt_nr=1 group by kname
 into :KBEZ, :SALDO_WDATU
 do
  begin
   if (SALDO_WDATU IS NULL) then 
    SALDO_WDATU = 0;
   IF (SALDO_WDATU <> 0) THEN
    begin
     SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
     SUSPEND;
    end    
  end
 /* Ende - Konten BGH-Urteil-Heizkosten */

 /* Anfang - ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrage an passive RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen-Bestandskonten  */
 OBJ = :ONR; SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0; KBEZ = ''; KNR = 0;
 FOR
  select sum(buchzahl.BETRAG), buchzahl.ARTOP, rueckbkt.RUECKPOS from buchung, buchzahl, rueckbkt
  where (ONRSOLL=:onr or ONRHABEN=:onr) and (KSOLL in (select knr from rueckbkt where onr=:onr group by knr)) and (ARTHABEN in (27)) and (Datum >= :DTVON and Datum <= :DTBIS)
  and buchzahl.BNR=buchung.bnr and rueckbkt.onr=:onr and RUECKBKT.knr=buchzahl.knr and buchzahl.betrag<>0 group by buchzahl.ARTOP, rueckbkt.RUECKPOS
 into :TEMP_SUM, :ART, :RLPOS
 DO
  BEGIN
   SALDO_FESTG = SALDO_FESTG + TEMP_SUM;
   EXECUTE STATEMENT 'select name, case (' || :ART || ')
    when 1 then pos1name
    when 2 then pos2name
    when 3 then pos3name
    when 4 then pos4name
    when 5 then pos5name
    when 6 then pos6name
    when 7 then pos7name
    when 8 then pos8name
    when 9 then pos9name
    when 10 then pos10name
    else pos1name end from rueckpos where nr=' || :RLPOS INTO :STMP1, :STMP2;
   KBEZ = STMP2 || ' fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r ' || STMP1;
   IF (:TEMP_SUM < 0) then
    GRUPPEN_NR=2;
   ELSE
    GRUPPEN_NR=1;
   --
   IF (SALDO_FESTG <> 0) THEN
    BEGIN
     SALDO_FESTG_SUM = SALDO_FESTG_SUM + SALDO_FESTG;
     SALDO_FESTG = ABS(SALDO_FESTG);
     SUSPEND;
     SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0; KBEZ = ''; KNR = 0;
    END
  END
 /* Ende - ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrage an passive RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen-Bestandskonten  */


 /* Anfang - ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrage an andere aktive Bestandskonten */
 OBJ = :ONR; SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0;
 KBEZ = 'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤ge'; KNR = 0; GRUPPEN_NR=3;
 FOR
  select objbanken.knr, 0 from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=0
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.KNR
  union all
  select objbanken.knr, 1 from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=1
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.KNR
  union all
  select knr, 2 from rueckbkt where onr=:onr group by knr
  union all
  select knr, 1 from konten where onr=:onr and KKLASSE=24 and KNR>0 and knr<>:IKTOUNEINBR group by knr
 INTO :ITMP, :ART
 DO
  begin
   /* SOLL - Seite auswerten */
   for
    select SUM(betrag) from buchung
    where (ONRSOLL=:onr or ONRHABEN=:onr) and (KSOLL=:ITMP) and (ARTHABEN in (20, 22, 24)) and (Datum >= :DTVON and Datum <= :DTBIS)
   into :TEMP_SUM
   do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       IF (ART = 0) THEN
        SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
       ELSE
        BEGIN
         IF (ART = 1) THEN
          SALDO_SONST = SALDO_SONST + TEMP_SUM;
         ELSE
          SALDO_FESTG = SALDO_FESTG + TEMP_SUM;
        END
      END
    end
   /* */
   /* HABEN - Seite auswerten */
   for
    select SUM(betrag) from buchung
    where (ONRSOLL=:onr or ONRHABEN=:onr) and (KHABEN=:ITMP) and (ARTSOLL in (20, 22, 24)) and (Datum >= :DTVON and Datum <= :DTBIS)
   into :TEMP_SUM
   do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       IF (ART = 0) THEN
        SALDO_GIROK = SALDO_GIROK - TEMP_SUM;
       ELSE
        BEGIN
         IF (ART = 1) THEN
          SALDO_SONST = SALDO_SONST - TEMP_SUM;
         ELSE
          SALDO_FESTG = SALDO_FESTG - TEMP_SUM;
        END
      END
    end
  end
 /* */
 IF ((SALDO_GIROK <> 0) or (SALDO_SONST <> 0) or (SALDO_FESTG <> 0)) THEN
  BEGIN
   SALDO_FESTG_SUM = SALDO_FESTG_SUM + SALDO_FESTG;
   SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
   SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
   SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
   SUSPEND;
   SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0; KBEZ = ''; KNR = 0;
  END
 /* Ende - ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrage an andere aktive Bestandskonten */


 /* Anfang - ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrage an das Durchlaufkonto 99990 */
 OBJ = :ONR; SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0;
 KBEZ = 'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrag an Durchlaufkto.'; KNR = 0; GRUPPEN_NR=3;
 FOR
  select objbanken.knr, 0 from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=0
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.KNR
  union all
  select objbanken.knr, 1 from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=1
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.KNR
  union all
  select knr, 2 from rueckbkt where onr=:onr group by knr
  union all
  select knr, 1 from konten where onr=:onr and KKLASSE=24 and KNR>0 and knr<>:IKTOUNEINBR group by knr
 INTO :ITMP, :ART
 DO
  begin
   /* SOLL - Seite auswerten */
   for
    select SUM(betrag) from buchung
    where (ONRSOLL=:onr or ONRHABEN=:onr) and (KSOLL=:ITMP) and (KHABEN=99990) and (Datum >= :DTVON and Datum <= :DTBIS)
   into :TEMP_SUM
   do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       IF (ART = 0) THEN
        SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
       ELSE
        BEGIN
         IF (ART = 1) THEN
          SALDO_SONST = SALDO_SONST + TEMP_SUM;
         ELSE
          SALDO_FESTG = SALDO_FESTG + TEMP_SUM;
        END
      END
    end
   /* */
   /* HABEN - Seite auswerten */
   for
    select SUM(betrag) from buchung
    where (ONRSOLL=:onr or ONRHABEN=:onr) and (KHABEN=:ITMP) and (KSOLL=99990) and (Datum >= :DTVON and Datum <= :DTBIS)
   into :TEMP_SUM
   do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       IF (ART = 0) THEN
        SALDO_GIROK = SALDO_GIROK - TEMP_SUM;
       ELSE
        BEGIN
         IF (ART = 1) THEN
          SALDO_SONST = SALDO_SONST - TEMP_SUM;
         ELSE
          SALDO_FESTG = SALDO_FESTG - TEMP_SUM;
        END
      END
    end
  end
 /* */
 IF ((SALDO_GIROK <> 0) or (SALDO_SONST <> 0) or (SALDO_FESTG <> 0)) THEN
  BEGIN
   SALDO_FESTG_SUM = SALDO_FESTG_SUM + SALDO_FESTG;
   SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
   SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
   SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
   SUSPEND;
   SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0; KBEZ = ''; KNR = 0;
  END
 /* Ende - ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrage an das Durchlaufkonto 99990 */


 /* Anfang - ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrage an passive Bestandskonten ohne RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
 OBJ = :ONR; SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0;
 KBEZ = 'ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤ge an passive Bestandskonten'; KNR = 0;
 FOR
  select objbanken.knr, 0 from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=0
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.KNR
  union all
  select objbanken.knr, 1 from objbanken, banken, konten where objbanken.onr=:onr and objbanken.BANKNR=banken.nr and ART=1
   and objbanken.onr=konten.onr and objbanken.knr=konten.knr and (BEW=:IKTO1 or BEW=:IKTO2)
   group by OBJBANKEN.KNR
  union all
  select knr, 1 from konten where onr=:onr and KKLASSE=24 and KNR>0 and knr<>:IKTOUNEINBR group by knr
 INTO :ITMP, :ART
 DO
  begin
   /* SOLL - Seite auswerten */
   for
    select SUM(betrag) from buchung
    where (ONRSOLL=:onr or ONRHABEN=:onr) and (KSOLL=:ITMP) and (ARTHABEN in (27)) and (Datum >= :DTVON and Datum <= :DTBIS)
   into :TEMP_SUM
   do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       IF (ART = 0) THEN
        SALDO_GIROK = SALDO_GIROK + TEMP_SUM;
       ELSE
        BEGIN
         IF (ART = 1) THEN
          SALDO_SONST = SALDO_SONST + TEMP_SUM;
        END
      END
    end
   /* */
   /* HABEN - Seite auswerten */
   for
    select SUM(betrag) from buchung
    where (ONRSOLL=:onr or ONRHABEN=:onr) and (KHABEN=:ITMP) and (ARTSOLL in (27)) and (Datum >= :DTVON and Datum <= :DTBIS)
   into :TEMP_SUM
   do
    begin
     if (TEMP_SUM IS NULL) then
      TEMP_SUM = 0;
     if (TEMP_SUM <> 0) then
      begin
       IF (ART = 0) THEN
        SALDO_GIROK = SALDO_GIROK - TEMP_SUM;
       ELSE
        BEGIN
         IF (ART = 1) THEN
          SALDO_SONST = SALDO_SONST - TEMP_SUM;
         ELSE
          SALDO_FESTG = SALDO_FESTG - TEMP_SUM;
        END
      END
    end
  end

 IF ((SALDO_GIROK <> 0) or (SALDO_SONST <> 0) or (SALDO_FESTG <> 0)) THEN
  BEGIN
   SALDO_FESTG_SUM = SALDO_FESTG_SUM + SALDO_FESTG;
   SALDO_GIROK_SUM = SALDO_GIROK_SUM + SALDO_GIROK;
   SALDO_SONST_SUM = SALDO_SONST_SUM + SALDO_SONST;
   SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
   SUSPEND;
   SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0; KBEZ = ''; KNR = 0;
  END
 /* Ende - ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“bertrage an passive Bestandskonten ohne RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */

 /* Salden der Bestandskonten einfÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼gen */
 KLASSE = 9999;
 OBJ = ONR;
 KNR = 0;
 SDATUM = CAST(DTBIS AS VARCHAR(10));
 KBEZ = 'Endbestand per ' || SUBSTRING(SDATUM FROM 9 FOR 2) || '.' || SUBSTRING(SDATUM FROM 6 FOR 2) || '.' || SUBSTRING(SDATUM FROM 1 FOR 4);
 SALDO_FESTG = SALDO_FESTG_SUM;
 SALDO_GIROK = SALDO_GIROK_SUM;
 SALDO_SONST = SALDO_SONST_SUM;
 /* SALDO_WDATU = SALDO_WDATU_SUM; */
 SALDO_WDATU = 0; /* Uwe: wenn ich im Bericht die W-DATUM spalte = verteilungsrelevante BetrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤ge summiere muss das hier 0 sein */
 GRUPPEN_NR=4;
 SUSPEND;

 /* Uwe kommt im Bericht am SchluÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¸ */
 /* Anfang - ZufÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrungen und Entnahmen ausweisen */
 OBJ = :ONR; SALDO_FESTG = 0; SALDO_GIROK = 0; SALDO_SONST = 0; SALDO_WDATU = 0;
 select max(RL_GESAMTSOLL - ENTRL_GESAMT) as RL from nkmaster where onr=:onr into :TEMP_SUM;
 if (TEMP_SUM IS NULL) then
  TEMP_SUM = 0;
 SALDO_WDATU = TEMP_SUM;

 IF (SALDO_WDATU <> 0) THEN
  begin
   KLASSE = 0;
   KBEZ = 'Geplante ErhaltungsrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagenzufÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung abzgl. Entnahmen';
   SALDO_WDATU_SUM = SALDO_WDATU_SUM + SALDO_WDATU;
   GRUPPEN_NR=5;
   SUSPEND;
  end
 /* Ende - ZufÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrungen und Entnahmen ausweisen */

END
