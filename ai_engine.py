"""AI 分析引擎 — 调用 DeepSeek API 生成比赛分析报告"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass


def _build_prompt(team_a, team_b, a_players, b_players, h2h):
    """构建发给 AI 的提示词"""
    def describe_team(team, players):
        cats = {"star": [], "debut": [], "veteran": [], "absent": []}
        for p in players:
            cat = p["category"]
            if cat in cats:
                cats[cat].append(
                    f"{p['name']}({p['position']}, {p['age']}岁, {p['status']})"
                )
        lines = [
            f"球队：{team['name']} ({team['fifa_code']})",
            f"FIFA排名：#{team['fifa_rank']}" if team["fifa_rank"] else "",
            f"教练：{team['coach'] or '暂无数据'}",
            f"战术风格：{team['style'] or '暂无数据'}",
            f"优势：{team['strengths'] or '暂无数据'}",
            f"短板：{team['weaknesses'] or '暂无数据'}",
            f"明星球员：{', '.join(cats['star']) if cats['star'] else '暂无数据'}",
            f"首次登场新星：{', '.join(cats['debut']) if cats['debut'] else '无'}",
            f"高龄老将：{', '.join(cats['veteran']) if cats['veteran'] else '无'}",
            f"缺席球员：{', '.join(cats['absent']) if cats['absent'] else '无'}",
        ]
        return "\n".join(line for line in lines if line)

    team_a_desc = describe_team(team_a, a_players)
    team_b_desc = describe_team(team_b, b_players)
    h2h_text = h2h["summary"] if h2h else "两队此前未有正式比赛交手记录"

    return f"""你是一位资深足球分析师，正在为2026年世界杯小组赛撰写赛前分析报告。

请根据以下两支球队的真实数据，分析双方各自优劣势。注意：
- 不预测比分和胜负
- 基于给定数据做推理，不编造信息
- 如有球员缺席（退役/伤缺/未入选），在报告中醒目标注
- 用中文输出，专业但可读性强
- 输出格式为HTML片段，用 <div class="report-grid"><div class="report-col">...</div><div class="report-col">...</div></div> 包裹
- 每队的col里包含：h4标题（带球队名和FIFA排名）、简要分析段落、优势和风险各自的ul列表
- 如果两队风格之间存在克制关系（如高位压迫 vs 防守反击），在grid后面加一个 <p class="style-clash"> 说明

除此之外，你还需要在grid后面增加一段 <div class="goal-total-analysis"> 的分析，专门判断本场比赛更可能打出"大比分"（总进球≥3）还是"小比分"（总进球＜3）。判断依据包括但不限于：
- 两队的攻防风格（进攻火力 vs 防守稳固度）
- 关键球员缺席对攻防两端的影响
- 两队近期的进球/失球趋势
- 历史交锋的进球数规律
- 小组赛阶段的策略考量（保守求稳 vs 全力争胜）

输出格式示例：
<div class="goal-total-analysis">
  <h4>📊 大小球分析</h4>
  <p class="goal-prediction">倾向：<strong>大球（总进球≥3）</strong> 或 <strong>小球（总进球＜3）</strong></p>
  <p>简要推理理由...</p>
</div>

【历史交锋】
{h2h_text}

【队伍A — {team_a['name']}】
{team_a_desc}

【队伍B — {team_b['name']}】
{team_b_desc}"""


def generate_match_report(match_id, team_a, team_b, a_players, b_players, h2h):
    """生成AI比赛分析报告。优先读缓存，未命中则调 DeepSeek API，再降级为规则引擎。"""
    from models import get_cached_report, save_report_cache

    # 1. 先查缓存
    cached = get_cached_report(match_id)
    if cached:
        return cached

    # 2. 调 API 或降级
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    report = _generate_with_deepseek(api_key, team_a, team_b, a_players, b_players, h2h) if api_key \
        else _generate_rule_based(team_a, team_b, a_players, b_players, h2h)

    # 3. 写入缓存（下次秒开）
    save_report_cache(match_id, report)
    return report


def _generate_with_deepseek(api_key, team_a, team_b, a_players, b_players, h2h):
    """调用 DeepSeek API"""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        prompt = _build_prompt(team_a, team_b, a_players, b_players, h2h)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一位资深足球分析师。输出专业的赛前分析，使用中文，只返回HTML片段不要markdown包裹。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        html = response.choices[0].message.content
        # 去掉可能的 ```html 包裹
        if html.startswith("```"):
            html = html.split("\n", 1)[-1]
            if html.endswith("```"):
                html = html[:-3]
        return html
    except Exception as e:
        fallback = _generate_rule_based(team_a, team_b, a_players, b_players, h2h)
        return (
            f'<p style="color:#f87171;margin-bottom:12px;">⚠️ DeepSeek API 调用失败（{e}），以下为规则引擎分析：</p>'
            + fallback
        )



def _goal_total_analysis(team_a, team_b, a_players, b_players):
    """规则引擎：大小球预判"""
    score = 0

    def analyze(team, players):
        s = 0
        style = (team.get("style") or "").lower()
        strengths = (team.get("strengths") or "").lower()
        # 进攻风格加分
        if any(kw in style for kw in ["进攻", "压迫", "传控", "冲击", "全攻全守"]):
            s += 1
        if any(kw in strengths for kw in ["火力", "进球", "终结", "冲击力"]):
            s += 1
        # 防守风格减分
        if any(kw in style for kw in ["防守反击", "稳固防守", "稳守", "铁桶"]):
            s -= 1
        if any(kw in strengths for kw in ["防守", "拦截", "铁血"]):
            s -= 1
        # 球星攻击手
        stars = [p for p in players if p["category"] == "star"]
        attackers = [p for p in stars if p["position"] in ("前锋", "中场")]
        s += min(len(attackers), 3) * 0.5
        # 缺席
        for p in players:
            st = (p.get("status") or "")
            if p["category"] == "absent" or "伤" in st or "缺席" in st or "退出" in st:
                if p.get("position") in ("前锋", "中场"):
                    s -= 0.5
                elif p.get("position") == "后卫":
                    s += 0.5
        # FIFA排名
        rank = team.get("fifa_rank")
        if rank and rank < 15:
            s += 0.5
        return s

    score = analyze(team_a, a_players) + analyze(team_b, b_players)

    if score >= 1.5:
        pred = "大球（总进球>=3）"
        confidence = "较高"
        reason = "两队均具备较强的进攻火力和进攻意愿，同时防守端存在一定隐患，比赛节奏可能较快。"
    elif score >= 0.5:
        pred = "大球（总进球>=3）"
        confidence = "中等"
        reason = "综合攻防数据来看进攻方略占优势，具备打出大比分的条件，但存在一定不确定性。"
    elif score >= -0.5:
        pred = "小球（总进球<3）"
        confidence = "中等"
        reason = "两队攻防相对均衡，比赛可能较为胶着，进球数预计不会太多。"
    elif score >= -1.5:
        pred = "小球（总进球<3）"
        confidence = "较高"
        reason = "防守型打法占主导，进攻端创造力有限，加上关键球员缺席，预计比赛节奏偏慢。"
    else:
        pred = "小球（总进球<3）"
        confidence = "高"
        reason = "双方都偏向保守风格，防守组织严密，进攻端缺乏足够的爆破点，大概率陷入沉闷拉锯。"

    return f'''<div class="goal-total-analysis">
  <h4>📊 大小球分析 <span style="font-size:0.75rem;color:#94a3b8;">（规则引擎）</span></h4>
  <p class="goal-prediction">倾向：<strong style="color:{"#f59e0b" if "大球" in pred else "#3b82f6"};font-size:1.1em;">{pred}</strong> <span style="color:#94a3b8;">（置信度：{confidence}）</span></p>
  <p>{reason}</p>
</div>'''

def _generate_rule_based(team_a, team_b, a_players, b_players, h2h):
    """规则引擎降级方案（不依赖API）"""
    def snap(team, players):
        stars = [p for p in players if p["category"] == "star" and "伤" not in p["status"]]
        injuries = [p for p in players if "伤" in p["status"] or "缺席" in p["status"] or "退出" in p["status"] or "未入选" in p["status"]]
        veterans = [p for p in players if p["category"] == "veteran"]
        debuts = [p for p in players if p["category"] == "debut"]
        advs, risks = [], []
        if injuries:
            for inj in injuries:
                risks.append(f'⚠️ {inj["name"]}：{inj["status"]}')
        if veterans:
            risks.append(f'有{len(veterans)}位高龄球员，体能和速度可能在比赛后半段下滑')
        if team["weaknesses"] and team["weaknesses"] != "暂无数据":
            risks.append(f'已知短板：{team["weaknesses"]}')
        if stars:
            names = ", ".join(s["name"] for s in stars[:3])
            advs.append(f"核心球员在阵：{names}等{len(stars)}位主力可出战")
        if team["fifa_rank"] and team["fifa_rank"] < 15:
            advs.append(f"FIFA排名#{team['fifa_rank']}，整体实力占优")
        if not injuries:
            advs.append("目前无伤病困扰，阵容完整度高")
        if team["strengths"] and team["strengths"] != "暂无数据":
            advs.append(f'战术体系：{team["style"] or ""} → {team["strengths"]}')
        if debuts:
            advs.append(f"有{len(debuts)}位新星首次亮相世界杯，可能带来惊喜")
        absentees = [p for p in players if p["category"] == "absent" or "伤" in p["status"] or "缺席" in p["status"] or "退出" in p["status"] or "未入选" in p["status"]]
        return {
            "name": team["name"], "code": team["fifa_code"],
            "rank": team["fifa_rank"], "coach": team["coach"],
            "advs": advs or ["暂无足够数据进行分析"],
            "risks": risks or ["暂无足够数据进行分析"],
            "has_data": bool(team["has_detail"]) if "has_detail" in team.keys() else False,
            "absentees": absentees,
        }

    a = snap(team_a, a_players)
    b = snap(team_b, b_players)
    h2h_text = h2h["summary"] if h2h else "两队此前未有正式比赛交手记录"

    # 关键缺席
    absence_alert = ""
    all_absences = []
    for side, sd in [("🔵", a), ("🔴", b)]:
        for p in sd["absentees"]:
            all_absences.append(
                f'<span style="color:#fbbf24;">{side} {sd["name"]}</span> — '
                f'<strong>{p["name"]}</strong>（{p["status"]}）'
            )
    if all_absences:
        absence_alert = (
            '<div class="absence-alert"><strong>🚨 重要球员缺席</strong><br>'
            + "<br>".join(all_absences)
            + "</div>"
        )

    # 阵容克制
    style_note = ""
    a_style = (team_a["style"] or "") if "style" in team_a.keys() else ""
    b_style = (team_b["style"] or "") if "style" in team_b.keys() else ""
    if "反击" in a_style and "压迫" in b_style:
        style_note = '<p class="style-clash"><strong>⚡ 阵容克制提示：</strong>防守反击型打法可能对高位压迫体系形成一定克制，需关注临场执行。</p>'
    elif "压迫" in a_style and "反击" in b_style:
        style_note = '<p class="style-clash"><strong>⚡ 阵容克制提示：</strong>高位压迫面对防守反击存在被突破的风险，需注意防线身后空间。</p>'

    a_warn = "" if a["has_data"] else '<span style="color:#fbbf24;">（数据待补充）</span>'
    b_warn = "" if b["has_data"] else '<span style="color:#fbbf24;">（数据待补充）</span>'
    goal_total = _goal_total_analysis(team_a, team_b, a_players, b_players)

    return f"""
{absence_alert}
<div class="report-grid">
  <div class="report-col">
    <h4 style="color:#3b82f6;">🔵 {a['name']} ({a['code']}) {a_warn}</h4>
    <p style="margin-bottom:6px;color:#94a3b8;">{h2h_text}</p>
    <p>FIFA排名 #{a['rank'] or '未知'} · 教练 {a['coach'] or '暂无数据'}</p>
    <div class="adv-list"><strong>优势</strong><ul>{''.join(f'<li>{x}</li>' for x in a['advs'])}</ul></div>
    <div class="risk-list"><strong>风险</strong><ul>{''.join(f'<li>{x}</li>' for x in a['risks'])}</ul></div>
  </div>
  <div class="report-col">
    <h4 style="color:#ef4444;">🔴 {b['name']} ({b['code']}) {b_warn}</h4>
    <p>FIFA排名 #{b['rank'] or '未知'} · 教练 {b['coach'] or '暂无数据'}</p>
    <div class="adv-list"><strong>优势</strong><ul>{''.join(f'<li>{x}</li>' for x in b['advs'])}</ul></div>
    <div class="risk-list"><strong>风险</strong><ul>{''.join(f'<li>{x}</li>' for x in b['risks'])}</ul></div>
  </div>
</div>
{style_note}
{goal_total}
<p style="color:#92400e;margin-top:12px;font-size:0.82rem;"><strong>📌 注：</strong>本分析基于知识库数据生成。设置 DEEPSEEK_API_KEY 环境变量可启用 DeepSeek AI 深度分析，提供更专业的战术解读。</p>
"""
