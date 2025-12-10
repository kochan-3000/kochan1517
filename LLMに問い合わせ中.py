import os
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests

from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.ollama import OllamaEmbedding


# =========================================================
# 定数設定
# =========================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b"                  # 生成モデル
INDEX_PATH = "E:/LLM/storage"            # インデックス保存フォルダ
EMBED_MODEL_NAME = "nomic-embed-text"    # 埋め込みモデル


# =========================================================
# Ollama にプロンプトを送信
# =========================================================
def query_ollama(prompt: str) -> str:
    """Ollama にプロンプトを送信し、応答を返す"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=600
        )
        response.raise_for_status()

        data = response.json()
        return data.get("response", "[エラー] Ollama応答が不正です。")

    except Exception as e:
        return f"[Ollamaエラー] {e}"


# =========================================================
# RAG による回答生成
# =========================================================
def ask_with_rag(query: str) -> str:
    """ローカルインデックスを使った RAG 検索を実行"""
    if not os.path.exists(INDEX_PATH):
        return "[エラー] インデックスフォルダが見つかりません。"

    try:
        # 埋め込みモデル
        embed_model = OllamaEmbedding(model_name=EMBED_MODEL_NAME)

        # インデックスロード
        storage_context = StorageContext.from_defaults(persist_dir=INDEX_PATH)
        index = load_index_from_storage(storage_context, embed_model=embed_model)

        # ローカル検索
        retriever = index.as_retriever(similarity_top_k=3)
        retrieved_docs = retriever.retrieve(query)
        context = "\n".join(doc.text for doc in retrieved_docs)

        # 生成モデルへの最終プロンプト
        full_prompt = (
            "次の資料を参考に質問に答えてください。\n\n"
            f"資料:\n{context}\n\n"
            f"質問:{query}\n\n回答:"
        )

        return query_ollama(full_prompt)

    except Exception as e:
        return f"[RAGエラー] {e}"


# =========================================================
# GUI動作用関数
# =========================================================
def run_query():
    """入力欄の内容でRAG質問を実行"""
    query = entry.get().strip()
    if not query:
        messagebox.showwarning("警告", "質問を入力してください。")
        return

    output_box.insert(tk.END, f"\n[質問] {query}\n", "question")
    output_box.see(tk.END)

    def task():
        answer = ask_with_rag(query)
        output_box.insert(tk.END, f"\n[回答] {answer}\n", "answer")
        output_box.see(tk.END)

    threading.Thread(target=task).start()


# =========================================================
# GUIセットアップ
# =========================================================
root = tk.Tk()
root.title("ローカルRAGチャット - Qwen3 + nomic")
root.geometry("800x600")

# 入力欄 + 送信ボタン
frame = tk.Frame(root)
frame.pack(pady=10)

entry = tk.Entry(frame, width=80)
entry.pack(side=tk.LEFT, padx=10)

button = tk.Button(frame, text="送信", command=run_query)
button.pack(side=tk.LEFT)

# 出力欄
output_box = scrolledtext.ScrolledText(root, wrap=tk.WORD)
output_box.pack(fill=tk.BOTH, expand=True)

# フォーマット設定
output_box.tag_config("question", foreground="blue", font=("Meiryo", 10, "bold"))
output_box.tag_config("answer", foreground="green", font=("Meiryo", 10))

# メインループ
root.mainloop()

