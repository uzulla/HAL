import os
import sys
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.main import main


def test_main_function():
    """HALメイン関数のテスト"""
    runner = CliRunner()
    
    with patch("src.hal.main.uvicorn.run") as mock_run:
        with patch("src.hal.main.HALServer") as mock_server:
            mock_server_instance = MagicMock()
            mock_server.return_value = mock_server_instance
            
            result = runner.invoke(main, ["--host", "127.0.0.1", "--port", "8000"])
            
            assert result.exit_code == 0
            
            mock_server.assert_called_once()
            
            mock_run.assert_called_once_with(
                mock_server_instance.app, 
                host="127.0.0.1", 
                port=8000
            )


def test_main_verbose_mode():
    """HALメイン関数のverboseモードテスト"""
    runner = CliRunner()
    
    with patch("src.hal.main.uvicorn.run"):
        with patch("src.hal.main.HALServer") as mock_server:
            with patch("src.hal.main.logger") as mock_logger:
                result = runner.invoke(main, ["--verbose"])
                
                assert result.exit_code == 0
                
                mock_logger.add.assert_called()
                
                mock_server.assert_called_once_with(verbose=True, fix_reply=None)


def test_main_daemon_mode():
    """HALメイン関数のデーモンモードテスト"""
    runner = CliRunner()
    
    with patch("src.hal.main.uvicorn.run"):
        with patch("src.hal.main.HALServer") as mock_server:
            result = runner.invoke(main, ["--fix-reply-daemon", "固定応答"])
            
            assert result.exit_code == 0
            
            mock_server.assert_called_once_with(verbose=False, fix_reply="固定応答")
