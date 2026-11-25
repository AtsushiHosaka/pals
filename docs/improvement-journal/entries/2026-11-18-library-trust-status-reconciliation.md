# 信頼の水準を含む履歴とSSEの照合（2026-11-18）

Web95への追加レビューで、履歴にlibrary_trust:nullがあると、イベントhookの投影がそのfieldを落としてstatus_sync_failedになると指摘された。旧9524b0aで、通常のproperty順と逆順の2件を実hookで再現し、両方が失敗することを確認した。

34714b07c8d8ae6e1c3ca6d00996239a8ed0b24eで投影にtrustを保持し、一覧の比較を固定順にした。未指定とnullだけを同じものとし、実際の監査情報の違いは詳細・一覧の比較へ含める。APIの256文字制限と一致するようUnicode scalarで数え、孤立surrogateと制御文字を拒否した。

関係する3suite31件が成功・スキップ0、1.98秒。型・lint・独立レビューが成功し、[head自身の必須CI](https://github.com/AtsushiHosaka/pals-webfront/actions/runs/44258605980)も成功した。旧headのgreenを流用していない。本番表示・保存の受け入れは未確認。追加モデル費用・本番操作は0。[Web PR95](https://github.com/AtsushiHosaka/pals-webfront/pull/95)。
