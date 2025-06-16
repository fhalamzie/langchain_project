-- Prozedur: GET_SOLLSTBEZ
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE GET_SOLLSTBEZ
DECLARE VARIABLE WHGBEZ VARCHAR(25);
DECLARE VARIABLE SNAME VARCHAR(80);
DECLARE VARIABLE SVNAME VARCHAR(80);
DECLARE VARIABLE SOBEZ VARCHAR(100);
BEGIN
 IF (ISDEBITOR=1) THEN
  BEGIN
   SELECT OBEZ from objekte
   WHERE ONR=:ONR
   INTO :SOBEZ;
   IF (:KNR<200000) THEN
     BEGIN
        SELECT EBEZ from wohnung
        WHERE ONR=:ONR and BKNR=:KNR
        INTO :WHGBEZ;
        select ba.BNAME, ba.BVNAME, ba.BSTR || ', ' || ba.BPLZORT from bewohner b,bewadr ba
        where b.bewnr=ba.bewnr and ONR=:ONR and KNR=:KNR
        into :SNAME, :SVNAME, BEZ;
     END
    ELSE
     BEGIN /* EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer */
      SELECT EBEZ from wohnung
      WHERE ONR=:ONR and EKNR=:KNR
      INTO :WHGBEZ;
      select ENAME, EVNAME, ESTR || ', ' || EPLZORT from eigadr, eigentuemer
      where EIGENTUEMER.ONR=:ONR and EIGENTUEMER.KNR=:KNR
      and EIGADR.EIGNR = EIGENTUEMER.EIGNR
      into :SNAME, :SVNAME, BEZ;
     END
    IF (:SVNAME IS NULL) then
     BEZ=:SNAME || ', ' || :BEZ;
    ELSE
     BEZ=:SNAME || ' ' || :SVNAME || ', ' || :BEZ;
     BEZ=:SOBEZ|| ' - ' || :WHGBEZ || ', ' || :BEZ;
   SUSPEND;
  END
 ELSE
  BEGIN
   SELECT NAME || ', ' || STRASSE || ' ' || PLZ || ' ' || ORT || TEL1 from lieferan
   where LIEFKNR=:KNR
   INTO
    BEZ;
   SUSPEND;
  END
END
