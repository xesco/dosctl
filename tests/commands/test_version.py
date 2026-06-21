"""Tests for the --version flag and the `version` subcommand on the CLI."""
from click.testing import CliRunner

import dosctl
from dosctl.main import cli


class TestVersionCommand:
    def test_shows_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert dosctl.__version__ in result.output

    def test_output_contains_dosctl_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert "dosctl" in result.output

    def test_version_subcommand_is_registered(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "dosctl" in result.output
        assert dosctl.__version__ in result.output
