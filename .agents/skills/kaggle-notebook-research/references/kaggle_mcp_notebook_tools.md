<!--
kaggle_mcp_notebook_tools.md
Where: .agents/skills/kaggle-notebook-research/references.
What: Practical notes for Kaggle MCP notebook research tools.
Why: Keep SKILL.md concise while preserving observed tool behavior and query patterns.
-->

# Kaggle MCP Notebook Tools

このreferenceは、公開Notebook調査でKaggle MCPを使うときの実用メモ。

## Tool Selection

| 目的 | 優先ツール | メモ |
| --- | --- | --- |
| 軽いNotebook一覧 | `search_notebooks` | ref/title/author/last_run_time/votesを素早く取れる。 |
| fork・score・comment込み一覧 | `search_content` | `Kernel`に絞ると`fork_parent_kernel_url`、`best_public_score`、medal、comments、owner tierが取れる。 |
| 本文・metadata確認 | `get_notebook_info` | 本文全体が返るため、代表候補だけに使う。 |
| 出力ファイル確認 | `list_notebook_files` | model、npz、json、submissionなどの存在を確認する。 |
| セッション出力確認 | `list_notebook_session_output` | 実行セッションのoutput一覧が必要なときだけ使う。 |
| 出力取得 | `download_notebook_output` | 小さい特定ファイルだけに限定する。 |

## Observed BirdCLEF 2026 Patterns

2026-04-26に`birdclef-2026`で試した挙動:

- `search_notebooks(competition="birdclef-2026", sortBy="VoteCount")`は高vote候補を素早く返す。
- `search_notebooks(..., sortBy="Hotness")`は最近伸びている候補も混じる。
- `search_notebooks(..., search="perch", sortBy="Relevance")`はPerch系のstarter、派生、ensembleを拾いやすい。
- `search_content(filters.query="birdclef-2026 pantanal distill", documentTypes=["Kernel"], canonicalOrderBy="Votes")`は同名派生の親子関係とpublic scoreを拾えた。
- `get_notebook_info`はNotebook本文のJSONが非常に大きい。まずmetadataだけ見て、本文はセル見出し・設定・差分箇所に絞る。

## Query Patterns

軽量候補:

```text
search_notebooks(
  competition="<competition-slug>",
  group="Everyone",
  pageSize=20,
  page=1,
  sortBy="VoteCount"
)
```

詳細候補:

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

代表Notebook本文:

```text
get_notebook_info(userName="<owner>", kernelSlug="<slug>")
```

出力ファイル:

```text
list_notebook_files(userName="<owner>", kernelSlug="<slug>", pageSize=50)
```

## Family Mapping Checklist

- `fork_parent_kernel_url`があれば親URLを正とする。
- 親URLがない場合は、title、slug、Notebook見出し、data/model sources、主要関数名、score表記で近さを見る。
- 同名でもauthorが違うだけで別実装と断定しない。
- public scoreは`kernel_document.best_public_score`を優先し、Notebook title内のscoreは補助扱いにする。
- `dataset_data_sources`や`model_data_sources`が変わっているNotebookは、小さなコード差分でも実験価値がある可能性がある。
- `enable_internet=false`、`enable_gpu=true`、`machine_shape`は再現性・提出可否に関係するため記録する。

## Noise Rules

優先度を下げる:

- タイトルだけscore更新で、親との差分が見えないもの。
- `submission.csv`だけが出力で、モデルやログがなく、本文も小変更だけのもの。
- 実行エラー修正、依存install修正、batch size修正だけのもの。
- 古い高voteだが、より新しい派生に完全に取り込まれているもの。

優先度を上げる:

- 親より`best_public_score`が上がっている。
- 新しいdataset/model sourceを追加している。
- OOF、CV、pseudo label、postprocess、ONNX化、推論高速化が本文で説明されている。
- comment数が多く、議論で訂正や追加情報が出ていそう。
