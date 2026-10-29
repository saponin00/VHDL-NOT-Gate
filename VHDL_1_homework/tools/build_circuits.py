"""Build self-contained Logisim-evolution 5 projects from the VHDL sources."""
from pathlib import Path
import copy
import json
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT.parent / 'VHDL_homework'

LIBRARIES = ['Wiring', 'Gates', 'Plexers', 'Arithmetic', 'FPArithmetic',
             'Memory', 'I/O', 'TTL', 'TCL', 'Base']

DESIGNS = [
    dict(circuit='P1_logic', entity='logic4', file='01_logic4.vhd',
         title='1. Four-input AND and OR',
         inputs=[('a',1,1),('b',1,1),('c',1,1),('d',1,1)],
         outputs=[('out1',1),('out2',1)],
         notes=['AND = 1 only when a=b=c=d=1.', 'OR = 1 when at least one input is 1.']),
    dict(circuit='P2_mux', entity='mux8_1', file='02_mux8_1.vhd',
         title='2. Eight-to-one multiplexer',
         inputs=[(name,1,int(name=='e')) for name in 'abcdefgh']+[('ch',3,4)],
         outputs=[('data',1)],
         notes=['ch: 000=a, 001=b, 010=c, 011=d, 100=e, 101=f, 110=g, 111=h.',
                'Initial example: only e=1; ch=100 selects e, so data=1.']),
    dict(circuit='P3_letters', entity='letter_display', file='03_letter_display.vhd',
         title='3. Letter decoder and seven-segment display',
         inputs=[('en',1,1),('dat',3,0)], outputs=[('display',8)],
         notes=['dat: 0=A, 1=b, 2=C, 3=d, 4=F, 5=G; 6/7=blank.',
                'en=0 blanks the display. Output order: abcdefgdp.']),
    dict(circuit='P4_vote25', entity='vote25', file='04_vote25.vhd',
         title='4. Twenty-five-person majority vote',
         inputs=[('vt',25,0x1fff)], outputs=[('result',1)],
         notes=['vt is hexadecimal. 0000FFF = 12 yes votes; 0001FFF = 13 yes votes.',
                'A strict majority requires at least 13 votes.']),
    dict(circuit='P5_count13', entity='count13_display', file='05_count13_display.vhd',
         title='5. Count ones in thirteen bits and display the count',
         inputs=[('vt',13,0x1fff),('en',1,1)], outputs=[('display',8)],
         notes=['vt is hexadecimal. 0005 -> 2; 03FF -> A; 1FFF -> d.',
                'Thirteen bits contain at most thirteen ones. E/F cannot be reached.',
                'en=0 blanks all segments, including the decimal point.']),
]

def attribute(node, name, value):
    ET.SubElement(node, 'a', name=name, val=str(value))

def component(circuit, library, name, x, y, **attrs):
    kwargs={'name':name, 'loc':f'({x},{y})'}
    if library is not None:
        kwargs['lib']=str(library)
    node=ET.SubElement(circuit,'comp',**kwargs)
    for key,val in attrs.items():
        attribute(node,key,str(val).lower() if isinstance(val,bool) else val)
    return node

def wire(circuit, *points):
    for p,q in zip(points,points[1:]):
        if p==q: continue
        assert p[0]==q[0] or p[1]==q[1], (p,q)
        ET.SubElement(circuit,'wire',{'from':f'({p[0]},{p[1]})','to':f'({q[0]},{q[1]})'})

def label(circuit, x, y, text, size=14, bold=False):
    component(circuit,9,'Text',x,y,text=text,font=f'SansSerif {"bold" if bold else "plain"} {size}',halign='left')

def pin(circuit,x,y,name,width=1,output=False,initial=0):
    return component(circuit,0,'Pin',x,y,appearance='NewPins',
                     facing='west' if output else 'east',type='output' if output else 'input',
                     width=width,label=name,labelloc='north',radix='16' if width>3 else '2',
                     initial=f'0x{initial:x}')

def display(circuit, output_x, output_y):
    # The output monitor and splitter share the 8-bit output bus.
    pin(circuit,570,90,'segments_hex',8,output=True)
    wire(circuit,(output_x,output_y),(540,output_y),(540,90),(570,90))
    wire(circuit,(540,output_y),(570,output_y),(570,300))
    node=component(circuit,0,'Splitter',570,300,facing='east',fanout=8,incoming=8,
                   appear='left',spacing=2)
    for bit in range(8): attribute(node,f'bit{bit}',7-bit)
    for branch,name in enumerate(['a','b','c','d','e','f','g','dp']):
        y=150+20*branch
        wire(circuit,(590,y),(650,y))
        component(circuit,0,'Tunnel',650,y,label=name,facing='west')

    component(circuit,6,'7-Segment Display',770,200,active=True,decimalPoint=True)
    for name,x,y,ty in [('g',770,200,170),('f',780,200,150),
                         ('a',790,200,130),('b',800,200,110),
                         ('e',770,260,290),('d',780,260,310),
                         ('c',790,260,330),('dp',800,260,350)]:
        wire(circuit,(x,y),(x,ty),(710,ty))
        component(circuit,0,'Tunnel',710,ty,label=name,facing='east')
    label(circuit,700,390,'1 = segment ON; dp always OFF.',12)

def build_circuit(design):
    node=ET.Element('circuit',name=design['circuit'])
    attribute(node,'appearance','logisim_evolution')
    attribute(node,'circuit',design['circuit'])
    attribute(node,'circuitnamedboxfixedsize','true')
    attribute(node,'simulationFrequency','1.0')
    label(node,70,40,design['title'],18,True)
    label(node,70,70,'Poke inputs to change values. Enable VHDL simulation in the Simulate menu.',12)
    component(node,None,design['entity'],500,200)
    for i,(name,width,initial) in enumerate(design['inputs']):
        y=200+20*i
        pin(node,150,y,name,width,initial=initial)
        wire(node,(150,y),(280,y))
    if design['outputs']==[('display',8)]:
        display(node,500,200)
    else:
        for i,(name,width) in enumerate(design['outputs']):
            y=200+20*i
            pin(node,650,y,name,width,output=True)
            wire(node,(500,y),(650,y))
    notes_y=max(440,250+20*len(design['inputs']))
    for i,text in enumerate(design['notes']): label(node,70,notes_y+25*i,text,13)
    return node

def project(designs):
    node=ET.Element('project',source='5.0.0',version='1.0')
    node.text='\nSelf-contained VHDL homework project for Logisim-evolution 5.0.0.\n'
    for i,name in enumerate(LIBRARIES): ET.SubElement(node,'lib',desc='#'+name,name=str(i))
    ET.SubElement(node,'main',name=designs[0]['circuit'])
    options=ET.SubElement(node,'options')
    for key,val in [('gateUndefined','ignore'),('simlimit','1000'),('simrand','0')]: attribute(options,key,val)
    toolbar=ET.SubElement(node,'toolbar')
    for name in ['Poke Tool','Edit Tool','Wiring Tool','Text Tool']:
        ET.SubElement(toolbar,'tool',name=name)
    for design in designs:
        node.append(build_circuit(design))
    for design in designs:
        vhdl=ET.SubElement(node,'vhdl',appearance='logisim_evolution',name=design['entity'])
        vhdl.text=(ROOT/'src'/design['file']).read_text(encoding='utf-8')
    return node

def write_project(path, designs):
    node=project(designs)
    ET.indent(node,space='  ')
    ET.ElementTree(node).write(path,encoding='utf-8',xml_declaration=True)

if __name__=='__main__':
    for folder in ['src','circuits','tests','evidence','report']:
        (ROOT/folder).mkdir(parents=True,exist_ok=True)
    for design in DESIGNS:
        source=LEGACY/design['file']
        if source.exists(): shutil.copy2(source,ROOT/'src'/design['file'])
    write_project(ROOT/'circuits/VHDL1_all.circ',DESIGNS)
    for i,design in enumerate(DESIGNS,1):
        write_project(ROOT/'circuits'/f'{i:02}_{design["entity"]}.circ',[design])
    if (LEGACY/'tb_homework.vhd').exists():
        shutil.copy2(LEGACY/'tb_homework.vhd',ROOT/'tests/tb_homework.vhd')
    else:
        assert (ROOT/'tests/tb_homework.vhd').exists(), 'Missing submitted testbench'
    (ROOT/'tests/design_manifest.json').write_text(json.dumps(DESIGNS,indent=2),encoding='utf-8')
    print('Created six self-contained .circ projects and five VHDL source files.')
