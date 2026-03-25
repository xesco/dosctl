"""Tests for the --version flag on the CLI."""
from click.testing import CliRunner
from dosctl.main import cli
import dosctl


class TestVersionCommand:
    def test_shows_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert dosctl.__version__ in result.output

    def test_output_contains_dosctl_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert "DOSCtl" in result.output
