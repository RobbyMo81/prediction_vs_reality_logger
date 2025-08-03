
import pytest
from click.testing import CliRunner
from prediction_logger import cli

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli.main, ['--help'])
    assert result.exit_code == 0
    assert 'Usage' in result.output