-- Prozedur: WEG_SAMMELLIST
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE WEG_SAMMELLIST
DECLARE VARIABLE BKANT NUMERIC(15, 2);
DECLARE VARIABLE HKANT NUMERIC(15, 2);
DECLARE VARIABLE BKVZ NUMERIC(15, 2);
DECLARE VARIABLE HKVZ NUMERIC(15, 2);
DECLARE VARIABLE BKERG NUMERIC(15, 2);
DECLARE VARIABLE HKERG NUMERIC(15, 2);
DECLARE VARIABLE RTMP NUMERIC(15, 2);
DECLARE VARIABLE ART INTEGER;
BEGIN
 IF (IART=1) THEN  /* WEG-Abrechnung reines WEG-HAUS */
  BEGIN
   FOR SELECT ONR, KNR, KNRSTR, KBEZ, HAUSGVZ, IHRABRVON, IHRABRBIS, WEG_ZUF_GES_SOLL, ENTRL_ANTEIL, SONUML_ANTEIL 
   FROM NKMASTER
   WHERE ONR = :IONR
   ORDER BY KNR
   INTO :ONR, :KNR, :KNRSTR, :KBEZ, :VZ, :DTVON, :DTBIS, :WEG_ZUF_GES_SOLL, :ENTRL_ANTEIL, :SONUML_ANTEIL
   DO
    BEGIN
     KOST_UML = 0;
     KOST_NUML = 0;
     KOST_EIN = 0;
     KOST_GES = 0;
     ERG = 0;
     /*  */
     select -kanteil from nkdetail where onr=:onr and knr=:knr and ear=4 and kklasse is null and haupt_nr=1 and kgesamt<0 and kname='Entnahmen' INTO :ENTRL_ANTEIL;
     /* */     
     IF (WEG_ZUF_GES_SOLL IS NULL) THEN
      WEG_ZUF_GES_SOLL = 0;
     IF (ENTRL_ANTEIL IS NULL) THEN
      ENTRL_ANTEIL = 0;
     IF (SONUML_ANTEIL IS NULL) THEN
      SONUML_ANTEIL = 0;
     IF (VZ IS NULL) THEN
      VZ = 0;      
     /*  */     
     FOR
      select sum(kbruttoanteil) as BETRAG, 1 as ART from NKDETAIL where ONR = :IONR and KNR=:KNR and haupt_nr=1 and ((abrnr=1 and ear=1) or (abrnr=4 and ear=4 and kklasse is not null)) /* numl Ausgaben */
      union all
      select sum(kbruttoanteil) as BETRAG, 2 as ART from NKDETAIL where ONR = :IONR and KNR=:KNR and haupt_nr=1 and abrnr=2 and ear=1 /* uml  Ausgaben */
      union all
      select sum(kbruttoanteil) as BETRAG, 3 as ART from NKDETAIL where ONR = :IONR and KNR=:KNR and haupt_nr=1 and ear=3 /*  s. Einnahmen */
     into :RTMP, :ART
     do
      begin
       if (RTMP IS NULL) then
        RTMP = 0;
       if (:ART = 1) then
        KOST_NUML = RTMP;
       else
        begin
         if (:ART= 2) then
          KOST_UML = RTMP;
         else
          begin
           if (:ART = 3) then
            KOST_EIN = - RTMP;
          end
        end
      end
     /*  */
     KOST_GES = KOST_NUML + KOST_UML - KOST_EIN + WEG_ZUF_GES_SOLL - ENTRL_ANTEIL;
     ERG = VZ + SONUML_ANTEIL - KOST_GES;
     /*  */
     SUSPEND;
    END
  END /* IART = 1 */
 ELSE
 IF (IART=3) THEN  /* WEG-Abrechnung E/B gemeinsam */
  BEGIN
   FOR SELECT ONR, KNR, KNRSTR, KBEZ, HAUSGVZ, IHRABRVON, IHRABRBIS, WEG_ZUF_GES_SOLL, ENTRL_ANTEIL, SONUML_ANTEIL 
   FROM NKMASTER
   WHERE ONR = :IONR
   ORDER BY KNR
   INTO :ONR, :KNR, :KNRSTR, :KBEZ, :VZ, :DTVON, :DTBIS, :WEG_ZUF_GES_SOLL, :ENTRL_ANTEIL, :SONUML_ANTEIL 
   DO
    BEGIN
     KOST_UML = 0;
     KOST_NUML = 0;
     KOST_EIN = 0;
     KOST_GES = 0;
     ERG = 0;
     /*  */
     select -kanteil from nkdetail where onr=:onr and knr=:knr and ear=4 and kklasse is null and haupt_nr=1 and kgesamt<0 and kname='Entnahmen' INTO :ENTRL_ANTEIL;
     /* */    
     IF (WEG_ZUF_GES_SOLL IS NULL) THEN
      WEG_ZUF_GES_SOLL = 0;
     IF (ENTRL_ANTEIL IS NULL) THEN
      ENTRL_ANTEIL = 0;
     IF (SONUML_ANTEIL IS NULL) THEN
      SONUML_ANTEIL = 0;
     IF (VZ IS NULL) THEN
      VZ = 0; 
     /*  */ 
     FOR
      select sum(kbruttoanteil) as BETRAG, 1 as ART from NKDETAIL where ONR = :IONR and KNR=:KNR and haupt_nr=1 and ((ear=1) or (ear=4 and kklasse is not null)) and name is null /* numl Ausgaben */
      union all
      select sum(kbruttoanteil) as BETRAG, 2 as ART from NKDETAIL where ONR = :IONR and KNR=:KNR and haupt_nr=1  and ear=1 and name is not null /* uml  Ausgaben */
      union all
      select sum(kbruttoanteil) as BETRAG, 3 as ART from NKDETAIL where ONR = :IONR and KNR=:KNR and haupt_nr=1 and ear=3 /*  s. Einnahmen */
     into :RTMP, :ART
     do
      begin
       if (RTMP IS NULL) then
        RTMP = 0;
       if (:ART = 1) then
        KOST_NUML = RTMP;
       else
        begin
         if (:ART= 2) then
          KOST_UML = RTMP;
         else
          begin
           if (:ART = 3) then
            KOST_EIN = - RTMP;
          end
        end
      end
     /*  */
     KOST_GES = KOST_NUML + KOST_UML - KOST_EIN + WEG_ZUF_GES_SOLL - ENTRL_ANTEIL;
     ERG = VZ + SONUML_ANTEIL - KOST_GES;
     /*  */
     SUSPEND;
    END
  END /* IART = 3 */
 ELSE
 IF (IART=2) THEN  /* WEG-Abrechnung E/B getrennt */
  BEGIN
   FOR SELECT ONR, KNR, KNRSTR, KBEZ, HAUSGVZ, IHRABRVON, IHRABRBIS, WEG_ZUF_GES_SOLL, ENTRL_ANTEIL, BKANT, HKANT, BKVZ, HKVZ, BKERG, HKERG, SONUML_ANTEIL
   FROM NKMASTER
   WHERE ONR = :IONR
   ORDER BY ENR, KNR DESC
   INTO :ONR, :KNR, :KNRSTR, :KBEZ, :VZ, :DTVON, :DTBIS, :WEG_ZUF_GES_SOLL, :ENTRL_ANTEIL, :BKANT, :HKANT, :BKVZ, :HKVZ, :BKERG, :HKERG, :SONUML_ANTEIL
   DO
    BEGIN
     KOST_UML = 0;
     KOST_NUML = 0;
     KOST_EIN = 0;
     KOST_GES = 0;
     ERG = 0;
     /*  */
     select -kanteil from nkdetail where onr=:onr and knr=:knr and ear=4 and kklasse is null and haupt_nr=1 and kgesamt<0 and kname='Entnahmen' INTO :ENTRL_ANTEIL;
     /* */     
     IF (WEG_ZUF_GES_SOLL IS NULL) THEN
      WEG_ZUF_GES_SOLL = 0;
     IF (ENTRL_ANTEIL IS NULL) THEN
      ENTRL_ANTEIL = 0;
     IF (SONUML_ANTEIL IS NULL) THEN
      SONUML_ANTEIL = 0;
     IF (VZ IS NULL) THEN
      VZ = 0; 
     /*  */ 
     IF (KNR<200000) THEN
      BEGIN
       KOST_GES = BKANT + HKANT;
       VZ = BKVZ + HKVZ;
       KOST_UML = KOST_GES;
       KOST_NUML = 0;
       ERG = BKERG + HKERG;
      END
     ELSE
      BEGIN
       FOR
        select sum(kbruttoanteil) as BETRAG, 1 as ART from NKDETAIL where ONR = :IONR and KNR=:KNR and haupt_nr=1 and ((ear=1) or (ear=4 and kklasse is not null)) /* numl Ausgaben */
        union all
        select sum(kbruttoanteil) as BETRAG, 3 as ART from NKDETAIL where ONR = :IONR and KNR=:KNR and haupt_nr=1 and ear=3 /*  s. Einnahmen */
       into :RTMP, :ART
       do
        begin
         if (RTMP IS NULL) then
          RTMP = 0;        
         if (:ART = 1) then
          KOST_NUML = RTMP;
         else
          begin
           if (:ART = 3) then
            KOST_EIN = - RTMP;
          end
        end
       /*  */
       KOST_GES = KOST_NUML + KOST_UML - KOST_EIN + WEG_ZUF_GES_SOLL - ENTRL_ANTEIL;
       ERG = VZ + SONUML_ANTEIL - KOST_GES;
       /*  */
      END
     SUSPEND;
    END
  END /* IART = 2 */
END
