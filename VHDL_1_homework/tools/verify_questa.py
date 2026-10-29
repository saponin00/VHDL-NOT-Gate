"""Compile and simulate the submitted VHDL with the installed Questa tools."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--questa',default=r'C:\VHDL-SIMULATION\questa_fse\win64')
    args=parser.parse_args()
    bin_dir=Path(args.questa)
    sources=sorted((ROOT/'src').glob('*.vhd'))+[ROOT/'tests/tb_homework.vhd']
    log=[]
    with tempfile.TemporaryDirectory(prefix='vhdl1_verify_') as temporary:
        scratch=Path(temporary)
        for source in sources: shutil.copy2(source,scratch/source.name)
        (scratch/'verify.do').write_text('onerror {quit -code 1}\nrun -all\nquit -f\n',encoding='ascii')
        commands=[
            [str(bin_dir/'vlib.exe'),'work'],
            [str(bin_dir/'vcom.exe'),'-2002',*[source.name for source in sources]],
            [str(bin_dir/'vsim.exe'),'-c','work.tb_homework','-do','verify.do'],
        ]
        for command in commands:
            result=subprocess.run(command,cwd=scratch,capture_output=True,text=True,errors='replace',
                                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=90)
            text=result.stdout+result.stderr
            log.append(text)
            if result.returncode:
                (ROOT/'tests/questa.log').write_text('\n'.join(log),encoding='utf-8')
                raise RuntimeError(text)
    combined='\n'.join(log)
    assert 'ALL PASS: 23213 test cases' in combined, combined
    (ROOT/'tests/questa.log').write_text(combined,encoding='utf-8')
    circuit_files=sorted((ROOT/'circuits').glob('*.circ'))
    entity_sources={source.stem.split('_',1)[1]:source.read_text(encoding='utf-8').strip()
                    for source in sources if source.name != 'tb_homework.vhd'}
    embedded=0
    for file in circuit_files:
        project=ET.parse(file).getroot()
        assert project.attrib['source']=='5.0.0'
        for code in project.findall('vhdl'):
            assert code.text.strip()==entity_sources[code.attrib['name']],file
            embedded+=1
    result=dict(vhdl_standard='2002',test_cases=23213,status='PASS',
                circuit_files=len(circuit_files),embedded_source_checks=embedded,
                problem_cases={'P1':16,'P2':2048,'P3':16,'P4':4748,'P5':16385},
                scope='All binary inputs for P1/P2/P3/P5; count/position/random/boundary tests for P4. E/F unreachable for 13-bit input.')
    (ROOT/'tests/results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
