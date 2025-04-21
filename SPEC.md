〈HAL - Humans Are Listening〉 CLI/TUI ソフトウェア実装指示書

1. プロジェクト概要

CLI/TUI アプリケーション「HAL」は、外部の AI Agent から OpenAI の /v1/chat/completions API 互換リクエストを受け取り（認証は常に OK とするスタブ実装）、裏側で人間がレスポンスを書いて返すサービスです。
	•	API と互換性を持つ HTTP サーバー
	•	同時リクエスト不可（排他制御）
	•	画面上にリクエスト内容を表示し、人間オペレータが応答文を作成
	•	応答を JSON 形式で返却
	•	各種エラー・ステータスコード制御機能

2. 要件一覧
	1.	言語／フレームワーク
	•	任意（例：Python + curses／click、Go + tview、Node.js + ink など）
	2.	HTTP エンドポイント
	•	POST /v1/chat/completions
	•	ヘッダ：Content-Type: application/json、Authorization: Bearer <token>（トークン判定は常に OK）
	3.	リクエストボディ

{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user",   "content": "..."}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}


	4.	排他制御
	•	1リクエスト処理中は次のリクエストを受け付けず HTTP 503 または 429 を返す
	•	処理終了後にロックを解放
	5.	認証スタブ

def authenticate(token: str) -> bool:
    return True


	6.	TUI／CLI 表示
	•	受信したリクエスト情報（model、messages、パラメータ）を見やすく整形して表示
	•	入力フォームまたはエディタでオペレータが応答を記述
	•	ワンキー操作：
	•	F1＝「このメッセージには対応できません」→HTTP 200 + {"error": "cannot_answer"}
	•	F2＝Internal Server Error →HTTP 500
	•	F3＝Forbidden →HTTP 403
	•	Enter＝通常レスポンス
	7.	レスポンスフォーマット

{
  "id": "chatcmpl-xxxxx",
  "object": "chat.completion",
  "created": 1713800000,
  "model": "<受信 model>",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "<オペレータが入力>"},
      "finish_reason": "stop"
    }
  ]
}


	8.	エラー応答
	•	503/429：{"error": "server_busy"}
	•	403：{"error": "forbidden"}
	•	500：{"error": "internal_error"}

3. アーキテクチャ／モジュール構成
	1.	HTTP サーバー
	•	リクエスト受信 → 認証 → 排他チェック → パース → TUI 呼び出し
	2.	排他制御ユーティリティ
	•	グローバル mutex／シングルトンロック
	3.	TUI モジュール
	•	画面描画：リクエスト内容／操作ヘルプ／入力エリア
	•	キーイベントハンドラ：F1/F2/F3/Enter
	4.	JSON シリアライザ
	•	応答データ構造を組み立て → json.dumps
	5.	エラーハンドラ
	•	ステータスコードとエラーメッセージの対応
	6.	起動スクリプト／CLI
	•	ポート設定、ログレベル、デバッグモードなど

4. 実装タスク
	1.	プロジェクト初期化（依存管理設定、ディレクトリ構成）
	2.	HTTP サーバー骨組み実装
	3.	認証スタブ関数作成
	4.	排他制御のミドルウェア実装
	5.	リクエストパーサ＆バリデーション
	6.	TUI コンポーネント実装
	7.	レスポンス JSON 組み立てモジュール実装
	8.	エラー応答ハンドリング
	9.	テストケース（正常フロー／排他エラー／各種キー操作）
	10.	README および起動手順ドキュメント整備

