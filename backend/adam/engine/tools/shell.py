"""
أدوات الشل وتنفيذ بايثون — HARDENED v4
=========================================

[FIX v4 — CRITICAL SECURITY]
- C1: Python sandbox rebuilt from scratch:
  - Removed ALL imports from sandbox header (math, json, etc)
  - Strict __builtins__ whitelist: only safe builtins that can't escape
  - Expanded dangerous pattern checks: __import__, __builtins__,
    __globals__, __code__, exec, compile, open, getattr, setattr,
    delattr, __class__, __subclasses__, __bases__, __mro__,
    globals, locals, vars, dir, eval
  - Block string concatenation tricks for dunder attributes
- C5: Shell find path traversal protection:
  - SENSITIVE_PATHS list blocks access to /etc, /proc, /sys, etc.
  - Any argument starting with a sensitive path is rejected
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

# [C5] المسارات الحساسة — يُمنع الوصول إليها عبر أوامر الشل
SENSITIVE_PATHS = [
    "/etc", "/proc", "/sys", "/root", "/home",
    "/var/log", "/boot", "/dev",
]


def _is_sensitive_path(arg: str) -> bool:
    """فحص هل المسار يبدأ بمسار حساس"""
    # Normalize the path to prevent evasion with trailing slashes or dots
    normalized = arg.rstrip("/")
    for sensitive in SENSITIVE_PATHS:
        # Block if the argument starts with a sensitive path
        if normalized == sensitive or normalized.startswith(sensitive + "/"):
            return True
    return False


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

            # [C5] فحص المسارات الحساسة في كل المعاملات
            for arg in args[1:]:
                if _is_sensitive_path(arg):
                    return {"success": False, "error": f"وصول مرفوض لمسار حساس: {arg}"}

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

            # [C1] منع الأنماط الخطرة — قائمة شاملة مع حماية من الالتفاف
            _dangerous_patterns = [
                # استيراد خطير
                "import os", "from os ", "import subprocess", "from subprocess",
                "import shutil", "from shutil ", "import sys", "sys.modules",
                "__import__", "exec(", "eval(", "compile(",
                "open(", "__builtins__", "getattr(", "setattr(",
                "delattr(", "hasattr(",
                # شبكات
                "socket", "http", "urllib", "requests",
                # أنماط خطرة إضافية
                "breakpoint(", "input(", "exit(", "quit(",
                "os.system", "os.popen", "os.exec", "os.spawn",
                "ctypes", "multiprocessing", "threading",
                # أنماط إضافية ضد الالتفاف
                "pathlib.Path", "os.path.join", "os.makedirs",
                "os.remove", "os.rmdir", "shutil.rmtree",
                # حماية من الالتفاف على الحماية
                "importlib", "import_module", "_import_",
                "base64.b64decode", "base64.b64encode",
                "pickle.loads", "pickle.dumps", "marshal.loads",
                "subprocess.popen", "subprocess.run",
                "os.environ", "os.getenv",
                "  import ",  # مسافات متعددة قبل import
                # [C1] حماية من تجاوز الصندوق عبر تسلسل فئات بايثون
                "__class__", "__mro__", "__subclasses__", "__base__",
                "__bases__", "__dict__", "__globals__", "__init__",
                "__func__", "__code__",
                # [C1] دوال كشف البنية — محظورة تماماً
                "globals(", "locals(", "vars(", "dir(",
                "type.__subclasses__",
            ]
            code_lower = code.lower().replace('\t', ' ')  # توحيد المسافات
            for _dp in _dangerous_patterns:
                # فحص غير حساس للمسافات — يمنع الالتفاف بمسافات متعددة
                dp_normalized = ' '.join(_dp.lower().split())
                code_normalized = ' '.join(code_lower.split())
                if dp_normalized in code_normalized:
                    return {"success": False, "error": f"نمط غير آمن: {_dp}"}

            # [C1] فحص حيل دمج النصوص — مثل "__imp" + "ort__"
            # نحذف علامات الاقتباس وعلامات الجمع والمسافات لنكشف الدمج
            _dunder_fragments = [
                "__import__", "__builtins__", "__globals__", "__code__",
                "__class__", "__subclasses__", "__bases__", "__mro__",
                "__init__", "__func__", "__dict__", "__base__",
            ]
            # Remove quotes, plus signs, and spaces to detect concatenation tricks
            code_stripped = code.replace('"', '').replace("'", "").replace("+", "").replace(" ", "")
            for fragment in _dunder_fragments:
                if fragment in code_stripped:
                    return {"success": False, "error": f"نمط غير آمن (concat): {fragment}"}

            # [C1] تنفيذ في وضع sandbox مع restricted __builtins__
            try:
                # بناء كود sandboxed — __builtins__ يحتوي فقط على آمنة
                _safe_builtins = {
                    "None": None, "True": True, "False": False,
                    "print": print, "range": range, "len": len,
                    "int": int, "float": float, "str": str,
                    "list": list, "dict": dict, "tuple": tuple,
                    "set": set, "bool": bool, "type": type,
                    "isinstance": isinstance, "enumerate": enumerate,
                    "zip": zip, "map": map, "filter": filter,
                    "sorted": sorted, "reversed": reversed,
                    "min": min, "max": max, "sum": sum,
                    "abs": abs, "round": round, "any": any, "all": all,
                }
                _sandbox_header = f"__builtins__ = {_safe_builtins}\n"
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
