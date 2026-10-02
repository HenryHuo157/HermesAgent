// 《1688 選品篩選工作冊》— 採購部實戰工具冊（配合 Luma AI）
const pptxgen = require("pptxgenjs");

const p = new pptxgen();
p.layout = "LAYOUT_WIDE";           // 13.33 × 7.5"
p.author = "Luma · Mainplan";
p.title = "1688 選品篩選工作冊";

// ---- 調色板：鑄鐵黑 / 深青 / 火焰橙（廚具火候感）----
const INK = "23272F", BG = "FFFFFF";
const PRIMARY = "1E6E68", PRIMARY_D = "15514C", TINT = "EAF3F2";
const ACCENT = "E8590C", ACCENT_T = "FDEEE3";
const TEXT = "1F2937", MUTED = "64748B", LINE = "E2E8F0", FAINT = "C7D2DD";
const F = "Microsoft JhengHei";
const W = 13.33, M = 0.5;

const sh = () => ({ type: "outer", color: "1A2330", blur: 7, offset: 2, angle: 45, opacity: 0.14 });

function header(s, kicker, title) {
  s.background = { color: BG };
  s.addText(kicker, { x: M, y: 0.34, w: 9, h: 0.3, fontSize: 12, bold: true, color: ACCENT, fontFace: F, margin: 0 });
  s.addText(title, { x: M, y: 0.62, w: W - 2 * M, h: 0.62, fontSize: 26, bold: true, color: TEXT, fontFace: F, margin: 0 });
}
function band(s, text, y = 6.55) {
  s.addShape("rect", { x: 0, y, w: W, h: 0.95 - (6.55 - y) * 0.5, fill: { color: TINT } });
  s.addText(text, { x: M, y, w: W - 2 * M, h: 0.95 - (6.55 - y) * 0.5, fontSize: 12.5, color: PRIMARY_D, fontFace: F, valign: "middle", margin: 0 });
}
function checkbox(s, x, y, size = 0.3) {
  s.addShape("rect", { x, y, w: size, h: size, fill: { color: BG }, line: { color: PRIMARY, width: 1.75 } });
}
function hairline(s, x, y, w) {
  s.addShape("line", { x, y, w, h: 0, line: { color: LINE, width: 0.75 } });
}

// ============ S1 封面 ============
let s = p.addSlide();
s.background = { color: INK };
s.addText("選", { x: 7.6, y: 0.4, w: 5.6, h: 6.8, fontSize: 330, bold: true, color: "2B313C", fontFace: F, align: "center", valign: "middle", margin: 0 });
s.addText("MAINPLAN 敏寶 · 採購部實戰手冊", { x: 0.9, y: 2.0, w: 9, h: 0.4, fontSize: 14, bold: true, color: ACCENT, fontFace: F, margin: 0, charSpacing: 2 });
s.addText("1688 選品篩選工作冊", { x: 0.9, y: 2.45, w: 9.6, h: 1.15, fontSize: 52, bold: true, color: "FFFFFF", fontFace: F, margin: 0 });
s.addText("邊逛邊對照：初篩 · 評估 · 背調 · 詢價，一冊搞掂", { x: 0.9, y: 3.75, w: 9, h: 0.5, fontSize: 17, color: "B9C6D6", fontFace: F, margin: 0 });
s.addShape("line", { x: 0.9, y: 4.55, w: 2.2, h: 0, line: { color: ACCENT, width: 3 } });
s.addText("配合 Luma AI 使用 · 2026 年 10 月版", { x: 0.9, y: 4.75, w: 9, h: 0.4, fontSize: 12.5, color: "8A97A8", fontFace: F, margin: 0 });

// ============ S2 六步流程 ============
s = p.addSlide();
header(s, "工作流程", "選品六步：從線索到打樣");
const steps = [
  ["01", "找線索", "1688／淘寶／展會，照常你自己逛，眼光不可替代", "你的活"],
  ["02", "三分鐘初篩", "五條硬性條件逐條打勾，過不了的直接跳過", "頁 3"],
  ["03", "填評估卡", "一個品一頁：價格、賣點、認證、風險寫齊", "頁 4·5"],
  ["04", "工廠背調", "工廠還是貿易商？評分 ≥18 分才進詢價", "頁 6"],
  ["05", "詢價對比", "必問八條逐條問，多份報價上對比表", "頁 7·8"],
  ["06", "打樣決策", "打樣／試單／放棄，結論圈進評估卡", "頁 4"],
];
const cw = 1.93, gap = 0.11, y0 = 1.55, ch = 3.5;
steps.forEach((st, i) => {
  const x = M + i * (cw + gap);
  const last = i === steps.length - 1;
  s.addShape("roundRect", { x, y: y0, w: cw, h: ch, fill: { color: BG }, line: { color: last ? ACCENT : LINE, width: last ? 1.75 : 1 }, rectRadius: 0.07, shadow: sh() });
  s.addText(st[0], { x: x + 0.18, y: y0 + 0.16, w: 1.2, h: 0.5, fontSize: 24, bold: true, color: last ? ACCENT : PRIMARY, fontFace: F, margin: 0 });
  s.addText(st[1], { x: x + 0.18, y: y0 + 0.72, w: cw - 0.36, h: 0.4, fontSize: 15, bold: true, color: TEXT, fontFace: F, margin: 0 });
  s.addText(st[2], { x: x + 0.18, y: y0 + 1.18, w: cw - 0.36, h: 1.55, fontSize: 11.5, color: MUTED, fontFace: F, margin: 0, lineSpacingMultiple: 1.2 });
  hairline(s, x + 0.18, y0 + 2.92, cw - 0.36);
  s.addText(st[3], { x: x + 0.18, y: y0 + 3.02, w: cw - 0.36, h: 0.35, fontSize: 12, bold: true, color: last ? ACCENT : PRIMARY, fontFace: F, margin: 0 });
  if (i < steps.length - 1) {
    s.addText("→", { x: x + cw - 0.02, y: y0 + 1.4, w: gap + 0.06, h: 0.5, fontSize: 15, bold: true, color: FAINT, fontFace: F, align: "center", valign: "middle", margin: 0 });
  }
});
band(s, "每個候選品一張評估卡，月度選品會直接拿這本冊子過單；Luma 能代填的部分見頁 9。", 5.55);

// ============ S3 三分鐘初篩 ============
s = p.addSlide();
header(s, "STEP 02 · 三分鐘初篩", "五條硬性條件，一條不過就跳過");
const checks = [
  ["目標客群匹配嗎？", "我們做歐美廚具零售／批發，內銷雜貨款不跟"],
  ["毛利空間夠嗎？", "1688 價 ≤ 推測零售價 × 25%（示例門檻，部門可調）"],
  ["起訂量扛得住嗎？", "首單 ≤ 500 件，或支持混批／現貨代發"],
  ["有差異化嗎？", "比現有貨盤或市面大路貨多一個賣點：省空間／材質／使用場景"],
  ["侵權風險排查了嗎？", "大牌外觀款、帶專利號的慎碰——先查再談，談不攏就放"],
];
checks.forEach((c, i) => {
  const y = 1.62 + i * 0.93;
  checkbox(s, M, y + 0.12);
  s.addText(c[0], { x: M + 0.55, y, w: 6.6, h: 0.42, fontSize: 15.5, bold: true, color: TEXT, fontFace: F, margin: 0 });
  s.addText(c[1], { x: M + 0.55, y: y + 0.42, w: 11.3, h: 0.38, fontSize: 12, color: MUTED, fontFace: F, margin: 0 });
  if (i < checks.length - 1) hairline(s, M, y + 0.86, W - 2 * M);
});
band(s, "五格全打勾 → 進入評估卡（頁 4）；任何一格過不了 → 記下原因就跳過，不糾纏。");

// ============ S4 評估卡模板 ============
s = p.addSlide();
header(s, "STEP 03 · 單品深評", "選品評估卡（複製本頁，一個品一頁）");
s.addShape("roundRect", { x: M, y: 1.5, w: 4.0, h: 4.55, fill: { color: "FAFCFC" }, line: { color: PRIMARY, width: 1.5, dashType: "dash" }, rectRadius: 0.08 });
s.addText("產品截圖\n貼這裡", { x: M, y: 1.5, w: 4.0, h: 4.55, fontSize: 16, color: FAINT, fontFace: F, align: "center", valign: "middle", margin: 0, lineSpacingMultiple: 1.3 });
s.addText("正反面／細節圖可縮拼，帶上 1688 頁面連結", { x: M, y: 6.12, w: 4.2, h: 0.35, fontSize: 10.5, color: MUTED, fontFace: F, margin: 0 });
const fields4 = ["品名／型號", "材質／規格", "1688 價格", "推測零售價", "毛利空間（對照 25% 門檻）", "MOQ／階梯價", "交期", "差異化賣點", "目標客群／渠道", "認證要求"];
const fx = 4.85, fw = 3.95, fhh = 0.9;
fields4.forEach((f, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = fx + col * (fw + 0.2), y = 1.5 + row * fhh;
  s.addText(f, { x, y, w: fw, h: 0.3, fontSize: 11, bold: true, color: MUTED, fontFace: F, margin: 0 });
  s.addShape("line", { x, y: y + 0.62, w: fw, h: 0, line: { color: FAINT, width: 1 } });
});
s.addText("結論：", { x: fx, y: 6.25, w: 0.9, h: 0.5, fontSize: 14, bold: true, color: TEXT, fontFace: F, valign: "middle", margin: 0 });
["打樣", "試單", "放棄"].forEach((t, i) => {
  s.addShape("roundRect", { x: fx + 0.95 + i * 1.5, y: 6.25, w: 1.32, h: 0.5, fill: { color: BG }, line: { color: i === 2 ? FAINT : PRIMARY, width: 1.5 }, rectRadius: 0.25 });
  s.addText(t, { x: fx + 0.95 + i * 1.5, y: 6.25, w: 1.32, h: 0.5, fontSize: 13, bold: true, color: i === 2 ? MUTED : PRIMARY, fontFace: F, align: "center", valign: "middle", margin: 0 });
});
s.addText("圈選一項", { x: fx + 5.6, y: 6.25, w: 2, h: 0.5, fontSize: 11, color: MUTED, fontFace: F, valign: "middle", margin: 0 });

// ============ S5 評估卡示範 ============
s = p.addSlide();
header(s, "STEP 03 · 單品深評", "選品評估卡 · 填寫示範");
s.addText("示範頁 · 數據為虛構", { x: 9.9, y: 0.4, w: 2.9, h: 0.3, fontSize: 11, bold: true, color: ACCENT, fontFace: F, align: "right", margin: 0 });
s.addShape("roundRect", { x: M, y: 1.5, w: 4.0, h: 4.55, fill: { color: "FAFCFC" }, line: { color: PRIMARY, width: 1.5, dashType: "dash" }, rectRadius: 0.08 });
s.addText("截圖位置\n（示範略）", { x: M, y: 1.5, w: 4.0, h: 4.55, fontSize: 16, color: FAINT, fontFace: F, align: "center", valign: "middle", margin: 0, lineSpacingMultiple: 1.3 });
s.addText("重點提醒：矽膠要「鉑金矽膠」，普通矽膠有異味退貨風險", { x: M, y: 6.12, w: 4.4, h: 0.55, fontSize: 10.5, color: ACCENT, fontFace: F, margin: 0 });
const filled = [
  ["品名／型號", "摺疊式矽膠瀝水籃"], ["材質／規格", "食品級矽膠＋PP 框"],
  ["1688 價格", "¥18.5（1000 件價）"], ["推測零售價", "HK$99"],
  ["毛利空間", "進價佔 19% ✓（門檻 25%）"], ["MOQ／階梯價", "300 件起，可混色"],
  ["交期", "現貨 7 天"], ["差異化賣點", "摺疊後僅 3cm，省頭程運費"],
  ["目標客群／渠道", "露營／小廚房客群"], ["認證要求", "FDA＋LFGB 食品級測試報告"],
];
filled.forEach((f, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = fx + col * (fw + 0.2), y = 1.5 + row * fhh;
  s.addText(f[0], { x, y, w: fw, h: 0.3, fontSize: 11, bold: true, color: MUTED, fontFace: F, margin: 0 });
  s.addText(f[1], { x, y: y + 0.28, w: fw, h: 0.34, fontSize: 12.5, color: TEXT, fontFace: F, margin: 0 });
  hairline(s, x, y + 0.66, fw);
});
s.addText("結論：", { x: fx, y: 6.25, w: 0.9, h: 0.5, fontSize: 14, bold: true, color: TEXT, fontFace: F, valign: "middle", margin: 0 });
["打樣", "試單", "放棄"].forEach((t, i) => {
  const on = i === 0;
  s.addShape("roundRect", { x: fx + 0.95 + i * 1.5, y: 6.25, w: 1.32, h: 0.5, fill: { color: on ? ACCENT : BG }, line: { color: on ? ACCENT : (i === 2 ? FAINT : PRIMARY), width: 1.5 }, rectRadius: 0.25 });
  s.addText(t, { x: fx + 0.95 + i * 1.5, y: 6.25, w: 1.32, h: 0.5, fontSize: 13, bold: true, color: on ? "FFFFFF" : (i === 2 ? MUTED : PRIMARY), fontFace: F, align: "center", valign: "middle", margin: 0 });
});

// ============ S6 工廠評分表 ============
s = p.addSlide();
header(s, "STEP 04 · 工廠背調", "供應商評分表：≥18 分才進詢價");
const th = { bold: true, color: "FFFFFF", fill: { color: PRIMARY }, fontFace: F, fontSize: 12.5, valign: "middle" };
const td = (t, o = {}) => ({ text: t, options: { fontFace: F, fontSize: 12, color: TEXT, valign: "middle", ...o } });
s.addTable([
  [{ text: "維度", options: th }, { text: "5 分長這樣", options: th }, { text: "1 分長這樣", options: th }, { text: "得分", options: th }],
  [td("成立年限", { bold: true }), td("5 年以上，有出口記錄"), td("新註冊，查無歷史"), td("")],
  [td("註冊資本", { bold: true }), td("100 萬人民幣以上"), td("10 萬以下"), td("")],
  [td("主營匹配", { bold: true }), td("主營就是這個品類"), td("五金百貨什麼都做"), td("")],
  [td("外貿痕跡", { bold: true }), td("官網＋展會＋出口數據"), td("只有內銷 1688 店"), td("")],
  [td("認證文件", { bold: true }), td("能即時提供測試報告"), td("「可以做的啦」說不出編號"), td("")],
], { x: M, y: 1.5, w: W - 2 * M, colW: [2.3, 4.6, 4.63, 0.8], rowH: 0.56, border: { pt: 0.75, color: LINE }, fill: { color: BG }, margin: 0.08 });
["≥18 進詢價", "12–17 先視頻／實地驗廠", "<12 放棄"].forEach((t, i) => {
  const on = i === 0;
  s.addShape("roundRect", { x: M + i * 3.1, y: 5.15, w: 2.95, h: 0.52, fill: { color: on ? PRIMARY : BG }, line: { color: on ? PRIMARY : FAINT, width: 1.5 }, rectRadius: 0.24 });
  s.addText(t, { x: M + i * 3.1, y: 5.15, w: 2.95, h: 0.52, fontSize: 12.5, bold: true, color: on ? "FFFFFF" : MUTED, fontFace: F, align: "center", valign: "middle", margin: 0 });
});
band(s, "定身份：經營範圍含「製造」＋工業區地址＝工廠；只寫「貿易」＋寫字樓＝貿易商。貿易商也能用，但價格與品質責任要多盯一層。", 5.95);

// ============ S7 認證速查 ============
s = p.addSlide();
header(s, "STEP 05 · 合規底線", "廚具認證速查：問工廠要這些文件");
s.addTable([
  [{ text: "品類", options: th }, { text: "主要市場認證", options: th }, { text: "問工廠要的文件", options: th }],
  [td("食品接觸（鍋／杯／餐具）", { bold: true }), td("歐盟 LFGB・1935/2004；美國 FDA；內銷 GB 4806"), td("食品級材質證明＋第三方測試報告（1 年內有效）")],
  [td("小家電（空氣炸鍋等）", { bold: true }), td("歐盟 CE＋RoHS；美國 ETL／UL；內銷 CCC"), td("證書編號（官網可驗真）＋整機測試報告")],
  [td("刀具剪刀", { bold: true }), td("歐盟 1935/2004＋目標國刀具有效標準"), td("材質報告＋硬度／鋒利度測試")],
  [td("兒童餐具", { bold: true }), td("食品級＋歐盟 EN 14372"), td("重金屬遷移＋鄰苯二甲酸酯測試")],
], { x: M, y: 1.55, w: W - 2 * M, colW: [3.1, 4.9, 4.33], rowH: 0.78, border: { pt: 0.75, color: LINE }, fill: { color: BG }, margin: 0.08 });
band(s, "本頁是速查不是法律意見；進新市場先查當地法規。證書編號一定要上發證機構官網驗真，截图不算數。", 5.75);

// ============ S8 必問八條 + 紅旗 ============
s = p.addSlide();
header(s, "STEP 05 · 詢價", "詢價必問八條與紅旗信號");
const qs = [
  "材質證明與測試報告，能不能提供？",
  "車間實拍／視頻驗廠，現在就約",
  "打樣週期與打樣費，可不可退？",
  "MOQ 與階梯價：300／1000／3000 件",
  "交期與旺季排產，最晚什麼時候能出？",
  "驗貨標準：AQL 2.5？全檢？誰付費？",
  "付款方式：30% 訂金＋見提單副本付尾款",
  "包裝與嘜頭：能不能做我們的？",
];
qs.forEach((q, i) => {
  const y = 1.55 + i * 0.58;
  s.addText(String(i + 1).padStart(2, "0"), { x: M, y, w: 0.5, h: 0.42, fontSize: 14, bold: true, color: ACCENT, fontFace: F, margin: 0 });
  s.addText(q, { x: M + 0.55, y, w: 5.9, h: 0.42, fontSize: 13, color: TEXT, fontFace: F, margin: 0 });
  if (i < qs.length - 1) hairline(s, M, y + 0.5, 6.45);
});
s.addShape("roundRect", { x: 7.45, y: 1.55, w: 5.38, h: 4.6, fill: { color: ACCENT_T }, rectRadius: 0.1 });
s.addText("紅旗信號：見一個，緩一緩", { x: 7.75, y: 1.8, w: 4.9, h: 0.4, fontSize: 15, bold: true, color: ACCENT, fontFace: F, margin: 0 });
const flags = [
  "拒絕視頻驗廠，只肯發照片",
  "報價明顯低於行情 30% 以上",
  "只收全款，或走私人帳戶",
  "說不出測試報告編號",
  "一味催單催款，避談品質細節",
];
flags.forEach((f, i) => {
  const y = 2.35 + i * 0.72;
  s.addShape("rect", { x: 7.75, y: y + 0.06, w: 0.16, h: 0.16, fill: { color: ACCENT } });
  s.addText(f, { x: 8.05, y, w: 4.6, h: 0.4, fontSize: 13, color: TEXT, fontFace: F, margin: 0 });
});
band(s, "工廠的每條回覆記進評估卡背面——談判時有據可依，換供應商時有檔可查。", 6.5);

// ============ S9 Luma 代勞 ============
s = p.addSlide();
header(s, "配合 Luma AI", "髒活交給 Luma，你只做判斷");
const ai = [
  ["「我想找新品」", "採購經理提問模式", "不知道從哪開始？它一題一題問你，帶你走完整個選品流程"],
  ["「評估這個新品」（截圖拖進對話）", "選品評估卡初稿", "賣點、售價區間、認證清單、風險、要問工廠的問題，一次列全"],
  ["「查一下這家工廠的底細」", "工廠背調卡", "工廠還是貿易商＋風險記錄＋針對性驗廠提問清單"],
  ["「這幾份報價幫我對比」（拖文件）", "統一對比表", "單價／貨期／條款橫向對齊，最低價高亮，幣種自動折算"],
  ["「1,000 美元換港幣是多少」", "匯率速算", "當日中間價，帶來源；整張價格表也能批量換"],
];
ai.forEach((a, i) => {
  const y = 1.5 + i * 0.98;
  s.addShape("roundRect", { x: M, y, w: 5.1, h: 0.85, fill: { color: TINT }, rectRadius: 0.08 });
  s.addText(a[0], { x: M + 0.2, y, w: 4.75, h: 0.85, fontSize: 12, bold: true, color: PRIMARY_D, fontFace: F, valign: "middle", margin: 0 });
  s.addText("→", { x: 5.72, y, w: 0.5, h: 0.85, fontSize: 18, bold: true, color: ACCENT, fontFace: F, valign: "middle", align: "center", margin: 0 });
  s.addText(a[1], { x: 6.35, y: y + 0.04, w: 6.4, h: 0.36, fontSize: 14, bold: true, color: TEXT, fontFace: F, margin: 0 });
  s.addText(a[2], { x: 6.35, y: y + 0.42, w: 6.4, h: 0.4, fontSize: 11, color: MUTED, fontFace: F, margin: 0 });
});
band(s, "網頁 47.243.79.144 或飛書喊它；輸出的是可下載文件，直接歸檔進這本冊子對應的頁。", 6.5);

// ============ S10 封底 ============
s = p.addSlide();
s.background = { color: INK };
s.addText("貨比三家，先比這一冊。", { x: 0.9, y: 2.5, w: 11.5, h: 1.0, fontSize: 42, bold: true, color: "FFFFFF", fontFace: F, margin: 0 });
s.addText("每個候選品一頁卡；月度選品會，用冊子過單。", { x: 0.9, y: 3.65, w: 10, h: 0.5, fontSize: 16, color: "B9C6D6", fontFace: F, margin: 0 });
s.addShape("line", { x: 0.9, y: 4.5, w: 2.2, h: 0, line: { color: ACCENT, width: 3 } });
s.addText("Luma · 敏寶團隊 AI　|　網頁 47.243.79.144　|　飛書搜 HarmesAgent", { x: 0.9, y: 4.72, w: 11, h: 0.4, fontSize: 12.5, color: "8A97A8", fontFace: F, margin: 0 });

p.writeFile({ fileName: "1688選品篩選工作冊.pptx" }).then(() => console.log("OK 10 slides"));
