import os
import sys
from unittest.mock import MagicMock, patch

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
            with patch("src.hal.utils.setup_logging") as mock_setup_logging:
                result = runner.invoke(main, ["--verbose"])
                
                assert result.exit_code == 0
                
                mock_setup_logging.assert_called_once_with(verbose=True, log_file=None)
                
                mock_server.assert_called_once_with(verbose=True, fix_reply=None, json_dump_log=None)


def test_main_daemon_mode():
    """HALメイン関数のデーモンモードテスト"""
    runner = CliRunner()
    
    with patch("src.hal.main.uvicorn.run"):
        with patch("src.hal.main.HALServer") as mock_server:
            result = runner.invoke(main, ["--fix-reply-daemon", "固定応答"])
            
            assert result.exit_code == 0
            
            mock_server.assert_called_once_with(verbose=False, fix_reply="固定応答", json_dump_log=None)


def test_main_log_file_option():
    """HALメイン関数のログファイルオプションテスト"""
    runner = CliRunner()
    test_log_file = "test_main.log"
    
    if os.path.exists(test_log_file):
        os.unlink(test_log_file)
    
    try:
        with patch("src.hal.main.uvicorn.run"):
            with patch("src.hal.main.HALServer") as mock_server:
                with patch("src.hal.utils.setup_logging") as mock_setup_logging:
                    result = runner.invoke(main, ["--log", test_log_file])
                    
                    assert result.exit_code == 0
                    
                    mock_setup_logging.assert_called_once_with(
                        verbose=False, log_file=test_log_file
                    )
                    mock_server.assert_called_once_with(
                        verbose=False, 
                        fix_reply=None, 
                        json_dump_log=None
                    )
    
    finally:
        if os.path.exists(test_log_file):
            os.unlink(test_log_file)


def test_main_json_dump_log_option():
    """HALメイン関数のJSONダンプログオプションテスト"""
    runner = CliRunner()
    test_json_dump_log_file = "test_json_dump.ndjson"
    
    if os.path.exists(test_json_dump_log_file):
        os.unlink(test_json_dump_log_file)
    
    try:
        with patch("src.hal.main.uvicorn.run"):
            with patch("src.hal.main.HALServer") as mock_server:
                with patch("src.hal.utils.setup_logging") as mock_setup_logging:
                    result = runner.invoke(main, ["--json-dump-log", test_json_dump_log_file])
                    
                    assert result.exit_code == 0
                    
                    mock_setup_logging.assert_called_once_with(
                        verbose=False, log_file=None
                    )
                    mock_server.assert_called_once_with(
                        verbose=False, fix_reply=None, json_dump_log=test_json_dump_log_file
                    )
    
    finally:
        if os.path.exists(test_json_dump_log_file):
            os.unlink(test_json_dump_log_file)
