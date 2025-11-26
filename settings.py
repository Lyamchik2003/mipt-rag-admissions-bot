"""Единая конфигурация проекта."""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv("keys.env")


@dataclass(frozen=True)
class BotSettings:
    """Настройки бота."""
    token: str = field(default_factory=lambda: os.getenv("MAX_VK_BOT_TOKEN", ""))
    username: str = field(default_factory=lambda: os.getenv("MAX_VK_BOT_USERNAME", ""))


@dataclass(frozen=True)
class OpenAISettings:
    """Настройки OpenAI API."""
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    api_base: str = field(default_factory=lambda: os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"))
    model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-ada-002"
    temperature: float = 0.0


@dataclass(frozen=True)
class RAGSettings:
    """Настройки RAG-пайплайна."""
    default_index_dir: str = "faiss_index"
    bachelor_index_dir: str = "faiss_index_bachelor"
    master_index_dir: str = "faiss_index_master"
    retriever_k: int = 7
    max_question_length: int = 500
    min_question_length: int = 3


@dataclass(frozen=True)
class Settings:
    """Главный класс настроек."""
    bot: BotSettings = field(default_factory=BotSettings)
    openai: OpenAISettings = field(default_factory=OpenAISettings)
    rag: RAGSettings = field(default_factory=RAGSettings)
    
    def validate(self) -> list[str]:
        """Проверяет обязательные настройки. Возвращает список ошибок."""
        errors = []
        if not self.bot.token:
            errors.append("MAX_VK_BOT_TOKEN not set")
        if not self.openai.api_key:
            errors.append("OPENAI_API_KEY not set")
        return errors


settings = Settings()
