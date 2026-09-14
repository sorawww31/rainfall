<!--
.agents/docs/templates/plan-template.md
Where: shared agent documentation template.
What: Template for implementation design documents aimed at AI coding agents.
Why: Keep plans concrete, verifiable, and safe before code changes begin.
-->

# <機能名または依頼名> 設計書

## 0. メタ情報

- 作成日: <YYYY-MM-DD>
- 作成者: <agent/user>
- 対象リポジトリ/ディレクトリ: `<path>`
- 依頼原文: `<user request>`
- 想定読者: 実装担当AIエージェント、レビュー担当者、人間のオーナー
- ステータス: draft / approved / implemented / obsolete

## 1. 目的

- 解決したい問題:
- 成功条件:
- ユーザーに見える成果物:
- 今回やらないこと:

## 2. 現状把握

- 関連ファイル:
- 既存の設計/慣習:
- 既存テスト:
- 既存ドキュメント:
- 外部API/ライブラリ:
- 未確認事項:

## 3. 要件

### 3.1 機能要件

- <何をできるようにするか>

### 3.2 非機能要件

- 安全性:
- 性能/コスト:
- 保守性:
- 監査性/ログ:
- 互換性:

### 3.3 制約

- 変更可能な範囲:
- 変更してはいけない範囲:
- 依存追加の可否:
- セキュリティ/秘密情報:

## 4. エージェント設計判断

Anthropic、OpenAI、Google ADK、Microsoft Foundry の公開ドキュメントに共通する方針に従い、まず単純な構成から始め、必要性が明確な場合だけ agentic な複雑性を足す。

### 4.1 workflow か agent か

- 選択: single LLM / prompt chain / routing / parallel / orchestrator-workers / evaluator-optimizer / autonomous agent
- 選択理由:
- 複雑性を増やす条件:
- 単純な代替案:

### 4.2 タスク分解

| Step | 目的 | 入力 | 出力 | 実行者 | 失敗時の扱い |
| --- | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |

### 4.3 コンテキスト設計

- 事前に読むべきファイル:
- 逐次読むファイル:
- コンテキストに入れない情報:
- 長大ログ/検索結果の扱い:
- 状態/session/memory の扱い:

### 4.4 ツール設計

| Tool | 使う目的 | 入力契約 | 出力契約 | 使うタイミング | ガードレール |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

- ツール選択ルール:
- 失敗時のフォールバック:
- ツール出力を信頼しすぎないための検証:

### 4.5 ガードレール

- 入力チェック:
- 出力チェック:
- tool call 前後のチェック:
- 副作用のある操作の承認条件:
- human-in-the-loop が必要な条件:

### 4.6 観測性

- ログ/trace に残す単位:
- 残してはいけない機密情報:
- デバッグに必要な中間成果物:
- 完了報告に含める項目:

## 5. 実装方針

- 最小変更の方針:
- 変更対象ファイル:
- 新規ファイル:
- 削除ファイル:
- config に寄せる値:
- 既存パターンとの整合:

## 6. 詳細設計

### 6.1 データ/API/関数契約

```text
入力:
出力:
エラー:
副作用:
```

### 6.2 処理フロー

```text
1.
2.
3.
```

### 6.3 エラー処理

- 想定エラー:
- ユーザーに確認する条件:
- 自動復旧できる条件:
- 中断する条件:

## 7. テスト計画

- 追加/更新するテスト:
- 正常系:
- 異常系:
- 回帰観点:
- 手動確認:
- 実行コマンド:

## 8. ドキュメント更新

- 更新するREADME/AGENTS/コマンド/設定:
- ユーザー向け変更点:
- 移行手順:

## 9. リスクと対策

| Risk | Impact | Probability | Mitigation | Owner |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## 10. 実装ステップ

1. <小さく戻せる単位の変更>
2. <テスト追加>
3. <実装>
4. <ドキュメント更新>
5. <検証>

## 11. 未解決事項

- <80% 未満の確信、曖昧な要件、API契約変更、セキュリティ判断など>

## 12. 参照した一次情報

- 確認日: 2026-04-26
- Anthropic: Building effective agents - https://www.anthropic.com/engineering/building-effective-agents
- Anthropic: Create custom subagents - https://code.claude.com/docs/en/sub-agents
- Anthropic: Writing effective tools for AI agents - https://www.anthropic.com/engineering/writing-tools-for-agents
- OpenAI: Agents SDK - https://openai.github.io/openai-agents-python/
- OpenAI: Agents SDK guardrails - https://openai.github.io/openai-agents-python/guardrails/
- OpenAI: Agents SDK tracing - https://openai.github.io/openai-agents-python/tracing/
- Google: Agent Development Kit multi-agent systems - https://adk.dev/agents/multi-agents/
- Microsoft: Foundry Agent Service tool best practices - https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/tool-best-practice?view=foundry

## 13. レビュー用チェックリスト

- [ ] 要件と非目標が明確
- [ ] 現状ファイルを読んだ根拠がある
- [ ] 外部API/ライブラリは現在の公式情報で確認済み
- [ ] 最小構成から始める設計になっている
- [ ] workflow と agent の選択理由が明確
- [ ] tool contract と失敗時の扱いが明確
- [ ] guardrail / human-in-the-loop / secret handling が明確
- [ ] trace/log/evaluation/test の方針が明確
- [ ] 実装ステップが小さく、戻しやすい
- [ ] 未解決事項が隠されていない
