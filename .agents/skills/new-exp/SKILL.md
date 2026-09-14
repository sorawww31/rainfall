---
name: new-exp
description: Kaggle 実験を既存の experiments/expXXX_* から新しい experiments/expYYY_slug へコピーし、専用ブランチ作成と初期コピー commit まで進める。ユーザーが「新しい実験を作って」「new-exp」「exp をコピーして」「次の実験ブランチを切って」などを依頼したときに使う。
---

# New Exp

<!--
.agents/skills/new-exp/SKILL.md
Where: project-local Codex skill.
What: Workflow for starting a copied Kaggle experiment safely.
Why: Keep experiment setup, branch naming, and the initial commit consistent.
-->

## 概要

既存の `experiments/expXXX_*` を新しい `experiments/expYYY_slug` にコピーし、`expYYY/slug` ブランチで初期コピーだけを commit する。
このスキルの責務は初期コピー commit までに限定し、設計書作成や実装計画は扱わない。

## 事前確認

1. `AGENTS.md` を読み、リポジトリの作業ルールを確認する。
2. `git status --branch --short` で現在ブランチと既存の未コミット変更を確認する。
3. `find experiments -maxdepth 1 -type d -name 'exp[0-9][0-9][0-9]_*' | sort` で既存 experiment を確認する。
4. 既存の未コミット変更があっても破棄しない。今回 stage / commit するのは新規 `experiments/expYYY_slug` だけにする。

## 名前の決め方

1. ベース experiment は、ユーザー指定があればそれを使う。
2. 未指定で候補が1つだけなら、その experiment を使う。
3. 未指定で候補が複数あり、最新番号をベースにしてよい確信が80%未満ならユーザーに確認する。
4. 新番号 `YYY` は既存の最大 `expNNN` の次番号を3桁ゼロ埋めで選ぶ。ユーザー指定があれば、未使用か確認して優先する。
5. `slug` はユーザーの実験意図から短い lowercase の ASCII 名にする。ディレクトリは `expYYY_slug`、ブランチは `expYYY/slug` を基本にする。
6. `experiments/expYYY_slug` または `expYYY/slug` ブランチが既に存在する場合は、自動上書きせずユーザーに確認する。

## ワークフロー

1. 必要に応じて `.agents/skills/create-branch/SKILL.md` を読み、ブランチ作成の安全確認を適用する。
2. `YYY` と `slug` を決めたら、コピー前に `git branch --list 'expYYY/slug'` で衝突を確認する。
3. `git switch -c expYYY/slug` で専用ブランチを作成して移動する。コピー前に移動するのは、失敗時に元ブランチへ新規コピーを残しにくくするため。
4. `cp -r experiments/expXXX_base experiments/expYYY_slug` でベース experiment をコピーする。
5. コピー直後は新規 experiment の中身を編集しない。まず初期コピーだけを commit する。
6. `git status --short` と `git diff --stat -- experiments/expYYY_slug` を確認する。
7. 必要に応じて `.agents/skills/commit/SKILL.md` を読み、commit の安全確認を適用する。
8. `git add -- experiments/expYYY_slug` で新規 experiment だけを stage する。
9. `git diff --cached --stat` と `git diff --cached --check` を実行する。
10. `git commit -m "init expYYY"` で初期コピーを commit する。
11. `git status --branch --short` と `git log --oneline -n 1` でブランチ、commit、残差分を確認する。

## スコープ外の扱い

1. `plan-create` はこのスキルのスコープに含めない。
2. 初期 commit 後に設計書や実装計画が必要な場合は、ユーザーに別途依頼してもらう。
3. コンテキストクリアや新規スレッド開始はユーザー操作として扱い、このスキル内では実行しない。

## 停止して確認する条件

- ベース experiment が特定できない。
- `YYY`、`slug`、ブランチ名の確信度が80%未満。
- コピー先またはブランチ名が既に存在する。
- 既存の未コミット変更と新規 experiment の差分を安全に分離できない。
- commit 前の検証で secret、巨大生成物、不要な一時ファイルが疑われる。

## 完了報告

最後に次だけを短く報告する。

- 作成した experiment ディレクトリ
- 作成して切り替えたブランチ名
- 初期 commit hash と message
- 残った未コミット変更の有無
