# 店小满 — 学区AI促销平台

> 面向大学城商家的智能营销与促销管理 SaaS 平台  
> 原型线上可访问 · 前后端完整代码 · SQLite 数据库设计

## 项目简介

店小满专为大学城周边小微商家打造。通过对商品销量、天气变化、学校日历等多维数据的分析，自动生成营销文案与定价建议，帮助商家提升日常经营效率。学生端可按学校筛选附近促销商品与店铺，打通校园与商圈的信息壁垒。

### 技术亮点

- **零依赖前端架构**: 纯 Vanilla JS 实现的完整 SPA（约 176KB），无 React/Vue 等框架依赖，部署门槛极低
- **双角色会话系统**: 商家/学生双端独立登录，支持双会话同时在线、一键切换身份
- **多因子智能定价**: 综合销量权重(0.35)、库存(0.25)、回头率(0.25)、天气(0.15)的加权评分算法，逐产品生成建议价
- **AI 营销文案引擎**: 基于产品组合 + 学区时间节点 + 天气 + 活动主题，自动生产朋友圈/小红书/群发三套差异化文案
- **学区日历系统**: 预置 50+ 高校考试周 / 开学 / 节假日时间节点，支持自定义添加
- **GPS + 地图双模选址**: 浏览器 GPS 快速定位，搭配百度地图手动选址，地址即时写入数据库
- **数据全量持久化**: 所有用户操作（产品/价格/促销/销售记录/订单/聊天）均实时同步后端 SQLite，刷新不丢失

## 技术架构

```
  L1  FRONTEND                          Vanilla JS SPA, 176KB
 ┌──────────────────────────────────────────────────────────┐
 │  Dashboard  ·  Shop Manager  ·  AI Marketing             │
 │  Smart Pricing  ·  Sales Info  ·  Calendar  ·  Reports   │
 └────────────────────────┬─────────────────────────────────┘
                          │  REST API (fetch + Token)
 ┌────────────────────────┴─────────────────────────────────┐
 │  L2  API GATEWAY                Flask, 16 endpoints      │
 │                                                          │
 │  /api/auth       /api/shops        /api/products          │
 │  /api/promotions /api/messages     /api/orders            │
 │  /api/sales-records  /api/stats    /api/geocode           │
 └────────────────────────┬─────────────────────────────────┘
                          │  SQL (SQLite WAL Mode)
 ┌────────────────────────┴─────────────────────────────────┐
 │  L3  DATA STORE                 SQLite, 7 tables         │
 │                                                          │
 │  users   shops   products   promotions                   │
 │  messages   sales_records   orders                       │
 └──────────────────────────────────────────────────────────┘
```

### 分层说明

| 层级 | 技术选型 | 核心职责 |
|------|----------|----------|
| **前端表现层** | HTML5 + CSS3 + ES6+ (Vanilla JS) | SPA 路由切换 · 双角色 UI · 动态卡片渲染 · 离线回退策略 |
| **API 网关层** | Python Flask + CORS | 16 个 RESTful 端点 · Token 认证 · 角色权限校验 · 请求参数校验 |
| **数据持久层** | SQLite 3 (WAL 模式) | 7 表外键关联 · 自动建表迁移 · 种子数据初始化 · ACID 事务 |
| **安全层** | SHA-256 + Bearer Token | 密码哈希存储 · 会话 Token 管理 · shop_id 归属校验 · CORS 白名单 |
| **部署层** | Gunicorn + systemd | 多 worker 生产环境 · 静态文件代理 · 单文件部署 · 零外部依赖 |

### 核心业务流程

```
  Merchant                          Student
  ────────                          ───────
  Login                             Login
    │                                  │
    ▼                                  ▼
  Manage Shop                       Browse
  (产品/调价/促销)                  (促销/店铺)
    │                                  │
    ▼               ┌────────┐         ▼
  Token Auth ──────→│ SHARED │←──── API Aggregate
  SHA-256+shop_id   │ API    │      SQL JOIN
    │               │ Auth   │         │
    ▼               │ DB     │         ▼
  SQLite Write ────→│ CORS   │←──── Filter
  products/promos   └────────┘      按学校筛选
    │                                  │
    ▼                                  ▼
  Render                             Order
  前端动态更新                        下单写库
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | HTML5 + CSS3 + ES6+ | Vanilla JS SPA，零框架，纯标准 Web 技术 |
| 后端 | Python 3.7+ / Flask | RESTful API，16 个端点，标准库辅助 |
| 数据库 | SQLite 3 (WAL 模式) | 零配置，单文件部署，无需独立数据库服务 |
| 认证 | Token + SHA-256 | 注册/登录、角色区分、店铺归属校验 |
| 部署 | Gunicorn / systemd | 支持 Linux 生产环境，单文件前端可独立部署 |

## 项目结构

```
dian-xiao-man/
├── README.md                           # 项目文档（本文）
├── requirements.txt                    # Python 依赖
├── .gitignore
├── 后端/
│   └── server.py                       # Flask API 服务（端口 5000）
│       包含 16 个 RESTful 端点：
│       · 用户注册/登录         POST /api/auth/register | login
│       · 当前用户信息           GET  /api/me
│       · 店铺列表（聚合数据）   GET  /api/shops · PUT 更新地址
│       · 产品 CRUD              GET|POST|PUT|DELETE /api/products
│       · 促销管理               GET|POST|DELETE /api/promotions
│       · 销售记录               GET|POST|DELETE /api/sales-records
│       · 学生订单               GET|POST /api/orders
│       · 消息收发（+AI 回复）   GET|POST /api/messages
│       · 全站统计               GET  /api/stats
│       · GPS 逆地理编码         GET  /api/geocode
├── 前端/
│   ├── generate_html.py               # HTML 生成器（Python 脚本）
│   └── index.html                      # 完整 SPA 前端文件（176KB）
└── 文档/
    └── A4_proposal.html                # A4 单页方案文档
```

## 数据库设计

### users — 用户表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自增主键 |
| username | TEXT | UNIQUE | 登录用户名 |
| password_hash | TEXT | NOT NULL | SHA-256 密码哈希 |
| role | TEXT | NOT NULL | merchant / student |
| shop_id | TEXT | | 关联店铺 ID（商家） |
| shop_name | TEXT | | 店铺名称（注册时填写） |
| school | TEXT | | 所在学校 |

### shops — 店铺表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | 店铺唯一标识 |
| name | TEXT | NOT NULL | 店铺名称 |
| emoji | TEXT | | 店铺图标 |
| color | TEXT | | 主题色 |
| type | TEXT | | 经营类型（9 大类） |
| addr | TEXT | | 详细地址 |
| dist | TEXT | | 距离参考 |
| desc | TEXT | | 店铺简介 |
| tags | TEXT | | 标签（JSON 格式） |
| school | TEXT | | 所属学校（筛选维度） |

### products — 产品表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自增主键 |
| shop_id | TEXT | FK → shops.id | 归属店铺 |
| name | TEXT | NOT NULL | 产品名称 |
| price | REAL | NOT NULL | 当前售价 |
| base_price | REAL | | 原始定价 |
| tag | TEXT | | 标签（主推/爆款/滞销） |
| sales | INTEGER | | 累计销量 |
| retain | REAL | | 回头率（%） |
| inv | INTEGER | | 库存数量 |

### promotions — 促销表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自增主键 |
| shop_id | TEXT | FK → shops.id | 归属店铺 |
| shop_name | TEXT | | 店铺名称 |
| name | TEXT | NOT NULL | 商品名称 |
| price | REAL | | 原价 |
| deal_price | REAL | | 促销价 |
| deal | TEXT | | 优惠方式描述 |
| deal_time | TEXT | | 活动时间段 |
| title | TEXT | | 活动标题 |
| created | TEXT | | 创建日期 |

### messages — 消息表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自增主键 |
| shop_id | TEXT | FK → shops.id | 归属店铺 |
| sender | TEXT | NOT NULL | 发送者（student/merchant） |
| text | TEXT | NOT NULL | 消息内容 |
| time | TEXT | | 发送时间 |

### sales_records — 销售记录表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自增主键 |
| shop_id | TEXT | FK → shops.id | 归属店铺 |
| date | TEXT | NOT NULL | 营业日期 |
| revenue | REAL | NOT NULL | 当日营业额 |
| orders | INTEGER | | 订单数 |
| note | TEXT | | 备注 |

### orders — 学生订单表
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | TEXT | PRIMARY KEY | 订单唯一标识 |
| shop_id | TEXT | FK → shops.id | 归属店铺 |
| student | TEXT | | 下单学生 |
| product | TEXT | NOT NULL | 产品名称 |
| price | REAL | NOT NULL | 成交价 |
| deal | TEXT | | 优惠方式 |
| deal_price | REAL | | 优惠后价格 |
| status | TEXT | | 订单状态（待取餐/已完成） |

## 功能模块详解

### 商家端（9 个模块）

| 模块 | 核心功能 | 技术实现 |
|------|----------|----------|
| 首页仪表盘 | 今日营业额/订单统计，学区时间节点，AI 建议推送 | DOM 实时渲染 + API 统计接入 |
| 店铺管理 | 店铺名称/类型/地址编辑，GPS+地图双模选址，产品清单增删改实时同步后端 | 产品 CRUD API + 地址 PUT API + 百度地图外链 |
| AI 营销文案 | 活动主题 + 时间节点 + 产品组合 → 3 套差异化文案，一键同步到促销表 | 模板引擎 + POST /api/promotions 持久化 |
| 智能定价 | 销量/库存/回头率/天气多因子加权评分，调价即时写入数据库 | 加权算法 + PUT /api/products 持久化 |
| 售卖信息 | 促销活动管理，全部产品报价，AI 文案一键同步 | syncToSalesInfo 数据桥接 |
| 学区日历 | 预置 50+ 高校考试周/开学/节假日，支持自定义 | 数组渲染 + 编辑模式 |
| 客户消息 | 学生咨询列表，AI 自动回复 | 关键词匹配 + 模糊回退策略 |
| 经营报表 | 手动录入营收/订单数据，历史记录展示 | 本地数组存储 + 日期筛选 |
| 个人中心 | 账号信息、角色管理、双角色切换 | Session 管理 + 菜单弹窗 |

### 学生端（4 个模块）

| 模块 | 核心功能 | 技术实现 |
|------|----------|----------|
| 今日促销 | 按学校筛选促销商品，卡片展示（店名+价格+优惠+导航），每次打开从后端拉最新 | 动态过滤 + GET /api/promotions 实时刷新 |
| 附近店铺 | 店铺网格展示，产品报价查看，每次打开从后端拉最新数据 | GET /api/shops 实时刷新 + 外链导航 |
| 我的订单 | 学生下单历史，支持实时下单并持久化至后端 | POST/GET /api/orders + 内存渲染 |
| 快捷体验 | 6 商家 + 1 学生预置账号，一键登录即用 | quickLogin 自动填充 + Token 认证 |

## API 接口文档

### 认证接口

| 方法 | 端点 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/api/auth/register` | `{username, password, role, shop_id?, ...}` | `{token, user}` |
| POST | `/api/auth/login` | `{username, password}` | `{token, user: {role, ...}}` |
| GET | `/api/me` | Header: `Authorization: Bearer <token>` | `{id, username, role, ...}` |

### 业务接口

| 方法 | 端点 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/shops` | — | 获取全部店铺（含产品和促销聚合数据） |
| GET | `/api/products/<shop_id>` | — | 获取指定店铺产品列表 |
| POST | `/api/products/<shop_id>` | Token | 添加产品（需校验 shop_id 归属） |
| PUT | `/api/products/<shop_id>/<pid>` | Token | 更新产品信息（支持部分更新） |
| DELETE | `/api/products/<shop_id>/<pid>` | Token | 删除产品 |
| GET | `/api/promotions` | — | 获取全部促销列表 |
| POST | `/api/promotions` | Token | 添加促销 |
| DELETE | `/api/promotions/<id>` | Token | 删除促销 |
| GET | `/api/messages/<shop_id>` | — | 获取店铺消息记录 |
| POST | `/api/messages/<shop_id>` | — | 发送消息（含 AI 自动回复） |
| GET | `/api/sales-records/<shop_id>` | — | 获取销售记录 |
| POST | `/api/sales-records/<shop_id>` | Token | 录入销售记录 |
| DELETE | `/api/sales-records/<shop_id>/<rid>` | Token | 删除销售记录 |
| GET | `/api/orders/<shop_id>` | — | 获取店铺订单 |
| POST | `/api/orders/<shop_id>` | — | 学生下单 |
| GET | `/api/stats` | — | 全站统计 |
| GET | `/api/geocode?lat=&lng=` | — | GPS 逆地理编码代理 |

## 快速启动

```bash
# 1. 安装依赖
pip install flask

# 2. 启动后端（首次运行自动建表+种子数据）
cd 后端
python server.py
# → 服务运行在 http://localhost:5000

# 3. （可选）重新生成前端 HTML
cd 前端
python generate_html.py
# → 输出 index.html 到当前目录
```

## 体验账号

| 用户名 | 角色 | 店铺 | 密码 |
|--------|------|------|------|
| zhangtea | 商家 | 🧋 老张的茶 | 123456 |
| lifruit | 商家 | 🍉 李姐水果铺 | 123456 |
| wangprint | 商家 | 🖨️ 王师傅文印 | 123456 |
| lafu | 商家 | 🍜 拉福兰州拉面 | 123456 |
| jjbakery | 商家 | 🍰 静静烘焙坊 | 123456 |
| haolinshi | 商家 | 🏪 好邻零食铺 | 123456 |
| student1 | 学生 | — | 123456 |

> 登录页底部提供快捷体验区，点击按钮即可一键登录以上任意账号。

## 部署

```bash
# 生产环境推荐 Gunicorn
pip install gunicorn
cd 后端
gunicorn -w 4 -b 0.0.0.0:5000 server:app

# 或 systemd 服务
# 参见 /etc/systemd/system/dianxiaoman.service
```

## License

本项目为笔试作品，仅供学习与展示参考。
