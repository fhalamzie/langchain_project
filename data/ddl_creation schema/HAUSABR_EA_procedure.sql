-- Prozedur: HAUSABR_EA
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE HAUSABR_EA
DECLARE VARIABLE IMWSTART INTEGER;
DECLARE VARIABLE KTOUNEINBRINGLICH INTEGER;
DECLARE VARIABLE IPROZ_UST NUMERIC(15, 4);
DECLARE VARIABLE IBNR INTEGER;
DECLARE VARIABLE IMWST NUMERIC(15, 2);
DECLARE VARIABLE RVORTRAG NUMERIC(15, 2);
DECLARE VARIABLE KBEW1 CHAR(1);
DECLARE VARIABLE KBEW2 CHAR(1);
DECLARE VARIABLE IS_KVERTEILUNG CHAR(1);
DECLARE VARIABLE IS_KBEW CHAR(1);
DECLARE VARIABLE IS_HAUSTYP INTEGER;
DECLARE VARIABLE TEMP_SUM NUMERIC(15, 2);
DECLARE VARIABLE TEMP_UST NUMERIC(15, 2);
DECLARE VARIABLE KKSTNR INTEGER;
DECLARE VARIABLE KONTONR VARCHAR(30);
DECLARE VARIABLE BHEIZ VARCHAR(1);
DECLARE VARIABLE IHEIZK INTEGER;
DECLARE VARIABLE IHEIZEXTERN INTEGER;
DECLARE VARIABLE LEVBANKNR INTEGER;
DECLARE VARIABLE IGN SMALLINT;
DECLARE VARIABLE DTVONBDATUM DATE;
DECLARE VARIABLE DTBISBDATUM DATE;
DECLARE VARIABLE DTVONWDATUM DATE;
DECLARE VARIABLE DTBISWDATUM DATE;
DECLARE VARIABLE ITMP INTEGER;
DECLARE VARIABLE RLPOS INTEGER;
DECLARE VARIABLE RUECKL1 NUMERIC(15, 2);
DECLARE VARIABLE RUECKL2 NUMERIC(15, 2);
DECLARE VARIABLE RUECKL3 NUMERIC(15, 2);
DECLARE VARIABLE RUECKL4 NUMERIC(15, 2);
DECLARE VARIABLE RUECKL5 NUMERIC(15, 2);
DECLARE VARIABLE RUECKL6 NUMERIC(15, 2);
DECLARE VARIABLE RUECKL7 NUMERIC(15, 2);
DECLARE VARIABLE RUECKLAB NUMERIC(15, 2);
DECLARE VARIABLE SKBEZ VARCHAR(188);
BEGIN
 RUECKL1=0;
 RUECKL2=0;
 RUECKL3=0;
 RUECKL4=0;
 RUECKL5=0;
 RUECKL6=0;
 RUECKL7=0;
 RUECKLAB=0;
 SKBEZ='';
 SALDOGES_EK=0;
 SALDOGES_AP=0;
 EA=1;
 UST_E=0;
 UST_A=0;
 UST_AANRECH=0;
 ABRVON=DTVON;
 ABRBIS=DTBIS;
 If (VON_ONR=BIS_ONR) THEN
  ISAMMEL=0;
 ELSE
  ISAMMEL=1;
 /* W_Datum abfragen  */
 if (IS_WDATUM = 'N') then
  begin
   DTVONBDATUM = DTVON;
   DTBISBDATUM = DTBIS;
   DTVONWDATUM = '01.01.1900';
   DTBISWDATUM = '01.01.1900';
  end
 else
  begin
   DTVONBDATUM = '01.01.1900';
   DTBISBDATUM = '01.01.1900';
   DTVONWDATUM = DTVON;
   DTBISWDATUM = DTBIS;
  end  
 FOR SELECT ONR, BSONST, HUWERT from OBJEKTE
 WHERE ONR>=:VON_ONR and ONR<=:BIS_ONR
 INTO :ONR, :IS_HAUSTYP, :IPROZ_UST
 DO
  BEGIN
   IF (IPROZ_UST IS null) THEN
    IPROZ_UST=0;
   IF (IPROZ_UST<>0) THEN
    IPROZ_UST=IPROZ_UST / 100;
   IF (IS_HAUSTYP = 0) THEN
    BEGIN
     KBEW1='J';
     KBEW2='J';
    END
   ELSE
    IF (IS_HAUSTYP = 1) THEN
     BEGIN
      KBEW1='N';
      KBEW2='N';
    END
   ELSe
    BEGIN /* Miet & WEG */
     IF (IS_ABR_HAUSTYP=0) THEN  /* Nur Miet bei Pro Haus */
      BEGIN
       KBEW1='J';
       KBEW2='J';
      END
     ELSE
      IF (IS_ABR_HAUSTYP=1) THEN  /* Nur WEG bei Pro Haus */
       BEGIN
        KBEW1='N';
        KBEW2='N';
       END
      ELSE
       BEGIN
        KBEW1='J';
        KBEW2='N';
       END
    END
   /* Alle E/K Konten*/
   FOR
    SELECT KNR, KNRSTR, KBEZ, IFREI1, KKLASSE, KVERTEILUNG, BHEIZ, IHEIZK, IHEIZEXT, KBEW, KKSTNR, RLPOS, 0 as GN, NICHT_IN_EAR from konten where ONR=:ONR AND (KKLASSE<20 or (KKLASSE>=110 and KKLASSE<=580)) and KKLASSE<>18 AND (KBEW=:KBEW1 OR KBEW=:KBEW2 OR KKSTNR=3) and KNR not in (50,51,52,53,54,60,61,62,63,64,0)
    union
    SELECT KNR, KNRSTR, KBEZ, IFREI1, KKLASSE, KVERTEILUNG, BHEIZ, IHEIZK, IHEIZEXT, KBEW, KKSTNR, RLPOS, 1 as GN, NICHT_IN_EAR from konten where ONR=:ONR AND (KKLASSE=15 or (KKLASSE>=110 and KKLASSE<=580)) AND (KBEW=:KBEW1 OR KBEW=:KBEW2 OR KKSTNR=3) and KNR not in (50,51,52,53,54,60,61,62,63,64,0)
    union
    SELECT KNR, KNRSTR, KBEZ, IFREI1, KKLASSE, KVERTEILUNG, BHEIZ, IHEIZK, IHEIZEXT, KBEW, KKSTNR, RLPOS, 0 as GN, NICHT_IN_EAR from konten where ONR=:ONR AND (KNR in (50,51,52,53,54,60,61,62,63,64)) and (:IS_ABR_HAUSTYP <> 1)
    order by 5
   INTO :KNR, :KNRSTR, :SKBEZ, :IMWSTART, :KLASSE, :IS_KVERTEILUNG, :BHEIZ, :IHEIZK, :IHEIZEXTERN, :IS_KBEW, :KKSTNR, :RLPOS, :IGN, NICHT_IN_EAR
   DO
    begin
     KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
     SAUS=0;
     SEIN=0;
     UST_A=0;
     UST_E=0;
     UST_AANRECH=0;
     IF (BHEIZ IS NULL) THEN
      BHEIZ='N';
     IF (IHEIZEXTERN IS NULL) THEN
      IHEIZEXTERN=-1;
     IF (IHEIZK IS NULL) THEN
      IHEIZK=-1;
     IF (IHEIZK>0 OR IHEIZEXTERN>0) THEN
      BHEIZ='J';
     IF (IGN=1) THEN
      BEGIN
       SKBEZ = 'Guthaben/Nachzahlung ' || KBEZ;
       KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
      END
     IF (IST_BUCHHALTUNG='J') THEN
      BEGIN
       IF (IS_WDATUM='N') THEN
        BEGIN
         /* E/K im Soll auf A/P direkt gebucht */
         select Sum(Betrag), Sum(Betrag - ((BETRAG*100) / (100+MWST))) from buchung   
         where (ONRSOLL=:ONR And KSOLL=:KNR)
         and ((ONRHABEN=:ONR OR ONRHABEN=0) And ((ARTHABEN>=20 And ArtHaben<=30) OR (ARTHABEN=1 OR ARTHABEN=19)))
         and (Datum>=:DTVON and Datum<=:DTBIS)
         and (GN=:IGN or GN=71)
         into :TEMP_SUM, TEMP_UST;
         if (TEMP_SUM IS NULL) then
          TEMP_SUM=0;
         if (TEMP_UST IS NULL) then
          TEMP_UST=0;
         IF ((KLASSE>=110) and (KLASSE<=580)) THEN
          TEMP_UST=0;   
         IF (KLASSE=1) THEN
          BEGIN
           SAUS=TEMP_SUM;
           UST_A=TEMP_UST;
          END
         ELSE
          BEGIN
           SEIN=-TEMP_SUM;
           UST_E=-TEMP_UST;
          END
         /* E/K im Haben direkt auf A/P gebucht*/
         select Sum(Betrag), Sum(Betrag - ((BETRAG*100) / (100+MWST))) from buchung
         where (ONRHABEN=:ONR And KHABEN=:KNR)
         and ((ONRSOLL=:ONR or ONRSOLL=0) And ((ARTSOLL>=20 And ArtSoll<=30) OR (ARTSOLL=1 OR ARTSOLL=19)))
         and (Datum>=:DTVON and Datum<=:DTBIS)
         and (GN=:IGN or GN=71)
         into :TEMP_SUM, TEMP_UST;
         if (TEMP_SUM IS NULL) then
          TEMP_SUM=0;
         if (TEMP_UST IS NULL) then
          TEMP_UST=0;
         IF ((KLASSE>=110) and (KLASSE<=580)) THEN
          TEMP_UST=0;
         IF (KLASSE=1) THEN
          begin
           SAUS=SAUS-TEMP_SUM;
           UST_A=UST_A-TEMP_UST;
          end
         ELSE
          begin
           SEIN=SEIN+TEMP_SUM;
           UST_E=TEMP_UST;
          end
         /*A/P im SOll, DEB/KRED im Haben, kein SpLIT*/
         select Sum(Betrag), Sum(Betrag - ((BETRAG*100) / (100+MWSTOP))) from buchung
         where KNROP=:KNR
         AND
         (ONRSOLL=:ONR And ArtSoll>=20 And ArtSoll<=27)
         and (Datum>=:DTVON and Datum<=:DTBIS)
         and (GN=:IGN or GN=71)
         into :TEMP_SUM, TEMP_UST;
         if (TEMP_SUM IS NULL) then
          TEMP_SUM=0;
         if (TEMP_UST IS NULL) then
          TEMP_UST=0;
         IF ((KLASSE>=110) and (KLASSE<=580)) THEN
          TEMP_UST=0; 
         IF (KLASSE=1) THEN
          BEGIN
           SAUS=SAUS - TEMP_SUM;
           UST_A=UST_A-TEMP_UST;
          END
         ELSE
          BEGIN
           SEIN=SEIN + TEMP_SUM;
           UST_E=UST_E+TEMP_UST;
          END
         /*A/P im Haben, DEB/KRED im Soll, kein SPLIT*/
         select Sum(Betrag),Sum(Betrag - ((BETRAG*100) / (100+MWSTOP))) from buchung
         where KNROP=:KNR
         and (GN=:IGN or GN=71)
         AND
         (ONRHABEN=:ONR And ArtHaben>=20 And ArtHaben<=27)
         and (Datum>=:DTVON and Datum<=:DTBIS)
         into :TEMP_SUM, TEMP_UST;
         if (TEMP_SUM IS NULL) then
          TEMP_SUM=0;
         if (TEMP_UST IS NULL) then
          TEMP_UST=0;
         IF ((KLASSE>=110) and (KLASSE<=580)) THEN
          TEMP_UST=0; 
         IF (KLASSE=1) THEN
          BEGIN
           SAUS=SAUS + TEMP_SUM;
           UST_A=UST_A+TEMP_UST;
          END
         ELSE
          BEGIN
           SEIN=SEIN - TEMP_SUM;
           UST_E=UST_E-TEMP_UST;
          END
         /* Umwandlungen G/N in geleistete BK*/
         IF (KLASSE>=10 AND KLASSE<=18) THEN
          BEGIN
           /* KEIN SPLIT */
           select Sum(Betrag),Sum(Betrag - ((BETRAG*100) / (100+MWSTOP))) from buchung
           where KNROP=:KNR
           AND (ONRSOLL=:ONR And ArtSoll>=60 And ArtSoll<=62)
           AND (ONRHABEN=:ONR And ArtHaben>=10  And ArtHaben<=18)
           and (Datum>=:DTVON and Datum<=:DTBIS)
           and (GN=:IGN or GN=71)
           into :TEMP_SUM, TEMP_UST;
           if (TEMP_SUM IS NULL) then
            TEMP_SUM=0;
           if (TEMP_UST IS NULL) then
            TEMP_UST=0;
           IF ((KLASSE>=110) and (KLASSE<=580)) THEN
            TEMP_UST=0; 
           SEIN=SEIN - TEMP_SUM;
           UST_E=UST_E-TEMP_UST;
           /* SPLIT */
           select sum(buchzahl.betrag), Sum(buchzahl.Betrag - ((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP))) from buchzahl, buchung
           where buchzahl.knr=:KNR
           and buchzahl.bnr=buchung.bnr
           and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
           and (buchung.onrsoll=:ONR and buchung.artsoll>=60 and buchung.artsoll<=62)
           and (GN=:IGN or GN=71)
           into :TEMP_SUM, :TEMP_UST;
           if (TEMP_SUM IS NULL) then
            TEMP_SUM=0;
           if (TEMP_UST IS NULL) then
            TEMP_UST=0;
           IF ((KLASSE>=110) and (KLASSE<=580)) THEN
            TEMP_UST=0; 
           SEIN=SEIN - TEMP_SUM;
           UST_E=UST_E-TEMP_UST;
          END
         /* K SPLIT Bank immer im Haben bei Kosten*/
         IF (KLASSE=1) THEN
          BEGIN
           select sum(bz.betrag),Sum(bz.Betrag - ((bz.BETRAG*100) / (100+bz.MWSTOP))) from buchzahl bz, buchung b1, buchung b2
           where bz.knr=:KNR 
           and bz.bnr=b1.bnr
           and (b1.datum>=:DTVON and b1.datum<=:DTBIS)
           and (b1.arthaben>=20 and b1.arthaben<=27)
           and (b1.GN=:IGN or b1.GN=71)
           and bz.OPNR=b2.bnr and (b2.ONRSOLL=:onr or b2.onrhaben=:onr)
           into :TEMP_SUM, :TEMP_UST;
           if (TEMP_SUM IS NULL) then
            TEMP_SUM=0;
           if (TEMP_UST IS NULL) then
            TEMP_UST=0;
           IF ((KLASSE>=110) and (KLASSE<=580)) THEN
            TEMP_UST=0; 
           SAUS=SAUS + TEMP_SUM;
           UST_A=UST_A+TEMP_UST;
          END
         else
          BEGIN
           select sum(buchzahl.betrag), Sum(buchzahl.Betrag - ((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP))) from buchzahl, buchung
           where buchzahl.knr=:KNR
           and buchzahl.bnr=buchung.bnr
           and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
           and (buchung.onrsoll=:ONR and buchung.artsoll>=20 and buchung.artsoll<=27)
           and (GN=:IGN or GN=71)
           into :TEMP_SUM, :TEMP_UST;
           if (TEMP_SUM IS NULL) then
            TEMP_SUM=0;
           if (TEMP_UST IS NULL) then
            TEMP_UST=0;
           IF ((KLASSE>=110) and (KLASSE<=580)) THEN
            TEMP_UST=0; 
           SEIN=SEIN + TEMP_SUM;
           UST_E=UST_E+TEMP_UST;
          END
         SALDO=SEIN-SAUS;
         SALDOGES_EK=SALDOGES_EK+SALDO;
        END
       ELSE
        BEGIN  /* W-DATUM */
         /* E/K im Soll auf A/P direkt gebucht */
         select Sum(Betrag), Sum(Betrag - ((BETRAG*100) / (100+MWST))) from buchung
         where (ONRSOLL=:ONR And KSOLL=:KNR)
         and ((ONRHABEN=:ONR OR ONRHABEN=0) And ((ARTHABEN>=20 And ArtHaben<=30) OR (ARTHABEN=1 OR ARTHABEN=19)))
         and (WDatum>=:DTVON and WDatum<=:DTBIS)
         and (GN=:IGN or GN=71)
         into :TEMP_SUM, TEMP_UST;
         if (TEMP_SUM IS NULL) then
          TEMP_SUM=0;
         if (TEMP_UST IS NULL) then
          TEMP_UST=0;
         IF ((KLASSE>=110) and (KLASSE<=580)) THEN
          TEMP_UST=0; 
         IF (KLASSE=1) THEN
          BEGIN
           SAUS=TEMP_SUM;
           UST_A=TEMP_UST;
          END
         ELSE
          BEGIN
           SEIN=-TEMP_SUM;
           UST_E=-TEMP_UST;
          END
         /* E/K im Haben direkt auf A/P gebucht*/
         select Sum(Betrag), Sum(Betrag - ((BETRAG*100) / (100+MWST))) from buchung
         where (ONRHABEN=:ONR And KHABEN=:KNR)
         and ((ONRSOLL=:ONR or ONRSOLL=0) And ((ARTSOLL>=20 And ArtSoll<=30) OR (ARTSOLL=1 OR ARTSOLL=19)))
         and (WDatum>=:DTVON and WDatum<=:DTBIS)
         and (GN=:IGN or GN=71)
         into :TEMP_SUM, TEMP_UST;
         if (TEMP_SUM IS NULL) then
          TEMP_SUM=0;
         if (TEMP_UST IS NULL) then
          TEMP_UST=0;
         IF ((KLASSE>=110) and (KLASSE<=580)) THEN
          TEMP_UST=0; 
         IF (KLASSE=1) THEN
          begin
           SAUS=SAUS-TEMP_SUM;
           UST_A=UST_A-TEMP_UST;
          end
         ELSE
          begin
           SEIN=SEIN+TEMP_SUM;
           UST_E=TEMP_UST;
          end
         /*A/P im SOll, DEB/KRED im Haben, kein SpLIT*/
         select Sum(Betrag), Sum(Betrag - ((BETRAG*100) / (100+MWSTOP))) from buchung
         where KNROP=:KNR
         AND
         (ONRSOLL=:ONR And ArtSoll>=20 And ArtSoll<=27)
         and (WDatum>=:DTVON and WDatum<=:DTBIS)
         and (GN=:IGN or GN=71)
         into :TEMP_SUM, TEMP_UST;
         if (TEMP_SUM IS NULL) then
          TEMP_SUM=0;
         if (TEMP_UST IS NULL) then
          TEMP_UST=0;
         IF ((KLASSE>=110) and (KLASSE<=580)) THEN
          TEMP_UST=0; 
         IF (KLASSE=1) THEN
          BEGIN
           SAUS=SAUS - TEMP_SUM;
           UST_A=UST_A-TEMP_UST;
          END
         ELSE
          BEGIN
           SEIN=SEIN + TEMP_SUM;
           UST_E=UST_E+TEMP_UST;
          END
         /*A/P im Haben, DEB/KRED im Soll, kein SPLIT*/
         select Sum(Betrag),Sum(Betrag - ((BETRAG*100) / (100+MWSTOP))) from buchung
         where KNROP=:KNR
         AND
         (ONRHABEN=:ONR And ArtHaben>=20 And ArtHaben<=27)
         and (WDatum>=:DTVON and WDatum<=:DTBIS)
         and (GN=:IGN or GN=71)
         into :TEMP_SUM, TEMP_UST;
         if (TEMP_SUM IS NULL) then
          TEMP_SUM=0;
         if (TEMP_UST IS NULL) then
          TEMP_UST=0;
         IF ((KLASSE>=110) and (KLASSE<=580)) THEN
          TEMP_UST=0; 
         IF (KLASSE=1) THEN
          BEGIN
           SAUS=SAUS + TEMP_SUM;
           UST_A=UST_A+TEMP_UST;
          END
         ELSE
          BEGIN
           SEIN=SEIN - TEMP_SUM;
           UST_E=UST_E-TEMP_UST;
          END
         /* Umwandlungen GN in geleistete BK*/
         IF (KLASSE>=10 AND KLASSE<=18) THEN
          BEGIN
           select Sum(Betrag),Sum(Betrag - ((BETRAG*100) / (100+MWSTOP))) from buchung
           where KNROP=:KNR
           AND (ONRSOLL=:ONR And ArtSoll>=60 And ArtSoll<=62)
           AND (ONRHABEN=:ONR And ArtHaben>=10  And ArtHaben<=18)
           and (WDatum>=:DTVON and WDatum<=:DTBIS)
           and (GN=:IGN or GN=71)
           into :TEMP_SUM, TEMP_UST;
           if (TEMP_SUM IS NULL) then
            TEMP_SUM=0;
           if (TEMP_UST IS NULL) then
            TEMP_UST=0;
           IF ((KLASSE>=110) and (KLASSE<=580)) THEN
            TEMP_UST=0; 
           SEIN=SEIN - TEMP_SUM;
           UST_E=UST_E-TEMP_UST;
           /* SPLIT */
           select sum(buchzahl.betrag), Sum(buchzahl.Betrag - ((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP))) from buchzahl, buchung
           where buchzahl.knr=:KNR
           and buchzahl.bnr=buchung.bnr
           and (buchung.wdatum>=:DTVON and buchung.wdatum<=:DTBIS)
           and (buchung.onrsoll=:ONR and buchung.artsoll>=60 and buchung.artsoll<=62)
           and (GN=:IGN or GN=71)
           into :TEMP_SUM, :TEMP_UST;
           if (TEMP_SUM IS NULL) then
            TEMP_SUM=0;
           if (TEMP_UST IS NULL) then
            TEMP_UST=0;
           IF ((KLASSE>=110) and (KLASSE<=580)) THEN
            TEMP_UST=0; 
           SEIN=SEIN - TEMP_SUM;
           UST_E=UST_E-TEMP_UST;
          END
         /* K SPLIT Bank immer im Haben bei Kosten*/
         IF (KLASSE=1) THEN
          BEGIN
           select sum(buchzahl.betrag),Sum(buchzahl.Betrag - ((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP))) from buchzahl, buchung
           where buchzahl.knr=:KNR
           and buchzahl.bnr=buchung.bnr
           and (buchung.wdatum>=:DTVON and buchung.wdatum<=:DTBIS)
           and (buchung.onrhaben=:ONR and buchung.arthaben>=20 and buchung.arthaben<=27)
           and (GN=:IGN or GN=71)
           into :TEMP_SUM, :TEMP_UST;
           if (TEMP_SUM IS NULL) then
            TEMP_SUM=0;
           if (TEMP_UST IS NULL) then
            TEMP_UST=0;
           IF ((KLASSE>=110) and (KLASSE<=580)) THEN
            TEMP_UST=0; 
           SAUS=SAUS + TEMP_SUM;
           UST_A=UST_A+TEMP_UST;
          END
         else
          BEGIN
           select sum(buchzahl.betrag), Sum(buchzahl.Betrag - ((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP))) from buchzahl, buchung
           where buchzahl.knr=:KNR
           and buchzahl.bnr=buchung.bnr
           and (buchung.wdatum>=:DTVON and buchung.wdatum<=:DTBIS)
           and (buchung.onrsoll=:ONR and buchung.artsoll>=20 and buchung.artsoll<=27)
           and (GN=:IGN or GN=71)
           into :TEMP_SUM, :TEMP_UST;
           if (TEMP_SUM IS NULL) then
            TEMP_SUM=0;
           if (TEMP_UST IS NULL) then
            TEMP_UST=0;
           IF ((KLASSE>=110) and (KLASSE<=580)) THEN
            TEMP_UST=0; 
           SEIN=SEIN + TEMP_SUM;
           UST_E=UST_E+TEMP_UST;
          END
         SALDO=SEIN-SAUS;
         SALDOGES_EK=SALDOGES_EK+SALDO;
        END /* W-Datum */
      END /* IST_BUCHHALTUNG */
     ELSE
      BEGIN  /* SOLL_BUCHHALTUNG */
       SEIN=0;
       SAUS=0;
       UST_E=0;
       UST_A=0;
       /* +K -E im Soll  */
       select Sum(Betrag), Sum(Betrag - ((BETRAG*100) / (100+MWST))) from buchung
       where (ONRSOLL=:ONR And KSOLL=:KNR)
       and ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
       and (GN=:IGN or GN=71)
       into :TEMP_SUM, :TEMP_UST;
       if (TEMP_SUM IS NULL) then
        TEMP_SUM=0;
       if (TEMP_UST IS NULL) then
        TEMP_UST=0;
       IF ((KLASSE>=110) and (KLASSE<=580)) THEN
        TEMP_UST=0; 
       IF (KLASSE=1) THEN
        begin
         SAUS=TEMP_SUM;
         UST_A=TEMP_UST;
        end
       ELSE
        begin
         SEIN=-TEMP_SUM;
         UST_E=-TEMP_UST;
        end
       /* - K im Haben +E im HAben */
       select Sum(Betrag), Sum(Betrag - ((BETRAG*100) / (100+MWST))) from buchung
       where (ONRHABEN=:ONR And KHABEN=:KNR)
       and ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM))
       and (GN=:IGN or GN=71)
       into :TEMP_SUM, :TEMP_UST;
       if (TEMP_SUM IS NULL) then
        TEMP_SUM=0;
       if (TEMP_UST IS NULL) then
        TEMP_UST=0;
       IF ((KLASSE>=110) and (KLASSE<=580)) THEN
        TEMP_UST=0; 
       IF (KLASSE=1) THEN
        BEGIN
         SAUS=SAUS-TEMP_SUM;
         UST_A=UST_A-TEMP_UST;
        END
       ELSE
        BEGIN
         SEIN=SEIN+TEMP_SUM;
         UST_E=UST_E+TEMP_UST;
        END
       SALDO=SEIN-SAUS;
       SALDOGES_EK=SALDOGES_EK+SALDO;
      END    /* SOLL_BUCHHALTUNG */
     AUS=0;
     KVERTEILUNG=0;
     IF ((KLASSE=1) OR (KLASSE=19)) THEN /* AUSGABEN */
      BEGIN
       IF (KLASSE=1) THEN
       AUS=1;
       IF (KKSTNR=3) THEN
        BEGIN
         IF (BHEIZ='N') THEN
          KVERTEILUNG=3; /* nicht umlagefaehig */
         ELSE          
          KVERTEILUNG=1; /* immer Bewohner */
        END
       ELSE
        BEGIN
         IF (IS_HAUSTYP=0) THEN
          KVERTEILUNG=1;  /* Bewohner*/
         ELSE
          IF (IS_HAUSTYP=1) THEN
           BEGIN
            IF (IS_KVERTEILUNG='J') THEN
             KVERTEILUNG=1;  /* Bewohner */
            ELSE
             KVERTEILUNG=2;  /* Eigentuemer */
           END
         ELSE
          BEGIN
           IF (IS_KBEW='J') THEN
            KVERTEILUNG=1;  /* Bewohner */
           ELSE
            KVERTEILUNG=2;  /* Eigentuemer */
          END
       END
      END
      
     IF (((IS_HAUSTYP = 2) AND (IS_ABR_HAUSTYP=1) AND (KLASSE >= 10) AND KLASSE <= 13) or 
         ((IS_HAUSTYP = 2) AND (IS_ABR_HAUSTYP=0) AND (KLASSE = 15 or KLASSE=18 or (KLASSE>=110 and KLASSE<=580)))) THEN
      SALDO = 0;     
      
     IF (SALDO<>0) THEN
      BEGIN
       IF (NOT (IS_GN='N' AND (KLASSE=13 OR KLASSE=18 OR IGN=1))) THEN
        begin
         IF (NOT (IS_MIETE_NO='J' AND KLASSE=10)) THEN
          BEGIN
           /* Anrechnbare UST */
           IF (KLASSE=1) THEN
            BEGIN
             IF (IMWSTART=2) THEN /* Laut Hausanteil */
              UST_AANRECH=UST_A * IPROZ_UST;
             ELSE
              IF (IMWSTART=0) THEN /* 0% */
               UST_AANRECH=0;
              ELSE
               UST_AANRECH=UST_A; /* 100% */
            END
           IF ((KLASSE<19 AND KLASSE<>1) or (KLASSE>=110 and KLASSE<=580)) THEN
            BEGIN
             IF (IST_BUCHHALTUNG='J') THEN
              begin
               KNRSTR='Debitoren';
              end
             ITMP = KLASSE;
             KLASSE=2; /* VZ */
            END
           IF (RLPOS IS NOT NULL) THEN
            AUS=3;
           /**/
           IF (IGN=1) THEN
            KNR=60190;
           SUSPEND;
           /* Beitragsverpflichtung als Ausgabe in die RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
           IF (ITMP>=110 and ITMP<=580) THEN
            BEGIN
             AUS = 3;
             KLASSE = 1;
             SKBEZ='Beitragsverpflichtung ' || KBEZ;
             KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
             SAUS = SEIN;
             SEIN=0;
             SALDO = SEIN - SAUS;
             SUSPEND;
             if (ITMP=110) THEN
              RUECKL1 = RUECKL1 + SAUS;
             if (ITMP=120) THEN
              RUECKL2 = RUECKL2 + SAUS;
             if (ITMP=130) THEN
              RUECKL3 = RUECKL3 + SAUS;
             if (ITMP=140) THEN
              RUECKL4 = RUECKL4 + SAUS;
             if (ITMP=150) THEN
              RUECKL5 = RUECKL5 + SAUS;
             if (ITMP=160) THEN
              RUECKL6 = RUECKL6 + SAUS;
             if (ITMP=580) THEN
              RUECKL7 = RUECKL7 + SAUS;
             ITMP=0;
            END           
           if (KNRSTR='Debitoren') THEN
            begin
             IF (IS_WDATUM='N') THEN
              BEGIN
               /* VERRECHNUNGEN SPLIT */
               select  sum(buchzahl.betrag), Sum(buchzahl.Betrag - ((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP))) from buchzahl, buchung
                where buchzahl.KNR=:KNR
                and buchung.opbetrag is null
                and buchzahl.bnr=buchung.bnr
                and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
                and (buchung.onrsoll=:ONR and buchung.artsoll>=60 and buchung.artsoll<=69)
               into :TEMP_SUM, :TEMP_UST;
               if (TEMP_SUM IS NULL) then
                TEMP_SUM=0;
               if (TEMP_UST IS NULL) then
                TEMP_UST=0;
               IF ((KLASSE>=110) and (KLASSE<=580)) THEN
                TEMP_UST=0; 
               SEIN=TEMP_SUM;
               UST_E=TEMP_UST;
               /* VERRECHNUNGEN KEIN SPLIT */
               select  sum(betrag), Sum(Betrag - ((BETRAG*100) / (100+MWSTOP))) from buchung
               where (khaben=:KNR)
               and opbetrag is null
               and (buchung.datum>=:DTVON and buchung.datum<=:DTBIS)
               and artop<>0
               and (onrsoll=:ONR and artsoll>=60 and artsoll<=69)
               into :TEMP_SUM, :TEMP_UST;
               if (TEMP_SUM IS NULL) then
                TEMP_SUM=0;
               if (TEMP_UST IS NULL) then
                TEMP_UST=0;
               IF ((KLASSE>=110) and (KLASSE<=580)) THEN
                TEMP_UST=0; 
               SEIN=SEIN+TEMP_SUM;
               UST_E=UST_E+TEMP_UST;
               SKBEZ=KBEZ || ' (Verrechnungen)';
               KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
               SALDO=SEIN;
               SALDOGES_EK=SALDOGES_EK+SALDO;
               if (SALDO<>0) then
                SUSPEND;
              END
             ELSE
              BEGIN
               /* VERRECHNUNGEN SPLIT */
               select  sum(buchzahl.betrag), Sum(buchzahl.Betrag - ((buchzahl.BETRAG*100) / (100+buchzahl.MWSTOP))) from buchzahl, buchung
                where buchzahl.KNR=:KNR
                and buchung.opbetrag is null
                and buchzahl.bnr=buchung.bnr
                and (buchung.wdatum>=:DTVON and buchung.wdatum<=:DTBIS)
                and (buchung.onrsoll=:ONR and buchung.artsoll>=60 and buchung.artsoll<=69)
               into :TEMP_SUM, :TEMP_UST;
               if (TEMP_SUM IS NULL) then
                TEMP_SUM=0;
               if (TEMP_UST IS NULL) then
                TEMP_UST=0;
               IF ((KLASSE>=110) and (KLASSE<=580)) THEN
                TEMP_UST=0; 
               SEIN=TEMP_SUM;
               UST_E=TEMP_UST;
               /* VERRECHNUNGEN KEIN SPLIT */
               select  sum(betrag), Sum(Betrag - ((BETRAG*100) / (100+MWSTOP))) from buchung
               where (khaben=:KNR)
               and opbetrag is null
               and (buchung.wdatum>=:DTVON and buchung.wdatum<=:DTBIS)
               and artop<>0
               and (onrsoll=:ONR and artsoll>=60 and artsoll<=69)
               into :TEMP_SUM, :TEMP_UST;
               if (TEMP_SUM IS NULL) then
                TEMP_SUM=0;
               if (TEMP_UST IS NULL) then
                TEMP_UST=0;
               IF ((KLASSE>=110) and (KLASSE<=580)) THEN
                TEMP_UST=0; 
               SEIN=SEIN+TEMP_SUM;
               UST_E=UST_E+TEMP_UST;
               SKBEZ=KBEZ || ' (Verrechnungen)';
               KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
               SALDO=SEIN;
               SALDOGES_EK=SALDOGES_EK+SALDO;
               if (SALDO<>0) then
                SUSPEND;
              END
            END
          END
        end
       else
        begin
         IF ((IS_GN='N') AND (KLASSE>=110 and KLASSE<=580)) THEN
          BEGIN
           SAUS = SEIN;
           SEIN=0;
           if (KLASSE=110) THEN
            RUECKL1 = RUECKL1 + SAUS;
           if (KLASSE=120) THEN
            RUECKL2 = RUECKL2 + SAUS;
           if (KLASSE=130) THEN
            RUECKL3 = RUECKL3 + SAUS;
           if (KLASSE=140) THEN
            RUECKL4 = RUECKL4 + SAUS;
           if (KLASSE=150) THEN
            RUECKL5 = RUECKL5 + SAUS;
           if (KLASSE=160) THEN
            RUECKL6 = RUECKL6 + SAUS;
           if (KLASSE=580) THEN
            RUECKL7 = RUECKL7 + SAUS;
           SAUS=0;
          END
        end  
      END
   END /* Alle E/K Konten */
  END /* ONR */ 
 /*   */
 /* BESTANDSKONTEN  */
 /*   */
 IF (IS_BANKEN='J') THEN
  BEGIN
   EA=2;
   KNRSTR='';
   UST_A=0;
   UST_AANRECH=0;
   UST_E=0;
   SALDO=0;
   KVERTEILUNG=1;
   KNR=NULL;
   KLASSE=20;
   AUS=0;
   ITMP=0;
   FOR 
    select distinct a.banknr, bew from objbanken a, banken b, konten c
    where (a.onr>=:VON_ONR and a.ONR<=:BIS_ONR) and a.banknr=b.nr
    and a.onr=c.onr and a.knr=c.knr
    order by bic, iban
   INTO
    :IBNR, :IMWSTART
   DO
    BEGIN
     select KURZBEZ, KURZBEZ || ', IBAN ' || IBAN from banken where NR=:IBNR
     INTO :KNRSTR, :SKBEZ;
     KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
     for select distinct onr from objbanken where banknr=:IBNR and (ONR>=:VON_ONR and ONR<=:BIS_ONR) into :ONR  do
      begin
       SALDO=SALDO;
      end
     EXECUTE PROCEDURE BANKSALDO_ALT(:IBNR, DTVON) RETURNING_VALUES :SAUS;
     EXECUTE PROCEDURE BANKSALDO_ALT(:IBNR, DTBISP1) RETURNING_VALUES :SEIN;
     IF (KBEZ IS NULL) THEN
      SELECt BEZEICHNUNG FROM BANKEN WHERE NR=:IBNR INTO :KBEZ;
     SALDO=SEIN-SAUS;
     SALDOGES_AP=SALDOGES_AP+SALDO;
     IF(SEIN<>0 OR SAUS<>0) THEN
      BEGIN
       IF (VON_ONR=BIS_ONR) THEN
        BEGIN
         select KNR from objbanken where banknr=:IBNR and ONR=:VON_ONR INTO :knr;
         IF (IS_ABR_HAUSTYP=0 and IS_HAUSTYP=2) then
          BEGIN /* Nur Mieter Banken */
           SELECT LEVBANKNR from objekte where ONR=:VON_ONR into LEVBANKNR;
           IF ((LEVBANKNR=IBNR) OR (IMWSTART = 1)) THEN
            SUSPEND;
          END
         ELSE
          IF (IS_ABR_HAUSTYP=1 and IS_HAUSTYP=2) then
           BEGIN /* Nur Eigentuemer Banken */
            SELECT LEVBANKNR2 from objekte where ONR=:VON_ONR into LEVBANKNR;
            IF ((LEVBANKNR=IBNR) OR (IMWSTART = 0)) THEN
             SUSPEND;
           END
          ELSE
           SUSPEND;
        END
       ELSE
        BEGIN
         IF (ITMP<>IBNR) THEN
          BEGIN 
           ITMP=IBNR;
           SUSPEND;
          END 
        END 
      END
    END
  /* 98000, 99990 */
  KVERTEILUNG=4;
  SELECT KNR, KNRSTR, KBEZ, KKLASSE from konten
  where ONR=0 AND KNR='98000'
  INTO :KNR, :KNRSTR, :SKBEZ, :KLASSE;
  KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
  FOR SELECT ONR from Objekte where (ONR>=:VON_ONR and ONR<=:BIS_ONR) order by onr into :ONR do
   begin
    SAUS=0;
    SEIN=0;
    SALDO=0;
    EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, '98000', :DTVON, 'J','N') RETURNING_VALUES :SAUS;
    EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, '98000', :DTBISP1, 'J','N') RETURNING_VALUES :SEIN;
    SALDO=SEIN-SAUS;
    SALDOGES_AP=SALDOGES_AP+SALDO;
    IF(SALDO<>0) THEN
     SUSPEND;
   end
  /* 99990 */
  SELECT KNR, KNRSTR, KBEZ, KKLASSE from konten
  where ONR=0 AND KNR='99990'
  INTO :KNR, :KNRSTR, :SKBEZ, :KLASSE;
  KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
  FOR SELECT ONR from Objekte where (ONR>=:VON_ONR and ONR<=:BIS_ONR) order by onr into :ONR do
   begin
    SAUS=0;
    SEIN=0;
    SALDO=0;
    EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, '99990', :DTVON, 'J','N') RETURNING_VALUES :SAUS;
    EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, '99990', :DTBISP1, 'J','N') RETURNING_VALUES :SEIN;
    SALDO=SEIN-SAUS;
    SALDOGES_AP=SALDOGES_AP+SALDO;
    IF(SALDO<>0) THEN
     SUSPEND;
   end
  /* RLA */
  KVERTEILUNG=2;
  FOR SELECT KNR, KNRSTR, KBEZ, KKLASSE, ONR from konten
   where (ONR>=:VON_ONR and ONR<=:BIS_ONR) AND KKLASSE=22
   INTO :KNR, :KNRSTR, :SKBEZ, :KLASSE, :ONR
   DO
    begin
     KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
     SAUS=0;
     SEIN=0;
     EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTVON, 'J','N') RETURNING_VALUES :SAUS;
     EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTBISP1, 'J','N') RETURNING_VALUES :SEIN;
     SALDO=SEIN-SAUS;
     SALDOGES_AP=SALDOGES_AP+SALDO;
     select iban from rueckbkt where ONR=:ONR and KNR=:KNR INTO :KONTONR;
     SKBEZ=KBEZ || ' ' || KONTONR || ' fuer Haus ' || ONR;
     KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
     IF(SEIN<>0 OR SAUS<>0) THEN
      SUSPEND;
    end
  /* RLP */
  KVERTEILUNG=3;
  AUS=1;
  FOR SELECT KNR, KNRSTR, KBEZ, KKLASSE, ONR, RLPOS from konten
   where (ONR>=:VON_ONR and ONR<=:BIS_ONR) AND (KKLASSE=27 AND RLPOS IS NOT NULL)
   INTO :KNR, :KNRSTR, :SKBEZ, :KLASSE, :ONR, :RLPOS
   DO
    begin
     KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
     SAUS=0;
     SEIN=0;
     EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTVON, 'J','N') RETURNING_VALUES :SAUS;
     EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTBISP1, 'J','N') RETURNING_VALUES :SEIN;
     SEIN=-SEIN;
     SAUS=-SAUS;
     select KONTO_VZ from rueckpos where NR=:RLPOS INTO ITMP;
     /* Beitragsverpflichtung in Saldo ALT aufnehmen */
     select sum(sum_vz) from VZ_BE_DETAIL (:ONR, '01.01.1950', (:DTVON - 1), 200000, 299999, 'N') where vzpos=(:ITMP-60000) into :RUECKLAB;
     if (RUECKLAB is null) then
      RUECKLAB = 0;
     RUECKLAB = -RUECKLAB;
     SAUS = SAUS + RUECKLAB;
     SEIN = SEIN + RUECKLAB; 
     /* Beitragsverpflichtung fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r diese Position */     
     IF (ITMP=60110) THEN
      SEIN=SEIN - RUECKL1;
     IF (ITMP=60120) THEN
      SEIN=SEIN - RUECKL2;
     IF (ITMP=60130) THEN
      SEIN=SEIN - RUECKL3;
     IF (ITMP=60140) THEN
      SEIN=SEIN - RUECKL4;
     IF (ITMP=60150) THEN
      SEIN=SEIN - RUECKL5;
     IF (ITMP=60160) THEN
      SEIN=SEIN - RUECKL6;
     IF (ITMP=60580) THEN
      SEIN=SEIN - RUECKL7;
     SALDO=SEIN-SAUS;
     SALDOGES_AP=SALDOGES_AP+SALDO;
     SKBEZ = KBEZ || ' inkl. Beitragsverpflichtungen EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer';
     KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
     IF(SEIN<>0 OR SAUS<>0) THEN
      SUSPEND;
    end
  /* die anderen A/P */
  KVERTEILUNG=4;
  FOR SELECT KNR, KNRSTR, KBEZ, KKLASSE, ONR from konten
   where (ONR>=:VON_ONR and ONR<=:BIS_ONR) AND ((KKLASSE=27 AND RLPOS IS NULL) OR KKLASSE=24)
   INTO :KNR, :KNRSTR, :SKBEZ, :KLASSE, :ONR
   DO
    begin
     KBEZ = SUBSTRING(SKBEZ FROM 1 FOR 88);
     select KTOUneinbringlich from objekte where ONR=:ONR into :KTOUNEINBRINGLICH;
     if (KTOUNEINBRINGLICH is null) then
      KTOUNEINBRINGLICH = 0;
     if (:KNR <> KTOUNEINBRINGLICH) then
      begin
       SAUS=0;
       SEIN=0;
       EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTVON, 'J','N') RETURNING_VALUES :SAUS;
       EXECUTE PROCEDURE KONTOSALDO_ALT (:ONR, :KNR, :DTBISP1, 'J','N') RETURNING_VALUES :SEIN;
       IF (KLASSE=27) THEN
        BEGIN
         SEIN=-SEIN;
         SAUS=-SAUS;
         AUS=1;
        END
       ELSE
        AUS=0;
       SALDO=SEIN-SAUS;
       SALDOGES_AP=SALDOGES_AP+SALDO;
       IF(SEIN<>0 OR SAUS<>0) THEN
        SUSPEND;
     end
    end
  END  /* IS_BANKEN */
END
