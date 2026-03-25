"""Subagent registry for managing available subagents."""

import logging
from dataclasses import replace

from deerflow.subagents.builtins import BUILTIN_SUBAGENTS
from deerflow.subagents.config import SubagentConfig

logger = logging.getLogger(__name__)


def _load_custom_agent_as_subagent(name: str) -> SubagentConfig | None:
    """Try to load a custom agent (from ~/.deer-flow/agents/) as a subagent config.

    Args:
        name: The custom agent name.

    Returns:
        SubagentConfig if found, None otherwise.
    """
    try:
        from deerflow.config.agents_config import load_agent_config, load_agent_soul

        agent_config = load_agent_config(name)
    except (FileNotFoundError, ValueError):
        return None

    if agent_config is None:
        return None

    soul = load_agent_soul(name) or f"You are {agent_config.name}. {agent_config.description}"

    config = SubagentConfig(
        name=agent_config.name,
        description=agent_config.description or f"Custom agent: {agent_config.name}",
        system_prompt=soul,
        tools=None,
        disallowed_tools=["task", "ask_clarification", "present_files"],
        model=agent_config.model or "inherit",
        tool_groups=agent_config.tool_groups,
    )

    # Apply timeout override from config.yaml (same as built-in subagents)
    from deerflow.config.subagents_config import get_subagents_app_config

    app_config = get_subagents_app_config()
    effective_timeout = app_config.get_timeout_for(name)
    if effective_timeout != config.timeout_seconds:
        config = replace(config, timeout_seconds=effective_timeout)

    return config


def _list_custom_subagents() -> list[SubagentConfig]:
    """List all custom agents that can serve as subagents.

    Returns:
        List of SubagentConfig instances derived from custom agents.
    """
    try:
        from deerflow.config.agents_config import list_custom_agents

        configs = []
        for agent in list_custom_agents():
            sc = _load_custom_agent_as_subagent(agent.name)
            if sc is not None:
                configs.append(sc)
        return configs
    except Exception as e:
        logger.warning(f"Failed to list custom agents as subagents: {e}")
        return []


def get_subagent_config(name: str) -> SubagentConfig | None:
    """Get a subagent configuration by name, with config.yaml overrides applied.

    Looks up built-in subagents first, then falls back to custom agents
    defined in ~/.deer-flow/agents/.

    Args:
        name: The name of the subagent.

    Returns:
        SubagentConfig if found (with any config.yaml overrides applied), None otherwise.
    """
    config = BUILTIN_SUBAGENTS.get(name)
    if config is None:
        # Fall back to custom agent
        return _load_custom_agent_as_subagent(name)

    # Apply timeout override from config.yaml (lazy import to avoid circular deps)
    from deerflow.config.subagents_config import get_subagents_app_config

    app_config = get_subagents_app_config()
    effective_timeout = app_config.get_timeout_for(name)
    if effective_timeout != config.timeout_seconds:
        logger.debug(f"Subagent '{name}': timeout overridden by config.yaml ({config.timeout_seconds}s -> {effective_timeout}s)")
        config = replace(config, timeout_seconds=effective_timeout)

    return config


def list_subagents() -> list[SubagentConfig]:
    """List all available subagent configurations (built-in + custom agents).

    Returns:
        List of all registered SubagentConfig instances.
    """
    builtin = [get_subagent_config(name) for name in BUILTIN_SUBAGENTS]
    custom = _list_custom_subagents()
    return builtin + custom


def get_subagent_names() -> list[str]:
    """Get all available subagent names (built-in + custom agents).

    Returns:
        List of subagent names.
    """
    names = list(BUILTIN_SUBAGENTS.keys())
    names.extend(a.name for a in _list_custom_subagents())
    return names
