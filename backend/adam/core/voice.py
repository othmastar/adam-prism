from __future__ import annotations

"""
Adam Prism - Voice Pipeline
============================
VAD (Silero ONNX) → ASR (faster-whisper) → TTS (Edge TTS)
مع ModelSwapper لإدارة VRAM — موديل واحد في اللحظة.
Silma TTS متاح أيضاً كبديل للـ Voice Cloning.
"""

import asyncio
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger("adam_prism.voice_pipeline")

# الاستيرادات البطيئة — libraries تتحمل فقط عند الاستخدام الفعلي
_np = None
_onnx = None
_whisper = None
_silma = None
_edge = None
_scipy = None

def _load_numpy():
    global _np
    if _np is None:
        import numpy as n
        _np = n
    return _np

def _load_scipy():
    global _scipy
    if _scipy is None:
        import scipy.signal as s
        _scipy = s
    return _scipy


# ═══════════════════════════════════════
# Audio types
# ═══════════════════════════════════════

@dataclass
class AudioChunk:
    data: bytes
    sample_rate: int
    is_final: bool = False
    timestamp: float = 0.0


@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration_seconds: float
    segments: List[Dict[str, Any]]
    is_final: bool = True


@dataclass
class SynthesisResult:
    audio: bytes
    sample_rate: int = 24000
    duration_seconds: float = 0.0
    text: str = ""


# ═══════════════════════════════════════
# Voice Activity Detection
# ═══════════════════════════════════════

class SileroVAD:
    """كاشف النشاط الصوتي — Silero VAD v5 ONNX (CPU, خفيف ~2MB)"""

    def __init__(self, threshold: float = 0.5, min_speech_duration: float = 0.25,
                 min_silence_duration: float = 0.5):
        self._model = None
        self._threshold = threshold
        self._min_speech_duration = min_speech_duration
        self._min_silence_duration = min_silence_duration
        self._sample_rate = 16000
        self._window_size = 512
        self._available = False

    async def load(self) -> bool:
        """تحميل موديل Silero VAD — ONNX CPU خفيف"""
        try:
            import onnxruntime
            model_path = Path(tempfile.gettempdir()) / "silero_vad.onnx"

            if not model_path.exists():
                import urllib.request
                url = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
                logger.info("جاري تحميل Silero VAD ONNX model...")
                urllib.request.urlretrieve(url, str(model_path))
                logger.info("تم تحميل Silero VAD")

            self._model = onnxruntime.InferenceSession(
                str(model_path),
                providers=["CPUExecutionProvider"]
            )
            self._available = True
            logger.info("Silero VAD جاهز على CPU")
            return True
        except Exception as e:
            logger.warning(f"تعذر تحميل Silero VAD: {e}")
            self._available = False
            return False

    @property
    def available(self) -> bool:
        return self._available

    def is_speech(self, audio_chunk: _load_numpy().ndarray) -> float:
        """تحليل قطعة صوت — يعيد درجة الثقة بأنها كلام (0-1)"""
        if not self._available or self._model is None:
            return 0.0

        try:
            input_tensor = _load_numpy().expand_dims(audio_chunk.astype(_load_numpy().float32), 0)
            ort_inputs = {self._model.get_inputs()[0].name: input_tensor}
            ort_outs = self._model.run(None, ort_inputs)
            score = float(ort_outs[0].item())
            return score
        except Exception:
            return 0.0

    async def detect_speech_segments(self, audio: _load_numpy().ndarray,
                                      sample_rate: int) -> List[Dict[str, float]]:
        """تقسيم الصوت إلى مقاطع كلام وسكوت — يعيد قائمة {start, end, speech}"""
        if not self._available:
            return [{"start": 0.0, "end": len(audio) / sample_rate, "speech": True}]

        segments = []
        window_size = int(self._window_size)
        step = window_size // 2

        speech_frames = []
        for i in range(0, len(audio) - window_size + 1, step):
            chunk = audio[i:i + window_size]
            score = self.is_speech(chunk)
            is_speech = score >= self._threshold
            speech_frames.append(is_speech)

        # دمج الإطارات المتجاورة
        in_speech = False
        start_frame = 0
        for i, is_speech in enumerate(speech_frames):
            if is_speech and not in_speech:
                start_frame = i
                in_speech = True
            elif not is_speech and in_speech:
                speech_duration = (i - start_frame) * step / sample_rate
                if speech_duration >= self._min_speech_duration:
                    segments.append({
                        "start": start_frame * step / sample_rate,
                        "end": i * step / sample_rate,
                        "speech": True,
                    })
                in_speech = False

        if in_speech:
            segments.append({
                "start": start_frame * step / sample_rate,
                "end": len(speech_frames) * step / sample_rate,
                "speech": True,
            })

        if not segments:
            segments.append({"start": 0.0, "end": len(audio) / sample_rate, "speech": True})

        return segments

    def unload(self):
        self._model = None
        self._available = False


# ═══════════════════════════════════════
# Automatic Speech Recognition
# ═══════════════════════════════════════

class FasterWhisperASR:
    """ASR باستخدام faster-whisper Medium INT8 (CTranslate2, GPU ~1GB)"""

    MODELS = {
        "tiny": {"size": "tiny", "vram_gb": 0.0, "desc": "الأسرع"},
        "base": {"size": "base", "vram_gb": 0.0, "desc": "سريع"},
        "small": {"size": "small", "vram_gb": 0.0, "desc": "متوازن"},
        "medium": {"size": "medium", "vram_gb": 0.0, "desc": "دقيق"},
    }

    def __init__(self, model_size: str = "base", device: str = "cpu",
                 compute_type: str = "int8"):
        self._model = None
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._available = False
        self._language = "ar"

    async def load(self) -> bool:
        """تحميل faster-whisper (GPU) — ~1GB VRAM"""
        try:
            from faster_whisper import WhisperModel
            logger.info(f"جاري تحميل faster-whisper {self._model_size}...")
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None,
                lambda: WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                )
            )
            self._available = True
            logger.info(f"faster-whisper {self._model_size} جاهز على {self._device}")
            return True
        except Exception as e:
            logger.warning(f"تعذر تحميل faster-whisper: {e}")
            self._available = False
            return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def vram_gb(self) -> float:
        return self.MODELS.get(self._model_size, {}).get("vram_gb", 1.0)

    async def transcribe(self, audio: _load_numpy().ndarray,
                         sample_rate: int = 16000) -> TranscriptionResult:
        """نسخ الصوت إلى نص"""
        if not self._available or self._model is None:
            return TranscriptionResult(
                text="", language="ar", duration_seconds=0.0,
                segments=[], is_final=False,
            )

        try:
            loop = asyncio.get_event_loop()
            def _transcribe():
                seg_gen, info = self._model.transcribe(
                    audio,
                    language=self._language,
                    beam_size=5,
                    vad_filter=True,
                    condition_on_previous_text=True,
                )
                return list(seg_gen), info
            segments, info = await loop.run_in_executor(None, _transcribe)

            full_text = " ".join(seg.text.strip() for seg in segments)
            total_duration = sum(seg.end - seg.start for seg in segments) if segments else 0
            detected_lang = info.language if info else self._language

            return TranscriptionResult(
                text=full_text,
                language=detected_lang if detected_lang else "ar",
                duration_seconds=total_duration,
                segments=[
                    {"start": seg.start, "end": seg.end, "text": seg.text}
                    for seg in segments
                ],
                is_final=True,
            )
        except Exception as e:
            logger.error(f"تعذر النسخ الصوتي: {e}")
            return TranscriptionResult(
                text="", language="ar", duration_seconds=0.0,
                segments=[], is_final=False,
            )

    def unload(self):
        self._model = None
        self._available = False


# ═══════════════════════════════════════
# Model Swapper Import (اختياري — للتوافق)
# ═══════════════════════════════════════

try:
    from infrastructure import ModelSwapper
    _model_swapper_available = True
except ImportError:
    _model_swapper_available = False

# ═══════════════════════════════════════
# Text-to-Speech
# ═══════════════════════════════════════

class EdgeTTS:
    """TTS باستخدام Microsoft Edge TTS — جودة عالية، عربي، مجاني، CPU"""

    ARABIC_VOICES = [
        "ar-SA-HamedNeural",     # ذكر، سعودي (default)
        "ar-EG-ShakirNeural",    # ذكر، مصري
        "ar-SA-ZariyahNeural",   # أنثى، سعودي
        "ar-EG-SalmaNeural",     # أنثى، مصري
        "ar-AE-FatimaNeural",    # أنثى، إماراتي
        "ar-SA-HodaNeural",      # أنثى، مصري
    ]

    def __init__(self, voice: str = "ar-SA-HamedNeural"):
        self._voice = voice
        self._available = False
        self._sample_rate = 24000

    async def load(self) -> bool:
        """تحقق من توفر edge-tts — لا يحتاج تحميل (يستخدم API مايكروسوفت)"""
        try:
            import edge_tts
            # مجرد اختبار أن المكتبة تعمل
            voices = await edge_tts.list_voices()
            ar_voices = [v["ShortName"] for v in voices if v["ShortName"].startswith("ar-")]
            if ar_voices:
                logger.info(f"EdgeTTS جاهز — {len(ar_voices)} صوت عربي متاح")
            else:
                logger.warning("لا توجد أصوات عربية في EdgeTTS")
            self._available = True
            return True
        except Exception as e:
            logger.warning(f"EdgeTTS غير متوفر: {e}")
            self._available = False
            return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def vram_gb(self) -> float:
        return 0.0  # CPU only

    @staticmethod
    def _clean_text(text: str) -> str:
        """تنظيف النص من Markdown والرموز عشان TTS ما يقراهاش"""
        import re
        # 1. Strip code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        # 2. Strip inline code
        text = re.sub(r'`[^`]+`', '', text)
        # 3. Strip markdown links [text](url) → text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # 4. Strip image syntax ![alt](url)
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
        # 5. Strip bold/italic **text** or __text__ → text
        text = re.sub(r'(\*{1,3}|_{1,3})(.*?)\1', r'\2', text)
        # 6. Strip headers #
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 7. Strip blockquotes >
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        # 8. Strip list markers - * + at line start
        text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
        # 9. Strip numbered list markers
        text = re.sub(r'^\s*\d+[.\)]\s+', '', text, flags=re.MULTILINE)
        # 10. Strip horizontal rules --- *** ___
        text = re.sub(r'^[\s]*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        # 11. Strip HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # 12. Collapse multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 13. Strip thinking blocks
        text = re.sub(r'(?:Thinking|Here\'s a thinking|\[REDACTED\]).*?(?:done thinking\.|$)', '', text, flags=re.DOTALL)
        # 14. Strip [CAPS_TEXT] style annotations
        text = re.sub(r'\[[A-Z_]+\]', '', text)
        return text.strip()

    async def synthesize(self, text: str, language: str = "ar") -> SynthesisResult:
        """توليد صوت من نص — MP3 عبر Edge TTS API"""
        if not self._available:
            return SynthesisResult(audio=b"", text=text)

        try:
            import edge_tts
            import io

            cleaned = self._clean_text(text)
            if not cleaned.strip():
                return SynthesisResult(audio=b"", text=text)
            communicate = edge_tts.Communicate(cleaned, self._voice)
            audio_bytes = io.BytesIO()

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes.write(chunk["data"])

            raw_audio = audio_bytes.getvalue()
            duration = len(raw_audio) / 16000  # تقريبي

            return SynthesisResult(
                audio=raw_audio,
                sample_rate=24000,
                duration_seconds=duration,
                text=text,
            )
        except Exception as e:
            logger.error(f"EdgeTTS تعذر: {e}")
            return SynthesisResult(audio=b"", text=text)

    def unload(self):
        self._available = False


class LahgtnaTTS:
    """TTS باستخدام Lahgtna Chatterbox — on-premise، عربي، GPU، 3 لهجات"""

    DIALECTS = {
        "eg": {"code": "eg", "name": "مصري"},
        "sa": {"code": "sa", "name": "سعودي"},
        "ar": {"code": "ar", "name": "فصحى"},
    }
    MAX_TOKENS_CEILING = 4096
    MIN_TOKENS_FLOOR = 1000
    TOKEN_RATE = 2.5
    TOKEN_BUFFER = 500

    def __init__(self, dialect: str = "eg", repo_src: str = "",
                 ckpt_dir: str = ""):
        self._dialect = dialect
        self._repo_src = repo_src or os.environ.get("ADAM_VOICE_REPO", "")
        self._ckpt_dir = ckpt_dir or os.environ.get("ADAM_VOICE_CKPT", "")
        self._pipeline = None
        self._available = False
        self._sample_rate = 24000
        self._vram_gb = 2.0

    @property
    def available(self) -> bool:
        return self._available

    @property
    def vram_gb(self) -> float:
        return self._vram_gb

    def _calc_max_new_tokens(self, text_len: int) -> int:
        return max(self.MIN_TOKENS_FLOOR, min(self.MAX_TOKENS_CEILING, int(text_len * self.TOKEN_RATE + self.TOKEN_BUFFER)))

    async def load(self) -> bool:
        try:
            import sys, os
            os.chdir(self._repo_src)
            if self._repo_src not in sys.path:
                sys.path.insert(0, self._repo_src)
            from inference import run_pipeline
            self._pipeline = run_pipeline
            # تحميل سريع — يجرب pipeline بنص صغير
            test_path = os.path.join(tempfile.gettempdir(), "lahgtna_test.wav")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._pipeline(
                    text="اختبار", output_path=test_path, dialect=self._dialect,
                    exaggeration=0.5, temperature=0.8, cfg_weight=0.5,
                    ckpt_dir=self._ckpt_dir,
                )
            )
            if os.path.exists(test_path):
                os.remove(test_path)
            self._available = True
            logger.info(f"LahgtnaTTS جاهز — لهجة: {self._dialect} ({self.DIALECTS.get(self._dialect, {}).get('name', '')})")
            return True
        except Exception as e:
            logger.warning(f"LahgtnaTTS تعذر تحميل: {e}")
            self._available = False
            return False

    async def synthesize(self, text: str, language: str = "ar") -> SynthesisResult:
        if not self._available or self._pipeline is None:
            return SynthesisResult(audio=b"", text=text)
        start = time.time()
        dialect = self._dialect
        if language and language.startswith("ar"):
            pass
        try:
            import os, wave
            out_path = os.path.join(tempfile.gettempdir(), f"lahgtna_{int(time.time())}.wav")
            loop = asyncio.get_event_loop()
            text_len = len(text)
            max_tokens = self._calc_max_new_tokens(text_len)
            logger.info(f"LahgtnaTTS: {text_len} حرف → max_new_tokens={max_tokens}")
            result_path = await loop.run_in_executor(
                None,
                lambda: self._pipeline(
                    text=text, output_path=out_path, dialect=dialect,
                    exaggeration=0.5, temperature=0.8, cfg_weight=0.5,
                    ckpt_dir=self._ckpt_dir,
                )
            )
            path = result_path or out_path
            if not os.path.exists(path):
                logger.error("LahgtnaTTS: لم يتم إنشاء ملف الصوت")
                return SynthesisResult(audio=b"", text=text)
            with wave.open(str(path), 'r') as wf:
                frames = wf.readframes(wf.getnframes())
                duration = wf.getnframes() / wf.getframerate()
                sample_rate = wf.getframerate()
            os.remove(path)
            elapsed = time.time() - start
            logger.info(f"LahgtnaTTS: {duration:.1f}ث في {elapsed:.1f}ث — {text_len} حرف")
            return SynthesisResult(
                audio=frames, sample_rate=sample_rate,
                duration_seconds=duration, text=text,
            )
        except Exception as e:
            logger.error(f"LahgtnaTTS تعذر: {e}")
            return SynthesisResult(audio=b"", text=text)

    def unload(self):
        self._pipeline = None
        self._available = False
        import gc; gc.collect()
        try:
            import torch; torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info("LahgtnaTTS مُفرغ من VRAM")


# ═══════════════════════════════════════
# Audio utilities
# ═══════════════════════════════════════

def resample_audio(audio, orig_rate: int, target_rate: int):
    """إعادة عينة الصوت إلى التردد المطلوب"""
    if orig_rate == target_rate:
        return audio
    try:
        _scipy = _load_scipy()
        duration = len(audio) / orig_rate
        target_length = int(duration * target_rate)
        return _scipy.resample(audio, target_length)
    except ImportError:
        ratio = target_rate / orig_rate
        target_len = int(len(audio) * ratio)
        return _load_numpy().interp(
            _load_numpy().linspace(0, len(audio) - 1, target_len),
            _load_numpy().arange(len(audio)),
            audio,
        )


def audio_to_int16(audio) -> bytes:
    """تحويل float32 [-1, 1] إلى int16 PCM bytes"""
    audio = _load_numpy().clip(audio, -1.0, 1.0)
    return (audio * 32767).astype(_load_numpy().int16).tobytes()


def int16_to_float32(audio_bytes: bytes):
    """تحويل int16 PCM bytes إلى float32 [-1, 1]"""
    audio = _load_numpy().frombuffer(audio_bytes, dtype=_load_numpy().int16).astype(_load_numpy().float32) / 32767.0
    return _load_numpy().clip(audio, -1.0, 1.0)


# ═══════════════════════════════════════
# Main Voice Pipeline
# ═══════════════════════════════════════

class VoicePipeline:
    """خط أنابيب الصوت الكامل — VAD → ASR → TTS مع ModelSwapper"""

    MAX_CHUNK_DURATION = 11.0  # 11 ثانية للتقسيم (دراسة FastConformer)
    TARGET_SAMPLE_RATE = 16000

    def __init__(self, temp_dir: str = "temp/audio", tts_backend: str = "edge_tts",
                 tts_dialect: str = "eg", tts_voice: str = "ar-EG-ShakirNeural"):
        self.vad = SileroVAD()
        self.asr = FasterWhisperASR()
        self._tts_backend = tts_backend
        if tts_backend == "lahgtna":
            self.tts = LahgtnaTTS(dialect=tts_dialect)
            logger.info(f"VoicePipeline: TTS = Lahgtna (لهجة: {tts_dialect})")
        else:
            self.tts = EdgeTTS(voice=tts_voice)
            logger.info(f"VoicePipeline: TTS = EdgeTTS ({tts_voice})")

        self._temp_dir = Path(temp_dir)
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self._recording = False
        self._current_buffer: List[_load_numpy().ndarray] = []

    async def load_vad(self) -> bool:
        return await self.vad.load()

    async def load_asr(self) -> bool:
        return await self.asr.load()

    async def load_tts(self) -> bool:
        return await self.tts.load()

    async def unload_asr(self):
        """تفريغ ASR من VRAM"""
        self.asr.unload()
        import gc
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info("ASR مُفرغ من VRAM")

    async def unload_tts(self):
        """تفريغ TTS من VRAM"""
        self.tts.unload()
        import gc
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info("TTS مُفرغ من VRAM")

    # --- Audio format detection & decoding ---

    def _decode_audio(self, audio_data: bytes) -> tuple:
        """كشف تنسيق الصوت وتحويله إلى float32 numpy array + sample rate.
        يدعم: WAV, WebM/Opus (من المتصفح), PCM int16 raw."""
        np = _load_numpy()
        # كشف WAV
        if audio_data[:4] == b'RIFF':
            import wave, io
            try:
                with wave.open(io.BytesIO(audio_data), 'r') as w:
                    sr = w.getframerate()
                    frames = w.readframes(w.getnframes())
                    audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767.0
                    return np.clip(audio, -1.0, 1.0), sr
            except Exception:
                pass
        # كشف WebM (Opus من المتصفح)
        if audio_data[:4] == b'\x1a\x45\xdf\xa3':
            try:
                import pydub
                from io import BytesIO
                seg = pydub.AudioSegment.from_file(BytesIO(audio_data), format="webm")
                seg = seg.set_frame_rate(self.TARGET_SAMPLE_RATE).set_channels(1)
                raw = seg.raw_data
                audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0
                return np.clip(audio, -1.0, 1.0), seg.frame_rate
            except Exception as e:
                logger.warning(f"تعذر فك WebM: {e}")
        # افتراضي: PCM int16 raw
        audio = int16_to_float32(audio_data)
        return audio, self.TARGET_SAMPLE_RATE

    # --- Processing pipeline ---

    async def process_audio(self, audio_data: bytes,
                             sample_rate: int = 16000) -> TranscriptionResult:
        """معالجة صوت كامل → VAD → ASR → نص"""
        audio, actual_rate = self._decode_audio(audio_data)

        # Resample to 16kHz if needed
        if actual_rate != self.TARGET_SAMPLE_RATE:
            audio = resample_audio(audio, actual_rate, self.TARGET_SAMPLE_RATE)

        # VAD — تقسيم الكلام
        segments = await self.vad.detect_speech_segments(audio, self.TARGET_SAMPLE_RATE)

        # ASR — نسخ كل مقطع كلام
        all_text = []
        for seg in segments:
            if not seg["speech"]:
                continue
            start_sample = int(seg["start"] * self.TARGET_SAMPLE_RATE)
            end_sample = int(seg["end"] * self.TARGET_SAMPLE_RATE)
            segment_audio = audio[start_sample:end_sample]

            # تقسيم المقاطع الطويلة (أكثر من 11 ثانية)
            max_samples = int(self.MAX_CHUNK_DURATION * self.TARGET_SAMPLE_RATE)
            if len(segment_audio) > max_samples:
                chunks_text = await self._transcribe_long(segment_audio)
                all_text.extend(chunks_text)
            else:
                result = await self.asr.transcribe(segment_audio)
                if result.text.strip():
                    all_text.append(result.text.strip())

        full_text = " ".join(all_text)
        total_duration = len(audio) / self.TARGET_SAMPLE_RATE

        return TranscriptionResult(
            text=full_text,
            language=self.asr._language if self.asr._language else "ar",
            duration_seconds=total_duration,
            segments=[],
            is_final=True,
        )

    async def _transcribe_long(self, audio: _load_numpy().ndarray) -> List[str]:
        """تقسيم الصوت الطويل إلى أجزاء 11 ثانية ونسخ كل جزء"""
        max_samples = int(self.MAX_CHUNK_DURATION * self.TARGET_SAMPLE_RATE)
        results = []
        for start in range(0, len(audio), max_samples):
            chunk = audio[start:start + max_samples]
            if len(chunk) < self.TARGET_SAMPLE_RATE * 0.5:
                continue
            result = await self.asr.transcribe(chunk)
            if result.text.strip():
                results.append(result.text.strip())
        return results

    async def process_text(self, text: str, language: str = "ar") -> SynthesisResult:
        """توليد صوت من نص → TTS"""
        return await self.tts.synthesize(text, language)

    # --- Recording management ---

    def start_recording(self):
        self._recording = True
        self._current_buffer = []

    def add_audio_chunk(self, chunk: _load_numpy().ndarray):
        if self._recording:
            self._current_buffer.append(chunk)

    def stop_recording(self) -> Optional[_load_numpy().ndarray]:
        self._recording = False
        if not self._current_buffer:
            return None
        audio = _load_numpy().concatenate(self._current_buffer)
        self._current_buffer = []
        return audio

    @property
    def is_recording(self) -> bool:
        return self._recording

    # --- Audio file management ---

    async def save_audio(self, audio_data: bytes, filename: str) -> str:
        """حفظ الصوت في الملف المؤقت مع auto-cleanup قديم"""
        self._cleanup_old_files()

        filepath = self._temp_dir / filename
        with open(filepath, "wb") as f:
            f.write(audio_data)

        logger.info(f"صوت محفوظ: {filepath}")
        return str(filepath)

    def _cleanup_old_files(self, max_age_hours: int = 24):
        """حذف الملفات الأقدم من 24 ساعة"""
        now = time.time()
        cutoff = now - (max_age_hours * 3600)
        for f in self._temp_dir.glob("*"):
            if f.is_file() and f.stat().st_mtime < cutoff:
                try:
                    f.unlink()
                    logger.info(f"حذف صوت قديم: {f.name}")
                except Exception:
                    pass

    async def cleanup(self):
        """تنظيف نهائي"""
        await self.unload_asr()
        await self.unload_tts()
