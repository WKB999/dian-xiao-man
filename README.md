# 店小满 — 学区AI促销平台

面向大学城商家的智能营销与促销管理平台。提供产品管理、AI营销文案生成、智能定价建议、学区日历、客户消息等功能。

## 技术栈

- **前端**: 纯 HTML/CSS/JavaScript（Vanilla JS SPA，无框架依赖）
- **后端**: Python Flask + SQLite
- **架构**: 前后端分离，后端提供 RESTful API，前端独立部署

## 项目结构

```
店小满/
├── backend/
│   └── server.py          # Flask API 服务（端口 5000）
├── frontend/
│   ├── generate_html.py   # 前端代码生成器（Python → HTML）
│   └── 店小满_完整原型.html  # 生成的完整前端文件
├── requirements.txt
├── .gitignore
└── README.md
```

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成前端页面

```bash
cd frontend
python generate_html.py
```

### 3. 启动后端

```bash
cd backend
python server.py
```

访问 `http://localhost:5000`

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/me` | GET | 获取当前用户信息 |
| `/api/shops` | GET | 获取全部店铺列表 |
| `/api/products/<shop_id>` | GET/POST | 产品列表/添加 |
| `/api/products/<shop_id>/<id>` | PUT/DELETE | 更新/删除产品 |
| `/api/promotions` | GET/POST | 促销列表/添加 |
| `/api/messages/<shop_id>` | GET/POST | 消息列表/发送 |
| `/api/stats` | GET | 全站统计数据 |

## 功能模块

### 商家端
- 店铺管理（名称、类型、地址、产品清单）
- AI 营销文案生成（朋友圈/小红书/群发 3 套）
- 智能定价建议（销量/天气/库存多因子分析）
- 学区日历（考试周/开学/节假日时间节点）
- 售卖信息面板（促销产品管理）
- 客户消息（AI 自动回复 + 后台消息管理）

### 学生端
- 今日促销商品浏览（按学校筛选）
- 附近店铺列表（导航到店）
- 店铺详情查看（产品报价 + 促销活动）
- 学校选择器（50+ 高校）

## 体验账号

| 用户名 | 角色 | 店铺 |
|--------|------|------|
| zhangtea | 商家 | 老张的茶 |
| lifruit | 商家 | 李姐水果铺 |
| wangprint | 商家 | 王师傅文印 |
| lafu | 商家 | 拉福兰州拉面 |
| jjbakery | 商家 | 静静烘焙坊 |
| haolinshi | 商家 | 好邻零食铺 |
| student1 | 学生 | — |

密码统一: `123456`

## 部署说明

生成的前端 HTML 可独立部署到任何静态服务器。后端需 Python 3.7+ 环境。

生产部署建议：
```bash
# 使用 gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```
