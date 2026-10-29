library ieee;
use ieee.std_logic_1164.all;

-- Problem 2: ch=000 selects a, ..., ch=111 selects h.
entity mux8_1 is
    port (
        a, b, c, d, e, f, g, h : in  std_logic;
        ch                      : in  std_logic_vector(2 downto 0);
        data                    : out std_logic
    );
end entity mux8_1;

architecture rtl of mux8_1 is
begin
    with ch select
        data <= a   when "000",
                b   when "001",
                c   when "010",
                d   when "011",
                e   when "100",
                f   when "101",
                g   when "110",
                h   when "111",
                '0' when others;
end architecture rtl;
