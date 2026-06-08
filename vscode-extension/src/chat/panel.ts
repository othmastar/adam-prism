/**
 * Adam Prism Chat Panel — WebView-based chat interface
 */

import * as vscode from 'vscode';
import { AdamAPI } from '../api';

export class AdamChatPanel {
  public static readonly viewType = 'adamPrism.chat';
  private _panel: vscode.WebviewPanel;
  private _disposables: vscode.Disposable[] = [];
  private _messages: { role: string; content: string }[] = [];

  constructor(context: vscode.ExtensionContext, private api: AdamAPI) {
    this._panel = vscode.window.createWebviewPanel(
      AdamChatPanel.viewType,
      'آدم — Chat',
      vscode.ViewColumn.Beside,
      { enableScripts: true, retainContextWhenHidden: true }
    );
    this._panel.iconPath = vscode.Uri.joinPath(context.extensionUri, 'media', 'icon.png');
    this._panel.webview.html = this._html();

    this._panel.webview.onDidReceiveMessage(
      async (msg) => {
        if (msg.type === 'chat') {
          await this._handleChat(msg.text);
        }
      },
      null,
      this._disposables
    );

    this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
  }

  reveal() {
    this._panel.reveal();
  }

  dispose() {
    this._panel.dispose();
    for (const d of this._disposables) d.dispose();
    this._disposables = [];
  }

  get onDidDispose(): vscode.Event<void> {
    return this._panel.onDidDispose;
  }

  // ── Chat Logic ──────────────────────────

  private async _handleChat(text: string) {
    this._messages.push({ role: 'user', content: text });
    this._postMessage({ type: 'addMessage', role: 'user', content: text });

    try {
      const response = await this.api.chat(text);
      this._messages.push({ role: 'assistant', content: response });
      this._postMessage({ type: 'addMessage', role: 'assistant', content: response });
    } catch (err: any) {
      this._postMessage({ type: 'addMessage', role: 'assistant', content: `⚠️ ${err.message}` });
    }
  }

  private _postMessage(msg: any) {
    this._panel.webview.postMessage(msg);
  }

  // ── HTML Template ───────────────────────

  private _html(): string {
    return `<!DOCTYPE html>
<html lang="ar" dir="auto">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #1a1b26;
  --surface: #24253a;
  --text: #c9d1d9;
  --accent: #7c3aed;
  --user-bg: #312e81;
  --bot-bg: #1e293b;
  --border: #334155;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  flex-direction: column;
}
#header {
  padding: 12px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
#header .status { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
#header .status.online { background: #22c55e; }
#header .status.offline { background: #ef4444; }
#header .title { font-weight: 600; }
#messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.msg { max-width: 85%; padding: 10px 14px; border-radius: 12px; line-height: 1.5; white-space: pre-wrap; word-wrap: break-word; font-size: 13px; }
.msg.user { background: var(--user-bg); align-self: flex-end; border-bottom-right-radius: 4px; }
.msg.assistant { background: var(--bot-bg); align-self: flex-start; border-bottom-left-radius: 4px; border: 1px solid var(--border); }
.msg code { background: rgba(0,0,0,0.3); padding: 1px 4px; border-radius: 3px; font-size: 12px; }
.msg pre { background: #0d1117; padding: 8px; border-radius: 6px; overflow-x: auto; margin: 4px 0; }
.msg pre code { background: none; padding: 0; }
#input-area {
  padding: 12px 16px;
  background: var(--surface);
  border-top: 1px solid var(--border);
  display: flex;
  gap: 8px;
}
#input {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  padding: 8px 12px;
  font-size: 13px;
  outline: none;
  resize: none;
  font-family: inherit;
}
#input:focus { border-color: var(--accent); }
#send {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}
#send:hover { opacity: 0.9; }
#send:disabled { opacity: 0.5; cursor: not-allowed; }
.typing { color: #6b7280; font-style: italic; font-size: 12px; align-self: flex-start; }
</style>
</head>
<body>
<div id="header">
  <span class="status online" id="statusDot"></span>
  <span class="title">آدم</span>
  <span style="font-size:11px;color:#6b7280" id="statusText">online</span>
</div>
<div id="messages"></div>
<div id="input-area">
  <textarea id="input" rows="1" placeholder="اسأل آدم..." dir="auto"></textarea>
  <button id="send">إرسال</button>
</div>

<script>
(function() {
  const vscode = acquireVsCodeApi();
  const messages = document.getElementById('messages');
  const input = document.getElementById('input');
  const send = document.getElementById('send');

  // Auto-resize input
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  // Send message
  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    input.style.height = 'auto';
    send.disabled = true;
    vscode.postMessage({ type: 'chat', text });
  }

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  send.addEventListener('click', sendMessage);

  // Receive messages from extension
  window.addEventListener('message', (event) => {
    const msg = event.data;
    if (msg.type === 'addMessage') {
      const div = document.createElement('div');
      div.className = 'msg ' + msg.role;
      div.textContent = msg.content;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
      send.disabled = false;
    }
    if (msg.type === 'status') {
      const dot = document.getElementById('statusDot');
      const text = document.getElementById('statusText');
      dot.className = 'status ' + (msg.online ? 'online' : 'offline');
      text.textContent = msg.text || (msg.online ? 'online' : 'offline');
    }
  });
})();
</script>
</body>
</html>`;
  }
}
