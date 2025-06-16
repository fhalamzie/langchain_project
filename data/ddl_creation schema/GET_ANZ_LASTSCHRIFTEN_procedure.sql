-- Prozedur: GET_ANZ_LASTSCHRIFTEN
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE GET_ANZ_LASTSCHRIFTEN
DECLARE VARIABLE IANZ integer;
BEGIN
 IANZ=0;
 IF (IS_DTA='N') THEN
  BEGIN
   IF (A_BLZ<>'') THEN     /* PRO BLZ */
   FOR SELECT
    COUNT(BNR) from buchung
    WHERE (ARTSOLL=60 or ARTSOLL=62) and OPBETRAG>0.001 and LBNR IS NULL and SPLITNR IS NULL
     and LASTBANK IN (SELECT BANKEN.NR FROM BANKEN  WHERE ((BANKEN.BLZ=:A_BLZ) or (BANKEN.BIC=:A_BLZ)) AND BANKEN.ART=0)
   UNION
    SELECT COUNT(buchung.BNR) from buchung, splitbuch
    WHERE (ARTSOLL=60 or ARTSOLL=62) and splitbuch.OPBETRAG>0.001 and LBNR IS NULL
    and LASTBANK IN (SELECT BANKEN.NR FROM BANKEN  WHERE BANKEN.BLZ=:A_BLZ AND BANKEN.ART=0)
    and SPLITNR IS  NOT NULL
    AND buchung.bnr=splitbuch.bnr
    INTO :ANZ
   DO
    IANZ=IANZ+ANZ;
   ELSE
   /* PRO KONTO */
   /*           */
     FOR SELECT
      COUNT(BNR) from buchung
      WHERE (ARTSOLL=60 or ARTSOLL=62) and OPBETRAG>0.001 and LBNR IS NULL and LASTBANK=:A_KONTO and SPLITNR IS NULL
      UNION
      SELECT COUNT(buchung.BNR) from buchung, splitbuch
      WHERE (ARTSOLL=60 or ARTSOLL=62) and splitbuch.OPBETRAG>0.001 and LBNR IS NULL and LASTBANK=:A_KONTO and SPLITNR IS  NOT NULL
      AND buchung.bnr=splitbuch.bnr
      INTO :ANZ
      DO
       IANZ=IANZ+ANZ;
   ANZ=IANZ;
   SUSPEND;
  END
 ELSE
  BEGIN
   IF (A_BLZ<>'') THEN     /* PRO BLZ */
    BEGIN
     select COUNT(BNR) from buchung
     WHERE (ARTSOLL=60 or ARTSOLL=62) and OPBETRAG>0.001 and LBNR IS NULL and (LASTERZEUGT=0 or LASTERZEUGT IS NULL)
     and LASTBANK IN (SELECT BANKEN.NR FROM BANKEN  WHERE ((BANKEN.BLZ=:A_BLZ) or (BANKEN.BIC=:A_BLZ)) AND BANKEN.ART=0)
     into :ANZ;
    END
   ELSE
    BEGIN
     FOR SELECT /* PRO KONTO */
      COUNT(BNR) from buchung
      WHERE (ARTSOLL=60 or ARTSOLL=62) and OPBETRAG>0.001 and LBNR IS NULL and LASTBANK=:A_KONTO and SPLITNR IS NULL and (LASTERZEUGT=0 or LASTERZEUGT IS NULL)
      UNION
      SELECT COUNT(buchung.BNR) from buchung, splitbuch
      WHERE (ARTSOLL=60 or ARTSOLL=62) and splitbuch.OPBETRAG>0.001 and LBNR IS NULL and LASTBANK=:A_KONTO and SPLITNR IS  NOT NULL and (LASTERZEUGT=0 or LASTERZEUGT IS NULL)
      AND buchung.bnr=splitbuch.bnr
      INTO :ANZ
      DO
       IANZ=IANZ+ANZ;
      ANZ=IANZ;
    END
   SUSPEND;
  END
END
