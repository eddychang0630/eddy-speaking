# Eddy 口說 Chunks PWA

[開啟 Eddy 口說 Chunks](https://eddychang0630.github.io/eddy-speaking/)

## 結構
- `index.html`：整個 App（版面、樣式、程式）
- `lessons/`：課程資料，每課一個檔案，格式見 `lessons/README.md`
- `manifest.json`、`sw.js`、圖示：PWA 安裝與離線用

## 課程管理
- 標題列點「▼」切換課程；預設是「📅 今日複習」，把所有課程到期的卡片混在一起
- 每課分兩種：🎬 影片課（按家族分組）、💬 問答句（按情境分組）
- 新增一課：在 `lessons/` 加檔案，並寫進 `lessons/index.js`

## 部署與練習進度

- 將 `eddychang0630/eddy-speaking` 的 GitHub Pages 設為從 `main` 分支的 `/(root)` 發布。課程更新提交到這個 repository。
- 同一個瀏覽器的同一儲存環境會沿用原本的練習進度。跨瀏覽器或裝置時，可在設定中匯出及還原進度。

## 本機預覽
在這個資料夾執行 `python -m http.server 8000`，開 http://localhost:8000
（YouTube 內嵌播放器要用網址開才會動）

## 快捷鍵（電腦）
閃卡：Space 翻牌、P 播音、←/→ 切換、1 熟練、2 再練
跟讀 / 對話：Space 播放 / 停止
聽力抓塊：Space 播放、Enter 確認 / 下一題
