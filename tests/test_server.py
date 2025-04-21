import os
import sys
import pytest
from unittest.mock import patch

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.server import HALServer, authenticate, ChatCompletionRequest


def test_server_initialization():
    """サーバー初期化のテスト"""
    server = HALServer()
    assert not server.daemon_mode
    assert server.fix_reply is None
    
    server_daemon = HALServer(fix_reply="これは固定応答です。")
    assert server_daemon.daemon_mode
    assert server_daemon.fix_reply == "これは固定応答です。"

def test_server_routes():
    """サーバールートの設定テスト"""
    server = HALServer()
    
    routes = [route.path for route in server.app.routes]
    assert "/v1/chat/completions" in routes
    assert "/api/you" in routes

def test_daemon_mode_config():
    """デーモンモード設定のテスト"""
    # 固定応答モードでサーバーを初期化
    test_reply = "これは固定応答です。"
    server = HALServer(fix_reply=test_reply)
    
    assert server.daemon_mode
    assert server.fix_reply == test_reply

def test_authenticate():
    """認証関数のテスト（スタブ実装なので常にTrueを返す）"""
    assert authenticate("Bearer test-token") is True
    
    assert authenticate(None) is True


def test_server_shutdown_daemon():
    """デーモン終了機能のテスト"""
    server = HALServer(fix_reply="テスト応答")
    assert server.daemon_mode is True
    
    server_normal = HALServer()
    assert server_normal.daemon_mode is False


@pytest.mark.asyncio
async def test_shutdown_method():
    """_shutdown非同期メソッドのテスト"""
    server = HALServer()
    
    with patch("sys.exit") as mock_exit:
        with patch("asyncio.sleep") as mock_sleep:
            await server._shutdown()
            mock_sleep.assert_called_once_with(1)
            mock_exit.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_chat_completions_busy():
    """リクエスト処理中の排他制御テスト"""
    server = HALServer()
    
    with patch("src.hal.server.request_lock") as mock_lock:
        mock_lock.acquire.return_value = False
        
        request = ChatCompletionRequest(
            model="gpt-4", 
            messages=[{"role": "user", "content": "こんにちは"}]
        )
        
        routes = server.app.routes
        chat_route = [r for r in routes if r.path == "/v1/chat/completions"][0]
        
        with patch("src.hal.server.authenticate", return_value=True):
            response = await chat_route.endpoint(request)
            
            assert response.status_code == 503
            assert response.body.decode("utf-8") == '{"error":"server_busy"}'
