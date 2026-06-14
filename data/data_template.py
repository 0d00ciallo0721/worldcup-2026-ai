# 真实数据模板 — 按此格式填入2026世界杯真实数据后运行 python3 data/data_template.py 即可写入
TEAMS = [
    # (id, name, fifa_code, group, fifa_rank, coach, style, strengths, weaknesses)
    (1, "Argentina", "ARG", "A", 1, "Lionel Scaloni", "控球进攻", "...", "..."),
    # ... 添加更多球队
]
PLAYERS = [
    # (id, team_id, name, category, age, position, status, recent_form)
    # category: star / debut / veteran / absent
    (1, 1, "Lionel Messi", "veteran", 38, "FW", "高龄但仍首发", "..."),
    # ... 添加更多球员
]
MATCHES = [
    # (id, team_a_id, team_b_id, match_date, venue, group)
    (1, 1, 2, "2026-06-11 20:00", "...", "A"),
]
H2H = [
    # (id, team_a_id, team_b_id, summary)
    (1, 1, 2, "..."),
]
print("将以上数据替换为真实数据后运行: python3 data/data_template.py")
