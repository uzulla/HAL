import click
import uvicorn
from loguru import logger
import sys
from .server import HALServer

@click.command()
@click.option("--host", default="127.0.0.1", help="ホストアドレス")
@click.option("--port", default=8000, help="ポート番号")
@click.option("-v", "--verbose", is_flag=True, help="詳細なログ出力モード")
@click.option("--fix-reply-daemon", help="固定返答を返すデーモンモード")
def main(host, port, verbose, fix_reply_daemon):
    """HAL - Humans Are Listening - CLI/TUIアプリケーション"""
    
    logger.remove()
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")
    
    logger.info("HALを起動します")
    
    server = HALServer(verbose=verbose, fix_reply=fix_reply_daemon)
    
    mode = "デーモンモード" if fix_reply_daemon else "通常モード"
    logger.info(f"HALサーバーを起動します({mode}) - {host}:{port}")
    
    uvicorn.run(server.app, host=host, port=port)

if __name__ == "__main__":
    main()
