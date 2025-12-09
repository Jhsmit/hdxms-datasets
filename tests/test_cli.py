"""Tests for the CLI module."""

from typer.testing import CliRunner

from hdxms_datasets.__main__ import app, generate_template_script, DataFormat


runner = CliRunner()


def test_generate_template_single_state():
    """Test template generation for single state."""
    script = generate_template_script(
        dataset_id="HDX_TEST1234",
        data_format=DataFormat.dynamx_v3_state,
        num_states=1,
        ph=7.5,
        temperature=293.15,
    )

    assert "HDX_TEST1234" in script
    assert "DynamX_v3_state" in script
    assert "State_1" in script
    assert "pH=7.5" in script
    assert "temperature=293.15" in script


def test_generate_template_multiple_states():
    """Test template generation for multiple states."""
    script = generate_template_script(
        dataset_id="HDX_TEST5678",
        data_format=DataFormat.hdexaminer,
        num_states=3,
        ph=8.0,
        temperature=298.15,
    )

    assert "HDX_TEST5678" in script
    assert "HDExaminer" in script
    assert "State_1" in script
    assert "State_2" in script
    assert "State_3" in script
    assert "pH=8.0" in script
    assert "temperature=298.15" in script


def test_cli_create_help():
    """Test that help message works."""
    result = runner.invoke(app, ["create", "--help"], color=False)
    assert result.exit_code == 0
    assert "Create a new HDX-MS dataset" in result.stdout
    assert "--num-states" in result.stdout
    assert "--format" in result.stdout
    assert "--ph" in result.stdout
    assert "--temperature" in result.stdout


def test_app_help():
    """Test main app help."""
    result = runner.invoke(app, ["--help"], color=False)
    assert result.exit_code == 0
    assert "hdxms-datasets" in result.stdout
