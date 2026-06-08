import * as vscode from 'vscode';
import { AdamChatPanel } from './chat/panel';
import { AdamAPI } from './api';

let api: AdamAPI | undefined;
let chatPanel: AdamChatPanel | undefined;

export function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration('adam-prism');
  const endpoint = config.get<string>('endpoint', 'http://localhost:8000');
  const apiKey = config.get<string>('apiKey', '');
  api = new AdamAPI(endpoint, apiKey);

  // ── Open Chat Panel ──────────────────────────────────
  const chatCmd = vscode.commands.registerCommand('adam-prism.chat', () => {
    if (chatPanel) {
      chatPanel.reveal();
    } else {
      chatPanel = new AdamChatPanel(context, api!);
      chatPanel.onDidDispose(() => { chatPanel = undefined; });
    }
  });

  // ── Explain Code ─────────────────────────────────────
  const explainCmd = vscode.commands.registerCommand('adam-prism.explainCode', async () => {
    const code = getSelectedCode();
    if (!code) return;
    const response = await api!.chat(`Explain this code in Arabic:\n\`\`\`\n${code}\n\`\`\``);
    showResult(response, 'Adam Prism - Code Explanation');
  });

  // ── Review Code ──────────────────────────────────────
  const reviewCmd = vscode.commands.registerCommand('adam-prism.reviewCode', async () => {
    const code = getSelectedCode();
    if (!code) return;
    const response = await api!.chat(`Review this code for bugs, security issues, and improvements:\n\`\`\`\n${code}\n\`\`\``);
    showResult(response, 'Adam Prism - Code Review');
  });

  // ── Debug Code ───────────────────────────────────────
  const debugCmd = vscode.commands.registerCommand('adam-prism.debugCode', async () => {
    const code = getSelectedCode();
    if (!code) return;
    const response = await api!.chat(`Debug this code. Find bugs and suggest fixes:\n\`\`\`\n${code}\n\`\`\``);
    showResult(response, 'Adam Prism - Debug');
  });

  // ── Write Test ───────────────────────────────────────
  const testCmd = vscode.commands.registerCommand('adam-prism.writeTest', async () => {
    const code = getSelectedCode();
    if (!code) return;
    const response = await api!.chat(`Write unit tests for this code:\n\`\`\`\n${code}\n\`\`\``);
    showResult(response, 'Adam Prism - Tests');
  });

  // ── Ask About File ──────────────────────────────────
  const fileCmd = vscode.commands.registerCommand('adam-prism.askAboutFile', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const doc = editor.document;
    const code = doc.getText();
    const fileName = doc.fileName;
    const question = await vscode.window.showInputBox({
      prompt: 'What would you like to ask about this file?',
      placeHolder: 'e.g., Summarize this file',
    });
    if (!question) return;
    const response = await api!.chat(`File: ${fileName}\n\`\`\`\n${code}\n\`\`\`\n\nQuestion: ${question}`);
    showResult(response, 'Adam Prism - File Query');
  });

  // ── Set Endpoint ─────────────────────────────────────
  const endpointCmd = vscode.commands.registerCommand('adam-prism.setEndpoint', async () => {
    const url = await vscode.window.showInputBox({
      value: api?.endpoint || 'http://localhost:8000',
      prompt: 'Adam Prism API endpoint URL',
    });
    if (url) {
      api = new AdamAPI(url, api?.apiKey || '');
      vscode.workspace.getConfiguration('adam-prism').update('endpoint', url, true);
    }
  });

  context.subscriptions.push(chatCmd, explainCmd, reviewCmd, debugCmd, testCmd, fileCmd, endpointCmd);
}

export function deactivate() {
  chatPanel?.dispose();
}

// ── Helpers ──────────────────────────────────────────

function getSelectedCode(): string | undefined {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage('No active editor');
    return;
  }
  const selection = editor.selection;
  const code = editor.document.getText(selection);
  if (!code.trim()) {
    vscode.window.showErrorMessage('No code selected');
    return;
  }
  return code;
}

function showResult(text: string, title: string) {
  const panel = vscode.window.createWebviewPanel(
    'adamResult', title, vscode.ViewColumn.Beside,
    { enableScripts: true }
  );
  panel.webview.html = resultHtml(text);
}

function resultHtml(text: string): string {
  return `<!DOCTYPE html>
<html lang="ar" dir="auto">
<head><meta charset="UTF-8">
<style>
body { background: #1a1b26; color: #c9d1d9; padding: 16px; font-family: -apple-system, sans-serif; line-height: 1.6; }
pre { background: #0d1117; padding: 12px; border-radius: 8px; overflow-x: auto; }
code { background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
</style></head>
<body><pre style="white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(text)}</pre></body>
</html>`;
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
