-- Prozedur: STAFFMIETERH
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE STAFFMIETERH
DECLARE VARIABLE DTMIN DATE;
DECLARE VARIABLE DTMIN2 DATE;
DECLARE VARIABLE NMIN INTEGER;
DECLARE VARIABLE NSTAFFMIN1 NUMERIC(15, 2);
DECLARE VARIABLE NSTAFFMIN2 NUMERIC(15, 2);
DECLARE VARIABLE NMIET1 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM1 DATE;
DECLARE VARIABLE NMIET2 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM2 DATE;
DECLARE VARIABLE NMIET3 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM3 DATE;
DECLARE VARIABLE NMIET4 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM4 DATE;
DECLARE VARIABLE NMIET5 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM5 DATE;
DECLARE VARIABLE NMIET6 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM6 DATE;
DECLARE VARIABLE NMIET7 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM7 DATE;
DECLARE VARIABLE NMIET8 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM8 DATE;
DECLARE VARIABLE NMIET9 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM9 DATE;
DECLARE VARIABLE NMIET10 NUMERIC(15, 2);
DECLARE VARIABLE DTDATUM10 DATE;
DECLARE VARIABLE SBNAME VARCHAR(80);
DECLARE VARIABLE SBVNAME VARCHAR(80);
DECLARE VARIABLE IFOUND SMALLINT;
DECLARE VARIABLE DTNEUESTAFFEL DATE;
DECLARE VARIABLE DTALTESTAFFEL DATE;
DECLARE VARIABLE NNEUESTAFFEL NUMERIC(15, 2);
DECLARE VARIABLE NALTESTAFFEL NUMERIC(15, 2);
DECLARE VARIABLE DTEINZUG DATE;
DECLARE VARIABLE DTAUSZUG DATE;
BEGIN
 if (:IONR <> -1) then
  begin
   for
   select staffelvz.onr,staffelvz.betrag1,staffelvz.datum1,staffelvz.betrag2,staffelvz.datum2,staffelvz.betrag3,staffelvz.datum3,
   staffelvz.betrag4,staffelvz.datum4,staffelvz.betrag5,staffelvz.datum5,staffelvz.betrag6,staffelvz.datum6,staffelvz.betrag7,
   staffelvz.datum7,staffelvz.betrag8,staffelvz.datum8,staffelvz.betrag9,staffelvz.datum9,staffelvz.betrag10,staffelvz.datum10,
   staffelvz.knr,ba.bname,ba.bvname,vorausz.bez, b.vbeginn, b.vende 
   from staffelvz,bewohner b, bewadr ba, vorausz
   where b.bewnr=ba.bewnr and staffelvz.onr=b.onr and staffelvz.knr=b.knr and b.staffel='J' and vorausz.onr=b.onr
   and vorausz.knr=(((staffelvz.zpos-1)*10)+60000) and b.onr=:IONR
   order by staffelvz.onr,staffelvz.knr,staffelvz.zpos    
   into :ONR,nMiet1,dtDatum1,nMiet2,dtDatum2,nMiet3,dtDatum3,nMiet4,dtDatum4,nMiet5,dtDatum5,nMiet6,dtDatum6,nMiet7,dtDatum7,nMiet8,dtDatum8,nMiet9,dtDatum9,nMiet10,dtDatum10,:KNR,sbname,sbvname,:VZBEZ, dtEinzug, dtAuszug
   do
    begin
     dtNeueStaffel='01.01.1753';
     dtAlteStaffel='01.01.1753';
     nNeueStaffel=0;
     nAlteStaffel=0;
     ifound=0;
     if (dtEinzug is Null) then
      dtEinzug = '01.01.1900';
     if (dtAuszug is Null) then
      dtAuszug = '31.12.9990';     

     /*10 mal*/
     if ((dtDatum1 is not null) and (dtDatum1 >= :DTVON) and (dtDatum1 <= :DTBIS)) then
      begin
       if (dtDatum1 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum1;
          nNeueStaffel=nMiet1;
          ifound=1;
         end
      end

     if ((dtDatum2 is not null) and (dtDatum2 >= :DTVON) and (dtDatum2 <= :DTBIS)) then
      begin
       if (dtDatum2 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum2;
          nNeueStaffel=nMiet2;
          ifound=1;
         end
      end

     if ((dtDatum3 is not null) and (dtDatum3 >= :DTVON) and (dtDatum3 <= :DTBIS)) then
      begin
       if (dtDatum3 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum3;
          nNeueStaffel=nMiet3;
          ifound=1;
         end
      end

     if ((dtDatum4 is not null) and (dtDatum4 >= :DTVON) and (dtDatum4 <= :DTBIS)) then
      begin
       if (dtDatum4 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum4;
          nNeueStaffel=nMiet4;
          ifound=1;
         end
      end

     if ((dtDatum5 is not null) and (dtDatum5 >= :DTVON) and (dtDatum5 <= :DTBIS)) then
      begin
       if (dtDatum5 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum5;
          nNeueStaffel=nMiet5;
          ifound=1;
         end
      end

     if ((dtDatum6 is not null) and (dtDatum6 >= :DTVON) and (dtDatum6 <= :DTBIS)) then
      begin
       if (dtDatum6 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum6;
          nNeueStaffel=nMiet6;
          ifound=1;
         end
      end

     if ((dtDatum7 is not null) and (dtDatum7 >= :DTVON) and (dtDatum7 <= :DTBIS)) then
      begin
       if (dtDatum7 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum7;
          nNeueStaffel=nMiet7;
          ifound=1;
         end
      end

     if ((dtDatum8 is not null) and (dtDatum8 >= :DTVON) and (dtDatum8 <= :DTBIS)) then
      begin
       if (dtDatum8 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum8;
          nNeueStaffel=nMiet8;
          ifound=1;
         end
      end

     if ((dtDatum9 is not null) and (dtDatum9 >= :DTVON) and (dtDatum9 <= :DTBIS)) then
      begin
       if (dtDatum9 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum9;
          nNeueStaffel=nMiet9;
          ifound=1;
         end
      end

     if ((dtDatum10 is not null) and (dtDatum10 >= :DTVON) and (dtDatum10 <= :DTBIS)) then
      begin
       if (dtDatum10 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum10;
          nNeueStaffel=nMiet10;
          ifound=1;
         end
      end

     /*Alte Staffel*/
     if ((ifound=1) and (dtDatum1 >= dtAlteStaffel) and (dtDatum1 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum1;
       nAlteStaffel=nMiet1;
      end

     if ((ifound=1) and (dtDatum2 >= dtAlteStaffel) and (dtDatum2 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum2;
       nAlteStaffel=nMiet2;
      end

     if ((ifound=1) and (dtDatum3 >= dtAlteStaffel) and (dtDatum3 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum3;
       nAlteStaffel=nMiet3;
      end

     if ((ifound=1) and (dtDatum4 >= dtAlteStaffel) and (dtDatum4 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum4;
       nAlteStaffel=nMiet4;
      end

     if ((ifound=1) and (dtDatum5 >= dtAlteStaffel) and (dtDatum5 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum5;
       nAlteStaffel=nMiet5;
      end

     if ((ifound=1) and (dtDatum6 >= dtAlteStaffel) and (dtDatum6 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum6;
       nAlteStaffel=nMiet6;
      end

     if ((ifound=1) and (dtDatum7 >= dtAlteStaffel) and (dtDatum7 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum7;
       nAlteStaffel=nMiet7;
      end

     if ((ifound=1) and (dtDatum8 >= dtAlteStaffel) and (dtDatum8 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum8;
       nAlteStaffel=nMiet8;
      end

     if ((ifound=1) and (dtDatum9 >= dtAlteStaffel) and (dtDatum9 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum9;
       nAlteStaffel=nMiet9;
      end

     if ((ifound=1) and (dtDatum10 >= dtAlteStaffel) and (dtDatum10 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum10;
       nAlteStaffel=nMiet10;
      end

     if ((sbvname is not null) and (sbname is not null)) then
      BEWSTR=sbvname || ' ' || sbname;
     else
      begin
       if (sbvname is not null) then
        BEWSTR=sbvname;
       if (sbname is not null) then
        BEWSTR=sbname;
      end

     SDATUM=dtNeueStaffel;
     if (dtAlteStaffel='01.01.1753') then
      SDATUMALT=null;
     else
      SDATUMALT=dtAlteStaffel;
     STAFFMIET=nNeueStaffel;
     STAFFMIETALT=nAlteStaffel;
     DIFFSTAFFMIET=nNeueStaffel - nAlteStaffel;
     
     if ((dtAuszug < DTVON) or (dtEinzug > DTBIS)) then
      ifound = 0;
      
     if (ifound=1) then
      SUSPEND;
   end
  end
 else
  begin
   for
    select staffelvz.onr,staffelvz.betrag1,staffelvz.datum1,staffelvz.betrag2,staffelvz.datum2,staffelvz.betrag3,staffelvz.datum3,
    staffelvz.betrag4,staffelvz.datum4,staffelvz.betrag5,staffelvz.datum5,staffelvz.betrag6,staffelvz.datum6,staffelvz.betrag7,
    staffelvz.datum7,staffelvz.betrag8,staffelvz.datum8,staffelvz.betrag9,staffelvz.datum9,staffelvz.betrag10,staffelvz.datum10,
    staffelvz.knr,ba.bname,ba.bvname,vorausz.bez, b.vbeginn, b.vende 
    from staffelvz,bewohner b,bewadr ba, vorausz,objekte
    where b.bewnr=ba.bewnr and objekte.onr=b.onr and staffelvz.onr=b.onr and staffelvz.knr=b.knr and b.staffel='J' and 
    vorausz.onr=b.onr
    and vorausz.knr=(((staffelvz.zpos-1)*10)+60000) and objekte.bsonst<>1
    order by staffelvz.onr,staffelvz.knr,staffelvz.zpos
    into :ONR,nMiet1,dtDatum1,nMiet2,dtDatum2,nMiet3,dtDatum3,nMiet4,dtDatum4,nMiet5,dtDatum5,nMiet6,dtDatum6,nMiet7,dtDatum7,nMiet8,dtDatum8,nMiet9,dtDatum9,nMiet10,dtDatum10,:KNR,sbname,sbvname,:VZBEZ, dtEinzug, dtAuszug
   do
    begin
     dtNeueStaffel='01.01.1753';
     dtAlteStaffel='01.01.1753';
     nNeueStaffel=0;
     nAlteStaffel=0;
     ifound=0;
     if (dtEinzug is Null) then
      dtEinzug = '01.01.1900';
     if (dtAuszug is Null) then
      dtAuszug = '31.12.9990';     

     /*10 mal*/
     if ((dtDatum1 is not null) and (dtDatum1 >= :DTVON) and (dtDatum1 <= :DTBIS)) then
      begin
       if (dtDatum1 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum1;
          nNeueStaffel=nMiet1;
          ifound=1;
         end
      end

     if ((dtDatum2 is not null) and (dtDatum2 >= :DTVON) and (dtDatum2 <= :DTBIS)) then
      begin
       if (dtDatum2 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum2;
          nNeueStaffel=nMiet2;
          ifound=1;
         end
      end

     if ((dtDatum3 is not null) and (dtDatum3 >= :DTVON) and (dtDatum3 <= :DTBIS)) then
      begin
       if (dtDatum3 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum3;
          nNeueStaffel=nMiet3;
          ifound=1;
         end
      end

     if ((dtDatum4 is not null) and (dtDatum4 >= :DTVON) and (dtDatum4 <= :DTBIS)) then
      begin
       if (dtDatum4 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum4;
          nNeueStaffel=nMiet4;
          ifound=1;
         end
      end

     if ((dtDatum5 is not null) and (dtDatum5 >= :DTVON) and (dtDatum5 <= :DTBIS)) then
      begin
       if (dtDatum5 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum5;
          nNeueStaffel=nMiet5;
          ifound=1;
         end
      end

     if ((dtDatum6 is not null) and (dtDatum6 >= :DTVON) and (dtDatum6 <= :DTBIS)) then
      begin
       if (dtDatum6 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum6;
          nNeueStaffel=nMiet6;
          ifound=1;
         end
      end

     if ((dtDatum7 is not null) and (dtDatum7 >= :DTVON) and (dtDatum7 <= :DTBIS)) then
      begin
       if (dtDatum7 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum7;
          nNeueStaffel=nMiet7;
          ifound=1;
         end
      end

     if ((dtDatum8 is not null) and (dtDatum8 >= :DTVON) and (dtDatum8 <= :DTBIS)) then
      begin
       if (dtDatum8 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum8;
          nNeueStaffel=nMiet8;
          ifound=1;
         end
      end

     if ((dtDatum9 is not null) and (dtDatum9 >= :DTVON) and (dtDatum9 <= :DTBIS)) then
      begin
       if (dtDatum9 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum9;
          nNeueStaffel=nMiet9;
          ifound=1;
         end
      end

     if ((dtDatum10 is not null) and (dtDatum10 >= :DTVON) and (dtDatum10 <= :DTBIS)) then
      begin
       if (dtDatum10 >= dtNeueStaffel) then
         begin
          dtNeueStaffel=dtDatum10;
          nNeueStaffel=nMiet10;
          ifound=1;
         end
      end

     /*Alte Staffel*/
     if ((ifound=1) and (dtDatum1 >= dtAlteStaffel) and (dtDatum1 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum1;
       nAlteStaffel=nMiet1;
      end

     if ((ifound=1) and (dtDatum2 >= dtAlteStaffel) and (dtDatum2 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum2;
       nAlteStaffel=nMiet2;
      end

     if ((ifound=1) and (dtDatum3 >= dtAlteStaffel) and (dtDatum3 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum3;
       nAlteStaffel=nMiet3;
      end

     if ((ifound=1) and (dtDatum4 >= dtAlteStaffel) and (dtDatum4 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum4;
       nAlteStaffel=nMiet4;
      end

     if ((ifound=1) and (dtDatum5 >= dtAlteStaffel) and (dtDatum5 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum5;
       nAlteStaffel=nMiet5;
      end

     if ((ifound=1) and (dtDatum6 >= dtAlteStaffel) and (dtDatum6 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum6;
       nAlteStaffel=nMiet6;
      end

     if ((ifound=1) and (dtDatum7 >= dtAlteStaffel) and (dtDatum7 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum7;
       nAlteStaffel=nMiet7;
      end

     if ((ifound=1) and (dtDatum8 >= dtAlteStaffel) and (dtDatum8 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum8;
       nAlteStaffel=nMiet8;
      end

     if ((ifound=1) and (dtDatum9 >= dtAlteStaffel) and (dtDatum9 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum9;
       nAlteStaffel=nMiet9;
      end

     if ((ifound=1) and (dtDatum10 >= dtAlteStaffel) and (dtDatum10 < dtNeueStaffel)) then
      begin
       dtAlteStaffel=dtDatum10;
       nAlteStaffel=nMiet10;
      end
      
     if ((sbvname is not null) and (sbname is not null)) then
      BEWSTR=sbvname || ' ' || sbname;
     else
      begin
       if (sbvname is not null) then
        BEWSTR=sbvname;
       if (sbname is not null) then
        BEWSTR=sbname;
      end

     SDATUM=dtNeueStaffel;
     if (dtAlteStaffel='01.01.1753') then
      SDATUMALT=null;
     else
      SDATUMALT=dtAlteStaffel;
     STAFFMIET=nNeueStaffel;
     STAFFMIETALT=nAlteStaffel;
     DIFFSTAFFMIET=nNeueStaffel - nAlteStaffel;
     
     if ((dtAuszug < DTVON) or (dtEinzug > DTBIS)) then
      ifound = 0;     
     
     if (ifound=1) then
      SUSPEND;
    end
  end
END
