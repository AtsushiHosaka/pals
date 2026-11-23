#!/usr/bin/env bash
# Weekly open-PR review (pals#467). Zero cost: GitHub API reads only.
# Lists open PRs oldest first across the PALS repos and flags which ones broke the PR lifetime rules:
#   age >= 7 days  -> decide: merge or close
#   stacked        -> base branch is another open PR's head (depth 1 = ok, >=3 = rule violation)
#   draft          -> long-lived draft is not allowed; open an Issue instead
# Writes ~/pals-pr-review/YYYY-MM-DD.md and prints it. Run by cron (see docs/release-reliability-policy.md).
set -euo pipefail
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
OWNER=AtsushiHosaka
REPOS=${PALS_REVIEW_REPOS:-"pals pals-api pals-agent pals-webfront pals-infra"}
LIMIT=${PALS_PR_LIST_LIMIT:-1000}
MAX_AGE_DAYS=${PALS_PR_MAX_AGE_DAYS:-7}
OUT_DIR=${PALS_PR_REVIEW_DIR:-$HOME/pals-pr-review}
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/$(date +%F).md"
NOW=$(date +%s)
tmp=$(mktemp); trap 'rm -f "$tmp" "$tmp.one" "$tmp.json"' EXIT
for r in $REPOS; do
  gh pr list -R "$OWNER/$r" --state open --limit "$LIMIT" \
    --json number,title,createdAt,isDraft,headRefName,baseRefName,headRepository,headRepositoryOwner,url > "$tmp.one"
  # Fail loudly instead of silently dropping the oldest PRs (gh lists newest first).
  [ "$(jq length "$tmp.one")" -lt "$LIMIT" ] || { echo "$r: open PRs reached --limit $LIMIT; list incomplete" >&2; exit 5; }
  jq --arg repo "$r" '[.[]|.repo=$repo]' "$tmp.one" >> "$tmp"
done
jq -s --arg owner "$OWNER" --argjson now "$NOW" --argjson max "$MAX_AGE_DAYS" '
  add // [] | map(. + {age: (($now - (.createdAt|fromdateiso8601)) / 86400 | floor)}) as $all
  | $all | map(. as $p
      | .depth = ([ $all[] | select(.repo==$p.repo) ] | . as $same
          | def d($b; $n): if $n>5 then $n else ($same | map(select(.headRefName==$b and .headRepositoryOwner.login==$owner and .headRepository.name==$p.repo)) | if length==0 then $n else d(.[0].baseRefName; $n+1) end) end;
          d($p.baseRefName; 0)))
  | sort_by(-.age)' "$tmp" > "$tmp.json"
{
  echo "# PR棚卸し $(date +%F)（古い順）"
  echo
  total=$(jq length "$tmp.json"); over=$(jq "[.[]|select(.age>=$MAX_AGE_DAYS)]|length" "$tmp.json")
  echo "open: ${total}件 / ${MAX_AGE_DAYS}日以上: ${over}件。すべて「マージ」か「閉じる」で決着させる。"
  echo
  jq -r --argjson max "$MAX_AGE_DAYS" '.[] |
    "- " + (if .age>=$max then "**要決着** " else "" end)
    + "\(.repo)#\(.number) \(.age)日 " + (if .isDraft then "[draft] " else "" end)
    + (if .depth>=3 then "[積み深さ\(.depth)・違反] " elif .depth>=1 then "[積み\(.depth)] " else "" end)
    + "\(.title) \(.url)"' "$tmp.json"
} | tee "$OUT"
rm -f "$tmp.json"
