library ieee;
use ieee.std_logic_1164.all;

-- Problem 1: four-input AND and OR gates.
entity logic4 is
    port (
        a, b, c, d : in  std_logic;
        out1       : out std_logic;
        out2       : out std_logic
    );
end entity logic4;

architecture rtl of logic4 is
begin
    out1 <= a and b and c and d;
    out2 <= a or b or c or d;
end architecture rtl;
