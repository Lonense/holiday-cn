# holiday-cn

[![Build Status](https://github.com/Lonese/holiday-cn/workflows/CI/badge.svg)](https://github.com/Lonese/holiday-cn/actions)
[![Release](https://img.shields.io/github/release/Lonese/holiday-cn.svg)](https://github.com/Lonese/holiday-cn/releases/latest)
[![CalVer](https://img.shields.io/badge/calver-YYYY.0M.0D-22bfda.svg)](http://calver.org)
[![Maintainability](https://api.codeclimate.com/v1/badges/c8e9d9c51bd2d858c577/maintainability)](https://codeclimate.com/github/Lonese/holiday-cn/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/c8e9d9c51bd2d858c577/test_coverage)](https://codeclimate.com/github/Lonese/holiday-cn/test_coverage)
![Maintenance](https://img.shields.io/maintenance/yes/2021.svg)
Fork from NateScarlet/holiday-cn
中国法定节假日数据 自动每日抓取国务院公告
整合苹果自带节假日

- [x] 提供 JSON 格式节假日数据
- [x] CI 自动更新
- [x] 数据变化时自动发布新版本 ( `Watch` - `Release only` 以获取邮件提醒! )
- [x] [发布页面]提供 JSON 打包下载

数据格式:

[JSON Schema](./schema.json)

```TypeScript
interface Holidays {
  /** 完整年份, 整数。*/
  year: number;
  /** 所用国务院文件网址列表 */
  papers: string[];
  days: {
    /** 节日名称 */
    name: string;
    /** 日期, ISO 8601 格式 */
    date: string;
    /** 是否为休息日 */
    isOffDay: boolean;
  }[]
}
```

## 注意事项

- 年份是按照国务院文件标题年份而不是日期年份，12 月份的日期可能会被下一年的文件影响，因此应检查两个文件。

## 通过互联网使用

数据地址格式:

    https://raw.githubusercontent.com/Lonese/holiday-cn/master/{年份}.json

或使用 JSDelivr：
 
    https://cdn.jsdelivr.net/gh/Lonese/holiday-cn@master/{年份}.json

## ICalendar 订阅

网址格式参见上一节

`{年份}.ics` 为对应年份的节假日

`holiday-cn.ics` 为 3 年前至次年的节假日

感谢 @retanoj 的 ics 格式转换实现

## 作为 git 子模块使用

参见 [Git 工具 - 子模块](https://git-scm.com/book/zh/v2/Git-%E5%B7%A5%E5%85%B7-%E5%AD%90%E6%A8%A1%E5%9D%97)

