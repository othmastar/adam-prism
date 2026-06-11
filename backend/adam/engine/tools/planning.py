"""أداة التخطيط — CRUD للمهام"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict


class PlanningMixin:
    """Mixin: planning tool — todo list CRUD"""

    async def _tool_planning(self, params: Dict) -> Dict:
        action = params.get("action", "list")
        todo_file = self.config.get("todo_file", os.path.expanduser("~/.local/share/adam/todo_list.json"))
        result = {"success": True, "action": action}
        try:
            from pathlib import Path as _Path
            _todo_path = _Path(todo_file)
            todos = json.loads(_todo_path.read_text(encoding='utf-8')) if _todo_path.exists() else []

            if action == "list":
                status = params.get("status")
                filtered = [t for t in todos if not status or t.get("status") == status]
                result["todos"] = filtered; result["total"] = len(todos); result["filtered"] = len(filtered)

            elif action == "create":
                task = {"id": str(uuid.uuid4())[:8], "title": params.get("title", "مهمة جديدة"),
                        "description": params.get("description", ""), "priority": params.get("priority", "medium"),
                        "status": "pending", "due_date": params.get("due_date", ""),
                        "tags": params.get("tags", []), "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()}
                todos.append(task)
                _todo_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding='utf-8')
                result["task"] = task; result["message"] = f"تم إضافة المهمة: {task['title']}"

            elif action == "update":
                task_id = params.get("id")
                for t in todos:
                    if t["id"] == task_id:
                        for k in ["title", "description", "priority", "status", "due_date", "tags"]:
                            if k in params: t[k] = params[k]
                        t["updated_at"] = datetime.now().isoformat()
                        _todo_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding='utf-8')
                        result["task"] = t; result["message"] = f"تم تحديث المهمة: {t['title']}"
                        break
                else:
                    return {"success": False, "error": "المهمة مش موجودة"}

            elif action == "delete":
                task_id = params.get("id")
                before = len(todos)
                todos = [t for t in todos if t["id"] != task_id]
                if len(todos) < before:
                    _todo_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding='utf-8')
                    result["message"] = f"تم حذف المهمة {task_id}"
                else:
                    return {"success": False, "error": "المهمة مش موجودة"}

            elif action == "plan":
                tasks_created = []
                for task_data in params.get("tasks", []):
                    task = {"id": str(uuid.uuid4())[:8], "title": task_data.get("title", "مهمة جديدة"),
                            "description": task_data.get("description", ""), "priority": task_data.get("priority", "medium"),
                            "status": "pending", "due_date": task_data.get("due_date", ""),
                            "tags": task_data.get("tags", []), "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()}
                    todos.append(task); tasks_created.append(task)
                _todo_path.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding='utf-8')
                result["tasks"] = tasks_created; result["message"] = f"تم إنشاء {len(tasks_created)} مهمة في الخطة"
            else:
                return {"success": False, "error": f"أمر غير معروف: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return result
