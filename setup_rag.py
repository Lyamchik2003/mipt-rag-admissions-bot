# setup_rag.py

import json
import os
from pathlib import Path

from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from config import OPENAI_API_KEY, OPENAI_API_BASE

# 1. Укажите путь к вашему файлу с чанками
INPUT_PATH = Path("data/responses.json")  # или data/rag_knowledge_base.jsonl, если JSONL

# 2. Папка, куда сохранится индекс
INDEX_DIR = Path("faiss_index")


# Загружаем чанки из FAQ и правил, добавляя метку источника
def load_all_chunks():
    chunks = []
    # FAQ (основная база)
    with open("data/data_faq.json", encoding="utf-8") as f:
        faq = json.load(f)
        for entry in faq:
            entry = entry.copy()
            entry["source"] = "faq"
            chunks.append(entry)
    # Правила
    with open("data/rules2025_magistratura_only.json", encoding="utf-8") as f:
        rules = json.load(f)
        for entry in rules:
            entry = entry.copy()
            entry["source"] = "rules"
            chunks.append(entry)
    return chunks


def main():
    # Настроим ключ
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

    # 1) Загружаем все чанки (FAQ + правила)
    chunks = load_all_chunks()

    # 2) Разбиваем текст внутри каждого чанка, если он слишком длинный
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = []
    metadatas = []
    for entry in chunks:
        # разбиваем текст на части
        parts = splitter.split_text(entry["text"])
        for part in parts:
            texts.append(part)
            # В метаданные кладём всё, включая source и metadata (если есть)
            meta = {"source": entry.get("source", "faq")}
            if "metadata" in entry:
                meta.update(entry["metadata"])
            # Для правил — если есть пункт, добавим его явно
            if entry["source"] == "rules" and "section" in entry:
                meta["section"] = entry["section"]
            metadatas.append(meta)

    # 3) Генерируем эмбеддинги
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE
    )

    # 4) Строим FAISS-индекс
    vectorstore = FAISS.from_texts(
        texts,
        embeddings,
        metadatas=metadatas
    )

    # 5) Сохраняем локально
    INDEX_DIR.mkdir(exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))

    print(f"✅ Индекс сохранён в папке '{INDEX_DIR}'. (FAQ + правила)")

if __name__ == "__main__":
    main()
