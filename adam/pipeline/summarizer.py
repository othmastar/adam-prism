"""
Adam Prism - نظام التلخيص الحي الهرمي
======================================
Hierarchical Live Summarization
يقرأ الملفات الضخمة جزءاً بجزء، يلخص كل جزء، يربط بينها، وينتج:
- ملخصات متدرجة
- خريطة مفاهيم
- بيانات تدريبية جاهزة
- ملفات حية على القرص
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator

import httpx

logger = logging.getLogger("adam_prism.pipeline.summarizer")


class LiveSummarizer:
    """
    التلخيص الحي الهرمي.
    
    الآلية:
    1. يُقسّم الملف الكبير لأجزاء (chunks)
    2. كل جزء يُلخص مع سياق من الجزء السابق
    3. الملخصات تُكتب في ملفات حية فوراً
    4. بعد الانتهاء: ملخص شامل + خريطة مفاهيم + بيانات تدريبية
    
    هذا يمنع:
    - اختناق السياق (context overflow)
    - ضياع المعلومات بين الأجزاء
    - فقدان الروابط بين الأفكار
    """

    def __init__(self, config: Dict[str, Any], shared_clients=None):
        self.config = config
        self.shared_clients = shared_clients
        self.ollama_base = config.get("ollama_base", "http://localhost:11434")
        self.model_name = config.get("model_name", "gemma3:4b")
        self.chunk_size = config.get("chunk_size", 3000)
        self.overlap = config.get("overlap", 200)
        self.output_dir = Path(config.get("summary_output_dir", "./notebook/summaries"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # الملف الحي الرئيسي
        self.live_file = self.output_dir / "live_summary.md"

    async def summarize_document(
        self,
        text: str,
        source: str = "unknown",
        title: str = "untitled",
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        تلخيص مستند كامل بالآلية الهرمية.
        
        Returns:
            {
                "master_summary": str,
                "concept_map": Dict,
                "training_data": List[Dict],
                "chunk_summaries": List[str],
                "stats": Dict
            }
        """
        start_time = datetime.now()
        
        # 1. تقسيم المستند
        chunks = self._split_text(text)
        logger.info(f"تم تقسيم المستند إلى {len(chunks)} جزء")
        
        # 2. تلخيص كل جزء مع السياق التراكمي
        chunk_summaries = []
        cumulative_context = ""
        concept_map = {"nodes": [], "edges": []}
        training_data = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"تلخيص الجزء {i+1}/{len(chunks)}...")
            
            # تلخيص مع السياق السابق
            summary = await self._summarize_chunk(
                chunk=chunk,
                chunk_index=i,
                total_chunks=len(chunks),
                previous_context=cumulative_context,
                source=source
            )
            
            chunk_summaries.append(summary)
            
            # تحديث السياق التراكمي (آخر ملخصين فقط لمنع التضخم)
            cumulative_context = " ".join(chunk_summaries[-2:])
            
            # استخراج المفاهيم
            concepts = await self._extract_concepts(summary)
            concept_map["nodes"].extend(concepts)
            
            # استخراج بيانات تدريبية
            qa_pairs = await self._extract_training_data(summary, chunk)
            training_data.extend(qa_pairs)
            
            # كتابة في الملف الحي فوراً
            self._write_live(i + 1, len(chunks), summary, concepts, source)
            
            # إرسال تقدم
            if progress_callback:
                await progress_callback(i + 1, len(chunks), summary)

        # 3. إنشاء الملخص الشامل
        master_summary = await self._create_master_summary(chunk_summaries, title)
        
        # 4. بناء خريطة المفاهيم الكاملة
        concept_map = await self._build_concept_map(concept_map, chunk_summaries)
        
        # 5. حفظ النتائج
        result = {
            "master_summary": master_summary,
            "concept_map": concept_map,
            "training_data": training_data,
            "chunk_summaries": chunk_summaries,
            "stats": {
                "total_chunks": len(chunks),
                "total_chars": len(text),
                "total_training_pairs": len(training_data),
                "total_concepts": len(concept_map.get("nodes", [])),
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
        }
        
        # حفظ على القرص
        self._save_results(title, result)
        
        return result

    def _split_text(self, text: str) -> List[str]:
        """تقسيم النص لأجزاء مع تداخل"""
        # تقسيم حسب الفقرات أولاً
        paragraphs = text.split("\n\n")
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # لو إضافة الفقرة تتجاوز الحجم
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # التداخل: آخر جزء من القطعة السابقة
                overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # آخر قطعة
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    async def _summarize_chunk(
        self,
        chunk: str,
        chunk_index: int,
        total_chunks: int,
        previous_context: str,
        source: str
    ) -> str:
        """تلخيص جزء واحد مع السياق السابق"""
        context_section = ""
        if previous_context:
            context_section = f"""
السياق من الأجزاء السابقة:
{previous_context[-500:]}

---

"""

        prompt = f"""أنت آدم - تلخص هذا الجزء من المستند مع ربطه بالسياق السابق.

{context_section}الجزء {chunk_index + 1} من {total_chunks} - المصدر: {source}

المحتوى:
{chunk}

اكتب ملخصاً يشمل:
1. الأفكار الرئيسية في هذا الجزء
2. أي ربط بأفكار من الأجزاء السابقة
3. مصطلحات أو مفاهيم جديدة ظهرت
4. أسئلة أو نقاط تحتاج توضيح"""

        try:
            if self.shared_clients:
                client = await self.shared_clients.get("ollama", self.ollama_base, 120.0)
            else:
                client = httpx.AsyncClient(timeout=120.0)
            response = await client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_ctx": 4096}
                }
            )
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"فشل تلخيص الجزء {chunk_index}: {e}")
            return f"[فشل التلخيص: {str(e)[:100]}]"
        finally:
            if not self.shared_clients and 'client' in dir() and client:
                await client.aclose()

    async def _extract_concepts(self, summary: str) -> List[Dict]:
        """استخراج المفاهيم من الملخص"""
        prompt = f"""استخرج المفاهيم الرئيسية من النص التالي.
لكل مفهوم: الاسم، التعريف المختصر، النوع (نظرية/مفهوم/مبدأ/أداة/شخص/حدث)

النص:
{summary}

أجب بـ JSON فقط:
[{{"name": "...", "definition": "...", "type": "..."}}]"""

        try:
            if self.shared_clients:
                client = await self.shared_clients.get("ollama", self.ollama_base, 60.0)
            else:
                client = httpx.AsyncClient(timeout=60.0)
            response = await client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
            )
            text = response.json().get("response", "[]")
            return json.loads(text.strip().replace("```json", "").replace("```", ""))
        except Exception:
            return []
        finally:
            if not self.shared_clients and 'client' in dir() and client:
                await client.aclose()

    async def _extract_training_data(self, summary: str, original: str) -> List[Dict]:
        """استخراج أزواج سؤال-جواب للبيانات التدريبية"""
        prompt = f"""من الملخص التالي، استخرج أزواج سؤال وجواب مفيدة كبيانات تدريبية.

الملخص:
{summary}

أجب بـ JSON فقط:
[{{"instruction": "...", "input": "", "output": "..."}}]"""

        try:
            if self.shared_clients:
                client = await self.shared_clients.get("ollama", self.ollama_base, 60.0)
            else:
                client = httpx.AsyncClient(timeout=60.0)
            response = await client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                }
            )
            text = response.json().get("response", "[]")
            return json.loads(text.strip().replace("```json", "").replace("```", ""))
        except Exception:
            return []
        finally:
            if not self.shared_clients and 'client' in dir() and client:
                await client.aclose()

    async def _create_master_summary(self, chunk_summaries: List[str], title: str) -> str:
        """إنشاء الملخص الشامل من كل الملخصات الجزئية"""
        all_summaries = "\n\n---\n\n".join([
            f"الجزء {i+1}: {s}" for i, s in enumerate(chunk_summaries)
        ])
        
        prompt = f"""أنت آدم - أنشئ ملخصاً شاملاً نهائياً من كل الملخصات الجزئية.

العنوان: {title}

الملخصات الجزئية:
{all_summaries}

اكتب ملخصاً شاملاً يتضمن:
1. الفكرة المركزية
2. المحاور الرئيسية
3. الاستنتاجات
4. التطبيقات العملية"""

        try:
            if self.shared_clients:
                client = await self.shared_clients.get("ollama", self.ollama_base, 120.0)
            else:
                client = httpx.AsyncClient(timeout=120.0)
            response = await client.post(
                "/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_ctx": 4096}
                }
            )
            return response.json().get("response", "")
        except Exception as e:
            return f"[فشل إنشاء الملخص الشامل: {e}]"
        finally:
            if not self.shared_clients and 'client' in dir() and client:
                await client.aclose()

    async def _build_concept_map(self, concept_map: Dict, summaries: List[str]) -> Dict:
        """بناء خريطة المفاهيم مع الروابط"""
        # تبسيط: استخراج الروابط من المفاهيم
        nodes = concept_map.get("nodes", [])
        edges = []
        
        # ربط المفاهيم من نفس النوع
        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                if node_a.get("type") == node_b.get("type"):
                    edges.append({
                        "source": node_a.get("name", ""),
                        "target": node_b.get("name", ""),
                        "relation": "same_type"
                    })
        
        concept_map["edges"] = edges
        return concept_map

    def _write_live(self, chunk_num: int, total: int, summary: str, concepts: List, source: str):
        """كتابة في الملف الحي فوراً"""
        with open(self.live_file, "a", encoding="utf-8") as f:
            f.write(f"\n## الجزء {chunk_num}/{total} — {source}\n")
            f.write(f"**وقت الكتابة**: {datetime.now().strftime('%H:%M:%S')}\n\n")
            f.write(f"{summary}\n\n")
            if concepts:
                f.write("**المفاهيم**: " + ", ".join([c.get("name", "") for c in concepts[:5]]) + "\n")

    def _save_results(self, title: str, result: Dict):
        """حفظ النتائج الكاملة"""
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:50]
        
        # الملخص الشامل
        with open(self.output_dir / f"{safe_title}_master.md", "w", encoding="utf-8") as f:
            f.write(result["master_summary"])
        
        # خريطة المفاهيم
        with open(self.output_dir / f"{safe_title}_concepts.json", "w", encoding="utf-8") as f:
            json.dump(result["concept_map"], f, ensure_ascii=False, indent=2)
        
        # البيانات التدريبية
        with open(self.output_dir / f"{safe_title}_training.jsonl", "w", encoding="utf-8") as f:
            for item in result["training_data"]:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
