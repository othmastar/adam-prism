"""
Adam Prism — Subagent Teams
=============================
التنسيق بين وكلاء متعددين: task decomposition + parallel execution + result aggregation.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Awaitable

from adam.subagents.session import SubagentSession

logger = logging.getLogger("adam_prism.subagents.teams")


class SubagentTeam:
    """
    فريق وكلاء — بيوزع المهام ويجمع النتائج.
    
    مثال:
    ```python
    team = SubagentTeam(engine, name="code-team")
    team.add_agent("researcher", "You research the problem and find solutions")
    team.add_agent("coder", "You write clean Python code")
    team.add_agent("reviewer", "You review code for bugs and improvements")
    result = await team.run("Build a REST API with FastAPI")
    ```
    """

    def __init__(self, engine, name: str = "team"):
        self.engine = engine
        self.name = name
        self.agents: Dict[str, SubagentSession] = {}
        self._order: List[str] = []
        self._results: Dict[str, Dict] = {}
        self.created_at = datetime.now(timezone.utc)

    def add_agent(
        self,
        name: str,
        system_prompt: str,
        tools_enabled: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """إضافة وكيل للفريق"""
        session = SubagentSession(
            name=name,
            engine=self.engine,
            config={
                "system_prompt": system_prompt,
                "tools_enabled": tools_enabled,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "max_history": 10,
            },
        )
        self.agents[name] = session
        self._order.append(name)
        logger.info(f"👤 Agent '{name}' added to team '{self.name}'")
        return session

    async def run(
        self,
        task: str,
        parallel: bool = False,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        تشغيل الفريق بالكامل على مهمة.
        
        Args:
            task: المهمة المطلوبة
            parallel: إذا كان True، الـ agents يشتغلوا بالتوازي
            context: سياق إضافي (اختياري)
        """
        self._results = {}
        context_str = f"\nالسياق:\n{json.dumps(context, ensure_ascii=False)}" if context else ""

        if parallel:
            return await self._run_parallel(task, context_str)
        return await self._run_sequential(task, context_str)

    async def _run_sequential(self, task: str, context: str = "") -> Dict[str, Any]:
        """تشغيل agents بالتسلسل — كل واحد يشوف ناتج اللي قبله"""
        previous_result = ""
        for name in self._order:
            agent = self.agents[name]
            prompt = f"المهمة الأساسية:\n{task}\n{context}"
            if previous_result:
                prompt += f"\n\nنتائج الخطوات السابقة:\n{previous_result}"

            logger.info(f"🔄 Running agent '{name}'...")
            try:
                result = await agent.chat(prompt)
                agent_result = result.get("response", "")
                self._results[name] = {
                    "response": agent_result,
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                previous_result += f"\n--- {name} ---\n{agent_result}"
            except Exception as e:
                logger.warning(f"⚠️ Agent '{name}' failed: {e}")
                self._results[name] = {"response": "", "status": f"error: {e}"}

        return self._summarize(task)

    async def _run_parallel(self, task: str, context: str = "") -> Dict[str, Any]:
        """تشغيل agents بالتوازي — كل واحد يشتغل لوحده"""
        prompts = {name: f"المهمة:\n{task}\n{context}" for name in self._order}

        async def _run_one(name: str, prompt: str):
            agent = self.agents[name]
            try:
                result = await agent.chat(prompt)
                self._results[name] = {
                    "response": result.get("response", ""),
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as e:
                self._results[name] = {"response": "", "status": f"error: {e}"}

        tasks = [_run_one(name, prompts[name]) for name in self._order]
        await asyncio.gather(*tasks)
        return self._summarize(task)

    def _summarize(self, task: str) -> Dict[str, Any]:
        """تجميع نتائج كل agents في تقرير واحد"""
        all_results = {name: data["response"] for name, data in self._results.items()}
        return {
            "team": self.name,
            "task": task,
            "agents": self._order,
            "results": all_results,
            "status": "completed",
            "created_at": self.created_at.isoformat(),
        }

    async def chat_with_agent(self, agent_name: str, message: str) -> Dict:
        """التحدث مع وكيل معين داخل الفريق"""
        if agent_name not in self.agents:
            return {"error": f"Agent '{agent_name}' not found"}
        return await self.agents[agent_name].chat(message)

    def get_agent_result(self, agent_name: str) -> Optional[str]:
        """الحصول على نتيجة وكيل معين"""
        data = self._results.get(agent_name)
        return data["response"] if data else None

    def get_status(self) -> Dict:
        return {
            "name": self.name,
            "agents": list(self.agents.keys()),
            "results_count": len(self._results),
            "created_at": self.created_at.isoformat(),
        }

    def remove_agent(self, name: str):
        """إزالة وكيل من الفريق"""
        self.agents.pop(name, None)
        self._order = [n for n in self._order if n != name]


class TeamManager:
    """مدير فرق الوكلاء — بيدير creation + orchestration"""

    def __init__(self, engine):
        self.engine = engine
        self._teams: Dict[str, SubagentTeam] = {}

    def create_team(self, name: str) -> SubagentTeam:
        team = SubagentTeam(self.engine, name=name)
        self._teams[name] = team
        return team

    def get_team(self, name: str) -> Optional[SubagentTeam]:
        return self._teams.get(name)

    def remove_team(self, name: str) -> bool:
        team = self._teams.pop(name, None)
        return team is not None

    def list_teams(self) -> List[Dict]:
        return [t.get_status() for t in self._teams.values()]

    def remove_all(self):
        self._teams.clear()
