from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from pyecharts import options as opts
from pyecharts.charts import Pie
from pyecharts.globals import ThemeType
import random

app = Flask(__name__)
DB_FILE = "account.db"

# 暖心情绪文案库
MOOD_WORDS = [
    "每一笔记录，都是认真生活的证据✨",
    "理性消费，快乐加倍哦😊",
    "管好小钱钱，拥抱小幸福💖",
    "今天也是努力生活的一天！",
    "合理规划，未来可期🌟",
    "记账也是记录美好生活呀~",
    "不乱花钱，给自己攒一份惊喜🎁",
    "慢慢来，生活和钱包都会越来越好"
]

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS record
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT, money FLOAT, category TEXT,
                  remark TEXT, create_time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS budget
                 (id INTEGER PRIMARY KEY, budget FLOAT)''')
    c.execute("SELECT * FROM budget")
    if not c.fetchone():
        c.execute("INSERT INTO budget VALUES (1, 2000)")
    conn.commit()
    conn.close()

# 获取随机情绪文案
def get_mood_text():
    return random.choice(MOOD_WORDS)

# 首页
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
    mood = get_mood_text()
    return render_template("index.html", records=records, budget=budget,
                           today_money=today_money, today=today, mood=mood)

# 新增记录
@app.route('/add', methods=['POST'])
def add_record():
    r_type = request.form['type']
    money = float(request.form['money'])
    category = request.form['category']
    remark = request.form['remark']
    create_time = request.form['create_time']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO record (type, money, category, remark, create_time) VALUES (?,?,?,?,?)",
              (r_type, money, category, remark, create_time))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# 删除记录
@app.route('/delete/<int:rid>')
def delete_record(rid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM record WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# 修改页面
@app.route('/edit/<int:rid>')
def edit_page(rid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM record WHERE id=?", (rid,))
    record = c.fetchone()
    conn.close()
    mood = get_mood_text()
    return render_template("edit.html", record=record, mood=mood)

# 提交修改
@app.route('/update/<int:rid>', methods=['POST'])
def update_record(rid):
    r_type = request.form['type']
    money = float(request.form['money'])
    category = request.form['category']
    remark = request.form['remark']
    create_time = request.form['create_time']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''UPDATE record SET type=?,money=?,category=?,remark=?,create_time=?
                 WHERE id=?''', (r_type, money, category, remark, create_time, rid))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# 修改预算
@app.route('/set_budget', methods=['POST'])
def set_budget():
    new_budget = float(request.form['budget'])
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE budget SET budget=? WHERE id=1", (new_budget,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# 饼状图
@app.route('/pie')
def pie_chart():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT category, SUM(money) FROM record GROUP BY category")
    data = c.fetchall()
    conn.close()
    pie = (
        Pie(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
        .add(series_name="消费分类", data_pair=data, radius="60%")
        .set_global_opts(title_opts=opts.TitleOpts(title="消费分类占比饼图"))
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}元"))
    )
    return pie.render_embed()

# 收支统计
@app.route('/stat')
def stat():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT SUM(money) FROM record WHERE type='收入'")
    income = c.fetchone()[0] or 0
    c.execute("SELECT SUM(money) FROM record WHERE type='支出'")
    expend = c.fetchone()[0] or 0
    conn.close()
    mood = get_mood_text()
    return render_template("stat.html", income=income, expend=expend, mood=mood)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)