"""Improved squad verification using club matching"""
import re, html as h, sys

with open('/tmp/espn_wc2026.html', 'r') as f:
    content = f.read()

content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
body = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
text = h.unescape(body.group(1) if body else content)
text = re.sub(r'<[^>]+>', '\n', text)
text = re.sub(r'\n{3,}', '\n\n', text)
text = re.sub(r'[ \t]+', ' ', text)
lines = [l.strip() for l in text.split('\n') if l.strip()]

TEAM_NAMES_ORDERED = [
    ("Mexico", "MEX"), ("South Africa", "RSA"), ("South Korea", "KOR"), ("Czechia", "CZE"),
    ("Canada", "CAN"), ("Bosnia-Herzegovina", "BIH"), ("Qatar", "QAT"), ("Switzerland", "SUI"),
    ("Brazil", "BRA"), ("Morocco", "MAR"), ("Haiti", "HAI"), ("Scotland", "SCO"),
    ("United States", "USA"), ("Paraguay", "PAR"), ("Australia", "AUS"), ("Türkiye", "TUR"),
    ("Germany", "GER"), ("Curacao", "CUW"), ("Ivory Coast", "CIV"), ("Ecuador", "ECU"),
    ("Netherlands", "NED"), ("Japan", "JPN"), ("Sweden", "SWE"), ("Tunisia", "TUN"),
    ("Belgium", "BEL"), ("Egypt", "EGY"), ("Iran", "IRN"), ("New Zealand", "NZL"),
    ("Spain", "ESP"), ("Cape Verde", "CPV"), ("Saudi Arabia", "KSA"), ("Uruguay", "URU"),
    ("France", "FRA"), ("Senegal", "SEN"), ("Iraq", "IRQ"), ("Norway", "NOR"),
    ("Argentina", "ARG"), ("Algeria", "ALG"), ("Austria", "AUT"), ("Jordan", "JOR"),
    ("Portugal", "POR"), ("Congo DR", "COD"), ("Uzbekistan", "UZB"), ("Colombia", "COL"),
    ("England", "ENG"), ("Croatia", "CRO"), ("Ghana", "GHA"), ("Panama", "PAN")
]

TEAM_NAMES_SET = {t[0] for t in TEAM_NAMES_ORDERED}

def extract_espn_squads(lines):
    """Extract player+club pairs per team from ESPN HTML text"""
    teams = {}
    current_team = None
    current_code = None
    players = []

    for i, line in enumerate(lines):
        ls = line.strip()

        # Detect team header
        for tname, tcode in TEAM_NAMES_ORDERED:
            if ls == tname and i+1 < len(lines):
                nxt = lines[i+1].strip()
                if any(kw in nxt for kw in ["Final", "Roster", "squad"]):
                    if current_team:
                        teams[current_code] = {"name": current_team, "players": players}
                    current_team = tname
                    current_code = tcode
                    players = []
                    break

        if not current_team:
            continue

        # Stop at Manager line
        if ls.startswith("Manager:"):
            teams[current_code] = {"name": current_team, "players": players}
            current_team = None
            current_code = None
            players = []
            continue

        # Skip headers
        if ls.rstrip(':') in ("Goalkeepers", "Goalkeepers", "Defenders", "Defenders",
                               "Midfielders", "Midfielders", "Forwards", "Forwards"):
            continue

        # Skip metadata lines
        if any(kw in ls for kw in ["Final", "Roster", "announced", "Manager", "GROUP ",
                                   "JUMP TO", "Open Extended", "Email", "Print", "Manager:"]):
            continue

        # Extract player name and club
        # Format varies: "Name Club" or "Name (Club)" or "Name (Club),"
        cleaned = ls.rstrip(',);]')

        # Skip short fragments
        if len(cleaned) < 5:
            continue
        if cleaned.startswith(')') or cleaned.startswith('],'):
            continue

        # Try to extract name and club
        # Format 1: "Player Name (Club)"
        m = re.match(r'^(.+?)\s*\(([^)]+)\)$', cleaned)
        if m:
            name = m.group(1).strip()
            club = m.group(2).strip()
            if 3 < len(name) < 50:
                players.append((name, club))
                continue

        # Format 2: "Player Name Club" - club on same line without parens
        # Many entries are just club names on their own line after a player
        # Simple heuristic: if line doesn't have parens, it might be a player name
        # But many are just club names. Collect all and pair later.
        words = cleaned.split()
        if 1 <= len(words) <= 4:
            # Could be a player name or a club name
            players.append((cleaned, ""))

    if current_team:
        teams[current_code] = {"name": current_team, "players": players}

    return teams

def normalize_club(name):
    """Normalize club name for comparison"""
    n = name.lower().strip()
    n = re.sub(r'[^\w\s]', '', n)
    # Common club name mappings
    mappings = {
        'real madrid': 'real madrid',
        'barcelona': 'barcelona',
        'manchester city': 'man city',
        'man city': 'man city',
        'manchester united': 'man utd',
        'man utd': 'man utd',
        'arsenal': 'arsenal',
        'chelsea': 'chelsea',
        'liverpool': 'liverpool',
        'tottenham': 'spurs',
        'tottenham hotspur': 'spurs',
        'bayern munich': 'bayern',
        'bayern': 'bayern',
        'borussia dortmund': 'dortmund',
        'paris saint germain': 'psg',
        'psg': 'psg',
        'juventus': 'juve',
        'inter milan': 'inter',
        'inter': 'inter',
        'ac milan': 'milan',
        'milan': 'milan',
        'napoli': 'napoli',
        'atalanta': 'atalanta',
        'as roma': 'roma',
        'roma': 'roma',
        'newcastle': 'newcastle',
        'newcastle united': 'newcastle',
        'aston villa': 'villa',
        'brighton': 'brighton',
        'brighton hove albion': 'brighton',
        'crystal palace': 'palace',
        'west ham': 'west ham',
        'west ham united': 'west ham',
        'wolverhampton': 'wolves',
        'wolverhampton wanderers': 'wolves',
        'nottingham forest': 'forest',
        'everton': 'everton',
        'fulham': 'fulham',
        'bournemouth': 'bournemouth',
        'brentford': 'brentford',
        'leicester': 'leicester',
        'leicester city': 'leicester',
        'southampton': 'southampton',
        'leeds': 'leeds',
        'leeds united': 'leeds',
        'celtic': 'celtic',
        'rangers': 'rangers',
        'benfica': 'benfica',
        'porto': 'porto',
        'sporting': 'sporting',
        'ajax': 'ajax',
        'psv': 'psv',
        'psv eindhoven': 'psv',
        'feyenoord': 'feyenoord',
        'galatasaray': 'galatasaray',
        'fenerbahce': 'fenerbahce',
        'besiktas': 'besiktas',
        'al hilal': 'al hilal',
        'al nassr': 'al nassr',
        'al ahli': 'al ahli',
        'al ittihad': 'al ittihad',
        'inter miami': 'inter miami',
        'lafc': 'lafc',
        'atlanta united': 'atlanta utd',
        'santos': 'santos',
        'flamengo': 'flamengo',
        'palmeiras': 'palmeiras',
        'bayer leverkusen': 'leverkusen',
        'leverkusen': 'leverkusen',
        'rb leipzig': 'leipzig',
        'borussia monchengladbach': 'gladbach',
        'eintracht frankfurt': 'frankfurt',
        'vfb stuttgart': 'stuttgart',
        'stuttgart': 'stuttgart',
        'tsg hoffenheim': 'hoffenheim',
        'hoffenheim': 'hoffenheim',
        'marseille': 'marseille',
        'monaco': 'monaco',
        'lyon': 'lyon',
        'lille': 'lille',
        'nice': 'nice',
        'rennes': 'rennes',
        'strasbourg': 'strasbourg',
        'lens': 'lens',
        'atalanta': 'atalanta',
        'bologna': 'bologna',
        'fiorentina': 'fiorentina',
        'lazio': 'lazio',
        'torino': 'torino',
        'sassuolo': 'sassuolo',
        'genoa': 'genoa',
        'como': 'como',
        'real sociedad': 'real sociedad',
        'real betis': 'real betis',
        'atletico madrid': 'atletico',
        'atlético madrid': 'atletico',
        'athletic club': 'athletic',
        'villarreal': 'villarreal',
        'sevilla': 'sevilla',
        'valencia': 'valencia',
        'girona': 'girona',
    }
    for k, v in mappings.items():
        if k in n:
            return v
    return n

# Load DB
sys.path.insert(0, '/Users/wolong/Desktop/世界杯AI工作流')
from models import PLAYERS, TEAMS

# Build DB player index with club info
db_players = {}
for p in PLAYERS:
    tid, name, cat, age, pos, status, form = p[1], p[2], p[3], p[4], p[5], p[6], p[7]
    for t in TEAMS:
        if t[0] == tid:
            code = t[2]
            if code not in db_players:
                db_players[code] = []
            db_players[code].append({
                "name": name, "cat": cat, "pos": pos, "age": age,
                "status": status, "form": form, "team_id": tid
            })
            break

# Extract ESPN squads
espn = extract_espn_squads(lines)

# Compare
print("=" * 70)
print("48队球员核查报告 (俱乐部+位置交叉比对)")
print("=" * 70)

all_issues = []
verified_count = 0
total_db_players = 0

for tname, code in TEAM_NAMES_ORDERED:
    espn_data = espn.get(code, {})
    espn_players = espn_data.get("players", [])
    db_team = db_players.get(code, [])

    # Build ESPN club index
    espn_clubs = set()
    for pname, pclub in espn_players:
        if pclub:
            espn_clubs.add(normalize_club(pclub))

    # Build ESPN name fragments for matching
    espn_names_lower = [p[0].lower() for p in espn_players]

    for dbp in db_team:
        total_db_players += 1
        if dbp["cat"] == "absent":
            continue  # Skip absent players - they're supposed to be not in squad

        # Try to match by club (from form field)
        form = dbp["form"]
        db_club_hints = set()
        # Extract potential club names from form field
        known_clubs = [
            "皇马", "巴萨", "拜仁", "多特", "利物浦", "阿森纳", "切尔西", "曼联", "曼城",
            "巴黎", "尤文", "国米", "米兰", "那不勒斯", "马竞", "热刺", "纽卡",
            "西汉姆", "狼队", "阿斯顿维拉", "布莱顿", "富勒姆", "水晶宫", "埃弗顿",
            "勒沃库森", "莱比锡", "法兰克福", "霍芬海姆", "斯图加特",
            "马赛", "里昂", "摩纳哥", "里尔", "尼斯", "朗斯", "雷恩",
            "本菲卡", "波尔图", "葡萄牙体育", "阿贾克斯", "埃因霍温", "费耶诺德",
            "利雅得新月", "利雅得胜利", "吉达国民", "迈阿密国际",
            "洛杉矶", "亚特兰大联", "桑托斯", "弗拉门戈", "帕尔梅拉斯",
            "皇马", "巴萨", "拜仁", "多特蒙德", "利物浦", "阿森纳", "切尔西", "曼联", "曼城",
            "巴黎圣日耳曼", "尤文图斯", "国际米兰", "AC米兰", "那不勒斯", "马德里竞技",
            "热刺", "纽卡斯尔", "西汉姆联", "狼队", "塞维利亚", "瓦伦西亚",
            "凯尔特人", "格拉斯哥流浪者", "加拉塔萨雷", "费内巴切", "贝西克塔斯",
            "河床", "博卡青年", "科林蒂安",
            "利雅得新月", "利雅得胜利", "吉达国民",
            "诺丁汉森林", "伯恩茅斯", "布伦特福德", "莱斯特城", "南安普顿",
            "阿尔艾因", "阿尔萨德", "阿尔杜海勒",
            "克雷莫纳", "都灵", "博洛尼亚", "佛罗伦萨", "拉齐奥", "热那亚",
            "皇家社会", "皇家贝蒂斯", "比利亚雷亚尔", "赫罗纳",
            "门兴格拉德巴赫", "柏林联合",
        ]
        for club_hint in known_clubs:
            if club_hint in form:
                db_club_hints.add(club_hint)

        # Chinese club -> English club mapping
        club_cn_to_en = {
            "皇马": "real madrid", "巴萨": "barcelona", "拜仁": "bayern",
            "多特": "dortmund", "多特蒙德": "dortmund",
            "利物浦": "liverpool", "阿森纳": "arsenal", "切尔西": "chelsea",
            "曼联": "man utd", "曼城": "man city",
            "巴黎": "psg", "巴黎圣日耳曼": "psg",
            "尤文": "juve", "尤文图斯": "juve",
            "国米": "inter", "国际米兰": "inter",
            "米兰": "milan", "AC米兰": "milan",
            "那不勒斯": "napoli",
            "马竞": "atletico", "马德里竞技": "atletico",
            "热刺": "spurs", "纽卡": "newcastle", "纽卡斯尔": "newcastle",
            "西汉姆": "west ham", "西汉姆联": "west ham",
            "狼队": "wolves",
            "勒沃库森": "leverkusen", "莱比锡": "leipzig",
            "法兰克福": "frankfurt", "霍芬海姆": "hoffenheim", "斯图加特": "stuttgart",
            "马赛": "marseille", "里昂": "lyon", "摩纳哥": "monaco",
            "里尔": "lille", "尼斯": "nice", "朗斯": "lens", "雷恩": "rennes",
            "本菲卡": "benfica", "波尔图": "porto", "葡萄牙体育": "sporting",
            "阿贾克斯": "ajax", "埃因霍温": "psv", "费耶诺德": "feyenoord",
            "利雅得新月": "al hilal", "利雅得胜利": "al nassr",
            "吉达国民": "al ahli",
            "迈阿密国际": "inter miami",
            "桑托斯": "santos", "弗拉门戈": "flamengo", "帕尔梅拉斯": "palmeiras",
            "凯尔特人": "celtic",
            "加拉塔萨雷": "galatasaray", "费内巴切": "fenerbahce",
            "诺丁汉森林": "forest", "伯恩茅斯": "bournemouth",
            "布伦特福德": "brentford", "莱斯特城": "leicester",
            "富勒姆": "fulham", "水晶宫": "palace", "埃弗顿": "everton",
            "皇家社会": "real sociedad", "皇家贝蒂斯": "real betis",
            "比利亚雷亚尔": "villarreal", "赫罗纳": "girona",
            "塞维利亚": "sevilla", "瓦伦西亚": "valencia",
            "门兴": "gladbach", "门兴格拉德巴赫": "gladbach",
            "罗马": "roma",
        }

        matched = False
        for cn_club in db_club_hints:
            en_club = club_cn_to_en.get(cn_club)
            if en_club and en_club in espn_clubs:
                matched = True
                verified_count += 1
                break

        if not matched:
            # Try direct name matching for very unique names
            db_name_simple = dbp["name"].lower()
            for e_name in espn_names_lower:
                # Check for significant overlap
                if len(db_name_simple) >= 4 and db_name_simple[:4] in e_name:
                    matched = True
                    verified_count += 1
                    break
                if len(db_name_simple) >= 4 and e_name[:4] in db_name_simple:
                    matched = True
                    verified_count += 1
                    break

        if not matched:
            all_issues.append(f"❓ [{code}] {dbp['name']} ({dbp['cat']}, {dbp['pos']}) — 未能匹配ESPN名单 | form: {dbp['form'][:60]}")

# Print results
print(f"\n数据库共有 {total_db_players} 名在队球员（不含absent）")
print(f"成功匹配 {verified_count} 人")
print(f"未能匹配 {len(all_issues)} 人\n")

if all_issues:
    print("⚠️  未能匹配的球员（需要人工核实）：\n")
    for issue in all_issues:
        print(f"  {issue}")

# Also show teams with no ESPN data
print(f"\n--- ESPN数据提取状态 ---")
for tname, code in TEAM_NAMES_ORDERED:
    espn_data = espn.get(code, {})
    n_espn = len(espn_data.get("players", []))
    n_db = len(db_players.get(code, []))
    status = "✅" if n_espn > 0 else "❌ 提取失败"
    print(f"  [{code}] {tname}: ESPN {n_espn}人 | DB {n_db}人 | {status}")
