# RISC-V RAG 知識庫 — 開發日誌

> 記錄每個決策背後的原因，讓未來的自己（和面試官）看懂這個專案是怎麼長出來的。

---

## 為什麼做這個專案？

**起點（2026-05-03）：** 分析 NVIDIA 新竹 SOC AI Application Engineer 職缺（JR2016498）。

JD 的核心要求是：用 LLM / RAG / Agent 幫硬體設計團隊打造內部 AI 工具。這個職缺有一個特殊之處：它同時需要 AI 工程能力（LLM 應用、RAG pipeline）和半導體領域知識（SoC、RTL、匯流排協定）。

這是一個我有機會的缺口——市面上大多數 AI 工程師沒有硬體背景，而我有 13 年的 CPU IP 經驗（ARC-V、AXI4、Interrupt Architecture）。但我缺 LLM 應用開發的實作經驗。

**決策：不上課，直接做專案。**

與其看 LangChain 教程，不如直接做一個用得到的東西。專案主題選 RISC-V 規格知識庫，原因：
1. 我對這些文件有深度理解（AIA 甚至親自翻譯過）
2. 跨多份文件的問答，才能展示 RAG 的真正價值
3. 做完直接是工作工具，不只是 demo

---

## Phase 1：理解 RAG 是什麼（2026-05-03～04）

**做了什麼：** 釐清 RAG pipeline 每個零件的用途。

**為什麼要先弄懂概念？** 工具要用對地方。LLM 本身有兩個根本限制：

1. **Context window 有限**：即使 Claude 有很長的 context，把 2000 頁的 RISC-V spec 整份丟進去，費用極高、速度極慢，而且有「Lost in the Middle」問題——模型對文件中間段落的記憶明顯比開頭和結尾差。

2. **無法查詢自己沒看過的資料**：LLM 的知識是訓練時截止的，無法即時存取你自己的私有文件。

**RAG 的解法：** 把文件事先切段、向量化，存進資料庫。查詢時只取出最相關的幾段，送給 LLM 回答。這樣每次查詢只需要看幾頁，不是幾千頁。

**Pipeline 全貌：**
```
建置階段（一次性）：
PDF → 切段（chunks） → Embedding（向量化） → ChromaDB（向量資料庫）

查詢階段（每次使用）：
問題 → 向量化 → 相似度搜尋 → 取出最相關 chunks → 送給 Claude → 回答
```

---

## Phase 2：環境建置（2026-05-03～05）

**做了什麼：** 安裝 Python 環境、所有套件、設定 API Key。

**為什麼用系統 Python（/usr/bin/python3）而不建 venv？**
macOS 上的 PEP 668 限制讓系統 pip 需要加 `--break-system-packages` 才能安裝，但對於個人開發機、單一專案的場景，這樣做夠了，不需要額外的虛擬環境複雜度。

**安裝的套件和各自的角色：**

| 套件 | 用途 |
|------|------|
| `anthropic` | 呼叫 Claude API 產生回答 |
| `voyageai` / `langchain-voyageai` | Embedding 模型（把文字轉成向量） |
| `langchain-community` | PDF 載入工具（PyPDFLoader） |
| `langchain-chroma` | LangChain 與 ChromaDB 的橋接層 |
| `chromadb` | 向量資料庫，存放所有 chunk 的向量 |
| `pypdf` | 讀取 PDF 原始文字 |
| `python-dotenv` | 從 .env 檔讀取 API Key |

**為什麼選 Voyage AI 做 Embedding，不用 OpenAI？**
Anthropic 官方推薦 Voyage AI 搭配 Claude。`voyage-3.5` 在技術文件的語意理解上表現優於 OpenAI 的 text-embedding 系列，且與 Claude 的訓練分佈更接近。

**為什麼選 ChromaDB，不用 Pinecone 或 Weaviate？**
ChromaDB 是本機向量資料庫，完全免費、不需要網路、零配置。對於第一個 RAG 專案，這是最快上手的選擇。等規模變大、需要多人共用時，才值得換成雲端向量庫。

**API Key 踩坑：**
`ANTHROPIC_API_KEY` 不能寫進 `~/.zshrc`——這會讓 Claude Code CLI 的認證出問題（兩個 key 衝突）。正確做法是放在專案的 `.env` 檔，用 `python-dotenv` 讀取。

---

## Phase 3：核心程式碼（2026-05-05～06）

**做了什麼：** 寫 `ingest.py`（建庫）和 `query.py`（查詢）。

### ingest.py — 把 PDF 變成可搜尋的資料庫

**步驟拆解：**

```python
# 1. 掃描所有 PDF
pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]

# 2. 用 PyPDFLoader 逐頁讀取，每頁自動帶 metadata（檔名、頁碼）
loader = PyPDFLoader(path)
docs = loader.load()

# 3. 用 RecursiveCharacterTextSplitter 切段
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,    # 每段最多 2000 字元（約 500 tokens）
    chunk_overlap=200,  # 相鄰段重疊 200 字元，保留跨段的上下文
)

# 4. 用 Voyage AI 把每個 chunk 轉成向量
embeddings = VoyageAIEmbeddings(model="voyage-3.5")

# 5. 存進 ChromaDB
db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=DB_DIR)
```

**為什麼 chunk_size 選 2000？**
初版用 1000 字元（約 250 tokens），太小了。技術規格文件的段落通常跨越幾百字，切太細會把完整的概念拆成兩半，搜尋時拿到的 chunk 缺乏上下文。2000 字元約等於一個完整的規格小節，語意更完整。

**chunk_overlap 的用途：**
如果一個重要的句子剛好落在兩個 chunk 的交界，沒有 overlap 就會被切斷。200 字元的重疊讓相鄰 chunk 各自保留對方的結尾/開頭，確保沒有語意遺漏。

### query.py — 問問題、找答案

```python
# 1. 把問題也轉成向量（必須用同一個 embedding model）
embeddings = VoyageAIEmbeddings(model="voyage-3.5")
db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

# 2. 向量相似度搜尋，取最相近的 5 個 chunk
docs = db.similarity_search(question, k=5)

# 3. 組 prompt 送給 Claude Haiku
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    ...
)
```

**為什麼 ingest 和 query 要用同一個 embedding model？**
Embedding 是把文字映射到一個高維空間的特定位置。如果建庫用 Voyage AI，查詢也必須用 Voyage AI——才能在同一個「座標系」裡比較距離。換了 embedding model，所有向量都要重建。

**為什麼用 Claude Haiku，不用 Sonnet 或 Opus？**
RAG 的 LLM 任務是「根據提供的段落整理回答」，不需要複雜推理。Haiku 速度快（通常 2-3 秒）、成本極低（約每次查詢 NT$0.01），完全夠用。Sonnet 和 Opus 適合需要深度推理的任務。

**初始結果：** 1 份 PDF（913 頁）→ 2683 chunks。

---

## Phase 4：知識庫大擴充（2026-06-01）

**做了什麼：** 從 1 份 PDF 擴充到 27 份 RISC-V 官方規格，重建向量庫。

**為什麼從 1 份 PDF 開始，而不是一開始就收集 27 份？**
工程開發的核心原則：先讓系統跑起來，再擴展。如果一開始就試圖把 27 份 PDF 全部搞定，很容易在環境設置、格式問題、API 費用等地方卡住，還沒看到任何結果就放棄了。先用 1 份 PDF 驗證 pipeline 完全正確，再擴展素材。

**收集 27 份 PDF 的過程與發現：**

這個過程本身就是學習。遇到幾個有趣的問題：

1. **Repo 搬家問題：** 許多 RISC-V 規格的 GitHub repo 已從 `riscv` org 搬到 `riscvarchive` org，直接搜 `riscv/riscv-indirect-csr-access` 找不到，要搜 `riscvarchive/riscv-indirect-csr-access`。自動化搜尋時必須追蹤 HTTP 301 redirect。

2. **規格已合併問題：** Smepmp、CMO（Cache Management Operations）、Zfinx 等擴展已被合併進統一的 ISA Manual，不再有獨立的 PDF release。認識這件事很重要——它代表這些規格已「畢業」進主流。

3. **非 Release 的 PDF：** SPMP for Hypervisor 的 PDF 直接放在 repo 的 `main` branch 裡（不在 GitHub Release），要用 `raw.githubusercontent.com` 路徑才能下載。

4. **跨組織的 repo：** IOPMP 在 `riscv-non-isa/riscv-iopmp`，不是 `iopmp-spec`。WorldGuard 的 PDF 甚至是在 RISC-V 郵件論壇的附件裡。

**最終結果：** 27 份 PDF、2073 頁 → 3224 chunks（chunk_size 調大到 2000）。

---

## Phase 5：回答品質問題與修正（2026-06-01）

**發現了什麼問題？**

測試時問了兩個問題：

> 問：「rv32, rv64差別在什麼地方」
> 答：（包含應用場景：RV32 適合嵌入式，RV64 適合需要大地址空間的系統）

> 問：「rv32, rv64適合的應用場景 在SPEC裡面有描述嗎」
> 答：「我無法找到關於應用場景的詳細描述」

**矛盾點：** 如果文件沒有描述應用場景，第一個問題的回答哪來的？

**原因：RAG Hallucination（混合幻覺）**

這是 RAG 系統一個很常見的問題。當 prompt 沒有明確限制時，LLM 會無縫地把兩種知識混合在一起：
- **從文件撈到的內容**（address width、ADDW 指令、Sv32/Sv39 等）
- **LLM 自己訓練資料裡的知識**（應用場景是 Claude 從網路文章裡學到的，不是 spec 說的）

用戶感受不到差別，但技術上這是很嚴重的問題——RAG 的核心價值是「基於文件的可靠回答」，如果混入了 LLM 的訓練知識，就失去了「可溯源」的保障。

**修正方式：強制結構化輸出**

把 prompt 改成要求 Claude 強制分兩個區塊回答：

```
## 📄 文件依據
→ 只能引用提供的文件段落，每句話標上來源 (來源 #N, p.X)
→ 文件沒提到的，要明確寫「（文件未載）」

## 🧠 補充參考（訓練知識）
→ 只放文件沒有、但 Claude 訓練資料裡有的補充
→ 每點開頭加「⚠️ 非文件來源」
→ 若無補充，寫「（無額外補充）」
```

同時在回答末尾加上被引用的 PDF 清單（檔名 + 頁碼）。

**效果：** 現在每個回答都清楚標示「這是 spec 說的」和「這是 AI 自己推斷的」，完全可追溯。

---

## 目前狀態（2026-06-01）

```
rag-project/
├── data/          # 27 份 RISC-V spec PDF（24 MB）
├── db/            # ChromaDB 向量庫（70 MB，3224 chunks）
├── src/
│   ├── ingest.py  # 建庫腳本（chunk_size=2000）
│   └── query.py   # 查詢介面（分文件依據/訓練知識兩區）
└── download_specs.sh  # 一鍵下載 27 份 PDF
```

**已完成：**
- ✅ RAG pipeline 端到端可運作
- ✅ 27 份 RISC-V 官方規格全數收錄
- ✅ 回答可追溯來源（PDF 檔名 + 頁碼）
- ✅ 文件依據與訓練知識明確分離

---

## 下一步計劃

### Week 2：FastAPI Endpoint
把 `query.py` 包成 REST API，讓任何設備都能透過 HTTP 查詢：
```bash
curl -X POST http://server/ask -d '{"question": "What is APLIC?"}'
```
**為什麼？** 一個有 API 的 AI 服務，才算是真正的「服務」，不只是一個 script。面試時 demo 更有說服力，也是實際部署到任何平台的前提。

### Week 3：RAGAS Evaluation
設計 20 個有標準答案的問題，用 RAGAS 框架評估系統準確率：
- **Context Recall**：文件有這個答案，RAG 有沒有找到相關段落？
- **Faithfulness**：回答是否忠實於找到的段落，沒有亂加東西？
- **Answer Relevancy**：回答有沒有回答問題，還是答非所問？

**為什麼？** 沒有 evaluation，你不知道系統是真的好還是看起來好。Evaluation 是讓 RAG 從「demo toy」變成「可信賴工具」的關鍵步驟。

### 雲端部署
把 FastAPI 服務部署到 Render 或 Railway，不需要開著自己的電腦就能查詢。
