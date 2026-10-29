"""Use Logisim's own loader/writer to validate every submitted project."""
from pathlib import Path
import argparse
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--logisim',default=r'C:\VHDL-SIMULATION\logisim\logisim-evolution.exe')
    args=parser.parse_args()
    results=[]
    with tempfile.TemporaryDirectory(prefix='logisim_validate_') as temporary:
        for source in sorted((ROOT/'circuits').glob('*.circ')):
            out=Path(temporary)/source.name
            result=subprocess.run([args.logisim,'--new-file-format',str(source),str(out)],
                capture_output=True,text=True,errors='replace',timeout=30,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode or not out.exists():
                raise RuntimeError(result.stdout+result.stderr)
            project=ET.parse(out).getroot()
            circuits=project.findall('circuit')
            results.append(dict(file=source.name,status='PASS',circuits=len(circuits),
                                embedded_vhdl=len(project.findall('vhdl')),
                                wires=sum(len(c.findall('wire')) for c in circuits)))
    (ROOT/'tests/logisim_import_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()
