# VHDL 1 - Logisim 과제

강의자료 마지막 페이지의 1~5번 문제를 VHDL과 Logisim-evolution 회로로 구현한 제출 자료입니다.

보고서는 문제별 핵심 설명과 실제 Logisim 구동 사진만 넣은 기본 형식으로 정리했습니다. 공개본에서는 제출자 식별정보를 제외했습니다.

## 실행

1. Logisim-evolution 5.0.0에서 `circuits/VHDL1_all.circ`를 엽니다.
2. QuestaSim/ModelSim 연동 경로를 설정합니다. 제작 환경에서는 `C:\VHDL-SIMULATION\questa_fse\win64`를 사용했습니다.
3. `Simulate > VHDL Simulation Enabled`를 켜고 상태가 Active가 될 때까지 기다립니다.
4. 필요하면 `Simulate > Reset Simulation`으로 초기 입력을 다시 반영합니다.
5. 왼쪽의 `P1_logic`~`P5_count13`을 더블클릭하여 문제를 선택합니다. 다른 문제로 이동한 경우 **Simulate > Restart VHDL simulator**를 실행하여 현재 회로로 다시 구성합니다.
6. Active가 된 뒤 **Reset Simulation**을 한 번 실행하여 초기 입력을 반영합니다.
7. Poke Tool로 입력을 바꿉니다. 여러 비트인 vt 입력은 16진수로 표시합니다.

각 문제를 따로 열 수 있는 개별 `.circ` 파일도 `circuits/`에 있습니다. VHDL 소스는 회로 파일 내부에도 포함되어 있어 별도의 절대 파일 경로에 의존하지 않습니다.

| 문제 | 회로 | 입력 | 결과 |
|---|---|---|---|
| 1 | P1_logic | a,b,c,d | 4입력 AND와 OR |
| 2 | P2_mux | a~h, ch(2:0) | 8개 중 하나 선택 |
| 3 | P3_letters | dat(2:0), en | A,b,C,d,F,G 표시 |
| 4 | P4_vote25 | vt 25비트 | 찬성 13표 이상이면 1 |
| 5 | P5_count13 | vt 13비트, en | 1 개수를 16진수 한 자리로 표시 |

3번의 선택 코드는 0=A, 1=b, 2=C, 3=d, 4=F, 5=G이며 6과 7은 소등합니다. 3번의 선택 코드와 en 입력은 문제에 지정되지 않은 구현 선택입니다. en은 강의의 표시기 예제와 같게 추가했습니다.

## 7세그먼트

출력 순서는 `display(7 downto 0) = a b c d e f g dp`입니다. 1에서 켜지는 표시기이며, en=0이면 모든 막대를 끕니다. Splitter와 이름이 같은 Tunnel을 사용해 막대별 비트를 연결했습니다.

## 5번의 입력 범위

13비트에는 1이 최대 13개 들어갑니다. 따라서 도달 가능한 결과는 0~9, A,b,C,d입니다. E(14)와 F(15) 패턴은 요구사항의 표시 표에 포함했으나, 13비트 입력으로는 도달하지 않습니다. 14와 15도 실제로 표시하려면 입력이 15비트 이상이어야 합니다.

## 파일

- `src/`: 문제별 VHDL 소스 5개
- `circuits/`: 전체 프로젝트와 문제별 회로 5개
- `tests/`: 테스트벤치, 실행 로그, 검증 결과
- `report/`: 보고서 PDF와 편집 가능한 원문
- `evidence/`: 실제 Logisim 동작 화면
- `tools/`: 회로 생성 및 Questa 검증을 재현하는 도구

## 검증

제작 환경에 설치된 Questa에서 VHDL-2002로 분석하고 시뮬레이션합니다. Starter 라이선스는 한 번에 한 세션만 허용하므로 독립 테스트를 실행할 때는 먼저 Logisim의 VHDL Simulation Enabled를 꺼서 Questa 세션을 종료합니다.

```text
python tools/verify_questa.py --questa C:\VHDL-SIMULATION\questa_fse\win64
```

전체 23,213개 테스트를 실행합니다. 1, 2, 3, 5번은 이진 입력 전체를 검사하고, 4번은 찬성표 수별 순환 배치와 의사난수 및 경계 전환을 검사합니다. 25비트 전체 입력 33,554,432개를 전부 검사한 것은 아닙니다. E/F는 입력 범위 밖이므로 5번의 동적 검증 대상이 아닙니다.

`tools/audit_wiring.py`는 VHDL 테스트와 별도로 입력·출력 포트의 연결, 비트 폭, Splitter에서 7세그먼트까지의 비트 배선을 검사합니다. 검사 결과는 `tests/wiring_audit.json`에 있습니다. 입력값이 가려져 명확하게 확인되지 않는 이전 사진 한 장은 검증 자료에서 제외했습니다.

출처: 사용자가 제공한 `VHDL_1 (1).pdf`, 17~18쪽의 표시기 기준, 22쪽의 문제. 회로 파일의 VHDL 내용과 별도 소스 파일이 동일한지도 검사합니다.
