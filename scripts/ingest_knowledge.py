#!/usr/bin/env python3
"""
Adam Knowledge Ingester — يحقن المعرفة في Qdrant

الاستخدام:
  python3 ingest_knowledge.py                  ← يحقن كل الدفعات
  python3 ingest_knowledge.py --dry-run         ← يعرض بس من غير حفظ
  python3 ingest_knowledge.py --list-collections ← يعرض الكوليكشنز

الصيغة (كل chunk):
{
    "text": "المحتوى الكامل بصيغة آدم: مشكلة → حل → خلاصة → عبرة",
    "category": "ot_attacks | ot_standards | ai_ml | fintech | leadership",
    "source": "اسم المصدر",
    "year": 2026,
    "tags": ["tag1", "tag2"]
}
"""

import sys
import time

QDRANT_URL = "http://localhost:6333"
OLLAMA_URL = "http://localhost:11434"
COLLECTION = "security_guard"

# ═══════════════════════════════════════════════════
#  المعرفة — أول دفعة: هجمات 2025-2026
# ═══════════════════════════════════════════════════

KNOWLEDGE = [
    {
        "text": """🔴 المشكلة: FrostyGoop — أول malware يستهدف أنظمة التدفئة عبر Modbus TCP. في شتاء 2024، هجوم سيبراني على 600 مبنى سكني في Lviv، Ukraine. الحرارة تحت الصفر والمباني من غير تدفئة. الـ malware بيكتب zeros في registers الـ ENCO controller، فبيخلي النظام يعتقد إن درجة الحرارة 0°C، فيفصل التدفئة تماماً.

🟢 الحل التقني: FrostyGoop استغل حقيقة إن Modbus TCP (البروتوكول القياسي في OT من 1979) مش فيه أي authentication أو encryption. أي حد عنده access لـ network يقدر يكتب في أي register. الـ ENCO controllers ما كانتش معمول لها network segmentation كويس — جوه same subnet بتاع الـ IT network. الحل: تطبيق network segmentation صارم (Purdue model)، use Modbus TCP over VPN/TLS، وعمل allowlist للـ IPs المسموح لها تكتب في PLC registers.

📝 الخلاصة لآدم: Modbus TCP عمره 46 سنة ومصمم من غير security — مش bug ده feature من زمن تاني. مسؤولية مهندس OT إنه يعرف إن البروتوكول نفسه مكشوف، ويعزله صح.

🗣️ بصمة آدم: ياعم، البروتوكولات الـ legacy مش bugs — هي كانت صح في زمنها. المشكلة إننا بنستخدمها في 2024 من غير升級. زي ما تحط قفل على باب من كرتون — القفل مش المشكلة، الباب هو المشكلة.

🏷️ بروتوكول: Modbus TCP | قطاع: طاقة/تدفئة | درس: Network Segmentation""",
        "source": "Dragos | Elementsa Analysis 2024",
        "year": 2024,
        "tags": "Modbus TCP, FrostyGoop, Lviv, heating, network_segmentation"
    },
    {
        "text": """🔴 المشكلة: Poland Energy 2025 — أول هجوم منسق على قطاع الطاقة في بولندا. 4 أهداف في وقت واحد: مزارع رياح، محطة CHP، ومصنعين صناعيين. الهجوم استخدم wipers (malware بيمسح البيانات) على IT و OT مع بعض. timing كان في بداية الشتاء — ضغط سياسي + أضرار مادية.

🟢 الحل التقني: الهجوم استخدم نفس الـ TTPs عبر 4 جهات مختلفة — معناه إنه مجموعة واحدة مدعومة من دولة. الـ wipers مسحت VM backups والـ SCADA servers في نفس الوقت، فـ recovery كان صعب. نقطة الاختراق: remote access VPN من غير MFA. الحل: MFA إلزامي لأي remote access للـ OT network، air-gapped backups للـ SCADA configurations، incident response plan مخصص لـ OT (مش copy-paste من IT).

📝 الخلاصة لآدم: الهجمات الـ coordinated على OT بتتطور — مش بس malware، ده حرب هجينة. timing الشتاء مش coincidene، ده pressure tactic.

🗣️ بصمة آدم: الشتوا مش موسم برد بس — في الـ OT security، الشتوا موسم هجمات. الـ heat والـ power أهداف استراتيجية. لو مش عامل MFA على VPN بتاعتك، أنت كده فاتح الباب.

🏷️ Wipers | قطاع: طاقة | درس: Remote Access Security""",
        "source": "CERT Polska Report 2025",
        "year": 2025,
        "tags": "wipers, Poland, coordinated_attack, MFA"
    },
    {
        "text": """🔴 المشكلة: AEMO SCADA Failure 2021 — سوق الطاقة الأسترالي خسر الـ SCADA بالكامل. مش هجوم — software bug. الـ SCADA system المسؤول عن مراقبة كل محطات الطاقة في Eastern Australia وقع لمدة ساعات، والـ operators شغّلوا manual fallback procedures.

🟢 الحل التقني: Software upgrade غيّر behavior في حاجة معينة من غير ما يوثقها — فـ الـ SCADA server عمل crash cascade. الحقيقة المخيفة: لو كان ده هجوم بدل bug، كان ممكن يسبب blackout فعلي. السوق الأسترالي اعتمد على resiliency يدوي — engineers يقرأوا من spreadsheets ويكلموا power stations بالتليفون. الحل: automated failover مع disaster recovery drills منتظمة، لو SCADA وقع الانتقال لـ backup يكون seamless مش manual phone calls.

📝 الخلاصة لآدم: أكبر درس: single point of failure في OT مش الـ hardware — هو الـ software update من غير testing. أي change في OT محتاج change management صارم.

🗣️ بصمة آدم: أكبر كابوس لمهندس OT مش hacker — هو software update يوم جمعة. AEMO عرفت إن hand cranking الـ power grid بالتليفون أصعب من متوقع.

🏷️ SCADA Failure | قطاع: طاقة | درس: Change Management""",
        "source": "AEMO Final Report 2021",
        "year": 2021,
        "tags": "SCADA, AEMO, software_bug, change_management"
    },
    {
        "text": """🔴 المشكلة: TRITON (2017, Petro Rabigh, Saudi Arabia) — هجوم على Safety Instrumented Systems (SIS) في مصفاة بتروكيماويات سعودية. الـ malware استهدف Schneider Triconex SIS — نظام مسؤول عن السلامة (اللي يوقف المصنع لو حصل خطر). لو نجح، كان ممكن يسبب انفجار أو تسرب غاز.

🟢 الحل التقني: TRITON اخترق engineering workstation بتاعة الـ SIS من خلال phishing + persistence على IT network طول 90 يوم من غير اكتشاف. لما حاول يعدل الـ firmware بتاع الـ SIS controller، codes فشل فعطل الـ SIS (تسبب في shutdown اللي تم تشخيصه غلط كـ mechanical failure). الخسارة: $938 مليون + 10 أيام توقف. الحل: SIS لازم يكون air-gapped تماماً عن IT و OT networks، مع separate engineering workstations و separate credentials. أي access لـ SIS يحتاج two-person rule.

📝 الخلاصة لآدم: TRITON علم العالم إن الـ Safety Systems مش safe. قبل 2017، الكل كان فاكر إن SIS منيعة بالعزل. بعد TRITON، أي SIS في العالم اتعاملت كـ attack surface.

🗣️ بصمة آدم: كنت فاكر إن SIS خط أحمر؟ TRITON قالك: لا، هو خط متقطع. 938 مليون دولار عشان تتعلم إن الـ safety systems محتاجة حماية زيها زي production systems.

🏷️ SIS | قطاع: طاقة/بتروكيماويات | درس: Air Gap SIS""",
        "source": "INL CyOTE Case Study | Dragos Analysis",
        "year": 2017,
        "tags": "TRITON, SIS, Schneider, safety_override, air_gap"
    },
    {
        "text": """🔴 المشكلة: Oldsmar Water Treatment 2021 — هacker اخترق محطة معالجة مياه في فلوريدا وحاول يزود نسبة الصوديوم (NaOH) من 100 ppm لـ 11,100 ppm — كمية كافية إنها تسمم آلاف الناس لو فشل الـ operator إنه يلاحظ.

🟢 الحل التقني: الاختراق جاي من TeamViewer مثبت على Windows 7 قديم — shared password، من غير MFA. الـ operator شاف الماوس بتتحرك لوحدها على الشاشة فعرف إن فيه مشكلة وعكس التغيير في ثواني. الحل: ممنوع remote desktop مباشر على OT systems، use jump servers مع MFA و session recording. وممنوع Windows 7 في OT — أي OS end-of-life خطر أمني.

📝 الخلاصة لآدم: Oldsmar مثال صارخ إن البساطة مش أمان. كل ما كان الـ remote access أسهل، كان الاختراق أسهل. الحل مش firewall — الحل هو Zero Trust: no implicit trust for any device or user.

🗣️ بصمة آدم: عامل قفل على باب حديد — وفاتح شباك من غير سلك. TeamViewer على OT وكلمة سر مشتركة — ياعم إحنا بنستدعي الهكرز بجد.

🏷️ Water Treatment | قطاع: مياه | درس: Zero Trust / Remote Access""",
        "source": "INL CyOTE Case Study",
        "year": 2021,
        "tags": "Oldsmar, water_treatment, TeamViewer, zero_trust, remote_access"
    },
    {
        "text": """🔴 المشكلة: Norsk Hydro 2019 — LockerGoga ransomware ضرب شركة الألمنيوم النرويجية العملاقة. 35,000 موظف اضطروا يشتغلوا manual — pen and paper. الخسارة: $71 مليون. لكن القصة إنهم رفضوا يدفعوا الفدية — وقرروا يوقفوا الانتاج بدل ما يدفعوا.

🟢 الحل التقني: الاختراق جاي من IT network — spearphishing email → AD compromise → ransomware spread. الـ OT systems اتعطلت مش لأن الـ ransomware وصلها، لكن لأن الـ IT-OT integration خلت الـ production تعتمد على IT systems. المصنع اختار shutdown الآمن بدل تشغيل unsafe. الحل: IT-OT integration لازم يكون resilient — لو IT وقعت، OT تقدر تشغل standalone على الأقل في minimum viable mode. وعمل backup strategy للـ OT configurations منفصل عن IT.

📝 الخلاصة لآدم: Norsk Hydro قرارهم إنهم ميدفعوش الفدية علم العالم إن integrity أهم من availability في OT. Life > production.

🗣️ بصمة آدم: 71 مليون دولار عشان يقولوا: "مش هنفادي." قرار صعب بس علم العالم إن الـ ethics في OT مش رفاهية — هي أساسية. Life always comes first.

🏷️ Ransomware | قطاع: صناعة | درس: IT-OT Resilience""",
        "source": "INL CyOTE Case Study | Dragos",
        "year": 2019,
        "tags": "Norsk Hydro, LockerGoga, ransomware, IT-OT, ethics"
    },

# ═══════════════════════════════════════════════════
#  المعرفة — الدفعة الثانية: معايير OT
# ═══════════════════════════════════════════════════

    {
        "text": """🔴 المشكلة: IEC 62443 هو المعيار العالمي لأمن أنظمة التحكم الصناعي (IACS). قبل 62443، كل مصنع كان عنده standards خاصة — Siemens عنده حاجة، Rockwell عنده حاجة تانية، Schneider عنده حاجة تالتة. مفيش لغة مشتركة بين مهندسي OT وأمن المعلومات.

🟢 الحل التقني: IEC 62443 قسم الأمن لـ 4 أجزاء:
- الجزء 1: General — مفاهيم أساسية
- الجزء 2: Policies & Procedures — إجراءات آمنة
- الجزء 3: System — متطلبات النظام (الأهم للمهندسين)
- الجزء 4: Component — متطلبات المكونات

الأهم في الجزء 3: نموذج Zones & Conduits. الـ Zone = منطقة أمنية (مثلاً: Zone 1 = PLC network, Zone 2 = HMI network). الـ Conduit = قناة اتصال بين مناطق (مثلاً: Router/Firewall بين Zone 1 و Zone 2). كل Zone ليها Security Level (SL):
- SL 1: حماية ضد هجمات غير مقصودة
- SL 2: حماية ضد هجمات بسيطة
- SL 3: حماية ضد هجمات متقدمة
- SL 4: حماية ضد هجمات دولة

📝 الخلاصة لآدم: IEC 62443 مش standard تقني — هو لغة مشتركة بين مهندس OT ومهندس security. لو عرفت zones/conduits/SL، تقدر تصمم أي شبكة OT آمنة.

🗣️ بصمة آدم: قبل 62443، كل مصنع كان بيكتب الأمن من دماغه — وكانت العواقب وخيمة. دلوقتي عندنا لغة عالمية: حدد zone، اعزلها بـ conduit، حدد SL. بسيطة.

🏷️ IEC 62443 | قطاع: صناعي | درس: Zones/Conduits/SL""",
        "category": "ot_standards",
        "source": "IEC 62443-3-3 | ISA99",
        "year": 2023,
        "tags": "IEC 62443, zones, conduits, security_levels, IACS"
    },
    {
        "text": """🔴 المشكلة: Purdue Model for Control Hierarchy — تقسيم هرمي لشبكة OT من 5 مستويات. المشكلة: الشركات بتوصل Level 3 (Operations) مباشرة بـ Level 0 (Field) من غير segmentation، فلو اخترق IT يوصل لـ PLC.

🟢 الحل التقني: Purdue Model:
- Level 5: Enterprise (IT) — ERP, email, internet
- Level 4: Site Business — scheduling, reporting
- Level 3: Operations — SCADA servers, HMI, historian
- Level 2: Control — PLC, RTU, DCS controllers
- Level 1: Basic Control — sensors, actuators
- Level 0: Process — physical machinery

القاعدة الذهبية: Level 3 و 4 و 5 يتوصلوا عبر DMZ (منطقة منزوعة السلاح). Level 0 و 1 و 2 ما يوصلوش للإنترنت أبداً. أي access لـ Level 0-2 يحتاج jump server مع MFA.

📝 الخلاصة لآدم: Purdue مش مجرد diagram — هو firewall rules. كل خط بين مستويين = firewall rule محدد. لو مش عندك rules واضحة، انت مش مطبق Purdue.

🗣️ بصمة آدم: Purdue Model مش رسمة في PowerPoint — دي دستور الشبكة. Level 5 مع Level 0 من غير DMZ؟ يبقى انت كده عامل bridge للهاكر يدخل من الـ email لـ PLC.

🏷️ Purdue Model | قطاع: صناعي | درس: Network Segmentation""",
        "category": "ot_standards",
        "source": "Purdue Reference Architecture | ISA-95",
        "year": 2020,
        "tags": "Purdue, levels, DMZ, segmentation, ISA-95"
    },
    {
        "text": """🔴 المشكلة: MITRE ATT&CK for ICS — أشهر framework لتصنيف هجمات OT. المشكلة: معظم فرق blue team مش عارفة تستخدمه عملياً.

🟢 الحل التقني: الـ framework مقسم لـ 14 tactic (تكتيكات):
1. Initial Access (T0822) — phishing, external remote service
2. Execution (T0836) — تطبيق الأوامر على controller
3. Persistence (T0830) — البقاء في النظام
4. Privilege Escalation (T0842) — رفع صلاحيات
5. Evasion (T0843) —躲避 detection
6. Discovery (T0846) — استكشاف الشبكة
7. Lateral Movement (T0849) — التحرك بين الأجهزة
8. Collection (T0863) — جمع المعلومات
9. Command & Control (T0869) — C2 server
10. Inhibit Response Function (T0803) — منع الاستجابة
11. Impair Process Control (T0818) — تعطيل التحكم
12. Impact (T0828) — تدمير أو تعطيل

كل tactic ليها techniques محددة (أكثر من 800 technique). مثلاً T0822 (Initial Access) فيها: spearphishing, removable media, external remote service.

📝 الخلاصة لآدم: MITRE ATT&CK مش قائمة قراءة — هو خريطة. لو عرفت threat actor بيستخدم technique إيه، تعرف هيهاجم إزاي قبل ما يضرب.

🗣️ بصمة آدم: الـ MITRE ATT&CK للـ OT زيّ GPS لأمن المعلومات. لو مش عارف الـ TTPs بتاعة المهاجم، أنت بتلف في الدائري.

🏷️ MITRE ATT&CK | قطاع: OT | درس: Threat Intelligence""",
        "category": "ot_standards",
        "source": "MITRE ATT&CK for ICS v15",
        "year": 2025,
        "tags": "MITRE, ATT&CK, ICS, TTPs, threat_intel"
    },

# ═══════════════════════════════════════════════════
#  المعرفة — الدفعة الثالثة: AI/ML عميق
# ═══════════════════════════════════════════════════

    {
        "text": """🔴 المشكلة: تكاليف تدريب LLMs باهظة. Llama 3 8B full fine-tuning يحتاج 120GB VRAM. الحل: LoRA.

🟢 الحل التقني: LoRA (Low-Rank Adaptation) — بدل ما تغير كل weights الـ model (120GB VRAM)، بتضيف matrices صغيرة (rank = 16-128) على layers مختارة. التغييرات بسيطة بس فعالة.
- LoRA rank = حجم المصفوفات الصغيرة. rank أعلى = قدرة تعلم أكبر لكن VRAM أعلى.
- QLoRA: إضافة quantization 4-bit عشان تقلل VRAM أكثر — Llama 3 8B من 120GB → 10GB VRAM.
- الفرق بين LoRA و QLoRA: QLoRA يستخدم NF4 quantization ويخزن الـ LoRA weights في float16.
- التطبيق: Qwen3.5-4B LoRA rank=64 على RTX 3060 12GB شغال ومستقر.

📝 الخلاصة لآدم: لو عاوز تظبط موديل على GPU صغير — LoRA/QLoRA هو الحل. الـ rank يحدد قدرة التعلم. rank 64 توازن بين الجودة والـ VRAM.

🗣️ بصمة آدم: قبل LoRA، تدريب موديل 8B كان عايز 120GB VRAM — 4 GPUs A100. بفضل LoRA، نفس الموديل يشتغل على RTX 3060 12GB. البساطة أقوى.

🏷️ LoRA | قطاع: AI/ML | درس: Fine-tuning Efficiency""",
        "category": "ai_ml",
        "source": "LoRA Paper (Hu et al., ICLR 2022) | QLoRA (Dettmers et al., NeurIPS 2023)",
        "year": 2024,
        "tags": "LoRA, QLoRA, fine-tuning, efficiency, low-rank"
    },
    {
        "text": """🔴 المشكلة: Qwen3.5-4B يستخدم hybrid architecture — 24 SSM layers + 8 Attention layers. معظم الناس مش فاهمين إزاي ده يشتغل.

🟢 الحل التقني: Qwen3.5 يجمع بين:
- Gated DeltaNet (SSM) — 24 layer: Linear-time sequence modeling. يستخدم matrix-valued state [128×128] لكل head. سريع جداً في الـ inference (أقل VRAM من Attention).
- Full Attention — 8 layer (في layers 3,7,11,15,19,23,27,31): يمكن الـ model من رؤية كل الـ sequence. عشان SSM مش قوي في ربط المعلومات البعيدة.
النسبة 3:1 (3 SSM لكل 1 Attention) أثبتت أفضل أداء.

السبب إن الـ PEFT merge (زي merge_and_unload) بيكسر الـ SSM layers — لأن PEFT مش متصمم يتعامل مع hybrid architectures. الحل الوحيد: adapter mode (زي Unsloth).

📝 الخلاصة لآدم: SSM طبقة سريعة وخفيفة للـ local context. Attention طبقة دقيقة للـ global context. الجمع بينهم يخلي الموديل سريع ودقيق.

🗣️ بصمة آدم: Qwen3.5 زي فريق كرة قدم — 24 لاعب سرعة (SSM) و 8 لاعبين استراتيجيين (Attention). PEFT merge يخرب الـ hybrid لأن ميعرفش يتعامل مع نوعين مختلفين من اللاعبين.

🏷️ Qwen3.5 Architecture | قطاع: AI/ML | درس: Hybrid SSM+Attention""",
        "category": "ai_ml",
        "source": "Gated Delta Networks (arXiv:2412.06464) | Qwen3.5 Blog",
        "year": 2026,
        "tags": "Qwen3.5, Gated DeltaNet, SSM, Attention, hybrid"
    },
    {
        "text": """🔴 المشكلة: vLLM ده الحل الأسرع لتشغيل LLMs في production. بيستخدم PagedAttention — تقنية تخلي الـ KV cache management زي virtual memory بالظبط.

🟢 الحل التقني: PagedAttention:
- الـ KV cache (ذاكرة التوليد) بتتقسم لـ blocks صغيرة (pages).
- بدل ما تحجز contiguous memory للـ KV cache كاملة، بتخصص blocks حسب الحاجة.
- النتيجة: استخدام ذاكرة أفضل (24x throughput مقارنة بـ HuggingFace).
- Continuous batching: بدل ما تستنى first request تخلص، بتخلط tokens من requests مختلفة في نفس batch.
- Disaggregated prefill/decode: تفصل مرحلة prefill (حساب أول token) عن decode (بقية tokens) — يخلي الـ serving أسرع.
- Speculative decoding: model صغير يولد أول drafts، الـ big model يتأكد منها — يسرع بدون فقدان جودة.

📝 الخلاصة لآدم: vLLM مش مجرد inference engine — هو OS-level memory management بتاع الـ LLMs. PagedAttention غيّر الطريقة الـ KV cache بتتخصص بيها.

🗣️ بصمة آدم: PagedAttention زي الـ virtual memory في Windows — بدل ما تحجز RAM كامل للتطبيق، تخصص pages حسب الحاجة. الفكرة نفسها لـ KV cache. عبقرية البساطة.

🏷️ vLLM | قطاع: AI/ML | درس: Inference Optimization""",
        "category": "ai_ml",
        "source": "PagedAttention Paper (arXiv:2309.06180, SOSP 2023)",
        "year": 2024,
        "tags": "vLLM, PagedAttention, continuous_batching, inference"
    },

# ═══════════════════════════════════════════════════
#  المعرفة — الدفعة الرابعة: التمويل الإسلامي
# ═══════════════════════════════════════════════════

    {
        "text": """🔴 المشكلة: التمويل التقليدي قائم على الفائدة (Riba) — وهي محرمة في الشريعة الإسلامية. البنوك التقليدية بتقرض بفائدة، ودي مشكلة للمسلمين اللي عاوزين خدمات مصرفية متوافقة مع الشريعة.
🟢 الحل التقني: التمويل الإسلامي بيستخدم عقود بديلة:
- المضاربة (Mudarabah): شراكة بين صاحب رأس المال (رب المال) والمُضارب (اللي بيدير المشروع). الأرباح تتقسم حسب نسبة متفق عليها، الخسارة على صاحب رأس المال فقط.
- المشاركة (Musharakah): شراكة بين طرفين أو أكثر كلهم يساهموا برأس المال ويتقاسموا الربح والخسارة.
- المرابحة (Murabaha): البنك يشتري السلعة ويبيعها للعميل بسعر أعلى — دفعة واحدة أو أقساط. مش فائدة، ده ربح على بيع حقيقى.
- الإجارة (Ijarah): تأجير أصل (زي عربية أو عقار) مقابل أقساط إيجارية — زي leasing بالظبط.
📝 الخلاصة لآدم: التمويل الإسلامي مش مجرد "حلال" — هو نظام مالي متكامل قائم على المشاركة في الربح والخسارة مش على الفائدة. المضاربة والمشاركة هما أساس الـ Islamic banking في الخليج.
🗣️ بصمة آدم: الفرق بين البنك التقليدي والبنك الإسلامي: الأول يقولك "هقرضك بفايدة"، التاني يقولك "نشارك في الربح والخسارة". الأول عاوز يضمن مكسبه، التاني يشاركك النتيجة. فرق فلسفي قبل ما يكون مالي.

🏷️ التمويل الإسلامي | قطاع: Fintech | درس: Islamic Finance Basics""",
        "category": "fintech",
        "source": "AAOIFI Standards | SAMA Islamic Banking Guidelines",
        "year": 2025,
        "tags": "islamic_finance, mudarabah, musharakah, murabaha, ijarah, riba"
    },
    {
        "text": """🔴 المشكلة: سوق الصكوك (Sukuk) في السعودية تجاوز 600 مليار ريال — لكن كتير من المستثمرين مش فاهمين الفرق بين الصكوك والسندات التقليدية.
🟢 الحل التقني: الصكوك (Sukuk) = شهادات ملكية في أصل أو مشروع. الفرق عن السندات: السند = دين بفائدة، الصك = ملكية في أصل. في مايو 2026، شركة Intelligent Oud Trading Company أطلقت أول إصدار صكوك بقيمة 50 مليون ريال ضمن برنامج 300 مليون ريال، بعائد 10.50%، بإطار المضاربة. سوق الصكوك في الخليج بلغ 55 مليار دولار في الربع الأول من 2026 وحده.
📝 الخلاصة لآدم: الصكوك هي البديل الإسلامي للسندات. المستثمر بيمتلك جزء من الأصل مش بيقرض البنك. العائد مش فائدة — هو ربح من الأصل نفسه.
🗣️ بصمة آدم: السند: "أقرضك 1000، ترد 1100." الصك: "نشتري العقار ده مع بعض، نأجره، نقسم الإيجار." الأولى دين، التانية شراكة — فرق جوهري.

🏷️ صكوك | قطاع: Fintech | درس: Sukuk vs Bonds""",
        "category": "fintech",
        "source": "SAMA | Saudi Stock Exchange (Tadawul) Data 2025-2026",
        "year": 2026,
        "tags": "sukuk, bonds, islamic_finance, Tadawul, capital_market"
    },
    {
        "text": """🔴 المشكلة: التكافل (Takaful) — البديل الإسلامي للتأمين التجاري — مش مفهوم كويس في المنطقة. كتير بيعتبره مجرد "تأمين بحلة دينية".
🟢 الحل التقني: التكافل مبني على التعاون مش على بيع وشراء الخطر:
- التأمين التقليدي: شركة تبيع "حماية" — لو حصل حادثة، تدفع. ده بيع للخطر (Gharar) — محرم.
- التكافل: المشتركين يتبرعوا لصندوق مشترك. لو حصل حادثة لواحد، الصندوق يعوضه. الشركة تدير الصندوق مش تبيع حماية.
مثال: سلامة للتكافل (الإمارات) أكملت إعادة هيكلة 456 مليون درهم في 2026. سوق التكافل العالمي بيزيد 10-15% سنوياً في الخليج.
📝 الخلاصة لآدم: التكافل = تأمين تعاوني. الفرق الجوهري: في التأمين التقليدي بتشتري "حماية" مبنية على العقد. في التكافل بتتبرع لصندوق عشان تساعد غيرك ويساعدوك.
🗣️ بصمة آدم: التكافل زي "كلنا في الهوى سوا" — لما تحصل حادثة لواحد فينا، كلنا بنشارك في تعويضه. مش بنشتري حماية من شركة، بنشارك في صندوق عشان نحمي بعض.

🏷️ تكافل | قطاع: Fintech | درس: Takaful Insurance""",
        "category": "fintech",
        "source": "Salamah Takaful Annual Report 2026 | GCC Insurance Reports",
        "year": 2026,
        "tags": "takaful, insurance, islamic_finance, cooperative, GCC"
    },

# ═══════════════════════════════════════════════════
#  المعرفة — الدفعة الخامسة: المدفوعات الرقمية
# ═══════════════════════════════════════════════════

    {
        "text": """🔴 المشكلة: المدفوعات الرقمية في السعودية وصلت 85% من معاملات التجزئة في 2025 — لكن التحول السريع ده خلّى فجوة في الأمن والتنظيم.
🟢 الحل التقني: السعودية بقت واحدة من أعلى دول العالم في المدفوعات الإلكترونية بفضل:
- شبكة مدى (MADA): بتعالج 8 مليار معاملة سنوياً عبر 1.4 مليون نقطة بيع. كل POS في السعودية يدعم مدى.
- Apple Pay: متاح من 2019، متكامل مع مدى مباشرة، بيعالج مئات الملايين من المعاملات سنوياً.
- SAMA (البنك المركزي السعودي): مشرف على كل أنظمة الدفع، أصدر إطار محدث 2026 للإشراف على أنظمة الدفع ومشغليها، يشمل 18 من 24 مبدأ من PFMI الدولية.
📝 الخلاصة لآدم: السعودية في ثورة مدفوعات — 85% يعني إن النقد بقى أقلية. لكن مع التحول السريع، الأمن والتنظيم هما التحدي الأكبر.
🗣️ بصمة آدم: في 2015، 85% من السعوديين كانوا بيدفعوا كاش — مفيش Apple Pay، ولا مدى واسعة. في 2025، 85% من المعاملات إلكتروني. عشر سنين قلبوا المعادلة. عبقرية التبني السريع مع تنظيم قوي.

🏷️ مدفوعات رقمية | قطاع: Fintech | درس: Saudi Digital Payments""",
        "category": "fintech",
        "source": "SAMA Annual Report 2025 | MADA Statistics 2025",
        "year": 2025,
        "tags": "digital_payments, MADA, ApplePay, SAMA, KSA_Saudi"
    },
    {
        "text": """🔴 المشكلة: STC Pay اللي بدأت كـ fintech شركة اتحولت لـ STC Bank — أول بنك رقمي بالكامل في السعودية. الرحلة من 2018 لـ 2025 مهمة لفهم مستقبل الـ digital banking.
🟢 الحل التقني: STC Pay اتأسست في 2018 كأول شركة تقنية مالية مرخصة من SAMA. وصلت لأكثر من 12 مليون مستخدم مسجل. بعدها تحولت لـ STC Bank — بنك رقمي بالكامل متوافق مع الشريعة. النمو: 23-24% سنوياً في المستخدمين النشطين. نموذج STC Bank مختلف عن البنوك التقليدية: مفيش فروع، كل حاجة عبر التطبيق، رسوم أقل، سرعة أعلى.
📝 الخلاصة لآدم: STC Bank نموذج حقيقي للـ digital banking في الخليج. الرحلة من شركة اتصالات → fintech → بنك كامل بتظهر إن الحدود بين telco و banking بتختفي.
🗣️ بصمة آدم: STC بدأت شركة اتصالات — دلوقتي بقى عندها بنك برقم 12 مليون مستخدم. يبقى التقليدي مش safe. التحول الرقمي مش بس في التكنولوجيا — هو في إعادة تعريف إيه معناه "بنك" أصلاً.

🏷️ STC Bank | قطاع: Fintech | درس: Digital Banking Transformation""",
        "category": "fintech",
        "source": "STC Bank Reports | SAMA Fintech Licensing Data 2025",
        "year": 2025,
        "tags": "STC_Pay, STC_Bank, digital_banking, fintech, KSA"
    },
    {
        "text": """🔴 المشكلة: Open Banking (الخدمات المصرفية المفتوحة) في السعودية — SAMA أطلق أول إطار تنظيمي رسمي في 26 مارس 2026 بعد 4 سنين تجربة.
🟢 الحل التقني: Open Banking معناه إن البنك يفتح بيانات العميل (بموافقته) لشركات fintech عشان تقدم خدمات أفضل. SAMA طبقته على مرحلتين:
- المرحلة الأولى (2023): خدمات معلومات الحسابات AIS — تقدر تشوف أرصدة كل حساباتك في تطبيق واحد.
- المرحلة الثانية (فبراير 2024): خدمات بدء الدفع PIS — تقدر تدفع من حسابك في بنك مباشرة من تطبيق fintech.
8 مارس 2026: SAMA أصدر إطار محدث للإشراف على أنظمة الدفع، يشمل متطلبات الحوكمة، إدارة المخاطر، والأمن السيبراني — 18 من 24 مبدأ PFMI.
📝 الخلاصة لآدم: Open Banking في السعودية مش مجرد فتح بيانات — هو نقلة in ecosystem الخدمات المالية. fintechs بقى عندها access رسمي لبيانات البنوك.
🗣️ بصمة آدم: قبل Open Banking، كل بنك كان جزيرة — بياناته مقفولة. بعد Open Banking، البنوك بقوا منصة للتطبيقات المالية. المستقبل: مش بنك في جيبك — كل الخدمات المالية في تطبيق واحد.

🏷️ Open Banking | قطاع: Fintech | درس: SAMA Open Banking Framework""",
        "category": "fintech",
        "source": "SAMA Open Banking Regulations 2023-2026 | PFMI Framework",
        "year": 2026,
        "tags": "open_banking, SAMA, AIS, PIS, fintech_regulation"
    },

# ═══════════════════════════════════════════════════
#  المعرفة — الدفعة السادسة: القيادة التنفيذية والحوكمة
# ═══════════════════════════════════════════════════

    {
        "text": """🔴 المشكلة: 49% من CEOs في الشرق الأوسط يعتبروا المخاطر السيبرانية أكبر تحدٍ في 2026 — بس 58% بس اللي واثقين إنهم يقدرون يديروها. الفجوة بين الوعي والجاهزية خطيرة.
🟢 الحل التقني: مسح Heidrick & Struggles 2026 لـ 148 قائد في المنطقة أظهر:
- 80% من المؤسسات بتخطط تزود ميزانية الأمن السيبراني في 2026.
- ربعهم يتوقع زيادة 11% أو أكثر.
- 50% من CISOs في المنطقة يقدموا تقارير مباشرة للـ CEO.
التحول: الأمن السيبراني مش بس "حماية من الهكرز" — هو ممكن استراتيجي للأعمال. PWC Digital Trust Insights: 50% من CISOs يقدمون رؤاهم مباشرة للـ CEO، واجتماعات منتظمة مع مجلس الإدارة.
📝 الخلاصة لآدم: الـ CEO الجيد مش يسأل "هل احنا آمنين؟" — يسأل "هل عندنا visibility كافية على المخاطر؟" الفرق بين السؤالين هو الفرق بين security theatre و security حقيقي.
🗣️ بصمة آدم: كنت فاكر إن CEO مشغول بالـ revenue مش بالـ CVEs. بس الأرقام بتقول حاجة تانية: 80% عاوزين يزودوا ميزانية الأمن. يعني الـ CEOs صحوا — دلوقتي دورنا كـ CISOs إننا نترجم المخاطر التقنية لقرارات أعمال.

🏷️ Cyber Governance | قطاع: Leadership | درس: CEO Cybersecurity Awareness""",
        "category": "leadership",
        "source": "Heidrick & Struggles CEO Survey 2026 | PWC Digital Trust Insights 2026",
        "year": 2026,
        "tags": "cyber_governance, CEO, CISO, board_management, middle_east"
    },
    {
        "text": """🔴 المشكلة: 47% من قادة المنطقة يعتبروا الذكاء الاصطناعي تحدٍ رئيسي في 2026 — أعلى نسبة عالمياً. بس 36% بس اللي واثقين من قدرتهم على إدارة مخاطر الـ AI. فجوة حوكمة خطيرة.
🟢 الحل التقني: المنطقة عندها استثمارات ضخمة في AI — الإمارات والسعودية في المقدمة. الإمارات بتصدى لأكثر من 50,000 هجوم إلكتروني يومياً. لكن حوكمة AI لسه ورا:
- فرق كبير بين الاستثمار في AI والاستعداد لمخاطره.
- 98% من CEOs الإمارات و 100% السعودية يعتبروا الأمن السيبراني ممكن استراتيجي — لكن 23% (الإمارات) و 30% (السعودية) عندهم معرفة عميقة بالمخاطر المتطورة.
- توصية: إنشاء لجنة حوكمة AI في مجلس الإدارة، وضع إطار لـ AI ethics، وتدريب القادة على فهم مخاطر AI.
📝 الخلاصة لآدم: الاستثمار في AI من غير حوكمة = سباق من غير فرامل. المنطقة عندها الإرادة والموارد — بس حوكمة AI محتاج نظام واضح عشان يسبق المخاطر مش يتفاجئ بيها.
🗣️ بصمة آدم: 47% شايفين AI تحدي — 36% بس مستعدين. الفرق 11% ده هو فجوة الحوكمة. زي ما بنشتري أقوى سيارة وننسى نحط فرامل. الحوكمة مش بيروقراطية — هي الـ ABS بتاع الـ AI.

🏷️ AI Governance | قطاع: Leadership | درس: Board-Level AI Risk Management""",
        "category": "leadership",
        "source": "Heidrick & Struggles 2026 | PWC Digital Trust Insights 2026 | Accenture CEO Studies",
        "year": 2026,
        "tags": "AI_governance, board_oversight, AI_risk, middle_east, digital_trust"
    },
]

import httpx

def get_embedding(text: str) -> list:
    r = httpx.post(f"{OLLAMA_URL}/api/embeddings", json={
        "model": "nomic-embed-text",
        "prompt": text
    }, timeout=30)
    r.raise_for_status()
    return r.json()["embedding"]

def collection_exists(name: str) -> bool:
    r = httpx.get(f"{QDRANT_URL}/collections", timeout=10)
    cols = [c["name"] for c in r.json()["result"]["collections"]]
    return name in cols

def store_point(text: str, embedding: list, payload: dict):
    pid = str(hash(text))[:32]
    r = httpx.put(
        f"{QDRANT_URL}/collections/{COLLECTION}/points",
        json={
            "points": [{
                "id": abs(hash(text)),
                "vector": embedding,
                "payload": payload
            }]
        },
        timeout=30
    )
    r.raise_for_status()
    return True

def main():
    dry_run = "--dry-run" in sys.argv

    if "--list-collections" in sys.argv:
        r = httpx.get(f"{QDRANT_URL}/collections", timeout=10)
        cols = r.json()["result"]["collections"]
        print("📦 Qdrant Collections:")
        for c in cols:
            cr = httpx.get(f"{QDRANT_URL}/collections/{c['name']}", timeout=10)
            pts = cr.json()["result"]["points_count"]
            print(f"  {c['name']}: {pts} points")
        return

    ensure_collection()

    print(f"Ingesting {len(KNOWLEDGE)} chunks into '{COLLECTION}'...")
    for item in KNOWLEDGE:
        text = item["text"]
        tags = item.get("tags", "")
        source = item.get("source", "Adam Knowledge Base 2026")

        embedding = get_embedding(text)

        payload = {
            "text": text,
            "category": item.get("category", "ot_attacks"),
            "source": source,
            "tags": tags,
            "ingested": time.strftime("%Y-%m-%d"),
            "year": item.get("year", 2026),
        }

        if dry_run:
            print("\n📄 Chunk (dry run):")
            print("  Category: ot_attacks")
            print(f"  Source: {source}")
            print(f"  Tags: {tags}")
            print(f"  Text preview: {text[:100]}...")
            print(f"  Embedding dim: {len(embedding)}")
        else:
            store_point(text, embedding, payload)
            print(f"  ✅ Stored: {text[:60]}...")

    print(f"\n{'✅ DRY RUN' if dry_run else '✅ Done'} — {len(KNOWLEDGE)} chunks")

def ensure_collection():
    """تأكد إن collection موجودة"""
    if collection_exists(COLLECTION):
        print(f"Collection '{COLLECTION}' موجودة")
        return

    print(f"Collection '{COLLECTION}' مش موجودة — هنعملها...")
    r = httpx.put(
        f"{QDRANT_URL}/collections/{COLLECTION}",
        json={
            "vectors": {
                "size": 768,
                "distance": "Cosine"
            }
        },
        timeout=10
    )
    if r.status_code in (200, 201):
        print(f"  ✅ Collection '{COLLECTION}' اتعملت")
    else:
        print(f"  ❌ فشل إنشاء collection: {r.text}")
        sys.exit(1)

if __name__ == "__main__":
    if "--list-collections" not in sys.argv:
        # Check Qdrant and Ollama first
        try:
            r = httpx.get(f"{QDRANT_URL}/", timeout=5)
        except Exception:
            print("⚠️ Qdrant مش شغال. شغله بـ: bash adam.sh on")
            sys.exit(1)
        try:
            r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        except Exception:
            print("⚠️ Ollama مش شغال")
            sys.exit(1)
    main()
