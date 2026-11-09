# 課程資料格式

> ⚠️ `registerLesson(...)` 括號裡必須是**標準 JSON**（雙引號、沒有註解、沒有結尾逗號），`tools/build_audio.py` 才讀得懂。
> 新增或修改課程後，要重新產生自然語音：見最下面「產生 Kokoro 音檔」。

每一課是一個 `.js` 檔，內容是一次 `registerLesson({...})`。
新增一課：放進這個資料夾，再把檔名加到 `index.js` 的 `LESSON_FILES`。
檔名用「日期-主題」，例如 `2026-11-12-cafe-ordering.js`。`id` 和檔名相同（不含 .js），之後不要改，進度靠它對應。

## 🎬 影片課（type: "video"）
參考 `2026-11-05-chunks.js`。
- `video`：videoId、title、channel、durationFormatted、coreConcept
- `concepts`：影片核心觀念 [{icon, t, p, q}]
- `chapters`：影片章節 [["名稱", 秒數]]
- `groups`：家族 [{id, number, titleZh, titleEn, description, startTime}]
- `cards`：chunk [{id, groupId, written, spoken, meaningZh, usageNote, timestamp, examples:[{en, zh, time}]}]
- `challenges`：聽力抓塊題 [{sentence, targetChunks, spokenHint, zh, time}]
- `dialogue`：{title, startTime, lines:[{speaker:"A"|"B", en, zh, chunksUsed, time}]}
- `shadow`：{title, startTime, sentences:[{en, spoken, zh, time}]}

## 💬 問答句（type: "qa"）
口語問句 + 自然回答，按「情境」分組。對話、跟讀、聽力題沒寫的話，App 會自動從卡片產生。

```js
// 下面是說明用的寫法；實際檔案請寫成標準 JSON
registerLesson({
  id: '2026-11-12-cafe-ordering', type: 'qa', date: '2026-11-12',
  title: '咖啡店點餐與閒聊', short: '11/12 咖啡店',
  description: '一句話說明這一課練什麼',
  groups: [
    { id: 'order', number: 1, titleZh: '點餐', titleEn: 'Ordering', description: '在櫃檯點飲料' },
    { id: 'chat',  number: 2, titleZh: '閒聊', titleEn: 'Small talk' }
  ],
  cards: [
    {
      id: 1, groupId: 'order',
      question: 'Can I get a latte to go?', questionZh: '我可以外帶一杯拿鐵嗎？',
      chunks: ['Can I get', 'to go'],          // 要高亮、拿來出聽力題的語塊
      usageNote: 'Can I get… 比 I want… 自然有禮貌',
      answers: [
        { en: 'Sure, what size would you like?', zh: '好的，您要什麼尺寸？' },
        { en: 'Of course. Anything else?', zh: '當然，還需要別的嗎？', note: '店員常接的一句' }
      ]
    }
  ]
});
```

## 產生 Kokoro 音檔

App 會優先播放 `audio/` 裡預先產生的 MP3（主聲音 `am_puck`，對話 B 角色 `af_heart`），找不到才用系統語音。
新增課程後，在 Windows 的 eddy-speaking 資料夾執行：

```powershell
& "$env:USERPROFILE\Desktop\English class 整理重點\.models\kokoro\venv\Scripts\python.exe" tools\build_audio.py --push
```

已經有的音檔會跳過，只產生新句子；不再用到的舊音檔會刪掉。
