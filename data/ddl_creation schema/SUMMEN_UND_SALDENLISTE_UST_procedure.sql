-- Prozedur: SUMMEN_UND_SALDENLISTE_UST
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE SUMMEN_UND_SALDENLISTE_UST
DECLARE VARIABLE IONR_ INTEGER;
BEGIN
 IF (KKLASSE_VON=71 OR KKLASSE_VON=30) THEN
  IONR_=0;
 ELSE
  IONR_=IONR; 
  IF (KKLASSE_VON = 1) THEN
   BEGIN
    KNR=1576;
    KBEZ='Abziehbare Vorsteuer';
   END
  ELSE
   BEGIN
    KNR=1776;
    KBEZ='Umsatzsteuer';
   END 
/* FOR SELECT KNR, KBEZ from KONTEN where (KKLASSE>=:KKLASSE_VON and KKLASSE<=:KKLASSE_BIS) and ONR=:IONR_ order by KNR into :KNR, :KBEZ do */
    begin
     IF (:IEBWERTSACHKONTEN=1) THEN  /* auch EB-Wert UST bei Sachkonten */
      BEGIN
       select SUM(BETRAG) -  SUM((Betrag*100) / (100+MWST)) from buchung where (ONRSOLL=:IONR_ AND (ONRHABEN=:IONR or ONRHABEN=0)) and (ARTSOLL>=:KKLASSE_VON and ARTSOLL<=:KKLASSE_BIS) and (DATUM<:DTEBWERT) AND (MWST<>0) into :SALDO_S;    
       IF (SALDO_S IS NULL) then
        SALDO_S = 0;
       select SUM(BETRAG) -  SUM((Betrag*100) / (100+MWST)) from buchung where (ONRHABEN=:IONR_ AND (ONRSOLL=:IONR or ONRSOLL=0)) and (ARTHABEN>=:KKLASSE_VON and ARTHABEN<=:KKLASSE_BIS) and (DATUM<:DTEBWERT) AND (MWST<>0) into :SALDO_H;    
       IF (SALDO_H IS NULL) then
        SALDO_H = 0;
       /* wenn negativ dann S/H tauschen, weil es in der doppleten kein - gibt */
       IF (SALDO_S < 0) then
        begin
         SALDO_H = SALDO_H + ABS(SALDO_S);
         SALDO_S = 0;
        end 
       IF (SALDO_H < 0) then
        begin
         SALDO_S = SALDO_S + ABS(SALDO_H);
         SALDO_H = 0;
        end 
       EBWERT_S = SALDO_S;
       EBWERT_H = SALDO_H;
       EBWERT = EBWERT_S - EBWERT_H;
       IF (SOLL_PLUS='J') THEN
        BEGIN 
         EBWERT = SALDO_S - SALDO_H;
         IF (EBWERT>=0) THEN
          BEGIN
           EBWERT_SH='S';
          END 
         ELSE
          BEGIN
           EBWERT_SH='H';
           EBWERT = - EBWERT;      
          END 
        END
       ELSE
        BEGIN
         EBWERT = SALDO_H - SALDO_S;
         IF (EBWERT>=0) THEN
          BEGIN
           EBWERT_SH='H';
          END 
         ELSE
          BEGIN
           EBWERT_SH='S';
           EBWERT = - EBWERT;      
          END 
        END   
      END
     ELSE
      BEGIN
       EBWERT_SH='S';
       EBWERT = 0;
      END  
       

     select SUM(BETRAG) - SUM((Betrag*100) / (100+MWST)) from buchung where (ONRSOLL=:IONR_ AND (ONRHABEN=:IONR or ONRHABEN=0)) and (ARTSOLL>=:KKLASSE_VON and ARTSOLL<=:KKLASSE_BIS) and (DATUM>=:DTVON and DATUM<=:DTBIS) AND (MWST<>0) into :SALDO_S;

     IF (SALDO_S IS NULL) then
      SALDO_S = 0;
     select SUM(BETRAG) -  SUM((Betrag*100) / (100+MWST)) from buchung where (ONRHABEN=:IONR_ AND (ONRSOLL=:IONR or ONRSOLL=0)) and (ARTHABEN>=:KKLASSE_VON and ARTHABEN<=:KKLASSE_BIS) and (DATUM>=:DTVON and DATUM<=:DTBIS) AND (MWST<>0) into :SALDO_H;     
     IF (SALDO_H IS NULL) then
      SALDO_H = 0;  
     /* wenn negativ dann S/H tauschen, weil es in der doppleten kein - gibt */
     IF (SALDO_S < 0) then
      begin
       SALDO_H = SALDO_H + ABS(SALDO_S);
       SALDo_S = 0;
      end 
     IF (SALDO_H < 0) then
      begin
       SALDO_S = SALDO_S + ABS(SALDO_H);
       SALDo_H = 0;
      end 
    select SUM(BETRAG) -  SUM((Betrag*100) / (100+MWST)) from buchung where (ONRSOLL=:IONR_ AND (ONRHABEN=:IONR or ONRHABEN=0)) and (ARTSOLL>=:KKLASSE_VON and ARTSOLL<=:KKLASSE_BIS) and (DATUM>=:DTEBWERT and DATUM<=:DTBIS) AND (MWST<>0) into :SALDO_KUM_S;     
     IF (SALDO_KUM_S IS NULL) then
      SALDO_KUM_S = 0;
     select SUM(BETRAG) -  SUM((Betrag*100) / (100+MWST)) from buchung where (ONRHABEN=:IONR_ AND (ONRSOLL=:IONR or ONRSOLL=0)) and (ARTHABEN>=:KKLASSE_VON and ARTHABEN<=:KKLASSE_BIS) and (DATUM>=:DTEBWERT and DATUM<=:DTBIS) AND (MWST<>0) into :SALDO_KUM_H;          
     IF (SALDO_KUM_H IS NULL) then
      SALDO_KUM_H = 0;
 /* wenn negativ dann S/H tauschen, weil es in der doppleten kein - gibt */
     IF (SALDO_KUM_S < 0) then
      begin
       SALDO_KUM_H = SALDO_KUM_H + ABS(SALDO_KUM_S);
       SALDO_KUM_S = 0;
      end 
     IF (SALDO_KUM_H < 0) then
      begin
       SALDO_KUM_S = SALDO_KUM_S + ABS(SALDO_KUM_H);
       SALDO_KUM_H = 0;
      end       
      
      
     IF (SOLL_PLUS='J') THEN
      BEGIN 
       IF (EBWERT_SH='S') THEN
        SALDO = SALDO_KUM_S - SALDO_KUM_H + EBWERT;
       ELSE
        SALDO = SALDO_KUM_S - SALDO_KUM_H - EBWERT;
       IF (SALDO>=0) THEN
        BEGIN
         SALDO_SH='S';
        END 
       ELSE
        BEGIN
         SALDO_SH='H';
         SALDO = - SALDO;      
        END 
      END
     ELSE
      BEGIN
       IF (EBWERT_SH='H') THEN
        SALDO = SALDO_KUM_H - SALDO_KUM_S + EBWERT;
       ELSE
        SALDO = SALDO_KUM_H - SALDO_KUM_S - EBWERT;
       IF (SALDO>=0) THEN
        BEGIN
         SALDO_SH='H';
        END 
       ELSE
        BEGIN
         SALDO_SH='S';
         SALDO = - SALDO;      
        END 
      END  
     IF (NOT (EBWERT=0 AND SALDO_S =0 AND SALDO_H = 0 AND SALDO_KUM_S = 0 AND SALDO_KUM_H = 0 AND SALDO = 0)) THEN
      BEGIN
       SUSPEND;
      END 
    end
end
