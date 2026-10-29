"""Check the submitted Logisim wiring, independently of the VHDL testbench."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def xy(value):
    return tuple(map(int,re.findall(r'-?\d+',value)))

def attrs(component):
    return {a.attrib['name']:a.attrib['val'] for a in component.findall('a')}

def ports(source):
    source=re.sub(r'--[^\n]*','',source)
    start=re.search(r'\bport\s*\(',source,re.I).end()
    depth=1
    end=start
    while depth:
        if source[end]=='(':depth+=1
        if source[end]==')':depth-=1
        end+=1
    result=[]
    for declaration in source[start:end-1].split(';'):
        match=re.fullmatch(r'\s*([\w\s,]+)\s*:\s*(in|out)\s+(std_logic(?:_vector\s*\(\s*(\d+)\s+downto\s+(\d+)\s*\))?)\s*',declaration,re.I)
        if not match:raise ValueError(declaration)
        names,mode,_,upper,lower=match.groups()
        width=int(upper)-int(lower)+1 if upper else 1
        result.extend((name.strip(),mode.lower(),width) for name in names.split(','))
    return result

def audit(file):
    root=ET.parse(file).getroot()
    definitions={node.attrib['name']:ports(node.text) for node in root.findall('vhdl')}
    findings=[]
    for circuit in root.findall('circuit'):
        comps=circuit.findall('comp')
        wires=[(xy(w.attrib['from']),xy(w.attrib['to'])) for w in circuit.findall('wire')]
        points={p for pair in wires for p in pair}
        parent={}
        def find(p):
            parent.setdefault(p,p)
            if parent[p]!=p:parent[p]=find(parent[p])
            return parent[p]
        def join(p,q):parent[find(p)]=find(q)
        pins=[];vports=[];splitters=[];segments=[];tunnels={}
        for comp in comps:
            x,y=xy(comp.attrib['loc']);a=attrs(comp);name=comp.attrib['name']
            if name=='Pin':
                pins.append((a.get('label',''),a.get('type','input'),int(a.get('width','1')),(x,y)))
                points.add((x,y))
            elif name=='Tunnel':
                tunnels.setdefault(a['label'],[]).append((x,y));points.add((x,y))
            elif name in definitions:
                inputs=[p for p in definitions[name] if p[1]=='in']
                outputs=[p for p in definitions[name] if p[1]=='out']
                for i,(label,mode,width) in enumerate(inputs):
                    p=(x-220,y+20*i);vports.append((label,mode,width,p));points.add(p)
                for i,(label,mode,width) in enumerate(outputs):
                    p=(x,y+20*i);vports.append((label,mode,width,p));points.add(p)
            elif name=='Splitter':
                assert a.get('facing','east')=='east'
                assert a.get('appear','left')=='left'
                fanout=int(a['fanout']);spacing=int(a.get('spacing','1'))*10
                branch=[(x+20,y-(10+spacing*(fanout-1))+spacing*i) for i in range(fanout)]
                points.update([(x,y),*branch])
                bit_branch={bit:int(a.get(f'bit{bit}',str(bit))) for bit in range(int(a['incoming']))}
                splitters.append(((x,y),branch,bit_branch))
            elif name=='7-Segment Display':
                offsets={'a':(20,0),'b':(30,0),'c':(20,60),'d':(10,60),'e':(0,60),'f':(10,0),'g':(0,0),'dp':(30,60)}
                segments=[(label,(x+dx,y+dy)) for label,(dx,dy) in offsets.items()]
                points.update(p for _,p in segments)
        for p in points:find(p)
        for p,q in wires:
            on_wire=[]
            for point in points:
                if p[0]==q[0]==point[0] and min(p[1],q[1])<=point[1]<=max(p[1],q[1]):on_wire.append(point)
                elif p[1]==q[1]==point[1] and min(p[0],q[0])<=point[0]<=max(p[0],q[0]):on_wire.append(point)
            for point in on_wire:join(p,point)
        for locations in tunnels.values():
            for point in locations:join(locations[0],point)
        inputs_checked=0;outputs_checked=0
        for label,mode,width,point in vports:
            wanted='input' if mode=='in' else 'output'
            attached=[pin for pin in pins if pin[1]==wanted and find(pin[3])==find(point)]
            assert len(attached)==1,(file.name,circuit.attrib['name'],label,attached)
            pin=attached[0]
            assert pin[2]==width,(label,'width mismatch')
            if mode=='in':
                assert pin[0]==label,(label,pin[0])
                inputs_checked+=1
            else:outputs_checked+=1
        routes=0
        if segments:
            assert len(splitters)==1
            trunk,branches,bit_branch=splitters[0]
            output=[p for p in vports if p[0]=='display'][0]
            assert find(trunk)==find(output[3])
            expected={'a':7,'b':6,'c':5,'d':4,'e':3,'f':2,'g':1,'dp':0}
            for label,point in segments:
                attached=[i for i,branch in enumerate(branches) if find(branch)==find(point)]
                assert attached==[bit_branch[expected[label]]],(file.name,label,attached)
                routes+=1
        findings.append(dict(circuit=circuit.attrib['name'],input_connections=inputs_checked,
                             output_connections=outputs_checked,segment_bit_routes=routes,status='PASS'))
    return dict(file=file.name,checks=findings,status='PASS')

if __name__=='__main__':
    results=[audit(file) for file in sorted((ROOT/'circuits').glob('*.circ'))]
    output=dict(projects=len(results),circuit_instances=sum(len(r['checks']) for r in results),
                status='PASS',method='Static net connectivity, port widths, and seven-segment bit routing; not a separate simulator.',results=results)
    (ROOT/'tests/wiring_audit.json').write_text(json.dumps(output,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps(output,indent=2))
