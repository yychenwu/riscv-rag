# RISC-V RAG Knowledge Base

以 Claude + Voyage AI + ChromaDB 建構的 RISC-V 規格知識庫，涵蓋 27 份官方 spec PDF（2073 頁、3224 chunks），支援語意搜尋與問答。

## 架構

```
PDF (27份) → PyPDF 解析 → Voyage AI Embedding → ChromaDB
                                                      ↓
用戶提問 → 向量搜尋 → 取相關 chunk → Claude → 回答
```

## 知識庫涵蓋範圍

| 類別 | 規格 |
|------|------|
| ISA Manual | RISC-V Unified ISA Manual (Vol 1 + Vol 2 + Privileged, 2026-06-01) |
| Interrupt | AIA 1.0、PLIC 1.0、Double Trap 1.0、Ssqosid 1.0 |
| Memory Protection | SPMP 1.0-rc4、SPMP for Hypervisor 0.2、IOPMP 0.8.2、IOMMU |
| Extensions | Vector 1.0、Bitmanip 1.0、Zicond 1.0、Zc* 1.0.4、Scalar Crypto 1.0.1、Sstc 0.5.4、Zaamo/Zalrsc 1.0、Indirect CSR rc7/rc3 |
| Platform | SBI 3.0、Profiles (RVA23/RVB23)、Platform Security Model 0.1、WorldGuard 0.4 |
| Debug & Trace | Debug 1.0-STABLE、N-Trace 1.0、Trace Control 1.0、Trace Connectors 1.0 |

## 環境需求

- Python 3.9+（使用 `/usr/bin/python3`，不需 venv）
- Anthropic API Key
- Voyage AI API Key

## 快速開始

### 1. 安裝套件

```bash
pip install -r requirements.txt --break-system-packages
```

### 2. 設定 API Key

在專案根目錄建立 `.env`：

```
ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...
```

### 3. 下載 PDF（已有 data/ 可跳過）

```bash
bash download_specs.sh
```

### 4. 建立向量資料庫

```bash
# 如果 db/ 已存在要重建，先刪除：
# python3 -c "import shutil; shutil.rmtree('db/')"

/usr/bin/python3 src/ingest.py
```

完成後會在 `db/` 產生向量資料庫（27 份 PDF → 3224 chunks）。

### 5. 開始查詢

互動模式：
```bash
/usr/bin/python3 src/query.py
```

單次查詢：
```bash
/usr/bin/python3 src/query.py "What is the RISC-V AIA interrupt architecture?"
```

## 專案結構

```
rag-project/
├── data/                  # 27 份 RISC-V spec PDF
├── db/                    # ChromaDB 向量資料庫（自動產生，不進 git）
├── src/
│   ├── ingest.py          # PDF → 向量資料庫（chunk_size=2000）
│   └── query.py           # 查詢介面
├── download_specs.sh      # 自動下載 27 份 PDF 的腳本
├── .env                   # API Keys（不進 git）
└── requirements.txt
```

## 新增 PDF

把新 PDF 放進 `data/`，然後重建資料庫：

```bash
python3 -c "import shutil; shutil.rmtree('db/')"
/usr/bin/python3 src/ingest.py
```

## 注意事項

- `db/`、`.env` 已加入 `.gitignore`，不會上傳 GitHub
- ANTHROPIC_API_KEY **不可**寫入 `~/.zshrc`，會干擾 Claude Code CLI 認證；請用專案 `.env`
