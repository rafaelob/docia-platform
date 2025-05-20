"""Unit tests for orchestration configuration loading."""

from pathlib import Path
from unittest.mock import patch, mock_open
import pytest
import yaml

from medflowai.core.orchestration_config import (
    OrchestrationConfig,
    OrchestrationStep,
    load_orchestration_config,
    DEFAULT_ORCHESTRATION_ID,
)


def test_orchestration_step_validation():
    """Test validation of OrchestrationStep model."""
    # Valid step
    step = OrchestrationStep(
        type="agent",
        name="medflowai.agents.TriageAgent",
        on_error="retry",
    )
    assert step.type == "agent"
    assert step.name == "medflowai.agents.TriageAgent"
    assert step.on_error == "retry"

    # Invalid step type
    with pytest.raises(ValueError, match="Input should be 'agent', 'tool' or 'parallel'"):
        OrchestrationStep(type="invalid", name="test")

    # Invalid on_error
    with pytest.raises(ValueError, match="Input should be 'retry', 'skip' or 'abort'"):
        OrchestrationStep(type="agent", name="test", on_error="crash")


def test_orchestration_config_validation():
    """Test validation of OrchestrationConfig model."""
    # Valid config
    config = OrchestrationConfig(
        id="test-flow",
        description="Test flow",
        flow=[
            {"type": "agent", "name": "TestAgent", "on_error": "retry"},
        ],
        version="1.0.0",
    )
    assert config.id == "test-flow"
    assert len(config.flow) == 1
    assert config.version == "1.0.0"

    # Empty flow
    with pytest.raises(ValueError, match="`flow` must contain at least one step"):
        OrchestrationConfig(
            id="empty-flow",
            description="Empty flow",
            flow=[],
        )

    # Invalid ID format
    with pytest.raises(ValueError, match=r"String should match pattern"):
        OrchestrationConfig(
            id="Invalid Flow Name!",
            description="Invalid ID",
            flow=[{"type": "agent", "name": "TestAgent"}],
        )


def test_load_orchestration_config(tmp_path, monkeypatch):
    """Test loading orchestration config from file."""
    # Create a test YAML file
    test_yaml = """
    id: test-flow
    description: Test flow
    version: 1.0.0
    flow:
      - type: agent
        name: TestAgent
        on_error: retry
    env:
      - TEST_VAR
    """
    
    # Mock environment with required var
    monkeypatch.setenv("TEST_VAR", "test_value")
    
    # Test loading from file
    test_file = tmp_path / "test_flow.yaml"
    test_file.write_text(test_yaml)
    
    with patch("medflowai.core.orchestration_config.CONFIG_ROOT", tmp_path):
        config = load_orchestration_config("test_flow")
    
    assert config.id == "test-flow"
    assert len(config.flow) == 1
    assert config.flow[0].name == "TestAgent"


def test_load_orchestration_config_missing_env(monkeypatch, tmp_path):
    """Test loading config with missing environment variables."""
    test_yaml = """
    id: test-env
    description: Test env vars
    flow: [{type: agent, name: TestAgent}]
    env: [MISSING_VAR]
    """
    
    test_file = tmp_path / "test_env.yaml"
    test_file.write_text(test_yaml)
    
    with (
        patch("medflowai.core.orchestration_config.CONFIG_ROOT", tmp_path),
        pytest.raises(
            OSError,
            match=r"Missing required environment variables for orchestration 'test_env': MISSING_VAR"
        ),
    ):
        load_orchestration_config("test_env")


def test_default_orchestration_loads(tmp_path):
    """Test that the default orchestration file exists and is valid."""
    # Create a test default config
    test_yaml = """
    id: test-default
    description: Test default config
    flow: [{type: agent, name: TestAgent}]
    """
    
    test_file = tmp_path / f"{DEFAULT_ORCHESTRATION_ID}.yaml"
    test_file.write_text(test_yaml)
    
    with patch("medflowai.core.orchestration_config.CONFIG_ROOT", tmp_path):
        config = load_orchestration_config(DEFAULT_ORCHESTRATION_ID)
        assert config.id == "test-default"
        assert len(config.flow) > 0


def test_parallel_flow_validation():
    """Test validation of parallel flow steps."""
    config = OrchestrationConfig(
        id="parallel-test",
        description="Test parallel flow",
        flow=[
            {
                "type": "parallel",
                "agents": [
                    {"type": "agent", "name": "medflowai.agents.Agent1", "on_error": "skip"},
                    {"type": "agent", "name": "medflowai.agents.Agent2", "on_error": "skip"},
                ]
            }
        ]
    )
    assert config.flow[0].type == "parallel"
    assert len(config.flow[0].agents or []) == 2
    assert config.flow[0].agents[0].name == "medflowai.agents.Agent1"
    assert config.flow[0].agents[1].name == "medflowai.agents.Agent2"


def test_parallel_flow_validation_errors():
    """Test validation errors in parallel flow steps."""
    # Missing agents list
    with pytest.raises(ValueError, match=r"'agents' list is required for parallel steps"):
        OrchestrationConfig(
            id="parallel-test-invalid",
            description="Invalid parallel flow",
            flow=[{"type": "parallel"}],
        )
    
    # Invalid agent type in parallel step - Pydantic will raise a ValidationError
    with pytest.raises(ValueError, match=r"Value error, 'agents' list is required for parallel steps"):
        OrchestrationConfig(
            id="parallel-test-invalid-agent",
            description="Invalid agent in parallel flow",
            flow=[
                {
                    "type": "parallel",
                    "agents": [
                        {"type": "parallel"}  # Nested parallel not allowed
                    ]
                }
            ],
        )
