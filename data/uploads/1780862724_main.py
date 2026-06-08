#!/usr/bin/env python3
"""Adam Prism — التوأم الرقمي الشخصي
عين الحارس — Egyptian Arabic Conscious AI

الاستخدام:
  python main.py            # تشغيل السيرفر (افتراضي port 8000)
  python main.py --help     # عرض المساعدة
  python scripts/merge_lora.py  # دمج LoRA (للتطوير فقط)
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from run_api import main as server_main


def main():
    parser = argparse.ArgumentParser(description="Adam Prism — التوأم الرقمي الشخصي")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--mode", choices=["ollama", "lora"], default=None,
                        help="Inference mode (default: from config)")
    args = parser.parse_args()

    if args.host != "0.0.0.0":
        import os
        os.environ["API_HOST"] = args.host
    if args.port != 8000:
        import os
        os.environ["API_PORT"] = str(args.port)
    if args.mode:
        import os
        os.environ["INFERENCE_MODE"] = args.mode

    try:
        asyncio.run(server_main())
    except KeyboardInterrupt:
        print("\n👋 إلى اللقاء")
    except Exception as e:
        print(f"❌ خطأ: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
