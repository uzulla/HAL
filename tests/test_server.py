import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.server import (
    ChatCompletionRequest,
    HALServer,
    Message,
    MessageContentPart,
    authenticate,
)


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
        
        mock_raw_request = MagicMock()
        mock_raw_request.headers = {"Content-Type": "application/json"}
        mock_raw_request.body = AsyncMock(return_value=b'{}')
        
        with patch("src.hal.server.authenticate", return_value=True):
            response = await chat_route.endpoint(request, mock_raw_request)
            
            assert response.status_code == 503
            assert response.body.decode("utf-8") == '{"error":"server_busy"}'


@pytest.mark.asyncio
async def test_verbose_request_logging():
    """verboseモードでのHTTPリクエスト詳細ログのテスト"""
    server = HALServer(verbose=True)
    
    with patch("src.hal.server.logger") as mock_logger:
        with patch("src.hal.server.request_lock") as mock_lock:
            mock_lock.acquire.return_value = True
            
            request = ChatCompletionRequest(
                model="gpt-4", 
                messages=[{"role": "user", "content": "こんにちは"}]
            )
            
            mock_raw_request = MagicMock()
            mock_raw_request.headers = {"Content-Type": "application/json"}
            mock_raw_request.body = AsyncMock(return_value=b'{"test": "data"}')
            
            routes = server.app.routes
            chat_route = [r for r in routes if r.path == "/v1/chat/completions"][0]
            
            with patch("src.hal.server.authenticate", return_value=True):
                await chat_route.endpoint(request, mock_raw_request)
                
                headers_dict = dict(mock_raw_request.headers)
                mock_logger.debug.assert_any_call(f"HTTPリクエストヘッダー: {headers_dict}")
                mock_logger.debug.assert_any_call("HTTPリクエストボディ: {\"test\": \"data\"}")


def test_message_model_array_content():
    """配列形式のコンテンツを持つMessageモデルのテスト"""
    message = Message(
        role="user",
        content=[
            MessageContentPart(type="text", text="これはテストです"),
            MessageContentPart(type="text", text="配列形式のコンテンツ")
        ]
    )
    
    assert message.role == "user"
    assert isinstance(message.content, list)
    assert len(message.content) == 2
    assert message.content[0].type == "text"
    assert message.content[0].text == "これはテストです"
    assert message.content[1].type == "text"
    assert message.content[1].text == "配列形式のコンテンツ"
    
    message_str = Message(role="user", content="こんにちは")
    assert message_str.role == "user"
    assert message_str.content == "こんにちは"


@pytest.mark.asyncio
async def test_server_daemon_array_content():
    """デーモンモードでの配列形式コンテンツのテスト"""
    server = HALServer(verbose=True, fix_reply="テスト応答")
    
    request_data = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "これはテストです"},
                    {"type": "text", "text": "配列形式のコンテンツ"}
                ]
            }
        ]
    }
    
    request = ChatCompletionRequest(**request_data)
    
    with patch("src.hal.server.request_lock") as mock_lock:
        mock_lock.acquire.return_value = True
        
        with patch("src.hal.server.authenticate", return_value=True):
            routes = server.app.routes
            chat_route = [r for r in routes if r.path == "/v1/chat/completions"][0]
            
            mock_raw_request = MagicMock()
            mock_raw_request.headers = {"Content-Type": "application/json"}
            mock_raw_request.body = AsyncMock(return_value=b'{}')
            
            response = await chat_route.endpoint(request, mock_raw_request)
            
            assert response.model == "gpt-4"
            assert response.choices[0]["message"]["content"] == "テスト応答"


@pytest.mark.asyncio
async def test_json_dump_log():
    """JSONダンプログ機能のテスト"""
    import json
    import os
    
    test_json_dump_file = "test_json_dump.ndjson"
    
    if os.path.exists(test_json_dump_file):
        os.unlink(test_json_dump_file)
    
    try:
        server = HALServer(verbose=True, json_dump_log=test_json_dump_file)
        
        with patch("src.hal.server.request_lock") as mock_lock:
            mock_lock.acquire.return_value = True
            
            request = ChatCompletionRequest(
                model="gpt-4", 
                messages=[{"role": "user", "content": "こんにちは"}]
            )
            
            mock_raw_request = MagicMock()
            mock_raw_request.headers = {"Content-Type": "application/json"}
            request_body = {
                "model": "gpt-4", 
                "messages": [{"role": "user", "content": "こんにちは"}]
            }
            mock_raw_request.json = AsyncMock(return_value=request_body)
            mock_raw_request.body = AsyncMock(return_value=json.dumps(request_body).encode('utf-8'))
            
            routes = server.app.routes
            chat_route = [r for r in routes if r.path == "/v1/chat/completions"][0]
            
            with patch("src.hal.server.authenticate", return_value=True):
                with patch("src.hal.tui_fix.process_request") as mock_process:
                    mock_process.return_value = {"content": "こんにちは、お元気ですか？"}
                    
                    await chat_route.endpoint(request, mock_raw_request)
                    
                    assert os.path.exists(test_json_dump_file)
                    
                    with open(test_json_dump_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        assert len(lines) == 2  # リクエストとレスポンスの2行
                        
                        request_log = json.loads(lines[0])
                        response_log = json.loads(lines[1])
                        
                        assert request_log["type"] == "request"
                        assert request_log["data"]["model"] == "gpt-4"
                        assert request_log["data"]["messages"][0]["content"] == "こんにちは"
                        
                        assert response_log["type"] == "response"
                        assert response_log["data"]["role"] == "assistant"
                        assert response_log["data"]["content"] == "こんにちは、お元気ですか？"
    
    finally:
        if os.path.exists(test_json_dump_file):
            os.unlink(test_json_dump_file)
