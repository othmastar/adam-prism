"""
Adam Prism Engine Chat - دورة المعالجة الكاملة
================================================
The main chat() method and its sub-methods: vision, security, classify+context,
generate+tools, finalize.
"""

import re
import json
import time
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

from adam.engine.tools import AdamPrismEngineTools

logger = logging.getLogger("adam_prism.core")

def _bg_task(coro):
    """جدولة مهمة خلفية مع التقاط الاستثناءات — يمنع task exception was never retrieved"""
    task = asyncio.create_task(coro)
    task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
    return task


class AdamPrismEngineChat(AdamPrismEngineTools):
    """
    Mixin: chat() processing cycle + sub-methods.
    """

    async def chat(self, user_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        الدورة الكاملة للمعالجة (مُحسّنة للسرعة):
        أمان → تصنيف (بدون Ollama) → بحث → توليد → أدوات → حفظ
        """
        self.cycle_count += 1
        cycle_start = time.time()
        self._current_cycle_steps = []
        errors = []

        # Edge cases: empty or too long input
        user_message = (user_message or "").strip()
        if not user_message:
            return {"response": "...", "mode": "teacher", "intent": {"mode": "teacher", "intent_type": "empty"}, "knowledge_used": 0, "cycle": self.cycle_count}
        max_input_len = self.config.get("max_input_length", 8000)
        if len(user_message) > max_input_len:
            user_message = user_message[:max_input_len] + "\n\n[تم اقتطاع الرسالة لطولها]"

        vision_blocked = await self._chat_check_vision(user_message)
        if vision_blocked:
            return vision_blocked

        await self._emit_step("استقبال", "running", {"message": user_message[:100]})
        logger.info(f"[دورة {self.cycle_count}] بدء المعالجة")
        total_deadline = time.time() + self.config.get("cycle_timeout", 120)

        blocked = await self._chat_run_security(user_message)
        if blocked is not None:
            if "_error" in blocked:
                errors.append(blocked["_error"])
            else:
                return blocked

        intent, enriched_context, relevant_knowledge, cleaned_message, errors = \
            await self._chat_classify_context(user_message, errors)

        response_text, tool_records, tool_calls_made, errors = \
            await self._chat_generate_and_tools(
                cleaned_message, enriched_context, intent,
                total_deadline, errors, relevant_knowledge, user_message
            )

        return await self._chat_finalize(
            user_message, response_text, intent, enriched_context,
            tool_records, tool_calls_made, errors, cycle_start
        )

    async def _chat_check_vision(self, user_message: str) -> Optional[Dict]:
        """Edge case: الكشف عن الصور — الموديل لا يدعمها"""
        VISION_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
        if any(user_message.lower().strip().endswith(ext) for ext in VISION_EXTENSIONS) or \
           any(f"Screenshot from" in user_message or f"screenshot_{int(time.time()):0f}" for _ in [1]):
            pass
        vision_refs = [w for w in user_message.split() if any(w.lower().endswith(ext) for ext in VISION_EXTENSIONS) or "screenshot" in w.lower()]
        if vision_refs:
            logger.warning(f"اكتشاف مرجع صورة — الموديل لا يدعم الصور: {vision_refs[0]}")
            return {
                "response": "⚠️ هذا الموديل النصي لا يدعم معالجة الصور. لاستخدام الصور، غيّر الموديل إلى نموذج multimodal مثل `llava` أو `gemma3-vision` عبر الإعدادات.",
                "mode": "communicator", "intent": {"mode": "communicator", "intent_type": "image_ref"}, "knowledge_used": 0, "cycle": self.cycle_count,
            }
        return None

    async def _chat_run_security(self, user_message: str) -> Optional[Dict]:
        """المرحلة 1: فحص الأمان + Input Guard. يرجع dict لو ممنوع، None لو تمام"""
        await self._emit_step("فحص الأمان", "running")
        try:
            if self.security:
                security_check = await self._security_check_with_timeout(user_message)
                if not security_check["allowed"]:
                    await self._emit_step("فحص الأمان", "blocked", {"reason": security_check.get("reason", "")})
                    return {
                        "response": "⚠️ تم رفض الطلب لأسباب أمنية.",
                        "reason": security_check["reason"],
                        "cycle": self.cycle_count
                    }
        except Exception as e:
            logger.warning(f"فحص الأمان فشل: {e}")
            return {"_error": f"security:{e}"}
        await self._emit_step("فحص الأمان", "done")

        if self.security_guard:
            guard_verdict = await self.security_guard.check_input(user_message)
            if guard_verdict.action.value == "block":
                await self._emit_step("Input Guard", "blocked", {"reason": guard_verdict.reason})
                return {
                    "response": "⚠️ تم رفض الطلب. لا يمكنني معالجة هذا النوع من الطلبات.",
                    "reason": f"input_guard:{guard_verdict.reason}",
                    "cycle": self.cycle_count
                }
            elif guard_verdict.action.value == "flag":
                logger.warning(f"Input Guard flagged: {guard_verdict.reason}")
        return None

    async def _chat_classify_context(self, user_message: str, errors: List) -> tuple:
        """المرحلة 2-4: تصنيف القصد + بناء السياق + بحث + URL handling"""
        await self._emit_step("تحليل القصد", "running")
        try:
            intent = self._quick_classify_intent(user_message)
            self.active_mode = intent.get("mode", "communicator")
        except Exception as e:
            logger.warning(f"تحليل القصد فشل: {e}")
            errors.append(f"intent:{e}")
            intent = {"mode": "communicator", "intent_type": "general", "confidence": 1.0, "topics": []}
            self.active_mode = "communicator"
        await self._emit_step("تحليل القصد", "done", {"mode": self.active_mode, "intent": intent.get("intent_type", "")})

        await self._emit_step("بناء السياق", "running")
        ctx_start = time.time()
        try:
            enriched_context = await self._build_context(user_message, intent)
        except Exception as e:
            logger.warning(f"بناء السياق فشل: {e}")
            errors.append(f"context:{e}")
            enriched_context = {"intent": intent, "mode": self.active_mode, "cycle": self.cycle_count}
        self.metrics.timing("chat.build_context", (time.time() - ctx_start) * 1000)
        self.metrics.inc("chat.cycles")
        await self._emit_step("بناء السياق", "done", {"memories": len(enriched_context.get("memories", []))})

        await self._emit_step("البحث في الذاكرة", "running")
        relevant_knowledge = []
        ks_start = time.time()
        if self.knowledge:
            try:
                relevant_knowledge = await asyncio.wait_for(
                    self.knowledge.search(user_message, top_k=3), timeout=10
                )
                enriched_context["knowledge"] = relevant_knowledge
            except asyncio.TimeoutError:
                logger.warning("بحث المعرفة timed out")
                errors.append("knowledge:timeout")
            except Exception as e:
                logger.warning(f"بحث المعرفة فشل: {e}")
                errors.append(f"knowledge:{e}")
        self.metrics.timing("chat.knowledge_search", (time.time() - ks_start) * 1000)
        await self._emit_step("البحث في الذاكرة", "done", {"results": len(relevant_knowledge)})

        url_pattern = r'https?://[^\s<>"\'(){}|\\^`\[\]]+'
        has_url = bool(re.search(url_pattern, user_message))
        cleaned_message = re.sub(url_pattern, "[[WEBPAGE_FETCHED]]", user_message).strip()

        if has_url or self.max_history <= 0:
            enriched_context["sanitized_history"] = []
        else:
            sanitized_history = []
            for msg in self.conversation_history:
                sanitized = {**msg}
                sanitized["content"] = re.sub(url_pattern, "[[WEBPAGE_FETCHED]]", msg.get("content", ""))
                sanitized_history.append(sanitized)
            enriched_context["sanitized_history"] = sanitized_history[-10:]

        if has_url and self.tools:
            urls = re.findall(url_pattern, user_message)
            if urls:
                url = urls[0]
                try:
                    if self.eyes:
                        try:
                            await asyncio.wait_for(self.eyes.initialize(), timeout=15)
                        except Exception:
                            pass
                    result = await asyncio.wait_for(
                        self._execute_tool("browser_fetch", {"url": url}), timeout=50
                    )
                    content = result.get("result") or result.get("data", "")
                    if result.get("success") and len(content) > 10:
                        enriched_context["fetched_content"] = content
                        self.active_mode = "strategic_analyst"
                        intent = {"mode": "strategic_analyst", "intent_type": "personality_analysis", "confidence": 1.0, "topics": []}
                    elif not result.get("success"):
                        logger.warning(f"browser_fetch failed: {result.get('error', 'unknown')}")
                        errors.append("url_fetch:fetch_failed")
                except asyncio.TimeoutError:
                    logger.warning("URL auto-fetch timed out")
                    errors.append("url_fetch:timeout")
                except Exception as e:
                    logger.warning(f"URL fetch failed: {e}")
                    errors.append(f"url_fetch:{e}")

        return intent, enriched_context, relevant_knowledge, cleaned_message, errors

    async def _chat_generate_and_tools(
        self, cleaned_message: str, enriched_context: Dict, intent: Dict,
        deadline: float, errors: List, relevant_knowledge: List,
        original_message: str = ""
    ) -> tuple:
        """المرحلة 5-6: توليد الرد + تنفيذ الأدوات + plugin hooks"""
        fallback_response = "عذراً، حدث خطأ أثناء معالجة طلبك. حاول مرة أخرى."
        max_tool_calls = self.config.get("max_tool_calls", 5)
        tool_calls_made = 0
        tool_records = []

        if self.plugins:
            cleaned_message, enriched_context = await self.plugins.run_before_generate(cleaned_message, enriched_context)

        # Heuristic: auto-inject tool call للمهام الواضحة (معرفة، متصفح، شيل)
        auto_tool = self._detect_auto_tool(cleaned_message, intent, bool(relevant_knowledge))
        if auto_tool and time.time() < deadline:
            tool_calls_made += 1
            await self._emit_step("تنفيذ أداة (تلقائي)", "running", {"tool": auto_tool["_tool"]})
            try:
                tool_result = await asyncio.wait_for(
                    self._execute_tool(auto_tool["_tool"], auto_tool.get("params", {})),
                    timeout=self.config.get("tool_timeout", 30)
                )
            except asyncio.TimeoutError:
                tool_result = {"success": False, "error": "الأداة تجاوزت الوقت المحدد"}
                errors.append(f"auto_tool:{auto_tool['_tool']}:timeout")
            except Exception as e:
                tool_result = {"success": False, "error": str(e)}
                errors.append(f"auto_tool:{auto_tool['_tool']}:{e}")

            tool_records.append({
                "name": auto_tool["_tool"], "params": auto_tool.get("params", {}),
                "success": tool_result.get("success", False),
                "error": tool_result.get("error"),
            })
            if tool_result.get("success"):
                raw = (tool_result.get("result") or tool_result.get("results") or
                       tool_result.get("data") or tool_result.get("text") or
                       tool_result.get("output") or tool_result.get("content") or "")
                if not raw and (tool_result.get("title") or tool_result.get("url")):
                    raw = f"Page: {tool_result.get('title','?')} @ {tool_result.get('url','?')}"
                if isinstance(raw, list):
                    lines = []
                    for r in raw:
                        if isinstance(r, dict):
                            lines.append(f"- [{r.get('collection','?')}] {str(r.get('text',''))[:300]}")
                        else:
                            lines.append(f"- {str(r)[:300]}")
                    content = "\n".join(lines)
                else:
                    content = str(raw)[:2000]
                content = content or f"✅ {auto_tool['_tool']} completed"
                enriched_context["auto_tool_result"] = {
                    "tool": auto_tool["_tool"],
                    "content": content
                }
            await self._emit_step("تنفيذ أداة (تلقائي)", "done", {"tool": auto_tool["_tool"], "success": tool_result.get("success", False)})

        try:
            response_text = await self._generate_with_timeout(cleaned_message, enriched_context, deadline=deadline)
        except asyncio.TimeoutError:
            logger.warning(f"التوليد تجاوز الوقت المحدد")
            errors.append("generation:timeout")
            response_text = ""
        except Exception as e:
            logger.error(f"التوليد فشل: {e}")
            errors.append(f"generation:{e}")
            response_text = ""

        if not response_text.strip():
            response_text = fallback_response

        final_response = ""
        while tool_calls_made < max_tool_calls and time.time() < deadline:
            try:
                tool_request = self._parse_tool_request(response_text)
            except Exception:
                tool_request = None
            if not tool_request:
                final_response = response_text
                break

            tool_calls_made += 1
            tool_name = tool_request.get("_tool", "")
            tool_params = tool_request.get("params", {})
            # لو الأداة اتنفذت قبل كده في auto-inject, ندي النتيجة للموديل ونخرجه
            if tool_name == enriched_context.get("auto_tool_result", {}).get("tool"):
                await self._emit_step("تخطي أداة", "skipped", {"tool": tool_name, "reason": "auto-injected already"})
                errors.append(f"tool:{tool_name}:skipped_duplicate")
                result_data = enriched_context.get("auto_tool_result", {}).get("content", "✅ done")
                msgs = self._build_messages(cleaned_message, enriched_context)
                msgs.append({"role": "assistant", "content": response_text})
                msgs.append({"role": "user", "content": f"نتيجة الأداة [{tool_name}]:\n{result_data[:2000]}\n\nاستخدم هذه النتيجة للرد على المستخدم."})
                try:
                    response_text = await self._call_lora_server(msgs)
                    m = re.search(r'<\|?tool_call\|?>', response_text)
                    if m:  # still has tool call, take text before it
                        response_text = response_text[:m.start()].strip() or "✅ Done. What else?"
                    final_response = response_text
                    break
                except Exception as e:
                    logger.error(f"Skip callback gen failed: {e}")
                    final_response = "✅ Already done. How can I help?"
                    break

            await self._emit_step("تنفيذ أداة", "running", {"tool": tool_name})
            try:
                tool_result = await asyncio.wait_for(
                    self._execute_tool(tool_name, tool_params),
                    timeout=self.config.get("tool_timeout", 30)
                )
            except asyncio.TimeoutError:
                tool_result = {"success": False, "error": "الأداة تجاوزت الوقت المحدد"}
                errors.append(f"tool:{tool_name}:timeout")
            except Exception as e:
                tool_result = {"success": False, "error": str(e)}
                errors.append(f"tool:{tool_name}:{e}")
            await self._emit_step("تنفيذ أداة", "done", {"tool": tool_name, "success": tool_result.get("success", False)})

            tool_records.append({
                "name": tool_name, "params": tool_params,
                "success": tool_result.get("success", False),
                "error": tool_result.get("error"),
            })

            try:
                tool_result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
                if len(tool_result_str) > 2000:
                    tool_result_str = tool_result_str[:2000] + "\n... [مقتطع - النتيجة كبيرة]"
                system_message = f"نتيجة '{tool_name}':\n{tool_result_str}"
                msgs = self._build_messages(cleaned_message, enriched_context)
                msgs.append({"role": "assistant", "content": response_text})
                msgs.append({"role": "user", "content": system_message})
                # GPU memory managed by LoRA server process
                pass
                response_text = await self._call_lora_server(msgs)

                m = re.search(r'<\|?tool_call\|?>', response_text)
                if m:
                    progress = response_text[:m.start()].strip()
                    if progress:
                        final_response = progress
                    continue
                else:
                    final_response = response_text
                    break
            except Exception as e:
                logger.error(f"Tool callback generation failed: {e}")
                errors.append(f"tool_callback:{e}")
                final_response = response_text
                break

        response_text = final_response or response_text
        # Strip any remaining tool call syntax from final output
        response_text = re.sub(r'<\|?tool_call\|?>.*?<\|?/?tool_call\|?>', '', response_text, flags=re.DOTALL).strip()
        response_text = re.sub(r'<\|?tool_call\|?>[^<]*', '', response_text).strip()
        if not response_text.strip():
            response_text = fallback_response

        if self.plugins:
            response_text = await self.plugins.run_after_generate(cleaned_message, response_text)

        self_msg = original_message or cleaned_message
        response_text = self._self_verify_response(response_text, self_msg, intent)
        await self._emit_step("التوليد", "done", {"length": len(response_text), "tool_calls": tool_calls_made, "verified": True})

        return response_text, tool_records, tool_calls_made, errors

    def _detect_auto_tool(self, message: str, intent: Dict, has_knowledge: bool = False) -> Optional[Dict]:
        """معطل — auto-tool heuristics تسببت في تنفيذ أوامر غير مقصودة.
        النموذج يقرر استخدام الأدوات عبر التنسيق المنظم بدلاً من keyword matching."""
        return None

    async def _chat_finalize(
        self, user_message: str, response_text: str, intent: Dict,
        enriched_context: Dict, tool_records: List, tool_calls_made: int,
        errors: List, cycle_start: float
    ) -> Dict[str, Any]:
        """المرحلة 7-8: حفظ + trace + Output Guard + return"""
        fallback_response = "عذراً، حدث خطأ أثناء معالجة طلبك. حاول مرة أخرى."
        cycle_duration = time.time() - cycle_start
        self.metrics.timing("chat.cycle.total", cycle_duration * 1000)

        await self._emit_step("التسجيل والحفظ", "running")
        if response_text != fallback_response and self.max_history > 0:
            self.conversation_history.append({"role": "user", "content": user_message, "timestamp": datetime.now().isoformat()})
            self.conversation_history.append({"role": "assistant", "content": response_text, "timestamp": datetime.now().isoformat()})
            self._trim_conversation_history(self.max_history)

        if self.notebook:
            try:
                await self.notebook.record({
                    "cycle": self.cycle_count, "input": user_message, "intent": intent,
                    "mode": self.active_mode, "response": response_text,
                    "knowledge_used": len(enriched_context.get("knowledge", [])),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"فشل حفظ في الدفتر: {e}")

        if self.knowledge:
            try:
                await self.knowledge.store_conversation(
                    question=user_message, answer=response_text,
                    metadata={"mode": self.active_mode, "cycle": self.cycle_count, "intent": intent}
                )
            except Exception as e:
                logger.warning(f"فشل حفظ في Qdrant: {e}")
        await self._emit_step("التسجيل والحفظ", "done")

        _bg_task(self._extract_and_save_lessons(user_message, response_text, intent))

        if self.continuous_learner:
            _bg_task(
                self.continuous_learner.process_interaction(
                    user_message, response_text,
                    {"mode": self.active_mode, "cycle": self.cycle_count}
                )
            )

        if self.trace_recorder:
            has_tool_errors = any(t.get("error") for t in tool_records)
            outcome = "success"
            if has_tool_errors:
                outcome = "partial"
            elif not response_text.strip():
                outcome = "failure"
            from core.trace_recorder import ConversationTrace
            trace = ConversationTrace(
                query=user_message, intent=intent, mode=self.active_mode,
                tool_calls=tool_records, outcome=outcome,
                response_length=len(response_text), tool_call_count=tool_calls_made,
                cycle=self.cycle_count, duration_ms=int(cycle_duration * 1000),
            )
            self.trace_recorder.record(trace)
            if self.meta_learner and tool_records:
                _bg_task(self.meta_learner.process_trace(trace))

        await self._emit_step("اكتمال الدورة", "done", {"duration_ms": int(cycle_duration * 1000)})

        if self.security_guard and response_text:
            try:
                output_verdict = await self.security_guard.check_output(response_text)
                logger.debug(f"Output Guard: action={output_verdict.action.value if hasattr(output_verdict, 'action') else '?'}")
                if hasattr(output_verdict, 'action') and output_verdict.action.value == "block":
                    logger.warning(f"Output Guard BLOCKED response (len={len(response_text)}): {response_text[:200]}")
                    response_text = "⚠️ لا يمكنني عرض هذا الرد لأسباب أمنية."
                elif hasattr(output_verdict, 'sanitized_content') and output_verdict.sanitized_content:
                    response_text = output_verdict.sanitized_content
            except Exception as e:
                logger.warning(f"Output Guard error: {e}")

        return {
            "response": response_text,
            "mode": self.active_mode,
            "intent": intent,
            "knowledge_used": len(enriched_context.get("knowledge", [])),
            "tools_used": [t["name"] for t in tool_records],
            "tool_records": tool_records,
            "tool_calls_made": tool_calls_made,
            "errors": errors,
            "cycle": self.cycle_count,
            "duration_ms": int(cycle_duration * 1000)
        }
