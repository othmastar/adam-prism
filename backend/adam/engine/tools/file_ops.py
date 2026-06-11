"""أدوات الملفات — disk, file_read, file_write, file_download"""

import os
import subprocess
import uuid
from typing import Dict

import httpx

from adam.infrastructure import sanitize_path


class FileOpsMixin:
    """Mixin: disk + file read/write/download tools"""

    async def _tool_disk(self, params: Dict) -> Dict:
        try:
            disk_data = {}
            extra_paths = [p for p in self.config.get("extra_disk_paths", []) if os.path.exists(p)]
            for path in ["/"] + extra_paths:
                    usage = subprocess.check_output(["df", "-h", path]).decode().split("\n")[1].split()
                    disk_data[path] = {"size": usage[1], "used": usage[2], "available": usage[3], "used_pct": usage[4]}
            return {"success": True, "disks": disk_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _tool_file(self, tool_name: str, params: Dict) -> Dict:
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
                with open(safe, "r", encoding="utf-8", errors="replace") as f:
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
                os.makedirs(os.path.dirname(safe) or ".", exist_ok=True)
                with open(safe, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "path": safe, "size": len(content)}

            elif tool_name == "file_download":
                url = params.get("url", "")
                if not url:
                    return {"success": False, "error": "مفيش URL"}
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
        except Exception as e:
            return {"success": False, "error": str(e)}
