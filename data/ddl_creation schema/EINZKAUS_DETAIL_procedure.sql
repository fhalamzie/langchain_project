-- Prozedur: EINZKAUS_DETAIL
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE EINZKAUS_DETAIL
DECLARE VARIABLE BETRAG NUMERIC(15, 2);
DECLARE VARIABLE DTBDATUMVON DATE;
DECLARE VARIABLE DTBDATUMBIS DATE;
DECLARE VARIABLE DTWDATUMVON DATE;
DECLARE VARIABLE DTWDATUMBIS DATE;
DECLARE VARIABLE VZART INTEGER;
DECLARE VARIABLE IKSOLL INTEGER;
BEGIN
 /* TEMP 
 ONR = 998;
 KNR = 200100;
 DTVON = '1.10.2016';
 DTBIS = '31.12.2016';
 BWDATUM = 'N';  
 KEINESOLLSTELLUNGEN = 'N'; */
 
 /* Datum Variablen belegen */
 if (BWDATUM = 'N') then
  begin
   DTBDATUMVON = DTVON;
   DTBDATUMBIS = DTBIS;
   DTWDATUMVON = '01.01.1900';
   DTWDATUMBIS = '01.01.1900';
  end
 else
  begin
   DTWDATUMVON = DTVON;
   DTWDATUMBIS = DTBIS;
   DTBDATUMVON = '01.01.1900';
   DTBDATUMBIS = '01.01.1900';
  end
 /* 
 /* Berechnung 
 */
 IF (KEINESOLLSTELLUNGEN = 'N') THEN
  BEGIN
   /* Sollstellungen KHABEN = VZART  BNR = OPNR */
   for
    select OPNR, BETRAG, ARTHABEN from buchung
    where ((onrsoll=:onr) or (onrhaben=:onr)) and ((ksoll=:knr) or (khaben=:knr)) and ((DATUM>=:DTBDATUMVON and DATUM<=:DTBDATUMBIS) or (WDATUM>=:DTWDATUMVON and WDATUM<=:DTWDATUMBIS)) 
    and Betrag<>0 and opbetrag is not null
   into :BNR, :BETRAG, :VZART
   DO
    begin
     BETRAG = -BETRAG;
     MIETE = 0; BK = 0; HK = 0; GN = 0; 
     IF (VZART=10 OR VZART=15) THEN
      MIETE = MIETE + BETRAG;
     ELSE
      IF (VZART=11 OR VZART>=110) THEN
       BK = BK + BETRAG;
      ELSE
       IF (VZART=12 OR VZART=17) THEN
        HK = HK + BETRAG;
       ELSE
        IF (VZART=13 OR VZART=18) THEN
         GN = GN + BETRAG;
     SUSPEND;
    end
  END  
 /* ZAHLUNGEN SPLIT */    
 for
  select buchung.BNR, buchung.ksoll, buchzahl.BETRAG, buchzahl.artop from buchung,buchzahl
  where (buchzahl.bnr=buchung.bnr) and ((onrsoll=:ONR) or (onrhaben=:ONR)) and ((ksoll=:KNR) or (khaben=:KNR)) and ((DATUM>=:DTBDATUMVON and DATUM<=:DTBDATUMBIS) or (WDATUM>=:DTWDATUMVON and WDATUM<=:DTWDATUMBIS)) and buchzahl.Betrag<>0
 into :BNR, :IKSOLL, :BETRAG, :VZART
 DO
  begin
   MIETE = 0; BK = 0; HK = 0; GN = 0; 
   if (IKSOLL = KNR) then
    BETRAG = -BETRAG;
   IF (VZART=10 OR VZART=15) THEN
    MIETE = MIETE + BETRAG;
   ELSE
    IF (VZART=11 OR VZART>=110) THEN
     BK = BK + BETRAG;
    ELSE
     IF (VZART=12 OR VZART=17) THEN
      HK = HK + BETRAG;
     ELSE
      IF (VZART=13 OR VZART=18) THEN
       GN = GN + BETRAG;
   SUSPEND;
  end    
 /* ZAHLUNGEN KEIN SPLIT */    
 for select BNR, KSOLL, BETRAG, artop from buchung
  where ((onrsoll=:onr) or (onrhaben=:onr)) and ((ksoll=:knr) or (khaben=:knr)) and ((DATUM>=:DTBDATUMVON and DATUM<=:DTBDATUMBIS) or (WDATUM>=:DTWDATUMVON and WDATUM<=:DTWDATUMBIS)) and Betrag<>0 and opbetrag is null and splitnr is null and artop is not null and artop<>0 
 into :BNR, :IKSOLL, :BETRAG, :VZART
 DO
  begin
   MIETE = 0; BK = 0; HK = 0; GN = 0; 
   if (IKSOLL = KNR) then
    BETRAG = -BETRAG;
   IF (VZART=10 OR VZART=15) THEN
    MIETE = MIETE + BETRAG;
   ELSE
    IF (VZART=11 OR VZART>=110) THEN
     BK = BK + BETRAG;
    ELSE
     IF (VZART=12 OR VZART=17) THEN
      HK = HK + BETRAG;
     ELSE
      IF (VZART=13 OR VZART=18) THEN
       GN = GN + BETRAG;
   SUSPEND;
  end    
END
