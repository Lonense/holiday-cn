# holiday-cn

补充苹果日历未包含的中国节日数据。

## 包含节日

- 情人节、母亲节、父亲节
- 植树节、愚人节、世界地球日
- 抗日战争胜利纪念日、教师节、国耻日
- 辛亥革命纪念日、一二·九运动纪念日、南京大屠杀纪念日
- 平安夜、圣诞节
- 农历节日：龙抬头、上巳节、中元节、下元节、腊八节

## ICalendar 订阅

```
https://raw.githubusercontent.com/Lonense/holiday-cn/main/holiday-cn.ics
```

## 开发

### 安装依赖

```bash
pip install -r requirements.txt
```

### 生成日历

```bash
python update.py
```

## 项目结构

```
holiday-cn/
├── update.py           # 生成脚本
├── holiday-cn.ics      # 日历文件
├── requirements.txt    # 依赖
├── Makefile
├── README.md
└── LICENSE
```

## 许可证

MIT License
