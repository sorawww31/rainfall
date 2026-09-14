# Kaggle テンプレート

## コンペを始める
### 0. GitHubからリポジトリを作成する
GitHubページの右上「Use this template」から、リポジトリを作成する。
その後、自分の環境に git cloneする。
### 1. 環境変数を設定する

`.env.example`をコピーし、Kaggleユーザー名、API token、出場するコンペのslugを`.env`へ記入する。

```sh
cp .env.example .env
```

```dotenv
KAGGLE_USER_NAME=your_kaggle_user_name
KAGGLE_API_TOKEN=your_kaggle_api_token
COMPETITION=birdclef-2026
```

秘密情報を含む`.env`はcommitしない。AIエージェントを起動する前に、同じshellで環境変数を読み込む。

```sh
set -a
source .env
set +a
```

### 2. AIでオンボーディングする

Competitionデータ、公式ルール、Discussion、公開Notebook、EDAを一括で準備する場合は、次のSkillを使う。

```text
$kaggle-fetch-competition を使ってCOMPETITIONのコンペをオンボーディングして
```

データ取得だけを依頼する場合は`$import-kaggle-resource`を使う。

### 3. 手動でデータを取り込む

AIやKaggle MCPを使わず、Competitionデータを直接取得する場合は次を実行する。

```sh
uv run python tools/download_dataset.py competition "$COMPETITION"
```

Kaggle Datasetを追加する場合は`owner/dataset`形式で指定する。

```sh
uv run python tools/download_dataset.py dataset owner/dataset-slug
```

既存の保存先を置き換える必要がある場合だけ`--force`を付ける。

## 特徴
- Docker によるポータブルなKaggleと同一の環境
- Hydra による実験管理
- 実験用スクリプトファイルを major バージョンごとにフォルダごとに管理 & 実験パラメータ設定を minor バージョンとしてファイルとして管理
   - 実験用スクリプトと実験パラメータ設定を同一フォルダで局所的に管理して把握しやすくする
- dataclass を用いた config 定義を用いることで、エディタの補完機能を利用できるように
## フォーク源から追加した機能
- 実験管理が容易に
  - ```experiments/{major_exp_name}```単位での実験管理
  - モデル、ソースコード、実験ログを一括でKaggle Datasetにして実験を管理
  - ```tools/upload_dataset.py```で一括データセット化
- 環境変数管理
  - ```.env.example```を追加
    - 環境変数にてAPI_KEY等を管理
    - それに伴い```compose.yaml```を修正

### 変更コードまとめ
* 実験スクリプト
    * ```experiments/exp000_sample```直下のディレクトリ構造
    * ```experiments/exp000_sample/run.py```
* 環境構築
  * ```Dockerfile```
  * ```Dockerfile.cpu```
  * ```compose.yaml```
  * ```compose.cpu.yaml```
  * ```.env.example```
* その他
  * ```tools/upload_dataset.py```

### Hydra による Config 管理
- Config は yamlとdictで定義するのではなく、dataclass を用いて定義することで、エディタの補完などの機能を使いつつタイポを防止できるようにする
- 各スクリプトに共通する環境依存となる設定は utils/env.py の EnvConfig で定義される
- 各スクリプトによって変わる設定は、実行スクリプトのあるフォルダ(`{major_exp_name}`)の中に `exp/{minor_exp_name}.yaml` として配置することで管理。
    - 実行時に `exp={minor_exp_name}` で上書きする
    - `{major_exp_name}` と `{minor_exp_name}` の組み合わせで実験が再現できるようにする

## Structure(罫線表記)
```text
.
├── experiments
│    └── exp000_sample
│        ├── exp
│        ├── utils
│        ├── src
│        └── run.py
├── input
├── notebook
├── tools
├── outputs
├── Dockerfile
├── Dockerfile.cpu
├── LICENSE
├── Makefile
├── README.md
├── .env.example
├── compose.cpu.yaml
└── compose.yaml

```
## 環境変数の設定
```sh
cp .env.example .env
```
を行い、`.env`に必要事項を記入

## AIエージェント設定

Codex, Cursor, Claude Code, GitHub Copilot, Gemini CLI 向けの指示・skill・command・MCP設定を用意しています。

- 共通指示: `AGENTS.md`
- 共通skill: `.agents/skills/*/SKILL.md`
- 共通command: `.agents/commands/*.md`

### Skillsの管理

Skillはすべて `.agents/skills/` を正として管理します。ClaudeやCodexなど各エージェント側のSkillディレクトリは直接編集しません。Skillを追加・更新・削除した後は、`.agents/sync_skills.sh` を実行して各エージェントへ反映します。

```sh
# skillを追加する場合
.agents/skills/<skill-name>/SKILL.md

# Claude、Codex、Gemini、Cursorへ反映
bash .agents/sync_skills.sh
```

`.claude/skills/`、`.codex/skills/`、`.gemini/skills/`、`.cursor/skills/` は同期生成物です。Skillの管理は必ず `.agents/skills/` で行ってください。

Kaggle MCPを使う場合は、`KAGGLE_API_TOKEN` を環境変数として設定してください。詳細は `docs/agent-integrations.md` を参照してください。

## Docker による環境構築
Dockerが利用できない方は、同md下部のuvによる環境設定を参照してください。
```sh
# imageのbuild
make build

# bash に入る場合
make bash

# jupyter lab を起動する場合
make jupyter

# CPUで起動する場合はCPU=1やCPU=True などをつける
```
### スクリプトの実行方法
```sh
make bash
python experiments/exp000_sample/run.py exp=001
```

`experiments/exp000_sample/run.py` は実行時に出力ディレクトリを自動作成します。

- 出力先のベース: `env.output_dir`（デフォルト: `outputs`）
- 実験ごとの出力先: `{env.output_dir}/{major_exp_name}/{minor_exp_name}`
  - `major_exp_name`: 実行スクリプトの親ディレクトリ名（例: `exp000_sample`）
  - `minor_exp_name`: `exp=...` で選んだ設定名（例: `001`）
- `init_output_dir`関数によって、適切な`cfg.env.exp_output_dir`が設定される
- `exp.name` を指定すると末尾に `_{exp.name}` が付きます
### つまりcfg.env.exp_output_dir を利用すればいい
例:
```sh
python experiments/exp000_sample/run.py exp=001 exp.name=baseline
# -> outputs/exp000_sample/001_baseline/
```

## Kaggle データセットの作成

### 1. 任意の1ディレクトリをアップロードする
```sh
# Kaggle API Keyが必要
# major_virsion_nameでそのまま提出
# -t: タイトル, -d: ディレクトリ
python tools/upload_dataset.py --title exp000 --dir experiments/exp000_sample
```

### 2. `--exp` で実験関連ディレクトリをまとめてアップロードする（新機能）
`--exp` を指定すると、次のパターンに一致するディレクトリを探して1つのDatasetにまとめます。

- `experiments/<exp>_*`
- `outputs/<exp>_*`

Dataset内では `experiments/` と `outputs/` のサブディレクトリとして保存されます。

`-t/--title` を明示指定した場合は、その値をDataset名として使用します。
未指定の場合は、最初に見つかった対象ディレクトリ名から自動でDataset名を決定します。

```sh
# 例: experiments/exp000_sample と output/exp000_sample をまとめてアップロード
python tools/upload_dataset.py --exp exp000

# 例: --exp 利用時にタイトルを明示指定
python tools/upload_dataset.py --exp exp000 --title exp000-custom
```

## uvによる環境構築
### uvのインストール
詳しくは[こちら](https://docs.astral.sh/uv/getting-started/installation/v)を参照
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
uv version # インストールの確認
```
### .venv 仮想環境の作成
```sh
# セットアップ
make uv-setup

# jupyter lab を起動する場合
make uv-jupyter

```
適宜追加したいモジュールは、以下のコマンドで追加してください。その他利用方法は
```sh
uv add numpy
```
その他利用方法は[こちら](https://docs.astral.sh/uv/)を参照してください。

**注意事項**
* pythonバージョン, numpyバージョンはkaggle kernelに合わせ最新版ではない
  * ```python==3.11.13```
  * ```numpy==1.26.4```
* ```torch, cuda```は、各環境に合わせインストールしてください。
### スクリプトの実行方法
```sh
uv run experiments/exp000_sample/run.py exp=001
```
