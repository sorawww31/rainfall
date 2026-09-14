---
name: kaggle-to-notion
description: 指定された experiments/expXXX_* ディレクトリの Kaggle サブミッション結果を MCP 経由で取得し、コード、config、README のベース実験との差分を含む実験サマリを Notion 実験管理 DB に記録する。ユーザーが「Notion に実験まとめて」「Kaggle の結果を Notion に送って」「expXXX のスコアを Notion に記録」「サブミット結果を同期」などを依頼したとき、または Kaggle/BirdCLEF 実験を「ベース exp との差分 + サブミットスコア」で 1 ページに残したいときに使う。
---

# Kaggle to Notion

この Skill は、Kaggle 実験ディレクトリを読み、Kaggle 提出スコアとローカル差分をまとめて Notion に 1 実験 1 ページで記録する。
外部書き込みを伴うため、Notion 先、既存ページ更新、大量変更の挙動が曖昧なときはユーザーに確認してから進める。

## --dry-run の効果スコープ

`--dry-run` を指定した場合、各ステップの挙動は次のとおり。

| ステップ | dry-run での動作 |
|---|---|
| 1. 実験ディレクトリを読む | 通常通り実行 |
| 2. ベースとの差分を要約する | 通常通り実行 |
| 3. Kaggle サブミッションを取得する | 通常通り実行（MCP 呼び出しあり） |
| 4. Notion 書き込み先を解決する | 検索・fetch は行う。既存ページ検出時は確認 prompt を出さず、payload に上書き候補フラグだけ立てる |
| 5. ページ本文を作る | 通常通り実行 |
| 6. Notion に書き込む | **スキップ**。予定プロパティと本文を会話に出して終了 |

## 前提確認

開始時に次を確認する。

- Kaggle MCP が使えること。未認可なら authorize 手順を案内して停止する。
- Notion MCP が使えること。検索や作成が未認可ならセットアップを案内して停止する。
- `experiments/` 配下に `expXXX_*` 形式の実験ディレクトリがあること。

MCP ツール名が環境で固定されていない場合は、利用可能な Kaggle/Notion ツールを検索してから使う。元コマンド環境では Kaggle は `kaggle-wsl`、Notion は `claude_ai_Notion` を想定している。

## 引数

ユーザー依頼から次を解釈する。

- `experiment_dir` は必須。例: `exp026_absmax`。`exp026` のような接頭辞だけなら `experiments/` 直下を前方一致で解決する。
- `notion_url_or_id` は任意。未指定なら Notion を検索し、DB 候補を 3〜5 件提示して選ばせる。
- `--base exp_dir` は任意。比較基準を明示する。
- `--dry-run` は任意。Notion へ書き込まず、構築したプロパティと本文だけを会話に出す。

## ワークフロー

### 1. 実験ディレクトリを読む

1. `experiments/` 配下から `experiment_dir` を 1 つに解決する。複数ヒットしたら確認する。
2. ディレクトリ名から `exp_tag` を抽出する。例: `exp026_absmax` なら `exp026`。
3. 存在する範囲で次を読む。
   - `README.md` 全体
   - `exp/*.yaml` の一覧と各ファイルの先頭 30 行程度
   - `config.yaml`
   - `run.py`、`inference.py`、`launch.py` の冒頭
   - `src/` 配下のファイル一覧
4. ベース実験を決める。優先順は `--base`、README の lineage（当該 exp の節で直接言及している直前実験）、番号上の直前 `expNNN-1_*`。README に lineage が複数階層書かれている場合は、今回の exp の節が直接 import / extends している実験を採る。推定できない場合は根拠を添えてユーザーに聞く。

### 2. ベースとの差分を要約する

`diff -ruN experiments/<base_dir> experiments/<experiment_dir>` などのローカルファイル比較を使い、Notion には意味のある差分だけ入れる。

- `exp/*.yaml` と `config.yaml` は unified diff を使う。30 行を超える場合は要約する。
- 追加/削除ファイルを列挙する。
- `src/` の変更は関数/クラス単位で「何が追加・削除・変更されたか」を 1〜3 行で要約する。
- `README.md`, `src/`, `exp/`, `submissionスコア`の対応関係を明確にするべし。
- README は全文差分ではなく、該当 `exp_tag` の変更履歴セクションだけを引用する。

### 3. Kaggle サブミッションを取得し yaml と紐付ける

1. コンペ slug が不明なら README/config から推定し、必要なら Kaggle MCP で `birdclef` を検索する。BirdCLEF 固定にしない。
2. 自分の competition submissions を取得する。
3. `exp_tag` に一致する提出を次の優先順位でフィルタする。
   - 優先 1: notebook slug (URL) に `exp_tag` を含む（例: `clef-exp026-*`）
   - 優先 2: notebook title に `exp_tag` を含む
   - 優先 3: description に `exp_tag` を含む
   - 複数階層にヒットした場合は全て採用し、提出日時順に並べる。
   - 0 件ならエラーにしない。ローカル差分と README は続行して本文を組み立てる。「サブミッション未検出。ローカル情報のみで Notion に下書きを作りますか？」と確認し、yes なら `サブミッション結果` は `なし` の 1 行にし、`最高 public/private score` は `N/A` として 5 → 6 に進む。no ならここで停止する。
4. 各提出から `submitted_at`、public/private score、status、description、notebook 名と version を抽出する。
   - 本文テーブルの `提出日時 (JST)` 列: JST 文字列 (`YYYY-MM-DD HH:MM JST`)
   - DB の date プロパティ: ISO-8601 (UTC オフセット付き、例: `2026-04-25T14:35:33+00:00`)
   - `1 submission = 1 row` を原則とし、各行に推定 yaml 1 つとその根拠 1 つだけを入れる。
5. **提出物と exp/*.yaml の対応を推定する**。次の手順で試みる。
   - description や notebook バージョンコメントに yaml 名 (例: `003.yaml`, `003_seeds.yaml`) が書かれていれば採用する。
   - 書かれていない場合は exp/*.yaml の一覧から「複数件あるなら全て候補として列挙」し、「README の実験説明で最後に言及されている yaml」を有力候補とする。
   - どれか特定できない場合は「使用 yaml 不明（候補: xxx.yaml, yyy.yaml）」と記録し、本文の `## 利用した config` に候補を全て挙げる。

### 4. Notion 書き込み先を解決する

  - `notion_url_or_id` がある場合は fetch して DB かページかを判定する。DB なら 6. に従ってページを作成・更新する。ページなら既定はその配下に子ページを 1 つ作る。本文への直接追記はしない。子ページ作成ができない、または同名子ページが既にある場合は確認する。
  - 未指定なら Notion を「実験」「experiment」「BirdCLEF」「Kaggle」などで検索し、DB 候補を優先して提示する。
  - DB の場合は fetch でプロパティスキーマを読み、型に合うプロパティだけ設定する。`experiment_dir` / score / date / `base_dir` は exact-match を優先し、同型候補が複数あるときは自動選択せず停止する。
  - 同じ `experiment_dir` タイトルの既存ページがある場合: 衝突判定は `notion_url_or_id` で解決した target 配下に限定する。workspace 全体の別ページは衝突扱いにしない。`--dry-run` のときは確認 prompt を出さず payload に上書き候補フラグを立てる。通常実行時は target 配下に同名ページがあるときだけ、既存ページを更新する / 別ページを作る / 中止のどれにするか確認する。

### 5. ページ本文を作る

次の順序で Markdown 本文を作る。DB プロパティに入る値は本文と重複させすぎない。
0 件のときはこのテンプレートを置き換え、`## サブミッション結果` の直下に `- なし` の 1 行だけを置く。`サブミッション数` は `0`、`最高 public/private score` は `N/A / N/A` とする。

```markdown
# <experiment_dir>

## サマリ
- ベース: <base_dir>
- exp_tag: <exp_tag>
- サブミッション数: <n>
- 最高 public score: <best_public> / 最高 private score: <best_private>

## サブミッション結果
| 提出日時 (JST) | notebook | yaml (推定) | status | public | private | description |
| --- | --- | --- | --- | --- | --- | --- |
| ... |
## 今回の変更（README より）
> 該当 exp_tag の変更履歴

## ベース (<base_dir>) との差分
### exp/*.yaml の差分
...

### config.yaml の差分
...

### コードの変更
- `src/<file>.py`: 変更の意味

## 利用した config
- 主要 preset: <yaml 名（不明なら候補を列挙）>
- 使用 yaml とスコアの対応（推定）:
  | yaml | best public | 根拠 |
  | --- | --- | --- |
  | 003.yaml | 0.910 | description に記載 |
- runtime 既定値: ...
```

0 件時の代替フォーマットは次のとおり。

```markdown
# <experiment_dir>

## サマリ
- ベース: <base_dir>
- exp_tag: <exp_tag>
- サブミッション数: 0
- 最高 public score: N/A / 最高 private score: N/A

## サブミッション結果
- なし

## 今回の変更（README より）
> 該当 exp_tag の変更履歴

## ベース (<base_dir>) との差分
...

## 利用した config
...
```

差分が長い場合は Notion のコードブロックやトグルに分け、巨大な本文を直貼りしない。

### 6. Notion に書き込む

`--dry-run` なら送信せず、予定プロパティと本文を会話に出して終了する（「--dry-run の効果スコープ」表参照）。

DB に作る場合はスキーマに合わせて自然に埋まるプロパティだけ設定する。

- タイトル列: `experiment_dir`
- スコアの数値列: 最高 public score
- 日付列: 最新 submission の `submitted_at`（ISO-8601 UTC オフセット付き）
- ベース exp のテキスト列または relation: `base_dir`

DB に期待プロパティが存在しない場合の優先順位:
1. 同型の別プロパティ（例: title が無くても text 列があればそこへ）
2. 本文側に補足して DB プロパティは設定しない
3. スキップして完了報告の「取りこぼし」欄に記載

## 完了報告

最後に短く報告する。

- 作成または更新した Notion ページ URL（dry-run なら「dry-run のため書き込みなし」）
- 最高 public/private score
- ベース実験
- サブミッション件数と pending/failed の内訳
- 取りこぼし。例: README なし、`exp/` 空、Kaggle 0 件、使用 yaml 不明
