import json
from loguru import logger
from typing import Dict, Any

def format_json_response(data: Dict[str, Any], indent: int = 2) -> str:
    """JSON応答を整形して返す"""
    return json.dumps(data, indent=indent, ensure_ascii=False)

def setup_logging(verbose: bool = False):
    """ロギングの設定"""
    import sys
    
    logger.remove()  # デフォルトハンドラを削除
    
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    return logger
