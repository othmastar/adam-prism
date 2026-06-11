"""أدوات الشل وتنفيذ بايثون"""

import subprocess
from datetime import datetime
from typing import Dict


class ShellToolsMixin:
    """Mixin: shell + python execution tools"""

    async def _tool_shell(self, tool_name: str, params: Dict) -> Dict:
        if tool_name == "shell":
            command = params.get("command", "")
            if not command:
                return {"success": False, "error": "مفيش أمر"}

            _dangerous = [
                "rm -rf /", "rm -rf /*", "mkfs", "dd if=", "chmod 777", "chmod -R 777",
                "chown root", "chown -R root", ":(){ :|:& };:", "forkbomb",
                "wget ", "curl ", "nc ", "netcat ", "nmap ", "masscan",
                "> /etc/", ">> /etc/", "| bash", "| sh ", "| python3",
                "python3 -c ", "python -c ", "eval ", "exec ",
                "chattr ", "mkswap", "swapoff", "debugfs", "dd of=",
                "fdisk", "parted", "pvcreate", "vgcreate", "lvcreate",
                "modprobe", "insmod", "rmmod", "kmod",
                "iptables", "ufw", "firewall-cmd",
                "passwd", "useradd", "usermod", "userdel", "adduser", "deluser",
                "shutdown", "reboot", "halt", "poweroff", "init ",
                "apt remove", "apt purge", "dpkg --purge", "rpm -e",
                "pacman -R", "yum remove",
            ]
            blocked = [b for b in _dangerous if b in command.lower()]
            if blocked:
                return {"success": False, "error": f"محظور: {blocked[0]}"}

            _unsafe_chars = ["`", "$(", "$(", "${", "|&", "&&", "||"]
            for _c in _unsafe_chars:
                if _c in command:
                    return {"success": False, "error": f"رموز غير آمنة: {_c}"}

            try:
                import shlex
                try:
                    args = shlex.split(command)
                    r = subprocess.run(args, capture_output=True, text=True, timeout=30)
                except Exception:
                    r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                output = r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
                with open("/tmp/adam_shell.log", "a") as f:
                    f.write(f"[{datetime.now().isoformat()}] cmd={command} exit={r.returncode}\n")
                return {"success": r.returncode == 0, "output": output, "exit_code": r.returncode}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "الأمر تجاوز الـ 30 ثانية"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        if tool_name == "python_exec":
            code = params.get("code", "")
            if not code:
                return {"success": False, "error": "مفيش كود"}
            _blocked_imports = ["import os", "from os ", "import subprocess", "from subprocess",
                               "import shutil", "from shutil ", "import sys", "sys.modules",
                               "__import__(", "exec(", "eval(", "compile(",
                               "open(", "__builtins__", "del ", "__del__"]
            for _bi in _blocked_imports:
                if _bi in code:
                    return {"success": False, "error": f"استيراد غير آمن: {_bi}"}
            try:
                r = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=30)
                output = r.stdout.strip() + ("\n" + r.stderr.strip() if r.stderr.strip() else "")
                with open("/tmp/adam_python.log", "a") as f:
                    f.write(f"[{datetime.now().isoformat()}] code={code[:100]} exit={r.returncode}\n")
                return {"success": r.returncode == 0, "output": output, "exit_code": r.returncode}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "الكود تجاوز الـ 30 ثانية"}
            except Exception as e:
                return {"success": False, "error": str(e)}
