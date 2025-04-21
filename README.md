# HAL = Humans Are Listening

CLI/TUI アプリケーション「HAL」は、外部の AI Agent から OpenAI の /v1/chat/completions API 互換リクエストを受け取り、裏側で人間がレスポンスを書いて返すサービスです。

## 機能

- API と互換性を持つ HTTP サーバー
- 同時リクエスト不可（排他制御）
- 画面上にリクエスト内容を表示し、人間オペレータが応答文を作成
- 応答を JSON 形式で返却
- 各種エラー・ステータスコード制御機能

## 追加機能

- テストクライアント
- 固定返答をするデーモンモード
- 詳細ログ出力モード

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/uzulla/HAL.git
cd HAL

# 仮想環境のセットアップ
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

## 使い方

### HALサーバーの起動

```bash
# 通常モード
python -m src.hal.main

# verboseモード
python -m src.hal.main -v

# 固定返答デーモンモード
python -m src.hal.main --fix-reply-daemon="こんにちは、休暇中です。"
```

### テストクライアントの使用

```bash
# メッセージ送信
python -m src.chat-client.main send --user "こんにちは、元気ですか？"

# システムプロンプト付きメッセージ送信
python -m src.chat-client.main send --system "あなたは医療アシスタントです。" --user "頭痛がします"

# デーモンの終了
python -m src.chat-client.main daemon --kill --message "任意のメッセージ"
```

## 操作方法

TUI画面では以下のキー操作が可能です：

- F1：「このメッセージには対応できません」を返す
- F2：Internal Server Error を返す
- F3：Forbidden を返す
- Enter：入力した応答を送信する

