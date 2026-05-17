"""
Loads company/team configuration from company_config.md.
Reads YAML frontmatter between the first two --- delimiters.
"""

import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent / "company_config.md"


@lru_cache(maxsize=1)
def load_company_config() -> dict[str, Any]:
    """Parse YAML frontmatter from company_config.md and return as dict."""
    try:
        text = _CONFIG_PATH.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if not match:
            logger.warning("No YAML frontmatter found in company_config.md — using defaults")
            return _defaults()
        return yaml.safe_load(match.group(1)) or _defaults()
    except FileNotFoundError:
        logger.warning("company_config.md not found — using defaults")
        return _defaults()
    except yaml.YAMLError as exc:
        logger.error(f"Failed to parse company_config.md frontmatter: {exc}")
        return _defaults()


def get_team_stack() -> str:
    return load_company_config().get("team_stack", "TypeScript, Playwright, React, Node.js")


def get_company_name() -> str:
    return load_company_config().get("company_name", "TechOnboard Demo")


def get_app_description() -> str:
    cfg = load_company_config()
    return str(cfg.get("app_description", "")).strip()


def get_tools_summary() -> str:
    tools: dict = load_company_config().get("tools", {})
    parts = []
    for category, items in tools.items():
        parts.append(f"{category}: {', '.join(items)}")
    return " | ".join(parts)


def get_learning_sequence() -> list[str]:
    return load_company_config().get("learning_sequence", [])


def get_first_ticket(seniority: str) -> str:
    tickets: dict = load_company_config().get("first_ticket", {})
    return tickets.get(seniority, tickets.get("junior", "First ticket assigned by the manager."))


def get_access_rules(seniority: str) -> dict:
    rules: dict = load_company_config().get("access_rules", {})
    return rules.get(seniority, {})


def _defaults() -> dict[str, Any]:
    return {
        "company_name": "TechOnboard Demo",
        "app_name": "Demo App",
        "team_stack": "TypeScript, Playwright, React, Node.js, GitHub Actions",
        "tools": {
            "testing": ["Playwright", "TypeScript"],
            "ci_cd": ["GitHub Actions"],
            "project_management": ["Jira"],
            "version_control": ["GitHub"],
        },
        "learning_sequence": [
            "Local environment setup",
            "Run existing tests",
            "Understand the project structure",
            "First small PR",
        ],
    }
