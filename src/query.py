#!/usr/bin/env python3
"""
query.py — 向量搜尋 + Claude 回答，RAG 查詢介面。
用法：
  互動模式：python3 src/query.py
  單次問答：python3 src/query.py "你的問題"
"""
import os
import sys
import warnings
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()  # 從 .env 載入 ANTHROPIC_API_KEY

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import anthropic

# 向量資料庫路徑（由 ingest.py 產生）
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "db")


def build_prompt(question: str, context_chunks: list) -> str:
    """把搜尋到的 chunk 組成 context，搭配角色設定，送給 Claude。"""
    # 每個 chunk 標上來源檔名與頁碼，方便 Claude 引用、用戶事後查閱
    context = "\n\n---\n\n".join([
        f"[Source: {doc.metadata.get('source', 'unknown')}, page {doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for doc in context_chunks
    ])
    return f"""You are a technical assistant specializing in RISC-V architecture and semiconductor IP.
Answer the question using ONLY the context below. If the answer is not in the context, say so.

Context:
{context}

Question: {question}

Answer:"""


def query(question: str, top_k: int = 5) -> str:
    """
    主查詢函式：
    1. 把問題向量化
    2. 在 ChromaDB 找最相近的 top_k 個 chunk
    3. 組 prompt 送給 Claude Haiku
    4. 回傳回答文字
    """
    if not os.path.exists(DB_DIR):
        return "Error: Vector store not found. Run `python3 src/ingest.py` first."

    # 載入同一個 embedding 模型（ingest 和 query 必須一致，才能比較向量）
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

    # 向量相似度搜尋，取最相近的 top_k 個 chunk
    docs = db.similarity_search(question, k=top_k)
    if not docs:
        return "No relevant content found."

    prompt = build_prompt(question, docs)

    # 用 Claude Haiku 回答（速度快、成本低，適合 RAG 查詢）
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def interactive_mode():
    """互動模式：持續接受輸入直到用戶輸入 quit/exit/q。"""
    print("RAG Query System (RISC-V)")
    print("Type 'quit' to exit\n")
    while True:
        question = input("Question: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue
        print("\nSearching...\n")
        answer = query(question)
        print(f"Answer:\n{answer}\n")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 直接從命令列傳入問題
        q = " ".join(sys.argv[1:])
        print(query(q))
    else:
        interactive_mode()
