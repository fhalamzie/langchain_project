-- Prozedur: SEV_ABRECHNUNG
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE SEV_ABRECHNUNG
BEGIN
  if (MIT_MIETAUSZAHLUNG='J') then
   begin
    for select BNR, ONR, KNR, SEVKNR, BUCHDATUM, BELEGNR, BETRAG,TEXT,SEVBANKNR, MWST, BUCHNR from sevmieten
    where (ONR>=:ONRVON and ONR<=:ONRBIS)
    and (BUCHDATUM>=:DTVON and BUCHDATUM<=:DTBIS)
    and ((KNR<60 and STATUS=10) or (STATUS=10 and KNR=64) or KNR=60)
    into :BNR, :ONR, :KNR, :SEVKNR, :BUCHDATUM, :BELEGNR, :BETRAG, :TEXT, :SEVBANKNR, :MWST, :BUCHNR
    do
     begin
      if (KNR=50 or KNR=51 or KNR=52 or KNR=54) then
       begin
        EA=2;
        AUSGABE=BETRAG;
        EINNAHME=0;
       end
      else
       if (KNR=53) THEN
        BEGIN
         EA=3;
         AUSGABE=BETRAG;
         EINNAHME=0;
        END
       else
        BEGIN
         EA=1;
         EINNAHME=BETRAG;
         AUSGABE=0;
        END
      suspend;
    end
   end
  else
   begin
    for select BNR, ONR, KNR, SEVKNR, BUCHDATUM, BELEGNR, BETRAG,TEXT,SEVBANKNR, MWST, BUCHNR from sevmieten
    where (ONR>=:ONRVON and ONR<=:ONRBIS)
    and (BUCHDATUM>=:DTVON and BUCHDATUM<=:DTBIS)
    and (((KNR=50 or KNR=51 or KNR=52 or KNR=54) and STATUS=10) or ((STATUS=10 and KNR=64) or KNR=60))
    into :BNR, :ONR, :KNR, :SEVKNR, :BUCHDATUM, :BELEGNR, :BETRAG, :TEXT, :SEVBANKNR, :MWST, :BUCHNR
    do
     begin
     if (KNR=50 or KNR=51 or KNR=52 or KNR=54) then
       begin
        EA=2;
        AUSGABE=BETRAG;
        EINNAHME=0;
       end
      else
       if (KNR=53) THEN
        BEGIN
         EA=3;
         AUSGABE=BETRAG;
         EINNAHME=0;
        END
       else
        BEGIN
         EA=1;
         EINNAHME=BETRAG;
         AUSGABE=0;
        END
       suspend;
     end
   end
 END
