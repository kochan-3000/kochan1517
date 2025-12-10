
import os
import json
from pathlib import Path
from tqdm import tqdm
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama

# === 設定 ===
SCAN_PATH = "E:/"  # 🔍 HDD全体をスキャン
INDEX_PATH = Path("E:/LLM_Index/simple_index_qwen")  # 🔧 インデックス保存先

# 除外するフォルダ
EXCLUDE_DIRS = [
    "Windows", "Program Files", "Program Files (x86)",
    "$Recycle.Bin", "AppData", "System Volume Information",
    "Recovery", "PerfLogs"
]

# === モデル設定 ===
llm = Ollama(model="nomic-embed-text", request_timeout=60.0)
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# === インデックスフォルダ確認 ===
os.makedirs(INDEX_PATH, exist_ok=True)
print(f"📁 インデックスフォルダ: {INDEX_PATH}")

# 空の JSON ファイルを必要なら生成
for f in ["docstore.json", "index_store.json", "vector_store.json"]:
    json_path = INDEX_PATH / f
    if not json_path.exists():
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump({}, jf)
        print(f"🆕 {f} を新規作成しました")

# === ファイル読み込み ===
print(f"📂 {SCAN_PATH} をスキャン中（除外: {', '.join(EXCLUDE_DIRS)}）...")
docs = []

for root, dirs, files in os.walk(SCAN_PATH):
    if any(excl in root for excl in EXCLUDE_DIRS):
        continue

    for f in files:
        ext = f.lower().split(".")[-1]
        if ext in ["txt", "md", "pdf", "docx", "mp3"]:
            full_path = os.path.join(root, f)
            try:
                # MP3はメタデータのみ抽出
                if ext == "mp3":
                    from mutagen.easyid3 import EasyID3
                    try:
                        tags = EasyID3(full_path)
                        text_data = "\n".join([f"{k}: {v}" for k, v in tags.items()])
                    except Exception:
                        text_data = f"音声ファイル: {f}"
                    with open("temp_mp3.txt", "w", encoding="utf-8") as tmp:
                        tmp.write(text_data)
                    reader = SimpleDirectoryReader(input_files=["temp_mp3.txt"])
                else:
                    reader = SimpleDirectoryReader(input_files=[full_path])
                docs.extend(reader.load_data())
            except Exception as e:
                print(f"⚠️ 読み込み失敗: {full_path} ({e})")

print(f"✅ 読み込み完了: {len(docs)} 件")

# === インデックス構築 ===
if len(docs) == 0:
    print("⚠️ 読み込めるドキュメントがありません。")
else:
    print("🧠 インデックス構築中...")
    try:
        storage_context = StorageContext.from_defaults(persist_dir=str(INDEX_PATH))
        index = VectorStoreIndex.from_documents(
            docs, storage_context=storage_context, embed_model=embed_model
        )
        index.storage_context.persist()
        print("✅ インデックス構築完了！")
        print(f"📄 インデックス保存先: {INDEX_PATH}")
    except Exception as e:
        print(f"❌ インデックス作成中にエラー: {e}")

# === モデル動作テスト ===
try:
    query_engine = index.as_query_engine(llm=llm)
    answer = query_engine.query("テストです。動作確認をしてください。")
    print("🤖 モデル動作確認:", answer)
except Exception as e:
    print(f"⚠️ モデル動作テストに失敗しました: {e}")
