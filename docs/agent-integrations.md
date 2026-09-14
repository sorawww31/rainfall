<!--
docs/agent-integrations.md
Where: project documentation.
What: Explains shared AI-agent instructions, skills, commands, and MCP settings.
Why: Help contributors keep Codex, Cursor, Claude Code, GitHub Copilot, and Gemini aligned.
-->

# AI Agent Integrations

このリポジトリでは、AIエージェント向けの指示・skill・commandを共通ソースから生成します。

## 共通ソース

- `AGENTS.md`: 全エージェントの共通作業方針。
- `.agents/skills/*/SKILL.md`: 共通 Agent Skills。
- `.agents/commands/*.md`: 共通 command prompt。
- `tools/sync_agent_assets.py`: 各ツールのネイティブ配置へ同期するスクリプト。

同期:

```sh
uv run python tools/sync_agent_assets.py
```

通常同期は必要な生成物を作成・更新します。`.agents/` から削除したskillやcommandに対応する生成物も削除したい場合は、厳密同期します。

```sh
uv run python tools/sync_agent_assets.py --prune
```

検証:

```sh
uv run python tools/sync_agent_assets.py --check
uv run python tools/sync_agent_assets.py --check --prune
uv run pytest tests/test_agent_assets.py
```

## MCP設定

`KAGGLE_API_TOKEN` を環境変数として設定してください。トークン値は設定ファイルに直接書かないでください。

| Tool | File | Notes |
| --- | --- | --- |
| Claude Code | `.mcp.json` | Project-scoped MCP設定。 |
| Codex | `.codex/config.toml` | Kaggle MCPを `bearer_token_env_var` で参照。 |
| Cursor | `.cursor/mcp.json` | `${env:KAGGLE_API_TOKEN}` を参照。 |
| GitHub Copilot in VS Code | `.vscode/mcp.json` | VS Code input promptでトークンを受け取る。 |
| Gemini CLI | `.gemini/settings.json` | `httpUrl` と `headers` でKaggle MCPを参照。 |

GitHub Copilot CLIのユーザー単位MCPは `~/.copilot/mcp-config.json` です。これは個人環境の設定なので、このリポジトリにはコミットしません。

## Commands

共通commandは `.agents/commands/*.md` に書きます。同期すると次に展開されます。

| Tool | Generated path |
| --- | --- |
| Claude Code | `.claude/commands/*.md` |
| Cursor | `.cursor/commands/*.md` |
| GitHub Copilot | `.github/prompts/*.prompt.md` |
| Gemini CLI | `.gemini/commands/*.toml` |

Codex CLIについては、公式ドキュメント上でプロジェクトローカルのcustom slash commandファイルが確認できませんでした。そのため、Codexでは `.agents/commands` を共通ソースとして参照するか、`shared-agent-commands` skillを使って同じpromptを実行します。

## Skills

共通skillは `.agents/skills` を正とします。Codex/Cursor/GitHub Copilot/Geminiはこの共有ディレクトリを使い、Claude Code向けには `.claude/skills` に同期します。
