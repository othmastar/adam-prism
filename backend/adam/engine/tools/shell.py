"""
أدوات الشل وتنفيذ بايثون — HARDENED v3
=========================================

[FIX v3 — CRITICAL SECURITY]
- Added Python class hierarchy bypass patterns:
  __class__, __mro__, __subclasses__, __base__, __dict__,
  __globals__, __init__, __func__, __code__
- Added vars(), dir(), type.__subclasses__ to blocked patterns
- Added sandboxed execution mode with restricted __builtins__
- Prevents escape from the Python sandbox via object traversal
"""

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

            # [FIX v3] منع الأنماط الخطرة — قائمة شاملة مع حماية من الالتفاف
            # يشمل الآن حماية من تجاوز الصندوق عبر تسلسل الفئات
            _dangerous_patterns = [
                # استيراد خطير
                "import os", "from os ", "import subprocess", "from subprocess",
                "import shutil", "from shutil ", "import sys", "sys.modules",
                "__import__", "exec(", "eval(", "compile(", "globals(",
                "locals(", "open(", "__builtins__", "getattr(", "setattr(",
                "delattr(", "hasattr(", "type(", "chr(", "ord(",
                # شبكات
                "socket", "http", "urllib", "requests",
                # أنماط خطرة إضافية
                "breakpoint(", "input(", "exit(", "quit(",
                "os.system", "os.popen", "os.exec", "os.spawn",
                "ctypes", "multiprocessing", "threading",
                # أنماط إضافية ضد الالتفاف
                "pathlib.Path", "os.path.join", "os.makedirs",
                "os.remove", "os.rmdir", "shutil.rmtree",
                # [NEW v3] حماية من الالتفاف على الحماية
                "importlib", "import_module", "_import_",
                "base64.b64decode", "base64.b64encode",
                "pickle.loads", "pickle.dumps", "marshal.loads",
                "subprocess.popen", "subprocess.run",
                "os.environ", "os.getenv",
                "  import ",  # مسافات متعددة قبل import
                # [NEW v3 — CRITICAL] حماية من تجاوز الصندوق عبر تسلسل فئات بايثون
                # هذه الأنماط تسمح بالوصول لأي فئة في بايثون وبالتالي
                # تنفيذ أي كود عبر object.__subclasses__()
                "__class__", "__mro__", "__subclasses__", "__base__",
                "__dict__", "__globals__", "__init__", "__func__",
                "__code__",
                # دوال كشف البنية
                "vars(", "dir(",
                "type.__subclasses__",
            ]
            code_lower = code.lower().replace('\t', ' ')  # توحيد المسافات
            for _dp in _dangerous_patterns:
                # فحص غير حساس للمسافات — يمنع الالتفاف بمسافات متعددة
                dp_normalized = ' '.join(_dp.lower().split())
                code_normalized = ' '.join(code_lower.split())
                if dp_normalized in code_normalized:
                    return {"success": False, "error": f"نمط غير آمن: {_dp}"}

            # [NEW v3] تنفيذ في وضع sandbox مع restricted __builtins__
            try:
                # بناء كود sandboxed — يحدد __builtins__ بمجموعة آمنة فقط
                _sandbox_header = (
                    "import math, json, re, collections, itertools, functools, "
                    "datetime, decimal, fractions, random, statistics, typing, "
                    "string, textwrap, pprint, hashlib, uuid\n"
                    "__builtins__ = {}\n"
                )
                sandboxed_code = _sandbox_header + code

                r = subprocess.run(
                    ["python3", "-c", sandboxed_code],
                    capture_output=True, text=True, timeout=30,
                    env={"PATH": "/usr/bin:/bin"},  # حدد PATH فقط
                )
                output = r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
                logger.info(f"python_exec (sandboxed): exit={r.returncode}")
                return {"success": r.returncode == 0, "output": output, "exit_code": r.returncode}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "الكود تجاوز الـ 30 ثانية"}
            except Exception as e:
                return {"success": False, "error": str(e)}
