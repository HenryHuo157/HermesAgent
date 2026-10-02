---
name: fx-rate
description: "匯率速算：HKD/CNY/USD/EUR/JPY 互轉，單筆或整張價格表，註明匯率來源與日期。"
version: 1.0.0
author: mainplan
license: proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [匯率, 採購, 換算, FX]
---

# 匯率速算（FX Rate）

## 何時使用
用戶需要貨幣換算：HKD / CNY / USD / EUR / JPY 之間，單個金額或整張價格表。

## 步驟
1. 用聯網搜索查當日中間價，輸出時注明「日期 + 來源」。查不到、或用戶指定了匯率，就用用戶的匯率並注明「用戶提供」。
2. 輸出格式：
   - 單筆：`1,000 USD ≈ 7,812 HKD（匯率 7.812，YYYY-MM-DD 中間價，來源）`
   - 多筆／整表：小表格（原幣金額｜匯率｜折算金額）
3. 整張價格表換算：讀原表 → 新增一列折算金額 → openpyxl 輸出新表 → `MEDIA:` 標籤交付
4. 大額採購在結尾加一句匯率波動提示（僅提示，不構成任何建議）

## 規則
- 匯率必須帶來源和日期，嚴禁憑記憶報數
- 金額保留兩位小數；表內幣種符號寫清楚（HK$／¥／US$）
