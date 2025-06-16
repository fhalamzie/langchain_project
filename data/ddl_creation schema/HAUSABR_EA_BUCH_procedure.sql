-- Prozedur: HAUSABR_EA_BUCH
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE HAUSABR_EA_BUCH
DECLARE VARIABLE TEMP_SUM NUMERIC(15, 2);
DECLARE VARIABLE IGN INTEGER;
DECLARE VARIABLE STR_LEN INTEGER;
DECLARE VARIABLE VERR CHAR(1);
DECLARE VARIABLE STR_TEXT VARCHAR(15);
DECLARE VARIABLE MWST2 NUMERIC(15, 2);
DECLARE VARIABLE DTVONBDATUM DATE;
DECLARE VARIABLE DTBISBDATUM DATE;
DECLARE VARIABLE DTVONWDATUM DATE;
DECLARE VARIABLE DTBISWDATUM DATE;
BEGIN
 TEMP_SUM = 0;
 IGN=0;
 VERR = 'N';
 STR_LEN = CHAR_LENGTH(:KBEZ);
 IF (STR_LEN > 15) THEN
  BEGIN
   STR_TEXT = SUBSTRING (:KBEZ FROM (STR_LEN-13) FOR 14);
   IF (STR_TEXT = ' (Verrechnung)') THEN
    VERR = 'J';
  END
 /* W_Datum abfragen */
 if (WDATUM = 'N') then
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
 /* */
 IF (BSOLL = 'N') THEN
  BEGIN
   IF (KNR=60190) THEN
    IGN=1;
   if (VERR = 'N') then
    begin
     for  
      select BNR, KHABEN, DATUM, BELEGNR, TEXT, BETRAG, MWST, MWSTOP from buchung
      where (ONRSOLL=:ONR And KSOLL=:KNR) and ((ONRHABEN=:ONR OR ONRHABEN=0) And ((ARTHABEN>=20 And ArtHaben<=30) OR (ARTHABEN=1 OR ARTHABEN=19))) and ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM)) and (GN=:IGN or GN=71) and betrag<>0
     into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST, :MWST2  
     do
      begin
       IF (KLASSE=1) THEN
        BEGIN
         TEMP_SUM = TEMP_SUM + BETRAG;  
        END
       ELSE
        BEGIN
         TEMP_SUM = TEMP_SUM - BETRAG;
         IF (MWST2 is null) then
          MWST2 = 0;
         IF ((MWST2 > 0) AND (MWST = 0)) THEN
          MWST = MWST2;    
        END  
       SUSPEND;  
      end
     /* E/K im Haben direkt auf A/P gebucht*/
     for
      select BNR, KSOLL, DATUM, BELEGNR, TEXT, BETRAG, MWST, MWSTOP from buchung
      where (ONRHABEN=:ONR And KHABEN=:KNR) and ((ONRSOLL=:ONR or ONRSOLL=0) And ((ARTSOLL>=20 And ArtSoll<=30) OR (ARTSOLL=1 OR ARTSOLL=19))) and ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM)) and (GN=:IGN or GN=71) and betrag<>0
     into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST, :MWST2
     do
      begin
       IF (KLASSE=1) THEN
        BEGIN
         TEMP_SUM = TEMP_SUM - BETRAG;  
        END
       ELSE
        BEGIN
         TEMP_SUM = TEMP_SUM + BETRAG;
         IF (MWST2 is null) then
          MWST2 = 0;
         IF ((MWST2 > 0) AND (MWST = 0)) THEN
          MWST = MWST2;         
        END  
       SUSPEND;
      end
     /*A/P im SOll, DEB/KRED im Haben, kein SpLIT*/  
     for
      select BNR, KSOLL, DATUM, BELEGNR, TEXT, BETRAG, MWST, MWSTOP from buchung
      where KNROP=:KNR AND (ONRSOLL=:ONR And ArtSoll>=20 And ArtSoll<=27) and ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM)) and (GN=:IGN or GN=71) and betrag<>0
     into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST, :MWST2
     do
      begin
       IF (KLASSE=1) THEN
        BEGIN
         TEMP_SUM = TEMP_SUM - BETRAG;  
        END
       ELSE
        BEGIN
         TEMP_SUM = TEMP_SUM + BETRAG;
         IF (MWST2 is null) then
          MWST2 = 0;
         IF ((MWST2 > 0) AND (MWST = 0)) THEN
          MWST = MWST2;         
        END  
       SUSPEND;
      end
     /*A/P im Haben, DEB/KRED im Soll, kein SPLIT*/
     for
      select BNR, KHABEN, DATUM, BELEGNR, TEXT, BETRAG, MWST, MWSTOP from buchung 
      where KNROP=:KNR and (GN=:IGN or GN=71) AND (ONRHABEN=:ONR And ArtHaben>=20 And ArtHaben<=27) and ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM)) and betrag<>0
     into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST, :MWST2
     do
      begin
       IF (KLASSE=1) THEN
        BEGIN
         TEMP_SUM = TEMP_SUM + BETRAG;  
        END
       ELSE
        BEGIN
         TEMP_SUM = TEMP_SUM - BETRAG;  
         IF (MWST2 is null) then
          MWST2 = 0;
         IF ((MWST2 > 0) AND (MWST = 0)) THEN
          MWST = MWST2;       
        END  
       SUSPEND;
      end
     /* Umwandlungen G/N in geleistete BK*/
     IF (KLASSE>=10 AND KLASSE<=18) THEN
      BEGIN
       /* KEIN SPLIT */
       for
        select BNR, KHABEN, DATUM, BELEGNR, TEXT, BETRAG, MWST, MWSTOP from buchung
        where KNROP=:KNR AND (ONRSOLL=:ONR And ArtSoll>=60 And ArtSoll<=62) AND (ONRHABEN=:ONR And ArtHaben>=10  And ArtHaben<=18) and ((Datum >= :DTVONBDATUM and Datum <= :DTBISBDATUM) or (WDatum >= :DTVONWDATUM and WDatum <= :DTBISWDATUM)) and (GN=:IGN or GN=71) and betrag<>0
       into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST, :MWST2
       do
        begin
         TEMP_SUM = TEMP_SUM - BETRAG;
         IF (MWST2 is null) then
          MWST2 = 0;
         IF ((MWST2 > 0) AND (MWST = 0)) THEN
          MWST = MWST2;         
         SUSPEND;
        end
       /* SPLIT */
       for
        select buchung.BNR, KHABEN, DATUM, BELEGNR, TEXT, buchzahl.BETRAG,buchzahl. MWSTOP from buchzahl, buchung 
        where buchzahl.knr=:KNR and buchzahl.bnr=buchung.bnr and ((buchung.Datum >= :DTVONBDATUM and buchung.Datum <= :DTBISBDATUM) or (buchung.WDatum >= :DTVONWDATUM and buchung.WDatum <= :DTBISWDATUM)) and (buchung.onrsoll=:ONR and buchung.artsoll>=60 and buchung.artsoll<=62) and (GN=:IGN or GN=71) and buchzahl.betrag<>0
       into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST
       do
        begin
         TEMP_SUM = TEMP_SUM - BETRAG;  
         SUSPEND;
        end
      END  
     /* K SPLIT Bank immer im Haben bei Kosten*/
     IF (KLASSE=1) THEN
      BEGIN
       for
        select buchung.BNR, KHABEN, DATUM, BELEGNR, TEXT, buchzahl.BETRAG, buchzahl.MWSTOP from buchzahl, buchung
        where buchzahl.knr=:KNR and buchzahl.bnr=buchung.bnr and ((buchung.Datum >= :DTVONBDATUM and buchung.Datum <= :DTBISBDATUM) or (buchung.WDatum >= :DTVONWDATUM and buchung.WDatum <= :DTBISWDATUM)) and (buchung.onrhaben=:ONR and buchung.arthaben>=20 and buchung.arthaben<=27) and (GN=:IGN or GN=71) and buchzahl.betrag<>0
       into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST
       do
        begin
         TEMP_SUM = TEMP_SUM + BETRAG;  
         SUSPEND;
        end
      END
     else
      BEGIN
       for
        select buchung.BNR, KSOLL, DATUM, BELEGNR, TEXT, buchzahl.BETRAG, buchzahl.MWSTOP from buchzahl, buchung
        where buchzahl.knr=:KNR and buchzahl.bnr=buchung.bnr and ((buchung.Datum >= :DTVONBDATUM and buchung.Datum <= :DTBISBDATUM) or (buchung.WDatum >= :DTVONWDATUM and buchung.WDatum <= :DTBISWDATUM)) and (buchung.onrsoll=:ONR and buchung.artsoll>=20 and buchung.artsoll<=27) and (GN=:IGN or GN=71) and buchzahl.betrag<>0
       into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST
       do
        begin
         TEMP_SUM = TEMP_SUM + BETRAG;  
         SUSPEND;
        end
      END
    end
   else
    begin
     /* VERRECHNUNGEN SPLIT */
     for
      select buchung.BNR, KSOLL, DATUM, BELEGNR, TEXT, buchzahl.BETRAG, buchzahl.MWSTOP from buchzahl, buchung
      where buchzahl.KNR=:KNR and buchung.opbetrag is null and buchzahl.bnr=buchung.bnr and ((buchung.Datum >= :DTVONBDATUM and buchung.Datum <= :DTBISBDATUM) or (buchung.WDatum >= :DTVONWDATUM and buchung.WDatum <= :DTBISWDATUM)) and (buchung.onrsoll=:ONR and buchung.artsoll>=60 and buchung.artsoll<=69) and buchzahl.betrag<>0 
     into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST
     do
      begin
       TEMP_SUM = TEMP_SUM + BETRAG;  
       SUSPEND;
      end
     /* VERRECHNUNGEN KEIN SPLIT */
     for
      select BNR, KSOLL, DATUM, BELEGNR, TEXT, BETRAG, MWST from buchung
      where (khaben=:KNR) and opbetrag is null and ((buchung.Datum >= :DTVONBDATUM and buchung.Datum <= :DTBISBDATUM) or (buchung.WDatum >= :DTVONWDATUM and buchung.WDatum <= :DTBISWDATUM)) and artop<>0 and (onrsoll=:ONR and artsoll>=60 and artsoll<=69) and betrag<>0
     into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST
     do
      begin
       TEMP_SUM = TEMP_SUM + BETRAG;  
       SUSPEND;
      end
    end  
  end
 else
  begin
   for  
    select BNR, GKONTO, DATUM, BELEGNR, TEXT, BETRAG, MWST from KONTOAUSZUG(:ONR, :KNR, :DTVON, :DTBIS, 'J', :WDATUM) order by DATUM, GKONTO
    into :BNR, :IKNR, :DATUM, :BELEGNR, :TEXT, :BETRAG, :MWST
   do
    begin
     TEMP_SUM = TEMP_SUM + BETRAG;
     SUSPEND;  
    end  
  end  
 /* Summe */
 IF (TEMP_SUM<>0) THEN
  BEGIN
   BNR = 0;
   IKNR = 0;
   DATUM = '31.12.2999';
   BELEGNR = 0;
   TEXT = 'SALDO';
   BETRAG = TEMP_SUM;
   SUSPEND;
  END
END
