from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TextArea, Label, Button, Static
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel
import json
from loguru import logger

class Message(BaseModel):
    role: str
    content: str

class TUIApp(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 1;
        grid-rows: 1fr 3fr 1fr auto;
    }
    
        height: 100%;
        overflow-y: scroll;
        border: solid green;
    }
    
        height: 100%;
        border: solid blue;
    }
    
        height: 100%;
        layout: horizontal;
        border: solid red;
    }
    
        height: auto;
        border: solid yellow;
        background: $accent;
        color: $text;
        text-align: center;
        padding: 1;
    }
    
    Button {
        width: 25%;
    }
    
    TextArea {
        height: 100%;
    }
    """
    
    current_request = reactive(None)
    response_ready = asyncio.Event()
    response_data = None
    
    def __init__(self, request_data: Dict[str, Any], verbose: bool = False):
        super().__init__()
        self.request_data = request_data
        self.verbose = verbose
        if verbose:
            logger.info("TUIを初期化しました")
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="request-container"):
            yield Label("受信したリクエスト:")
            yield Static(id="model", classes="request-item")
            yield Static(id="messages", classes="request-item")
            yield Static(id="params", classes="request-item")
        
        with Container(id="response-container"):
            yield Label("応答の入力:")
            yield TextArea(id="response-input")
        
        with Horizontal(id="controls-container"):
            yield Button("送信 [Enter]", id="send", variant="primary")
            yield Button("対応不可 [F1]", id="cannot-answer", variant="warning")
            yield Button("内部エラー [F2]", id="internal-error", variant="error")
            yield Button("権限なし [F3]", id="forbidden", variant="error")
        
        with Container(id="help-container"):
            yield Static("操作方法: [F1] 対応不可 | [F2] 内部エラー | [F3] 権限なし | [Enter] 送信")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """アプリが起動したときにリクエストデータを表示"""
        self.update_request_display()
    
    def update_request_display(self) -> None:
        """リクエスト情報を画面に表示"""
        model_display = self.query_one("#model")
        messages_display = self.query_one("#messages")
        params_display = self.query_one("#params")
        
        model_display.update(f"モデル: {self.request_data['model']}")
        
        messages_text = "メッセージ:\n"
        for msg in self.request_data["messages"]:
            messages_text += f"- {msg['role']}: {msg['content']}\n"
        messages_display.update(messages_text)
        
        params_text = "パラメータ:\n"
        params_text += f"- max_tokens: {self.request_data.get('max_tokens', 1000)}\n"
        params_text += f"- temperature: {self.request_data.get('temperature', 0.7)}\n"
        params_display.update(params_text)
        
        if self.verbose:
            logger.info("TUIにリクエスト情報を表示しました")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """ボタンが押されたときの処理"""
        button_id = event.button.id
        
        if button_id == "send":
            self.submit_response()
        elif button_id == "cannot-answer":
            self.response_data = {"error": "cannot_answer"}
            self.response_ready.set()
            self.exit()
        elif button_id == "internal-error":
            self.response_data = {"error": "internal_error"}
            self.response_ready.set()
            self.exit()
        elif button_id == "forbidden":
            self.response_data = {"error": "forbidden"}
            self.response_ready.set()
            self.exit()
    
    def on_key(self, event) -> None:
        """キーボードショートカットの処理"""
        if event.key == "f1":
            self.response_data = {"error": "cannot_answer"}
            self.response_ready.set()
            self.exit()
        elif event.key == "f2":
            self.response_data = {"error": "internal_error"}
            self.response_ready.set()
            self.exit()
        elif event.key == "f3":
            self.response_data = {"error": "forbidden"}
            self.response_ready.set()
            self.exit()
        elif event.key == "enter" and not isinstance(self.focused, TextArea):
            self.submit_response()
    
    def submit_response(self) -> None:
        """応答を送信する"""
        response_text = self.query_one("#response-input").text
        self.response_data = {"content": response_text}
        self.response_ready.set()
        if self.verbose:
            logger.info(f"応答を送信: {response_text}")
        self.exit()

async def process_request(request_data, verbose=False):
    """リクエストをTUIで処理し、結果を返す"""
    if verbose:
        logger.info("TUIでリクエストの処理を開始")
    
    app = TUIApp(request_data.dict(), verbose)
    async def run_app():
        await app.run_async()
    
    asyncio.create_task(run_app())
    
    await app.response_ready.wait()
    
    if verbose:
        logger.info(f"TUIからの応答: {app.response_data}")
    
    return app.response_data
