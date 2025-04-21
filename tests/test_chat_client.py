import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from chat_client.main import cli, send, daemon


def test_cli_initialization():
    """CLIコマンドグループの初期化テスト"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    
    assert result.exit_code == 0
    assert "HALテストクライアント" in result.output


def test_cli_verbose_option():
    """verboseオプションのテスト"""
    runner = CliRunner()
    
    result = runner.invoke(cli, ["-v", "--help"], obj={})
    
    assert result.exit_code == 0
    assert "-v, --verbose" in result.output
    
    result_command = runner.invoke(cli, ["--help"], obj={})
    assert result_command.exit_code == 0


def test_send_command():
    """sendコマンドのテスト"""
    runner = CliRunner()
    
    with patch("src.chat_client.main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "こんにちは！"}}
            ]
        }
        mock_post.return_value = mock_response
        
        result = runner.invoke(cli, ["send", "--user", "こんにちは"], obj={})
        
        assert result.exit_code == 0
        
        mock_post.assert_called_once()
        
        args, kwargs = mock_post.call_args
        assert "http://" in args[0]
        assert kwargs["json"]["messages"][1]["content"] == "こんにちは"


def test_daemon_command():
    """daemonコマンドのテスト"""
    runner = CliRunner()
    
    result = runner.invoke(cli, ["daemon"], obj={})
    assert result.exit_code == 0
    assert "デーモンの終了方法" in result.output
    
    with patch("src.chat_client.main.requests.delete") as mock_delete:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "shutting_down"}
        mock_delete.return_value = mock_response
        
        result = runner.invoke(cli, ["daemon", "--kill"], obj={})
        
        assert result.exit_code == 0
        
        mock_delete.assert_called_once()
