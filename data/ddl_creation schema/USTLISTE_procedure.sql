-- Prozedur: USTLISTE
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE USTLISTE
DECLARE VARIABLE KONTO INTEGER;
DECLARE VARIABLE KKLASSE INTEGER;
DECLARE VARIABLE KEINNAHME CHAR(1);
DECLARE VARIABLE IMWSTART INTEGER;
DECLARE VARIABLE IPROZ_UST NUMERIC(15, 2);
DECLARE VARIABLE IS_HAUSTYP INTEGER;
DECLARE VARIABLE KBEW1 CHAR(1);
DECLARE VARIABLE KBEW2 CHAR(1);
BEGIN
 ANRECH_PROZ=100;
 AUS=0;
 IF (VON_ONR=BIS_ONR) THEN
  ISAMMEL=0;
 ELSE
  ISAMMEL=1;
 FOR SELECT ONR, BSONST, HUWERT from OBJEKTE
 WHERE ONR>=:VON_ONR and ONR<=:BIS_ONR
 INTO :ONR, :IS_HAUSTYP, :IPROZ_UST
 DO
  BEGIN
   IF (IS_HAUSTYP = 0) THEN
    BEGIN
     KBEW1='J';
     KBEW2='J';
    END
   ELSE
    IF (IS_HAUSTYP = 1) THEN
     BEGIN
      KBEW1='N';
      KBEW2='N';
    END
   ELSe
    BEGIN
     KBEW1='J';
     KBEW2='N';
    END
   /*
   /* Alle E/K Konten */
   /*               */
   FOR SELECT KNR, KNRSTR, KBEZ, IFREI1, KKLASSE from konten
   where ONR=:ONR AND (KKLASSE<20 or (KKLASSE>=110 and KKLASSE<=580)) AND (KBEW=:KBEW1 OR KBEW=:KBEW2) AND KNR<>0
   INTO :KNR, :KNRSTR, :KBEZ, IMWSTART, KKLASSE
    DO
     begin
      for select UST_PROZ, SUM(UST), SUM(NETTO), SUM(BRUTTO) from
       USTLISTE_KONTO(:DTVON, :DTBIS, :ONR, :KNR, :KKLASSE, :IST_BUCHHALTUNG)
       group by ust_proz
      INTO :UST_PROZ, :UST, :NETTO, :BRUTTO
       DO
        BEGIN
         /* RL-VZ immer ohne Steuer */
         if ((KKLASSE>=110 and KKLASSE<=580)) then
          begin
           UST_PROZ = 0;
           UST = 0;
           NETTO = BRUTTO;
          end
         /*  */
         IF (KKLASSE=1) THEN
          BEGIN
           AUS=1;
           POS=20;
           IF (IMWSTART=0) THEN
            ANRECH_PROZ=0;   /* 0% anrechenbar */
           ELSE
            IF (IMWSTART=1) THEN
             ANRECH_PROZ=100;  /* 100% anrechenbar */
            ELSE
             IF (IMWSTART=2) THEN
              ANRECH_PROZ=IPROZ_UST; /* lt. Anteil Haus */
           UST_ANRECH=-(UST * ANRECH_PROZ / 100);
           UST=-UST;
          END
         ELSE  /* Einnahmen */
          BEGIN
           IF (KKLASSE=19) THEN
            BEGIN
             POS=20;
             IF (IMWSTART=0) THEN
              ANRECH_PROZ=0;   /* 0% anrechenbar */
             ELSE
              IF (IMWSTART=1) THEN
               ANRECH_PROZ=100;  /* 100% anrechenbar */
              ELSE
               IF (IMWSTART=2) THEN
                ANRECH_PROZ=IPROZ_UST; /* lt. Anteil Haus */
             UST_ANRECH=UST * ANRECH_PROZ / 100;
            END
           ELSE
            BEGIN
             POS=(KNR-60000)/10 + 1;
             ANRECH_PROZ=100;
             UST_ANRECH=UST;
             IF (IST_BUCHHALTUNG='J') THEN
              KNRSTR='Debitor';
            END
           AUS=0;
          END
         SUSPEND;
        END
     end /* Konto */
  end /* objekt */
END
