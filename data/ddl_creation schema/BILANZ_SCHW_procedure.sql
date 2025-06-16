-- Prozedur: BILANZ_SCHW
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE BILANZ_SCHW
DECLARE VARIABLE IKLASSE INTEGER;
DECLARE VARIABLE BANKNR INTEGER;
DECLARE VARIABLE KURZBEZ VARCHAR(15);
DECLARE VARIABLE SALDO NUMERIC (18, 2);
BEGIN
 IF (ONR_IN<>0) THEN
  BEGIN
   ONR=ONR_IN;
   FOR select knr,kbez,ea,bkart,bkbemerkung,kklasse
    from konten where (KKLASSE=20 or KKLASSE=22 or KKLASSE=27 or KKLASSE=24) and onr=:ONR_IN
    INTO :KNR,:BEZEICHNUNG,:EA,:ART,:BEMERKUNG,:IKLASSE
    DO
    BEGIN
     EXECUTE PROCEDURE KONTOSALDO_ALT(:ONR,:KNR,:DTSTICHTAG,'N','N') RETURNING_VALUES STAND;
     IF (STAND IS NULL) THEN
      STAND=0;
     if (IKLASSE<>27) then
      KLASSE='Aktiven';
     else
      KLASSE='Passiven';
     SUSPEND;
    END
  END
 ELSE
  BEGIN /* ALLE HÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦Ãƒâ€šÃ‚Â¾USER */
   /* Alle Banken */
   for select distinct banknr from objbanken into :banknr do
    begin
     STAND=0;
     for select ONR, KNR from objbanken where BANKNR=:BANKNR into :ONR, :KNR
      do
       begin
        select distinct onr, knr,kbez,ea,bkart,bkbemerkung,kklasse
        from konten where ONR=:ONR and KNR=:KNR
        INTO :ONR, :KNR,:BEZEICHNUNG,:EA,:ART,:BEMERKUNG,:IKLASSE;
        EXECUTE PROCEDURE KONTOSALDO_ALT(:ONR,:KNR,:DTSTICHTAG,'N','N') RETURNING_VALUES SALDO;
        IF (SALDO IS NULL) THEN
         SALDO=0;
        STAND=STAND+SALDO;
      END
     if (IKLASSE<>27) then
      KLASSE='Aktiven';
     else
      KLASSE='Passiven';
     select kurzbez from banken where nr=:banknr into :kurzbez;
     BEZEICHNUNG=BEZEICHNUNG || ' ' || kurzbez;
     SUSPEND;
    END
   /* restlichen nicht Bank */
   FOR select onr, knr,kbez,ea,bkart,bkbemerkung,kklasse
    from konten where (KKLASSE=22 or KKLASSE=27 or KKLASSE=24)
    INTO :ONR, :KNR,:BEZEICHNUNG,:EA,:ART,:BEMERKUNG,:IKLASSE
   DO
    BEGIN
     EXECUTE PROCEDURE KONTOSALDO_ALT(:ONR,:KNR,:DTSTICHTAG,'N','N') RETURNING_VALUES STAND;
     IF (STAND IS NULL) THEN
      STAND=0;
     if (IKLASSE<>27) then
      KLASSE='Aktiven';
     else
      KLASSE='Passiven';
     SUSPEND;
    END
  END
END
