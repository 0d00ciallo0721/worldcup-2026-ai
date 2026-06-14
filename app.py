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

    # 全部比赛按时间排序
    all_matches = get_all_matches_sorted()

    return render_template(
        "index.html",
        groups=groups,
        all_matches=all_matches,
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
    )


# ── 启动 ──────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    init_db()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", debug=False, port=port)
