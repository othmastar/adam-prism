"""أدوات الشل وتنفيذ بايثون — HARDENED v2"""

import subprocess
import shlex
import logging
from typing import Dict

logger = logging.getLogger("adam_prism.shell")

# الأوامر المسموحة فقط — أي أمر خارج القائمة يُرفض
# تم حذف الأوامر الخطرة: ps, top, free, uptime, hostname
ALLOWED_COMMANDS = {
    "ls", "cat", "pwd", "echo", "grep", "head", "tail", "wc",
    "find", "df", "du", "whoami", "date", "uname", "which",
    "sort", "uniq", "diff", "file", "stat", "tree",
}

# الحد الأقصى لطول الأمر — منع أوامر طويلة جداً
MAX_COMMAND_LENGTH = 500


class ShellToolsMixin:
    """Mixin: shell + python execution tools"""

    async def _tool_shell(self, tool_name: str, params: Dict) -> Dict:
        if tool_name == "shell":
            command = params.get("command", "")
            if not command:
                return {"success": False, "error": "مفيش أمر"}

            # فحص طول الأمر
            if len(command) > MAX_COMMAND_LENGTH:
                return {"success": False, "error": f"الأمر طويل جداً (الحد: {MAX_COMMAND_LENGTH} حرف)"}

            # رفض أي رموز خطرة
            _unsafe_chars = ["`", "$(", "${", "|&", "&&", "||", ";", ">", ">>", "<", "\n", "\r"]
            for _c in _unsafe_chars:
                if _c in command:
                    return {"success": False, "error": f"رموز غير آمنة: {_c}"}

            # تقسيم الأمر والتحقق من القائمة البيضاء
            try:
                args = shlex.split(command)
            except ValueError as e:
                # لا نستخدم shell=True أبداً — نرفض الأمر بدلاً من ذلك
                return {"success": False, "error": f"أمر غير صالح: {e}"}

            if not args:
                return {"success": False, "error": "أمر فارغ"}

            base_cmd = args[0]
            if base_cmd not in ALLOWED_COMMANDS:
                return {"success": False, "error": f"أمر محظور وغير مسموح: {base_cmd} — الأوامر المتاحة: {', '.join(sorted(ALLOWED_COMMANDS))}"}

            # تنفيذ بدون shell=True أبداً
            try:
                r = subprocess.run(args, capture_output=True, text=True, timeout=30)
                output = r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
                logger.info(f"shell: {command} exit={r.returncode}")
                return {"success": r.returncode == 0, "output": output, "exit_code": r.returncode}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "الأمر تجاوز الـ 30 ثانية"}
            except FileNotFoundError:
                return {"success": False, "error": f"الأمر '{base_cmd}' مش موجود على النظام"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        if tool_name == "python_exec":
            code = params.get("code", "")
            if not code:
                return {"success": False, "error": "مفيش كود"}

            # حد أقصى لكود البايثون — منع كود طويل جداً
            if len(code) > 2000:
                return {"success": False, "error": "الكود طويل جداً (الحد: 2000 حرف)"}

            # منع الأنماط الخطرة — قائمة شاملة
            _dangerous_patterns = [
                "import os", "from os ", "import subprocess", "from subprocess",
                "import shutil", "from shutil ", "import sys", "sys.modules",
                "__import__", "exec(", "eval(", "compile(", "globals(",
                "locals(", "open(", "__builtins__", "getattr(", "setattr(",
                "delattr(", "hasattr(", "type(", "chr(", "ord(",
                "socket", "http", "urllib", "requests",
                # أنماط خطرة إضافية
                "breakpoint(", "input(", "exit(", "quit(",
                "os.system", "os.popen", "os.exec", "os.spawn",
                "ctypes", "multiprocessing", "threading",
                # [NEW v2] أنماط إضافية
                "pathlib.Path", "os.path.join", "os.makedirs",
                "os.remove", "os.rmdir", "shutil.rmtree",
            ]
            code_lower = code.lower()
            for _dp in _dangerous_patterns:
                if _dp.lower() in code_lower:
                    return {"success": False, "error": f"نمط غير آمن: {_dp}"}

            try:
                r = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=30)
                output = r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
                logger.info(f"python_exec: exit={r.returncode}")
                return {"success": r.returncode == 0, "output": output, "exit_code": r.returncode}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "الكود تجاوز الـ 30 ثانية"}
            except Exception as e:
                return {"success": False, "error": str(e)}
