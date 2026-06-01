#!/usr/bin/env python3
"""
ingest.py — 把 data/ 裡的 PDF 切段、向量化，存進 ChromaDB。
只需要跑一次（或新增 PDF 時重跑）。
用法：python3 src/ingest.py
"""
import os
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_voyageai import VoyageAIEmbeddings
from langchain_chroma import Chroma

# 資料目錄（放 PDF）和向量資料庫目錄
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "db")

# voyage-3.5 適合技術文件（通用高品質）；若主要是程式碼可改用 voyage-code-3
VOYAGE_MODEL = "voyage-3.5"


def ingest_pdfs():
    # 掃描 data/ 資料夾，找所有 PDF
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in data/")
        return

    print(f"Found {len(pdf_files)} PDF(s): {pdf_files}")

    # 逐一讀取每個 PDF，每頁變成一個 Document（含 metadata：檔名、頁碼）
    all_docs = []
    for pdf_file in pdf_files:
        path = os.path.join(DATA_DIR, pdf_file)
        print(f"Loading {pdf_file}...")
        loader = PyPDFLoader(path)
        docs = loader.load()
        print(f"  {len(docs)} pages loaded")
        all_docs.extend(docs)

    # 切段：每段最多 1000 字元，相鄰段重疊 200 字元（保留上下文語義）
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],  # 優先從段落、換行處切
    )
    chunks = splitter.split_documents(all_docs)
    print(f"\nTotal chunks: {len(chunks)}")

    # 使用 Voyage AI embedding（Anthropic 官方推薦，技術文件效果佳）
    print(f"Using Voyage AI embedding model: {VOYAGE_MODEL}")
    embeddings = VoyageAIEmbeddings(
        model=VOYAGE_MODEL,
    )

    # 把所有 chunk 向量化並存進 ChromaDB，資料庫持久化到 db/ 資料夾
    print("Building ChromaDB vector store...")
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR,
    )
    print(f"Done! Vector store saved to {DB_DIR}")
    print(f"Total vectors: {db._collection.count()}")


if __name__ == "__main__":
    ingest_pdfs()
