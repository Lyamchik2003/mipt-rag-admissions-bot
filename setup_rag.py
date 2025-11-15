"""setup_rag.py

Генерирует два FAISS-индекса из двух JSON-файлов:
 - Бакалавриат → faiss_index_bachelor
 - Магистратура → faiss_index_master

По умолчанию использует:
 - bachelor: data/rules2025.json
 - master:   data/rules2025_magistratura_only.json

Можно переопределить через аргументы командной строки:
  --bachelor PATH --master PATH --bachelor-out DIR --master-out DIR
"""

import argparse
import json
import os
from pathlib import Path
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from config import OPENAI_API_KEY, OPENAI_API_BASE


DEFAULT_BACHELOR_JSON = Path("data/rules2025.json")
DEFAULT_MASTER_JSON = Path("data/rules2025_magistratura_only.json")
DEFAULT_BACHELOR_OUT = Path("faiss_index_bachelor")
DEFAULT_MASTER_OUT = Path("faiss_index_master")
DEFAULT_BACHELOR_MD = Path("data/raw/bachelort_rules.md")


def load_json_entries(path: Path, default_source: str) -> list[dict]:
    """Загружает массив объектов из JSON. Каждый объект должен содержать поле 'text'.
    Добавляет поле 'source' для трассировки происхождения."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"Ожидался массив JSON в {path}, получено: {type(data)}")
        entries = []
        for entry in data:
            if not isinstance(entry, dict) or "text" not in entry:
                # допускаем простые строки и преобразуем их в объекты
                if isinstance(entry, str):
                    entry = {"text": entry}
                else:
                    raise ValueError(f"Запись не является объектом с ключом 'text': {entry}")
            e = entry.copy()
            e.setdefault("source", default_source)
            entries.append(e)
        return entries


def build_and_save_index(entries: list[dict], out_dir: Path):
    def _split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
        text = text or ""
        if chunk_size <= 0:
            return [text]
        chunks = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + chunk_size, n)
            chunks.append(text[start:end])
            if end == n:
                break
            start = end - chunk_overlap if end - chunk_overlap > start else end
        return chunks
    texts: list[str] = []
    metadatas: list[dict] = []

    for entry in entries:
        parts = _split_text(entry.get("text", ""))
        for part in parts:
            texts.append(part)
            meta = {"source": entry.get("source", "unknown")}
            if "metadata" in entry and isinstance(entry["metadata"], dict):
                meta.update(entry["metadata"])
            # Если у записи есть раздел/секция — добавим
            if "section" in entry:
                meta["section"] = entry["section"]
            metadatas.append(meta)

    if not texts:
        raise ValueError("После разбиения не осталось текста для индексации.")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
    )

    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    out_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(out_dir))


def _parse_markdown_to_entries(md_text: str, default_source: str) -> list[dict]:
    """Парсит Markdown в список записей вида {text, source, section}.

    Заголовки #, ##, ### формируют иерархию; в метаданные кладём 'section' как путь "H1 > H2 > H3".
    Текст каждой секции будет дополнен заголовочным путём в начале, чтобы сохранить контекст при разбиении.
    """
    lines = md_text.splitlines()
    heading_stack: list[tuple[int, str]] = []  # (level, title)
    current_buf: list[str] = []
    entries: list[dict] = []

    def heading_path() -> str:
        return " > ".join(title for _, title in heading_stack)

    def flush_section():
        if current_buf:
            section_text = "\n".join(current_buf).strip()
            if section_text:
                path = heading_path()
                prefix = (path + "\n\n") if path else ""
                entries.append({
                    "text": prefix + section_text,
                    "source": default_source,
                    "section": path if path else None,
                })

    for raw in lines:
        line = raw.rstrip()
        # Определяем заголовок: начиная с #
        if line.lstrip().startswith("#"):
            # Считаем уровень
            stripped = line.lstrip()
            i = 0
            while i < len(stripped) and stripped[i] == '#':
                i += 1
            level = i  # 1..6
            title = stripped[i:].strip(" #\t")
            # Сбрасываем предыдущую секцию
            flush_section()
            current_buf = []
            # Обновляем стек заголовков
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
        else:
            current_buf.append(line)

    flush_section()

    # Уберём None из метаданных section
    for e in entries:
        if e.get("section") is None:
            e.pop("section", None)
    return entries


def build_index_from_markdown(md_path: Path, out_dir: Path, default_source: str):
    """Строит FAISS-индекс из Markdown-файла."""
    text = md_path.read_text(encoding="utf-8")
    entries = _parse_markdown_to_entries(text, default_source=default_source)
    build_and_save_index(entries, out_dir)


def main():
    parser = argparse.ArgumentParser(description="Сборка двух FAISS-индексов: бакалавриат и магистратура")
    parser.add_argument("--bachelor", type=Path, default=DEFAULT_BACHELOR_JSON, help="JSON с данными для бакалавриата")
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER_JSON, help="JSON с данными для магистратуры")
    parser.add_argument("--bachelor-out", type=Path, default=DEFAULT_BACHELOR_OUT, help="Папка для индекса бакалавриата")
    parser.add_argument("--master-out", type=Path, default=DEFAULT_MASTER_OUT, help="Папка для индекса магистратуры")
    parser.add_argument("--bachelor-md", type=Path, default=DEFAULT_BACHELOR_MD, help="Markdown-файл для бакалавриата (альтернатива JSON)")
    parser.add_argument("--master-md", type=Path, default=None, help="Markdown-файл для магистратуры (альтернатива JSON)")
    args = parser.parse_args()

    # Настроим ключ для эмбеддингов
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

    # Бакалавриат
    if args.bachelor_md is not None and args.bachelor_md.exists():
        build_index_from_markdown(args.bachelor_md, args.bachelor_out, default_source="bachelor")
        print(f"✅ Индекс бакалавриата из Markdown сохранён в '{args.bachelor_out}'. Источник: {args.bachelor_md}")
    else:
        if args.bachelor_md is not None and not args.bachelor_md.exists():
            print(f"⚠️ Markdown для бакалавриата не найден по пути: {args.bachelor_md}. Использую JSON: {args.bachelor}")
        bachelor_entries = load_json_entries(args.bachelor, default_source="bachelor")
        build_and_save_index(bachelor_entries, args.bachelor_out)
        print(f"✅ Индекс бакалавриата сохранён в '{args.bachelor_out}'. Источник: {args.bachelor}")

    # Магистратура
    if args.master_md is not None:
        build_index_from_markdown(args.master_md, args.master_out, default_source="master")
        print(f"✅ Индекс магистратуры из Markdown сохранён в '{args.master_out}'. Источник: {args.master_md}")
    else:
        master_entries = load_json_entries(args.master, default_source="master")
        build_and_save_index(master_entries, args.master_out)
        print(f"✅ Индекс магистратуры сохранён в '{args.master_out}'. Источник: {args.master}")


if __name__ == "__main__":
    main()
