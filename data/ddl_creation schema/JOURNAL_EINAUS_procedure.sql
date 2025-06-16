-- Prozedur: JOURNAL_EINAUS
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE JOURNAL_EINAUS
DECLARE VARIABLE KLASSE INTEGER;
DECLARE VARIABLE ITMP INTEGER;
BEGIN
 ONR =: IONR;
 AUSGABE = 0;
 IF (ART = 1) THEN
  DRUCKEN = 0;
 ELSE
  DRUCKEN = 1;
 
 /* EINNAHMEN */
 FOR 
  SELECT KNR, KKLASSE from konten where ONR=:IONR and ((KKLASSE>=60 AND KKLASSE<=62) OR (KKLASSE=19)) and KNR>=:EKNRVON AND KNR<=:EKNRBIS ORDER BY KKLASSE
 INTO :GROUPKNR, :KLASSE
 do
  begin /* for Konten */
   FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN,
              BELEGNR, TEXT, MWST, BETRAG, ONR, KSTRHABEN, KSTRSOLL
   from journal_einaus_k (:ONR,:GROUPKNR,:DTVON,:DTBIS,:KLASSE,'N')
   INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN,
        :BELEGNR, :TEXT, :MWST, :BETRAG, :ONR, :KSTRHABEN, :KSTRSOLL
   do
    SUSPEND;
  END
 
 /* AUSGABEN */
 AUSGABE = 1;
 IF (ART = 0) THEN
  DRUCKEN = 0;
 ELSE
  DRUCKEN = 1;
 FOR 
  SELECT KNR, KKLASSE from konten where ONR=:IONR and ((KKLASSE=1) or ((KKLASSE=27) and (RLPOS is not null))) and KNR>=:AKNRVON AND KNR<=:AKNRBIS ORDER BY KKLASSE
 INTO :GROUPKNR, :KLASSE
  do
   begin /* for Konten */
    IF (:KLASSE = 1) THEN
     BEGIN
      FOR SELECT BNR, DATUM, WDATUM, KSOLL, KHABEN,
                 BELEGNR, TEXT, MWST, BETRAG, ONR, KSTRHABEN, KSTRSOLL
      from journal_einaus_k (:ONR,:GROUPKNR,:DTVON,:DTBIS,:KLASSE,'N')
      INTO :BNR, :DATUM, :WDATUM, :KSOLL, :KHABEN,
           :BELEGNR, :TEXT, :MWST, :BETRAG, :ONR, :KSTRHABEN, :KSTRSOLL
      do
       SUSPEND;
     END
    ELSE
     BEGIN
      select KONTO_VZ from rueckpos where onr=:IONR and KNRP=:GROUPKNR INTO :ITMP;
      /* Beitragsverpflichtung in Saldo ALT aufnehmen */
      select sum(sum_vz) from VZ_BE_DETAIL (:IONR, :DTVON, :DTBIS, 200000, 299999, :BWDATUM) where vzpos=(:ITMP-60000) into :BETRAG;
      if (BETRAG is null) then
       BETRAG = 0;

      BNR = 0;
      ONR =: IONR;
      DATUM = :DTBIS;
      WDATUM = :DTBIS;
      KSOLL = GROUPKNR;
      KHABEN = GROUPKNR;
      BELEGNR = 0;
      TEXT = 'Beitragsverpflichtung zur ErhaltungsrÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklage';
      MWST = 0;
      KSTRHABEN = GROUPKNR;
      KSTRSOLL = GROUPKNR;
      
      IF (BETRAG <> 0) THEN
       SUSPEND;
     END    
   END
END
