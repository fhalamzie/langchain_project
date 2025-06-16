-- Prozedur: VERSAMMLUNG_ERG
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE VERSAMMLUNG_ERG
DECLARE VARIABLE ISUM1 NUMERIC(18, 4);
DECLARE VARIABLE ISUM2 NUMERIC(18, 4);
DECLARE VARIABLE ISUM3 NUMERIC(18, 4);
DECLARE VARIABLE ISUM NUMERIC(18, 4);
DECLARE VARIABLE IANZ1 INTEGER;
DECLARE VARIABLE IANZ2 INTEGER;
DECLARE VARIABLE IANZ3 INTEGER;
DECLARE VARIABLE IABWESEND INTEGER;
DECLARE VARIABLE IALLE NUMERIC(18, 4);
BEGIN
 select count(*) from vereig where ONR=:IONR and VERNR=:IVERNR and abwesend>0 into IABWESEND;
 /* */
 FOR select versammlung.vernr,versammlung.onr,obez,oplzort,ostr,verdat,
  htp,utp,kurzbez, id,text,text_protokoll,abstimmung,doppqual,abstimmung_art
  from versammlung, verthemen
  where versammlung.onr=:IONR and verthemen.vernr=:IVERNR and versammlung.vernr=verthemen.vernr and versammlung.onr=verthemen.onr
  order by htp,utp
 INTO :VERNR,:ONR,:OBJBEZ,:OBJPLZORT,:OBJSTR,:VDATUM,:HTP,:UTP,:KURZBEZ,:ID,:TEXT,:TEXT_PROTOKOLL, :ABSTIMMUNG,:DOPPQUALI,:ABSTIMMUNG_ART
  DO 
   BEGIN
    BESCHLUSS_TEXT = '';
    ANTEILESUM1=0;
    ANTEILESUM2=0;
    ANTEILESUM3=0;
    ANZPERSJA=0;
    ANZPERSNEIN=0;
    ANZPERSENTHALTUNG=0;
          
    if (ABSTIMMUNG_ART>0) then
     begin
      for select sum(vereig.eiganteil) as Anteil, count(vererg.sja) as ANZPERS from vererg,vereig,verthemen
      where vererg.vernr=:IVERNR and vererg.onr=:IONR and vererg.eigid=vereig.nr and vereig.onr=vererg.onr and vererg.vernr=vereig.vernr and vererg.themaid=verthemen.id
      and vererg.themaid=:ID and vererg.sja='J'
      group by vererg.themaid,verthemen.kurzbez
      into :ISUM1, :IANZ1
       do
        begin
         ANTEILESUM1=ISUM1;
         ANZPERSJA=IANZ1;
        end

      for select sum(vereig.eiganteil) as Anteil, count(vererg.snein) as ANZPERS from vererg,vereig,verthemen
      where vererg.vernr=:IVERNR and vererg.onr=:IONR and vererg.eigid=vereig.nr and vereig.onr=vererg.onr and vererg.vernr=vereig.vernr and vererg.themaid=verthemen.id
      and vererg.themaid=:ID and vererg.snein='J'
      group by vererg.themaid,verthemen.kurzbez
      into :ISUM2, :IANZ2
       do
        begin
         ANTEILESUM2=ISUM2;
         ANZPERSNEIN=IANZ2;
        end

      for select sum(vereig.eiganteil) as Anteil, count(vererg.senthaltung) as ANZPERS from vererg,vereig,verthemen
      where vererg.vernr=:IVERNR and vererg.onr=:IONR and vererg.eigid=vereig.nr and vereig.onr=vererg.onr and vererg.vernr=vereig.vernr and vererg.themaid=verthemen.id
      and vererg.themaid=:ID and vererg.senthaltung='J'
      group by vererg.themaid,verthemen.kurzbez
      into :ISUM3, :IANZ3
       do
        begin
         ANTEILESUM3=ISUM3;
         ANZPERSENTHALTUNG=IANZ3;
        end
       
        
      for select sum(vereig.eiganteil) as Anteil
      from vererg,vereig,verthemen
      where vererg.vernr=:IVERNR and vererg.onr=:IONR and vererg.eigid=vereig.nr and vereig.onr=vererg.onr and vererg.vernr=vereig.vernr and vererg.themaid=verthemen.id
      and vererg.themaid=:ID 
      group by vererg.themaid,verthemen.kurzbez
      into :ISUM
       do
        begin
         ANTEILEGESAMMT=ISUM;   
        end
        
        
        
        
      /* */
      if (ABSTIMMUNG_ART = 1) then /* BeschlÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ssen mit einfacher Mehrheit */ 
       BEGIN
        IF (BKOPF = 'N') THEN
         BEGIN
          IF (ANTEILESUM1 > ((ANTEILESUM1+ANTEILESUM2)/2)) THEN
           BESCHLUSS_TEXT = 'Beschluss aufgrund einfacher Mehrheit angenommen (die Ja-Stimmen sind hÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶her als die Nein-Stimmen)';
          ELSE
           BESCHLUSS_TEXT = 'Beschluss aufgrund einfacher Mehrheit nicht angenommen (die Ja-Stimmen sind niedriger als die Nein-Stimmen)';         
         END
        ELSE
         BEGIN  
          IF (ANZPERSJA > ((ANZPERSJA+ANZPERSNEIN)/2)) THEN
           BESCHLUSS_TEXT = 'Beschluss aufgrund einfacher Mehrheit angenommen (die Ja-Stimmen sind hÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶her als die Nein-Stimmen)';
          ELSE
           BESCHLUSS_TEXT = 'Beschluss aufgrund einfacher Mehrheit nicht angenommen (die Ja-Stimmen sind niedriger als die Nein-Stimmen)';
         END  
       END
      ELSE
       BEGIN
        if (ABSTIMMUNG_ART = 2) then /* BeschlÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼ssen mit doppelt qualifizierter Mehrheit */ 
         BEGIN
          IALLE = ANZPERSJA+ANZPERSNEIN+ANZPERSENTHALTUNG+IABWESEND;
          IF ((ANTEILESUM1 > (ANTEILEGESAMMT/2)) and (ANZPERSJA>=((IALLE/3)*2))) THEN
           BESCHLUSS_TEXT = 'Beschluss aufgrund doppelt qualifizierter Mehrheit angenommen (mehr als 50% aller Miteigentumsanteile und 2/3 aller Stimmberechtigten, inkl. Abwesende, haben mit Ja gestimmt)';
          ELSE
           BESCHLUSS_TEXT = 'Beschluss aufgrund doppelt qualifizierter Mehrheit nicht angenommen (weniger als 51% aller Miteigentumsanteile und 2/3 aller Stimmberechtigten, inkl. Abwesende, haben mit Ja gestimmt)';
         END
        ELSE
         BEGIN
          if (ABSTIMMUNG_ART = 3) then /* Einstimmiger Beschluss */ 
           BEGIN
            IF (ANZPERSJA = (ANZPERSJA + ANZPERSNEIN + ANZPERSENTHALTUNG)) THEN
             BEGIN
              BESCHLUSS_TEXT = 'Beschluss aufgrund Einstimmigkeit angenommen (alle Anwesenden haben mit Ja gestimmt)';
             END 
            ELSE
             BESCHLUSS_TEXT = 'Beschluss aufgrund fehlender Einstimmigkeit nicht angenommen (nicht alle der Anwesenden haben mit Ja gestimmt)';
           END
          ELSE
           BEGIN
            if (ABSTIMMUNG_ART = 4) then /* Allstimmiger Beschluss */ 
             BEGIN
              IF ((ANZPERSJA = (ANZPERSJA + ANZPERSNEIN + ANZPERSENTHALTUNG)) AND (IABWESEND = 0)) THEN
               BESCHLUSS_TEXT = 'Beschluss aufgrund Allstimmigkeit angenommen (keiner Abwesend und alle haben mit Ja gestimmt)';
              ELSE
               BESCHLUSS_TEXT = 'Beschluss aufgrund fehlender Allstimmigkeit nicht angenommen (durch Abwesenheit oder nicht alle haben mit Ja gestimmt)';
             END            
            ELSE
             BEGIN
              IF (ABSTIMMUNG_ART = 5) then /* Umlaufbeschluss*/
               BEGIN
                IF (ANZPERSJA=(ANZPERSJA+ANZPERSNEIN+ANZPERSENTHALTUNG+IABWESEND)) THEN
                 BESCHLUSS_TEXT = 'Beschluss aufgrund Allstimmigkeit angenommen (alle EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer haben mit Ja gestimmt)';
                ELSE
                 BESCHLUSS_TEXT = 'Beschluss aufgrund fehlender Allstimmigkeit nicht angenommen (nicht alle EigentÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼mer haben mit Ja gestimmt)';
               END
              ELSE
               BEGIN
                if (ABSTIMMUNG_ART = 6) then /* Baulichen VerÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤nderungen */ 
                 BEGIN
                  IALLE = ANZPERSJA+ANZPERSNEIN+ANZPERSENTHALTUNG; /* +IABWESEND - nicht gueltig */
                  IF ((ANTEILESUM1 > (ANTEILEGESAMMT/2)) and (ANZPERSJA>=((IALLE/3)*2))) THEN
                   BESCHLUSS_TEXT = 'Beschluss einer baulichen VerÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤nderungen angenommen (mehr als 50% aller Miteigentumsanteile und 2/3 aller Stimmberechtigten haben mit Ja gestimmt)';
                  ELSE
                   BEGIN
                    IF (ANTEILESUM1 > ((ANTEILESUM1+ANTEILESUM2)/2)) THEN
                     BESCHLUSS_TEXT = 'Beschluss einer baulichen VerÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤nderungen aufgrund einfacher Mehrheit angenommen (die Ja-Miteigentumsanteile sind hÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¶her als die Nein-Miteigentumsanteile)';
                    ELSE
                     BESCHLUSS_TEXT = 'Beschluss einer baulichen VerÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤nderungen aufgrund einfacher Mehrheit nicht angenommen (die Ja-Miteigentumsanteile sind niedriger als die Nein-Miteigentumsanteile)';  
                   END 
                 END 
               END 
             END           
           END   
         END        
       END
     end
    suspend;
   END
END
