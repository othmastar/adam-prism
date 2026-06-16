# دليل المستخدم البسيط — Adam Prism
# Non-Technical User Guide

> **You don't need to know anything about programming, Python, or AI to try Adam.**
> Follow these 5 steps. Pick your operating system below.

---

## 🌐 Method 1: Try Adam Online (Easiest, 0 Steps)

If you just want to see Adam in action — **no installation needed**:

1. Open your web browser (Chrome, Firefox, Edge, Safari)
2. Go to: **https://othmastar.github.io/adam-prism/**
3. Type a message in the box
4. Press Enter or click "إرسال"

✅ **That's it.** You can chat with Adam in Arabic or English.

> 💡 Adam is running in **demo mode** with smart mock responses.
> For real AI responses, you need to install Ollama (Method 2 below).

---

## 💻 Method 2: Run Adam on Your Computer (3 Commands)

If you want Adam to run **locally on your computer** (offline, private, faster):

### What you need first

- **A computer** (Windows, Mac, or Linux)
- **Internet connection** (only for the initial installation)
- **10 minutes** of your time
- **2 GB free disk space** (for Python and Adam)

### Step-by-step for your operating system

#### 🪟 Windows (10, 11)

**Step 1: Download Adam**
1. Open your web browser
2. Go to: https://github.com/othmastar/adam-prism
3. Click the green **"Code"** button (top right)
4. Click **"Download ZIP"**
5. Find the downloaded file (usually in `Downloads` folder)
6. **Right-click** the ZIP file → **"Extract All..."**
7. Choose a location (e.g., `Desktop\adam-prism`)

**Step 2: Open Command Prompt**
1. Press the **Windows key** + **R** on your keyboard
2. Type `cmd` and press Enter
3. A black window will open (this is normal!)

**Step 3: Run Adam**
1. In the black window, type:
   ```
   cd Desktop\adam-prism
   bin\adam
   ```
2. Press Enter
3. Wait 1-2 minutes (first time only — installing dependencies)
4. You'll see "Starting Adam Prism on http://0.0.0.0:8000"

**Step 4: Open Adam in browser**
1. Open Chrome, Firefox, or Edge
2. Go to: **http://localhost:8000**
3. Chat with Adam!

**Step 5: Stop Adam (when done)**
1. Go back to the black window
2. Press **Ctrl + C**

---

#### 🍎 macOS (Intel or Apple Silicon)

**Step 1: Download Adam**
1. Open your web browser
2. Go to: https://github.com/othmastar/adam-prism
3. Click the green **"Code"** button
4. Click **"Download ZIP"**
5. Find the downloaded file (usually in `Downloads`)
6. **Double-click** the ZIP to extract
7. Move the folder to your home directory (or wherever you like)

**Step 2: Open Terminal**
1. Press **Cmd + Space** on your keyboard
2. Type `terminal` and press Enter
3. A white window will open

**Step 3: Run Adam**
1. In the Terminal, type:
   ```
   cd ~/Downloads/adam-prism
   ./bin/adam
   ```
2. Press Enter
3. Wait 1-2 minutes (first time only)
4. You'll see "Starting Adam Prism on http://0.0.0.0:8000"

**Step 4: Open Adam in browser**
1. Open Safari, Chrome, or Firefox
2. Go to: **http://localhost:8000**
3. Chat with Adam!

**Step 5: Stop Adam (when done)**
1. Go back to Terminal
2. Press **Ctrl + C**

---

#### 🐧 Linux (Ubuntu, Debian, Fedora, etc.)

**Step 1: Download Adam**
1. Open your web browser
2. Go to: https://github.com/othmastar/adam-prism
3. Click the green **"Code"** button
4. Click **"Download ZIP"**
5. Or use the terminal: `wget https://github.com/othmastar/adam-prism/archive/refs/heads/showcase.zip`

**Step 2: Open Terminal**
1. Press **Ctrl + Alt + T** (on most Linux distros)
2. A terminal window will open

**Step 3: Run Adam**
1. In the Terminal, type:
   ```
   cd ~/Downloads/adam-prism
   ./bin/adam
   ```
2. Press Enter
3. Wait 1-2 minutes (first time only)
4. You'll see "Starting Adam Prism on http://0.0.0.0:8000"

**Step 4: Open Adam in browser**
1. Open Firefox or Chrome
2. Go to: **http://localhost:8000**
3. Chat with Adam!

**Step 5: Stop Adam (when done)**
1. Go back to Terminal
2. Press **Ctrl + C**

---

## 🌟 Method 3: One-Click Install (with Docker, for advanced users)

If you already have Docker installed, just run:

**Linux/Mac (one terminal command):**
```bash
curl -fsSL https://raw.githubusercontent.com/othmastar/adam-prism/main/bin/install.sh | bash
```

**Windows (PowerShell):**
```powershell
iwr https://raw.githubusercontent.com/othmastar/adam-prism/main/bin/install.sh -OutFile install.sh
bash install.sh
```

This installs Docker (if missing), Ollama, Adam, and starts everything automatically.

---

## 🎯 What to try once Adam is running

1. **Chat in Arabic:** "مرحبا آدم، انت مين؟" or "ايه مميزاتك؟"
2. **Chat in English:** "Who are you?" or "What can you do?"
3. **Try quick questions:** Click any button in the demo UI
4. **Check the API:** Open http://localhost:8000/docs in your browser

---

## 🆘 Common Problems

### "I see 'Adam is running' but the browser is blank"
**Solution:** Make sure you open **http://localhost:8000** (not https, not 127.0.0.1)

### "Port 8000 is already in use"
**Solution:** Run Adam on a different port:
- Windows: `bin\adam --port 8080`
- Mac/Linux: `./bin/adam --port 8080`
- Then open http://localhost:8080

### "Python is not installed"
**Solution:** Download Python from https://python.org (choose "Add Python to PATH" during install on Windows)

### "Permission denied" on Mac/Linux
**Solution:** Make the script executable:
```bash
chmod +x bin/adam
./bin/adam
```

### "Ollama not found" warning
**Don't worry!** Adam will use smart mock responses. For real AI, install Ollama:
- Linux/Mac: `curl -fsSL https://ollama.ai/install.sh | sh`
- Windows: Download from https://ollama.ai
- Then: `ollama pull qwen2.5:3b`

---

## 📞 Need help?

- **📧 Email:** othmastar@gmail.com
- **💼 LinkedIn:** https://www.linkedin.com/in/othmastar
- **💬 WhatsApp/Telegram:** +20 100 292 6918
- **🌐 GitHub Issues:** https://github.com/othmastar/adam-prism/issues
- **🏢 For companies:** othman@adam-prism.local

---

## 🇪🇬 النسخة العربية — دليل مختصر

### بدون أي خلفية تقنية

**الطريقة 1 (الأسهل):** افتح **https://othmastar.github.io/adam-prism/** في المتصفح، اكتب أي رسالة، اضغط Enter. خلاص!

**الطريقة 2 (3 خطوات):**
1. حمّل Adam من GitHub (Download ZIP)
2. افتح Terminal (أو CMD على Windows)
3. اكتب `bin/adam` (أو `bin\adam` على Windows)
4. افتح **http://localhost:8000** في المتصفح

**أي مشكلة؟** راسلنا على othmastar@gmail.com أو واتساب +20 100 292 6918.

---

*آخر تحديث: يونيو 2026 — Adam Prism v1.0.0b1*
*Built by Mohamed Othman — Sovereign Neural Fortresses*
