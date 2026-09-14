---
name: kaggle-discussion-research
description: Kaggle MCPのdiscussion/forum系ツールでKaggle Discussion、Competition Solution、コメント、返信を調査し、docs/discussion/*.mdへ根拠付きで要約する。ユーザーが「XXXの1位解法を調査」「YYYの上位解法をまとめて」「参加中コンペの有用Discussionを調査」「このコンペのdiscussionから実装ヒントを拾って」など、Kaggle discussionやsolution writeupの調査・整理を依頼したときに使う。
---

<!--
SKILL.md
Where: .agents/skills/kaggle-discussion-research.
What: Research Kaggle discussion topics and summarize findings into docs/discussion.
Why: Preserve actionable competition knowledge with source links, including important comments.
-->

# Kaggle Discussion Research

このSkillは、Kaggle MCPでDiscussion本文だけでなくコメント・返信まで読み、実装に使える知見を`docs/discussion/*.md`へ残すための手順を定める。
Discussion検索はノイズが混ざるため、取得元URL、topic ID、comment ID、取得日を残し、推測と確認済み情報を分ける。

## 前提確認

1. ユーザー依頼から対象を決める。
   - 明示slugを優先する。例: `<competition-slug>`。
   - 「現在参加中のコンペ」ならREADME、config、実験名、Kaggle MCPのcompetition検索結果から候補を出す。
   - 「1位解法」「上位解法」は終了済みコンペのCompetition Solution / WriteUpを優先する。
   - 「有用投稿」は検索語だけに頼らず、Top、Hot、Recent、Active、高vote、高コメント数、host/admin投稿、データ不備、ルール、強いbaseline、LB共有、推論高速化を広く見る。
2. Kaggle MCPツールが未ロードなら、tool discoveryで`search_content`、`list_forum_topics`、`get_forum_topic`、`get_writeup_by_topic`を探す。
3. `context()` MCPが使える環境なら、Kaggle APIや利用ライブラリの挙動確認に使う。使えない場合は「context MCPは利用不可」と明示し、Kaggle MCPの結果を根拠にする。
4. 出力先は通常`docs/discussion/`とする。`kaggle-fetch-competition`から呼ばれた場合は`docs/competitions/<slug>/discussion.md`を使う。既存ファイルを更新する場合は、先に全文を読んでユーザーの追記を戻さない。

## Kaggle MCPで調査する

### 1. コンペを解決する

1. まず`search_content`でコンペslugまたは名称を検索する。
   - `documentTypes=["Competition"]`
   - active参加中なら`competitionFilters.status="Active"`も使う。
2. `search_content`がCompetition以外を返したり、候補が空なら`search_competitions(search="<slug>")`へ切り替える。
3. 採用する候補を`document_type == "COMPETITION"`、slug、title、deadline、team_count、team_rank、joined/bookmarked状態で確認する。
4. `competition_document`の`id`、`slug`、`enriched_info.url`をメモする。`search_competitions`を使った場合も、title、url、deadline、team_count、user_rankを同様にメモする。

Kaggle MCP利用時の注意:

- `search_content(documentTypes=["Topic"])`はTopic以外のKernelを返すことがある。Topic候補は必ず`document_type`か`parent_url`で絞る。
- `search_content(documentTypes=["Competition"])`もCompetition以外を返すことがある。Competition解決に失敗したら`search_competitions`へ切り替える。
- コンペ固有のforum idやcompetition idは、毎回MCPの検索結果から確認する。

### 2. Topic候補を網羅的に集める

`list_forum_topics`を主探索に使う。まず網羅パスでHot/Top/Recent/Activeを巡回し、その後に検索語で補完する。
`search_content`は補助として使い、Topic以外が混ざったら捨てる。

1. 網羅パス:
   - `list_forum_topics(category="Competitions", hasSearchQuery=true, searchQuery="<slug>", sortBy="Top", page=1..N)`
   - 同じ条件で`sortBy="Hot"`、`sortBy="Recent"`、`sortBy="Active"`も見る。
   - `N`は通常2〜3ページを目安にし、topic数が少ないコンペでは全件に近づける。大量コンペでは重複を除いて50〜100件程度を候補上限にする。
   - 終了済みコンペの解法調査では`category="CompetitionWriteUps"`、`sortBy="Top"`、`sortBy="Recent"`も見る。
   - 実APIでは、`searchQuery="<slug>"`付きだと`sortBy`を変えても先頭集合がかなり似ることがある。その場合は「複数経路を見た」と見なさず、`page=2..N`、`author="Admin"`、`search_content`補助、可能なら`forumId`指定へ広げて差分を作る。
2. Host/admin確認:
   - `author="Admin"`はhost/admin専用集合を保証しない。補助探索としてのみ使い、返却後に`author_type`や投稿者名でhost/admin topicだけを再抽出する。
   - `list_forum_topics(category="Competitions", author="Admin", hasSearchQuery=true, searchQuery="<slug>", sortBy="Recent")`を試す。
   - API上のauthor指定でhost投稿が十分拾えない場合は、網羅パス結果の`author_type`、title、tagsからhost/organizer投稿を拾う。
   - `forumId`がtopic取得結果などから見えているなら、`hasForumId=true`でそのforumに絞った列挙も試す。`get_forum`が権限不足でもtopic本文取得を優先して進める。
3. 候補表を作る:
   - topic id、title、URL、sortByでの発見元、votes、comment_count、post_date、last_comment_post_date、author_type、author tier/rank、tagsを記録する。
   - 同一topicは1行に統合し、発見元を`Top, Hot, Recent`のように複数残す。
   - votesが多い、Hotに出る、comment_countが多い、last_comment_post_dateが新しい、host/admin、上位者やGrandmasterの投稿、Notebook/Codeリンクあり、データ・ルール・評価に関わるものを優先して読む。
   - 低voteでもRecent/Activeで伸びているtopicや、コメントが多い質問topicは読む候補に残す。
4. ノイズを判定する:
   - 候補表に`read` / `skim` / `skip`を付け、`skip`にも理由を残す。
   - 原則skip: 個人のNotebook実行エラー、環境構築エラー、GPU/Internet/timeoutだけの相談、提出失敗ログ、Kaggle UIの一時不具合、データダウンロード不可、チーム募集、自己紹介、感想、雑談、重複質問。
   - 原則skim: 初心者質問、LB自慢、単発のscore共有、AIツール雑談、コードなしのアイデア投稿。コメントに上位者・host・具体実装・ルール訂正があればreadへ昇格する。
   - 原則read: host/admin発表、データ不備、評価・ルール・外部データ、leak、CV/LB乖離、再現可能なbaseline、学習/推論/後処理、公開Notebookの重要更新、上位者の具体コメント、複数人が検証した知見。
   - titleだけで捨てず、Hot/Top/高コメント数のtopicは最低限コメント要約や先頭数件を確認する。エラー投稿でもhost回答や汎用的な回避策がある場合は採用する。
5. 検索補完:
   - 網羅パスで見落としそうなテーマだけ検索語で補う。
   - 汎用語: `baseline`、`training`、`inference`、`score`、`LB`、`data`、`duplicate`、`leak`、`rules`、`external data`、`validation`、`CV`、`ensemble`、`postprocess`。
   - 対象コンペの説明、データ、評価指標、上位Notebook名から固有語を追加する。
   - 表形式なら特徴量、CV split、leak、target encoding、欠損処理を探す。
   - 画像ならaugmentation、pretrain、resolution、TTA、segmentation/detection/classification固有語を探す。
   - 音声ならwindow、embedding、SED、sampling rate、推論時間を探す。
   - NLPならtokenizer、sequence length、prompt、retrieval、external corpusを探す。
   - 時系列ならlag、rolling feature、group split、leak、horizonを探す。
   - 検索語が空振りでも終わらない。特にactive competitionではstickyなhost threadや高コメントtopicの返信に、rule訂正・metadata補足・submission制約が埋もれていることが多いので、host/admin threadをコメント込みで読む。
6. 解法探索:
   - 検索語を`"1st place solution <slug>"`、`"top solution <slug>"`、`"writeup <slug>"`、`"solution summary <slug>"`で試す。
   - 終了済みコンペでは`category="CompetitionWriteUps"`も試す。
7. `search_content(documentTypes=["Topic"])`はKernelやDatasetが混ざることがある。候補は`document_type == "TOPIC"`かつ`parent_url`または`enriched_info.url`が対象slugを含むものだけ採用する。検索語に合っても別コンペや一般Forumなら除外する。

読むtopic数は依頼の粒度に合わせる。指定がなければ、候補表を作った上で`read`上位10〜20件を本文・コメント込みで読み、`skim`は必要に応じて確認する。
「網羅的に」「全部見て」に近い依頼なら、候補数、ページ数、未読理由をMarkdownに残し、時間内に読めなかったtopicを未確認に入れる。

### 3. Topic本文とコメントを読む

各候補topicに対して`get_forum_topic`を呼ぶ。

```text
get_forum_topic(forumTopicId=<topic_id>, includeComments=true, hasInitialPageSize=true, initialPageSize=100)
```

1. `first_message.raw_markdown`を読む。
2. `comments[].raw_markdown`とネストした`replies[].raw_markdown`を読む。
3. `is_partial=true`やコメント数不足がある場合は、`startingCommentId`で追加取得できるか試す。取得できないコメントは「未取得」と明記する。
4. コメントは重要度で拾う。
   - 投稿者・上位者・host・高voteの補足。
   - OPの誤り訂正、Notebookリンク、score更新、設定値、外部データ可否、推論時間、再現条件。
   - 質問への回答にだけ具体的な実装情報がある場合。
5. 重要コメントには`https://www.kaggle.com<topic_url>#<comment_id>`形式のリンクを付ける。

### 4. WriteUpを確認する

解法・上位解法調査では、topic候補ごとに`get_writeup_by_topic`を試す。

- 取得できた場合はWriteUp本文を優先し、Discussionコメントは補足として扱う。
- 取得できない場合は、Discussion本文とコメントだけに基づく要約であることを明記する。
- 順位、score、team名をKaggle MCPで確認できない場合は推測で書かない。

## Markdownへ保存する

出力先は`docs/discussion/<YYYY-MM-DD>-<competition-slug>-<short-topic>.md`を基本にする。
複数topicを横断する調査なら`docs/discussion/<YYYY-MM-DD>-<competition-slug>-discussion-research.md`にまとめる。

新規Markdownには冒頭コメントを置く。

```markdown
<!--
<filename>
Where: docs/discussion.
What: Kaggle discussion research summary for <competition>.
Why: Preserve actionable ideas and source links from topics, comments, and writeups.
-->
```

本文テンプレート:

```markdown
# <調査タイトル>

- 取得日: <YYYY-MM-DD>
- 対象: <competition title> (`<slug>`)
- 依頼: <user request>
- 調査範囲: <Top/Recent/WriteUp/search terms/pages>
- 候補数: <collected/read/skipped>
- 注意: <未取得コメント、MCP制約、推測の有無>

## 結論
- <実装や判断に直結する要点>

## 実装ヒント
- <model/data/training/inference/validation/ensembleなど>

## 候補一覧
| 判定 | 優先 | topic id | title | 発見元 | votes | comments | last activity | 理由 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| read | high | ... | ... | Top, Hot | ... | ... | ... | 高voteかつコメント多 |
| skip | low | ... | Notebook error | Recent | ... | ... | ... | 個人環境の実行エラーのみ |

## Topic別メモ
### <topic title>
- URL: <Kaggle URL>
- topic id: <id>
- votes/comments: <n>/<n>
- 要点:
  - <OPとコメントを統合した要約>
- 重要コメント:
  - <author> (<date>, comment <id>): <要約> <URL#comment_id>
- 信頼度: <高/中/低> - <理由>

## 未確認・リスク
- <閉じたtestで使えるか、ルール確認が必要か、再現性不足など>

## Source Index
| 種別 | id | title/comment | URL | メモ |
| --- | --- | --- | --- | --- |
| topic | ... | ... | ... | ... |
| comment | ... | ... | ... | ... |
```

## 要約ルール

- 原文の長い引用は避け、要約中心にする。必要な短いフレーズ、score、ファイル名、Notebook名だけ引用する。
- OPだけで結論を出さず、コメント・返信で訂正や実装詳細が出ていないか確認する。
- 「参加者の推測」「host/organizerの確定情報」「自分の推定」を分けて書く。
- 実装に使う場合は、Notebookリンク、モデル名、学習データ、外部データ、推論時間、LB/CV、コンペルールとの関係を分けて記録する。
- 現在開催中コンペではLB投稿を過信しない。closed/private testで成立する条件を必ず書く。

## 検証

1. 作成・更新したMarkdownを読み直し、リンク、見出し、表、未確認事項を確認する。
2. skill自体を編集した場合は、skill-creatorの`quick_validate.py`で対象skillを検証する。
3. 共有skillを追加した場合は、生成アダプタを同期し、関連テストを追加または更新する。
4. 最後に`git diff -- docs/discussion .agents/skills/kaggle-discussion-research`を確認し、調査範囲と未取得情報を報告する。
