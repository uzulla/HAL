import io
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hal.utils import format_json_response, setup_logging


def test_format_json_response():
    """JSON応答整形関数のテスト"""
    test_data = {
        "name": "HAL",
        "message": "こんにちは、世界",
        "nested": {
            "key": "value"
        }
    }
    
    formatted = format_json_response(test_data)
    parsed = json.loads(formatted)
    
    assert parsed["name"] == "HAL"
    assert parsed["message"] == "こんにちは、世界"
    assert parsed["nested"]["key"] == "value"
    
    formatted_custom = format_json_response(test_data, indent=4)
    assert "    " in formatted_custom  # 4スペースのインデントを確認


def test_setup_logging():
    """ロギング設定関数のテスト"""
    with patch("sys.stderr", new_callable=io.StringIO):
        logger = setup_logging(verbose=False)
        assert logger is not None
        
        logger = setup_logging(verbose=True)
        assert logger is not None
