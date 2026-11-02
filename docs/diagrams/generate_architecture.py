#!/usr/bin/env python3
"""Generate the sparse icon overview; network details remain in the companion README.

No network, AWS or application operations. The official AWS SVGs remain unmodified.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
ASSETS = HERE / 'assets/aws-2026-07'
DEST = HERE / 'pals-aws-private-target.drawio'
provenance = json.loads((ASSETS / 'provenance.json').read_text())
for name, ref in provenance['unmodified_svg_files'].items():
    assert hashlib.sha256((ASSETS / (name + '.svg')).read_bytes()).hexdigest() == ref['sha256']

mxfile = ET.Element('mxfile', host='app.diagrams.net', agent='PALS architecture overview', version='32.6.1')
diagram = ET.SubElement(mxfile, 'diagram', id='pals-overview', name='PALS AWS overview')
model = ET.SubElement(diagram, 'mxGraphModel', dx='1800', dy='1070', grid='1', gridSize='10',
    guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1', pageScale='1',
    pageWidth='1800', pageHeight='1070', background='#FFFFFF', math='0', shadow='0')
root = ET.SubElement(model, 'root')
ET.SubElement(root, 'mxCell', id='0')
ET.SubElement(root, 'mxCell', id='1', parent='0')
FONT = 'fontFamily=Hiragino Sans,Noto Sans JP,Arial;'

def cell(name, text, x, y, w, h, style):
    c = ET.SubElement(root, 'mxCell', id=name, value=text, style=style, vertex='1', parent='1')
    ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})
    return c

def text(name, value, x, y, w, h=64, size=23, align='center', color='#202A36'):
    return cell(name, value, x, y, w, h,
        f'text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;{FONT}'
        f'fontSize={size};fontColor={color};align={align};verticalAlign=top;spacing=0;')

def boundary(name, x, y, w, h, color):
    cell(name, '', x, y, w, h,
        f'rounded=1;absoluteArcSize=1;arcSize=8;fillColor=none;strokeColor={color};strokeWidth=1.4;dashed=1;')

def icon(name, asset, label, x, y, size=96, caption_width=230):
    svg = quote((ASSETS / (asset + '.svg')).read_text(), safe='')
    cell(name, '', x, y, size, size,
        'shape=image;imageAspect=0;aspect=fixed;strokeColor=none;fillColor=none;image=data:image/svg+xml,'+svg+';')
    text(name+'-label', label, x+(size-caption_width)/2, y+size+12, caption_width)

def edge(name, source, target, points=(), extra='', both=False):
    e = ET.SubElement(root, 'mxCell', id=name, source=source, target=target, value='', edge='1', parent='1',
        style='edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=20;html=1;'
        'endArrow=block;endFill=1;strokeWidth=2.4;strokeColor=#202A36;'
        +('startArrow=block;startFill=1;' if both else '')+extra)
    g = ET.SubElement(e, 'mxGeometry', relative='1', **{'as':'geometry'})
    if points:
        arr = ET.SubElement(g, 'Array', **{'as':'points'})
        for x,y in points: ET.SubElement(arr, 'mxPoint', x=str(x), y=str(y))

# Only overview boundaries and short icon labels. CIDRs, ports, machine classes,
# AZ placement, WAF/ACM, egress and operations are documented in README.md.
text('title', 'PALS / AWS', 55, 45, 380, 45, 30, 'left')
boundary('aws', 460, 100, 1290, 890, '#73A4BD')
text('region', 'ap-northeast-1', 480, 116, 350, 36, 22, 'left', '#367391')
boundary('private', 900, 350, 790, 430, '#91B6A1')
text('private-label', 'Private subnets', 920, 366, 350, 36, 22, 'left', '#47775C')

icon('browser','users','利用者',75,425)
cell('cloudflare','',260,430,110,80,'shape=cloud;fillColor=#FFF2E3;strokeColor=#DD963F;strokeWidth=1.8;')
text('cloudflare-label','Cloudflare',220,538,190)
icon('alb','alb','Application<br>Load Balancer',620,425)
icon('control','ec2','Amazon EC2<br>Web / API',980,425)
icon('database','aurora','Amazon Aurora',1450,425)
icon('compute','ec2','Amazon EC2<br>Workers / Lean',1080,600)
icon('sqs','sqs','Amazon SQS',660,725)
icon('s3','s3','Amazon S3',1450,820)
icon('cognito','cognito','Amazon Cognito',660,190)
cell('openai','',260,820,110,80,'shape=cloud;fillColor=#F3F5F7;strokeColor=#8795A4;strokeWidth=1.8;')
text('openai-label','OpenAI API',215,930,210)

edge('user-cloudflare','browser','cloudflare',extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('cloudflare-alb','cloudflare','alb',extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('alb-api','alb','control',extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('api-db','control','database',extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('api-sqs','control','sqs',[(850,497),(850,650),(708,650)],'exitX=0;exitY=0.75;entryX=0.5;entryY=0;')
edge('sqs-compute','sqs','compute',[(1010,773),(1010,648)],'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('api-lean','control','compute',[(1280,502),(1280,648)],'exitX=1;exitY=0.8;entryX=1;entryY=0.5;',True)
edge('worker-s3','compute','s3',[(1370,648),(1370,868)],'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('worker-openai','compute','openai',[(950,677),(950,1020),(430,1020),(430,860)],'exitX=0;exitY=0.8;entryX=1;entryY=0.5;jumpStyle=arc;jumpSize=12;')
edge('user-auth','browser','cognito',[(123,238)],'exitX=0.5;exitY=0;entryX=0;entryY=0.5;')

ET.indent(mxfile, space='  ')
DEST.write_text(ET.tostring(mxfile, encoding='unicode')+'\n')
print(DEST)
