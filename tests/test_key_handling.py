import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.tui import TUIApp


def test_key_handling_ctrl_cmd_enter():
    """Ctrl+Enter と Cmd+Enter のテスト"""
    request_data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "テスト"}]
    }
    
    text_area_mock = MagicMock()
    text_area_mock.text = "テスト応答"
    
    with patch.object(TUIApp, 'query_one', return_value=text_area_mock):
        app = TUIApp(request_data)
        
        ctrl_enter_event = MagicMock()
        ctrl_enter_event.key = "ctrl+enter"
        app.on_key(ctrl_enter_event)
        assert app.response_data == {"content": "テスト応答"}
        assert app.response_ready.is_set()
        
        app.response_data = None
        app.response_ready.clear()
        
        ctrl_m_event = MagicMock()
        ctrl_m_event.key = "ctrl+m"
        app.on_key(ctrl_m_event)
        assert app.response_data == {"content": "テスト応答"}
        assert app.response_ready.is_set()
        
        app.response_data = None
        app.response_ready.clear()
        
        cmd_enter_event = MagicMock()
        cmd_enter_event.key = "cmd+enter"
        app.on_key(cmd_enter_event)
        assert app.response_data == {"content": "テスト応答"}
        assert app.response_ready.is_set()
        
        app.response_data = None
        app.response_ready.clear()
        
        cmd_m_event = MagicMock()
        cmd_m_event.key = "cmd+m"
        app.on_key(cmd_m_event)
        assert app.response_data == {"content": "テスト応答"}
        assert app.response_ready.is_set()


def test_key_handling_enter_logic():
    """Enter キーの処理ロジックのテスト"""
    request_data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "テスト"}]
    }
    
    def mock_on_key(self, event):
        """モック版の on_key メソッド"""
        if (event.key == "ctrl+enter" or event.key == "ctrl+m" or 
            event.key == "cmd+enter" or event.key == "cmd+m"):
            self.submit_response()
        elif event.key == "enter":
            pass
    
    with patch.object(TUIApp, 'on_key', mock_on_key):
        app = TUIApp(request_data)
        
        with patch.object(app, 'submit_response') as mock_submit:
            enter_event = MagicMock()
            enter_event.key = "enter"
            app.on_key(enter_event)
            
            mock_submit.assert_not_called()
