-- Prozedur: ABRECHNUNG_VZ
-- Generiert: 2025-05-31 10:26:41

CREATE OR ALTER PROCEDURE ABRECHNUNG_VZ
BEGIN
 IF (IKNR<200000) THEN
  BEGIN /* Bewohner */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 11, 0, :BDATUM) RETURNING_VALUES :BKVZ, :BKVZ_NETTO;
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 12, 0, :BDATUM) RETURNING_VALUES :HKVZ, :HKVZ_NETTO;
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 13, 0, :BDATUM) RETURNING_VALUES :OPGN, :OPGN_NETTO;
  END
 ELSE
  BEGIN
   /* UWE: Es gibt keine G/N in der WEG */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 15, 0, :BDATUM) RETURNING_VALUES :HAUSGVZ, :HAUSGVZ_NETTO;
/*   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 15, 1, :BDATUM) RETURNING_VALUES :HAUSGVZ_NZ, :HAUSGVZ_NETTO_NZ; */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 110, 0, :BDATUM) RETURNING_VALUES :RL1, :RL1_NETTO; /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
/*   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 110, 1, :BDATUM) RETURNING_VALUES :RL1_NZ, :RL1_NZ_NETTO;  RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen NZ */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 120, 0, :BDATUM) RETURNING_VALUES :RL2, :RL2_NETTO; /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
/*   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 120, 1, :BDATUM) RETURNING_VALUES :RL2_NZ, :RL2_NZ_NETTO;  RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen NZ */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 130, 0, :BDATUM) RETURNING_VALUES :RL3, :RL3_NETTO; /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
/*   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 130, 1, :BDATUM) RETURNING_VALUES :RL3_NZ, :RL3_NZ_NETTO;  RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen NZ */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 140, 0, :BDATUM) RETURNING_VALUES :RL4, :RL4_NETTO; /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
/*   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 140, 1, :BDATUM) RETURNING_VALUES :RL4_NZ, :RL4_NZ_NETTO;  RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen NZ */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 150, 0, :BDATUM) RETURNING_VALUES :RL5, :RL5_NETTO; /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
/*   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 150, 1, :BDATUM) RETURNING_VALUES :RL5_NZ, :RL5_NZ_NETTO;  RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen NZ */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 160, 0, :BDATUM) RETURNING_VALUES :RL6, :RL6_NETTO; /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
/*   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 160, 1, :BDATUM) RETURNING_VALUES :RL6_NZ, :RL6_NZ_NETTO;  RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen NZ */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 170, 0, :BDATUM) RETURNING_VALUES :RL7, :RL7_NETTO; /* RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen */
/*   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 170, 1, :BDATUM) RETURNING_VALUES :RL7_NZ, :RL7_NZ_NETTO;  RÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¼cklagen NZ */
   EXECUTE PROCEDURE ABRECHNUNG_VZ_ZPOS (:IONR, :IKNR, :DTVON, :DTBIS, :BISTVZ, 17, 0, :BDATUM) RETURNING_VALUES :SONDERUML, :SONDERUML_NETTO; /* Sonderumlage */
  END
 SUSPEND;
END
