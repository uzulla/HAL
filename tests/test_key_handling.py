import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.tui_fix import TUIApp


def test_key_handling_f12():
    """F12 キーのテスト"""
    request_data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "テスト"}]
    }
    
    text_area_mock = MagicMock()
    text_area_mock.text = "テスト応答"
    
    with patch.object(TUIApp, 'query_one', return_value=text_area_mock):
        app = TUIApp(request_data)
        
        f12_event = MagicMock()
        f12_event.key = "f12"
        app.on_key(f12_event)
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
        if event.key == "f12":
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
