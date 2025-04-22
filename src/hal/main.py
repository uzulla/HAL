import click
import uvicorn
from loguru import logger

from .server import HALServer


@click.command()
@click.option("--host", default="127.0.0.1", help="ホストアドレス")
@click.option("--port", default=8000, help="ポート番号")
@click.option("-v", "--verbose", is_flag=True, help="詳細なログ出力モード")
@click.option("--fix-reply-daemon", help="固定返答を返すデーモンモード")
@click.option("--log", help="ログを出力するファイルパス")
@click.option("--json-dump-log", help="JSONボディをndjson形式で出力するファイル")
def main(host, port, verbose, fix_reply_daemon, log, json_dump_log):
    """HAL - Humans Are Listening - CLI/TUIアプリケーション"""
    
    from .utils import setup_logging
    
    setup_logging(verbose=verbose, log_file=log)
    
    logger.info("HALを起動します")
    
    server = HALServer(verbose=verbose, fix_reply=fix_reply_daemon, json_dump_log=json_dump_log)
    
    mode = "デーモンモード" if fix_reply_daemon else "通常モード"
    logger.info(f"HALサーバーを起動します({mode}) - {host}:{port}")
    
    if json_dump_log:
        logger.info(f"JSONダンプログを出力します: {json_dump_log}")
    
    uvicorn.run(server.app, host=host, port=port)

if __name__ == "__main__":
    main()
