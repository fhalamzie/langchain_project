-- Prozedur: BEAUSEINZUG
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE BEAUSEINZUG
DECLARE VARIABLE DTBEGINN DATE;
DECLARE VARIABLE DTENDE DATE;
DECLARE VARIABLE SBNAME VARCHAR(80);
DECLARE VARIABLE SBVNAME VARCHAR(80);
DECLARE VARIABLE SBTITEL VARCHAR(30);
DECLARE VARIABLE OVON INTEGER;
DECLARE VARIABLE OBIS INTEGER;
DECLARE VARIABLE SFIRMA VARCHAR(1);
DECLARE VARIABLE SFIRMANAME VARCHAR(80);
DECLARE VARIABLE SBRIEFAN VARCHAR(40);
BEGIN
 if (:IONR<>-1) then
  begin
   OVON = :IONR;
   OBIS = :IONR;
  end
 else
  begin
   OVON = 1;
   OBIS = 999;  
  end
 /* */   
 if (:BBEW='J') then
  begin
   for    
    select onr,knr,ba.bewnr, ba.bname,ba.bvname,vbeginn,vende,vende,ba.btitel,
    ba.BFIRMA, ba.BFIRMANAME, ba.BBRIEFAN  
    from bewohner b, bewadr ba 
    where b.bewnr=ba.bewnr and knr<200000 and (onr>=:OVON and onr<=:OBIS) 
    order by ONR,KNR
    into :ONR,:KNR,:BEWNR, sbname,sbvname,dtBeginn,dtEnde,:gekdatum,sbtitel,SFIRMA, SFIRMANAME, SBRIEFAN
   do
    begin
     BESTR = ''; EINDATUM = null; AUSDATUM = null;
     /* */
     if (dtBeginn is not null) then
      if ((dtBeginn >= :DTVON) and (dtBeginn <= :DTBIS)) then
       begin
        EINDATUM = dtBeginn;
        AUSDATUM = dtEnde;
       end
     if (dtEnde is not null) then
      if ((dtEnde >= :DTVON) and (dtEnde <= :DTBIS)) then
       begin
        EINDATUM = dtBeginn;
        AUSDATUM = dtEnde;
       end
     /* */  
     IF ((SFIRMA = 'N') OR (SFIRMA IS NULL)) THEN
      BEGIN
       if ((sbvname is not null) and (sbname is not null)) then
        BESTR=TRIM(sbvname) || ' ' || TRIM(sbname);
       else
        begin
         if (sbvname is not null) then
          BESTR=TRIM(sbvname);
         if (sbname is not null) then
          BESTR=TRIM(sbname);
        end
       BESTR = TRIM(BESTR);
       /* */
       if ((sbtitel is not null) and (sbtitel <> '')) then
        BESTR = TRIM(sbtitel) || ' ' || BESTR;
      END   
     ELSE
      BEGIN
       IF (SBRIEFAN = 'Sehr geehrte Damen und Herren') THEN
        BESTR = SFIRMANAME;
       ELSE 
        BEGIN
         IF (SFIRMANAME IS NULL) THEN
          SFIRMANAME = '';
         IF (sbNAME IS NULL) THEN
          sbNAME = '';
         IF (sbVNAME IS NULL) THEN
          sbVNAME = ''; 
          
         IF (SFIRMANAME <> '') THEN
          BESTR = SFIRMANAME || ';'; 
          
         IF (sbNAME = '') THEN
          BESTR = BESTR || ' ' || sbVNAME;
         ELSE
          BESTR = BESTR || ' ' || sbNAME || ', ' || sbVNAME;
        END 
      END 

     BESTR = TRIM(BESTR);   
     /* */ 
     if ((EINDATUM is not null) or (AUSDATUM is not null)) then
      begin
       if (IART=1) then
        begin
         if (dtBeginn is not null) then
          if ((dtBeginn >= :DTVON) and (dtBeginn <= :DTBIS)) then
           SUSPEND;
        end
       else
        begin
         if (IART=2) then
          begin
           if (dtEnde is not null) then
            if ((dtEnde >= :DTVON) and (dtEnde <= :DTBIS)) then
             SUSPEND;
          end
         else
          SUSPEND;
        end
      end
    end    
  end
 else
  begin
   for
    select onr,knr,eigadr.eignr,ename,evname,ezbeginn,ezende,ezende, etitel,
     EFIRMA, EFIRMANAME, EBRIEFAN 
      from eigentuemer,eigadr where knr>200000 and (onr>=:OVON and onr<=:OBIS) and eigentuemer.eignr=eigadr.eignr order by ONR,KNR
   into :ONR,:KNR,:BEWNR, sbname,sbvname,dtBeginn,dtEnde,:gekdatum,sbtitel,SFIRMA, SFIRMANAME, SBRIEFAN
   do
    begin
     BESTR = ''; EINDATUM = null; AUSDATUM = null;
     if (dtBeginn is not null) then
      if ((dtBeginn >= :DTVON) and (dtBeginn <= :DTBIS)) then
       begin
        EINDATUM=dtBeginn;
        AUSDATUM=dtEnde;
       end
     if (dtEnde is not null) then
      if ((dtEnde >= :DTVON) and (dtEnde <= :DTBIS)) then
       begin
        EINDATUM=dtBeginn;
        AUSDATUM=dtEnde;
       end
       
     /* */  
      IF ((SFIRMA = 'N') OR (SFIRMA IS NULL)) THEN
       BEGIN
         if ((sbvname is not null) and (sbname is not null)) then
          BESTR=TRIM(sbvname) || ' ' || TRIM(sbname);
         else
          begin
           if (sbvname is not null) then
            BESTR=TRIM(sbvname);
           if (sbname is not null) then
            BESTR=TRIM(sbname);
          end
         BESTR = TRIM(BESTR);
         /* */
         if ((sbtitel is not null) and (sbtitel <> '')) then
          BESTR = TRIM(sbtitel) || ' ' || BESTR;
       END   
     ELSE
      BEGIN
       IF (SBRIEFAN = 'Sehr geehrte Damen und Herren') THEN
        BESTR = SFIRMANAME;
       ELSE 
        BEGIN
         IF (SFIRMANAME IS NULL) THEN
          SFIRMANAME = '';
         IF (sbNAME IS NULL) THEN
          sbNAME = '';
         IF (sbVNAME IS NULL) THEN
          sbVNAME = ''; 
          
         IF (SFIRMANAME <> '') THEN
          BESTR = SFIRMANAME || ';'; 
          
         IF (sbNAME = '') THEN
          BESTR = BESTR || ' ' || sbVNAME;
         ELSE
          BESTR = BESTR || ' ' || sbNAME || ', ' || sbVNAME;
        END 
      END 
     BESTR = TRIM(BESTR);   
     /* */        
     if ((EINDATUM is not null) or (AUSDATUM is not null)) then
      begin
       if (IART=1) then
        begin
         if (dtBeginn is not null) then
          if ((dtBeginn >= :DTVON) and (dtBeginn <= :DTBIS)) then
           SUSPEND;
        end
       else
        begin
         if (IART=2) then
          begin
           if (dtEnde is not null) then
            if ((dtEnde >= :DTVON) and (dtEnde <= :DTBIS)) then
             SUSPEND;
          end
         else
          SUSPEND;
        end
      end
    end
  end
END
