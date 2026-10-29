library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tb_homework is
end entity tb_homework;

architecture test of tb_homework is
    signal gate_in : std_logic_vector(3 downto 0) := (others => '0');
    signal and_out, or_out : std_logic;
    signal mux_in : std_logic_vector(7 downto 0) := (others => '0');
    signal mux_sel : std_logic_vector(2 downto 0) := (others => '0');
    signal mux_out : std_logic;
    signal letter_en : std_logic := '0';
    signal letter_dat : std_logic_vector(2 downto 0) := (others => '0');
    signal letter_seg : std_logic_vector(7 downto 0);
    signal votes : std_logic_vector(25 downto 1) := (others => '0');
    signal majority : std_logic;
    signal count_vt : std_logic_vector(13 downto 1) := (others => '0');
    signal count_en : std_logic := '0';
    signal count_seg : std_logic_vector(7 downto 0);

    -- Independent display oracle: specify lit segments by name.
    function segments(lit : string) return std_logic_vector is
        variable value : std_logic_vector(7 downto 0) := (others => '0');
    begin
        for i in lit'range loop
            case lit(i) is
                when 'a' => value(7) := '1';
                when 'b' => value(6) := '1';
                when 'c' => value(5) := '1';
                when 'd' => value(4) := '1';
                when 'e' => value(3) := '1';
                when 'f' => value(2) := '1';
                when 'g' => value(1) := '1';
                when others => null;
            end case;
        end loop;
        return value;
    end function;

    function expected_hex(n : natural) return std_logic_vector is
    begin
        case n is
            when  0 => return segments("abcdef");
            when  1 => return segments("bc");
            when  2 => return segments("abdeg");
            when  3 => return segments("abcdg");
            when  4 => return segments("bcfg");
            when  5 => return segments("acdfg");
            when  6 => return segments("acdefg");
            when  7 => return segments("abc");
            when  8 => return segments("abcdefg");
            when  9 => return segments("abcdfg");
            when 10 => return segments("abcefg");
            when 11 => return segments("cdefg");
            when 12 => return segments("adef");
            when 13 => return segments("bcdeg");
            when 14 => return segments("adefg");
            when 15 => return segments("aefg");
            when others => return segments("");
        end case;
    end function;

    -- Integer arithmetic reference, independent of the DUT's bit scan.
    function bit_count(n : natural) return natural is
        variable remaining : natural := n;
        variable total : natural := 0;
    begin
        while remaining > 0 loop
            total := total + remaining mod 2;
            remaining := remaining / 2;
        end loop;
        return total;
    end function;
begin
    dut_logic : entity work.logic4
        port map(a => gate_in(0), b => gate_in(1), c => gate_in(2),
                 d => gate_in(3), out1 => and_out, out2 => or_out);
    dut_mux : entity work.mux8_1
        port map(a => mux_in(0), b => mux_in(1), c => mux_in(2),
                 d => mux_in(3), e => mux_in(4), f => mux_in(5),
                 g => mux_in(6), h => mux_in(7), ch => mux_sel,
                 data => mux_out);
    dut_letter : entity work.letter_display
        port map(en => letter_en, dat => letter_dat, display => letter_seg);
    dut_vote : entity work.vote25
        port map(vt => votes, result => majority);
    dut_count : entity work.count13_display
        port map(vt => count_vt, en => count_en, display => count_seg);

    stimulus : process
        variable expected : std_logic_vector(7 downto 0);
        variable vote_pattern : std_logic_vector(25 downto 1);
        variable random_state : unsigned(24 downto 0) := to_unsigned(1, 25);
        variable random_value : natural;
        variable checks : natural := 0;
    begin
        -- All 16 binary input combinations.
        for n in 0 to 15 loop
            gate_in <= std_logic_vector(to_unsigned(n, 4));
            wait for 1 ns;
            if n = 15 then
                assert and_out = '1' report "AND all-ones failed" severity failure;
            else
                assert and_out = '0' report "AND failed" severity failure;
            end if;
            if n = 0 then
                assert or_out = '0' report "OR all-zeros failed" severity failure;
            else
                assert or_out = '1' report "OR failed" severity failure;
            end if;
            checks := checks + 1;
        end loop;
        report "PASS problem 1: 16 input combinations" severity note;

        -- All 256 input words and all 8 selections.
        for n in 0 to 255 loop
            mux_in <= std_logic_vector(to_unsigned(n, 8));
            for sel in 0 to 7 loop
                mux_sel <= std_logic_vector(to_unsigned(sel, 3));
                wait for 1 ns;
                if (n / (2 ** sel)) mod 2 = 1 then
                    assert mux_out = '1' report "MUX high failed" severity failure;
                else
                    assert mux_out = '0' report "MUX low failed" severity failure;
                end if;
                checks := checks + 1;
            end loop;
        end loop;
        report "PASS problem 2: 2048 input/selection combinations" severity note;

        -- All 8 selectors at each enable level, including unused codes.
        for enable_value in 0 to 1 loop
            if enable_value = 1 then letter_en <= '1';
            else letter_en <= '0'; end if;
            for n in 0 to 7 loop
                letter_dat <= std_logic_vector(to_unsigned(n, 3));
                expected := segments("");
                if enable_value = 1 then
                    case n is
                        when 0 => expected := segments("abcefg");
                        when 1 => expected := segments("cdefg");
                        when 2 => expected := segments("adef");
                        when 3 => expected := segments("bcdeg");
                        when 4 => expected := segments("aefg");
                        when 5 => expected := segments("acdef");
                        when others => null;
                    end case;
                end if;
                wait for 1 ns;
                assert letter_seg = expected report "Letter display failed" severity failure;
                checks := checks + 1;
            end loop;
        end loop;
        report "PASS problem 3: 16 selector/enable combinations" severity note;

        -- Every population from 0 to 25, rotated across all input positions.
        for n in 0 to 25 loop
            for offset in 0 to 24 loop
                vote_pattern := (others => '0');
                for j in 1 to n loop
                    vote_pattern(((j - 1 + offset) mod 25) + 1) := '1';
                end loop;
                votes <= vote_pattern;
                wait for 1 ns;
                if n >= 13 then
                    assert majority = '1' report "Majority true failed" severity failure;
                else
                    assert majority = '0' report "Majority false failed" severity failure;
                end if;
                checks := checks + 1;
            end loop;
        end loop;

        -- An additional 4096 reproducible pseudorandom arrangements.
        for n in 1 to 4096 loop
            random_state := random_state xor shift_left(random_state, 7);
            random_state := random_state xor shift_right(random_state, 9);
            random_state := random_state xor shift_left(random_state, 8);
            random_value := to_integer(random_state);
            votes <= std_logic_vector(random_state);
            wait for 1 ns;
            if bit_count(random_value) >= 13 then
                assert majority = '1' report "Random majority true failed" severity failure;
            else
                assert majority = '0' report "Random majority false failed" severity failure;
            end if;
            checks := checks + 1;
        end loop;
        -- Explicit high-to-zero transition detects retained/latch output bugs.
        votes <= (others => '1');
        wait for 1 ns;
        assert majority = '1' report "All votes high failed" severity failure;
        checks := checks + 1;
        votes <= (others => '0');
        wait for 1 ns;
        assert majority = '0' report "All votes zero after high failed" severity failure;
        checks := checks + 1;
        report "PASS problem 4: 4748 vote patterns/transitions" severity note;

        -- Every 13-bit word at both enable levels: 8192 * 2.
        for n in 0 to 8191 loop
            count_vt <= std_logic_vector(to_unsigned(n, 13));
            for enable_value in 0 to 1 loop
                if enable_value = 1 then
                    count_en <= '1';
                    expected := expected_hex(bit_count(n));
                else
                    count_en <= '0';
                    expected := segments("");
                end if;
                wait for 1 ns;
                assert count_seg = expected
                    report "Count display failed for input " & integer'image(n)
                    severity failure;
                checks := checks + 1;
            end loop;
        end loop;
        count_en <= '0';
        wait for 1 ns;
        assert count_seg = segments("")
            report "Enable-off transition failed" severity failure;
        checks := checks + 1;
        report "PASS problem 5: 16385 input/enable combinations and transition" severity note;
        report "ALL PASS: " & integer'image(checks) & " test cases" severity note;
        wait;
    end process;
end architecture test;
