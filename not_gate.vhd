LIBRARY ieee;
USE ieee.std_logic_1164.all;

ENTITY not_gate IS
  PORT (
    a : IN  std_logic;
    y : OUT std_logic
  );
END not_gate;

ARCHITECTURE TypeArchitecture OF not_gate IS
BEGIN
    y <= NOT a;
END TypeArchitecture;