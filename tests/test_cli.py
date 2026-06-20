"""
tests/test_cli.py — CLI integration tests for Morpheus.
"""

from __future__ import annotations


from typer.testing import CliRunner

from morpheus.cli import app

runner = CliRunner()


class TestRunCommand:
    def test_run_missing_file(self):
        result = runner.invoke(app, ["run", "/nonexistent/file.py"])
        assert result.exit_code != 0

    def test_run_invalid_mode(self):
        result = runner.invoke(
            app, ["run", "examples/simple.py", "--mode", "invalid"]
        )
        assert result.exit_code != 0
        assert "Invalid mode" in result.stdout

    def test_run_invalid_personality(self):
        result = runner.invoke(
            app, ["run", "examples/simple.py", "--personality", "invalid"]
        )
        assert result.exit_code != 0
        assert "Invalid personality" in result.stdout

    def test_run_narrator_mode(self, mocker):
        mock_client = mocker.patch("morpheus.cli.OllamaClient")
        mock_client.return_value.stream.return_value = ["mock token"]
        mock_client.return_value.generate.return_value = "mock narration"
        mock_client.return_value.provider_name = "mock"
        mock_client.return_value.model = "mock-model"

        result = runner.invoke(
            app, ["run", "examples/simple.py", "--mode", "narrator", "--no-store"]
        )
        assert result.exit_code == 0

    def test_run_prophecy_mode(self, mocker):
        mock_client = mocker.patch("morpheus.cli.OllamaClient")
        mock_client.return_value.stream.return_value = ["mock token"]
        mock_client.return_value.generate.return_value = "mock narration"
        mock_client.return_value.provider_name = "mock"
        mock_client.return_value.model = "mock-model"

        result = runner.invoke(
            app, ["run", "examples/simple.py", "--mode", "prophecy", "--no-store"]
        )
        assert result.exit_code == 0

    def test_run_teach_mode(self, mocker):
        mock_client = mocker.patch("morpheus.cli.OllamaClient")
        mock_client.return_value.stream.return_value = ["mock token"]
        mock_client.return_value.generate.return_value = "mock narration"
        mock_client.return_value.provider_name = "mock"
        mock_client.return_value.model = "mock-model"

        result = runner.invoke(
            app, ["run", "examples/simple.py", "--mode", "teach", "--no-store"],
            input="a\na\n"
        )
        assert result.exit_code == 0
        assert "Session Complete!" in result.stdout

    def test_run_oracle_mode(self, mocker):
        mock_client = mocker.patch("morpheus.cli.OllamaClient")
        mock_client.return_value.stream.return_value = ["mock token"]
        mock_client.return_value.generate.return_value = "mock narration"
        mock_client.return_value.provider_name = "mock"
        mock_client.return_value.model = "mock-model"

        result = runner.invoke(
            app, ["run", "examples/simple.py", "--mode", "oracle", "--no-store"]
        )
        assert result.exit_code == 0
        assert "Oracle Narration" in result.stdout


class TestSpyCommand:
    def test_spy_missing_file(self):
        result = runner.invoke(app, ["spy", "/nonexistent/file.py"])
        assert result.exit_code != 0


class TestMapCommand:
    def test_map_missing_file(self):
        result = runner.invoke(app, ["map", "/nonexistent/file.py"])
        assert result.exit_code != 0


class TestDiffCommand:
    def test_diff_invalid_ids(self):
        result = runner.invoke(app, ["diff", "id1", "id2"])
        # Should fail gracefully — no such runs in storage
        assert result.exit_code != 0


class TestAnalyzeCommand:
    def test_analyze_missing_run(self):
        result = runner.invoke(app, ["analyze", "nonexistent-id"])
        assert result.exit_code != 0
        assert "No run found" in result.stdout


class TestHelp:
    def test_help_shows_all_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        for cmd in ["run", "spy", "map", "diff", "analyze"]:
            assert cmd in result.stdout

    def test_run_help_shows_backend_flag(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--backend" in result.stdout
        assert "--model" in result.stdout
