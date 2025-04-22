import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

request_lock = threading.Lock()

class MessageContentPart(BaseModel):
    type: str
    text: str

class Message(BaseModel):
    role: str
    content: Union[str, List[MessageContentPart]]

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: int = 1000
    temperature: float = 0.7

class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:5]}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[Dict[str, Any]]

def authenticate(token: Optional[str] = Header(None, alias="Authorization")) -> bool:
    return True

class HALServer:
    def __init__(
        self, 
        verbose: bool = False, 
        fix_reply: Optional[str] = None, 
        json_dump_log: Optional[str] = None
    ):
        self.app = FastAPI()
        self.verbose = verbose
        self.fix_reply = fix_reply
        self.json_dump_log = json_dump_log
        self.setup_exception_handlers()
        self.setup_routes()
        self.daemon_mode = fix_reply is not None
        
        if verbose:
            logger.info("Verbose mode enabled")
        if self.daemon_mode:
            logger.info(f"デーモンモード有効 - 固定返答: {fix_reply}")
            
    def setup_exception_handlers(self):
        @self.app.exception_handler(StarletteHTTPException)
        async def http_exception_handler(request: Request, exc: StarletteHTTPException):
            if self.verbose:
                logger.warning(f"HTTPエラー: {exc.status_code} - {exc.detail}")
                logger.debug(f"リクエストURL: {request.url}")
                logger.debug(f"リクエストメソッド: {request.method}")
                logger.debug(f"リクエストヘッダー: {dict(request.headers)}")
                
                try:
                    body = await request.body()
                    if body:
                        logger.debug(f"リクエストボディ: {body.decode('utf-8', errors='replace')}")
                except Exception as e:
                    logger.debug(f"リクエストボディの取得に失敗: {e}")
            
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail}
            )
        
        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            if self.verbose:
                logger.warning(f"リクエスト検証エラー: {exc}")
                logger.debug(f"リクエストURL: {request.url}")
                logger.debug(f"リクエストメソッド: {request.method}")
                logger.debug(f"リクエストヘッダー: {dict(request.headers)}")
                
                try:
                    body = await request.body()
                    if body:
                        logger.debug(f"リクエストボディ: {body.decode('utf-8', errors='replace')}")
                except Exception as e:
                    logger.debug(f"リクエストボディの取得に失敗: {e}")
            
            return JSONResponse(
                status_code=422,
                content={"error": "validation_error", "detail": str(exc)}
            )
        
        @self.app.exception_handler(404)
        async def not_found_exception_handler(request: Request, exc: HTTPException):
            if self.verbose:
                logger.warning(f"未対応のURL: {request.url}")
                logger.debug(f"リクエストメソッド: {request.method}")
                logger.debug(f"リクエストヘッダー: {dict(request.headers)}")
                
                try:
                    body = await request.body()
                    if body:
                        logger.debug(f"リクエストボディ: {body.decode('utf-8', errors='replace')}")
                except Exception as e:
                    logger.debug(f"リクエストボディの取得に失敗: {e}")
            
            return JSONResponse(
                status_code=404,
                content={"error": "not_found", "detail": f"URL '{request.url}' not found"}
            )
        
        @self.app.exception_handler(405)
        async def method_not_allowed_exception_handler(request: Request, exc: HTTPException):
            if self.verbose:
                logger.warning(f"未対応のメソッド: {request.method} for URL {request.url}")
                logger.debug(f"リクエストヘッダー: {dict(request.headers)}")
                
                try:
                    body = await request.body()
                    if body:
                        logger.debug(f"リクエストボディ: {body.decode('utf-8', errors='replace')}")
                except Exception as e:
                    logger.debug(f"リクエストボディの取得に失敗: {e}")
            
            error_detail = f"Method '{request.method}' not allowed for URL '{request.url}'"
            return JSONResponse(
                status_code=405,
                content={"error": "method_not_allowed", "detail": error_detail}
            )

    def setup_routes(self):
        @self.app.post("/v1/chat/completions")
        async def chat_completions(
            request: ChatCompletionRequest,
            raw_request: Request,
            authenticated: bool = Depends(authenticate)
        ):
            if self.verbose:
                logger.info(f"リクエスト受信: {request}")
                logger.debug(f"HTTPリクエストヘッダー: {dict(raw_request.headers)}")
                body = await raw_request.body()
                if body:
                    logger.debug(f"HTTPリクエストボディ: {body.decode('utf-8', errors='replace')}")
                    if self.json_dump_log:
                        from .utils import dump_json_to_file
                        request_data = await raw_request.json()
                        dump_json_to_file(self.json_dump_log, request_data, is_request=True)
            
            if not request_lock.acquire(blocking=False):
                if self.verbose:
                    logger.warning("別のリクエストが処理中のため、このリクエストは拒否されました")
                return JSONResponse(
                    status_code=503,
                    content={"error": "server_busy"}
                )
            
            try:
                if self.daemon_mode:
                    if self.verbose:
                        logger.info(f"デーモンモードで固定返答を返します: {self.fix_reply}")
                    
                    return ChatCompletionResponse(
                        model=request.model,
                        choices=[{
                            "index": 0,
                            "message": {"role": "assistant", "content": self.fix_reply},
                            "finish_reason": "stop"
                        }]
                    )
                
                from .tui_fix import process_request
                result = await process_request(request)
                
                if self.verbose:
                    logger.info(f"応答結果: {result}")
                
                if self.json_dump_log and not result.get("error"):
                    from .utils import dump_json_to_file
                    response_data = {"role": "assistant", "content": result["content"]}
                    dump_json_to_file(self.json_dump_log, response_data, is_request=False)
                
                if result.get("error") == "cannot_answer":
                    if self.json_dump_log:
                        from .utils import dump_json_to_file
                        error_data = {"error": "cannot_answer"}
                        dump_json_to_file(self.json_dump_log, error_data, is_request=False)
                    return JSONResponse(
                        status_code=200,
                        content={"error": "cannot_answer"}
                    )
                elif result.get("error") == "internal_error":
                    if self.json_dump_log:
                        from .utils import dump_json_to_file
                        error_data = {"error": "internal_error"}
                        dump_json_to_file(self.json_dump_log, error_data, is_request=False)
                    return JSONResponse(
                        status_code=500,
                        content={"error": "internal_error"}
                    )
                elif result.get("error") == "forbidden":
                    if self.json_dump_log:
                        from .utils import dump_json_to_file
                        error_data = {"error": "forbidden"}
                        dump_json_to_file(self.json_dump_log, error_data, is_request=False)
                    return JSONResponse(
                        status_code=403,
                        content={"error": "forbidden"}
                    )
                
                return ChatCompletionResponse(
                    model=request.model,
                    choices=[{
                        "index": 0,
                        "message": {"role": "assistant", "content": result["content"]},
                        "finish_reason": "stop"
                    }]
                )
            
            finally:
                request_lock.release()
                if self.verbose:
                    logger.info("リクエスト処理完了、ロック解放")
        
        @self.app.delete("/api/you")
        async def shutdown_daemon():
            if not self.daemon_mode:
                return JSONResponse(
                    status_code=400,
                    content={"error": "not_in_daemon_mode"}
                )
            
            if self.verbose:
                logger.info("デーモン終了リクエストを受信")
            
            import asyncio
            asyncio.create_task(self._shutdown())
            
            return JSONResponse(
                status_code=200,
                content={"message": "shutting_down"}
            )
    
    async def _shutdown(self):
        import asyncio
        await asyncio.sleep(1)
        import sys
        sys.exit(0)
