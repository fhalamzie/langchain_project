-- Prozedur: UNTERSCHR_LISTE
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE UNTERSCHR_LISTE
BEGIN
 IF (BBEW='J') THEN
  BEGIN
   FOR 
   select ONR, KNR, ENR, ba.BNAME, ba.BVName, ba.BName2, ba.BVName2, ba.BTitel, ba.BTitel2,
    ba.BFIRMA, ba.BFIRMANAME, ba.BBRIEFAN  
   from bewohner b,bewadr ba  
   where b.bewnr=ba.bewnr and ONR=:IONR and (KNR - 100000 - ENR*100) = 0
   INTO :ONR, :KNR, :ENR, :NAME, :VName, :NAME2, :VNAME2, :TITEL, :TITEL2, :FIRMA, :FIRMANAME, :BRIEFAN
   DO
    BEGIN
     ANZ_WHG=1;
     SUSPEND;
    END
  END
 ELSE  /*EIGENTUEMER */
  BEGIN
   FOR select eignr, count(eignr), min(knr) from eigentuemer
   where ONR=:IONR and (KNR - 200000 - ENR*100) = 0
   group by eignr
   INTO :EIGNR, :ANZ_WHG, :KNR
   DO
    BEGIN
     SELECT ENAME, EVNAME, ENAME2, EVNAME2, ETITEL, ETITEL2, EFIRMA, EFIRMANAME, EBRIEFAN  from eigadr
     where EIGNR=:EIGNR
     INTO :NAME, :VName, :NAME2, :VNAME2, :TITEL, :TITEL2, :FIRMA, :FIRMANAME, :BRIEFAN;
     ONR=:IONR;
     ENR=(:KNR - 200000) / 100;
     SUSPEND;
    END
  END
END
