-- Prozedur: CRM_GET_UEBERBLICK
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE CRM_GET_UEBERBLICK
DECLARE VARIABLE GES_ROT INTEGER;
DECLARE VARIABLE GES_GELB INTEGER;
DECLARE VARIABLE GES_GRUEN INTEGER;
DECLARE VARIABLE GES_VORGAENGE INTEGER;
BEGIN
  ISSUM=0;
  GES_ROT=0; GES_GELB=0; GES_GRUEN=0; GES_VORGAENGE=0;
  for select ID, SUM(ANZ_ROT), SUM(ANZ_GELB), SUM(ANZ_GRUEN), sum(ANZ_VORGAENGE)
    from CRM_GET_UEBERBLICK_DET(:TYP,:DTBIS_GRUEN,:DTBIS_GELB,:DTBIS_ROT) group by ID
    into ID, ANZ_ROT, ANZ_GELB, ANZ_GRUEN, ANZ_VORGAENGE
    do
     begin
      if (TYP='O') then
       BEGIN
        select OBEZ, OSTRASSE, OPLZORT from OBJEKTE where ONR=:ID into NAME1, NAME2, NAME3;
       END
      ELSE
      if (TYP='M') then
       BEGIN
        select NAME, VORNAME from MITARBEITER where ID=:ID into :NAME1, :NAME2;
       END
     ELSE
      if (TYP='F') then
       BEGIN
        select NAME, VORNAME, ZUSATZ from LIEFERAN where KNR=:ID into :NAME1, :NAME2, :NAME3;
       END
      GES_ROT=GES_ROT+ANZ_ROT;
      GES_GELB=GES_GELB+ANZ_GELB;
      GES_GRUEN=GES_GRUEN+ANZ_GRUEN;
      GES_VORGAENGE=GES_VORGAENGE+ANZ_VORGAENGE;
      if (ID IS NOT NULL) then
       begin
        if (ANZ_ROT=0) then
         ANZ_ROT=NULL;
        if (ANZ_GELB=0) then
         ANZ_GELB=NULL;
        if (ANZ_GRUEN=0) then
         ANZ_GRUEN=NULL;
        if (ANZ_VORGAENGE=0) then
         ANZ_VORGAENGE=NULL;
         if (ID=AKT_MITARBEITER AND TYP='M') then
          ISSUM=1;
         ELSE
          ISSUM=0;
        suspend;
       end
     end
  ISSUM=2;
  if (GES_ROT>0) then
   ANZ_ROT=GES_ROT;
  else
   ANZ_ROT=NULL;
  if (GES_GELB>0) then
   ANZ_GELB=GES_GELB;
  else
   ANZ_GELB=NULL;
  if (GES_GRUEN>0) then
   ANZ_GRUEN=GES_GRUEN;
  else
   ANZ_GRUEN=NULL;
  if (GES_VORGAENGE>0) then
   ANZ_VORGAENGE=GES_VORGAENGE;
  else
   ANZ_VORGAENGE=NULL;
  NAME1='gesamt';
  NAME2='';
  NAME3='';
  ID=NULL;
  suspend;
END
