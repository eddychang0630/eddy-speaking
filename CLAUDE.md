# eddy-speaking：英文口說 Chunks PWA

靜態網頁 App，沒有建置步驟。GitHub Pages 直接從 `main` 分支根目錄部署：
https://eddychang0630.github.io/eddy-speaking/

## 檔案
- `index.html`：整個 App（CSS + JS 都在裡面）
- `lessons/index.js`：課程清單 `window.LESSON_FILES`
- `lessons/<日期-主題>.js`：每課一檔，內容是 `registerLesson(<標準 JSON>);`，格式見 `lessons/README.md`
  - `type: "video"`：影片課，按家族分組
  - `type: "qa"`：口語問答句，按情境分組
- `audio/`：Kokoro 預先產生的 MP3 和 `audio/manifest.js`（由 `tools/build_audio.py` 產生，不要手動改）
- `sw.js`：Service Worker，快取名稱前綴 `eddy-speaking-`

## 新增一課的流程
1. 把逐字稿或問答句整理成 `lessons/<YYYY-MM-DD-主題>.js`（標準 JSON），加進 `lessons/index.js`
2. 產生自然語音：
   ```powershell
   & "$env:USERPROFILE\Desktop\English class 整理重點\.models\kokoro\venv\Scripts\python.exe" tools\build_audio.py
   ```
   （主聲音 `am_puck`，對話 B 角色 `af_heart`；已有的音檔會跳過）
3. 把 `sw.js` 的 `CACHE_NAME` 版本號加一
4. `git pull --rebase`，commit，push 到 `main`，到 Actions 確認 Pages 部署成功

## 規則
- 學習進度存在 localStorage `eddy-chunks-v1`，key 格式是 `<課程id>:<卡片id>`；課程 id 和卡片 id 不要改，不然進度會對不上
- 和單字 App、句子 App 共用 `eddychang0630.github.io` 網域：只清 `eddy-speaking-` 開頭的快取，不要動 `eddy-flashcard-`、`eddy-sentences-`
- 單字 App 和句子 App 在另一個 repo `eddy-flashcards`，不要在這裡改
- 介面文字用繁體中文
