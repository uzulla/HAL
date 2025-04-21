import click
import requests
import json
import sys
from typing import List, Dict, Any
from loguru import logger
import os

@click.group()
@click.option("-v", "--verbose", is_flag=True, help="詳細なログ出力")
@click.option("--host", default="127.0.0.1", help="HALサーバーのホスト")
@click.option("--port", default=8000, help="HALサーバーのポート")
@click.pass_context
def cli(ctx, verbose, host, port):
    """HALテストクライアント - API呼び出しテスト用"""
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose
    ctx.obj["HOST"] = host
    ctx.obj["PORT"] = port
    
    logger.remove()
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")

@cli.command()
@click.option("--model", default="gpt-4", help="使用するモデル")
@click.option("--system", default="あなたは役立つアシスタントです。", help="システムプロンプト")
@click.option("--user", required=True, help="ユーザーメッセージ (必須)")
@click.option("--max-tokens", default=1000, help="最大トークン数")
@click.option("--temperature", default=0.7, help="温度パラメータ")
@click.pass_context
def send(ctx, model, system, user, max_tokens, temperature):
    """メッセージをHALに送信する (--user オプションが必須)"""
    host = ctx.obj["HOST"]
    port = ctx.obj["PORT"]
    verbose = ctx.obj["VERBOSE"]
    
    url = f"http://{host}:{port}/v1/chat/completions"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer fake-token"
    }
    
    if verbose:
        logger.info(f"リクエスト: {url}")
        logger.info(f"ペイロード: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if verbose:
            logger.info(f"ステータスコード: {response.status_code}")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(f"応答: {response.text}")
    
    except Exception as e:
        logger.error(f"エラー発生: {e}")
        sys.exit(1)

@cli.command()
@click.option("--kill", is_flag=True, help="既存のデーモンを終了する")
@click.pass_context
def daemon(ctx, kill):
    """デーモンの終了 (--kill オプションで実行中のデーモンを終了)"""
    host = ctx.obj["HOST"]
    port = ctx.obj["PORT"]
    
    if kill:
        url = f"http://{host}:{port}/api/you"
        try:
            response = requests.delete(url)
            print(f"デーモン終了リクエスト: {response.status_code}")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"エラー発生: {e}")
            sys.exit(1)
    else:
        print("デーモンの終了方法:")
        print(f"bin/chat-client daemon --kill")
        print("\nデーモンの起動方法:")
        print(f"bin/hal --fix-reply-daemon=\"固定返答メッセージ\"")

if __name__ == "__main__":
    cli(obj={})
