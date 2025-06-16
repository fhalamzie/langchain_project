-- Prozedur: SEV_SOLLSTELLUNGEN
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE SEV_SOLLSTELLUNGEN
DECLARE VARIABLE BANKNR_BLZ INTEGER;
 DECLARE VARIABLE ITEMP INTEGER;
 DECLARE VARIABLE IANZ INTEGER;
 DECLARE VARIABLE RTEMP NUMERIC (15 ,2);
 DECLARE VARIABLE SLEV_ANZAHL INTEGER;
BEGIN
  IF (LBNR_IN>=0) THEN
  BEGIN
    SEVBANKNR=:IBANKNR;
    FOR
    SELECT LBNR, SUM (BETRAG), COUNT (LBNR) from sevmieten where LBNR = :LBNR_IN
     group by LBNR
    INTO
    :LBNR, :BETRAG, :SLEV_ANZAHL
    do
    begin
      /* mehrere verschiedene Objekte */
      IANZ=0;
      for
      select count (ONR),
      ONR
      from sevmieten
      where LBNR = :LBNR
      group by ONR
      into
      :ITEMP, ONR
      do
      begin
        IANZ=IANZ+1;
      end
      IF (IANZ>1) THEN
      ONR=NULL;
      /* mehrere verschiedene Vertraege */
      IANZ=0;
      for
      select count (SEVKNR),
      SEVKNR
      from sevmieten
      where LBNR = :LBNR
      group by ONR,
      SEVKNR
      into
      :ITEMP, SEVKNR
      do
      begin
        IANZ=IANZ+1;
      end
      IF (IANZ>1) THEN
      SEVKNR=NULL;
      for
      select SLEVDATUM,
      KNR,
      BETRAG,
      BNR,
      BELEGNR
      from sevmieten
      where LBNR = :LBNR
      into
      DATUM, :ITEMP, :RTEMP, :BNR, :BELEGNR
      do
      begin
        IF ((ITEMP<60 AND RTEMP>=0) OR (ITEMP>=60 AND RTEMP < 0)) THEN
        VZ='-';
        else
        VZ='+';
      end
      /* mehrere verschiedene Datumsangaben */
      IANZ=0;
      IF (DATUM IS NULL) THEN
      BEGIN
        for
        select DATUM
        from sevmieten
        where LBNR = :LBNR
        group by DATUM
        into
        DATUM
        do
        begin
          IANZ=IANZ+1;
        end
        IF (IANZ>1) THEN
        DATUM=NULL;
      END
      /* vorzeichen feststellen */
      IF (VZ='-') then
      TEXT='Sammler (ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“berweisungen: ' || CAST(SLEV_ANZAHL AS VARCHAR(10)) || ')'
      ;
      ELSE
      TEXT='Sammler (Lastschriften: ' || CAST(SLEV_ANZAHL AS VARCHAR(10)) || ')'
      ;
      SUSPEND;
    end
  END
  ELSE
  BEGIN
    IF (SBLZ<>' ') THEN
    BEGIN
      FOR
      SELECT NR
      from BANKEN
      where BLZ = :SBLZ or
      BIC = :SBLZ
      into
      :BANKNR_BLZ
      do
      begin
        /* Sammler */
        SEVBANKNR=:BANKNR_BLZ;
        FOR
        SELECT LBNR,
        SUM (BETRAG),
        COUNT (LBNR)
        from sevmieten
        where SEVBANKNR = :BANKNR_BLZ and
        LBNR IS NOT NULL and
          (STATUS >= :STATUSVON and
          STATUS <= :STATUSBIS)
        group by LBNR
        INTO
        :LBNR, :BETRAG, :SLEV_ANZAHL
        do
        begin
          /* mehrere verschiedene Objekte */
          IANZ=0;
          for
          select count (ONR),
          ONR
          from sevmieten
          where LBNR = :LBNR
          group by ONR
          into
          :ITEMP, ONR
          do
          begin
            IANZ=IANZ+1;
          end
          IF (IANZ>1) THEN
          ONR=NULL;
          /* mehrere verschiedene Vertraege */
          IANZ=0;
          for
          select count (SEVKNR),
          SEVKNR
          from sevmieten
          where LBNR = :LBNR
          group by ONR,
          SEVKNR
          into
          :ITEMP, SEVKNR
          do
          begin
            IANZ=IANZ+1;
          end
          IF (IANZ>1) THEN
          SEVKNR=NULL;
          for
          select SLEVDATUM,
          KNR,
          BETRAG,
          BNR
          from sevmieten
          where LBNR = :LBNR
          into
          DATUM, :ITEMP, :RTEMP, :BNR
          do
          begin
            IF ((ITEMP<60 AND RTEMP>=0) OR (ITEMP>=60 AND RTEMP < 0)) THEN
            VZ='-';
            else
            VZ='+';
          end
          /* mehrere verschiedene Datumsangaben */
          IANZ=0;
          IF (DATUM IS NULL) THEN
          BEGIN
            for
            select DATUM
            from sevmieten
            where LBNR = :LBNR
            group by DATUM
            into
            DATUM
            do
            begin
              IANZ=IANZ+1;
            end
            IF (IANZ>1) THEN
            DATUM=NULL;
          END
          /* vorzeichen feststellen */
          IF (VZ='-') then
          TEXT='Sammler (ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“berweisungen: ' || CAST(SLEV_ANZAHL AS VARCHAR(10)) ||
          ')';
          ELSE
          TEXT='Sammler (Lastschriften: ' || CAST(SLEV_ANZAHL AS VARCHAR(10)) ||
          ')';
          SUSPEND;
        end
        SLEV_ANZAHL=NULL;
        LBNR=NULL;
        FOR
        SELECT BNR,
        ONR,
        KNR,
        SEVKNR,
        DATUM,
        BELEGNR,
        BETRAG,
        TEXT,
        JAHRMONAT,
        STATUS,
        SEVBANKNR,
        LBNR,
        LIEFKNR,
        MWST,
        SLEVDATUM
        from sevmieten
        where SEVBANKNR = :BANKNR_BLZ and
        LBNR IS NULL and
          (STATUS >= :STATUSVON and
          STATUS <= :STATUSBIS)
        INTO
        :BNR, :ONR, :KNR, :SEVKNR, :DATUM, :BELEGNR, :BETRAG, :TEXT,
        :JAHRMONAT, :STATUS, :SEVBANKNR, :LBNR, :LIEFKNR, :MWST, :SLEVDATUM
        do
        BEGIN
          IF ((KNR<60 AND BETRAG>=0) OR (KNR>=60 AND BETRAG < 0)) THEN
          VZ='-';
          else
          VZ='+';
          SUSPEND;
        END
      end
    END /* pro BLZ */
    ELSE
    BEGIN /* pro konto */
      /* Sammler */
      SEVBANKNR=:IBANKNR;
      FOR
      SELECT LBNR,
      SUM (BETRAG),
      COUNT (LBNR)
      from sevmieten
      where SEVBANKNR = :IBANKNR and
      LBNR IS NOT NULL and
        (STATUS >= :STATUSVON and
        STATUS <= :STATUSBIS)
      group by LBNR
      INTO
      :LBNR, :BETRAG, :SLEV_ANZAHL
      do
      begin
        /* mehrere verschiedene Objekte */
        IANZ=0;
        for
        select count (ONR),
        ONR
        from sevmieten
        where LBNR = :LBNR
        group by ONR
        into
        :ITEMP, ONR
        do
        begin
          IANZ=IANZ+1;
        end
        IF (IANZ>1) THEN
        ONR=NULL;
        /* mehrere verschiedene Vertraege */
        IANZ=0;
        for
        select count (SEVKNR),
        SEVKNR
        from sevmieten
        where LBNR = :LBNR
        group by ONR,
        SEVKNR
        into
        :ITEMP, SEVKNR
        do
        begin
          IANZ=IANZ+1;
        end
        IF (IANZ>1) THEN
        SEVKNR=NULL;
        for
        select SLEVDATUM,
        KNR,
        BETRAG,
        BNR
        from sevmieten
        where LBNR = :LBNR
        into
        DATUM, :ITEMP, :RTEMP, :BNR
        do
        begin
          IF ((ITEMP<60 AND RTEMP>=0) OR (ITEMP>=60 AND RTEMP < 0)) THEN
          VZ='-';
          else
          VZ='+';
        end
        /* mehrere verschiedene Datumsangaben */
        IANZ=0;
        IF (DATUM IS NULL) THEN
        BEGIN
          for
          select DATUM
          from sevmieten
          where LBNR = :LBNR
          group by DATUM
          into
          DATUM
          do
          begin
            IANZ=IANZ+1;
          end
          IF (IANZ>1) THEN
          DATUM=NULL;
        END
        /* vorzeichen feststellen */
        IF (VZ='-') then
        TEXT='Sammler (ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã¢â‚¬Å“berweisungen: ' || CAST(SLEV_ANZAHL AS VARCHAR(10)) ||
        ')';
        ELSE
        TEXT='Sammler (Lastschriften: ' || CAST(SLEV_ANZAHL AS VARCHAR(10)) ||
        ')';
        SUSPEND;
      end
      SLEV_ANZAHL=NULL;
      LBNR=NULL;
      FOR
      SELECT BNR,
      ONR,
      KNR,
      SEVKNR,
      DATUM,
      BELEGNR,
      BETRAG,
      TEXT,
      JAHRMONAT,
      STATUS,
      SEVBANKNR,
      LBNR,
      LIEFKNR,
      MWST,
      SLEVDATUM
      from sevmieten
      where SEVBANKNR = :IBANKNR and
      LBNR IS NULL and
        (STATUS >= :STATUSVON and
        STATUS <= :STATUSBIS)
      INTO
      :BNR, :ONR, :KNR, :SEVKNR, :DATUM, :BELEGNR, :BETRAG, :TEXT, :JAHRMONAT,
      :STATUS, :SEVBANKNR, :LBNR, :LIEFKNR, :MWST, :SLEVDATUM
      do
      BEGIN
        IF ((KNR<60 AND BETRAG>=0) OR (KNR>=60 AND BETRAG < 0)) THEN
        VZ='-';
        else
        VZ='+';
        SUSPEND;
      END
    END /* pro konto */
  END /* LBNR>=0 */
END
