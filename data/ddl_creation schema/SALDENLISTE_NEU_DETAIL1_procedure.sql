-- Prozedur: SALDENLISTE_NEU_DETAIL1
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE SALDENLISTE_NEU_DETAIL1
BEGIN


  /* TEMP 
 IONR=7;
 DTVON = '1.1.2018';
 DTBIS = '31.12.2018';
 VONKTO = 200200;
 BISKTO = 200200;
 WDATUM = 'N';
 BMITVORTRAG = 'J';
 BMITGN = 'J';  */


 IF (BMITGN='N') THEN /* NUR GN=0 */
  BEGIN
   for select SUM(SUM_VZ), SUM(SUM_VZ_NETTO), 
              SUM(SUM_VZ_SOLL), SUM(SUM_VZ_NETTO_SOLL),  
              KNR, VZPOS, GN  
    from SALDENLISTE_NEU_DETAIL2(:IONR,:DTVON,:DTBIS,:VONKTO,:BISKTO, :WDATUM) 
    group by KNR, VZPOS, GN
    having GN=0
    into SUM_VZ, SUM_VZ_NETTO, SUM_VZ_SOLL, SUM_VZ_NETTO_SOLL, KNR, VZPOS, GN 
    DO
     SUSPEND;
   END
  ELSE
   BEGIN
    for select SUM(SUM_VZ), SUM(SUM_VZ_NETTO), 
         SUM(SUM_VZ_SOLL), SUM(SUM_VZ_NETTO_SOLL), 
         KNR, VZPOS, GN  
     from SALDENLISTE_NEU_DETAIL2(:IONR,:DTVON,:DTBIS,:VONKTO,:BISKTO,:WDATUM) 
     group by KNR, VZPOS, GN
     into SUM_VZ, SUM_VZ_NETTO, SUM_VZ_SOLL, SUM_VZ_NETTO_SOLL, KNR, VZPOS, GN 
      DO
       begin
        SUM_VZ_VORTRAG = 0;
        SUM_VZ_NETTO_VORTRAG = 0;          
        SUM_VZ_VORTRAG_SOLL = 0;
        SUM_VZ_NETTO_VORTRAG_SOLL = 0; 
        SUSPEND;
       end 
   END   
 IF (BMITVORTRAG = 'J') THEN
  BEGIN  
   DTBIS=DTVON -1; /* ein tag vor beginn */
   DTVON='01.01.0001';
   IF (BMITGN='N') THEN /* NUR GN=0 */
    BEGIN
     for select SUM(SUM_VZ), SUM(SUM_VZ_NETTO), 
         SUM(SUM_VZ_SOLL), SUM(SUM_VZ_NETTO_SOLL),
         KNR, VZPOS, GN  
      from SALDENLISTE_NEU_DETAIL2(:IONR,:DTVON,:DTBIS,:VONKTO,:BISKTO,:WDATUM) 
      group by KNR, VZPOS, GN
      having GN=0
      into SUM_VZ_VORTRAG, SUM_VZ_NETTO_VORTRAG, 
      SUM_VZ_VORTRAG_SOLL, SUM_VZ_NETTO_VORTRAG_SOLL, KNR, VZPOS, GN 
      DO
       begin
        /* Vortrag wird geliefert, andere Werte =0 */
        SUM_VZ = 0;
        SUM_VZ_NETTO = 0;         
        SUM_VZ_SOLL = 0;
        SUM_VZ_NETTO_SOLL = 0;  
        SUSPEND;
       end 
     END
    ELSE
     BEGIN
      for select SUM(SUM_VZ), SUM(SUM_VZ_NETTO), 
          SUM(SUM_VZ_SOLL), SUM(SUM_VZ_NETTO_SOLL),
          KNR, VZPOS, GN  
       from SALDENLISTE_NEU_DETAIL2(:IONR,:DTVON,:DTBIS,:VONKTO,:BISKTO,:WDATUM) 
       group by KNR, VZPOS, GN
       into SUM_VZ_VORTRAG, SUM_VZ_NETTO_VORTRAG, SUM_VZ_VORTRAG_SOLL, SUM_VZ_NETTO_VORTRAG_SOLL, KNR, VZPOS, GN 
        DO
         begin
          /* Vortrag wird geliefert, andere Werte =0 */
          SUM_VZ = 0;
          SUM_VZ_NETTO = 0;  
          SUM_VZ_SOLL = 0;
          SUM_VZ_NETTO_SOLL = 0;  
          SUSPEND;
         end 
     END      
   END /* BMITVORTRAG */  
   
END
