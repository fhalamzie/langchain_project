-- Prozedur: USTLISTE_KONTO
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE USTLISTE_KONTO
DECLARE VARIABLE UST_TEMP INTEGER;
 DECLARE VARIABLE NETTO_TEMP INTEGER;
 DECLARE VARIABLE BRUTTO_TEMP INTEGER;
BEGIN
 IF (IST_BUCHHALTUNG='J') THEN
  BEGIN
   /* K Konto */
   IF (KKLASSE=1) THEN
    BEGIN
     /* K im Soll auf A/P direkt gebucht + */
     for select Sum(Betrag), SUM((BETRAG*100)/(MWST+100)), MWST from buchung
     where (ONRSOLL=:ONR And KSOLL=:KNR)
     and ((ONRHABEN=:ONR And ARTHABEN>=20 And ArtHaben<=27) OR (ArtHaben=1) OR (KHABEN=99990))
     and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWST
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      BEGIN
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      END
     /* K im Haben auf A/P direkt gebucht - */
     for select -Sum(Betrag), -SUM((BETRAG*100)/(MWST+100)), MWST from buchung
     where (ONRHABEN=:ONR And KHABEN=:KNR)
     and ((ONRSOLL=:ONR And ARTSOLL>=20 And ArtSoll<=27) OR (ArtSoll=1) OR (KSOLL=99990))
     and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWST
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      begin
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      end
     /*A/P im SOll, KRED im Haben, kein SpLIT -*/
     for select -Sum(Betrag), -SUM((BETRAG*100)/(MWSTOP+100)), MWSTOP from buchung
     where KNROP=:KNR
     AND (ONRSOLL=:ONR And ArtSoll>=20 And ArtSoll<=27)
          and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWSTOP
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      begin
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      end
     /*A/P im Haben, KRED im Soll, kein SPLIT +*/
     for select Sum(Betrag),SUM((BETRAG*100)/(MWSTOP+100)), MWSTOP from buchung
     where KNROP=:KNR
     AND
     (ONRHABEN=:ONR And ArtHaben>=20 And ArtHaben<=27)
     and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWSTOP
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      begin
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      end
     /* K SPLIT Bank immer im Haben bei Kosten*/
     for select sum(buchzahl.betrag),SUM((buchzahl.BETRAG*100)/(buchzahl.MWSTOP+100)),buchzahl.mwstop from buchzahl, buchung
     where buchzahl.knr=:KNR
     and buchzahl.bnr=buchung.bnr
     and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
     and (buchung.onrhaben=:ONR and buchung.arthaben>=20 and buchung.arthaben<=27)
     group by buchzahl.mwstop
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      begin
       if (BRUTTO IS NULL) then
        BRUTTO=0;
       if (NETTO IS NULL) then
        NETTO=0;
       UST=BRUTTO-Netto;
       SUSPEND;
      end
    END
   ELSE /* E */
    BEGIN
     /* E im Soll auf A/P direkt gebucht - */
     for select -Sum(Betrag), -SUM((BETRAG*100)/(MWST+100)), MWST from buchung
     where (ONRSOLL=:ONR And KSOLL=:KNR)
     and ((ONRHABEN=:ONR And ARTHABEN>=20 And ArtHaben<=27) OR (KSOLL=99990))
     and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWST
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      BEGIN
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      END
     /* E im Haben auf A/P direkt gebucht */
     for select Sum(Betrag), SUM((BETRAG*100)/(MWST+100)), MWST from buchung
     where (ONRHABEN=:ONR And KHABEN=:KNR)
     and ((ONRSOLL=:ONR And ARTSOLL>=20 And ArtSoll<=27) OR (KSOLL=99990))
     and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWST
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      begin
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      end
     /*A/P im SOll, DEB im Haben, kein SpLIT  */
     for select Sum(Betrag), SUM((BETRAG*100)/(MWSTOP+100)), MWSTOP from buchung
     where KNROP=:KNR
     AND (ONRSOLL=:ONR And ArtSoll>=20 And ArtSoll<=27)
          and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWSTOP
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      begin
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      end
     /*A/P im Haben, DEB im Soll, kein SPLIT +*/
     for select -Sum(Betrag), -SUM((BETRAG*100)/(MWSTOP+100)), MWSTOP from buchung
     where KNROP=:KNR
     AND
     (ONRHABEN=:ONR And ArtHaben>=20 And ArtHaben<=27)
     and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWSTOP
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      begin
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      end

     /* Umwandlungen G/N in geleistete BK*/
     IF (KKLASSE>=10 AND KKLASSE<=18) THEN
      BEGIN
       /* KEIN SPLIT */
       for select -Sum(Betrag),-SUM((BETRAG*100)/(MWSTOP+100)), MWSTOP from buchung
       where KNROP=:KNR
        AND (ONRSOLL=:ONR And ArtSoll>=60 And ArtSoll<=62)
        AND (ONRHABEN=:ONR And ArtHaben>=10  And ArtHaben<=18)
        and (Datum>=:DTVON and Datum<=:DTBIS)
       group by MWSTOP
       into :BRUTTO, :NETTO,  UST_PROZ
       do
        begin
         IF (BRUTTO IS NULL) THEN
          BRUTTO=0;
         IF (NETTO IS NULL) THEN
          NETTO=0;
         UST=BRUTTO-NETTO;
         IF (NETTO<>0 AND BRUTTO<>0) THEN
          SUSPEND;
        end
       /* SPLIT */
       for select -sum(buchzahl.betrag),-SUM((buchzahl.BETRAG*100)/(buchzahl.MWSTOP+100)),buchzahl.mwstop from buchzahl, buchung
       where buchzahl.knr=:KNR
        and buchzahl.bnr=buchung.bnr
        and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
        and (buchung.onrsoll=:ONR and buchung.artsoll>=60 and buchung.artsoll<=62)
       group by MWSTOP
       into :BRUTTO, :NETTO,  UST_PROZ
       do
        begin
         IF (BRUTTO IS NULL) THEN
          BRUTTO=0;
         IF (NETTO IS NULL) THEN
          NETTO=0;
         UST=BRUTTO-NETTO;
         IF (NETTO<>0 AND BRUTTO<>0) THEN
          SUSPEND;
        end
      END

     /* E SPLIT Bank immer im Soll bei E*/
     for select sum(buchzahl.betrag),SUM((buchzahl.BETRAG*100)/(buchzahl.MWSTOP+100)),buchzahl.mwstop from buchzahl, buchung
     where buchzahl.knr=:KNR
     and buchzahl.bnr=buchung.bnr
     and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
     and (buchung.onrsoll=:ONR and buchung.artsoll>=20 and buchung.artsoll<=27)
     group by buchzahl.mwstop
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      begin
       if (BRUTTO IS NULL) then
        BRUTTO=0;
       if (NETTO IS NULL) then
        NETTO=0;
       UST=BRUTTO-Netto;
       SUSPEND;
      end
    END
   END
  ELSE
    BEGIN  /* SOLL Buchhaltung */
     /* K/E im Soll  */
     for select Sum(Betrag), SUM((BETRAG*100)/(MWST+100)), MWST from buchung
     where (ONRSOLL=:ONR And KSOLL=:KNR)
     and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWST
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      BEGIN
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       IF (KKLASSE<>1) THEN
        BEGIN
         BRUTTO=-BRUTTO;
         NETTO=-NETTO;
        END
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      END
     /* - K im Haben E im HAben */
     for select Sum(Betrag), SUM((BETRAG*100)/(MWST+100)), MWST from buchung
     where (ONRHABEN=:ONR And KHABEN=:KNR)
     and (Datum>=:DTVON and Datum<=:DTBIS)
     group by MWST
     into :BRUTTO, :NETTO,  UST_PROZ
     do
      BEGIN
       IF (BRUTTO IS NULL) THEN
        BRUTTO=0;
       IF (NETTO IS NULL) THEN
        NETTO=0;
       IF (KKLASSE=1) THEN
        BEGIN
         BRUTTO=-BRUTTO;
         NETTO=-NETTO;
        END
       UST=BRUTTO-NETTO;
       IF (NETTO<>0 AND BRUTTO<>0) THEN
        SUSPEND;
      END
    END    /* SOLL Buchhaltung */
END
