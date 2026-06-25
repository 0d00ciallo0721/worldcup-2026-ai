"""世界杯AI资讯平台 — Flask 主入口"""
import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template
from models import (
    init_db,
    get_team,
    get_all_teams,
    get_match,
    get_all_matches_sorted,
    get_group_standings,
    get_prediction_for_match,
    CATEGORY_LABELS,
    RANK as FOCUS_CODES,
)
from ai_engine import generate_match_report

app = Flask(__name__)


@app.route("/")
def index():
    # 球队按组归类
    groups = {}
    teams = get_all_teams()
    for t in teams:
        g = t["group_name"]
        if g not in groups:
            groups[g] = []
        groups[g].append(t)

    # 积分榜（从比分动态计算）
    standings = get_group_standings()

    # 全部比赛按组归类，附加比分和预测对比数据
    all_matches = get_all_matches_sorted()
    matches_by_group = {}
    completed_count = 0
    for m in all_matches:
        g = m["group_name"]
        matches_by_group.setdefault(g, []).append(m)

        a_s = m.get("team_a_score")
        b_s = m.get("team_b_score")
        m["is_completed"] = a_s is not None and b_s is not None
        if m["is_completed"]:
            completed_count += 1
            total_goals = a_s + b_s
            ai_pred = get_prediction_for_match(m["id"])
            m["ai_pred"] = ai_pred
            if ai_pred == "大球":
                m["pred_correct"] = (total_goals >= 3)
            elif ai_pred == "小球":
                m["pred_correct"] = (total_goals < 3)
            else:
                m["pred_correct"] = None

    group_names = sorted(matches_by_group.keys())

    return render_template(
        "index.html",
        groups=groups,
        all_matches=all_matches,
        standings=standings,
        matches_by_group=matches_by_group,
        group_names=group_names,
        completed_count=completed_count,
        total_matches=72,
        data_date="2026年6月26日",
    )


@app.route("/team/<int:team_id>")
def team(team_id):
    team_data, players = get_team(team_id)

    if team_data is None:
        return render_template("team.html", team=None, players_by_cat={}, cat_labels=CATEGORY_LABELS), 404

    players_by_cat = {}
    for p in players:
        cat = p["category"]
        if cat not in players_by_cat:
            players_by_cat[cat] = []
        players_by_cat[cat].append(p)

    return render_template(
        "team.html",
        team=team_data,
        players_by_cat=players_by_cat,
        cat_labels=CATEGORY_LABELS,
    )


@app.route("/match/<int:match_id>")
def match(match_id):
    m, a, b, h2h, a_players, b_players = get_match(match_id)

    if m is None:
        return render_template("match.html", match=None), 404

    def classify_players(players):
        result = {}
        for p in players:
            cat = p["category"]
            if cat not in result:
                result[cat] = []
            result[cat].append(p)
        return result

    # ── 比分与预测对比 ──
    a_score = m["team_a_score"]
    b_score = m["team_b_score"]
    is_completed = a_score is not None and b_score is not None
    pred_result = None
    if is_completed:
        total_goals = a_score + b_score
        ai_pred = get_prediction_for_match(match_id)
        if ai_pred == "大球":
            pred_result = {
                "prediction": "大球（总进球≥3）",
                "actual": f"总进球 {total_goals}",
                "correct": total_goals >= 3,
            }
        elif ai_pred == "小球":
            pred_result = {
                "prediction": "小球（总进球＜3）",
                "actual": f"总进球 {total_goals}",
                "correct": total_goals < 3,
            }

    report = generate_match_report(match_id, a, b, a_players, b_players, h2h)
    return render_template(
        "match.html",
        match=m,
        team_a=a,
        team_b=b,
        h2h=h2h,
        a_players_by_cat=classify_players(a_players),
        b_players_by_cat=classify_players(b_players),
        cat_labels=CATEGORY_LABELS,
        report=report,
        is_completed=is_completed,
        pred_result=pred_result,
    )


# ── 启动 ──────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    init_db()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", debug=False, port=port)
