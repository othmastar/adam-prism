"""
أدوات الشل وتنفيذ بايثون — HARDENED v5
=========================================

[C1] Python sandbox: AST-based safe execution with restricted globals
[C5] Shell path traversal protection
"""

import ast
import logging
import shlex
import subprocess

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
    return any(normalized == sensitive or normalized.startswith(sensitive + "/") for sensitive in SENSITIVE_PATHS)


# دوال آمنة مسموح باستخدامها في الـ sandbox
_SAFE_BUILTINS = {
    "None": None, "True": True, "False": False,
    "print": print, "range": range, "len": len,
    "int": int, "float": float, "str": str, "repr": repr,
    "list": list, "dict": dict, "tuple": tuple,
    "set": set, "bool": bool, "type": type,
    "isinstance": isinstance, "enumerate": enumerate,
    "zip": zip, "map": map, "filter": filter,
    "sorted": sorted, "reversed": reversed,
    "min": min, "max": max, "sum": sum,
    "abs": abs, "round": round, "any": any, "all": all,
    "ord": ord, "chr": chr, "hex": hex, "oct": oct, "bin": bin,
    "pow": pow, "divmod": divmod, "hash": hash, "id": id,
    "iter": iter, "next": next, "slice": slice, "issubclass": issubclass,
    "hasattr": hasattr, "getattr": getattr,
}


_DANGEROUS_DUNDERS = frozenset({
    "__class__", "__bases__", "__subclasses__",
    "__mro__", "__globals__", "__code__",
    "__builtins__", "__dict__", "__init__",
    "__func__", "__base__", "__module__",
})

_DANGEROUS_FUNCS = frozenset({
    "exec", "eval", "compile", "__import__", "open",
    "breakpoint", "input", "exit", "quit",
    "globals", "locals", "vars", "dir",
})


def _check_ast_safe(tree: ast.AST) -> str | None:
    """فحص AST ورفض العُقد الخطرة. يرجع رسالة الخطأ أو None لو آمن."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "import غير مسموح به"
        # منع دوال خطرة
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name in _DANGEROUS_FUNCS:
                    return f"لا يمكن استخدام {name}()"
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ("__import__",):
                    return f"لا يمكن استخدام {node.func.attr}()"
        # منع الوصول للـ dunder attributes
        if isinstance(node, ast.Attribute) and node.attr in _DANGEROUS_DUNDERS:
            return f"لا يمكن الوصول لـ {node.attr}"
        # منع الـ dunders كـ string constants — يحمي من getattr(obj, '__class__')
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in _DANGEROUS_DUNDERS:
            return f"لا يمكن استخدام سترينج: {node.value}"
    return None


def _build_sandbox_code(code: str) -> str:
    """بناء كود sandboxed مع restricted globals."""
    import textwrap
    safe_repr = repr(_SAFE_BUILTINS)
    # exec() مع globals مخصصة — الـ __builtins__ مش في الكود نفسه
    exec_wrapper = textwrap.dedent(f"""\
_sandbox_globals = {{"__builtins__": {safe_repr}}}
exec({code!r}, _sandbox_globals)
""").strip()
    return exec_wrapper


class ShellToolsMixin:
    """Mixin: shell + python execution tools"""

    async def _tool_shell(self, tool_name: str, params: dict) -> dict:
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

            if len(code) > 2000:
                return {"success": False, "error": "الكود طويل جداً (الحد: 2000 حرف)"}

            # [C1] Sandbox عبر AST parsing بدلاً من pattern matching
            try:
                tree = ast.parse(code, mode='exec')
            except SyntaxError as e:
                return {"success": False, "error": f"Syntax error: {e}"}

            # فحص AST للعُقد الخطرة
            blocked = _check_ast_safe(tree)
            if blocked:
                return {"success": False, "error": f"نمط غير آمن: {blocked}"}

            # تنفيذ في subprocess مع restricted globals
            try:
                sandboxed_code = _build_sandbox_code(code)
                r = subprocess.run(
                    ["python3", "-c", sandboxed_code],
                    capture_output=True, text=True, timeout=30,
                    env={"PATH": "/usr/bin:/bin"},
                )
                output = r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
                logger.info(f"python_exec (sandboxed): exit={r.returncode}")
                return {"success": r.returncode == 0, "output": output, "exit_code": r.returncode}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "الكود تجاوز الـ 30 ثانية"}
            except Exception as e:
                return {"success": False, "error": str(e)}
