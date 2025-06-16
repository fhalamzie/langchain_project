-- Prozedur: EINNAHMEN_OBJ
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE EINNAHMEN_OBJ
DECLARE VARIABLE BETRAG NUMERIC (15, 2);
 DECLARE VARIABLE KNR INTEGER;
 DECLARE VARIABLE BSONST INTEGER;
 DECLARE VARIABLE Z1S NUMERIC (18, 2);
 DECLARE VARIABLE Z2S NUMERIC (18, 2);
 DECLARE VARIABLE Z3S NUMERIC (18, 2);
 DECLARE VARIABLE Z4S NUMERIC (18, 2);
 DECLARE VARIABLE Z5S NUMERIC (18, 2);
 DECLARE VARIABLE Z6S NUMERIC (18, 2);
 DECLARE VARIABLE Z7S NUMERIC (18, 2);
 DECLARE VARIABLE Z8S NUMERIC (18, 2);
 DECLARE VARIABLE GNS NUMERIC (18, 2);
 DECLARE VARIABLE Z1SG NUMERIC (18, 2);
 DECLARE VARIABLE Z2SG NUMERIC (18, 2);
 DECLARE VARIABLE Z3SG NUMERIC (18, 2);
 DECLARE VARIABLE Z4SG NUMERIC (18, 2);
 DECLARE VARIABLE Z5SG NUMERIC (18, 2);
 DECLARE VARIABLE Z6SG NUMERIC (18, 2);
 DECLARE VARIABLE Z7SG NUMERIC (18, 2);
 DECLARE VARIABLE Z8SG NUMERIC (18, 2);
 DECLARE VARIABLE GNSG NUMERIC (18, 2);
 DECLARE VARIABLE Z1SP NUMERIC (18, 2);
 DECLARE VARIABLE Z2SP NUMERIC (18, 2);
 DECLARE VARIABLE Z3SP NUMERIC (18, 2);
 DECLARE VARIABLE Z4SP NUMERIC (18, 2);
 DECLARE VARIABLE Z5SP NUMERIC (18, 2);
 DECLARE VARIABLE Z6SP NUMERIC (18, 2);
 DECLARE VARIABLE Z7SP NUMERIC (18, 2);
 DECLARE VARIABLE Z8SP NUMERIC (18, 2);
 DECLARE VARIABLE GNSP NUMERIC (18, 2);
 DECLARE VARIABLE Z1H NUMERIC (18, 2);
 DECLARE VARIABLE Z2H NUMERIC (18, 2);
 DECLARE VARIABLE Z3H NUMERIC (18, 2);
 DECLARE VARIABLE Z4H NUMERIC (18, 2);
 DECLARE VARIABLE Z5H NUMERIC (18, 2);
 DECLARE VARIABLE Z6H NUMERIC (18, 2);
 DECLARE VARIABLE Z7H NUMERIC (18, 2);
 DECLARE VARIABLE Z8H NUMERIC (18, 2);
 DECLARE VARIABLE GNH NUMERIC (18, 2);
 DECLARE VARIABLE Z1HG NUMERIC (18, 2);
 DECLARE VARIABLE Z2HG NUMERIC (18, 2);
 DECLARE VARIABLE Z3HG NUMERIC (18, 2);
 DECLARE VARIABLE Z4HG NUMERIC (18, 2);
 DECLARE VARIABLE Z5HG NUMERIC (18, 2);
 DECLARE VARIABLE Z6HG NUMERIC (18, 2);
 DECLARE VARIABLE Z7HG NUMERIC (18, 2);
 DECLARE VARIABLE Z8HG NUMERIC (18, 2);
 DECLARE VARIABLE GNHG NUMERIC (18, 2);
 DECLARE VARIABLE Z1HP NUMERIC (18, 2);
 DECLARE VARIABLE Z2HP NUMERIC (18, 2);
 DECLARE VARIABLE Z3HP NUMERIC (18, 2);
 DECLARE VARIABLE Z4HP NUMERIC (18, 2);
 DECLARE VARIABLE Z5HP NUMERIC (18, 2);
 DECLARE VARIABLE Z6HP NUMERIC (18, 2);
 DECLARE VARIABLE Z7HP NUMERIC (18, 2);
 DECLARE VARIABLE Z8HP NUMERIC (18, 2);
 DECLARE VARIABLE GNHP NUMERIC (18, 2);
 DECLARE VARIABLE Z1SOLL NUMERIC (18, 2);
 DECLARE VARIABLE Z2SOLL NUMERIC (18, 2);
 DECLARE VARIABLE Z3SOLL NUMERIC (18, 2);
 DECLARE VARIABLE Z4SOLL NUMERIC (18, 2);
 DECLARE VARIABLE Z5SOLL NUMERIC (18, 2);
 DECLARE VARIABLE Z6SOLL NUMERIC (18, 2);
 DECLARE VARIABLE Z7SOLL NUMERIC (18, 2);
 DECLARE VARIABLE Z8SOLL NUMERIC (18, 2);
 DECLARE VARIABLE GNSOLL NUMERIC (18, 2);
 DECLARE VARIABLE Z1BEZ NUMERIC (18, 2);
 DECLARE VARIABLE Z2BEZ NUMERIC (18, 2);
 DECLARE VARIABLE Z3BEZ NUMERIC (18, 2);
 DECLARE VARIABLE Z4BEZ NUMERIC (18, 2);
 DECLARE VARIABLE Z5BEZ NUMERIC (18, 2);
 DECLARE VARIABLE Z6BEZ NUMERIC (18, 2);
 DECLARE VARIABLE Z7BEZ NUMERIC (18, 2);
 DECLARE VARIABLE Z8BEZ NUMERIC (18, 2);
 DECLARE VARIABLE GNBEZ NUMERIC (18, 2);


BEGIN
 Z1S=0; Z2S=0;  Z3S=0; Z4S=0; Z5S=0; Z6S=0; Z7S=0; Z8S=0; GNS=0;
 Z1SG=0; Z2SG=0;  Z3SG=0; Z4SG=0; Z5SG=0; Z6SG=0; Z7SG=0; Z8SG=0; GNSG=0;
 Z1SP=0; Z2SP=0;  Z3SP=0; Z4SP=0; Z5SP=0; Z6SP=0; Z7SP=0; Z8SP=0; GNSP=0;
 Z1H=0; Z2H=0;  Z3H=0; Z4H=0; Z5H=0; Z6H=0; Z7H=0; Z8H=0; GNH=0;
 Z1HG=0; Z2HG=0;  Z3HG=0; Z4HG=0; Z5HG=0; Z6HG=0; Z7HG=0; Z8HG=0; GNHG=0;
 Z1HP=0; Z2HP=0;  Z3HP=0; Z4HP=0; Z5HP=0; Z6HP=0; Z7HP=0; Z8HP=0; GNHP=0;
 FOR SELECT ONR, BSONST from objekte where ONR>=:ONR_VON and ONR<=:ONR_BIS order by ONR into :ONR, :BSONST do
  BEGIN
   IF (BSONST=0 or BSONST=2) THEN
   BEGIN
   /* SOLL ALLE */
   LFDNR=1;
   Z1=0;
   Z2=0;
   Z3=0;
   Z4=0;
   Z5=0;
   Z6=0;
   Z7=0;
   Z8=0;
   GN=0;
   FOR SELECT SUM(BETRAG), KHABEN from buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND (ARTSOLL=60 AND (ARTHABEN>=10 AND ARTHABEN <=13))
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   and BETRAG<>0
   GROUP BY KHABEN
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=:BETRAG;
      END
    END
   Z1S=Z1S+Z1;Z2S=Z2S+Z2;Z3S=Z3S+Z3;Z4S=Z4S+Z4;Z5S=Z5S+Z5;Z6S=Z6S+Z6;Z7S=Z7S+Z7;Z8S=Z8S+Z8;GNS=GNS+GN;
   Z1SOLL=Z1;Z2SOLL=Z2;Z3SOLL=Z3;Z4SOLL=Z4;Z5SOLL=Z5;Z6SOLL=Z6;Z7SOLL=Z7;Z8SOLL=Z8;GNSOLL=GN;
   suspend;
   /* SOLL GEWERBLICH */
   LFDNR=2;
   Z1=0;
   Z2=0;
   Z3=0;
   Z4=0;
   Z5=0;
   Z6=0;
   Z7=0;
   Z8=0;
   GN=0;
   FOR SELECT SUM(BETRAG), KHABEN from buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND (ARTSOLL=60 AND (ARTHABEN>=10 AND ARTHABEN <=13))
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   and BETRAG<>0
   and MWST<>0
   GROUP BY KHABEN
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=:BETRAG;
      END
    END
   Z1SG=Z1SG+Z1;Z2SG=Z2SG+Z2;Z3SG=Z3SG+Z3;Z4SG=Z4SG+Z4;Z5SG=Z5SG+Z5;Z6SG=Z6SG+Z6;Z7SG=Z7SG+Z7;Z8SG=Z8SG+Z8;GNSG=GNSG+GN;
   suspend;
   /* SOLL NICHT GEWERBLICH */
   LFDNR=3;
   Z1=0;
   Z2=0;
   Z3=0;
   Z4=0;
   Z5=0;
   Z6=0;
   Z7=0;
   Z8=0;
   GN=0;
   FOR SELECT SUM(BETRAG), KHABEN from buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND (ARTSOLL=60 AND (ARTHABEN>=10 AND ARTHABEN <=13))
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   and BETRAG<>0
   and (MWST=0 OR MWST IS NULL)
   GROUP BY KHABEN
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=:BETRAG;
      END
    END
   Z1SP=Z1SP+Z1;Z2SP=Z2SP+Z2;Z3SP=Z3SP+Z3;Z4SP=Z4SP+Z4;Z5SP=Z5SP+Z5;Z6SP=Z6SP+Z6;Z7SP=Z7SP+Z7;Z8SP=Z8SP+Z8;GNSP=GNSP+GN;
   suspend;
   /* BEZAHLT ALLE */
   LFDNR=4;
   Z1=0;
   Z2=0;
   Z3=0;
   Z4=0;
   Z5=0;
   Z6=0;
   Z7=0;
   Z8=0;
   GN=0;
   /* KEIN SPLIT */
   FOR SELECT SUM(BETRAG), KNROP from Buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND (ARTOP>=10 AND ARTOP<=13)
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   AND (BANKNRSOLL IS NOT NULL)
   and BETRAG<>0
   GROUP BY KNROP
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=:BETRAG;
      END
    END /* FOR */
   /* SPLIT */
   for select sum(buchzahl.betrag), buchzahl.knr from buchzahl, buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND buchung.ARTOP=0
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   AND (BANKNRSOLL IS NOT NULL)
   and buchung.bnr=buchzahl.bnr
   group by buchzahl.knr
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=Z1+:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=Z2+:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=Z3+:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=Z4+:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=Z5+:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=Z6+:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=Z7+:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=Z8+:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=GN+:BETRAG;
      END
    END
   Z1H=Z1H+Z1;Z2H=Z2H+Z2;Z3H=Z3H+Z3;Z4H=Z4H+Z4;Z5H=Z5H+Z5;Z6H=Z6H+Z6;Z7H=Z7H+Z7;Z8H=Z8H+Z8;GNH=GNH+GN;
   Z1BEZ=Z1;Z2BEZ=Z2;Z3BEZ=Z3;Z4BEZ=Z4;Z5BEZ=Z5;Z6BEZ=Z6;Z7BEZ=Z7;Z8BEZ=Z8;GNBEZ=GN;
   suspend;
   /* BEZAHLT GEWERBLICH */
   LFDNR=5;
   Z1=0;
   Z2=0;
   Z3=0;
   Z4=0;
   Z5=0;
   Z6=0;
   Z7=0;
   Z8=0;
   GN=0;
   /* KEIN SPLIT */
   FOR SELECT SUM(BETRAG), KNROP from Buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND (ARTOP>=10 AND ARTOP<=13)
   AND (MWSTOP<>0)
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   AND (BANKNRSOLL IS NOT NULL)
   and BETRAG<>0
   GROUP BY KNROP
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=:BETRAG;
      END
    END /* FOR */
   /* SPLIT */
   for select sum(buchzahl.betrag), buchzahl.knr from buchzahl, buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND buchung.ARTOP=0
   AND buchzahl.mwstop<>0
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   AND (BANKNRSOLL IS NOT NULL)
   and buchung.bnr=buchzahl.bnr
   group by buchzahl.knr
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=Z1+:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=Z2+:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=Z3+:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=Z4+:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=Z5+:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=Z6+:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=Z7+:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=Z8+:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=GN+:BETRAG;
      END
    END
   Z1HG=Z1HG+Z1;Z2HG=Z2HG+Z2;Z3HG=Z3HG+Z3;Z4HG=Z4HG+Z4;Z5HG=Z5HG+Z5;Z6HG=Z6HG+Z6;Z7HG=Z7HG+Z7;Z8HG=Z8HG+Z8;GNHG=GNHG+GN;

   suspend;
   /* BEZAHLT NICHT GEWERBLICH */
   LFDNR=6;
   Z1=0;
   Z2=0;
   Z3=0;
   Z4=0;
   Z5=0;
   Z6=0;
   Z7=0;
   Z8=0;
   GN=0;
   /* KEIN SPLIT */
   FOR SELECT SUM(BETRAG), KNROP from Buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND (ARTOP>=10 AND ARTOP<=13)
   AND (MWSTOP=0)
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   AND (BANKNRSOLL IS NOT NULL)
   and BETRAG<>0
   GROUP BY KNROP
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=:BETRAG;
      END
    END /* FOR */
   /* SPLIT */
   for select sum(buchzahl.betrag), buchzahl.knr from buchzahl, buchung
   WHERE (ONRSOLL=:ONR OR ONRHABEN=:ONR)
   AND buchung.ARTOP=0
   AND buchzahl.mwstop=0
   AND (Datum>=:DTVON and Datum<=:DTBIS)
   AND (BANKNRSOLL IS NOT NULL)
   and buchung.bnr=buchzahl.bnr
   group by buchzahl.knr
   INTO :BETRAG, :KNR
   DO
    BEGIN
     IF (BETRAG IS NULL) THEN
      BETRAG=0;
     IF (BETRAG <> 0) THEN
      BEGIN
       IF (KNR=60000) then
        Z1=Z1+:BETRAG;
       ELSE
        IF (KNR=60010) then
         Z2=Z2+:BETRAG;
       ELSE
        IF (KNR=60020) then
         Z3=Z3+:BETRAG;
       ELSE
        IF (KNR=60030) then
         Z4=Z4+:BETRAG;
       ELSE
        IF (KNR=60040) then
         Z5=Z5+:BETRAG;
       ELSE
        IF (KNR=60050) then
         Z6=Z6+:BETRAG;
       ELSE
        IF (KNR=60060) then
         Z7=Z7+:BETRAG;
       ELSE
        IF (KNR=60070) then
         Z8=Z8+:BETRAG;
       ELSE
        IF (KNR=60090) then
         GN=GN+:BETRAG;
      END
    END
   Z1HP=Z1HP+Z1;Z2HP=Z2HP+Z2;Z3HP=Z3HP+Z3;Z4HP=Z4HP+Z4;Z5HP=Z5HP+Z5;Z6HP=Z6HP+Z6;Z7HP=Z7HP+Z7;Z8HP=Z8HP+Z8;GNHP=GNHP+GN;
   suspend;
   /* OP */
   LFDNR=7;
   Z1=Z1SOLL-Z1BEZ;
   Z2=Z2SOLL-Z2BEZ;
   Z3=Z3SOLL-Z3BEZ;
   Z4=Z4SOLL-Z4BEZ;
   Z5=Z5SOLL-Z5BEZ;
   Z6=Z6SOLL-Z6BEZ;
   Z7=Z7SOLL-Z7BEZ;
   Z8=Z8SOLL-Z8BEZ;
   GN=GNSOLL-GNBEZ;
   suspend;
   END /* BSONST */
  END /* FOR ONR */
 /* DUMMY FUER SUMMEN */
 ONR=1000;
 LFDNR=1;
 Z1=Z1S;Z2=Z2S;Z3=Z3S;Z4=Z4S;Z5=Z5S;Z6=Z6S;Z7=Z7S;Z8=Z8S;GN=GNS;
 SUSPEND;
 Z1=Z1SG;Z2=Z2SG;Z3=Z3SG;Z4=Z4SG;Z5=Z5SG;Z6=Z6SG;Z7=Z7SG;Z8=Z8SG;GN=GNSG;
 LFDNR=2;
 SUSPEND;
 Z1=Z1SP;Z2=Z2SP;Z3=Z3SP;Z4=Z4SP;Z5=Z5SP;Z6=Z6SP;Z7=Z7SP;Z8=Z8SP;GN=GNSP;
 LFDNR=3;
 SUSPEND;
 Z1=Z1H;Z2=Z2H;Z3=Z3H;Z4=Z4H;Z5=Z5H;Z6=Z6H;Z7=Z7H;Z8=Z8H;GN=GNH;
 LFDNR=4;
 SUSPEND;
 Z1=Z1HG;Z2=Z2HG;Z3=Z3HG;Z4=Z4HG;Z5=Z5HG;Z6=Z6HG;Z7=Z7HG;Z8=Z8HG;GN=GNHG;
 LFDNR=5;
 SUSPEND;
 LFDNR=6;
 Z1=Z1HP;Z2=Z2HP;Z3=Z3HP;Z4=Z4HP;Z5=Z5HP;Z6=Z6HP;Z7=Z7HP;Z8=Z8HP;GN=GNHP;
 SUSPEND;
 LFDNR=7;
 Z1=Z1S-Z1H;
 Z2=Z2S-Z2H;
 Z3=Z3S-Z3H;
 Z4=Z4S-Z4H;
 Z5=Z5S-Z5H;
 Z6=Z6S-Z6H;
 Z7=Z7S-Z7H;
 Z8=Z8S-Z8H;
 GN=GNS-GNH;
 SUSPEND;
END
