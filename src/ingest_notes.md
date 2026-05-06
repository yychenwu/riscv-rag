# ingest.py 架構說明

## 功能概述

把 `data/` 資料夾裡的 PDF 切段、向量化，存進 ChromaDB 向量資料庫。
只需要跑一次，新增 PDF 時重跑。

---

## Pipeline 流程

```
PDF 檔案
  ↓ PyPDFLoader               讀每一頁，帶 metadata（檔名、頁碼）
  ↓ RecursiveCharacterTextSplitter   切成 1000 字元的 chunk，重疊 200 字元
  ↓ VoyageAIEmbeddings        每個 chunk 轉成 1024 維向量
  ↓ ChromaDB                  向量 + 原文 + metadata 存到 db/ 資料夾
```

類比：Synthesis → P&R → 燒進 FPGA，做完結果存著，不用重做。

---

## 逐段說明

### 環境載入

```python
from dotenv import load_dotenv
load_dotenv()
```

從 `.env` 讀取 `VOYAGE_API_KEY`。Voyage SDK 會自動抓這個環境變數，不需要手動傳入。

---

### 路徑設定

```python
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_DIR   = os.path.join(os.path.dirname(__file__), "..", "db")
```

`__file__` 是當前檔案的絕對路徑，`".."` 往上一層到專案根目錄。
不用相對路徑是因為相對路徑依賴執行時的工作目錄，容易出錯。

---

### 讀 PDF

```python
loader = PyPDFLoader(path)
docs = loader.load()
```

每頁變成一個 `Document` 物件：

```
Document(
    page_content = "這頁的文字內容...",
    metadata = {"source": "data/riscv-spec.pdf", "page": 42}
)
```

metadata 在查詢結果裡用來標示「來源 PDF + 頁碼」。

---

### 切段（Chunking）

```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""],
)
```

**為什麼切？** 整頁塞進去向量語意太模糊，切小段才能精準檢索。

**separators 順序**：優先從段落（`\n\n`）切，再換行，再空格，最後才強切。盡量保持語意完整。

**chunk_overlap=200（20% 重疊）**：類比訊號處理的 windowing，避免重要語句被切在兩個 chunk 的邊界。若查詢結果常差一點，可調高至 500（50% 重疊），但 chunk 數量會增加約 50%。

---

### Embedding

```python
embeddings = VoyageAIEmbeddings(model="voyage-3.5")
```

建立呼叫 Voyage API 的物件，此時還沒送資料。真正的 API call 在下一步 `Chroma.from_documents()` 觸發。

`voyage-3.5`：通用高品質多語言模型，適合技術文件。

---

### 存入 ChromaDB

```python
db = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_DIR,
)
```

這一行做三件事：
1. 把所有 chunk 分批送給 Voyage API → 拿回 1024 維向量
2. 向量 + 原文 + metadata 一起存進 ChromaDB
3. `persist_directory` 讓資料庫寫到硬碟，重開 Python 還找得到

---

## 參數調整參考

| 參數 | 現值 | 調大效果 | 調小效果 |
|---|---|---|---|
| `chunk_size` | 1000 | 語意較完整，但向量較模糊 | 向量精準，但可能切斷語句 |
| `chunk_overlap` | 200 | 邊界語意保留更好，chunk 數增加 | chunk 數少，邊界可能遺漏 |
| `top_k`（query.py） | 5 | context 更豐富，但雜訊多 | 快但可能漏掉相關內容 |

---

## 容量規模

- 現況：913 頁 → 2683 chunks → ~10MB 硬碟
- ChromaDB 單機可支援數百萬向量，目前規模完全沒問題
- Voyage 免費額度 2 億 tokens，整個 4 份 PDF 計畫約用 1%

---

## 重跑時機

- 新增 PDF 到 `data/` 後
- 修改 `chunk_size` 或 `chunk_overlap` 後
- 換 embedding 模型後

重跑前需先刪掉舊資料庫：`rm -rf db/`
