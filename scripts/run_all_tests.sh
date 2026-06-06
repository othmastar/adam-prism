#!/bin/bash
# تشغيل الاختبار الشامل لكل الأدوات
echo "============================================"
echo "  أداة الاختبار الشامل — Adam All Tools Test"
echo "============================================"
echo ""

# تأكد إن Flask شغال
if ! curl -sf http://localhost:7860/chat -X POST -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"ping"}]}' > /dev/null 2>&1; then
    echo "⚠️  Flask server مش شغال. Test الـ execution tools هتفشل."
    echo "   شغله بـ: bash adam.sh on"
    echo ""
fi

PYTHONPATH=/mnt/Workspace/python-lib/site-packages:$PYTHONPATH \
python3 /mnt/Workspace/Adam_Prism_Complete_v2/scripts/test_all_tools.py 2>&1
