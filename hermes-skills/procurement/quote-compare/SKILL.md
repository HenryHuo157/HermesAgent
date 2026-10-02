---
name: quote-compare
description: "供應商報價對比：多份 Excel/PDF/圖片報價單 → 一張統一對比表（Excel 成品 + 要點結論）。"
version: 1.0.0
author: mainplan
license: proprietary
platforms: [linux]
metadata:
  hermes:
    tags: [採購, 報價, 對比, Excel, Procurement]
---

# 報價對比（Quote Compare）

## 何時使用
用戶上傳兩份或以上的供應商報價單（Excel / PDF / Word / 圖片），要求比較價格、貨期或條款。

## 步驟
1. 逐份讀取報價單：
   - Excel/CSV：用 openpyxl（已預裝）
   - PDF：先試 pdfplumber；不行就 `soffice --headless --convert-to xlsx`（LibreOffice 已預裝在 /usr/local/bin/soffice）
   - 圖片：直接用視覺讀取內容
2. 把每份報價歸一化成同一組欄位：品名／型號／規格、單價、數量、幣種、小計、MOQ（最小起訂量）、貨期、付款條款、報價有效期、是否含稅含運。
3. 同一款物料跨供應商橫向對齊。幣種不同時必須先折算：問用戶當天匯率，或用 fx-rate 技能查詢——嚴禁自己編匯率。
4. 用 openpyxl 生成對比表（xlsx）：
   - 每行一個物料，之後每個供應商一組欄位（單價／總價／貨期／條款）
   - 每行最低價用綠色底色標出；表頭附註匯率假設和各報價單日期
5. 交付：
   - xlsx 用 `MEDIA:` 標籤交付（絕不輸出裸路徑）
   - 回覆開頭先給 3–5 行結論：總價最低的供應商、最大價差、可疑或風險條款

## 規則
- 缺失欄位一律寫「未提供」，嚴禁編造數字
- 單價×數量與小計對不上時，原樣標注差異，不要替供應商「改正」
- 數據衝突時以報價單原文為準，並在表中加註
