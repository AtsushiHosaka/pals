# PALS Startup / AWS Activate Business Plan

Updated: 2026-06-22

## Purpose

このドキュメントは、PALS を起業プロジェクトとして進める場合の事業計画書ドラフトです。AWS Activate 申請、アクセラレーター応募、ギャップファンド応募、LP 制作、初期共同創業者との認識合わせに使い回すことを想定します。

法務・税務・会計判断は専門家確認が必要です。この文書では、PALS の事業仮説、会社設立の進め方、AWS Activate 申請に必要な情報、12 か月の実行計画を整理します。

## Executive Summary

PALS は、Lean などの定理証明支援系を学ぶ学生・研究者・開発者に向けた、AI と verifier を組み合わせた学習・証明支援プラットフォームです。自然言語の数学・計算機科学の問題をサブゴールへ分解し、Lean proof sketch を生成し、Lean compiler/verifier の診断をもとに修正案と解説を提示します。

生成 AI の普及により、コードや証明の「もっともらしさ」と「機械的に検証された正しさ」の差が重要になっています。PALS は、AI が答えを代筆するツールではなく、学習者が検証可能な証明を構築できる環境を提供します。

初期市場は、Lean / 形式手法 / 数学・情報科学教育に関心のある大学授業、ゼミ、研究室、自習者です。中長期では、高信頼ソフトウェア、AI 安全性、セキュリティ、金融など、仕様や証明の検証を必要とする開発・研修市場へ展開します。

## AWS Activate Strategy

### Current Fit

AWS Activate の公式ページでは、Activate Credits は pre-seed から scale stage の startup 向けで、Founders tier は self-funded / bootstrapped startup が直接応募でき、最大 USD 5,000、最初は USD 1,000 から開始できると説明されています。Portfolio tier は accelerator、angel investor、VC など Activate Provider の Organization ID が必要で、最大 USD 200,000 の credits が案内されています。

PALS の現状では、まず `Activate Founders` を狙うのが自然です。WASEDA ギャップファンド、TOKYO STARTUP GATEWAY、TECH PLANTER、VC/angel/accelerator などを通じて Activate Provider の Org ID を得られた場合に、`Activate Portfolio` へ進むのが次のステップです。

### Apply Timing

AWS 公式の説明では、credits は通常 1-2 年で失効するため、AWS 利用を本格化するタイミングで申請するのがよいとされています。PALS では、以下が揃ったタイミングが申請目安です。

- 法人または startup としての基本情報が整理されている。
- 独自ドメインと機能する Web サイトがある。
- AWS account が startup の business email/domain と整合している。
- 今後 6-12 か月で AWS を使う具体的な計画がある。
- Bedrock、Lambda、S3、CloudFront、ECS/Fargate、Aurora などの費用を credits で有効に使える見込みがある。

### What To Prepare

AWS Activate 申請に向けて、先に準備するもの:

- Startup name: PALS または法人名
- Domain: 例 `pals.dev`, `pals-ai.jp`, `proofpals.ai` など
- Company website: LP、プロダクト説明、contact、privacy note
- Business email: 例 `founder@<domain>`
- AWS account: business email と同じ domain を使う
- Product description: 1-2 paragraphs
- Target customer: universities, labs, Lean learners, high-assurance teams
- Funding stage: self-funded / pre-seed
- Founded date: 法人設立日または project/company launch date
- Traction: demo, interviews, grant applications, prototype milestones
- AWS usage plan: services, estimated monthly cost, scaling plan

## 起業するならどう進めるか

### Recommendation

PALS は、いきなり重い法人運営に入るより、次の順序がよいです。

1. 2026年6-7月: 個人/任意プロジェクトとして応募書類、LP、MVP 仕様を固める。
2. 2026年7-8月: WASEDA / TSG / TECH PLANTER などに応募し、外部評価とメンター接点を作る。
3. 2026年8-9月: ユーザーヒアリングとデモで、課題の強さ、利用者、導入者、支払者を分けて検証する。
4. 2026年9-10月: AWS credits、法人取引、共同創業者、知財帰属の必要性が出たら法人化する。
5. 2026年10月以降: Activate Founders、助成金、共同研究、pilot 導入へ進む。

法人化は「クレジットのため」だけではなく、契約、請求、知財帰属、共同創業者の持分、外部資金、AWS account の管理主体を明確にするために行います。PALS の場合、AWS Activate、grant、共同研究、大学/企業 pilot を狙うなら、遅くとも初回 pilot 契約前には法人化しておく方が進めやすいです。

### 合同会社か株式会社か

| 選択肢 | 向いている場合 | PALS での見方 |
| --- | --- | --- |
| 合同会社 | 小さく始めたい、当面 VC 調達や株式インセンティブを考えない | 低コストで早い。個人開発から事業実験へ移るだけなら有力 |
| 株式会社 | VC/angel 調達、株式による共同創業、将来の資本政策を考える | 外部資金・人材採用・大学発ベンチャー感を出しやすい |

PALS が最初に grants / credits / pilot revenue を狙うなら合同会社でも始められます。一方、共同創業者を入れる、VC/angel を早期に考える、大学発 startup として見せたい、ストックオプションを設計したい場合は株式会社が無難です。

### 設立前に決めること

- 創業者: 誰が代表者か、共同創業者がいるか
- 持分: founder equity、将来参加者への枠、貢献の扱い
- 知財: 個人で書いた code/docs を法人に移すか、OSS と private product をどう分けるか
- 大学関係: 大学の設備、研究、職務発明、共同研究に該当するものがないか
- OSS 方針: `pals-agent` は public OSS、hosted product / UI / operations は private commercial にするか
- 会計: Freee/MoneyForward などの利用、税理士相談のタイミング
- 契約: 利用規約、プライバシーポリシー、研究データ同意、pilot 契約

## Business Plan

### 1. Problem

生成 AI はコード、説明、数学的推論を高速に出力できるようになっています。しかし、AI の出力は「正しそうに見える」だけで、証明や仕様として正しいとは限りません。特に数学、計算機科学、セキュリティ、金融、AI safety などでは、誤った証明や仕様のまま進むことが大きなリスクになります。

Lean などの proof assistant は、証明を機械的に検証する強力な基盤です。しかし、初学者や授業導入には高い壁があります。

- 自然言語の証明を Lean の型・構文・tactic に変換するのが難しい。
- compiler diagnostics や goal state を読んで修正する経験が必要。
- 既存の LLM は `sorry` や誤った証明を含む出力を出すことがある。
- 教員/TA は学習者の途中過程や詰まりどころを把握しにくい。

この課題は、単なる「Lean の勉強が難しい」ではありません。AI 時代に、検証可能な推論を扱える人材と開発環境が不足していることが本質です。

### 2. Solution

PALS は、AI と Lean verifier を組み合わせた学習・証明支援プラットフォームです。ユーザーが自然言語の問題、Lean theorem statement、途中証明を入力すると、PALS agent が以下を行います。

1. 問題を小さな subgoal に分解する。
2. Lean の proof sketch を生成する。
3. Lean verifier で実行し、compiler diagnostics を取得する。
4. エラーの意味と次の修正方針を説明する。
5. verified proof までの試行履歴を保存する。

PALS の中心は「AI が答えを書くこと」ではなく「verifier feedback によって学習者が証明を進められること」です。最終出力は、`sorry` や `admit` を含まない Lean-verified artifact を目指します。

### 3. Product

MVP は以下の 3 つの interface から始めます。

| Interface | User | Value |
| --- | --- | --- |
| Learner workspace | 学生、自習者 | theorem statement、proof sketch、error explanation、hint |
| Instructor dashboard | 教員、TA | どの問題で詰まったか、どの error が多いか、教材改善 |
| Agent/verifier API | 研究者、開発者 | Lean verification job、trace 保存、RAG/LLM 評価 |

初期機能:

- Lean 入門問題の入力と証明支援
- Draft -> Sketch -> Prove -> Repair workflow
- Lean compiler/verifier feedback
- `sorry` / `admit` detection
- proof attempt trace の保存
- 日本語/英語での error explanation
- 問題ごとの success/failure metrics

### 4. Target Customers

Initial beachhead:

- Lean / 形式手法を学ぶ大学生・大学院生
- 数学、CS、ソフトウェア工学、セキュリティ、AI safety のゼミ/研究室
- Lean 入門授業や自主ゼミを運営する教員・TA

Secondary market:

- 高信頼ソフトウェア開発チーム
- セキュリティ・形式検証研修を行う企業
- AI code generation の検証・評価基盤を必要とする研究開発チーム

Buyer と user は分けて考えます。初期 user は学生/研究者ですが、buyer は授業運営者、研究室、大学、企業研修担当、R&D 部門になる可能性が高いです。

### 5. Market Entry

最初の 6 か月は、広い市場を追わず、以下の順で検証します。

1. Lean 初学者の自習課題
2. 大学ゼミ/授業での pilot
3. 研究室の formalization 支援
4. 企業研修/高信頼開発チーム向け proof workflow

Go-to-market:

- 早稲田内の学生・教員ヒアリング
- Lean / theorem proving community への OSS 公開
- WASEDA ギャップファンド、TSG、TECH PLANTER への応募
- 小規模 demo day / workshop
- 教育利用の case study 化

### 6. Business Model

初期収益仮説:

| Model | Price hypothesis | Notes |
| --- | --- | --- |
| Individual Pro | JPY 1,000-3,000 / month | 自習者向け。収益より usage validation |
| Course/Lab License | JPY 50,000-300,000 / semester | 授業・ゼミ単位。最初の本命 |
| Research Workspace | JPY 30,000-100,000 / month | trace, private data, custom benchmarks |
| Enterprise Training | JPY 500,000+ / cohort | 形式手法・AI安全性研修 |
| Verifier/Agent API | usage-based | proof job, trace, evaluation pipeline |

短期では、個人課金より授業/研究室 pilot の方が検証しやすいです。PALS の価値は単独の AI チャットではなく、学習ログ、検証履歴、教材改善、verified artifact にあります。

### 7. Competitive Positioning

競合/代替:

- ChatGPT / Claude / GitHub Copilot で Lean コードを聞く
- Lean language server / VS Code extension
- LeanDojo, Kimina, DeepSeek-Prover, Goedel-Prover などの研究系 prover
- 既存 LMS / 教材

Differentiation:

- Verifier-first: AI output を Lean で必ず検証する。
- Learning-first: 完成証明だけでなく、subgoal、diagnostics、repair を学べる。
- Trace-first: 成功/失敗/修正履歴を教材改善と future training data にする。
- Japan-first: 日本語の説明、国内大学での授業導入に寄せる。
- Cost-aware: local LLM と managed LLM を組み合わせ、MVP 予算を制御する。

### 8. Traction To Build

現時点の traction として主張できるもの:

- PALS parent repo の構成整理
- Lean verifier を `pals-agent` 内 tool/runtime として管理する方針決定
- AWS-first MVP architecture と JPY 80,000/month guardrail の整理
- Apple Silicon local LLM design
- Lean LLM research / Draft, Sketch, and Prove 方針の整理
- WASEDA ギャップファンド応募資料ドラフト

今後 30 日で作る traction:

- LP 1 枚
- CLI demo または minimal Web demo
- Lean 入門課題 10 問 benchmark
- 学生/教員ヒアリング 10 件
- WASEDA / TSG / TECH PLANTER 応募
- AWS Activate Founders 申請準備

### 9. 12-Month Roadmap

| Period | Goal | Deliverables |
| --- | --- | --- |
| 2026 Q3 | Problem/solution validation | user interviews, Lean benchmark, CLI/Web demo |
| 2026 Q4 | MVP pilot | learner workspace, verifier loop, trace storage, instructor metrics |
| 2027 Q1 | Pilot expansion | 1-2 course/lab pilots, pricing test, case study |
| 2027 Q2 | Commercialization | paid lab license, provider/accelerator credits, enterprise discovery |

### 10. AWS Architecture Plan

PALS は、MVP では scale-to-zero / pay-per-job を基本にします。

| Layer | AWS service candidate | Purpose |
| --- | --- | --- |
| Frontend | S3 + CloudFront | static web UI |
| API | API Gateway HTTP API + Lambda/FastAPI/Mangum | request handling |
| Queue | SQS + DLQ | proof job queue |
| Agent runtime | ECS Fargate RunTask | proof job execution |
| Verifier | sidecar/internal service in Fargate task | Lean compile/check |
| Database | Aurora Serverless v2 PostgreSQL + pgvector | users, traces, retrieval metadata |
| Artifacts | S3 | prompts, generated Lean files, diagnostics |
| LLM | Bedrock first, fallback adapter optional | draft/sketch/prove/repair |
| Observability | CloudWatch + Langfuse-compatible tracing | logs, timings, model/tool metrics |
| Security | IAM, KMS, Secrets Manager | least privilege, secret handling |

AWS Activate credits are useful for:

- Bedrock experiments
- Fargate proof jobs
- Aurora Serverless v2 validation
- S3/CloudFront hosting
- CloudWatch and support during launch

Cost guardrails:

- hard monthly budget alert
- per-proof-job max attempts
- LLM token cap per role
- Fargate timeout
- no NAT Gateway in MVP unless required
- no OpenSearch in MVP unless later justified
- no always-on Fargate service for proof jobs

### 11. Financial Plan

Initial funding need:

| Use | 6-month purpose |
| --- | --- |
| Cloud/LLM | AWS/Bedrock experiments, verifier jobs, logs |
| Product | frontend/backend/agent development |
| User research | interviews, user test incentives, workshop |
| Legal/admin | incorporation, terms/privacy, accounting setup |
| Design/demo | LP, demo video, pitch deck |

Non-dilutive funding targets:

- WASEDA ギャップファンド
- TOKYO STARTUP GATEWAY
- TECH PLANTER
- AWS Activate Founders
- Cloud credits from Google/Microsoft/AWS where applicable
- University pilot / research support

Fundraising stance:

最初は VC より、grant、credits、pilot revenue、angel/advisor support を優先します。PALS は技術検証と教育導入の時間が必要なので、早すぎる大型調達より、verified traction を積む方がよいです。

## AWS Activate Application Draft

### Startup Description

PALS is a verifier-centered AI learning platform for formal proof. It helps students, researchers, and developers transform natural-language mathematical and computer science problems into Lean proof sketches, run them through the Lean verifier, and learn from compiler diagnostics through guided repair suggestions. PALS combines LLM-based drafting with proof assistant feedback so users can move from informal reasoning to machine-checked proofs.

### Product Description

The product provides a learner workspace, instructor dashboard, and agent/verifier API. Learners enter theorem statements or proof attempts, receive subgoal decomposition and Lean proof sketches, and iterate with verifier-backed feedback. Instructors and researchers can inspect anonymized failure patterns, diagnostics, and proof traces to improve teaching material and build verified datasets.

### Target Market

Initial customers are universities, research labs, Lean learners, and instructors teaching formal methods, mathematics, software verification, or AI safety. Longer term, PALS targets high-assurance software teams and enterprise training programs that need verifiable reasoning workflows.

### Current Stage

Self-funded / pre-seed. The project has completed architecture planning, Lean LLM research, local/cloud LLM strategy, and grant application materials. Next milestones are a working MVP, user interviews with students and instructors, and small pilot deployments.

### Planned AWS Usage

PALS will use AWS for its hosted MVP: S3 and CloudFront for the web frontend, API Gateway and Lambda for API requests, SQS for proof jobs, ECS Fargate RunTask for agent/verifier workloads, Aurora Serverless v2 PostgreSQL with pgvector for traces and retrieval metadata, S3 for generated artifacts, and Amazon Bedrock for LLM calls. AWS credits will reduce cash burn while we test proof workloads, model routing, and user pilots.

### Traction Statement

PALS has a defined architecture, repository layout, Lean verifier ownership decision, local Apple Silicon LLM plan, and grant application draft. The next 30 days focus on building a minimum demo, creating a Lean benchmark, interviewing students/instructors, and applying to startup support programs.

## LP Copy Draft

### Hero

PALS

Learn formal proof with AI you can verify.

PALS helps learners turn mathematical and computer science problems into Lean proof sketches, then uses the Lean verifier to explain what works, what fails, and how to repair it.

### Sections

1. Why it matters
   - AI can generate plausible answers, but high-trust reasoning needs verification.

2. How PALS works
   - Draft subgoals, sketch Lean proof structure, run the verifier, repair from diagnostics.

3. Who it is for
   - Lean learners, instructors, research labs, high-assurance software teams.

4. Built around verification
   - No final `sorry`, no blind trust in model output, every result is checked.

5. Join pilot
   - Contact: [founder@domain]

## Immediate Checklist

### This Week

- [ ] Decide temporary startup name and domain candidates.
- [ ] Create a one-page LP with product description and contact form.
- [ ] Prepare business email on the domain.
- [ ] Create a lean, public-safe demo README or demo video.
- [ ] Draft AWS Activate Founders answers using the section above.
- [ ] Decide whether to apply before or after法人化.

### Before AWS Activate Application

- [ ] Functioning company/project website exists.
- [ ] AWS Builder ID is ready.
- [ ] AWS account uses business email/domain.
- [ ] Product, target market, funding stage, and company profile are consistent.
- [ ] 6-12 month AWS usage forecast is written.
- [ ] Billing alerts and budgets are configured before meaningful usage.

### Before Incorporation

- [ ] Decide 合同会社 vs 株式会社.
- [ ] Decide founder equity / membership.
- [ ] Decide OSS/commercial boundary.
- [ ] Check university IP and research-related obligations.
- [ ] Prepare articles of incorporation / company purpose.
- [ ] Prepare accounting workflow.
- [ ] Prepare company bank account plan.

## Company Purpose Draft

法人化する場合の事業目的案:

1. 人工知能、形式手法、定理証明支援系を用いたソフトウェア及び情報システムの企画、開発、運営、販売
2. 数学、情報科学、ソフトウェア工学、AI 安全性に関する教育サービス、教材、研修、コンサルティングの提供
3. ソフトウェアの品質保証、形式検証、仕様検証、セキュリティ検証に関するサービスの提供
4. 研究開発支援、データセット作成、評価基盤、API サービスの提供
5. 前各号に附帯又は関連する一切の事業

## References

- AWS Activate Credits: https://aws.amazon.com/startups/credits/
- AWS Activate credit guide: https://aws.amazon.com/startups/learn/everything-you-need-to-know-about-aws-activate-credits/
- AWS Activate application guide: https://aws.amazon.com/startups/learn/applying-for-aws-activate-credits-a-step-by-step-guide/
- 法人設立ワンストップサービス: https://app.e-oss.myna.go.jp/Application/ecOssTop/
- PALS architecture notes: `AGENTS.md`, `README.md`, `docs/lean-llm-research.md`, `docs/apple-silicon-local-llm.md`
