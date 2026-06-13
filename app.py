from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
DB_FILE = "account.db"

# ========== 语录库 ==========
QUOTE_LIB = {
    "支出-餐饮": [
        "干饭不亏！好好吃饭才有力气搞钱🍚",
        "今日干饭额度已用，明天继续努力~😋",
        "民以食为天，小钱换大满足✨"
    ],
    "支出-购物": [
        "理性购物，快乐翻倍🛍️",
        "买到心仪好物，值！但也要克制哦~",
        "购物一时爽，余额两行泪😜"
    ],
    "支出-交通": [
        "为出行买单，平安抵达最重要🚗",
        "通勤虽花钱，但为了更好的生活呀~",
        "绿色出行更省钱，环保又健康🌿"
    ],
    "支出-娱乐": [
        "偶尔放松，快乐无价🎮",
        "娱乐充电，继续元气满满！",
        "适度娱乐，生活更有滋味~"
    ],
    "支出-房租": [
        "这是必需滴，这个月已经完成一个支出大项目啦🏠",
        "有窝才有家，房租虽贵但安全感满满~",
        "房租交完，继续努力搞钱攒首付！"
    ],
    "支出-其他": [
        "小钱花在刀刃上，每一笔都值得💡",
        "零星支出也要记，积少成多哦~",
        "合理规划，不浪费每一分钱！"
    ],
    "收入-工资": [
        "工资到账，安全感拉满💼",
        "努力的回报，犒劳一下自己吧~",
        "工资进袋，本月底气十足！"
    ],
    "收入-其他": [
        "意外小收入，开心值+100🥳",
        "小钱入账，积少成多奔小康~",
        "开源节流，财富慢慢涨！"
    ]
}

DEFAULT_QUOTES = [
    "每一笔记录，都是认真生活的证据✨",
    "理性收支，快乐加倍哦😊",
    "管好小钱钱，拥抱小幸福💖",
    "今天也是努力生活的一天！"
]

# ========== 初始化数据库 ==========
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 创建表（兼容旧表，新增quote字段）
    c.execute('''CREATE TABLE IF NOT EXISTS record
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT, money FLOAT, category TEXT,
                  remark TEXT, create_time TEXT,
                  quote TEXT DEFAULT '')''')
    # 给旧表添加quote字段（如果不存在）
    try:
        c.execute("ALTER TABLE record ADD COLUMN quote TEXT DEFAULT ''")
    except:
        pass

    c.execute('''CREATE TABLE IF NOT EXISTS budget
                 (id INTEGER PRIMARY KEY, budget FLOAT)''')
    c.execute("SELECT * FROM budget")
    if not c.fetchone():
        c.execute("INSERT INTO budget VALUES (1, 2000)")
    conn.commit()
    conn.close()

# ========== 获取对应语录 ==========
def get_quote_by_category(rec_type, category):
    key = f"{rec_type}-{category}"
    if key in QUOTE_LIB:
        return random.choice(QUOTE_LIB[key])
    return random.choice(DEFAULT_QUOTES)

# ========== 首页 ==========
@app.route('/')
def index():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM record ORDER BY create_time DESC")
    records = c.fetchall()
    c.execute("SELECT budget FROM budget WHERE id=1")
    budget = c.fetchone()[0]
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT SUM(money) FROM record WHERE create_time LIKE ?", (f"{today}%",))
    today_money = c.fetchone()[0] or 0
    conn.close()

    # 修复：安全获取语录，兼容旧数据
    if records:
        if len(records[0]) >= 7 and records[0][6]:
            top_quote = records[0][6]
        else:
            top_quote = random.choice(DEFAULT_QUOTES)
    else:
        top_quote = random.choice(DEFAULT_QUOTES)

    return render_template("index.html", records=records, budget=budget,
                           today_money=today_money, today=today, mood=top_quote)

# ========== 新增记录 ==========
@app.route('/add', methods=['POST'])
def add_record():
    r_type = request.form['type']
    money = float(request.form['money'])
    category = request.form['category']
    remark = request.form['remark']
    create_time = request.form['create_time']
    quote = get_quote_by_category(r_type, category)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO record (type, money, category, remark, create_time, quote) VALUES (?,?,?,?,?,?)",
              (r_type, money, category, remark, create_time, quote))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ========== 编辑记录页面 ==========
@app.route('/edit/<int:rid>')
def edit_page(rid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM record WHERE id=?", (rid,))
    record = c.fetchone()
    conn.close()
    mood = record[6] if (len(record)>=7 and record[6]) else random.choice(DEFAULT_QUOTES)
    return render_template("edit.html", record=record, mood=mood)

# ========== 更新记录 ==========
@app.route('/update/<int:rid>', methods=['POST'])
def update_record(rid):
    r_type = request.form['type']
    money = float(request.form['money'])
    category = request.form['category']
    remark = request.form['remark']
    create_time = request.form['create_time']
    quote = get_quote_by_category(r_type, category)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''UPDATE record SET type=?,money=?,category=?,remark=?,create_time=?,quote=?
                 WHERE id=?''', (r_type, money, category, remark, create_time, quote, rid))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ========== 删除记录 ==========
@app.route('/delete/<int:rid>')
def delete_record(rid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM record WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ========== 设置预算 ==========
@app.route('/set_budget', methods=['POST'])
def set_budget():
    new_budget = float(request.form['budget'])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE budget SET budget=? WHERE id=1", (new_budget,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# ========== 统计页面 ==========
@app.route('/stat')
def stat():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT SUM(money) FROM record WHERE type='收入'")
    income = c.fetchone()[0] or 0
    c.execute("SELECT SUM(money) FROM record WHERE type='支出'")
    expend = c.fetchone()[0] or 0
    # 获取最新语录
    c.execute("SELECT quote FROM record ORDER BY create_time DESC LIMIT 1")
    latest_quote = c.fetchone()
    mood = latest_quote[0] if (latest_quote and latest_quote[0]) else random.choice(DEFAULT_QUOTES)
    conn.close()
    return render_template("stat.html", income=income, expend=expend, mood=mood)

# ========== 快速饼图（matplotlib版，无文件读写） ==========
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

@app.route('/pie')
def pie_chart():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT category, SUM(money) FROM record WHERE type='支出' GROUP BY category")
    data = c.fetchall()
    conn.close()

    if not data:
        return '''
        <html>
            <body style="text-align:center;padding-top:100px;">
                <h3>暂无支出数据，无法生成饼图</h3>
                <br><a href="/">返回首页</a>
            </body>
        </html>
        '''

    categories = [x[0] for x in data]
    amounts = [x[1] for x in data]

    # 生成饼图
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title("支出分类占比")

    # 转base64嵌入页面
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return f'''
    <html>
    <head>
        <title>消费分类饼图</title>
        <style>
            body {{ text-align: center; padding-top: 50px; }}
            img {{ max-width: 600px; }}
        </style>
    </head>
    <body>
        <h2>消费分类占比饼图</h2>
        <img src="data:image/png;base64,{img_base64}">
        <br><br>
        <a href="/" class="btn btn-primary">返回首页</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    init_db()
    app.run(debug=True)