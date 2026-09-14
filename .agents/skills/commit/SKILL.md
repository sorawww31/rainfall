---
name: commit-changes
description: 現在の Git worktree の変更を確認し、必要なら複数の論理コミットへ分割して安全にコミットする。ユーザーが「commitして」「今の変更をコミット」「何個かに分けてコミット」「とりあえずcommit」「変更を保存して」などを依頼したとき、または作業完了後にローカル変更をレビュー可能な commit にまとめたいときに使う。
---

# Commit Changes

<!--
.agents/skills/commit-changes/SKILL.md
Where: project-local Codex skill.
What: Workflow for turning current Git worktree changes into one or more safe commits.
Why: Prevent accidental commits of unrelated, unreviewed, or secret changes while keeping commits reviewable.
-->

## 概要

現在の Git 差分を読み、ユーザーの意図に合う最小単位でコミットする。
既存の未コミット変更はユーザー作業の可能性があるため、内容を確認せずにまとめて staging しない。

## ワークフロー

1. `git status --short` と `git status --branch --short` で変更量、現在ブランチ、ahead/behind を確認する。
2. 変更ファイルを特定し、コミット対象のファイルは全文または意味のある差分を読む。最低限 `git diff -- <path>`、staged 済みなら `git diff --cached -- <path>` を確認する。
3. secret、巨大生成物、不要な一時ファイル、ユーザー指示と無関係な変更がないか確認する。疑わしい場合はコミットせずユーザーに聞く。
4. コミット分割方針を決める。
   - 1コミット: 変更が単一目的で、実装・テスト・docs が同じ成果に属する。
   - 複数コミット: 独立した機能、修正、docs、生成アダプタ、リファクタが混在する。
   - 混在ファイル: 同じファイルに複数目的の変更がある場合は `git add -p` を優先する。
5. 各コミットごとに `git add -- <paths>` または `git add -p` で対象だけ staging する。`git add .` は、全差分を読んで全て対象と判断した場合だけ使う。
6. `git diff --cached --stat` と `git diff --cached --check` を実行し、staged 内容と空白エラーを確認する。
7. 可能なら関連テストや lint を実行する。時間や依存関係で実行できない場合は理由を記録して続行可否を判断する。
8. `git commit -m "<message>"` でコミットする。hook が失敗した場合、原因を確認し、`--no-verify` はユーザーが明示したときだけ使う。
9. 最後に `git status --short` と `git log --oneline -n <commit_count>` で結果を確認する。

## コミットメッセージ

- 1行目は命令形または簡潔な要約にする。
- 既存履歴に prefix 規約があれば従う。迷う場合は `git log --oneline -n 20` を確認する。
- 複数行本文は、理由や注意点がレビューに必要な場合だけ追加する。
- 日本語プロジェクトでは日本語、英語履歴が多いプロジェクトでは英語を優先する。

## 停止して確認する条件

- 変更の由来が不明で、ユーザー作業を巻き込む可能性がある。
- secret、認証情報、個人情報、巨大バイナリ、生成物の混入が疑われる。
- テスト失敗を残したままコミットする必要がある。
- amend、rebase、reset、force push など履歴を書き換える操作が必要になる。
- 確信度が80%未満。

## 完了報告

最後に次だけを短く報告する。

- 作成した commit hash と message
- 分割した場合は各 commit の意図
- 実行した検証コマンドと結果
- 残った未コミット変更の有無
