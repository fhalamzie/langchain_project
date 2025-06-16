-- Prozedur: EINZKAUS_VORTRAG
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE EINZKAUS_VORTRAG
DECLARE VARIABLE GN_1 SMALLINT;
DECLARE VARIABLE GN_2 SMALLINT;
DECLARE VARIABLE INR SMALLINT;
DECLARE VARIABLE IPOS SMALLINT;
DECLARE VARIABLE BETRAG NUMERIC(18, 2);
BEGIN
 IF (BMITVORTRAG='N') THEN
  BEGIN
   MIETE=0;
   BK=0;
   HK=0;
   GN=0;
   HAUSGELD=0;
   SUSPEND;
  END
 ELSE
  BEGIN
   if (KNR<200000) then
    BEGIN
     EXECUTE PROCEDURE einzkaus_vortrag_pos (:ONR, :KNR, :DTVON, :BWDATUM, :BMITVORTRAG, 0, 0, 10) RETURNING_VALUES :MIETE;
     EXECUTE PROCEDURE einzkaus_vortrag_pos (:ONR, :KNR, :DTVON, :BWDATUM, :BMITVORTRAG, 0, 0, 11) RETURNING_VALUES :BK;
     EXECUTE PROCEDURE einzkaus_vortrag_pos (:ONR, :KNR, :DTVON, :BWDATUM, :BMITVORTRAG, 0, 0, 12) RETURNING_VALUES :HK;
     EXECUTE PROCEDURE einzkaus_vortrag_pos (:ONR, :KNR, :DTVON, :BWDATUM, :BMITVORTRAG, 0, 0, 13) RETURNING_VALUES :GN;
     SALDO=MIETE+BK+HK+GN;
    END
   ELSE
    BEGIN
     if (GN_STATUS=0) then /* MIT GN */
      BEGIN
       GN_1=0;
       GN_2=1;
      END
     ELSE
      if (GN_STATUS=1) then /* OHNE GN */
       BEGIN
        GN_1=0;
        GN_2=0;
       END
     ELSE
      if (GN_STATUS=2) then /* NUR GN */
       BEGIN
        GN_1=1;
        GN_2=1;
       END
     EXECUTE PROCEDURE einzkaus_vortrag_pos (:ONR, :KNR, :DTVON, :BWDATUM, :BMITVORTRAG, :GN_1, :GN_2, 15) RETURNING_VALUES :BK; /* Hausgeld */
     HK=0;
     INR=1;
     WHILE (INR <= 48) do
      begin
       IPOS=(100 + (10 * INR));
       IF (INR<>8 and INR<>9) THEN /* reserviert */
        BEGIN
         EXECUTE PROCEDURE einzkaus_vortrag_pos (:ONR, :KNR, :DTVON, :BWDATUM, :BMITVORTRAG, :GN_1, :GN_2, :IPOS) RETURNING_VALUES :BETRAG; /* RL */
         if (BETRAG IS NOT NULL) then
          HK=HK+BETRAG;
         END 
       INR=INR+1; 
      end
     EXECUTE PROCEDURE einzkaus_vortrag_pos (:ONR, :KNR, :DTVON, :BWDATUM, :BMITVORTRAG, :GN_1, :GN_2, 17) RETURNING_VALUES :GN; /* Sonderumlage */
     SALDO=BK+HK+GN;
    END
   SUSPEND;
  END 
END
