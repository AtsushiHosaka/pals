#!/usr/bin/env python3
"""pals#486 の測定: pals-infra の gate の判定が、何か所で定義されているかを AST で数える(読み取りのみ。AWS・モデル・ネットワークは使わない)。

使い方: python3 pals-scripts/measure-gate-duplicates.py <pals-infra のチェックアウト>
出力(JSON): 上限値の数値リテラル定義の数(名前ごと)、forward-only 状態との比較の箇所、モード組の手書き比較、記録検証関数の実装。
対象は `<checkout>/scripts/*.py` と `<checkout>/host/private-runtime/*.py`。数える名前の一覧は NAMES。
"""
import ast, json, sys
from collections import defaultdict
from pathlib import Path
root = Path(sys.argv[1])
NAMES = {'OBSERVATION_MAX_AGE_S','OBSERVATION_SKEW_S','OBSERVATION_FUTURE_SLACK_S','PREFLIGHT_MAX_AGE_S','OPERATOR_APPLY_LIMIT_S','REFRESH_PROOF_MAX_AGE_S','RECORD_MAX_AGE_S',
 'CANARY_MAX_AGE_S','MIN_DISK_FREE_GB','MAX_RETAINED_WORKER_HOPS','MAX_RETAINED_WORKER_PINNED_HOPS','ALERT_MIN_S','ALERT_MAX_S','ALERT_MAX_SECONDS','ALERT_TIMEOUT_S','MARGIN_S',
 'POLICY_MAX_AHEAD_S','MAX_POLICY_WINDOW_S','LATE_MANIFEST_MARGIN_S','QUIESCE_TO_ADMISSION_LIMIT_S','PREFLIGHT_TO_ADMIT_LIMIT_S','ALERT_WINDOW_LIMIT_S','ALERT_WINDOW_MAX_S',
 'ALERT_CAP_S','MAX_WINDOW_SECONDS','PREFLIGHT_RECORD_MAX_BYTES'}
files = sorted(list((root/'scripts').glob('*.py')) + list((root/'host/private-runtime').glob('*.py')))
literal = defaultdict(list); fo_cmp = []; verifiers = []
def is_fo(n):
    return isinstance(n, ast.Constant) and n.value == 'admitted_not_serving' or isinstance(n, ast.Name) and n.id == 'FORWARD_ONLY_STATE'
for f in files:
    tree = ast.parse(f.read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in NAMES and isinstance(n.value, ast.Constant | ast.BinOp):
            literal[n.targets[0].id].append(f'{f.relative_to(root)}:{n.lineno}')
        if isinstance(n, ast.Compare) and any(is_fo(c) for c in [n.left, *n.comparators]):
            fo_cmp.append(f'{f.relative_to(root)}:{n.lineno}')
        if isinstance(n, ast.FunctionDef) and n.name in ('verify_record', 'verify_preflight_record') and len(n.body) > 3:
            verifiers.append(f'{f.relative_to(root)}:{n.lineno}')
# the mode-tuple agreement written out by hand: a Compare of two tuples/calls built from .get('predecessor_state')
tuples = []
for f in files:
    for n in ast.walk(ast.parse(f.read_text())):
        if isinstance(n, ast.Compare):
            src = ast.unparse(n)
            if "predecessor_state" in src and "runtime_predecessor_sha256" in src and 'get' in src:
                tuples.append(f'{f.relative_to(root)}:{n.lineno}')
numeric_defs = sum(len(v) for v in literal.values())
print(json.dumps({'numeric_literal_definitions_of_gate_limits': numeric_defs, 'by_name': {k: len(v) for k, v in sorted(literal.items())},
                  'observation_max_age_definitions': len(literal.get('OBSERVATION_MAX_AGE_S', [])),
                  'forward_only_state_comparisons': len(fo_cmp), 'forward_only_comparison_sites': fo_cmp,
                  'forward_only_mode_tuple_agreements_by_hand': len(tuples), 'tuple_sites': tuples,
                  'record_verifier_implementations': len(verifiers), 'verifier_sites': verifiers}, indent=1, sort_keys=True))
