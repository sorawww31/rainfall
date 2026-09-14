---
name: plan-create
description: ユーザーの要望から実装前の設計書または実装計画を作成する。ユーザーが「設計書を作って」「実装計画を立てて」「plan-create」「方針をまとめて」「AIエージェント向けの実装手順にして」などを依頼したとき、またはコード変更前に安全で検証可能な計画を文書化する必要があるときに使う。
---

# Plan Create

<!--
.agents/skills/plan-create/SKILL.md
Where: project-local Codex skill.
What: Instructions for drafting implementation design documents from a shared template.
Why: Keep agent implementation plans concrete, reviewable, and grounded in verified docs.
-->

## 概要

ユーザーの要望を、実装担当AIエージェントがそのまま使える設計書に変換する。
設計書は `.agents/docs/templates/plan-template.md` を必ず参照し、最小変更、安全性、検証可能性、未解決事項を明示する。

## 必ず読むテンプレート

設計書を作る前に、リポジトリルートから次を全文読む。

- `.agents/skills/plan-create/docs/plan-template.md`

テンプレートが存在しない場合は、作業を止めてユーザーに知らせる。別形式で勝手に代替しない。

## ワークフロー

1. ユーザー要望を短く再確認し、成果物が「会話上の設計書」か「ファイル作成」かを判断する。
2. 関連ファイルを特定し、変更候補のファイルは編集前に全文読む。設計書作成だけならファイルは変更しない。
3. 外部API、ライブラリ、AIエージェント設計の前提が含まれる場合は、現在の公式ドキュメントまたは一次情報で確認する。`context()` MCP が使える環境では `resolve_library-id`、`get-library-docs` の順で確認する。使えない場合は公式ドキュメント検索で代替し、代替した事実を設計書に書く。
4. `.agents/docs/templates/plan-template.md` の章立てを維持し、不要な章は削除せず `該当なし` または理由を書く。
5. 計画は実装しない。ユーザーが明示的に実装まで求めている場合でも、まず設計書を作成して確認可能な状態にする。
6. 確信度が80%未満、要件が曖昧、セキュリティ/権限/UX/API契約が変わる場合は、設計書の `未解決事項` に書き、必要ならユーザーに確認する。

## 出力先

- ユーザーがパスを指定した場合は、そのパスに設計書を書く。
- ユーザーがファイル作成を求めたがパス未指定の場合は、`./docs/plans/<YYYYMMDD>-<short-slug>-design.md` に書く。
- ユーザーが会話上の計画だけを求めた場合は、Markdown で返す。

## 設計書の品質基準

- 最小構成から始め、agentic な複雑性は必要性が明確な場合だけ追加する。
- workflow と agent の違いを明示し、選択理由を書く。
- tool contract、guardrail、trace/log、評価/テスト、human-in-the-loop の扱いを書く。
- 変更ステップは小さく、レビューしやすく、戻しやすくする。
- 「調査済みの事実」と「推測」を分けて書く。
- 外部情報を使った場合は、参照元と確認日を設計書に残す。

## 完了報告

最後に次だけを短く報告する。

- 作成した設計書のパス、または会話上に出したこと
- 参照した主なファイル/公式情報
- 未解決事項の有無
