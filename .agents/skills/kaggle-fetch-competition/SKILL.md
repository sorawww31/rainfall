---
name: kaggle-fetch-competition
description: 環境変数COMPETITIONのKaggleコンペを開始するため、参加・データ取得、公式ページと厳密なルールの文書化、Discussionと公開Notebookの動向調査、最高voteのEDA Notebook導入とMarkdownセルの日本語化を統括する。ユーザーが「コンペをオンボーディング」「新しいKaggleコンペを開始」「コンペ情報・ルール・流行手法をまとめて」「EDAまで用意」などを依頼したときに使う。
---

<!--
SKILL.md
Where: .agents/skills/kaggle-fetch-competition.
What: Onboard the competition selected by COMPETITION.
Why: Reach a documented, reproducible starting line before experiments begin.
-->

# Kaggle Fetch Competition

`COMPETITION`のコンペについて、データ、公式仕様、ルール、Discussion、公開Notebook、EDAを一続きで準備する。
推測を事実として書かず、取得日、Kaggle上のID、URL、未確認事項を残す。

## 責務

- Competitionデータ取得は`$import-kaggle-resource`へ委譲する。
- Discussion本文・コメント調査は`$kaggle-discussion-research`の調査手順を使う。
- 公開Notebookの系譜・重複・手法調査は`$kaggle-notebook-research`の調査手順を使う。
- このSkillは順序、共通出力先、公式情報との整合、EDA導入、完了判定を統括する。

## 並列実行

1. 対象slug、参加状態、必要容量、保存先、既存差分を確認するまでは直列に進める。
2. 事前確認後、実行環境にサブエージェント機能があれば、`$import-kaggle-resource`によるデータ取得と検証を専用エージェントへ委譲する。
   - ツール実行とarchiveの安全検査を完遂できる範囲で、利用可能な中の最も安価なモデルを明示指定して呼び出す。
   - モデルを指定できない環境では既定モデルで委譲し、指定できなかったことを最終報告に残す。
3. データ取得の完了を待たず、メインエージェントは公式情報の収集と`overview.md`、`rules.md`の作成を進める。余りの並列枠があれば、Discussion調査とNotebook調査・EDA導入も別のエージェントへ委譲する。データ取得用の枠を優先する。
4. 並列タスク間で同じファイルを編集しない。データ担当のリポジトリ内の永続成果物は`input/competitions/<slug>/`だけとし、Discussion担当は`discussion.md`、Notebook担当は`notebooks.md`とEDA Notebookだけを書き込む。
5. `data-and-evaluation.md`の公式仕様部分はデータ取得中に作成してよい。実データのschema、欠損、件数、公式説明との差分は、データ取得とファイル数検証の完了後に追記する。展開中のデータは読まない。
6. 最終整合性確認の前にすべてのタスクを待ち合わせ、成否、未確認事項、作成・変更パスを確認する。データ取得または件数検証が失敗した場合、他の調査が完了していても全体を成功扱いにしない。
7. サブエージェント機能がなければ直列に実行し、その制約を報告する。shellプロセスを起動したまま放置するfire-and-forgetは行わない。

## 出力

コンペslugを`<slug>`として、次を作成する。

```text
docs/competitions/<slug>/
├── overview.md
├── rules.md
├── data-and-evaluation.md
├── discussion.md
└── notebooks.md

notebook/EDA/
└── <owner>__<notebook-slug>.ipynb
```

各Markdownには冒頭コメントを置き、`Where`、`What`、`Why`を記す。
ディレクトリだけを先に追加する場合は`.gitkeep`を使う。成果物作成後も不要な`.gitkeep`を削除する必要はない。

## 1. 対象を確定する

1. プロセス環境の`COMPETITION`を読む。空なら停止し、設定を依頼する。
2. `.env.example`や類似slugから推測しない。ユーザーが明示的に別slugを指定した場合だけ優先する。
3. Kaggle MCPの`get_competition`でslug、title、URL、deadline、entrant deadline、team count、team rank、参加状態を確認する。
4. MCP結果のslugが`COMPETITION`と一致しなければ停止する。
5. 既存の`docs/competitions/<slug>/`、`notebook/EDA/`、README、AGENTS.mdの差分を読み、ユーザーの追記を戻さない。

## 2. 参加とデータを準備する

1. `$import-kaggle-resource`を使う。
2. `user_has_entered == true`を確認する。未参加でMCPから規約同意できない場合は、Kaggle上での手動同意を依頼する。
3. Competitionデータを`input/competitions/<slug>/`へ取得する。
4. MCPの総ファイル数とローカル件数を比較し、一致しなければ後続調査を成功扱いにしない。

## 3. 公式情報を収集する

Kaggle MCPの公式Competition情報を一次根拠として取得する。

1. `get_competition`で基本情報、期限、賞金、team/submission制約、Notebook提出要否を取得する。
2. `list_competition_pages`で少なくとも次を確認する。
   - Overview / Description
   - Data Description
   - Evaluation
   - Timeline
   - Rules
   - Prizes
   - Code Requirements
   - Acknowledgements / Licenses
3. `get_competition_data_files_summary`と`list_competition_data_files`を全ページ確認する。
4. 公式本文にない事項を一般的なKaggle慣行から補完しない。
5. 公式ページ同士に矛盾があれば、Rulesと更新日の新しいhost告知を優先し、矛盾自体を記録する。

## 4. 公式ドキュメントを書く

### `overview.md`

次を記す。

- 取得日、title、slug、URL、host、category、賞金、開催状態。
- 目的、予測対象、利用場面、タスク種別。
- 開始、entry、team merge、最終提出の各期限をUTCとJSTで併記する。
- team数、自分の参加・rank状態。
- 重要リンクとSource Index。

### `rules.md`

Rules本文を要約し、項目ごとに根拠ページ・節・確認日を付ける。

- eligibility、参加・team merge・最大team size。
- 日次提出上限、最終提出本数、private/public leaderboardの扱い。
- competition dataの利用範囲、private sharing、再配布、アクセス制御。
- external data、事前学習model、生成AI、手動ラベル、追加annotationの可否と公開条件。
- code sharing、open source、winner obligations、再現性、ライセンス。
- 複数アカウント、協力、leak、禁止行為。
- Notebook提出ならCPU/GPU、Internet、runtime、出力、再実行、外部依存制約。
- 賞金、受賞資格、提出物、期限、税務・本人確認など参加判断に必要な条件。
- hostによる変更権限と、確認できたルール更新・公式訂正。

断定できない項目は`未確認`とし、一般論で埋めない。長い原文引用は避ける。

### `data-and-evaluation.md`

次を記す。

- 全ファイル数、総容量、主要ディレクトリ、ファイル形式。
- train/test構造、target、ID、sample submission、hidden testの有無。
- 重要column、欠損、単位、時系列・group・重複・leak候補。
- metric名、数式、最適化方向、集約単位、tie/NaN/clipなどの注意。
- public/private split、shake-upやCV設計に関係する既知情報。
- submission列、行数、型、順序、Notebook提出手順。
- 公式説明と実データの不一致。大規模データは全件読まず、代表sampleとschemaを検証する。

## 5. Discussionを調査する

1. `$kaggle-discussion-research`の候補収集、本文・コメント・返信確認、ノイズ除去を行う。
2. 出力先だけ`docs/competitions/<slug>/discussion.md`へ統一する。
3. Top/Hot/Recent/Active、host/admin告知、データ不備、ルール訂正、CV/LB乖離、再現可能なbaselineを確認する。
4. 「host確定」「複数参加者が再現」「単一参加者の仮説」「自分の推定」を分ける。
5. 現在流行している手法は、直近更新、複数投稿・Notebookでの採用、score、再現報告を根拠に判定する。

## 6. 公開Notebookを調査する

1. `$kaggle-notebook-research`のVoteCount、Hotness、DateRun、CommentCount、検索語の複数軸で候補を集める。
2. 出力先だけ`docs/competitions/<slug>/notebooks.md`へ統一する。
3. fork親子、copy、small modificationをまとめ、同じ手法を重複集計しない。
4. EDA、baseline、training、inference、ensembleを分け、利用データ・model・score・更新日・votesを記録する。
5. 「高voteの定番」と「直近で増えている手法」を別々にまとめる。

## 7. 最高voteのEDAを導入する

1. 対象コンペで`search_notebooks`を`VoteCount`順に検索し、`EDA`、`data exploration`、`visualization`、`starter`でも補完する。
2. `search_content`でも公開Kernelを集め、competition ID/slugの一致、privacy、votes、更新日、fork親を確認する。
3. 上位候補の`get_notebook_info`本文を読み、主目的がEDAであることを確認する。titleだけでEDA判定しない。
4. 条件を満たす公開EDAの中で最大votesの1件を選ぶ。取得日、votes、候補範囲、選定理由を`notebooks.md`へ残す。
   - 有効なEDA候補が0件なら非EDAで代用せず、その事実と検索範囲を記録して導入を停止する。
5. author、URL、version、licenseを確認する。派生物の再配布条件が不明または禁止なら、書き込み前にユーザーへ確認する。
6. `get_notebook_info`の`blob.source`を一時保存し、`notebook/EDA/<owner>__<slug>.ipynb`へ配置する。
7. Markdownセルの自然言語だけを日本語へ翻訳する。
   - codeセルの`source`、comments、文字列、magic、outputs、execution countを変更しない。
   - 数式、URL、引用元、filename、column名、API名、model名を維持する。
   - HTMLを含むMarkdownは構造を壊さず、表示テキストだけを翻訳する。
8. 原本と翻訳版を比較し、codeセルの`source`とoutputsが同一、Notebook JSONが妥当であることを確認する。
9. author、原本URL、version、votes、license、翻訳範囲を`notebooks.md`へ記録する。

## 8. 整合性を確認する

1. 並列タスクがすべて終了し、中途のダウンロードや展開プロセスが残っていないことを確認する。
2. 5つのMarkdownでtitle、slug、日付、metric、期限、制約が一致することを確認する。
3. rulesとDiscussionが矛盾する場合はrulesを優先し、Discussion側に注意を書く。
4. Notebook手法がexternal data/model制約に抵触しないか確認する。
5. すべての重要な断定にKaggle URL、page名、topic/comment ID、Notebook refのいずれかを付ける。
6. 未取得ページ、未読topic、取得できないcomments、未確認licenseを隠さない。
7. 最後に作成物一覧、データ件数、調査範囲、導入EDA、使用したデータ取得モデルまたはモデル指定不可の事実、残課題を報告する。
