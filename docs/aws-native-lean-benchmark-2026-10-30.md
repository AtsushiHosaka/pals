# AWS largeでのLeanコンパイル測定

2026年10月30日、東京のprivate subnetに置いたr8a.largeで測定しました。Lean単体の測定であり、LLM、レビュー、キュー、DB、回答表示の時間は含みません。アプリの本番起動とDNS切り替えも、まだ行っていません。

CPUはAMD EPYC 9R45、2 vCPUです。agentのcommitは`0a45e4984538dc82294ad41994309081eddb9296`、Linux x86のverifier imageは非公開ECRの`sha256:6fe2a2e7e2b9385ba922bcf6fc9cf678494c69e3841c04d3b1be4c68700a707f`に固定しました。Leanは4.32.0-rc1、compiler commitは`b4812ae53eea93439ad5dce5a5c26591c31cb697`です。

群の準同型の単射性、数列の極限の和、互いに素な数の積の整除、線形写像の核の和の4題を使いました。4方式を入れ替えて各題3回ずつ、合計48回コンパイルし、すべて成功しました。必要なimportを指定した3方式では、各題のソースSHA256が一致しています。

| 方式 | 標本数 | 中央値 | p95 |
| --- | ---: | ---: | ---: |
| 広いMathlib import | 12 | 3.447秒 | 3.532秒 |
| 必要なimportを指定 | 12 | 1.520秒 | 1.654秒 |
| 必要なimportと毎回新しいLake環境cache | 12 | 1.617秒 | 1.762秒 |
| 必要なimportとLake環境cacheの再利用 | 12 | 0.805秒 | 1.403秒 |

再利用方式には最初のcache missが1回含まれ、残り11回はhitでした。これはLake環境の再利用で、Lean compilerの常駐化ではありません。各要求で新しいLean子プロセスが証明を検査しています。標本が少ないため、このp95は将来の遅延保証には使いません。OSのファイルcacheも制御していません。

UID65532、全capabilityなし、no-new-privileges、network none、rootとprojectの読み取り専用、tmpfs、2 CPU、4GiB、PID64、nofile1024を実機で検査しました。`memory.max`は4,294,967,296 bytes、`memory.peak`は821,260,288 bytes、OOMとOOM killは0でした。

一方、OSが報告した子プロセスの最大RSSは6,630,796 KiBでした。cgroupの課金値とプロセスのRSSは異なる観測なので、821 MBをホスト全体の必要メモリとは扱いません。workerとの同時実行、複数枠、HTTP/mTLSと本番負荷での容量確認が必要です。4GiB制限を緩める変更は行っていません。

生の測定値はGit対象外の作業領域に保存しました。ログ全体のSHA256は`016dc13e1f9a5fe47742b7a9cd2d4c5dee4858e33568d04bf968b43b3e6c8667`、corpusのSHA256は`0bfc1d6daf9b6b3dfb1f81c8bbaa5c9e81d9a1f4ce046c53370f37787e68c853`です。SSM経由の分割取得後に全体のハッシュを照合しています。
