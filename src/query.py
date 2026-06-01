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
load_dotenv()  # 從 .env 載入 ANTHROPIC_API_KEY 和 VOYAGE_API_KEY

from langchain_voyageai import VoyageAIEmbeddings
from langchain_chroma import Chroma
import anthropic

# 向量資料庫路徑（由 ingest.py 產生）
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "db")

# ingest 和 query 必須使用同一個 embedding 模型，才能比較向量
VOYAGE_MODEL = "voyage-3.5"


def build_prompt(question: str, context_chunks: list) -> str:
    """把搜尋到的 chunk 組成 context，強制分兩區塊回答。"""
    context = "\n\n---\n\n".join([
        f"[#{i+1} 來源: {os.path.basename(doc.metadata.get('source', 'unknown'))}, p.{doc.metadata.get('page', '?')}]\n{doc.page_content}"
        for i, doc in enumerate(context_chunks)
    ])
    return f"""You are a technical assistant specializing in RISC-V architecture and semiconductor IP.
Reply in the same language as the question (Traditional Chinese or English).

Your response MUST follow this exact structure:

## 📄 文件依據
Answer based STRICTLY on the provided context chunks below.
- Cite every statement with its source inline, e.g. （來源 #2, p.45）
- If a specific aspect is not in the context, write「（文件未載）」for that point.
- Do NOT use your training knowledge in this section.

## 🧠 補充參考（訓練知識）
- Only include knowledge from your training data that is NOT already covered above.
- Start each point with「⚠️ 非文件來源」to make it clear this is not from the spec.
- If everything is already covered by the documents, write「（無額外補充）」.

---

Context:
{context}

Question: {question}

Answer:"""


def query(question: str, top_k: int = 5) -> str:
    """
    主查詢函式：
    1. 把問題向量化
    2. 在 ChromaDB 找最相近的 top_k 個 chunk
    3. 組 prompt 送給 Claude Haiku（強制分文件依據 / 訓練知識兩區）
    4. 回傳回答 + 參考文件列表
    """
    if not os.path.exists(DB_DIR):
        return "Error: Vector store not found. Run `python3 src/ingest.py` first."

    embeddings = VoyageAIEmbeddings(model=VOYAGE_MODEL)
    db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

    docs = db.similarity_search(question, k=top_k)
    if not docs:
        return "No relevant content found."

    prompt = build_prompt(question, docs)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1536,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.content[0].text

    # 附上參考文件清單
    refs = "\n\n---\n## 📚 Retrieved References\n"
    seen = set()
    for i, doc in enumerate(docs):
        src = os.path.basename(doc.metadata.get("source", "unknown"))
        page = doc.metadata.get("page", "?")
        entry = f"  #{i+1}  {src}  —  p.{page}"
        if entry not in seen:
            seen.add(entry)
            refs += entry + "\n"

    return answer + refs


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
