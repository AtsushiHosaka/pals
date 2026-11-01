#!/usr/bin/env python3
"""Generate the editable seq11 architecture snapshot; export PNG with draw.io.

Evidence: signed seq11 manifest and actual both-host/catalog read-back receipts,
docs/aws-security-and-catalog-check-2026-10-31.md. No AWS calls are made.
All coordinates, labels and connectors below are diagram source, not an image.
"""
from pathlib import Path
from xml.etree import ElementTree as ET

DEST = Path(__file__).with_name('pals-aws-private-target.drawio')
WIDTH, HEIGHT = 2440, 1980
mxfile = ET.Element('mxfile', host='app.diagrams.net', agent='PALS architecture authoring', version='32.6.1')
diagram = ET.SubElement(mxfile, 'diagram', id='pals-private-current', name='AWS deployed architecture — seq11 2026-11-02')
model = ET.SubElement(diagram, 'mxGraphModel', dx=str(WIDTH), dy=str(HEIGHT), grid='1', gridSize='10', guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1', pageScale='1', pageWidth=str(WIDTH), pageHeight=str(HEIGHT), background='#ffffff', math='0', shadow='0')
root = ET.SubElement(model, 'root')
ET.SubElement(root, 'mxCell', id='0')
ET.SubElement(root, 'mxCell', id='1', parent='0')
FONT = 'fontFamily=Hiragino Sans,Noto Sans JP,Arial;fontColor=#18314e;'


def box(identifier, value, x, y, w, h, fill='#ffffff', stroke='#8ca4c0', size=21, extra=''):
    cell = ET.SubElement(root, 'mxCell', id=identifier, value=value,
        style=f'rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=1.5;fontSize={size};{FONT}align=left;verticalAlign=middle;spacing=14;{extra}', vertex='1', parent='1')
    ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})


def zone(identifier, value, x, y, w, h, fill, stroke):
    box(identifier, value, x, y, w, h, fill, stroke, 23,
        'verticalAlign=top;spacingTop=12;spacingLeft=18;fontStyle=1;')


def edge(identifier, source, target, value='', color='#2467a0', points=(), extra=''):
    cell = ET.SubElement(root, 'mxCell', id=identifier, source=source, target=target,
        value=value, edge='1', parent='1',
        style=f'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=20;html=1;endArrow=block;endFill=1;strokeWidth=2.5;strokeColor={color};fontColor={color};fontSize=18;fontFamily=Hiragino Sans,Arial;labelBackgroundColor=#ffffff;{extra}')
    geometry = ET.SubElement(cell, 'mxGeometry', relative='1', **{'as': 'geometry'})
    if points:
        array = ET.SubElement(geometry, 'Array', **{'as': 'points'})
        for x, y in points:
            ET.SubElement(array, 'mxPoint', x=str(x), y=str(y))


# Zones are drawn first. Boxes remain individually editable in draw.io.
box('title', '<b>PALS AWS 本番アーキテクチャ</b>', 40, 25, 2360, 65, '#142d4e', '#142d4e', 32, 'fontColor=#ffffff;')
box('snapshot', '<b>2026年11月2日 00:25 JST の配備記録 / seq11</b><br>全7コンテナ・private TLS・DB確認35段階・復旧設定を確認して公開を再開。既存カタログ9項目を保持。自然数冪の登録済み入力で公開実測4.66〜4.83秒。<br>Parent f6f02bc / API 9b8b004 / Worker 122f2f9 / Infra 46f4010 / Web a74b57b / manifest a22a5f2f0a98', 40, 105, 2360, 110, '#eaf7ee', '#579a72', 21)
zone('region', 'AWS 東京リージョン / ap-northeast-1', 40, 410, 2360, 1330, '#f6f8fc', '#8ca4c0')
zone('vpc', 'VPC 10.42.0.0/16 / 2 AZ: ap-northeast-1a・1c', 65, 460, 1650, 1235, '#ffffff', '#6f8eaf')
zone('public', 'Public subnets / 1a: 10.42.0.0/24・1c: 10.42.1.0/24', 90, 515, 1600, 235, '#edf4fd', '#8db1d9')
zone('control_zone', 'Private control / 1a: 10.42.20.0/24・1c: 10.42.21.0/24', 90, 785, 1600, 240, '#eff8f3', '#8bbba7')
zone('compute_zone', 'Private compute / 1a: 10.42.30.0/24・1c: 10.42.31.0/24', 90, 1080, 1600, 235, '#fff7ed', '#c6a46d')
zone('database_zone', 'Isolated DB / 1a: 10.42.10.0/24・1c: 10.42.11.0/24', 90, 1370, 1600, 215, '#f3effa', '#a995c9')

# Public entry and authentication.
box('user', '<b>利用者</b><br>ブラウザー', 70, 255, 220, 100, '#edf3fa')
box('cloudflare', '<b>Cloudflare DNS / Proxy</b><br>palschat.site・api.palschat.site<br>両方ともAWS ALBへ / Full (strict)', 400, 235, 520, 135, '#eaf7ee', '#579a72')
box('cognito', '<b>Cognito</b><br>既存の利用者認証を継続', 1800, 510, 530, 125, '#f4effb', '#aa95c4')
box('operator', '<b>運用者</b><br>AWS SSO → Systems Manager<br>SSHポート・踏み台なし', 1790, 235, 550, 135, '#f4effb', '#aa95c4')
box('alb', '<b>WAF → Internet-facing ALB</b><br>HTTPS 443 / ACM証明書<br>Cloudflare公式IPv4のみ許可・既定BLOCK<br>root優先rule / API既定rule → 同じcontrol EC2', 120, 575, 760, 140, '#eaf7ee', '#579a72', 21)
box('nat', '<b>NAT Gateway ×1 / AZ 1a</b><br>private hostの外向き通信', 1060, 600, 370, 100, '#fff1df', '#cf9a56', 20)
box('igw', '<b>IGW</b>', 1510, 600, 150, 100, '#edf4fd', '#8db1d9', 22)

# Exactly four control and three compute containers are deployed.
box('control', '<b>Control EC2 / t4g.medium ×1 / ARM64</b><br>2 vCPU・4 GiB / 10.42.20.43 / public IPv4なし<br><b>Web・API・Caddy・reconciler</b><br>ALB → Caddy → Web/API / APIからAuroraへTLS接続', 135, 850, 745, 145, '#eaf7ee', '#579a72', 22)
box('control_reserve', '<b>Control 1c: subnetのみ</b><br>EC2の二重化は未実施<br>Web containerの外向き通信はDROP', 1130, 855, 510, 135, '#f7fafc', '#a4b6c7', 21, 'dashed=1;')
box('compute', '<b>Compute EC2 / r8a.large ×1 / AMD64</b><br>2 vCPU・16 GiB / 10.42.30.100 / public IPv4なし<br><b>評価worker・証明worker・Lean verifier</b><br>verifierへDB・AWS・LLMの資格情報を渡さない', 135, 1140, 745, 145, '#fff0df', '#c99552', 22)
box('capacity', '<b>Compute 1c: subnetのみ</b><br>通常large → 大会xlargeは今後の切替機能<br>ASG・自動増減・30人負荷検証は未実施', 1130, 1150, 510, 125, '#fffcf7', '#c9b28e', 21, 'dashed=1;')
box('database', '<b>Aurora PostgreSQL 16.15 / pgvector</b><br>private endpoint / writer ×1・readerなし<br>control SG → 5432のみ / TLS verify-full・保存時暗号化<br>Draft 433件・Recipe登録102件・検索公開20件', 135, 1430, 745, 135, '#efe7fa', '#9d83bd', 21)
box('old_database', '<b>旧方式DB EC2: 停止済み</b><br>10.42.10.172 / m7g.large・EBS保持<br>専用interface endpoint ×6とS3 endpointは残存<br>Auroraの接続先ではない', 1130, 1430, 510, 135, '#f7f3fc', '#ac98c6', 20)
box('s3_endpoint', '<b>S3 Gateway Endpoint</b>　control・compute用 / DB専用とは分離', 800, 1615, 830, 55, '#e2f3ef', '#639f8d', 21)

# Regional / external services: endpoint placement is not a private subnet.
box('llm', '<b>外部LLM API / チャットで選択</b><br>Lean: 6.1 Terra / 6.1 Sol / 6 Luna<br>推論量: low / medium / high<br>その他の役割: 既存設定 / HTTPS・NAT', 1080, 235, 520, 135, '#fff1df', '#cf9a56', 20)
box('sqs', '<b>SQS + DLQ</b><br>評価・証明キュー / 既存を継続<br>workerがHTTPS 443で受信 / NAT経由', 1800, 710, 530, 125, '#fff1df', '#cf9a56', 22)
box('aws_api', '<b>SSM / ECR / CloudWatch / KMS</b><br>control・compute host → HTTPS 443 / NAT<br>SSM SecureString・KMSで秘密値管理<br>SSM経由の操作 / IMDSv2必須', 1800, 910, 530, 160, '#f4effb', '#aa95c4', 21)
box('s3', '<b>S3 / private・暗号化</b><br>資料・成果物・移行データ<br>Gateway Endpoint経由 / NATを通らない', 1800, 1160, 530, 125, '#e2f3ef', '#639f8d', 22)
box('operations', '<b>運用・費用・復旧</b><br>復旧unit 3本: 有効・待機中 / 実再起動試験は未実施<br>料金通知: 実額20・50・100・650 USD、予測520 USD<br>通知の実配信は未検証 / 一時参照権限は削除済み', 1800, 1405, 530, 200, '#f4effb', '#aa95c4', 21)

# Arrows denote the initiating side. Return traffic is omitted.
edge('e_user_proxy', 'user', 'cloudflare', 'HTTPS 443', extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('e_user_auth', 'user', 'cognito', '認証 / HTTPS 443', '#7956a1', [(180,225),(1740,225),(1740,570)], 'exitX=0.5;exitY=0;entryX=0;entryY=0.5;')
edge('e_proxy_alb', 'cloudflare', 'alb', 'HTTPS 443', points=[(660,390),(500,390)], extra='exitX=0.5;exitY=1;entryX=0.5;entryY=0;')
edge('e_alb_control', 'alb', 'control', 'HTTPS 443', extra='exitX=0.5;exitY=1;entryX=0.5;entryY=0;')
edge('e_verifier', 'control', 'compute', 'reconciler → verifier / mTLS 18117', points=[(320,1050)], extra='exitX=0.25;exitY=1;entryX=0.25;entryY=0;')
edge('e_worker_api', 'compute', 'control', 'worker → API / HTTPS 443', '#7956a1', [(700,1050)], 'exitX=0.8;exitY=0;entryX=0.8;entryY=1;')
edge('e_db', 'control', 'database', 'TLS 5432', points=[(110,1020),(110,1490)], extra='exitX=0;exitY=0.9;entryX=0;entryY=0.5;')
# Egress and S3 routes use routing corridors outside the workload boxes.
edge('e_control_nat', 'control', 'nat', 'host外向き', '#b5792d', [(1000,900),(1000,650)], 'exitX=1;exitY=0.35;entryX=0;entryY=0.5;')
edge('e_compute_nat', 'compute', 'nat', 'worker/host外向き', '#b5792d', [(1040,1200),(1040,740),(1245,740)], 'exitX=1;exitY=0.4;entryX=0.5;entryY=1;')
edge('e_nat_igw', 'nat', 'igw', 'HTTPS', '#b5792d', extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
edge('e_igw_llm', 'igw', 'llm', '443', '#b5792d', [(1700,650),(1700,385),(1340,385)], 'exitX=1;exitY=0.5;entryX=0.5;entryY=1;')
edge('e_igw_sqs', 'igw', 'sqs', '443', '#b5792d', [(1760,650),(1760,770)], 'exitX=1;exitY=0.7;entryX=0;entryY=0.5;')
edge('e_igw_aws', 'igw', 'aws_api', '443', '#b5792d', [(1725,670),(1725,990)], 'exitX=1;exitY=0.9;entryX=0;entryY=0.5;')
edge('e_ssm_operator', 'operator', 'aws_api', 'SSO / SSM操作', '#7956a1', [(2370,300),(2370,990)], 'exitX=1;exitY=0.5;entryX=1;entryY=0.5;')
edge('e_control_s3ep', 'control', 's3_endpoint', 'S3経路', '#36816c', [(920,960),(920,1595),(1020,1595)], 'exitX=1;exitY=0.8;entryX=0.25;entryY=0;')
edge('e_compute_s3ep', 'compute', 's3_endpoint', '', '#36816c', [(960,1260),(960,1595),(1420,1595)], 'exitX=1;exitY=0.8;entryX=0.75;entryY=0;')
edge('e_s3ep_s3', 's3_endpoint', 's3', 'HTTPS 443', '#36816c', [(1750,1640),(1750,1220)], 'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')

box('legend', '<b>矢印は通信の開始方向</b>　青: 公開・API・DB・verifier通信 / 橙: NAT経由の外向き通信 / 緑: S3 endpoint経由 / 紫: 認証・運用<br>EC2・DBへ直接公開なし。compute → Auroraの通信は許可しない。DB subnetにインターネット向けdefault routeなし。', 40, 1765, 2360, 80, '#edf3fa', '#a7bacd', 22)
box('limits', '<b>未完了の項目</b>　1秒回答・30人を10秒以内・1,100件の本番利用・ASG/自動増減・全体セキュリティ監査。<br>control・compute・NAT・Aurora writerは各1台。2 AZのsubnetだけでアプリが冗長化されるわけではない。Auroraはpending-reboot。', 40, 1860, 2360, 80, '#fff2df', '#cfad79', 21)
ET.indent(mxfile, space='  ')
DEST.write_text(ET.tostring(mxfile, encoding='unicode')+'\n', encoding='utf-8')
print(DEST)
