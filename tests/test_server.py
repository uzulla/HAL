import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.server import HALServer


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
