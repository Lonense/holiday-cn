# holiday-cn

中国法定节假日数据，自动每日抓取国务院公告。

## 功能

- [x] 自动抓取国务院节假日公告
- [x] 生成 JSON 格式节假日数据
- [x] 生成 ICS 日历文件
- [x] CI 自动更新
- [x] 支持多种节假日类型（法定节假日、传统节日、纪念日等）

## ICalendar 订阅

### 主日历（包含所有节假日）

```
https://raw.githubusercontent.com/Lonense/holiday-cn/main/holiday-cn.ics
```

### 年份日历

```
https://raw.githubusercontent.com/Lonense/holiday-cn/main/2023.ics
https://raw.githubusercontent.com/Lonense/holiday-cn/main/2024.ics
```

## 数据格式

### JSON 数据

```json
{
    "$schema": "https://raw.githubusercontent.com/Lonense/holiday-cn/master/schema.json",
    "$id": "https://raw.githubusercontent.com/Lonense/holiday-cn/master/2023.json",
    "year": 2023,
    "papers": [
        "http://www.gov.cn/zhengce/content/2022-12/08/content_5730844.htm"
    ],
    "days": [
        {
            "name": "元旦",
            "date": "2023-01-01",
            "isOffDay": true
        }
    ]
}
```

### ICS 日历

ICS 文件包含以下类型的节假日：

1. **法定节假日**：元旦、春节、清明节、劳动节、端午节、中秋节、国庆节
2. **传统节日**：龙抬头、上巳节、中元节、下元节、腊八节等
3. **纪念日**：抗日战争胜利纪念日、教师节、国耻日等
4. **其他节日**：情人节、母亲节、父亲节、圣诞节等

## 开发

### 环境要求

- Python 3.8+
- 依赖包见 `requirements.txt`

### 安装依赖

```bash
pip install -r requirements.txt -r dev-requirements.txt
```

### 运行测试

```bash
make test
```

### 代码格式化

```bash
make format
```

### 代码检查

```bash
make lint
```

### 更新数据

```bash
# 更新当前年和下一年数据
python update.py

# 更新所有年份数据（从2007年开始）
python update.py --all
```

## 项目结构

```
holiday-cn/
├── .github/
│   └── workflows/
│       └── update.yml        # GitHub Actions 工作流
├── tests/
│   └── test_update.py        # 测试文件
├── 2007.json                 # 2007年节假日数据
├── 2007.ics                  # 2007年日历文件
├── ...
├── 2024.json                 # 2024年节假日数据
├── 2024.ics                  # 2024年日历文件
├── holiday-cn.ics            # 主日历文件
├── schema.json               # JSON Schema
├── update.py                 # 主更新脚本
├── requirements.txt          # 生产依赖
├── dev-requirements.txt      # 开发依赖
├── Makefile                  # 构建脚本
├── LICENSE                   # 许可证
└── README.md                 # 项目说明
```

## 数据来源

数据来源于国务院办公厅发布的节假日安排通知。

## 许可证

MIT License