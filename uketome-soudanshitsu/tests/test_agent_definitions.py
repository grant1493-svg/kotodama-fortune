from pathlib import Path

AGENTS_DIR = Path.home() / ".claude" / "agents"
EXPECTED_AGENTS = {
    "performance-analyst-soudan": {"Read", "Write", "Glob", "Bash"},
    "concept-planner-soudan": {"Read", "Write", "WebSearch"},
    "writer-soudan": {"Read", "Write"},
    "qa-reviewer-soudan": {"Read", "Write"},
}


def _parse_frontmatter(text: str) -> dict:
    assert text.startswith("---"), "frontmatter missing"
    end = text.index("---", 3)
    block = text[3:end].strip()
    result = {}
    for line in block.splitlines():
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip()
    return result


def test_all_four_agent_files_exist():
    for name in EXPECTED_AGENTS:
        assert (AGENTS_DIR / f"{name}.md").exists(), f"{name}.md not found"


def test_each_agent_frontmatter_has_required_fields():
    for name in EXPECTED_AGENTS:
        text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        assert meta["name"] == name
        assert meta["description"]
        assert meta["tools"]
        assert meta["model"] == "sonnet"


def test_each_agent_declares_expected_tools():
    for name, required_tools in EXPECTED_AGENTS.items():
        text = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8")
        meta = _parse_frontmatter(text)
        declared = {t.strip() for t in meta["tools"].split(",")}
        assert required_tools.issubset(declared), f"{name} missing tools {required_tools - declared}"
