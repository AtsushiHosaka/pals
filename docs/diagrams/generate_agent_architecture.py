#!/usr/bin/env python3
"""Generate the PALS system + agent-flow diagram (two pages) as draw.io XML.

No network, AWS or application operations. Icons are read unmodified from
assets/aws-2026-07 (AWS) and assets/brand-icons (Simple Icons, CC0).
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
AWS = HERE / 'assets/aws-2026-07'
BRAND = HERE / 'assets/brand-icons'
DEST = HERE / 'pals-architecture.drawio'

provenance = json.loads((AWS / 'provenance.json').read_text())
for name, ref in provenance['unmodified_svg_files'].items():
    assert hashlib.sha256((AWS / (name + '.svg')).read_bytes()).hexdigest() == ref['sha256']

FONT = 'fontFamily=Hiragino Sans,Noto Sans JP,Arial;'
INK = '#202A36'
BLUE, PURPLE, TEAL, GREEN, ORANGE, RED, GRAY = '#2F6FB0', '#8C4FD0', '#2A8C82', '#3B8F4A', '#D9822B', '#C0392B', '#6B7785'


class Page:
    def __init__(self, mxfile, pid, name, w, h):
        d = ET.SubElement(mxfile, 'diagram', id=pid, name=name)
        m = ET.SubElement(d, 'mxGraphModel', dx=str(w), dy=str(h), grid='1', gridSize='10', guides='1',
                          tooltips='1', connect='1', arrows='1', fold='1', page='1', pageScale='1',
                          pageWidth=str(w), pageHeight=str(h), background='#FFFFFF', math='0', shadow='0')
        self.root = ET.SubElement(m, 'root')
        ET.SubElement(self.root, 'mxCell', id='0')
        ET.SubElement(self.root, 'mxCell', id='1', parent='0')

    def cell(self, cid, value, x, y, w, h, style):
        c = ET.SubElement(self.root, 'mxCell', id=cid, value=value, style=style, vertex='1', parent='1')
        ET.SubElement(c, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), **{'as': 'geometry'})

    def text(self, cid, value, x, y, w, h, size=18, align='left', color=INK, bold=False):
        self.cell(cid, value, x, y, w, h,
                  f'text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;{FONT}fontSize={size};'
                  f'fontColor={color};align={align};verticalAlign=top;spacing=0;{"fontStyle=1;" if bold else ""}')

    def icon(self, cid, path, x, y, size, label='', label_w=240, label_size=18):
        svg = quote(path.read_text(), safe='')
        self.cell(cid, '', x, y, size, size,
                  'shape=image;imageAspect=0;aspect=fixed;strokeColor=none;fillColor=none;'
                  'image=data:image/svg+xml,' + svg + ';')
        if label:
            self.text(cid + '-label', label, x + (size - label_w) / 2, y + size + 8, label_w, 70, label_size, 'center')

    def zone(self, cid, x, y, w, h, color, label='', fill='none', dashed=True, label_color=None, size=20):
        self.cell(cid, '', x, y, w, h,
                  f'rounded=1;absoluteArcSize=1;arcSize=14;fillColor={fill};strokeColor={color};strokeWidth=2;'
                  + ('dashed=1;' if dashed else ''))
        if label:
            self.text(cid + '-label', label, x + 16, y + 10, w - 32, 34, size, 'left', label_color or color, True)

    def box(self, cid, value, x, y, w, h, stroke=INK, fill='#FFFFFF', dashed=False, size=17, width=2.4):
        self.cell(cid, value, x, y, w, h,
                  f'rounded=1;absoluteArcSize=1;arcSize=14;whiteSpace=wrap;html=1;fillColor={fill};'
                  f'strokeColor={stroke};strokeWidth={width};{FONT}fontSize={size};fontColor={INK};align=left;'
                  f'verticalAlign=top;spacingLeft=14;spacingRight=12;spacingTop=10;'
                  + ('dashed=1;dashPattern=8 5;' if dashed else ''))

    def edge(self, cid, src, tgt, label='', points=(), extra='', color=INK, dashed=False, both=False):
        e = ET.SubElement(self.root, 'mxCell', id=cid, source=src, target=tgt, value=label, edge='1', parent='1',
                          style='edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=20;html=1;'
                                f'endArrow=block;endFill=1;strokeWidth=2.4;strokeColor={color};{FONT}fontSize=17;'
                                f'fontColor={color};labelBackgroundColor=#FFFFFF;'
                                + ('dashed=1;dashPattern=8 5;' if dashed else '')
                                + ('startArrow=block;startFill=1;' if both else '') + extra)
        g = ET.SubElement(e, 'mxGeometry', relative='1', **{'as': 'geometry'})
        if points:
            arr = ET.SubElement(g, 'Array', **{'as': 'points'})
            for x, y in points:
                ET.SubElement(arr, 'mxPoint', x=str(x), y=str(y))


def chip(color, text):
    return f'<font color="{color}"><b>● {text}</b></font>'


def small(text):
    return f'<font style="font-size:16px" color="{GRAY}">{text}</font>'


mxfile = ET.Element('mxfile', host='app.diagrams.net', agent='PALS architecture', version='32.6.1')

# ---------------------------------------------------------------- page 1
p = Page(mxfile, 'system', '全体構成', 2440, 1330)
p.text('title', 'PALS アーキテクチャ ― 全体構成', 40, 28, 1200, 50, 34, bold=True)
p.text('subtitle', 'ap-northeast-1 本番（seq15）。実線は配備と挙動を確認した構成、破線はコード上は配線済みだが本番での使用を確認していない構成です。', 40, 80, 2000, 30, 18, color=GRAY)

p.icon('users', AWS / 'users.svg', 50, 470, 90, '利用者', 160)
p.icon('cloudflare', BRAND / 'cloudflare.svg', 220, 470, 90, 'Cloudflare<br>DNS・Proxy', 180)

p.zone('region', 360, 120, 1740, 1170, '#73A4BD', 'AWS  ap-northeast-1', label_color='#367391')
p.icon('cognito', AWS / 'cognito.svg', 410, 160, 80, 'Amazon Cognito<br>ログイン', 200)
p.zone('public', 390, 400, 180, 300, '#91B6A1', 'Public subnet', size=16, label_color='#47775C')
p.icon('alb', AWS / 'alb.svg', 435, 470, 90, 'ALB<br>WAF・ACM', 170, 16)

# control host
p.zone('control', 620, 330, 480, 520, ORANGE, 'EC2 t4g.medium　control', fill='#FFF8F0', dashed=False)
p.icon('control-ec2', AWS / 'ec2.svg', 1040, 336, 48)
p.box('caddy', '<b>Caddy</b>　TLS終端・ホスト名で振り分け', 650, 400, 420, 56, ORANGE, size=16)
p.box('web', '<b>Web</b>（Next.js）:3000', 650, 470, 420, 50, ORANGE, size=16)
p.box('api', '<b>API</b>（FastAPI）:8000<br>' + small('認証・課金・ジョブ投入・検索・判定の確定'), 650, 534, 420, 100, ORANGE, '#FFFFFF', size=17, width=3.4)
p.box('reconciler', '<b>Reconciler</b><br>' + small('Lean検証の依頼・結果確定を仲介'), 650, 735, 420, 90, ORANGE, size=16)

# SQS
p.zone('sqs-zone', 1160, 330, 270, 310, '#E7157B', 'Amazon SQS', fill='#FFF5FA', dashed=False)
p.icon('sqs', AWS / 'sqs.svg', 1372, 336, 48)
p.box('q-assess', '<b>assessment</b>キュー<br>' + small('＋DLQ'), 1180, 410, 230, 76, '#E7157B', size=16)
p.box('q-proof', '<b>proof</b>キュー<br>' + small('＋DLQ'), 1180, 520, 230, 76, '#E7157B', size=16)

# compute host
p.zone('compute', 1480, 330, 520, 560, ORANGE, 'EC2 r8a.large　compute', fill='#FFF8F0', dashed=False)
p.icon('compute-ec2', AWS / 'ec2.svg', 1940, 336, 48)
p.box('w-assess', '<b>評価worker</b>（assessment lane）<br>' + small('質問を評価し、再利用か新規生成かを判定'), 1510, 410, 460, 76, ORANGE, size=16)
p.box('w-proof', '<b>証明worker</b>（proof lane）<br>' + small('Lean証明の生成・修復・解説'), 1510, 520, 460, 76, ORANGE, size=16)
p.box('verifier', '<b>Lean verifier</b>（隔離コンテナ）<br>' + small('mTLS :18117 のみ受付<br>外向き通信なし・認証情報なし<br>workerにはコンパイラなし'), 1510, 690, 460, 170, RED, '#FFF3F1', dashed=True, size=17)

# Aurora
p.zone('aurora', 620, 930, 1290, 330, '#C925D1', 'Amazon Aurora PostgreSQL（isolated subnet・pgvector）', fill='#FDF6FE', dashed=False)
p.icon('aurora-icon', AWS / 'aurora.svg', 1850, 936, 48)
cards = [
    ('c-recipe', BLUE, False, 'Lean Recipe catalog', 'ベクトルなし',
     '検証済みLeanソース<br>・形式文SHA-256の厳密一致<br>・英語全文検索（上位8件）<br>・全件取得し、worker内でn-gramスコア'),
    ('c-draft', PURPLE, True, 'Draft catalog', 'pgvector(384)',
     '自然文の証明方針 433行<br>OpenMath正規形を埋め込み、コサイン距離で上位8件<br>配線済み・本番での使用は未確認'),
    ('c-typed', PURPLE, True, 'Typed catalog', '配列(384次元)',
     'pgvectorではなく、APIがコサイン計算して上位8件<br>機能フラグ（既定OFF）<br>本番での使用は未確認'),
    ('c-mat', TEAL, False, 'Project資料', 'ベクトルなし',
     '原本とOCRテキスト（Tesseract）<br>PostgreSQL全文検索で出典を取得'),
    ('c-app', GRAY, False, '業務データ', '',
     'チャット・証明ジョブ・解説<br>課金（Stripe ID）・トークン利用枠・ゲスト'),
]
for i, (cid, col, dashed, title, tag, body) in enumerate(cards):
    p.box(cid, f'<b>{title}</b><br>' + (chip(col, tag) + '<br>' if tag else '') + small(body),
          640 + i * 248, 990, 232, 250, col, '#FFFFFF', dashed=dashed, size=17)

# S3
p.icon('s3', AWS / 's3.svg', 1950, 1000, 80, 'Amazon S3<br>証明の成果物', 200)

# external
p.zone('external', 2150, 120, 270, 640, GRAY, '外部サービス', size=16)
p.icon('stripe', BRAND / 'stripe.svg', 2245, 160, 80, 'Stripe API<br>課金', 200)
p.icon('openai', BRAND / 'openai.svg', 2245, 400, 80, 'OpenAI API<br>Responses：GPT-6 Luna / Terra<br>Embeddings：<br>text-embedding-3-small', 250, 16)

# edges
p.edge('e-user-cf', 'users', 'cloudflare', extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
p.edge('e-cf-alb', 'cloudflare', 'alb', extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
p.edge('e-user-cognito', 'users', 'cognito', '', [(95, 200)], 'exitX=0.5;exitY=0;entryX=0;entryY=0.5;')
p.edge('e-alb-caddy', 'alb', 'caddy', 'HTTPS :443', [(600, 515), (600, 428)], 'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
p.text('l-api-db', 'APIからAurora<br>TLS :5432', 440, 850, 170, 60, 16, 'right')
p.edge('e-api-db', 'api', 'aurora', '', [(636, 584), (636, 930)], 'exitX=0;exitY=0.5;entryX=0.012;entryY=0;')
p.edge('e-api-q1', 'api', 'q-assess', 'ジョブ投入', [(1130, 584), (1130, 448)], 'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
p.edge('e-api-q2', 'api', 'q-proof', '', [(1130, 584), (1130, 558)], 'exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
p.edge('e-q1-w', 'q-assess', 'w-assess', '取得', extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
p.edge('e-q2-w', 'q-proof', 'w-proof', '取得', extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;')
p.edge('e-w-api', 'compute', 'control', 'HTTPS :443', [(1290, 660)], 'exitX=0;exitY=0.59;entryX=1;entryY=0.636;', both=True)
p.edge('e-rec-ver', 'reconciler', 'verifier', 'mTLS :18117', extra='exitX=1;exitY=0.5;entryX=0;entryY=0.5;', color=RED)
p.edge('e-api-stripe', 'control', 'stripe', '', [(860, 200)], 'exitX=0.5;exitY=0;entryX=0;entryY=0.5;')
p.edge('e-w1-openai', 'w-assess', 'openai', '', extra='exitX=1;exitY=0.5;entryX=0;entryY=0.4;')
p.edge('e-w2-openai', 'w-proof', 'openai', 'NAT経由', [(2060, 558), (2060, 465)], 'exitX=1;exitY=0.5;entryX=0;entryY=0.8;')
p.edge('e-w-s3', 'compute', 's3', '成果物を保存', extra='exitX=0.98;exitY=1;entryX=0.5;entryY=0;')

# legend (left column)
p.zone('legend', 40, 1000, 290, 300, GRAY, '凡例', size=18, dashed=False)
p.cell('lg-solid', '', 60, 1060, 50, 40, f'rounded=1;fillColor=#FFFFFF;strokeColor={INK};strokeWidth=2.4;')
p.text('lg-solid-t', '確認済みの構成', 120, 1068, 200, 30, 16)
p.cell('lg-dash', '', 60, 1112, 50, 40, f'rounded=1;fillColor=#FFFFFF;strokeColor={PURPLE};strokeWidth=2.4;dashed=1;dashPattern=8 5;')
p.text('lg-dash-t', '配線済み・本番での使用は未確認', 120, 1112, 200, 48, 16)
p.cell('lg-red', '', 60, 1170, 50, 40, f'rounded=1;fillColor=#FFF3F1;strokeColor={RED};strokeWidth=2.4;dashed=1;dashPattern=8 5;')
p.text('lg-red-t', '隔離コンテナ', 120, 1178, 200, 30, 16)
p.text('lg-note', 'worker・APIにLeanはありません。Lean検証は隔離verifierだけが行います。', 60, 1226, 250, 70, 15, color=GRAY)

# ---------------------------------------------------------------- page 2
q = Page(mxfile, 'agent', 'エージェント処理フロー', 2440, 1540)
q.text('title', 'PALS アーキテクチャ ― エージェントの動き', 40, 28, 1400, 50, 34, bold=True)
q.text('subtitle', '1つの質問が、2種類のworkerとLean verifierをどう通るか。OpenAIマークは、その手順がOpenAI APIを呼ぶことを示します。', 40, 80, 2200, 30, 18, color=GRAY)

LLM = BRAND / 'openai.svg'
W = 250


def step(cid, x, y, title, body, stroke=INK, fill='#FFFFFF', w=W, h=200, llm=False, tag='', dashed=False):
    q.box(cid, f'<b>{title}</b><br>' + small(body) + (('<br>' + tag) if tag else ''), x, y, w, h, stroke, fill, dashed=dashed, size=18)
    if llm:
        q.icon(cid + '-llm', LLM, x + w - 42, y + 8, 30)


XS = [80, 410, 740, 1070, 1400, 1730, 2060]
CX = [x + W // 2 for x in XS]
REC = chip(BLUE, 'Recipe catalog')
R1, R2 = 190, 440            # lane A rows
LB, LB2, LB3 = 810, 1050, 1330  # lane B rows / regen line
SIDE = 'exitX=1;exitY=0.5;entryX=0;entryY=0.5;'

# lane A
q.zone('laneA', 40, 120, 2360, 550, BLUE, '', fill='#F7FAFE', dashed=False)
q.text('laneA-t', '評価worker（assessment lane）　質問を受け、保存済みRecipeを再利用するか、新規にLean証明するかを判定', 300, 132, 2080, 34, 22, color=BLUE, bold=True)
step('a1', XS[0], R1, '① 受付', 'assessmentキューから取得し、APIでclaim。添付・Project資料を読む')
step('a2', XS[1], R1, '② 完全一致の近道', '固定入力と一致すれば、検索を省いて再利用へ')
step('a3', XS[2], R1, '③ ローカル検索', '新規の通常質問のみ。Recipe全件（32件以内）をAPIから取得し、2〜4文字n-gramのTF-IDFで上位5件', tag=REC)
step('a4', XS[3], R1, '④ 独立2審査（並列）', 'GPT-6 Luna（low）×2。同じRecipe・revision・前提を両者が選んだときだけ承認', llm=True)
step('a5', XS[4], R1, '⑤ 再利用', '保存済みのRecipeを回答にする。新規生成なし', GREEN, '#F2FAF3')
step('a10', XS[5], R1, '回答を確定', 'APIへ結果を確定し、利用者の画面に表示', GREEN, '#F2FAF3')
step('a6', XS[2], R2, '⑥ 前処理', 'Luna：前提確認・規約の解決・検索意図の抽出', llm=True)
step('a7', XS[3], R2, '⑦ 全文検索 → 2審査', '英語全文検索で8件 → 独立にLuna×2（範囲評価・独立レビュー）。両者が同じ候補を承認', llm=True, tag=REC)
step('a8', XS[4], R2, '⑧ 新規Lean証明へ', '再利用できなければ、証明ジョブを作成する', ORANGE, '#FFF8F0')
q.box('pq', '<b>proof</b>キュー<br>' + small('SQS＋DLQ'), XS[5], R2 + 40, W, 120, '#E7157B', '#FFF5FA', size=18)

q.edge('ea1', 'a1', 'a2', extra=SIDE)
q.edge('ea2', 'a2', 'a3', '通常質問', extra=SIDE)
q.edge('ea3', 'a3', 'a4', extra=SIDE)
q.edge('ea4', 'a4', 'a5', '両者承認', extra=SIDE, color=GREEN)
q.edge('ea5', 'a5', 'a10', extra=SIDE, color=GREEN)
q.edge('ea2b', 'a2', 'a6', '通常以外', [(CX[1], R2 + 100)], 'exitX=0.5;exitY=1;entryX=0;entryY=0.5;')
q.edge('ea4b', 'a4', 'a6', '不承認', [(CX[3], 415), (CX[2], 415)], 'exitX=0.5;exitY=1;entryX=0.5;entryY=0;')
q.edge('ea6', 'a6', 'a7', extra=SIDE)
q.edge('ea7', 'a7', 'a8', '承認なし', extra=SIDE)
q.edge('ea7b', 'a7', 'a5', '両者承認', [(XS[3] + int(0.75 * W), 415), (CX[4], 415)], 'exitX=0.75;exitY=0;entryX=0.5;entryY=1;', color=GREEN)
q.edge('ea8', 'a8', 'pq', '', extra=SIDE, color='#E7157B')

# lane B
q.zone('laneB', 40, 730, 2360, 640, ORANGE, '', fill='#FFFBF6', dashed=False)
q.text('laneB-t', '証明worker（proof lane）　Leanで生成し、隔離verifierで検証し、失敗すれば修復する', 300, 742, 2080, 34, 22, color=ORANGE, bold=True)
step('b1', XS[0], LB, '① 受付', 'proofキューから取得し、APIでclaim')
step('b2', XS[1], LB, '② Recipe厳密一致', 'APIが形式文のSHA-256とLean toolchain指紋で照合', tag=REC)
step('b3', XS[2], LB, '③ Lean生成', 'Draft → Sketch → Proveの3段。GPT-6 Terra（medium）。sorry・admitを含む出力は拒否', llm=True)
step('b4', XS[3], LB, '④ 候補を提出', '成果物をS3へ保存し、APIに候補を登録して検証を依頼')
step('b5', XS[4], LB - 20, '⑤ Lean検証（隔離）', 'ReconcilerがmTLS :18117で依頼。verifierは外向き通信・認証情報なし。workerは結果をAPI経由で読む', RED, '#FFF3F1', h=240, dashed=True)
step('b6', XS[5], LB, '⑥ 意味審査', 'Luna（別セッション）が、問題と証明の内容が対応しているか審査', llm=True)
step('b7', XS[6], LB, '⑦ 解説 + 出力審査', 'Lunaが解説を生成し、公開前に別の審査で確認。検証済み回答として保存・表示', GREEN, '#F2FAF3', llm=True, w=290)
step('bh', XS[1], LB2, 'ヒット', '保存済みのソースをそのまま候補にする。LLM生成なし', GREEN, '#F2FAF3', h=150)
step('br', XS[4], LB2 + 20, '修復ルート選択', 'Lunaが draft / sketch / prove のどこから再開するか選ぶ。診断を添えて再生成（最大12回）', ORANGE, '#FFF8F0', llm=True, h=210)

q.edge('eb1', 'b1', 'b2', extra=SIDE)
q.edge('eb2', 'b2', 'b3', 'ミス', extra=SIDE)
q.edge('eb2h', 'b2', 'bh', 'ヒット', extra='exitX=0.5;exitY=1;entryX=0.5;entryY=0;', color=GREEN)
q.edge('ebh', 'bh', 'b4', '', [(CX[3], LB2 + 75)], 'exitX=1;exitY=0.5;entryX=0.5;entryY=1;', color=GREEN)
q.edge('eb3', 'b3', 'b4', extra=SIDE)
q.edge('eb4', 'b4', 'b5', extra=SIDE)
q.edge('eb5', 'b5', 'b6', '合格', extra=SIDE, color=GREEN)
q.edge('eb6', 'b6', 'b7', '承認', extra=SIDE, color=GREEN)
q.edge('eb5r', 'b5', 'br', '不合格', extra='exitX=0.5;exitY=1;entryX=0.5;entryY=0;', color=RED)
q.edge('ebr', 'br', 'b3', '再生成', [(CX[4], LB3), (CX[2], LB3)], 'exitX=0.5;exitY=1;entryX=0.5;entryY=1;jumpStyle=arc;jumpSize=14;', color=ORANGE)
q.edge('epq', 'pq', 'b1', 'ジョブを受け取る', [(CX[5], 700), (CX[0], 700)], 'exitX=0.5;exitY=1;entryX=0.5;entryY=0;', color='#E7157B')

# legend / note
q.icon('lg-llm-i', LLM, 60, 1410, 34)
q.text('lg-llm-t', '＝ OpenAI APIの呼び出し（Responses API。モデルはGPT-6 Luna / Terra）', 106, 1414, 1200, 30, 18)
q.text('lg-note', 'pgvectorのDraft catalogとTyped catalogは、この本線に含めていません（配線済みですが、本番での使用は未確認）。全体構成のAurora内カードを参照してください。', 60, 1464, 2300, 40, 18, color=GRAY)

ET.indent(mxfile, space='  ')
DEST.write_text(ET.tostring(mxfile, encoding='unicode') + '\n')
print(DEST)
