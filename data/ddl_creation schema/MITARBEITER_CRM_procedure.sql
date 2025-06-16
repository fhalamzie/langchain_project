-- Prozedur: MITARBEITER_CRM
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE MITARBEITER_CRM
DECLARE VARIABLE NAME VARCHAR(80);
DECLARE VARIABLE VORNAME VARCHAR(80);
BEGIN
FOR
 select Name, Vorname from mitarbeiter where id=:idm1 or id=:idm2 or id=:idm3 or id=:idm4 
  or id=:idm5 or id=:idm6 or id=:idm7 or id=:idm8 or id=:idm9 or id=:idm10 or id=:idm11 or id=:idm12
into :NAME, :VORNAME
DO
 begin
  if (NAME_VORNAME <> '') then 
   BEGIN
     NAME_VORNAME  = NAME_VORNAME || ', ';
     if (NAME<>'') THEN
      NAME_VORNAME = NAME_VORNAME || TRIM(NAME); 
     if (VORNAME<>'') THEN 
      NAME_VORNAME=NAME_VORNAME || ' ' || VORNAME;
   END
  ELSE 
  BEGIN
  NAME_VORNAME = TRIM(NAME);  
  if (VORNAME<>'') THEN
   if (NAME='') THEN
    NAME_VORNAME=VORNAME;
   else 
    NAME_VORNAME=NAME_VORNAME || ' ' || VORNAME;
   END
  end
  SUSPEND;
 
END
