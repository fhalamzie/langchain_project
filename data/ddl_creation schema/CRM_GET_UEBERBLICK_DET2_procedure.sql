-- Prozedur: CRM_GET_UEBERBLICK_DET2
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE CRM_GET_UEBERBLICK_DET2
BEGIN
 if (WER='F') then
  begin
   if (TABLE_TYP=1) then
    begin
     for select count(*), idf1 from aufgabe where IDF1 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idf1 into :ANZ, :ID do suspend;
     for select count(*), idf2 from aufgabe where IDF2 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idf2 into :ANZ, :ID do suspend;
     for select count(*), idf3 from aufgabe where IDF3 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idf3 into :ANZ, :ID do suspend;
     for select count(*), idf4 from aufgabe where IDF4 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idf4 into :ANZ, :ID do suspend;
     for select count(*), idf5 from aufgabe where IDF5 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idf5 into :ANZ, :ID do suspend;
    end
   else
   if (TABLE_TYP=2) then
    begin
     for select count(*), KKNR from termine_crm where KKNR IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by KKNR into :ANZ, :ID do suspend;
    end
   else
   if (TABLE_TYP=3) then
    begin
     for select count(*), KKNR from anruf where KKNR IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by KKNR into :ANZ, :ID do suspend;
    end
   else
    if (TABLE_TYP=4) then
     begin
      for select count(*), idf1 from vorgang where IDF1 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idf1 into :ANZ, :ID do suspend;
      for select count(*), idf2 from vorgang where IDF2 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idf2 into :ANZ, :ID do suspend;
      for select count(*), idf3 from vorgang where IDF3 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idf3 into :ANZ, :ID do suspend;
      for select count(*), idf4 from vorgang where IDF4 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idf4 into :ANZ, :ID do suspend;
      for select count(*), idf5 from vorgang where IDF5 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idf5 into :ANZ, :ID do suspend;
     end
   end
  else
 if (WER='M') then /*MITARBEITER*/
  begin
   if (TABLE_TYP=1) then
    begin
     for select count(*), idm1 from aufgabe where IDM1 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm1 into :ANZ, :ID do suspend;
     for select count(*), idm2 from aufgabe where IDM2 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm2 into :ANZ, :ID do suspend;
     for select count(*), idm3 from aufgabe where IDM3 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm3 into :ANZ, :ID do suspend;
     for select count(*), idm4 from aufgabe where IDM4 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm4 into :ANZ, :ID do suspend;
     for select count(*), idm5 from aufgabe where IDM5 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm5 into :ANZ, :ID do suspend;
     for select count(*), idm6 from aufgabe where IDM6 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm6 into :ANZ, :ID do suspend;
     for select count(*), idm7 from aufgabe where IDM7 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm7 into :ANZ, :ID do suspend;
     for select count(*), idm8 from aufgabe where IDM8 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm8 into :ANZ, :ID do suspend;
     for select count(*), idm9 from aufgabe where IDM9 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm9 into :ANZ, :ID do suspend;
     for select count(*), idm10 from aufgabe where IDM10 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm10 into :ANZ, :ID do suspend;
     for select count(*), idm11 from aufgabe where IDM11 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm11 into :ANZ, :ID do suspend;
     for select count(*), idm12 from aufgabe where IDM12 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm12 into :ANZ, :ID do suspend;
    end
   else
   if (TABLE_TYP=2) then
    begin
     for select count(*), idm1 from termine_crm where idm1 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm1 into :ANZ, :ID do suspend;
     for select count(*), idm2 from termine_crm where idm2 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm2 into :ANZ, :ID do suspend;
     for select count(*), idm3 from termine_crm where idm3 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm3 into :ANZ, :ID do suspend;
     for select count(*), idm4 from termine_crm where idm4 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm4 into :ANZ, :ID do suspend;
     for select count(*), idm5 from termine_crm where idm5 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm5 into :ANZ, :ID do suspend;
     for select count(*), idm6 from termine_crm where idm6 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm6 into :ANZ, :ID do suspend;
     for select count(*), idm7 from termine_crm where idm7 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm7 into :ANZ, :ID do suspend;
     for select count(*), idm8 from termine_crm where idm8 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm8 into :ANZ, :ID do suspend;
     for select count(*), idm9 from termine_crm where idm9 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm9 into :ANZ, :ID do suspend;
     for select count(*), idm10 from termine_crm where idm10 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm10 into :ANZ, :ID do suspend;
     for select count(*), idm11 from termine_crm where idm11 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm11 into :ANZ, :ID do suspend;
     for select count(*), idm12 from termine_crm where idm12 IS NOT NULL and STATUS<4 and (BEGINNT_AM >= :DT_VON and BEGINNT_AM <= :DT_BIS) and ISVORLAGE=0 group by idm12 into :ANZ, :ID do suspend;
    end
   else
   if (TABLE_TYP=3) then
    begin
     for select count(*), idm1 from anruf where idm1 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm1 into :ANZ, :ID do suspend;
     for select count(*), idm2 from anruf where idm2 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm2 into :ANZ, :ID do suspend;
     for select count(*), idm3 from anruf where idm3 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm3 into :ANZ, :ID do suspend;
     for select count(*), idm4 from anruf where idm4 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm4 into :ANZ, :ID do suspend;
     for select count(*), idm5 from anruf where idm5 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm5 into :ANZ, :ID do suspend;
     for select count(*), idm6 from anruf where idm6 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm6 into :ANZ, :ID do suspend;
     for select count(*), idm7 from anruf where idm7 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm7 into :ANZ, :ID do suspend;
     for select count(*), idm8 from anruf where idm8 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm8 into :ANZ, :ID do suspend;
     for select count(*), idm9 from anruf where idm9 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm9 into :ANZ, :ID do suspend;
     for select count(*), idm10 from anruf where idm10 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm10 into :ANZ, :ID do suspend;
     for select count(*), idm11 from anruf where idm11 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm11 into :ANZ, :ID do suspend;
     for select count(*), idm12 from anruf where idm12 IS NOT NULL and STATUS<4 and (DATUM >= :DT_VON and DATUM <= :DT_BIS) and ISVORLAGE=0 group by idm12 into :ANZ, :ID do suspend;
    end
   else
    if (TABLE_TYP=4) then
     begin
      for select count(*), idm1 from vorgang where IDM1 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm1 into :ANZ, :ID do suspend;
      for select count(*), idm2 from vorgang where IDM2 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm2 into :ANZ, :ID do suspend;
      for select count(*), idm3 from vorgang where IDM3 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm3 into :ANZ, :ID do suspend;
      for select count(*), idm4 from vorgang where IDM4 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm4 into :ANZ, :ID do suspend;
      for select count(*), idm5 from vorgang where IDM5 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm5 into :ANZ, :ID do suspend;
      for select count(*), idm6 from vorgang where IDM6 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm6 into :ANZ, :ID do suspend;
      for select count(*), idm7 from vorgang where IDM7 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm7 into :ANZ, :ID do suspend;
      for select count(*), idm8 from vorgang where IDM8 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm8 into :ANZ, :ID do suspend;
      for select count(*), idm9 from vorgang where IDM9 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm9 into :ANZ, :ID do suspend;
      for select count(*), idm10 from vorgang where IDM10 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm10 into :ANZ, :ID do suspend;
      for select count(*), idm11 from vorgang where IDM11 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm11 into :ANZ, :ID do suspend;
      for select count(*), idm12 from vorgang where IDM12 IS NOT NULL and STATUS<4 and ID<>-1 and (STARTDATUM >= :DT_VON and STARTDATUM <= :DT_BIS) and ISVORLAGE=0 group by idm12 into :ANZ, :ID do suspend;
     end
   end
END
