"""
店小满 v3 — Flask + SQLite + 登录注册
启动: python server.py  →  http://localhost:5000
"""
import sqlite3, json, os, datetime, hashlib, secrets
from flask import Flask, request, jsonify, send_file, g

app = Flask(__name__, static_folder='../', static_url_path='')
DB_PATH = os.path.join(os.path.dirname(__file__), 'store.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return resp

@app.teardown_appcontext
def close_db(e):
    db = g.pop('db', None)
    if db: db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            shop_id TEXT,
            school TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS shops(
            id TEXT PRIMARY KEY, name TEXT, emoji TEXT, color TEXT,
            type TEXT, addr TEXT, dist TEXT, description TEXT, tags TEXT,
            school TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id TEXT,
            name TEXT, price REAL, base_price REAL, tag TEXT,
            sales INTEGER DEFAULT 0, retain INTEGER DEFAULT 0,
            inv INTEGER DEFAULT 100, img TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS promotions(
            id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id TEXT,
            shop_name TEXT, name TEXT, price REAL, deal_price REAL,
            deal TEXT, deal_time TEXT, title TEXT, created TEXT
        );
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id TEXT,
            sender TEXT, text TEXT, time TEXT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sales_records(
            id INTEGER PRIMARY KEY AUTOINCREMENT, shop_id TEXT,
            date TEXT, revenue REAL, orders INTEGER DEFAULT 0, note TEXT DEFAULT '',
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS orders(
            id TEXT PRIMARY KEY, shop_id TEXT, student TEXT,
            product TEXT, price REAL, deal TEXT DEFAULT '', deal_price REAL,
            status TEXT DEFAULT '待取餐', created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # 添加列迁移（兼容旧库）
    try:
        db.execute("ALTER TABLE users ADD COLUMN school TEXT DEFAULT ''")
    except: pass
    try:
        db.execute("ALTER TABLE shops ADD COLUMN school TEXT DEFAULT ''")
    except: pass
    if db.execute("SELECT COUNT(*) FROM shops").fetchone()[0] == 0:
        seed(db)
    # 预置测试账号
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        pw = hashlib.sha256("123456".encode()).hexdigest()
        db.execute("INSERT INTO users(username,password_hash,role,shop_id,school) VALUES(?,?,?,?,?)",
                   ("student1", pw, "student", "", "东北大学"))
        db.execute("INSERT INTO users(username,password_hash,role,shop_id,school) VALUES(?,?,?,?,?)",
                   ("zhangtea", pw, "merchant", "zhangtea", ""))
        db.execute("INSERT INTO users(username,password_hash,role,shop_id,school) VALUES(?,?,?,?,?)",
                   ("lifruit", pw, "merchant", "lifruit", ""))
        db.execute("INSERT INTO users(username,password_hash,role,shop_id,school) VALUES(?,?,?,?,?)",
                   ("wangprint", pw, "merchant", "wangprint", ""))
        db.execute("INSERT INTO users(username,password_hash,role,shop_id,school) VALUES(?,?,?,?,?)",
                   ("lafu", pw, "merchant", "lafu", ""))
        db.execute("INSERT INTO users(username,password_hash,role,shop_id,school) VALUES(?,?,?,?,?)",
                   ("jjbakery", pw, "merchant", "jjbakery", ""))
        db.execute("INSERT INTO users(username,password_hash,role,shop_id,school) VALUES(?,?,?,?,?)",
                   ("haolinshi", pw, "merchant", "haolinshi", ""))
    db.commit(); db.close()

def seed(db):
    shops = [
        ("zhangtea","老张的茶","🧋","#f97316","奶茶/咖啡","东北大学南门东侧50米","120m","东大最火奶茶店。","学生8折,买一送一","东北大学"),
        ("lifruit","李姐水果铺","🍉","#10b981","水果生鲜","东北大学东门300米","280m","现切现卖新鲜水果。","满30送礼,当季鲜果","东北大学"),
        ("wangprint","王师傅文印","🖨️","#8b5cf6","文印店","东北大学东门100米","350m","支持在线上传文件。","毕业季,手机上传","东北大学"),
        ("lafu","拉福兰州拉面","🍜","#ef4444","餐饮小吃","东北大学南门对面","80m","正宗兰州拉面。","学生价,免费加面","东北大学"),
        ("jjbakery","静静烘焙坊","🍰","#ec4899","蛋糕甜品","东北大学西门200米","420m","手工现做蛋糕。","定制蛋糕,下午茶","东北大学"),
        ("haolinshi","好邻零食铺","🏪","#06b6d4","便利店","东北大学南门30米","50m","24h便利店。","满20减5,24h营业","东北大学"),
    ]
    db.executemany("INSERT INTO shops VALUES(?,?,?,?,?,?,?,?,?,?)", shops)
    prods = {
        "zhangtea":[("珍珠奶茶",15.9,"主推"),("杨枝甘露",18.0,"爆款"),("柠檬水",8.0,"引流"),("茉莉绿茶",10.0,""),("提拉米苏",22.0,"滞销")],
        "lifruit":[("冰西瓜(半个)",18.0,"当季"),("蜜瓜果切",15.0,""),("葡萄(斤)",12.0,""),("苹果果切",8.0,"")],
        "wangprint":[("黑白打印",0.1,"热促"),("彩色打印",0.5,""),("复印装订",5.0,""),("海报打印",15.0,"")],
        "lafu":[("兰州拉面",15.0,"热销"),("锅贴饺子",18.0,""),("麻辣烫",22.0,"")],
        "jjbakery":[("提拉米苏",25.0,"人气"),("泡芙(6只)",18.0,""),("纸杯蛋糕",12.0,"")],
        "haolinshi":[("冰可乐",4.0,"爆款"),("薯片(大袋)",8.0,""),("三明治",12.0,"热促"),("碳素笔",3.0,"")],
    }
    from random import randint
    for sid, plist in prods.items():
        for name, price, tag in plist:
            db.execute("INSERT INTO products(shop_id,name,price,base_price,tag,sales,retain,inv) VALUES(?,?,?,?,?,?,?,?)",
                       (sid,name,price,price,tag,randint(50,500),randint(30,80),randint(50,250)))
    promos = [
        ("zhangtea","老张的茶","珍珠奶茶",15.9,7.95,"买一送一","今晚起","期末冲刺"),
        ("lifruit","李姐水果铺","冰西瓜(半个)",18.0,12.0,"全场8折","本周末","夏日清凉"),
        ("wangprint","王师傅文印","黑白打印",0.10,0.05,"毕业季半价","本月","毕业服务周"),
        ("lafu","拉福兰州拉面","兰州拉面",15.0,10.0,"学生价","每天","学生优惠"),
        ("jjbakery","静静烘焙坊","提拉米苏",25.0,18.0,"下午茶7折","每日14:00","烘焙下午茶"),
        ("haolinshi","好邻零食铺","冰可乐",4.0,2.5,"买二送一","全天","便利店特惠"),
    ]
    today = datetime.date.today().strftime("%m/%d")
    for sid,sn,n,p,dp,d,t,title in promos:
        db.execute("INSERT INTO promotions(shop_id,shop_name,name,price,deal_price,deal,deal_time,title,created) VALUES(?,?,?,?,?,?,?,?,?)",
                   (sid,sn,n,p,dp,d,t,title,today))
    db.commit()

# ======== 认证 ========
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def make_token(user):
    return secrets.token_urlsafe(32)

# 内存 token 存储 (正式环境用 Redis)
sessions = {}

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = (data.get('username','')).strip()
    password = (data.get('password','')).strip()
    role = data.get('role','student')
    shop_id = data.get('shop_id','')
    shop_name = data.get('shop_name','')
    shop_addr = data.get('shop_addr','')
    shop_school = data.get('shop_school','')
    school = data.get('school','')
    if not username or not password:
        return jsonify({"error":"用户名和密码不能为空"}), 400
    db = get_db()
    if db.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone():
        return jsonify({"error":"用户名已存在"}), 409
    # 如果提供了shop_name，在shops表中创建店铺
    if role=='merchant' and shop_name and shop_id:
        db.execute("INSERT OR IGNORE INTO shops(id,name,emoji,color,type,addr,dist,description,tags,school) VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (shop_id, shop_name, '🏪', '#6366f1', '自定义', shop_addr, '附近', shop_name, '', shop_school))
    db.execute("INSERT INTO users(username,password_hash,role,shop_id,school) VALUES(?,?,?,?,?)",
               (username, hash_pw(password), role, shop_id, school))
    db.commit()
    uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    token = make_token({"id":uid,"role":role})
    sessions[token] = {"id":uid,"username":username,"role":role,"shop_id":shop_id,"shop_name":shop_name,"school":school}
    return jsonify({"token":token,"user":{"id":uid,"username":username,"role":role,"shop_id":shop_id,"shop_name":shop_name,"school":school}}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = (data.get('username','')).strip()
    password = (data.get('password','')).strip()
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
    if not user:
        return jsonify({"error":"用户不存在"}), 404
    if hash_pw(password) != user['password_hash']:
        return jsonify({"error":"密码错误"}), 401
    token = make_token({"id":user['id'],"role":user['role']})
    # 查询店铺名称、地址、学校
    shop_name = ''
    shop_addr = ''
    shop_school = ''
    if user['shop_id']:
        shop = db.execute("SELECT name,addr,school FROM shops WHERE id=?",(user['shop_id'],)).fetchone()
        if shop:
            shop_name = shop['name']
            shop_addr = shop['addr'] or ''
            shop_school = shop['school'] or ''
    # 优先使用店铺表中的学校，其次用户表中的学校
    school = shop_school or user['school'] or ''
    sessions[token] = {"id":user['id'],"username":user['username'],"role":user['role'],"shop_id":user['shop_id'],"shop_name":shop_name,"shop_addr":shop_addr,"school":school}
    return jsonify({"token":token,"user":{"id":user['id'],"username":user['username'],"role":user['role'],"shop_id":user['shop_id'],"shop_name":shop_name,"shop_addr":shop_addr,"school":school}})

def get_user():
    token = request.headers.get('Authorization','').replace('Bearer ','')
    return sessions.get(token)

@app.route('/api/<path:path>', methods=['OPTIONS'])
@app.route('/api/auth/<path:path>', methods=['OPTIONS'])
def handle_options(path=''):
    return '', 204

@app.route('/')
def index():
    return send_file('../index.html')

@app.route('/api/me')
def me():
    user = get_user()
    if not user: return jsonify({"error":"未登录"}), 401
    # 补充店铺名称、地址、学校
    shop_name = user.get('shop_name','')
    shop_addr = user.get('shop_addr','')
    shop_school = user.get('school','')
    if user.get('shop_id'):
        shop = get_db().execute("SELECT name,addr,school FROM shops WHERE id=?",(user['shop_id'],)).fetchone()
        if shop:
            if not shop_name: shop_name = shop['name']
            if not shop_addr: shop_addr = shop['addr'] or ''
            if not shop_school: shop_school = shop['school'] or ''
    return jsonify({**user, "shop_name":shop_name, "shop_addr":shop_addr, "school":shop_school})

@app.route('/api/shops')
def api_shops():
    db = get_db()
    rows = db.execute("SELECT * FROM shops").fetchall()
    shops = []
    for r in rows:
        prods = db.execute("SELECT * FROM products WHERE shop_id=?",(r['id'],)).fetchall()
        promos = db.execute("SELECT * FROM promotions WHERE shop_id=?",(r['id'],)).fetchall()
        shops.append({
            "id":r['id'],"name":r['name'],"emoji":r['emoji'],"color":r['color'],
            "type":r['type'],"addr":r['addr'],"dist":r['dist'],"desc":r['description'],
            "school":r['school'] or '',
            "tags": (r['tags'] or '').split(',') if r['tags'] else [],
            "products":[dict(p) for p in prods],
            "promos":[dict(p) for p in promos]
        })
    return jsonify(shops)

# 更新店铺信息（地址等）
@app.route('/api/shops/<shop_id>', methods=['PUT'])
def update_shop(shop_id):
    user = get_user()
    if not user or user.get('shop_id')!=shop_id:
        return jsonify({"error":"无权操作"}), 403
    data = request.get_json()
    db = get_db()
    for field in ['name','addr','school','type','description','tags']:
        if field in data:
            db.execute(f"UPDATE shops SET {field}=? WHERE id=?",(data[field],shop_id))
    db.commit()
    return jsonify({"ok":True})

# ======== 产品 CRUD ========
@app.route('/api/products/<shop_id>')
def api_products(shop_id):
    db = get_db()
    rows = db.execute("SELECT * FROM products WHERE shop_id=? ORDER BY id",(shop_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/products/<shop_id>', methods=['POST'])
def add_product(shop_id):
    user = get_user()
    if not user or user.get('shop_id')!=shop_id:
        return jsonify({"error":"无权操作"}), 403
    data = request.get_json()
    db = get_db()
    db.execute("INSERT INTO products(shop_id,name,price,base_price,tag,sales,retain,inv,img) VALUES(?,?,?,?,?,?,?,?,?)",
               (shop_id, data['name'], data['price'], data.get('base_price',data['price']),
                data.get('tag',''), data.get('sales',0), data.get('retain',0), data.get('inv',100), data.get('img','')))
    db.commit()
    pid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return jsonify({"ok":True,"id":pid}), 201

@app.route('/api/products/<shop_id>/<int:pid>', methods=['PUT'])
def update_product(shop_id, pid):
    user = get_user()
    if not user or user.get('shop_id')!=shop_id:
        return jsonify({"error":"无权操作"}), 403
    data = request.get_json()
    db = get_db()
    # 支持部分更新
    fields = ['name','price','base_price','tag','sales','retain','inv','img']
    sets = [f"{f}=?" for f in fields if f in data]
    vals = [data[f] for f in fields if f in data]
    if sets:
        db.execute(f"UPDATE products SET {','.join(sets)} WHERE id=? AND shop_id=?", vals + [pid, shop_id])
        db.commit()
    return jsonify({"ok":True})

@app.route('/api/products/<shop_id>/<int:pid>', methods=['DELETE'])
def delete_product(shop_id, pid):
    user = get_user()
    if not user or user.get('shop_id')!=shop_id:
        return jsonify({"error":"无权操作"}), 403
    get_db().execute("DELETE FROM products WHERE id=? AND shop_id=?",(pid,shop_id))
    get_db().commit()
    return jsonify({"ok":True})

# ======== 统计 ========
@app.route('/api/stats')
def api_stats():
    db = get_db()
    shop_count = db.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
    prod_count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    promo_count = db.execute("SELECT COUNT(*) FROM promotions").fetchone()[0]
    msg_count = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    return jsonify({"shops":shop_count,"products":prod_count,"promotions":promo_count,"messages":msg_count})

# ======== 逆地理编码 ========
@app.route('/api/geocode')
def api_geocode():
    lat = request.args.get('lat','')
    lng = request.args.get('lng','')
    if not lat or not lng:
        return jsonify({"error":"需要 lat 和 lng 参数"}), 400
    import urllib.request
    url = f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&accept-language=zh'
    req = urllib.request.Request(url, headers={'User-Agent': 'DianXiaoMan/1.0 (campus promotion platform)'})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            addr = data.get('display_name','') or f'{lat}, {lng}'
            if len(addr) > 80:
                addr = '，'.join(addr.split(',')[:3])
            return jsonify({"address":addr,"lat":lat,"lng":lng})
    except Exception as e:
        return jsonify({"address":f'{lat}, {lng}',"lat":lat,"lng":lng})

# ======== 促销 ========
@app.route('/api/promotions')
def api_promotions():
    return jsonify([dict(r) for r in get_db().execute("SELECT * FROM promotions ORDER BY id DESC")])

@app.route('/api/promotions', methods=['POST'])
def add_promotion():
    data = request.get_json()
    user = get_user()
    if not user or user.get('shop_id')!=data.get('shop_id'):
        return jsonify({"error":"只能给自己店铺发促销"}), 403
    db = get_db()
    today = datetime.date.today().strftime("%m/%d")
    db.execute("INSERT INTO promotions(shop_id,shop_name,name,price,deal_price,deal,deal_time,title,created) VALUES(?,?,?,?,?,?,?,?,?)",
               (data['shop_id'],data['shop_name'],data['name'],data['price'],
                data['deal_price'],data['deal'],data.get('deal_time',''),data['title'],today))
    db.commit()
    return jsonify({"ok":True}), 201

@app.route('/api/promotions/<int:pid>', methods=['DELETE'])
def delete_promotion(pid):
    user = get_user()
    if not user: return jsonify({"error":"未登录"}), 401
    db = get_db()
    p = db.execute("SELECT shop_id FROM promotions WHERE id=?",(pid,)).fetchone()
    if not p: return jsonify({"error":"不存在"}), 404
    if user.get('shop_id')!=p['shop_id']:
        return jsonify({"error":"无权操作"}), 403
    db.execute("DELETE FROM promotions WHERE id=?",(pid,))
    db.commit()
    return jsonify({"ok":True})

# ======== 销售记录 ========
@app.route('/api/sales-records/<shop_id>')
def api_sales_records(shop_id):
    rows = get_db().execute("SELECT * FROM sales_records WHERE shop_id=? ORDER BY date DESC",(shop_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/sales-records/<shop_id>', methods=['POST'])
def add_sales_record(shop_id):
    user = get_user()
    if not user or user.get('shop_id')!=shop_id:
        return jsonify({"error":"无权操作"}), 403
    data = request.get_json()
    db = get_db()
    db.execute("INSERT INTO sales_records(shop_id,date,revenue,orders,note) VALUES(?,?,?,?,?)",
               (shop_id, data['date'], data['revenue'], data.get('orders',0), data.get('note','')))
    db.commit()
    return jsonify({"ok":True,"id":db.execute("SELECT last_insert_rowid()").fetchone()[0]}), 201

@app.route('/api/sales-records/<shop_id>/<int:rid>', methods=['DELETE'])
def delete_sales_record(shop_id, rid):
    user = get_user()
    if not user or user.get('shop_id')!=shop_id:
        return jsonify({"error":"无权操作"}), 403
    get_db().execute("DELETE FROM sales_records WHERE id=? AND shop_id=?",(rid,shop_id))
    get_db().commit()
    return jsonify({"ok":True})

# ======== 学生订单 ========
@app.route('/api/orders/<shop_id>')
def api_orders(shop_id):
    rows = get_db().execute("SELECT * FROM orders WHERE shop_id=? ORDER BY created DESC",(shop_id,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/orders/<shop_id>', methods=['POST'])
def place_order_api(shop_id):
    data = request.get_json()
    db = get_db()
    db.execute("INSERT INTO orders(id,shop_id,student,product,price,deal,deal_price,status) VALUES(?,?,?,?,?,?,?,?)",
               (data['id'], shop_id, data.get('student',''), data['product'], data['price'],
                data.get('deal',''), data.get('deal_price',data['price']), data.get('status','待取餐')))
    db.commit()
    return jsonify({"ok":True}), 201

@app.route('/api/messages/<shop_id>')
def api_messages(shop_id):
    return jsonify([dict(r) for r in get_db().execute("SELECT * FROM messages WHERE shop_id=? ORDER BY id",(shop_id,))])

@app.route('/api/messages/<shop_id>', methods=['POST'])
def send_msg(shop_id):
    data = request.get_json()
    now = datetime.datetime.now().strftime("%H:%M")
    db = get_db()
    db.execute("INSERT INTO messages(shop_id,sender,text,time) VALUES(?,?,?,?)",
               (shop_id,data['sender'],data['text'],now))
    db.commit()
    from random import choice
    reply = choice(["好的！可以到店自取~","在的！欢迎到店~","没问题，随时来~","有啥可以帮你的？😊"])
    db.execute("INSERT INTO messages(shop_id,sender,text,time) VALUES(?,'merchant',?,?)",
               (shop_id,reply,datetime.datetime.now().strftime("%H:%M")))
    db.commit()
    return jsonify({"ok":True,"reply":reply})

if __name__ == '__main__':
    init_db()
    print("店小满 v3 已启动 -> http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
