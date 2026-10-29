library ieee;
use ieee.std_logic_1164.all;

-- Problem 3: display the letters a, b, c, d, f, g.
-- Seven-segment approximations: A, b, C, d, F, G.
-- display(7 downto 0) = a b c d e f g dp; 1 = segment on.
-- dat: 000=A, 001=b, 010=C, 011=d, 100=F, 101=G.
entity letter_display is
    port (
        en      : in  std_logic;
        dat     : in  std_logic_vector(2 downto 0);
        display : out std_logic_vector(7 downto 0)
    );
end entity letter_display;

architecture rtl of letter_display is
begin
    process(en, dat)
    begin
        display <= "00000000";
        if en = '1' then
            case dat is
                when "000" => display <= "11101110"; -- A
                when "001" => display <= "00111110"; -- b
                when "010" => display <= "10011100"; -- C
                when "011" => display <= "01111010"; -- d
                when "100" => display <= "10001110"; -- F
                when "101" => display <= "10111100"; -- G
                when others => display <= "00000000";
            end case;
        end if;
    end process;
end architecture rtl;
