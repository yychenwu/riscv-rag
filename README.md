# RISC-V RAG System

用 Claude + ChromaDB 建的 RAG（Retrieval-Augmented Generation）系統，可以對 RISC-V spec PDF 進行語意搜尋與問答。

## 架構

```
PDF → 切段 → HuggingFace Embedding → ChromaDB
                                           ↓
用戶提問 → 向量搜尋 → 取相關 chunk → Claude Haiku → 回答
```

## 環境需求

- Python 3.9+
- Anthropic API Key

## 快速開始

### 1. 建立虛擬環境

```bash
cd rag-project
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. 安裝套件

```bash
pip install anthropic python-dotenv langchain langchain-anthropic \
            langchain-community langchain-chroma chromadb pypdf \
            sentence-transformers
```

### 3. 設定 API Key

複製 `.env.example` 並填入你的 Anthropic API Key：

```bash
cp .env.example .env
# 編輯 .env，填入 ANTHROPIC_API_KEY=sk-ant-...
```

### 4. 放入 PDF

把要查詢的 PDF 放進 `data/` 資料夾：

```
data/
  riscv-spec.pdf
  riscv-privileged.pdf   # 可選
  amba-axi4.pdf          # 可選
```

### 5. 建立向量資料庫（只需跑一次）

```bash
python3 src/ingest.py
```

第一次執行會自動下載 embedding model（約 90MB）。完成後會在 `db/` 產生向量資料庫。

### 6. 開始問問題

互動模式：
```bash
python3 src/query.py
```

單次問答：
```bash
python3 src/query.py "What is the RISC-V interrupt handling mechanism?"
```

## 專案結構

```
rag-project/
├── data/              # 放 PDF 的地方
├── db/                # ChromaDB 向量資料庫（自動產生，不進 git）
├── src/
│   ├── ingest.py      # PDF → 向量資料庫
│   └── query.py       # 查詢介面
├── .env               # API Key（不進 git）
├── .env.example       # API Key 範本
└── requirements.txt   # 套件清單
```

## 新增 PDF 素材

把新 PDF 放進 `data/` 後，重跑 ingest：

```bash
python3 src/ingest.py
```

## 注意事項

- `db/` 和 `.env` 已加入 `.gitignore`，不會上傳 GitHub
- 建議使用 venv 隔離套件環境，避免系統 Python 版本衝突
- 每次開新 terminal 都要 `source venv/bin/activate`
