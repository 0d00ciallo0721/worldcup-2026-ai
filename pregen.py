"""预生成所有 72 场比赛的 AI 分析报告缓存"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from models import init_db, get_match, get_cached_report
from ai_engine import generate_match_report

init_db()

total = 72
for match_id in range(1, total + 1):
    if get_cached_report(match_id):
        print(f"[{match_id:02d}/{total}] 已有缓存，跳过")
        continue

    m, a, b, h2h, ap, bp = get_match(match_id)
    if m is None:
        print(f"[{match_id:02d}/{total}] 比赛不存在，跳过")
        continue

    print(f"[{match_id:02d}/{total}] 正在生成: {a['name']} vs {b['name']}...", end=" ", flush=True)
    try:
        report = generate_match_report(match_id, a, b, ap, bp, h2h)
        print(f"✅ ({len(report)}字)")
    except Exception as e:
        print(f"❌ 失败: {e}")

    time.sleep(1)  # 避免请求太快

print("\n🎉 全部比赛报告预生成完成！")
