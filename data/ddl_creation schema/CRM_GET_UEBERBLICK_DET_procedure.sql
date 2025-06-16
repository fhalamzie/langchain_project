-- Prozedur: CRM_GET_UEBERBLICK_DET
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE CRM_GET_UEBERBLICK_DET
declare variable IANZ INTEGER;
declare variable DT_FIRST DATE;
BEGIN
  if (TYP='O') then
   begin
    /* Aufgaben ROT */
    ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
    for select ONR, count(*) from aufgabe where STATUS<4 and BEGINNT_AM < :DTBIS_ROT and ISVORLAGE=0 group by ONR into :ID, :ANZ_ROT do SUSPEND;
    /* Aufgaben GELB */
    ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0;  ANZ_VORGAENGE=0;
    for select ONR, count(*) from aufgabe where STATUS<4 and (BEGINNT_AM >= :DTBIS_ROT and BEGINNT_AM < :DTBIS_GELB) and ISVORLAGE=0 group by ONR into :ID, :ANZ_GELB DO SUSPEND;
    /* Aufgaben GRUEN */
    ANZ_ROT=0;  ANZ_GELB=0;  ANZ_GRUEN=0;  ANZ_VORGAENGE=0;
    for select ONR, count(*) from aufgabe where STATUS<4 and (BEGINNT_AM >= :DTBIS_GELB and BEGINNT_AM < :DTBIS_GRUEN) and ISVORLAGE=0 group by ONR into :ID, :ANZ_GRUEN DO SUSPEND;
    /* TERMINE ROT */
    ANZ_ROT=0;  ANZ_GELB=0;  ANZ_GRUEN=0;  ANZ_VORGAENGE=0;
    for select ONR, count(*) from termine_crm where STATUS<4 and BEGINNT_AM < :DTBIS_ROT and ISVORLAGE=0 group by ONR into :ID, :ANZ_ROT do SUSPEND;
    /* TERMINE GELB */
    ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0;  ANZ_VORGAENGE=0;
    for select ONR, count(*) from termine_crm where STATUS<4 and (BEGINNT_AM >= :DTBIS_ROT and BEGINNT_AM < :DTBIS_GELB) and ISVORLAGE=0 group by ONR into :ID, :ANZ_GELB DO SUSPEND;
    /* TERMINE GRUEN */
    ANZ_ROT=0;  ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
    for select ONR, count(*) from termine_crm where STATUS<4 and (BEGINNT_AM >= :DTBIS_GELB and BEGINNT_AM < :DTBIS_GRUEN) and ISVORLAGE=0 group by ONR into :ID, :ANZ_GRUEN DO SUSPEND;
    /* ANRUFE ROT */
    ANZ_ROT=0;  ANZ_GELB=0;  ANZ_GRUEN=0;  ANZ_VORGAENGE=0;
    for select ONR, count(*) from anruf where STATUS<4 and DATUM < :DTBIS_ROT and ISVORLAGE=0 group by ONR into :ID, :ANZ_ROT do SUSPEND;
    /* ANRUFE GELB */
    ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0;  ANZ_VORGAENGE=0;
    for select ONR, count(*) from anruf where STATUS<4 and (DATUM >= :DTBIS_ROT and DATUM < :DTBIS_GELB) and ISVORLAGE=0 group by ONR into :ID, :ANZ_GELB DO SUSPEND;
    /* ANRUFE GRUEN */
    ANZ_ROT=0;  ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
    for select ONR, count(*) from anruf where STATUS<4 and (DATUM >= :DTBIS_GELB and DATUM < :DTBIS_GRUEN) and ISVORLAGE=0 group by ONR into :ID, :ANZ_GRUEN DO SUSPEND;
    /* VorgÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤nge */
    ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
    for select ONR, count(*) from vorgang where STATUS<4 and ID<>-1 and ISVORLAGE=0 group by ONR into :ID, :ANZ_VORGAENGE do suspend;
   END
  ELSE
   if (TYP='M' or TYP='F') then  /* MITARBEITER, FIRMEN */
    BEGIN
     DT_FIRST=CAST('1980-01-01' AS Date);
     /* Aufgaben ROT */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(1,:TYP,:DT_FIRST,:DTBIS_ROT) group by ID into :ID, :ANZ_ROT do suspend;
     /* Aufgaben Gelb */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(1,:TYP,:DTBIS_ROT,:DTBIS_GELB) group by ID into :ID, :ANZ_GELB do suspend;
     /* Aufgaben Gruen */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(1,:TYP,:DTBIS_GELB,:DTBIS_GRUEN) group by ID into :ID, :ANZ_GRUEN do suspend;
     /* Termine ROT */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(2,:TYP,:DT_FIRST,:DTBIS_ROT) group by ID into :ID, :ANZ_ROT do suspend;
     /* Termine Gelb */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(2,:TYP,:DTBIS_ROT,:DTBIS_GELB) group by ID into :ID, :ANZ_GELB do suspend;
     /* Termine Gruen */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(2,:TYP,:DTBIS_GELB,:DTBIS_GRUEN) group by ID into :ID, :ANZ_GRUEN do suspend;
     /* ANRUF ROT */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(3,:TYP,:DT_FIRST,:DTBIS_ROT) group by ID into :ID, :ANZ_ROT do suspend;
     /* ANRUF Gelb */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(3,:TYP,:DTBIS_ROT,:DTBIS_GELB) group by ID into :ID, :ANZ_GELB do suspend;
     /* ANRUF Gruen */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(3,:TYP,:DTBIS_GELB,:DTBIS_GRUEN) group by ID into :ID, :ANZ_GRUEN do suspend;
     /* Vorgaenge Rot*/
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(4,:TYP,:DT_FIRST,:DTBIS_ROT) group by ID into :ID, :ANZ_VORGAENGE do suspend;
     /* Vorgaenge Gelb */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(4,:TYP,:DTBIS_ROT,:DTBIS_GELB) group by ID into :ID, :ANZ_VORGAENGE do suspend;
     /* Vorgaenge Gruen */
     ANZ_ROT=0; ANZ_GELB=0; ANZ_GRUEN=0; ANZ_VORGAENGE=0;
     for select ID, sum(ANZ) from crm_get_ueberblick_det2(4,:TYP,:DTBIS_GELB,:DTBIS_GRUEN) group by ID into :ID, :ANZ_VORGAENGE do suspend;
    END /* MITARBEITER */
END
