"""أدوات الملفات — disk, file_read, file_write, file_download

[C3 — CRITICAL SECURITY]
- Added SSRF protection to file_download
- _is_private_ip: checks if hostname resolves to a private/internal IP
- _validate_url: validates URL against private IPs and cloud metadata IPs
- file_download calls _validate_url before downloading
"""

import ipaddress
import os
import subprocess
import uuid
from urllib.parse import urlparse

import httpx

from adam.infrastructure import sanitize_path

# ═══════════════════════════════════════════════════════
# [C3] SSRF Protection — منع الوصول للشبكة الداخلية
# ═══════════════════════════════════════════════════════

def _is_private_ip(hostname: str) -> bool:
    """فحص هل الـ hostname يرجع لعنوان IP خاص أو داخلي"""
    try:
        # محاولة تحويل الـ hostname لعنوان IP مباشرة
        ip = ipaddress.ip_address(hostname)
        return (
            ip.is_private or
            ip.is_loopback or
            ip.is_link_local or
            ip.is_reserved or
            ip.is_multicast or
            ip.is_unspecified
        )
    except ValueError:
        # الـ hostname مش عنوان IP — ممكن يكون اسم نطاق
        pass

    # فحص أسماء المضيفين المحلية
    localhost_names = {
        "localhost", "localhost.localdomain",
        "127.0.0.1", "0.0.0.0", "::1",
        "host.docker.internal", "host.internal",
    }
    if hostname.lower() in localhost_names:
        return True

    # فحص النطاقات الداخلية
    internal_suffixes = (".local", ".internal", ".localhost", ".docker", ".container")
    return bool(any(hostname.lower().endswith(s) for s in internal_suffixes))

def _validate_url(url: str) -> dict:
    """التحقق من صحة وأمان URL — منع SSRF"""
    if not url:
        return {"valid": False, "error": "مفيش URL"}

    try:
        parsed = urlparse(url)
    except (ValueError, TypeError):
        return {"valid": False, "error": f"URL غير صالح: {url}"}

    # التحقق من البروتوكول
    if parsed.scheme not in ("http", "https"):
        return {"valid": False, "error": f"بروتوكول غير مسموح: {parsed.scheme} — يُسمح بـ http و https فقط"}

    # التحقق من وجود hostname
    hostname = parsed.hostname
    if not hostname:
        return {"valid": False, "error": "URL بدون hostname"}

    # التحقق من إن الـ hostname مش عنوان خاص
    if _is_private_ip(hostname):
        return {
            "valid": False,
            "error": f"SSRF محظور: لا يمكن الوصول لعناوين الشبكة الداخلية ({hostname})"
        }

    # منع الوصول لعناوين cloud metadata المعروفة
    cloud_metadata_ips = {
        "169.254.169.254",  # AWS / GCP / Azure metadata
        "fd00:ec2::254",    # AWS IPv6 metadata
    }
    if hostname in cloud_metadata_ips:
        return {
            "valid": False,
            "error": f"SSRF محظور: لا يمكن الوصول لعناوين cloud metadata ({hostname})"
        }

    return {"valid": True}

class FileOpsMixin:
    """Mixin: disk + file read/write/download tools"""

    async def _tool_disk(self, params: dict) -> dict:
        try:
            disk_data = {}
            extra_paths = [p for p in self.config.get("extra_disk_paths", []) if os.path.exists(p)]
            for path in ["/", *extra_paths]:
                    usage = subprocess.check_output(["df", "-h", path]).decode().split("\n")[1].split()
                    disk_data[path] = {"size": usage[1], "used": usage[2], "available": usage[3], "used_pct": usage[4]}
            return {"success": True, "disks": disk_data}
        except (subprocess.CalledProcessError, OSError) as e:
            return {"success": False, "error": str(e)}

    async def _tool_file(self, tool_name: str, params: dict) -> dict:
        try:
            if tool_name == "file_read":
                path = params.get("path", "")
                if not path:
                    return {"success": False, "error": "مفيش مسار"}
                safe = sanitize_path(path)
                if not safe:
                    return {"success": False, "error": "مسار غير مصرح به"}
                if not os.path.isfile(safe):
                    return {"success": False, "error": f"الملف مش موجود: {safe}"}
                max_size = 1024 * 1024
                size = os.path.getsize(safe)
                if size > max_size:
                    return {"success": False, "error": f"الملف كبير جداً ({size//1024}KB). الحد 1MB."}
                with open(safe, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                return {"success": True, "data": content, "path": safe, "size": size}

            elif tool_name == "file_write":
                path = params.get("path", "")
                content = params.get("content", "")
                if not path:
                    return {"success": False, "error": "مفيش مسار"}
                if content is None:
                    return {"success": False, "error": "مفيش محتوى"}
                safe = sanitize_path(path)
                if not safe:
                    return {"success": False, "error": "مسار غير مصرح به"}
                # [M11] Block writes to dotfiles, hidden directories, and sensitive paths
                _BLOCKED_PATH_PARTS = (".ssh", ".config", ".aws", ".env", ".gnupg",
                                        ".kube", ".docker", ".npm", ".gitconfig",
                                        ".htpasswd", ".netrc", ".pgpass")
                # Check each component of the path for hidden/sensitive dirs
                path_parts = os.path.normpath(safe).split(os.sep)
                filename = os.path.basename(safe)
                for part in path_parts:
                    if part in _BLOCKED_PATH_PARTS:
                        return {"success": False, "error": f"الكتابة محظورة في مسار حساس: {part}"}
                # Block dotfiles (files starting with .)
                if filename.startswith('.') and filename != '.':
                    return {"success": False, "error": f"الكتابة محظورة للملفات المخفية: {filename}"}
                os.makedirs(os.path.dirname(safe) or ".", exist_ok=True)
                with open(safe, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "path": safe, "size": len(content)}

            elif tool_name == "file_download":
                url = params.get("url", "")
                if not url:
                    return {"success": False, "error": "مفيش URL"}

                # [C3] SSRF validation before downloading
                validation = _validate_url(url)
                if not validation["valid"]:
                    return {"success": False, "error": validation["error"]}

                async with httpx.AsyncClient(timeout=15) as hc:
                    r = await hc.get(url, follow_redirects=True)
                    r.raise_for_status()
                    dest = f"/tmp/adam_dl_{uuid.uuid4().hex[:8]}.bin"
                    with open(dest, "wb") as f:
                        f.write(r.content)
                return {"success": True, "path": dest, "size": len(r.content),
                        "content_type": r.headers.get("content-type", ""),
                        "preview": r.text[:200] if "text" in r.headers.get("content-type", "") else "(binary)"}
        except httpx.TimeoutException:
            return {"success": False, "error": "التحميل تجاوز الـ 15 ثانية"}
        except (httpx.RequestError, httpx.HTTPStatusError, OSError) as e:
            return {"success": False, "error": str(e)}
