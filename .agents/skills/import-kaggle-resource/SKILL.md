---
name: import-kaggle-resource
description: Kaggle MCPでCompetition、Dataset、Model、Notebook出力、Notebookソースを取得し、リポジトリの./input配下へ安全に配置する。ユーザーが「コンペを開始」「COMPETITIONのデータを取得」、またはKaggleのDataset・Model・Notebookを「import」「download」「inputへ追加」するよう依頼したときに使う。
---

<!--
SKILL.md
Where: .agents/skills/import-kaggle-resource.
What: Import Kaggle resources into the repository input tree via Kaggle MCP.
Why: Reproduce competition data and Kaggle Notebook input dependencies locally without collisions.
-->

# Import Kaggle Resource

Kaggle MCPでリソースを取得し、種別・所有者・slugを保持して`./input`へ配置する。
Kaggle CLI、Kaggle Python API、KaggleHub、`tools/download_dataset.py`は使わない。

## 配置規則

| 種別 | handle | 保存先 |
|---|---|---|
| Competition | `$COMPETITION` | `input/competitions/{competition}/` |
| Dataset | `{owner}/{dataset}` | `input/datasets/{owner}/{dataset}/` |
| Model | `{owner}/{model}/{framework}/{variation}/{version}` | `input/models/{owner}/{model}/{framework}/{variation}/{version}/` |
| Notebook出力 | `{owner}/{notebook}` | `input/notebook-outputs/{owner}/{notebook}/` |
| Notebookソース | `{owner}/{notebook}` | `input/notebooks/{owner}/{notebook}/` |

Kaggle Notebook本体はDatasetやNotebook出力をInputパネルへattachし、Modelを`/kaggle/input/{model}/{framework}/{variation}/{version}`へmountする。
このリポジトリでは衝突防止と取得元の追跡のため、さらに種別とownerをパスへ含める。

## 種別判定

1. Competitionの依頼では、リポジトリルートのプロセス環境変数`COMPETITION`だけをslugとして使う。空なら停止して設定を依頼し、`.env.example`や文脈から推測しない。
2. その他はURLまたはhandleから種別とslugを抽出する。
3. `owner/slug`だけではDatasetとNotebookを区別できないため、依頼文で確定できなければKaggle MCPのmetadataを確認する。
4. 「NotebookをInputへ追加」「Notebookをimport」はNotebook出力として扱う。
5. `.ipynb`、script、code、sourceの取得が明示された場合だけNotebookソースとして扱う。
6. Modelはvariationとversionが必要。version省略時は`get_model_variation`で最新versionを確定する。

## 事前確認

1. Kaggle MCPで正規handle、公開範囲、version、容量を確認する。
   - Competition: `get_competition`、`get_competition_data_files_summary`
   - Dataset: `get_dataset_info`、`get_dataset_files_summary`
   - Model: `get_model`、`get_model_variation`
   - Notebook: `get_notebook_info`、出力なら`list_notebook_files`
2. CompetitionではMCPのslugが`COMPETITION`と一致し、`user_has_entered == true`であることを確認する。
   - 未参加ならコンペURLを提示して停止し、Kaggle上での規約同意を依頼する。参加済みと偽らない。
   - 認証エラーならKaggle MCPの認証を案内し、認証後に再確認する。
3. 対応する保存先を組み立て、`./input`外へ出ないことを確認する。
4. 必要容量と空きディスクを比較する。
5. 保存先が空でなければ上書きせず、既存内容とversionを報告して確認を求める。
6. private、同意必須、認証切れで取得できない場合は、Kaggle MCPの認証を案内する。

## 取得

### Competition

1. `download_competition_data_files(competitionName=COMPETITION)`を呼ぶ。
2. 返された一時URLからZIPを一時領域へ取得する。
3. archive内に絶対パスや`..`がないことを確認し、既存ファイルを上書きせず`input/competitions/{COMPETITION}/`へ展開する。

### Dataset

1. `download_dataset(ownerSlug, datasetSlug, datasetVersionNumber, raw=false)`を呼ぶ。
2. 返された一時URLからZIPを一時領域へ取得する。
3. archive内に絶対パスや`..`がないことを確認し、`input/datasets/{owner}/{dataset}/`へ展開する。

例: `ravaghi/wellbore-geology-prediction-artifacts`は
`input/datasets/ravaghi/wellbore-geology-prediction-artifacts/`へ置く。

### Model

1. `get_model_variation`でcanonical framework、variation、versionを確定する。
2. `download_model_variation_version`を呼ぶ。
3. 返されたtar.gzのentryを検査し、`input/models/{owner}/{model}/{framework}/{variation}/{version}/`へ展開する。
4. framework名はKaggleのcanonical URLに現れる表記を使い、MCP enum文字列をディレクトリ名にしない。

ModelはKaggle Notebookでもversionがパスに含まれるため、省略しない。

### Notebook出力

1. `get_notebook_info`で正規handleとversionを確認する。
2. `list_notebook_files`をpage tokenがなくなるまで呼び、期待ファイルを記録する。
3. `download_notebook_output`を呼び、返されたZIPを`input/notebook-outputs/{owner}/{notebook}/`へ展開する。

Inputとして使えるのは保存済みNotebook実行の出力であり、`.ipynb`ソースではない。

### Notebookソース

1. `get_notebook_info`の`blob.source`を取得する。
2. `kernel_type == notebook`ならJSON妥当性を確認し、`input/notebooks/{owner}/{notebook}/{notebook}.ipynb`へ保存する。
3. scriptならlanguageに対応する拡張子で`input/notebooks/{owner}/{notebook}/{notebook}.{ext}`へ保存する。

## 共通の安全策

- KaggleへのアクセスはKaggle MCPだけを使う。MCPが返す署名付きURLの取得には`curl --fail --location --retry 3`などを使ってよい。
- 署名付きURLを回答、ファイル、ログへ残さない。
- ZIP/tar.gzは一時領域へ保存し、検証成功後に削除する。
- archiveを既存ディレクトリへ直接上書き展開しない。
- version違いを同じ保存先へ混在させない。
- DatasetやNotebook出力の明示versionを取得しても、ユーザー指定の安定パスを維持する。置換前に確認する。

## 検証

1. CompetitionとDatasetはMCPの`total_file_count`と展開後ファイル数を比較する。
2. Modelはarchiveの安全なfile entry数と展開後ファイル数を比較する。
3. Notebook出力は`list_notebook_files`の全ページと展開後の相対パスを比較する。
4. Notebookソースは`.ipynb`のJSON妥当性、またはscriptが空でないことを確認する。
5. 不一致なら成功扱いにせず、欠落数と再試行方針を示す。
6. 完了時に種別、正規handle、version、保存先、ファイル数、容量を報告する。

## 公式根拠

- KaggleHub: Kaggle NotebookではDataset、Model、Notebook出力がInputへattachされる。
  https://github.com/Kaggle/kagglehub
- Kaggle Model Metadata: Modelのmount pathは`/kaggle/input/{model}/{framework}/{variation}/{version}`。
  https://github.com/Kaggle/kaggle-api/wiki/Model-Metadata
- Kaggle CLI Kernels: Notebookソースのpullと実行出力のoutputは別操作。
  https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md
