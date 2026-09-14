---
name: kaggle-notebook-research
description: Kaggle MCPで公開Notebook/Kernelを検索し、fork親子関係、重複、派生、public score、利用データ・モデル・出力物、コード本文を根拠付きで調査してMarkdownにまとめる。ユーザーが「公開ノートブックを調査」「似たNotebookの違いを見たい」「BirdCLEFなど参加中コンペのnotebookから実装ヒントを拾って」「高スコアNotebookの派生元を追って」「Kaggle Notebookの重複・fork・改善点を整理して」などを依頼したときに使う。
---

<!--
SKILL.md
Where: .agents/skills/kaggle-notebook-research.
What: Research public Kaggle notebooks with fork and duplicate awareness.
Why: Turn noisy public notebook streams into actionable, source-grounded experiment ideas.
-->

# Kaggle Notebook Research

このSkillは、Kaggle MCPで公開Notebookを広く集め、単なるvote順ではなく、fork系譜・重複・小改変・実装上の差分まで見て、実験に使える知見を`docs/notebooks/*.md`へ残すための手順を定める。

Notebook調査は同名fork、丸写し、小さな後処理追加、古い高vote、低voteだが新しい高scoreが混ざる。候補収集、系譜整理、本文確認、要約を分けて進める。

詳細なMCPツール使い分けは、必要に応じて`references/kaggle_mcp_notebook_tools.md`を読む。

## 前提確認

1. 対象コンペを決める。
   - ユーザーがslugを明示したら優先する。例: `birdclef-2026`。
   - 「参加中コンペ」ならREADME、config、実験ディレクトリ名、Kaggle MCPのcompetition検索から候補を確認する。
2. Kaggle MCPツールが未ロードなら、tool discoveryで`search_notebooks`、`search_content`、`get_notebook_info`、`list_notebook_files`、`list_notebook_session_output`、`download_notebook_output`を探す。
3. `context()` MCPが使える環境ならKaggle APIや利用ライブラリの公式挙動確認に使う。使えない場合は「context MCPは利用不可」と明示し、Kaggle MCPの結果を根拠にする。
4. 出力先は通常`docs/notebooks/`とする。`kaggle-fetch-competition`から呼ばれた場合は`docs/competitions/<slug>/notebooks.md`を使う。既存ファイルを更新する場合は先に全文を読み、ユーザーの追記を戻さない。

## 候補を広く集める

### 1. 軽量一覧を複数軸で取る

`search_notebooks`を使い、同じコンペで複数sortと検索語を巡回する。

```text
search_notebooks(competition="<competition-slug>", group="Everyone", pageSize=20, page=1, sortBy="VoteCount")
search_notebooks(competition="<competition-slug>", group="Everyone", pageSize=20, page=1, sortBy="Hotness")
search_notebooks(competition="<competition-slug>", group="Everyone", pageSize=20, page=1, sortBy="DateRun")
search_notebooks(competition="<competition-slug>", group="Everyone", pageSize=20, page=1, sortBy="CommentCount")
```

検索語で補完する。

- 汎用語: `baseline`、`starter`、`training`、`inference`、`submission`、`ensemble`、`pseudo`、`CV`、`OOF`、`postprocess`、`ONNX`。
- 音声: `perch`、`SED`、`mel`、`soundscape`、`window`、`TTA`、`threshold`。
- 画像: `backbone`、`augmentation`、`resolution`、`segmentation`、`TTA`。
- 表形式: `feature`、`target encoding`、`group split`、`leak`、`catboost`、`lightgbm`。
- NLP: `tokenizer`、`retrieval`、`embedding`、`prompt`、`sequence length`。

### 2. 詳細メタデータを取る

`search_content`を使うと、`search_notebooks`よりも派生調査に必要な情報が多い。Kernelだけに絞り、vote順・更新日順・検索語で集める。

```text
search_content(
  filters={
    query="<competition-slug> <keyword>",
    documentTypes=["Kernel"],
    privacy="Public"
  },
  canonicalOrderBy="Votes",
  pageSize=20
)
```

候補表には少なくとも次を残す。

- `id`、`title`、`owner_user.user_name`、`owner_user.tier`、URL。
- `create_time`、`update_time`、votes、medal、`total_comments`。
- `kernel_document.best_public_score`。
- `kernel_document.fork_parent_kernel_url`と`fork_parent_user`。
- 発見元: `VoteCount`、`Hotness`、`DateRun`、`keyword: perch`など。

## 系譜と重複を整理する

1. 同じNotebookファミリーをまとめる。
   - `fork_parent_kernel_url`があるものは親URLでつなぐ。
   - 同名title、slugの共通prefix、同じデータソース、同じモデル名、同じscore表記を補助特徴にする。
   - 親が取れないNotebookは、同名でも別実装の可能性を残す。
2. 候補を分類する。
   - `root`: 親が見えない、またはシリーズの起点。
   - `direct-fork`: Kaggle上の親URLがある。
   - `copy-or-near-copy`: 親URLはないがtitle/構成/データソースがほぼ同じ。
   - `small-mod`: 閾値、TTA、後処理、batch size、LB向け係数など小変更。
   - `substantial-mod`: 新モデル、学習手順、pseudo label、外部データ、特徴抽出、CV設計など実装の芯が変わる。
   - `eda-or-utility`: 実験案よりデータ理解、可視化、変換、提出補助が主目的。
3. 優先順位を付ける。
   - 高public score、親よりscoreが上がった派生、最近更新、高comment、高vote、上位tier、利用データ・モデルが新しいものを優先。
   - 高voteでも古く、派生に取り込まれているだけならrootとして読む。
   - 低voteでもrecentでscoreや新規手法が強いものは読む。

## Notebook本文を読む

`get_notebook_info`は本文全体を返し、非常に大きくなることがある。全候補に呼ばず、各ファミリーから代表を選ぶ。

読む代表:

- rootまたは最古の高品質Notebook。
- best public scoreが高い派生。
- titleやmetadataで明確な新機能を主張する派生。
- コメント数が多いNotebook。
- 自分の実験に近いNotebook。

確認する項目:

1. `metadata`
   - `current_version_number`、`last_run_time`、`enable_gpu`、`enable_internet`、`machine_shape`、`docker_image`。
   - `competition_data_sources`、`dataset_data_sources`、`kernel_data_sources`、`model_data_sources`。
2. `blob.source`
   - JSONとして読める場合はNotebookセルに分解して、markdown見出し、設定値、関数名、出力保存、提出処理を見る。
   - すべてを要約しない。差分判定に効くセルだけを読む。
3. 出力物
   - `list_notebook_files`でモデル、npz、json、submissionなどを確認する。
   - `list_notebook_session_output`でセッション出力が必要か確認する。
   - `download_notebook_output`は必要な小さいファイルに限定する。提出CSVや巨大モデルを無目的に落とさない。

## 実装差分を抽出する

Notebookファミリーごとに、親から何が変わったかを要約する。

- データ: 外部dataset、pseudo label、OOF cache、metadata、taxonomy、過年度データ。
- モデル: backbone、Perch/embedding、SED、SSM/RNN/Transformer、ONNX変換、ensemble。
- 学習: fold、group split、loss、mixup/cutmix、sampling、early stopping、SWA、蒸留。
- 推論: window長、overlap、batch、TTA、postprocess、threshold、rank/file-level scaling。
- 検証: CV、OOF、public score、LB依存、hidden testで壊れそうな仮定。
- 再利用性: 自分のrepoに移植しやすいか、依存や実行時間が重いか、ルール確認が必要か。

「scoreが上がった」と書く場合は、Kaggle MCPで確認できた`best_public_score`またはNotebook内の明記を出典付きで残す。推測なら推測と書く。

## Markdownへ保存する

出力先は`docs/notebooks/<YYYY-MM-DD>-<competition-slug>-notebook-research.md`を基本にする。
単一ファミリーだけなら`docs/notebooks/<YYYY-MM-DD>-<competition-slug>-<family>.md`にする。

新規Markdownには冒頭コメントを置く。

```markdown
<!--
<filename>
Where: docs/notebooks.
What: Kaggle public notebook research summary for <competition>.
Why: Preserve actionable implementation ideas with fork, duplicate, and source context.
-->
```

本文テンプレート:

```markdown
# <調査タイトル>

- 取得日: <YYYY-MM-DD>
- 対象: <competition title> (`<slug>`)
- 依頼: <user request>
- 調査範囲: <sort/search terms/pages/families/read notebooks>
- 注意: <MCP制約、未取得本文、推測の有無>

## 結論
- <実装判断に直結する要点>

## Notebookファミリー
| family | 代表 | root/parent | 最高public score | votes | 判定 | 実装差分 | 優先度 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... | small-mod | TTA追加 | high |

## 候補一覧
| 判定 | ref | title | author | votes | score | updated | parent | 発見元 | 理由 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 詳細メモ
### <notebook title>
- URL: <Kaggle URL>
- ref/id/version: <owner/slug>, <id>, v<version>
- 親: <fork parent or none>
- metadata: <GPU/internet/data/model sources>
- 要点:
  - <親との差分と再利用可能な実装>
- リスク:
  - <LB依存、外部データ、時間、再現性、ルール確認>

## 実装候補
- <repoへ移すなら何をどこに入れるか>

## 未確認・リスク
- <読めていない候補、MCP制約、推測>

## Source Index
| 種別 | id/ref | title | URL | メモ |
| --- | --- | --- | --- | --- |
```

## 要約ルール

- 原文の長い引用は避け、要約中心にする。Notebook名、score、ファイル名、関数名、設定値は必要最小限だけ引用する。
- vote順だけで結論を出さない。fork親、public score、更新日、本文差分を一緒に見る。
- 同じtitleのNotebookを別物として扱う前に、親URLとコード構成を確認する。
- 開催中コンペではpublic LB最適化を過信しない。closed/private testで成立する条件を書く。
- ルールや外部データが絡む場合は、Kaggle公式ルールまたはcompetition情報を確認してから実装候補に入れる。

## 検証

1. 作成・更新したMarkdownを読み直し、リンク、表、未確認事項、推測表現を確認する。
2. skill自体を編集した場合は、skill-creatorの`quick_validate.py`で対象skillを検証する。
3. 共有skillを追加した場合は、生成アダプタを同期し、関連テストを追加または更新する。
4. 最後に`git diff -- docs/notebooks .agents/skills/kaggle-notebook-research tests`を確認し、調査範囲と未取得情報を報告する。
