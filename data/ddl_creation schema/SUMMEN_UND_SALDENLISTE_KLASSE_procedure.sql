-- Prozedur: SUMMEN_UND_SALDENLISTE_KLASSE
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE SUMMEN_UND_SALDENLISTE_KLASSE
DECLARE VARIABLE IONR_ INTEGER;
DECLARE VARIABLE IRLPOS INTEGER;
DECLARE VARIABLE IRLVZ INTEGER;
DECLARE VARIABLE SALDO_S_NETTO NUMERIC(18, 2);
DECLARE VARIABLE SALDO_H_NETTO NUMERIC(18, 2);
DECLARE VARIABLE SALDO_KUM_S_NETTO NUMERIC(18, 2);
DECLARE VARIABLE SALDO_KUM_H_NETTO NUMERIC(18, 2);
DECLARE VARIABLE RUECKLAB NUMERIC(18, 2);
DECLARE VARIABLE TMP NUMERIC(18, 2);
BEGIN
 IF (KKLASSE_VON=71 OR KKLASSE_VON=30) THEN
  IONR_=0;
 ELSE
  IONR_=IONR;
 FOR SELECT KNR, KBEZ, RLPOS from KONTEN where (KKLASSE>=:KKLASSE_VON and KKLASSE<=:KKLASSE_BIS) and ONR=:IONR_ order by KNR into :KNR, :KBEZ, :IRLPOS do
  begin
   IF (IRLPOS IS NULL) THEN
    IRLPOS = 0;
   IF ((IEBWERTSACHKONTEN=1) OR ((IEBWERTSACHKONTEN=0) AND (:KKLASSE<>4) AND (:KKLASSE <>5))) THEN  /* HINWEIS : EB WERT beu Einnahme/Ausgabekonten nur wenn IEBWERTSACHKONRTEB = 1 */
    BEGIN
     select SUM(BETRAG), SUM((Betrag*100) / (100+MWST)) from buchung where (ONRSOLL=:IONR_ AND (ONRHABEN=:IONR or ONRHABEN=0)) and KSOLL=:KNR and (DATUM<:DTEBWERT) into :SALDO_S, :SALDO_S_NETTO;

     IF (ISBRUTTO=0) THEN
      SALDO_S=SALDO_S_NETTO;
     IF (SALDO_S IS NULL) then
      SALDO_S = 0;

     select SUM(BETRAG), SUM((Betrag*100) / (100+MWST)) from buchung where (ONRHABEN=:IONR_ AND (ONRSOLL=:IONR or ONRSOLL=0)) and KHABEN=:KNR and (DATUM<:DTEBWERT) into :SALDO_H, :SALDO_H_NETTO;

     IF (ISBRUTTO=0) THEN
      SALDO_H=SALDO_H_NETTO;
     IF (SALDO_H IS NULL) then
      SALDO_H = 0;
     /* wenn negativ dann S/H tauschen, weil es in der doppleten kein - gibt */
     IF ((SALDO_S < 0) and (SALDO_H < 0)) THEN
      BEGIN
       /* TMP = ABS(SALDO_S);
       SALDO_S = ABS(SALDO_H);
       SALDO_H = TMP;
       TMP = 0;*/
      END
     ELSE
      BEGIN
       IF (SALDO_S < 0) then
        begin
         SALDO_H = SALDO_H + ABS(SALDO_S);
         SALDO_S = 0;
        end
       IF (SALDO_H < 0) then
        begin
         SALDO_S = SALDO_S + ABS(SALDO_H);
         SALDO_H = 0;
        end
      END
     /* Beitragsverpflichtung in AB einrechnen */
     IF ((KKLASSE_VON = 27) and (IRLPOS>0)) THEN
      BEGIN
       select KONTO_VZ from rueckpos where NR=:IRLPOS INTO :IRLVZ;
       /* In dieser Abfrage muss das Bis Datum < sein. Also nicht <= Deshalb Tag -1*/
       select sum(sum_vz) from VZ_BE_DETAIL (:IONR_, '01.01.1950', dateadd (-1 day to :DTEBWERT), 200000, 299999, 'N') where vzpos=(:IRLVZ-60000) into :RUECKLAB;
       if (RUECKLAB is null) then
        RUECKLAB = 0;
       SALDO_H = SALDO_H + RUECKLAB;
     END
     EBWERT_S = SALDO_S;
     EBWERT_H = SALDO_H;
     EBWERT = EBWERT_S - EBWERT_H;
     IF (SOLL_PLUS='J') THEN
      BEGIN
       EBWERT = SALDO_S - SALDO_H;
       IF (EBWERT>=0) THEN
        BEGIN
         EBWERT_SH='S';
        END
       ELSE
        BEGIN
         EBWERT_SH='H';
         EBWERT = - EBWERT;
        END
      END
     ELSE
      BEGIN
       EBWERT = SALDO_H - SALDO_S;
       IF (EBWERT>=0) THEN
        BEGIN
         EBWERT_SH='H';
        END
       ELSE
        BEGIN
         EBWERT_SH='S';
         EBWERT = - EBWERT;
        END
      END
    END
   ELSE
    BEGIN
     EBWERT_SH='S';
     EBWERT = 0;
    END

    WITH cteB
    AS
    (
    SELECT b.BETRAG, b.MWST,
    CASE when b.Datum >= :DTVON
    then b.Datum
    else ''
    end as Datum
    FROM buchung b
    where
    (b.ONRSOLL = :IONR_ AND (b.ONRHABEN = :IONR or b.ONRHABEN = 0))
    and b.KSOLL = :KNR
    and b.DATUM <= :DTBIS
    )
    SELECT SUM(q.BETRAG), SUM((q.BETRAG * 100) / (100 + q.MWST))
    FROM cteB q
    WHERE  q.Datum <> ''
	into :SALDO_S, :SALDO_S_NETTO;

   IF (ISBRUTTO=0) THEN
    SALDO_S=SALDO_S_NETTO;
   IF (SALDO_S IS NULL) then
    SALDO_S = 0;

    WITH cteB
    AS
    (
    SELECT b.BETRAG, b.MWST,
    CASE when b.Datum >= :DTVON
    then b.Datum
    else ''
    end as Datum
    FROM buchung b
    where
    (b.ONRHABEN = :IONR_ AND (b.ONRSOLL = :IONR or b.ONRSOLL = 0))
    and b.KHABEN = :KNR
    and b.DATUM <= :DTBIS
    )
    SELECT SUM(q.BETRAG), SUM((q.BETRAG * 100) / (100 + q.MWST))
    FROM cteB q
    WHERE  q.Datum <> ''
    into :SALDO_H, :SALDO_H_NETTO;

   IF (ISBRUTTO=0) THEN
    SALDO_H=SALDO_H_NETTO;
   IF (SALDO_H IS NULL) then
    SALDO_H = 0;
   /* Beitragsverpflichtung in AB einrechnen */
   IF ((KKLASSE_VON = 27) and (IRLPOS>0)) THEN
    BEGIN
     select KONTO_VZ from rueckpos where NR=:IRLPOS INTO :IRLVZ;
     select sum(sum_vz) from VZ_BE_DETAIL (:IONR_, :DTVON, :DTBIS, 200000, 299999, 'N') where vzpos=(:IRLVZ-60000) into :RUECKLAB;
     if (RUECKLAB is null) then
      RUECKLAB = 0;
     SALDO_H = SALDO_H + RUECKLAB;
    END
   /* wenn negativ dann S/H tauschen, weil es in der doppleten kein - gibt */
   IF ((SALDO_S < 0) and (SALDO_H < 0)) THEN
    BEGIN
     /* TMP = ABS(SALDO_S);
     SALDO_S = ABS(SALDO_H);
     SALDO_H = TMP;
     TMP = 0; */
    END
   ELSE
    BEGIN
     IF (SALDO_S < 0) then
      begin
       SALDO_H = SALDO_H + ABS(SALDO_S);
       SALDo_S = 0;
      end
     IF (SALDO_H < 0) then
      begin
       SALDO_S = SALDO_S + ABS(SALDO_H);
       SALDo_H = 0;
      end
    END

    WITH cteB
    AS
    (
    SELECT b.BETRAG, b.MWST,
    CASE when b.Datum >= :DTEBWERT
    then b.Datum
    else ''
    end as Datum
    FROM buchung b
    where
    (b.ONRSOLL = :IONR_ AND (b.ONRHABEN = :IONR or b.ONRHABEN = 0))
    and b.KSOLL = :KNR
    and b.DATUM <= :DTBIS
    )
    SELECT SUM(q.BETRAG), SUM((q.BETRAG * 100) / (100 + q.MWST))
    FROM cteB q
    WHERE  q.Datum <> ''
	into :SALDO_KUM_S, :SALDO_KUM_S_NETTO;

   IF (ISBRUTTO=0) THEN
    SALDO_KUM_S=SALDO_KUM_S_NETTO;
   IF (SALDO_KUM_S IS NULL) then
    SALDO_KUM_S = 0;

    WITH cteB
    AS
    (
    SELECT b.BETRAG, b.MWST,
    CASE when b.Datum >= :DTEBWERT
    then b.Datum
    else ''
    end as Datum
    FROM buchung b
    where
    (b.ONRHABEN = :IONR_ AND (b.ONRSOLL = :IONR or b.ONRSOLL = 0))
    and b.KHABEN = :KNR
    and b.DATUM <= :DTBIS
    )
    SELECT SUM(q.BETRAG), SUM((q.BETRAG * 100) / (100 + q.MWST))
    FROM cteB q
    WHERE  q.Datum <> ''
    into :SALDO_KUM_H, SALDO_KUM_H_NETTO;

   IF (ISBRUTTO=0) THEN
    SALDO_KUM_H=SALDO_KUM_H_NETTO;
   IF (SALDO_KUM_H IS NULL) then
    SALDO_KUM_H = 0;
   /* Beitragsverpflichtung in AB einrechnen */
   IF ((KKLASSE_VON = 27) and (IRLPOS>0)) THEN
    BEGIN
     select KONTO_VZ from rueckpos where NR=:IRLPOS INTO :IRLVZ;
     select sum(sum_vz) from VZ_BE_DETAIL (:IONR_, :DTEBWERT, :DTBIS, 200000, 299999, 'N') where vzpos=(:IRLVZ-60000) into :RUECKLAB;
     if (RUECKLAB is null) then
      RUECKLAB = 0;
     SALDO_KUM_H = SALDO_KUM_H + RUECKLAB;
    END
   /* wenn negativ dann S/H tauschen, weil es in der doppleten kein - gibt */
   IF ((SALDO_KUM_S < 0) and (SALDO_KUM_H < 0)) THEN
    BEGIN
     /* TMP = ABS(SALDO_KUM_S);
     SALDO_KUM_S = ABS(SALDO_KUM_H);
     SALDO_KUM_H = TMP;
     TMP = 0; */
    END
   ELSE
    BEGIN
     IF (SALDO_KUM_S < 0) then
      begin
       SALDO_KUM_H = SALDO_KUM_H + ABS(SALDO_KUM_S);
       SALDO_KUM_S = 0;
      end
     IF (SALDO_KUM_H < 0) then
      begin
       SALDO_KUM_S = SALDO_KUM_S + ABS(SALDO_KUM_H);
       SALDO_KUM_H = 0;
      end
    END
   IF (SOLL_PLUS='J') THEN
    BEGIN
     IF (EBWERT_SH='S') THEN
      SALDO = SALDO_KUM_S - SALDO_KUM_H + EBWERT;
     ELSE
      SALDO = SALDO_KUM_S - SALDO_KUM_H - EBWERT;
     IF (SALDO>=0) THEN
      BEGIN
       SALDO_SH='S';
      END
     ELSE
      BEGIN
       SALDO_SH='H';
       SALDO = - SALDO;
      END
    END
   ELSE
    BEGIN
     IF (EBWERT_SH='H') THEN
      SALDO = SALDO_KUM_H - SALDO_KUM_S + EBWERT;
     ELSE
      SALDO = SALDO_KUM_H - SALDO_KUM_S - EBWERT;
     IF (SALDO>=0) THEN
      BEGIN
       SALDO_SH='H';
      END
     ELSE
      BEGIN
       SALDO_SH='S';
       SALDO = - SALDO;
      END
    END
   IF (NOT (EBWERT=0 AND SALDO_S =0 AND SALDO_H = 0 AND SALDO_KUM_S = 0 AND SALDO_KUM_H = 0 AND SALDO = 0)) THEN
    BEGIN
     SUSPEND;
    END
  end
 /* Beitragsverpflichtung in Kosten aufnehmen einrechnen */
 IF (KKLASSE = 5) THEN
  BEGIN
   for
    select KONTO_VZ, KBEZ from rueckpos, konten where rueckpos.ONR=:IONR_ and rueckpos.onr=konten.onr and RUECKPOS.KONTO_VZ=KONTEN.KNR INTO :KNR, :KBEZ
   do
    begin
     KBEZ = 'ZufÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼hrung ' || KBEZ;
     /* AB */
     EBWERT_H = 0;
     EBWERT_S = 0;
     /* In dieser Abfrage muss das Bis Datum < sein. Also nicht <= Deshalb Tag -1*/
     if (IEBWERTSACHKONTEN=1) then
      BEGIN
       select sum(sum_vz) from VZ_BE_DETAIL (:IONR_, '01.01.1950', dateadd (-1 day to :DTEBWERT), 200000, 299999, 'N') where vzpos=(:KNR-60000) into :EBWERT_S;
       if (EBWERT_S is null) then
        EBWERT_S = 0;
      END

     EBWERT = EBWERT_S;
     /* Monat/Quartal */
     SALDO_H = 0;
     select sum(sum_vz) from VZ_BE_DETAIL (:IONR_, :DTVON, :DTBIS, 200000, 299999, 'N') where vzpos=(:KNR-60000) into :SALDO_S;
     if (SALDO_S is null) then
      SALDO_S = 0;
     /* Kumuliert */
     SALDO_KUM_H = 0;
     select sum(sum_vz) from VZ_BE_DETAIL (:IONR_, :DTEBWERT, :DTBIS, 200000, 299999, 'N') where vzpos=(:KNR-60000) into :SALDO_KUM_S;
     if (SALDO_KUM_S is null) then
      SALDO_KUM_S = 0;
     /* SALDO */
     SALDO = SALDO_KUM_S + EBWERT;
     EBWERT_SH = 'S';
     SALDO_SH = 'S';
     /* FERTIG */
     IF (NOT (EBWERT=0 AND SALDO_S =0 AND SALDO_H = 0 AND SALDO_KUM_S = 0 AND SALDO_KUM_H = 0 AND SALDO = 0)) THEN
      BEGIN
       SUSPEND;
      END
    end
  END
end
