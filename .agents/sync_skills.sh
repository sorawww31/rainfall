mkdir -p .claude/skills
mkdir -p .codex/skills
mkdir -p .gemini/skills
mkdir -p .cursor/skills
rsync -a --delete .agents/skills/ .claude/skills/
rsync -a --delete .agents/skills/ .codex/skills/
rsync -a --delete .agents/skills/ .gemini/skills/
rsync -a --delete .agents/skills/ .cursor/skills/