import pytest
from fastapi.testclient import TestClient
import threading
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.server import HALServer

def test_daemon_mode():
    """デーモンモードのテスト"""
    server = HALServer(fix_reply="これは固定応答です。")
    client = TestClient(server.app)
    
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "あなたは役立つアシスタントです。"},
                {"role": "user", "content": "こんにちは"}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        },
        headers={"Authorization": "Bearer fake-token"}
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["choices"][0]["message"]["content"] == "これは固定応答です。"
    
    shutdown_response = client.delete("/api/you")
    assert shutdown_response.status_code == 200
    assert "shutting_down" in shutdown_response.json()["message"]

def test_error_responses():
    """エラー応答のテスト"""
    server = HALServer()
    client = TestClient(server.app)
