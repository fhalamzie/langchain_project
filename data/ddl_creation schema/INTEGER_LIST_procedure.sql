-- Prozedur: INTEGER_LIST
-- Generiert: 2025-05-31 10:26:42

CREATE OR ALTER PROCEDURE INTEGER_LIST
DECLARE VARIABLE CHAR_COUNT INTEGER;
DECLARE VARIABLE PARAM_LENGTH INTEGER;
DECLARE VARIABLE READ_VALUE CHAR(1);
DECLARE VARIABLE CURRENT_INTEGER VARCHAR(20);
begin
    param_length = CHAR_LENGTH(input);
    char_count = 0;
    current_integer = '';
    while (char_count < param_length) do begin
        char_count = :char_count + 1;
        read_value = substring(:input from :char_count for 1);
        if (:read_value <> ',') then begin
            current_integer = :current_integer || :read_value;
        end else if (:read_value <> ' ') then  begin
            int_value = cast(:current_integer as integer);
            current_integer = '';
            suspend;
        end

        if (:char_count = :param_length) then begin
            int_value = cast(:current_integer as integer);
            suspend;
        end
    end
end
