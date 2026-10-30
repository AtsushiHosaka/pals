#!/usr/bin/env python3
"""Build editable draw.io XML. PNG must be exported with actual draw.io Desktop."""
from pathlib import Path
from xml.etree import ElementTree as ET

DEST = Path(__file__).with_name('pals-aws-private-target.drawio')
mxfile = ET.Element('mxfile', host='app.diagrams.net', agent='PALS architecture authoring', version='32.6.1')
diagram = ET.SubElement(mxfile, 'diagram', id='pals-private-target', name='AWS target architecture')
model = ET.SubElement(diagram, 'mxGraphModel', dx='2200', dy='1500', grid='1', gridSize='10', guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1', pageScale='1', pageWidth='2200', pageHeight='1750', background='#ffffff', math='0', shadow='0')
root = ET.SubElement(model, 'root')
ET.SubElement(root, 'mxCell', id='0')
ET.SubElement(root, 'mxCell', id='1', parent='0')
font = 'fontFamily=Hiragino Sans,Noto Sans JP,Arial;fontColor=#182b49;'

def box(i, text, x, y, w, h, fill='#ffffff', stroke='#6784a2', size=20, extra=''):
    c = ET.SubElement(root, 'mxCell', id=i, value=text, style=f'rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor={fill};strokeColor={stroke};strokeWidth=1.5;fontSize={size};spacing=10;{font}{extra}', vertex='1', parent='1')
    ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as':'geometry'})
    return i

def text(i, value, x, y, w, h, size=18, color='#334e6d', extra=''):
    return box(i, value, x, y, w, h, 'none', 'none', size, f'align=left;verticalAlign=middle;spacing=0;fontColor={color};{extra}')

def zone(i, label, x, y, w, h, fill, stroke):
    return box(i,label,x,y,w,h,fill,stroke,19,'align=left;verticalAlign=top;spacing=0;spacingLeft=16;spacingTop=8;fontStyle=1;arcSize=5;')

def edge(i, source, target, label='', color='#1769aa', dashed=False, points=(), extra=''):
    c = ET.SubElement(root, 'mxCell', id=i, value=label, edge='1', parent='1', source=source, target=target,
       style=f'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=20;html=1;endArrow=block;endFill=1;strokeColor={color};strokeWidth=2.2;fontSize=16;fontFamily=Hiragino Sans,Arial;fontColor={color};labelBackgroundColor=#ffffff;spacing=5;'+('dashed=1;dashPattern=6 4;' if dashed else '')+extra)
    g=ET.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'})
    if i=='e_verify_a': g.set('x','-0.5')
    if i=='e_worker_api': g.set('x','0.5')
    if points:
        arr=ET.SubElement(g,'Array',**{'as':'points'})
        for x,y in points: ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))

# Containers first, so that all connections and nodes remain editable and readable.
box('header','<b>PALS AWS移行</b>　private subnetを中心にした構成',40,28,2100,65,'#142d4e','#142d4e',30,'fontColor=#ffffff;align=left;spacingLeft=24;')
text('subtitle','2026年10月30日　通常は小さく運用し、大会前に計算ノードを事前増強',50,105,1410,40,21)
box('status','<b>移行先の設計図 / 未配備</b>',1590,107,540,42,'#fff1d6','#d68b19',20,'fontColor=#8b5207;')
zone('region','AWS 東京リージョン　ap-northeast-1',35,315,2110,1295,'#f7f9fc','#a1b2c4')
zone('vpc','Terraform管理VPC　10.42.0.0/16（設計値）　既存データ・認証は維持',60,357,1535,1220,'#ffffff','#537d65')
zone('public','Public subnets　外部からの入口はALBのみ',80,400,1495,220,'#fff6e9','#cf9f55')
zone('pub_a','AZ-A / Public-A　10.42.0.0/24',100,500,710,110,'#fffaf2','#dbc6a7')
zone('pub_b','AZ-B / Public-B　10.42.1.0/24',835,500,710,110,'#fffaf2','#dbc6a7')
zone('private','Private control subnets　EC2はpublic IPv4なし',80,655,1495,220,'#edf8f0','#68a37a')
zone('priv_a','AZ-A / Control-A　10.42.20.0/24',100,705,710,150,'#f7fcf8','#a6ceb1')
zone('priv_b','AZ-B / Control-B　10.42.21.0/24',835,705,710,150,'#f7fcf8','#a6ceb1')
zone('compute_zone','Private compute subnets　EC2はpublic IPv4なし',80,910,1495,255,'#fff7ed','#c99858')
zone('compute_zone_a','AZ-A / Compute-A　10.42.30.0/24',100,955,710,190,'#fffcf6','#ddc8a6')
zone('compute_zone_b','AZ-B / Compute-B　10.42.31.0/24',835,955,710,190,'#fffcf6','#ddc8a6')
zone('dbs','Isolated DB subnets　インターネット向けdefault routeなし',80,1195,1495,185,'#f1effa','#9d8bbf')
zone('db_a','AZ-A / DB-A　10.42.10.0/24',100,1240,710,125,'#faf9fd','#c4b9d8')
zone('db_b','AZ-B / DB-B　10.42.11.0/24',835,1240,710,125,'#faf9fd','#c4b9d8')
zone('asg','計算ノード ASG　normal = large ×1〜4 / event = xlarge ×4を事前起動',120,995,1400,140,'none','#c87526')

# Public and external components.
box('user','<b>利用者</b><br>ブラウザー',60,180,200,90,'#e9f2ff','#4d83bc',22)
box('dns','<b>現在のDNS管理元を維持</b><br>palschat.site<br>api.palschat.site',340,180,365,100,'#f2f5f8','#70879e',20)
box('acm','<b>ACM 証明書</b><br>公開ドメインのTLS',780,180,285,90,'#f7ecff','#9564b3',20)
box('operator','<b>運用者</b><br>AWS SSO / 容量CLI',1130,180,290,90,'#edf0fb','#6e77b8',20)
box('cognito','<b>Cognito</b><br>利用者の認証',1450,180,220,90,'#f7ecff','#9564b3',20)
box('llm','<b>外部LLM API</b><br>HTTPS 443 / API keyはworkerのみ',1720,180,390,90,'#fff0e5','#cc8b51',20)
box('alb','<b>Internet-facing ALB</b><br>HTTPS 443 / ACM　HTTP 80 → 443',620,425,470,65,'#fff0d9','#c98628',20)
box('nat','<b>NAT Gateway</b><br>初期はAZ-Aに1台',130,545,235,60,'#ffe9d2','#cb7838',19)
box('alb_a','ALB のAZ-A側',510,545,250,60,'#fff0d9','#c98628',19)
box('alb_b','ALB のAZ-B側',880,545,250,60,'#fff0d9','#c98628',19)
box('igw','<b>Internet Gateway</b>',1240,435,285,50,'#fff0d9','#c98628',20)

# Workload components.
box('control','<b>t4g.medium ×1</b><br>2 vCPU / 4GiB<br>Web・API・Caddy<br>reconciler・既存の直列OCR',130,745,420,100,'#e2efff','#3c79b3',18,'spacing=4;')
box('compute_a','<b>計算ノード</b><br>評価・証明worker / reviewer<br><b>隔離Lean verifier</b><br>normal: r8a.large / 1枠<br>2 vCPU・16GiB',170,1030,480,100,'#fff0df','#c87526',16,'spacing=4;')
box('compute_b','<b>ASGの追加ノード</b><br>event: r8a.xlarge / 各2枠<br>32GiB・4 vCPU<br>準備完了した枠だけ配送',880,1030,600,100,'#fff0df','#c87526',18,'dashed=1;spacing=4;')
box('control_b','<b>Control-B subnet</b><br>初期はcontrol EC2を置かない',880,745,600,100,'#f0f6ff','#94b2d0',19,'dashed=1;')
box('aurora','<b>Aurora PostgreSQL / pgvector</b><br>writer 1台・提供中は0 ACUにしない<br>control SGからTCP 5432のみ',330,1280,430,78,'#ede5fb','#8e6fb1',17,'shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=12;spacing=4;')
box('db_reserve','<b>DB subnet groupのもう一方のAZ</b><br>subnetの存在はreaderやDB二重化を意味しない',880,1280,600,65,'#f5f0fb','#b09bc7',18,'dashed=1;')
box('s3ep','<b>S3 Gateway Endpoint</b><br>control・computeからS3への経路',1165,1430,380,75,'#e2f6f0','#438873',19)
text('vpc_note','EC2・DBへの直接公開なし / SSHなし / verifierにDB・AWS・LLM資格情報を渡さない',110,1500,1015,45,17,'#365e4a')

# AWS regional services outside the VPC.
box('awsapis','<b>AWS API</b><br>SSM / ECR / STS / CloudWatch<br>private EC2からNAT経由のHTTPS',1675,415,420,130,'#eef2fb','#697eaf',20)
box('sqs','<b>SQS + DLQ</b><br>評価用 / 証明用<br>workerがNAT経由HTTPSで受信',1675,625,420,115,'#fff0e4','#bf8552',20)
box('s3','<b>S3</b><br>資料・成果物・バックアップ<br>private / 暗号化 / endpoint policy',1675,935,420,115,'#e5f6e8','#51945d',20)
box('ops','<b>SSM Automation / Auto Scaling</b><br>切替・readiness・drain<br>CloudWatchで段階別の待ちを観測<br>上限内で増設し、処理完了後に縮小',1675,1270,420,170,'#edf0fb','#6e77b8',19)

# Connectivity. Direction is the initiating side, not request+response duplication.
edge('e_auth','user','cognito','認証 HTTPS 443','#7956a1',True,[(160,160),(1560,160)],'exitX=0.5;exitY=0;entryX=0.5;entryY=0;')
edge('e_dns','user','dns','名前解決','#74859b',True)
edge('e_ingress','user','alb','HTTPS 443','#1769aa',False,[(260,305),(855,305)],'exitX=1;exitY=0.6;entryX=0.5;entryY=0;')
edge('e_dns_target','dns','alb','切替後 ALB を参照','#74859b',True,[(520,330),(590,330)],'exitX=0.5;exitY=1;entryX=0;entryY=0.3;')
edge('e_acm','acm','alb','証明書','#7956a1',True,[(940,330)],'exitX=0.5;exitY=1;entryX=0.7;entryY=0;')
edge('e_alb_a','alb','alb_a','','#c98628',True,[],'exitX=0.2;exitY=1;entryX=0.5;entryY=0;')
edge('e_alb_b','alb','alb_b','','#c98628',True,[],'exitX=0.8;exitY=1;entryX=0.5;entryY=0;')
edge('e_alb_control_a','alb_a','control','HTTPS 443','#1769aa',False,[(635,637),(270,637)],'exitX=0.5;exitY=1;entryX=0.5;entryY=0;')
edge('e_alb_control_b','alb_b','control','','#1769aa',False,[(1005,638),(525,638),(525,720),(500,720)],'exitX=0.5;exitY=1;entryX=0.9;entryY=0;')
edge('e_verify_a','control','compute_a','mTLS 18117','#1769aa',False,[],'exitX=0.8;exitY=1;entryX=0.8;entryY=0;')
edge('e_worker_api','compute_a','control','HTTPS 443','#7956a1',False,[],'exitX=0.2;exitY=0;entryX=0.2;entryY=1;')
edge('e_verify_b','control','compute_b','reconciler → verifier　mTLS 18117','#1769aa',False,[(575,890),(1560,890),(1560,1175),(1200,1175)],'exitX=1;exitY=0.9;entryX=0.5;entryY=1;')
edge('e_db','control','aurora','','#1769aa',False,[(70,835),(70,1310)],'exitX=0;exitY=0.9;entryX=0;entryY=0.5;')
edge('e_control_nat','control','nat','','#bf6f24',True,[(175,675)],'exitX=0.1;exitY=0;entryX=0.15;entryY=1;')
edge('e_compute_nat','compute_a','nat','','#bf6f24',True,[(95,1030),(95,620),(340,620)],'exitX=0;exitY=0;entryX=0.9;entryY=1;')
edge('e_nat_igw','nat','igw','','#bf6f24',True,[(395,500),(1375,500)],'exitX=1;exitY=0.3;entryX=0.5;entryY=1;')
edge('e_igw_aws','igw','awsapis','HTTPS 443','#bf6f24',True,[],'exitX=1;exitY=0.5;entryX=0;entryY=0.3;')
edge('e_igw_llm','igw','llm','HTTPS 443','#bf6f24',True,[(1560,380),(1900,380)],'exitX=1;exitY=0.2;entryX=0.5;entryY=1;')
edge('e_worker_sqs','compute_b','sqs','','#bf6f24',True,[(1590,1070),(1590,685)],'exitX=1;exitY=0.35;entryX=0;entryY=0.5;')
edge('e_app_s3','control','s3ep','','#36816c',False,[(575,880),(1560,880),(1560,1405),(1355,1405)],'exitX=0.9;exitY=1;entryX=0.5;entryY=0;')
edge('e_s3','s3ep','s3','HTTPS 443 / NATを通らない','#36816c',False,[(1610,1465),(1610,995)],'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('e_operator','operator','ops','','#7956a1',True,[(1450,300),(2130,300),(2130,1355)],'exitX=1;exitY=0.5;entryX=1;entryY=0.5;')
edge('e_ops_asg','ops','asg','','#7956a1',True,[(1615,1350),(1615,1175),(1535,1175)],'exitX=0;exitY=0.5;entryX=1;entryY=1;')

# Footer keeps the diagram's scope and known availability limits visible.
box('legend','<b>凡例</b>　青実線 = アプリ通信　橙破線 = NAT経由の外向き通信　紫破線 = 運用・制御　緑実線 = S3 endpoint経由',50,1635,2085,50,'#f3f6f9','#c4d0dc',18,'align=left;spacingLeft=18;')
text('limits','初期構成の可用性　Web・API 1台 / NAT 1台 / Aurora writer 1台。2AZのsubnetだけで全層が二重化されるわけではありません。',60,1695,2070,35,18,'#5d6674')
text('scope','実際の配備結果ではありません。DNS切替とデータ移行の完了後、AWSの構成を読み戻して配備図へ更新します。',60,1735,2070,35,18,'#8b5207')

ET.indent(mxfile, space='  ')
DEST.write_text(ET.tostring(mxfile, encoding='unicode')+'\n', encoding='utf-8')
print(DEST)
