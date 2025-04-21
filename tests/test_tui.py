import asyncio
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.tui import TUIApp, process_request


def test_tui_app_initialization():
    """TUIアプリ初期化のテスト"""
    request_data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "あなたは役立つアシスタントです。"},
            {"role": "user", "content": "こんにちは"}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    app = TUIApp(request_data)
    
    assert app.request_data == request_data
    assert app.verbose is False
    assert app.response_data is None
    assert isinstance(app.response_ready, asyncio.Event)
    assert app.response_ready.is_set() is False


def test_tui_app_verbose_mode():
    """verboseモードでのTUIアプリ初期化のテスト"""
    request_data = {"model": "gpt-4", "messages": []}
    
    app = TUIApp(request_data, verbose=True)
    assert app.verbose is True


@pytest.mark.asyncio
async def test_process_request():
    """process_request関数のテスト"""
    request_data = MagicMock()
    request_data.dict.return_value = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "テストメッセージ"}]
    }
    
    mock_app = MagicMock()
    mock_app.response_data = {"content": "応答テスト"}
    mock_app.response_ready = asyncio.Event()
    
    mock_app.response_ready.set()
    
    with patch("src.hal.tui.TUIApp", return_value=mock_app):
        with patch.object(mock_app, "run_async"):
            result = await process_request(request_data)
            
            assert result == {"content": "応答テスト"}
