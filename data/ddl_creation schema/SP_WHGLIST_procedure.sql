-- Prozedur: SP_WHGLIST
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE SP_WHGLIST
--Author RM
--Erstellt 03.03.2023
--Erstellt fÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼r die ZÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤hlerverwaltung
--Geandert 16.03.2023
--Null Werte abfangen
--Geandert 16.05.2023
--Null Werte abfangen
--
--Hier wird die BAdresse und die EAdresse gebildet
begin
  FOR
    with cteWhgList
    AS
    (
    SELECT
         wohnung.ONR
        ,wohnung.ENR
        ,bewohner.knr as BKNR
        ,eigentuemer.knr as EKNR
        ,wohnung.EBEZ
        ,wohnung.art
        ,bewohner.bewstatus
        ,bewohner.BLASTJA
        ,Right(1000000 + wohnung.ENR,3) as ENRSTR
        ,Right(1000000 + wohnung.ENR,3) || ' ' || wohnung.EBEZ as EBEZSTR
        ,case
           when bewadr.bname is Null then ''
           else bewadr.bname
         end as bname
        ,case
           when bewadr.bvname is Null then ''
           else bewadr.bvname
         end as bvname
        ,CASE
            WHEN bewadr.BFIRMA = 'J'
                THEN CASE
                        WHEN bewadr.BBriefAn = 'Sehr geehrte Damen und Herren'
                            THEN case 
                                   when NOT (bewadr.BFirmaName IS NULL) then bewadr.BFirmaName
                                   else ''
                                 end  
                        ELSE CASE
                                WHEN NOT (bewadr.BFirmaName IS NULL)
                                    THEN Trim(bewadr.BFirmaName) || CASE
                                            WHEN NOT (bewadr.BName IS NULL)
                                                THEN '; ' || Trim(bewadr.BName) || CASE
                                                        WHEN NOT (bewadr.BVName IS NULL)
                                                            THEN ', ' || TRIM(bewadr.BVName)
                                                        ELSE ''
                                                        END
                                            ELSE ''
                                            END
                                ELSE ''
                                END
                        END
            ELSE CASE
                    WHEN (
                            (Trim(bewadr.BNAME) <> '')
                            OR (Trim(bewadr.BVNAME) <> '')
                            )
                        THEN CASE
                                WHEN (Trim(bewadr.BNAME) <> '')
                                    THEN bewadr.BNAME || CASE
                                            WHEN Trim(bewadr.BVNAME) <> ''
                                                THEN ', ' || Trim(bewadr.BVNAME)
                                            ELSE ''
                                            END
                                ELSE CASE
                                        WHEN Trim(bewadr.BVNAME) <> ''
                                            THEN Trim(bewadr.BVNAME)
                                        ELSE ''
                                        END
                                END
                    ELSE ''
                    END
            END AS BAdresse
        ,bewadr.BFIRMA
        ,case
           when eigadr.ename is Null then ''
           else eigadr.ename
         end as ename
        ,case
           when eigadr.evname is Null then ''
           else eigadr.evname
         end as evname
        ,CASE
            WHEN eigadr.EFIRMA = 'J'
                THEN CASE
                        WHEN eigadr.EBriefAn = 'Sehr geehrte Damen und Herren'
                            THEN case 
                                   when NOT (eigadr.EFirmaName IS NULL) then eigadr.EFirmaName
                                   else ''
                                 end  
                        ELSE CASE
                                WHEN NOT (eigadr.EFirmaName IS NULL)
                                    THEN Trim(eigadr.EFirmaName) || CASE
                                            WHEN NOT (eigadr.EName IS NULL)
                                                THEN '; ' || Trim(eigadr.EName) || CASE
                                                        WHEN NOT (eigadr.EVNAME IS NULL)
                                                            THEN ', ' || TRIM(eigadr.EVName)
                                                        ELSE ''
                                                        END
                                            ELSE ''
                                            END
                                ELSE ''
                                END
                        END
            ELSE CASE
                    WHEN (
                            (Trim(eigadr.ENAME) <> '')
                            OR (Trim(eigadr.EVNAME) <> '')
                            )
                        THEN CASE
                                WHEN (Trim(eigadr.ENAME) <> '')
                                    THEN eigadr.ENAME || CASE
                                            WHEN Trim(eigadr.EVNAME) <> ''
                                                THEN ', ' || Trim(eigadr.EVNAME)
                                            ELSE ''
                                            END
                                ELSE CASE
                                        WHEN Trim(eigadr.EVNAME) <> ''
                                            THEN Trim(eigadr.EVNAME)
                                        ELSE ''
                                        END
                                END
                    ELSE ''
                    END
            END AS EAdresse
        ,eigadr.EFIRMA
        ,objekte.BSONST
        ,objekte.BKVON
        ,objekte.BKBIS

    FROM WOHNUNG
    INNER JOIN BEWOHNER ON wohnung.onr = bewohner.onr AND wohnung.bknr = bewohner.knr
    INNER JOIN EIGENTUEMER ON wohnung.onr = eigentuemer.onr AND wohnung.eknr = eigentuemer.knr
    INNER JOIN eigadr ON eigentuemer.eignr = eigadr.eignr
    INNER JOIN objekte ON objekte.onr = wohnung.onr
    INNER JOIN bewadr ON bewohner.bewnr = bewadr.bewnr
    WHERE wohnung.onr =:IONR

    UNION

	SELECT MAX(w.ONr) AS ONr
          ,0 AS ENR
          ,Null as BKNR
          ,Null as EKNR
          ,NULL AS EBEZ
          ,NULL AS art
          ,0 AS bewstatus
          ,Null as BLASTJA

          ,NULL AS ENRSTR
          ,' Objekt (AllgemeinzÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¤hler) ' AS EBEZSTR
          ,NULL AS bname
          ,NULL AS bvname
          ,NULL AS BAdresse
          ,NULL AS BFIRMA
          ,NULL AS ename
          ,NULL AS evname
          ,NULL AS EAdresse
          ,NULL AS EFIRMA
          ,Max(bsonst) AS bsonst
          ,Min(bkvon) AS bkvon
          ,MAX(bkbis) AS bkbis
	FROM WOHNUNG w
	INNER JOIN objekte	ON objekte.onr = w.onr
	WHERE w.onr = :IONR
    )
    Select
         ONr, ENr, BKNR, EKNR, EBEZ, ART,
         ENRSTR, EBEZSTR,
         BNAME, BVNAME, BADRESSE, BFIRMA,
         ENAME, EVNAME, EADRESSE, EFIRMA,
         BSONST, BKVON, BKBIS, BEWSTATUS

        ,case
           when BSonst = 0 then CASE
                                  when ENR = 0 then EBEZSTR
                                  when bewstatus <> 1 then EBEZSTR || ' ' || BADRESSE
                                  else EBEZSTR
                                end
           when BSonst = 1 then CASE
                                  when ENR = 0 then EBEZSTR
                                  when not EADRESSE is Null then EBEZSTR || ' ' || EADRESSE
                                  else EBEZSTR
                                end
           when BSonst = 2 then CASE
                                  when ENR = 0 then EBEZSTR
                                  when not ename is NULL then case
                                                                when bewstatus <> 1 then EBEZSTR || ' ' || bname || ' / ' || ENAME
                                                                when not EADRESSE is Null then EBEZSTR || ' ' || EADRESSE
                                                                else EBEZSTR
                                                              end
                                END
         end as ENRBez
    from cteWhgList

    into ONr, ENr, BKNR, EKNR, EBEZ, ART,
         ENRSTR, EBEZSTR,
         BNAME, BVNAME, BADRESSE, BFIRMA,
         ENAME, EVNAME, EADRESSE, EFIRMA,
         BSONST, BKVON, BKBIS, BEWSTATUS,
         ENRBez
  do
  begin
    suspend;
  end
end
