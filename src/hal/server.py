import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, Field

request_lock = threading.Lock()

class Message(BaseModel):
    role: str
    content: str

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
    def __init__(self, verbose: bool = False, fix_reply: Optional[str] = None):
        self.app = FastAPI()
        self.verbose = verbose
        self.fix_reply = fix_reply
        self.setup_routes()
        self.daemon_mode = fix_reply is not None
        
        if verbose:
            logger.info("Verbose mode enabled")
        if self.daemon_mode:
            logger.info(f"デーモンモード有効 - 固定返答: {fix_reply}")

    def setup_routes(self):
        @self.app.post("/v1/chat/completions")
        async def chat_completions(
            request: ChatCompletionRequest,
            authenticated: bool = Depends(authenticate)
        ):
            if self.verbose:
                logger.info(f"リクエスト受信: {request}")
            
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
                
                from .tui import process_request
                result = await process_request(request)
                
                if self.verbose:
                    logger.info(f"応答結果: {result}")
                
                if result.get("error") == "cannot_answer":
                    return JSONResponse(
                        status_code=200,
                        content={"error": "cannot_answer"}
                    )
                elif result.get("error") == "internal_error":
                    return JSONResponse(
                        status_code=500,
                        content={"error": "internal_error"}
                    )
                elif result.get("error") == "forbidden":
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
