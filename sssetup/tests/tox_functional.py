"""
    These test should only be ran by Tox with fresh virtualenvs for each invocation.
"""
from click.testing import CliRunner

from ..cli import status, link


class TestFunctional(object):
    """
        Order of methods matter!  We are assuming py.test will run in the order given in this
        class.
    """
    def test_status_before(self):
        runner = CliRunner()
        result = runner.invoke(status)
        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert lines.pop(0) == 'dbus package...needs linking into virtualenv'
        assert lines.pop(0) == 'Crypto package...needs linking into virtualenv'
        assert lines.pop(0) == 'secretstorage package...needs linking into virtualenv'

        # all output should be consumed
        assert not lines

    def test_status_verbose(self):
        runner = CliRunner()
        result = runner.invoke(status, ['-v'])
        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert lines[3] == 'Troubleshooting messages follow:'

    def test_link(self):
        runner = CliRunner()
        result = runner.invoke(link)
        assert result.exit_code == 0
        assert result.output == 'linking successful, run the status command to verify\n'

    def test_status_after(self):
        runner = CliRunner()
        result = runner.invoke(status)
        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert lines.pop(0) == 'dbus package...ready'
        assert lines.pop(0) == 'Crypto package...ready'
        assert lines.pop(0) == 'secretstorage package...ready'

        # all output should be consumed
        assert not lines
