import signal
import sys

import click
import uvicorn
from loguru import logger

from .server import HALServer


def signal_handler(sig, frame):
    logger.info("終了シグナルを受信しました。HALを終了します...")
    sys.exit(0)


@click.command()
@click.option("--host", default="127.0.0.1", help="ホストアドレス")
@click.option("--port", default=8000, help="ポート番号")
@click.option("-v", "--verbose", is_flag=True, help="詳細なログ出力モード")
@click.option("--fix-reply-daemon", help="固定返答を返すデーモンモード")
@click.option("--log", help="ログを出力するファイルパス")
def main(host, port, verbose, fix_reply_daemon, log):
    """HAL - Humans Are Listening - CLI/TUIアプリケーション"""
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    from .utils import setup_logging
    
    setup_logging(verbose=verbose, log_file=log)
    
    logger.info("HALを起動します")
    
    server = HALServer(verbose=verbose, fix_reply=fix_reply_daemon)
    
    mode = "デーモンモード" if fix_reply_daemon else "通常モード"
    logger.info(f"HALサーバーを起動します({mode}) - {host}:{port}")
    
    try:
        uvicorn.run(server.app, host=host, port=port, timeout_graceful_shutdown=10)
    except KeyboardInterrupt:
        logger.info("キーボード割り込みを検出しました。HALを終了します...")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
    finally:
        logger.info("HALを終了します")

if __name__ == "__main__":
    main()
