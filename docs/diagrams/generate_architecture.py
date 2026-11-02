#!/usr/bin/env python3
"""Build an offline, editable AWS-icon diagram of the saved seq15 deployment.

AWS SVGs are unmodified assets with source hashes in assets/aws-2026-07/provenance.json.
This generator performs no network, AWS, model, runtime, or application operations.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
ASSETS = HERE / 'assets/aws-2026-07'
DEST = HERE / 'pals-aws-private-target.drawio'
W, H = 2360, 1530
FONT = 'fontFamily=Hiragino Sans,Noto Sans JP,Arial;'
NAVY, BLUE, ORANGE, PURPLE, GREEN = '#192B43', '#2876AE', '#C97921', '#8753A1', '#338C78'
manifest = json.loads((ASSETS / 'provenance.json').read_text())
for name, ref in manifest['unmodified_svg_files'].items():
    assert hashlib.sha256((ASSETS / (name + '.svg')).read_bytes()).hexdigest() == ref['sha256']
mxfile = ET.Element('mxfile', host='app.diagrams.net', agent='PALS AWS architecture', version='32.6.1')
diagram = ET.SubElement(mxfile, 'diagram', id='pals-aws-seq15', name='AWS deployed architecture — seq15')
model = ET.SubElement(diagram, 'mxGraphModel', dx=str(W), dy=str(H), grid='1', gridSize='10',
    guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1', pageScale='1',
    pageWidth=str(W), pageHeight=str(H), background='#FFFFFF', math='0', shadow='0')
root = ET.SubElement(model, 'root')
ET.SubElement(root, 'mxCell', id='0')
ET.SubElement(root, 'mxCell', id='1', parent='0')

def cell(name, text, x, y, w, h, style):
    item = ET.SubElement(root, 'mxCell', id=name, value=text, style=style, vertex='1', parent='1')
    ET.SubElement(item, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})
    return item

def label(name, text, x, y, w, h=36, size=22, color=NAVY, bold=False, align='left', extra=''):
    return cell(name, text, x, y, w, h,
        f'text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;{FONT}fontSize={size};'
        f'fontColor={color};fontStyle={1 if bold else 0};align={align};verticalAlign=middle;spacing=0;{extra}')

def box(name, x, y, w, h, fill='#FFFFFF', stroke='#D6DEE8', dash=False, radius=8):
    return cell(name, '', x, y, w, h,
        f'rounded=1;absoluteArcSize=1;arcSize={radius};html=1;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};'
        f'strokeWidth=1.5;dashed={1 if dash else 0};pointerEvents=0;')

def icon(name, asset, x, y, size=72):
    data = quote((ASSETS / (asset + '.svg')).read_text(), safe='')
    return cell(name, '', x, y, size, size,
        'shape=image;imageAspect=0;aspect=fixed;verticalAlign=top;align=center;'
        'strokeColor=none;fillColor=none;image=data:image/svg+xml,' + data + ';')

def service(name, asset, title, caption, x, y, width=310):
    icon(name, asset, x, y, 64)
    label(name+'-title', title, x+82, y-1, width-82, 32, 21, bold=True)
    label(name+'-caption', caption, x+82, y+34, width-82, 53, 18, '#5F7185')

def edge(name, source, target, text='', color=BLUE, points=(), extra='', dashed=False):
    e = ET.SubElement(root, 'mxCell', id=name, source=source, target=target, value=text, edge='1', parent='1',
        style=f'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=20;html=1;'
        f'endArrow=block;endFill=1;strokeWidth=2.4;strokeColor={color};fontColor={color};'
        f'fontSize=17;{FONT}labelBackgroundColor=#FFFFFF;dashed={1 if dashed else 0};{extra}')
    g = ET.SubElement(e, 'mxGeometry', relative='1', **{'as':'geometry'})
    if points:
        arr = ET.SubElement(g, 'Array', **{'as':'points'})
        for x,y in points: ET.SubElement(arr, 'mxPoint', x=str(x), y=str(y))

# Clear hierarchy: AWS region > VPC > public subnets / actual AZ placement.
box('header', 40, 30, 2280, 95, NAVY, NAVY)
label('title', 'PALS  /  AWS ARCHITECTURE', 68, 43, 1500, 48, 36, '#FFFFFF', True)
label('subtitle', '東京 ap-northeast-1  ·  保存済み配備記録 seq15  ·  2026-11-02', 70, 91, 2100, 25, 19, '#CDD7E5')
box('aws', 430, 160, 1865, 1190, '#FAFBFD', '#869BB3')
label('region', 'AWS Cloud  /  Tokyo Region', 455, 170, 900, 40, 25, bold=True)
box('vpc-frame', 460, 235, 1410, 1050, '#FFFFFF', '#8297B1')
icon('vpc', 'vpc', 478, 247, 44)
label('vpc-label', 'Amazon VPC  /  10.42.0.0/16', 537, 251, 1120, 35, 23, bold=True)
box('public', 495, 315, 1340, 185, '#F2F6FC', '#A4B8D4')
label('public-label', 'Public subnets   1a: 10.42.0.0/24   /   1c: 10.42.1.0/24', 515, 321, 1290, 32, 20, '#37567B', True)
box('az-a', 495, 535, 805, 670, '#FCFDFE', '#CED8E5')
box('az-c', 1380, 535, 455, 670, '#FCFDFE', '#CED8E5')
label('az-a-label', 'AZ  /  ap-northeast-1a', 515, 543, 765, 33, 22, bold=True)
label('az-c-label', 'AZ  /  ap-northeast-1c', 1400, 543, 420, 33, 22, bold=True)
for name, y, height, title, fill, stroke in [
    ('control-subnet',590,175,'Private control  /  10.42.20.0/24','#F1F8F4','#ABD0BC'),
    ('compute-subnet',800,185,'Private compute  /  10.42.30.0/24','#FFF8EF','#DEBF91'),
    ('db-a-subnet',1020,160,'Isolated DB  /  10.42.10.0/24','#F5F1FA','#C4B1D8')]:
    box(name,515,y,765,height,fill,stroke);label(name+'-label',title,532,y+5,730,30,19,bold=True)
for name, y, height, title, fill, stroke in [
    ('control-c-subnet',590,175,'Private control  /  10.42.21.0/24','#F7FAF8','#CBDDD2'),
    ('compute-c-subnet',800,185,'Private compute  /  10.42.31.0/24','#FFFBF5','#E3D7C4'),
    ('db-c-subnet',1020,160,'Isolated DB  /  10.42.11.0/24','#F5F1FA','#C4B1D8')]:
    box(name,1400,y,415,height,fill,stroke);label(name+'-label',title,1414,y+8,390,30,18,bold=True)

# External participants: no AWS icon is used to pretend Cloudflare/OpenAI is AWS.
icon('users','users',135,350,90)
label('users-label','利用者 / ブラウザー',45,448,280,42,23,bold=True,align='center')
cell('cloudflare','',110,560,140,90,'shape=cloud;whiteSpace=wrap;html=1;fillColor=#FFF2E3;strokeColor=#D9903B;strokeWidth=2;')
label('cloudflare-label','Cloudflare',45,656,280,38,25,bold=True,align='center')
label('cloudflare-caption','DNS / Proxy<br>palschat.site · api.palschat.site',30,698,315,66,18,'#5F7185',align='center')
box('openai-card',50,1060,285,145,'#F3F6F9','#C8D1DD')
label('openai','OpenAI API',75,1080,240,40,25,bold=True,align='center')
label('openai-note','外部サービス<br>workerから HTTPS 443',65,1125,255,62,19,'#5F7185',align='center')

# AWS service/resource icons from the official July 2026 package.
icon('waf','waf',540,355,66)
label('waf-label','AWS WAF',520,439,180,30,20,bold=True)
label('waf-note','ALBへ関連付け',520,467,220,22,16,'#5F7185')
icon('alb','alb',870,365,78)
label('alb-label','Application Load Balancer',730,445,400,28,21,bold=True,align='center')
label('alb-note','1a / 1c  ·  HTTPS 443',790,474,300,22,17,'#5F7185',align='center')
icon('acm','acm',1220,370,60)
label('acm-label','ACM / TLS',1150,439,250,30,19,bold=True)
icon('nat','nat',1500,370,64)
label('nat-label','NAT Gateway',1430,439,220,28,20,bold=True,align='center')
label('nat-note','1aのみ / ×1',1440,471,200,23,17,'#5F7185',align='center')
icon('igw','igw',1710,375,60)
label('igw-label','Internet Gateway',1630,440,230,28,18,bold=True,align='center')

box('control',535,635,725,106)
icon('control-ec2','ec2',551,651,72)
label('control-title','Control  /  t4g.medium ×1',645,645,590,32,24,bold=True)
label('control-roles','Caddy  ·  Web  ·  API  ·  reconciler',645,684,590,30,20,'#5F7185')
label('control-noip','ARM64 / 公開IPv4なし',1015,713,225,22,15,'#5F7185',align='right')
box('compute',535,845,725,116)
icon('compute-ec2','ec2',551,865,72)
label('compute-title','Compute  /  r8a.large ×1',645,853,590,33,24,bold=True)
label('compute-roles','評価worker  ·  証明worker  ·  Lean verifier',645,892,600,30,20,'#5F7185')
label('compute-noip','AMD64 / 公開IPv4なし',1015,933,225,22,15,'#5F7185',align='right')
label('control-c-empty','subnetのみ<br>待機EC2・フェイルオーバーなし',1425,650,365,80,21,'#7D8C9D',align='center')
label('compute-c-empty','subnetのみ<br>ASG / 自動増減は未実装',1425,862,365,80,21,'#7D8C9D',align='center')
label('db-a-empty','DB subnet group の一部<br>インターネット向けdefault routeなし',540,1070,710,65,21,'#7D8C9D',align='center')
box('database',1415,1065,385,100)
icon('aurora','aurora',1428,1080,65)
label('aurora-title','Amazon Aurora',1510,1071,280,30,22,bold=True)
label('aurora-note','PostgreSQL 16 / pgvector<br>writer ×1・readerなし',1510,1104,275,54,17,'#5F7185')
box('s3-endpoint-card',1030,1214,700,50,'#F3FAF6','#B9D8CA')
icon('s3-endpoint','vpc',1040,1220,38)
label('s3-endpoint-label','S3 Gateway Endpoint / control・computeの経路',1092,1222,620,32,18,GREEN,True)

# Regional services sit outside the VPC/subnet boundary.
label('regional-title','Regional services',1900,242,360,38,23,bold=True)
service('cognito','cognito','Amazon Cognito','利用者認証',1920,300)
service('sqs','sqs','Amazon SQS','評価・証明キュー<br>+ Dead-letter queues',1920,500)
service('s3','s3','Amazon S3','非公開の資料・成果物<br>Gateway Endpoint経由',1920,720)
box('network-note',1900,895,360,355,'#F3F6FA','#D4DEE9')
label('security-title','通信と隔離',1920,910,315,35,22,bold=True)
label('security-note','• DBへの接続はcontrolのみ<br><br>• verifierは外向き通信なし<br>  DB / AWS / LLM資格情報なし<br><br>• アプリ外向き通信は<br>  NAT経由のTCP 443<br><br>• EC2へのSSH公開なし',1920,957,320,270,19,'#52677F')

# Network paths; distinct corridors avoid crossing workload text.
edge('browser-proxy','users','cloudflare','HTTPS',extra='exitX=0.5;exitY=1;entryX=0.5;entryY=0;')
edge('proxy-alb','cloudflare','alb','HTTPS 443',points=[(410,605),(410,428),(850,428)],extra='exitX=1;exitY=0.5;entryX=0;entryY=0.8;')
edge('waf-association','waf','alb','保護',PURPLE,extra='exitX=1;exitY=0.3;entryX=0;entryY=0.25;',dashed=True)
edge('certificate','acm','alb','証明書',PURPLE,extra='exitX=0;exitY=0.45;entryX=1;entryY=0.45;',dashed=True)
edge('alb-control','alb','control','',points=[(917,520),(1180,520)],extra='exitX=0.6;exitY=1;entryX=0.89;entryY=0;')
edge('verify','control','compute','reconciler → verifier / mTLS 18117',points=[(760,790)],extra='exitX=0.28;exitY=1;entryX=0.28;entryY=0;')
edge('worker-api','compute','control','worker → API / HTTPS 443',PURPLE,points=[(1125,790)],extra='exitX=0.8;exitY=0;entryX=0.8;entryY=1;')
edge('control-db','control','database','TLS 5432',points=[(1330,683),(1330,1115)],extra='exitX=1;exitY=0.45;entryX=0;entryY=0.5;')
edge('control-nat','control','nat','',ORANGE,[(1310,655),(1310,515),(1532,515)],'exitX=1;exitY=0.2;entryX=0.5;entryY=1;')
edge('compute-nat','compute','nat','',ORANGE,[(1310,868),(1310,515),(1532,515)],'exitX=1;exitY=0.2;entryX=0.5;entryY=1;')
edge('nat-igw','nat','igw','443',ORANGE,extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('internet-model','igw','openai-card','HTTPS 443',ORANGE,[(1740,225),(400,225),(400,1130)],'exitX=0.5;exitY=0;entryX=1;entryY=0.5;')
edge('aws-apis','igw','sqs','HTTPS 443',ORANGE,[(1848,405),(1848,530)],'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('control-s3','control','s3-endpoint-card','',GREEN,[(1355,723),(1355,1207),(1275,1207)],'exitX=1;exitY=0.83;entryX=0.35;entryY=0;')
edge('compute-s3','compute','s3-endpoint-card','',GREEN,[(1355,941),(1355,1207),(1275,1207)],'exitX=1;exitY=0.83;entryX=0.35;entryY=0;')
edge('endpoint-s3','s3-endpoint-card','s3','HTTPS 443',GREEN,[(1850,1238),(1850,754)],'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('authentication','users','cognito','認証 / HTTPS 443',PURPLE,[(180,213),(1952,213)],'exitX=0.5;exitY=0;entryX=0.5;entryY=0;',True)

# Operations are not part of the verifier's execution/credential boundary.
label('operations-title','AWS 管理・運用サービス（グローバル機能を含む）',460,1345,1835,25,17,'#5F7185')
box('operations',460,1375,1835,100,'#F8F9FC','#D6DEE8')
for x,name,asset,title,caption in [
 (478,'ssm','ssm','Systems Manager','SSO / ホスト操作'),
 (832,'ecr','ecr','Amazon ECR','コンテナイメージ'),
 (1186,'kms','kms','AWS KMS','秘密値 / 署名'),
 (1540,'logs','cloudwatch','CloudWatch','Auroraログ'),
 (1894,'budget','budgets','AWS Budgets','費用アラート')]:
    service(name,asset,title,caption,x,1390,340)
label('outside-note','実線: 通信開始方向<br>破線: 認証・設定の関連',45,1270,340,80,18,'#5F7185')
label('footer','EC2各1台・Aurora writer 1台・NAT 1台。2AZのsubnet配置は、アプリの冗長化を意味しません。',465,1300,1790,37,20,'#5F7185')
label('credit','AWS Architecture Icons · 2026-07-31 official package / ASG・大会モードは未実装。詳細と残作業はREADME・Issuesへ。',460,1490,1840,25,16,'#708296')
ET.indent(mxfile, space='  ')
DEST.write_text(ET.tostring(mxfile, encoding='unicode')+'\n')
print(DEST)
