-- Prozedur: GET_MAHNLISTE
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE GET_MAHNLISTE
--Erstellt
--Author
--Geandert 28.04.2023 
--Author RM
--IF (BMAHNALT='J') entfernt
DECLARE VARIABLE MSVON INTEGER;
DECLARE VARIABLE MSBIS INTEGER;
DECLARE VARIABLE KONTONAME VARCHAR(188);
DECLARE VARIABLE ILEV INTEGER;
DECLARE VARIABLE RBETRAG NUMERIC(18, 2);
DECLARE VARIABLE ITMP INTEGER;
DECLARE VARIABLE ITMP2 INTEGER;
DECLARE VARIABLE IVERWVON INTEGER;
DECLARE VARIABLE IVERWBIS INTEGER;
BEGIN
 IF (ZEIG_MAHNSTUFE=0) THEN  /* 1..5 */
  BEGIN
   MSVON=1;
   MSBIS=5;   
  END
 ELSE
  BEGIN
   MSVON=ZEIG_MAHNSTUFE;
   MSBIS=ZEIG_MAHNSTUFE;
  END
 IF (IAKTVERW=-1) THEN
  BEGIN
   IVERWVON=0;
   IVERWBIS=999;
  END
 ELSE
  BEGIN
   IVERWVON=IAKTVERW;
   IVERWBIS=IAKTVERW;
  END
 IF (BLEV='Z') then/* zuletzt gemahnt */
  BEGIN
   For
    select onrsoll, ksoll, kstrsoll, text, mahnstufe, opbetrag, datum, zzdatum, opnr, 'N', -1, 'N',ZULETZT_GEMAHNT from buchung
    where (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS) and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and 
    (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 
    and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS))) and ZULETZT_GEMAHNT IS NOT NULL
   into ONR, KNR, KNRSTR, TEXT, STUFE, BETRAG, DATUM, ZZDATUM, OPNR, SPERRE, ILEV, GEWERBLICH,ZULETZT_GEMAHNT
   DO
    SUSPEND;
   END
 ELSE
  BEGIN
    /* KEIN SPLIT */
    BEGIN
     ITMP=-1;
     ITMP2=-1;
     --(BMAHNALT='J')
     FOR
      select onrsoll, ksoll, kstrsoll, text, mahnstufe, opbetrag, datum, zzdatum, opnr, emahnsperre,lbnr, emwstausw,ZULETZT_GEMAHNT from buchung, eigentuemer
      where (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS) and splitnr is null and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS and MAHNALT = 'J'))) and OPBETRAG<>0 and zzdatum<=:ABDATUM
      and eigentuemer.onr=buchung.onrsoll and eigentuemer.knr=buchung.ksoll
      and emahnsperre = 'N'
      union
      select onrsoll, ksoll, kstrsoll, text, mahnstufe, opbetrag, datum, zzdatum, opnr, bmahnsperre,lbnr, bmwstausw,ZULETZT_GEMAHNT from buchung, bewohner
      where (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS) and splitnr is null and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS and MAHNALT = 'J'))) and OPBETRAG<>0 and zzdatum<=:ABDATUM
      and bewohner.onr=buchung.onrsoll and bewohner.knr=buchung.ksoll
      and bmahnsperre = 'N'
      order by 1, 2
      into ONR, KNR, KNRSTR, TEXT, STUFE, BETRAG, DATUM, ZZDATUM, OPNR, SPERRE, ILEV, GEWERBLICH,ZULETZT_GEMAHNT
      do
      begin
        IF ((ITMP<>KNR) OR (ITMP2<>ONR)) THEN
        BEGIN
         select saldo from KONTOSALDO_ALT(:ONR,:KNR,'01.01.9990','J','N') into RBETRAG;
         ITMP=KNR;
         ITMP2=ONR;
        END
        IF (RBETRAG<0) THEN
        BEGIN
         select KBEZ from konten where ONR=:ONR and KNR=:KNR into KONTONAME;
         KNRSTR=Left(KNRSTR || ' ' || KONTONAME, 100);
         if (BLEV='J') then
          SUSPEND;
         else
          begin
           if (ILEV is null) then
            SUSPEND;
          end
        END
      end
    END
    --(BMAHNALT='N')
    BEGIN
     for
      select onrsoll, ksoll, kstrsoll, text, mahnstufe, opbetrag, datum, zzdatum, opnr, emahnsperre,lbnr, emwstausw,ZULETZT_GEMAHNT from buchung, eigentuemer
      where (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS) and splitnr is null and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS and MAHNALT = 'N'))) and OPBETRAG>0 and zzdatum<=:ABDATUM
      and eigentuemer.onr=buchung.onrsoll and eigentuemer.knr=buchung.ksoll
      and emahnsperre = 'N'
      union
      select onrsoll, ksoll, kstrsoll, text, mahnstufe, opbetrag, datum, zzdatum, opnr, bmahnsperre,lbnr, bmwstausw,ZULETZT_GEMAHNT from buchung, bewohner
      where (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS) and splitnr is null and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS and MAHNALT = 'N'))) and OPBETRAG>0 and zzdatum<=:ABDATUM
      and bewohner.onr=buchung.onrsoll and bewohner.knr=buchung.ksoll
      and bmahnsperre = 'N'
      order by 1, 2
      into ONR, KNR, KNRSTR, TEXT, STUFE, BETRAG, DATUM, ZZDATUM, OPNR, SPERRE, ILEV, GEWERBLICH,ZULETZT_GEMAHNT
     do
      begin
       select KBEZ from konten where ONR=:ONR and KNR=:KNR into KONTONAME;
       KNRSTR=Left(KNRSTR || ' ' || KONTONAME, 100);
       IF (BETRAG>0) THEN
        BEGIN
         if (BLEV='J') then
          SUSPEND;
         else
          begin
           if (ILEV is null) then
            SUSPEND;
          end
        END
      end
    END
   /* SPLIT */
    BEGIN
     ITMP=-1;
     ITMP2=-1; 
     --(BMAHNALT='J')
     for
      select opnr,onrsoll, ksoll, kstrsoll, text, mahnstufe, datum, zzdatum,bmahnsperre,lbnr, bmwstausw,ZULETZT_GEMAHNT from buchung,bewohner
      where buchung.opbetrag<>0 and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS and MAHNALT = 'J'))) and splitnr is not null
      and bewohner.onr=buchung.onrsoll and bewohner.knr=buchung.ksoll
      and (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS)
      and bmahnsperre = 'N'
      and zzdatum<=:ABDATUM
      group by opnr,onrsoll, ksoll, kstrsoll, text, mahnstufe, datum, zzdatum,bmahnsperre,lbnr,bmwstausw,ZULETZT_GEMAHNT
      union
      select opnr,onrsoll, ksoll, kstrsoll, text, mahnstufe, datum, zzdatum,emahnsperre,LBNR, emwstausw,ZULETZT_GEMAHNT from buchung,eigentuemer
      where buchung.opbetrag<>0 and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS and MAHNALT = 'J'))) and splitnr is not null
      and eigentuemer.onr=buchung.onrsoll and eigentuemer.knr=buchung.ksoll
      and (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS)
      and emahnsperre = 'N'
      and zzdatum<=:ABDATUM
      group by opnr,onrsoll, ksoll, kstrsoll, text, mahnstufe, datum, zzdatum,emahnsperre,lbnr, emwstausw,ZULETZT_GEMAHNT
      order by 2, 3
      into :OPNR,ONR, KNR, KNRSTR, TEXT, STUFE, DATUM, ZZDATUM, :SPERRE,ILEV, gewerblich,ZULETZT_GEMAHNT do
     begin
      select opbetrag from splitbuch where bnr=:OPNR
      into BETRAG;
      IF ((ITMP<>KNR) OR (ITMP2<>ONR)) THEN
       BEGIN
        select saldo from KONTOSALDO_ALT(:ONR,:KNR,'01.01.9990','J','N') into RBETRAG;
        ITMP=KNR;
        ITMP2=ONR;
       END
      IF (RBETRAG<0) THEN
       BEGIN
        select KBEZ from konten where ONR=:ONR and KNR=:KNR into KONTONAME;
        KNRSTR=Left(KNRSTR || ' ' || KONTONAME, 100);
        if (BLEV='J') then
         SUSPEND;
        else
         begin
          if (ILEV is null) then
           SUSPEND;
         end
       END
     end
    END

    BEGIN
     --(BMAHNALT='N')
     for
      select opnr,onrsoll, ksoll, kstrsoll, text, mahnstufe, datum, zzdatum,bmahnsperre,lbnr, bmwstausw,ZULETZT_GEMAHNT from buchung,bewohner
      where buchung.opbetrag>0 and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS and MAHNALT = 'N'))) and splitnr is not null
      and bewohner.onr=buchung.onrsoll and bewohner.knr=buchung.ksoll
      and (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS)
      and bmahnsperre = 'N'
      and zzdatum<=:ABDATUM
      group by opnr,onrsoll, ksoll, kstrsoll, text, mahnstufe, datum, zzdatum,bmahnsperre,lbnr, bmwstausw,ZULETZT_GEMAHNT
      union
      select opnr,onrsoll, ksoll, kstrsoll, text, mahnstufe, datum, zzdatum,emahnsperre,LBNR, emwstausw,ZULETZT_GEMAHNT from buchung,eigentuemer
      where buchung.opbetrag>0 and (ONRSOLL>=:ONRVON and onrsoll<=:ONRBIS and (ONRSOLL in (select onr from objekte,verwalter where objekte.verwnr=verwalter.nr and onr<>0 and verwalter.nr>=:IVERWVON and verwalter.nr<=:IVERWBIS and MAHNALT = 'N'))) and splitnr is not null
      and eigentuemer.onr=buchung.onrsoll and eigentuemer.knr=buchung.ksoll
      and (MAHNSTUFE>=:MSVON and MAHNSTUFE<=:MSBIS)
      and emahnsperre = 'N'
      and zzdatum<=:ABDATUM
      group by opnr,onrsoll, ksoll, kstrsoll, text, mahnstufe, datum, zzdatum,emahnsperre,lbnr, emwstausw,ZULETZT_GEMAHNT
      order by 2, 3
      into :OPNR,ONR, KNR, KNRSTR, TEXT, STUFE, DATUM, ZZDATUM, :SPERRE,ILEV, GEWERBLICH,ZULETZT_GEMAHNT do
     begin
      select opbetrag from splitbuch where bnr=:OPNR
      into BETRAG;
      select KBEZ from konten where ONR=:ONR and KNR=:KNR into KONTONAME;
      KNRSTR=Left(KNRSTR || ' ' || KONTONAME, 100);
      IF (BETRAG>0) THEN
       BEGIN
        if (BLEV='J') then
         SUSPEND;
        else
         begin
          if (ILEV is null) then
           SUSPEND;
         end
       END
     end
    END
  END
END
