import json
import time
from typing import Any, Dict, Optional

from loguru import logger


def format_json_response(data: Dict[str, Any], indent: int = 2) -> str:
    """JSON応答を整形して返す"""
    return json.dumps(data, indent=indent, ensure_ascii=False)

def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """ロギングの設定"""
    import sys
    
    logger.remove()  # デフォルトハンドラを削除
    
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    if log_file:
        logger.add(log_file, level="DEBUG" if verbose else "INFO", rotation=None, mode="a")
    
    return logger


def dump_json_to_file(file_path: str, data: Dict[str, Any], is_request: bool = True) -> None:
    """JSONデータをndjson形式でファイルに追記する
    
    Args:
        file_path: 出力先ファイルパス
        data: ダンプするJSONデータ
        is_request: リクエストであればTrue、レスポンスであればFalse
    """
    with open(file_path, "a", encoding="utf-8") as f:
        dump_data = {
            "type": "request" if is_request else "response", 
            "data": data, 
            "timestamp": int(time.time())
        }
        f.write(json.dumps(dump_data, ensure_ascii=False) + "\n")
