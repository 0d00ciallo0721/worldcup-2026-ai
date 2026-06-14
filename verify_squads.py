"""Manually map DB Chinese names to ESPN English names for verification"""
import sys, re
sys.path.insert(0, '/Users/wolong/Desktop/世界杯AI工作流')
from models import PLAYERS, TEAMS

# ★★★ MANUAL NAME MAPPING: DB Chinese name -> ESPN English name keyword ★★★
# This is the authoritative cross-reference
NAME_MAP = {
    # Argentina
    "利昂内尔·梅西": "Messi",
    "劳塔罗·马丁内斯": "Lautaro",
    "恩佐·费尔南德斯": "Enzo",
    "埃米利亚诺·马丁内斯": "Emiliano",
    "胡利安·阿尔瓦雷斯": "Julián",
    "亚历克西斯·麦卡利斯特": "Mac Allister",
    "罗德里戈·德保罗": "De Paul",
    # Brazil
    "维尼修斯·儒尼奥尔": "Vinícius",
    "内马尔": "Neymar",
    "恩德里克": "Endrick",
    "拉菲尼亚": "Raphinha",
    "阿利松": "Alisson",
    "布鲁诺·吉马良斯": "Bruno Guimarães",
    "加布里埃尔·马丁内利": "Martinelli",
    "卡塞米罗": "Casemiro",
    # France
    "基利安·姆巴佩": "Mbappé",
    "奥斯曼·登贝莱": "Dembélé",
    "奥雷利安·楚阿梅尼": "Tchouaméni",
    "威廉·萨利巴": "Saliba",
    "恩戈洛·坎特": "Kanté",
    # England
    "哈里·凯恩": "Kane",
    "祖德·贝林厄姆": "Bellingham",
    "布卡约·萨卡": "Saka",
    "德克兰·赖斯": "Rice",
    # Germany
    "贾马尔·穆夏拉": "Musiala",
    "弗洛里安·维尔茨": "Wirtz",
    "凯·哈弗茨": "Havertz",
    "约书亚·基米希": "Kimmich",
    "曼努埃尔·诺伊尔": "Neuer",
    # Spain
    "拉明·亚马尔": "Yamal",
    "佩德里": "Pedri",
    "尼科·威廉姆斯": "Nico Williams",
    # Portugal
    "克里斯蒂亚诺·罗纳尔多": "Ronaldo",
    "布鲁诺·费尔南德斯": "Bruno Fernandes",
    "贝尔纳多·席尔瓦": "Bernardo Silva",
    "拉斐尔·莱奥": "Leão",
    # Netherlands
    "维吉尔·范戴克": "van Dijk",
    "弗伦基·德容": "de Jong",
    "科迪·加克波": "Gakpo",
    # Belgium
    "凯文·德布劳内": "De Bruyne",
    "蒂博·库尔图瓦": "Courtois",
    "罗梅卢·卢卡库": "Lukaku",
    "杰雷米·多库": "Doku",
    # Croatia
    "卢卡·莫德里奇": "Modric",
    "约什科·格瓦迪奥尔": "Gvardiol",
    "马特奥·科瓦契奇": "Kovacic",
    # Uruguay
    "费德里科·巴尔韦德": "Valverde",
    "达尔文·努涅斯": "Darwin",
    "罗纳德·阿劳霍": "Araújo",
    # Mexico
    "劳尔·希门尼斯": "Jiménez",
    "埃德森·阿尔瓦雷斯": "Edson",
    "吉列尔莫·奥乔亚": "Ochoa",
    "吉尔伯托·莫拉": "Mora",
    # USA
    "克里斯蒂安·普利西奇": "Pulisic",
    "福拉林·巴洛贡": "Balogun",
    "韦斯顿·麦肯尼": "McKennie",
    # Canada
    "阿方索·戴维斯": "Davies",
    "乔纳森·戴维": "Jonathan David",
    "斯蒂芬·尤斯塔基奥": "Eustáquio",
    # Japan
    "久保建英": "Kubo",
    "三笘薰": "Mitoma",
    "远藤航": "Endo",
    # South Korea
    "孙兴慜": "Son",
    "金玟哉": "Kim Min",
    "李刚仁": "Lee Kang",
    "黄喜灿": "Hwang Hee",
    # Morocco
    "阿什拉夫·哈基米": "Hakimi",
    "布拉希姆·迪亚兹": "Brahim",
    "亚辛·布努": "Bounou",
    # Senegal
    "萨迪奥·马内": "Mané",
    "卡利杜·库利巴利": "Koulibaly",
    "尼古拉斯·杰克逊": "Jackson",
    # Egypt
    "穆罕默德·萨拉赫": "Salah",
    "奥马尔·马尔穆什": "Marmoush",
    # Norway
    "埃尔林·哈兰德": "Haaland",
    "马丁·厄德高": "Ødegaard",
    "亚历山大·索尔洛特": "Sørloth",
    # Sweden
    "维克托·哲凯赖什": "Gyökeres",
    "亚历山大·伊萨克": "Isak",
    # Colombia
    "路易斯·迪亚斯": "Luis Díaz",
    "哈梅斯·罗德里格斯": "James",
    # Switzerland
    "格拉尼特·扎卡": "Xhaka",
    "曼努埃尔·阿坎吉": "Akanji",
    "格雷戈尔·科贝尔": "Kobel",
    # Scotland
    "安迪·罗伯逊": "Robertson",
    "约翰·麦金": "McGinn",
    "斯科特·麦克托米奈": "McTominay",
    # Czechia
    "托马斯·绍切克": "Soucek",
    "帕特里克·希克": "Schick",
    "弗拉迪米尔·曹法尔": "Coufal",
    # Australia
    "哈里·苏塔尔": "Souttar",
    "马修·瑞安": "Ryan",
    "内斯托里·伊兰昆达": "Irankunda",
    # South Africa
    "罗恩温·威廉姆斯": "Ronwen",
    "莱尔·福斯特": "Foster",
    "雷勒博希莱·莫福肯": "Mofokeng",
    # Qatar
    "阿克拉姆·阿菲夫": "Afif",
    "阿尔莫埃兹·阿里": "Almoez",
    # Turkey
    "阿尔达·居莱尔": "Güler",
    "凯南·伊尔迪兹": "Yildiz",
    "哈坎·恰尔汗奥卢": "Calhanoglu",
    # Bosnia
    "埃丁·哲科": "Dzeko",
    "塞亚德·科拉西纳茨": "Kolasinac",
    # Paraguay
    "米格尔·阿尔米隆": "Almirón",
    "胡里奥·恩西索": "Enciso",
    # Ecuador
    "莫伊塞斯·凯塞多": "Caicedo",
    "皮耶罗·因卡皮耶": "Hincapié",
    "恩纳·瓦伦西亚": "Enner Valencia",
    # Ivory Coast
    "弗兰克·凯西": "Kessié",
    "阿马德·迪亚洛": "Amad",
    "埃文·恩迪卡": "Ndicka",
    # Ghana
    "托马斯·帕尔特伊": "Partey",
    "安托万·塞梅尼奥": "Semenyo",
    # Tunisia
    "汉尼拔·梅布里": "Hannibal",
    "埃利斯·斯希里": "Skhiri",
    # Algeria
    "里亚德·马赫雷斯": "Mahrez",
    "阿明·古伊里": "Gouiri",
    # Austria
    "大卫·阿拉巴": "Alaba",
    "马塞尔·萨比策": "Sabitzer",
    # Congo DR
    "万-比萨卡": "Wan-Bissaka",
    "尚塞尔·姆本巴": "Mbemba",
    # New Zealand
    "克里斯·伍德": "Wood",
    "里贝拉托·卡卡塞": "Cacace",
    # Iran
    "迈赫迪·塔雷米": "Taremi",
    "阿里雷扎·贾汉巴赫什": "Jahanbakhsh",
    # Iraq
    "艾曼·侯赛因": "Aymen",
    "齐达内·伊克巴尔": "Iqbal",
    # Saudi Arabia
    "萨勒姆·多萨里": "Dawsari",
    # Cape Verde
    "瑞恩·门德斯": "Mendes",
    # Haiti
    "杜肯斯·纳松": "Nazon",
    "让-里克内·贝尔加尔德": "Bellegarde",
    # Curacao
    "里切德利·巴佐尔": "Bazoer",
    "尤尔根·洛卡迪亚": "Locadia",
    # Uzbekistan
    "埃尔多尔·绍穆罗多夫": "Shomurodov",
    # Jordan
    "穆萨·塔马里": "Tamari",
}

# Load ESPN data
with open('/tmp/espn_wc2026.html', 'r') as f:
    content = f.read()

import html as h
content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
body = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
text = h.unescape(body.group(1) if body else content)
text = re.sub(r'<[^>]+>', '\n', text)
text = re.sub(r'\n{3,}', '\n\n', text)
text = re.sub(r'[ \t]+', ' ', text)
espn_full_text = '\n'.join(l.strip() for l in text.split('\n') if l.strip())

# Build DB player index
db_index = {}
for p in PLAYERS:
    tid, name, cat, age, pos, status, form = p[1], p[2], p[3], p[4], p[5], p[6], p[7]
    for t in TEAMS:
        if t[0] == tid:
            code = t[2]
            if code not in db_index:
                db_index[code] = []
            db_index[code].append({"name": name, "cat": cat, "pos": pos, "age": age, "status": status, "tid": tid})
            break

# Verify each DB player
print("=" * 80)
print("48队球员逐人核查 (DB vs ESPN)")
print("=" * 80)

ok_count = 0
fail_count = 0
absent_ok_count = 0
issues = []

# Group order
GROUP_ORDER = ["A","B","C","D","E","F","G","H","I","J","K","L"]
team_by_group = {}
for t in TEAMS:
    g = t[3]
    if g not in team_by_group:
        team_by_group[g] = []
    team_by_group[g].append(t)

for g in GROUP_ORDER:
    if g not in team_by_group:
        continue
    print(f"\n{'─'*60}")
    print(f"  {g} 组")
    print(f"{'─'*60}")
    for t in team_by_group[g]:
        tid, name, code, group = t[0], t[1], t[2], t[3]
        players = db_index.get(code, [])
        print(f"\n  [{code}] {name}")
        for p in players:
            cn_name = p["name"]
            cat = p["cat"]
            keyword = NAME_MAP.get(cn_name, "")

            if cat == "absent":
                # Verify absent player is NOT in ESPN
                if keyword:
                    found_in_espn = keyword.lower() in espn_full_text.lower()
                    if found_in_espn:
                        issues.append(f"⚠️  [{code}] {cn_name} — DB标记absent，但在ESPN名单中找到！")
                        fail_count += 1
                    else:
                        absent_ok_count += 1
                        # Don't print absent confirmations unless issue
                else:
                    # No keyword to check - flag for manual review
                    issues.append(f"❓ [{code}] {cn_name} — 标记为absent，缺少英文关键词无法自动核查")
                continue

            if not keyword:
                issues.append(f"❓ [{code}] {cn_name} ({cat}) — 缺少英文名映射，无法自动核查")
                fail_count += 1
                continue

            found = keyword.lower() in espn_full_text.lower()
            if found:
                ok_count += 1
                # print(f"    ✅ {cn_name} ({cat})")
            else:
                issues.append(f"❌ [{code}] {cn_name} ({cat}) — ESPN名单中未找到!")
                fail_count += 1

print(f"\n{'='*80}")
print(f"核查结果汇总")
print(f"{'='*80}")
print(f"✅ 在队球员确认在ESPN名单中: {ok_count} 人")
print(f"✅ 缺席球员确认不在ESPN: {absent_ok_count} 人")
print(f"❌ 问题数: {len(issues)}")

if issues:
    print(f"\n📋 问题详情:")
    for iss in issues:
        print(f"  {iss}")

