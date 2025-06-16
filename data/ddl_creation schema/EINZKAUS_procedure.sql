-- Prozedur: EINZKAUS
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE EINZKAUS
DECLARE VARIABLE VZART INTEGER;
DECLARE VARIABLE LBNR INTEGER;
DECLARE VARIABLE OPBETRAG NUMERIC(18, 2);
DECLARE VARIABLE WDATUM DATE;
BEGIN
 for select SUM(MIETE),SUM(BK),SUM(HK),SUM(GN), BNR from EINZKAUS_DETAIL(:ONR,:KNR,:DTVON,:DTBIS,:BWDATUM,:KEINESOLLSTELLUNGEN)
 GROUP BY BNR 
 into :MIETE, :BK, :HK, :GN, :BNR 
 do
  begin
   SALDO = MIETE + BK + HK + GN;
   select a.DATUM, a.WDATUM, a.TEXT, (b.MWST / 100), a.BELEGNR, a.GN, a.OPBETRAG, a.LBNR from buchung a, buchung b where a.BNR=:BNR and a.opnr=b.bnr  
   INTO :DATUM, :WDATUM, :TEXT, :UST, :BELEGNR, :ISGN, :OPBETRAG, :LBNR;
   if (BWDATUM = 'J') then
    BEGIN
     DATUM2 = DATUM;
     DATUM = WDATUM;
    END 
   ELSE
    DATUM2 = WDATUM; 
   IF (OPBETRAG IS NOT NULL) THEN
    BEGIN
     if (OPBETRAG = 0) then
      begin
       BEMERKUNG='SO';
       ISOP = 1;
      end
     else
      begin
       BEMERKUNG='OP';
       ISOP = 2;
      end
    END
   ELSE
    BEGIN
     ISOP =0; 
     if (LBNR IS NOT NULL) then
      BEMERKUNG='LEV';
     ELSE
      BEMERKUNG='';     
    END 
   /**/
   IF (UST=0 OR UST IS NULL) THEN  /* NETTOMIETE */
    USTBETRAG = MIETE;
   ELSE
    USTBETRAG = (MIETE - (MIETE / (1 + UST))); 
   
   IF (GN IS NULL) THEN
    GN=0;  
   SUSPEND;
  end
END
