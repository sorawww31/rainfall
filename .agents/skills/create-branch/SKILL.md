---
name: create-branch
description: 現在の Git リポジトリで新しいブランチを安全に作成して切り替える。ユーザーが「新しいブランチ作って」「branch切って」「この作業用ブランチを作成」「featureブランチを作って」などを依頼したとき、または作業開始前に現在地点から専用ブランチへ移りたいときに使う。
---

# Create Branch

<!--
.agents/skills/create-branch/SKILL.md
Where: project-local Codex skill.
What: Workflow for creating and switching to a new Git branch.
Why: Avoid losing local changes or creating branches from the wrong start point.
-->

## 概要

現在の Git 状態を確認し、指定または推定した名前で新しいブランチを作る。
未コミット変更は破棄せず、新ブランチへそのまま持ち越すことを基本にする。

## ワークフロー

1. `git status --branch --short` で現在ブランチ、dirty 状態、ahead/behind を確認する。
2. `git branch --show-current` で detached HEAD ではないか確認する。detached HEAD の場合は、開始点をユーザーに確認する。
3. ブランチ名を決める。
   - ユーザー指定があれば、その名前を優先する。
   - 未指定なら依頼内容から短い kebab-case 名を推定する。例: `skill/commit-changes`、`fix/notion-score`。
   - 確信度が80%未満なら作成前に確認する。
4. `git branch --list <branch-name>` で既存ブランチ名と衝突しないか確認する。存在する場合は作成せず、切り替えるか別名にするか確認する。
5. 開始点を決める。
   - 指定がなければ現在の `HEAD` から作成する。
   - base ブランチや commit が指定された場合は、`git rev-parse --verify <start-point>` などで存在確認する。
6. `git switch -c <branch-name>` または `git switch -c <branch-name> <start-point>` を実行する。
7. 作成後に `git status --branch --short` を再実行し、現在ブランチと未コミット変更が保持されていることを確認する。

## 禁止または確認が必要な操作

- `git switch -C`、`git branch -f`、`git reset` など既存参照を上書きする操作は、ユーザーが明示した場合だけ行う。
- `--discard-changes`、`git checkout -f`、stash の drop などローカル変更を失う可能性がある操作は、必ず事前確認する。
- remote fetch/pull が必要な場合は、ネットワークアクセスや基準ブランチの更新が目的に含まれるか確認する。
- 既に同名ブランチがある場合、自動で別名を作らず候補名を提示する。

## ブランチ名の目安

- `feature/<topic>`: 新機能やスキル追加。
- `fix/<topic>`: バグ修正。
- `docs/<topic>`: docs だけの変更。
- `experiment/<topic>`: 試験的な作業。

既存リポジトリに命名規約がある場合は、それを優先する。迷う場合は `git branch --list` と `git log --oneline -n 20` から近い慣習を確認する。

## 完了報告

最後に次だけを短く報告する。

- 作成して切り替えたブランチ名
- 開始点のブランチまたは commit
- 未コミット変更を持ち越したかどうか
- 追加で必要な push や upstream 設定があるか
