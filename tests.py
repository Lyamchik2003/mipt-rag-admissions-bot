"""
Тесты для проверки работоспособности бота.

Использование:
    pytest tests.py -v                    # Все тесты
    pytest tests.py -v -m startup         # Только startup-тесты
    pytest tests.py -v -m "not slow"      # Без медленных тестов (API)
    python tests.py                       # Быстрая проверка перед запуском
    python tests.py --check-api           # С проверкой API ключей
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Generator

import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Возвращает корневую директорию проекта."""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def settings():
    """Загружает настройки приложения."""
    from settings import settings as app_settings
    return app_settings


@pytest.fixture(scope="session")
def faq_data(project_root: Path) -> dict:
    """Загружает FAQ данные."""
    faq_path = project_root / "data" / "faq.json"
    if not faq_path.exists():
        pytest.skip("FAQ файл не найден")
    
    with open(faq_path, encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Startup Tests - проверяют минимально необходимое для запуска
# =============================================================================

class TestStartup:
    """Тесты для проверки возможности запуска бота."""
    
    @pytest.mark.startup
    def test_required_modules_installed(self):
        """Проверяет установку обязательных модулей."""
        required_modules = {
            "aiomax": "pip install aiomax",
            "langchain_openai": "pip install langchain-openai", 
            "faiss": "pip install faiss-cpu",
            "dotenv": "pip install python-dotenv",
        }
        
        missing = []
        for module, install_cmd in required_modules.items():
            try:
                __import__(module)
            except ImportError:
                missing.append(f"{module} ({install_cmd})")
        
        assert not missing, f"Не установлены модули: {', '.join(missing)}"
    
    @pytest.mark.startup
    def test_env_file_exists(self, project_root: Path):
        """Проверяет наличие файла с переменными окружения."""
        env_file = project_root / "keys.env"
        assert env_file.exists(), "Файл keys.env не найден. Создайте его на основе keys.env.example"
    
    @pytest.mark.startup
    def test_bot_token_configured(self, settings):
        """Проверяет наличие токена бота."""
        assert settings.bot.token, "MAX_VK_BOT_TOKEN не установлен в keys.env"
    
    @pytest.mark.startup
    def test_openai_key_configured(self, settings):
        """Проверяет наличие API ключа OpenAI."""
        assert settings.openai.api_key, "OPENAI_API_KEY не установлен в keys.env"
    
    @pytest.mark.startup
    def test_at_least_one_faiss_index_exists(self, settings):
        """Проверяет наличие хотя бы одного FAISS-индекса."""
        indexes = [
            settings.rag.default_index_dir,
            settings.rag.bachelor_index_dir,
            settings.rag.master_index_dir,
        ]
        
        found = [
            idx for idx in indexes 
            if os.path.exists(os.path.join(idx, "index.faiss"))
        ]
        
        assert found, (
            "Не найдено ни одного FAISS-индекса. "
            "Запустите: python setup_rag.py"
        )


# =============================================================================
# Configuration Tests - проверяют корректность конфигурации
# =============================================================================

class TestConfiguration:
    """Тесты конфигурации приложения."""
    
    def test_settings_immutable(self, settings):
        """Проверяет что настройки неизменяемые (frozen dataclass)."""
        with pytest.raises(Exception):
            settings.bot.token = "new_token"
    
    def test_openai_model_valid(self, settings):
        """Проверяет что модель OpenAI указана корректно."""
        assert settings.openai.model, "Модель OpenAI не указана"
        valid_prefixes = ("gpt-", "o1", "o3")
        assert any(
            settings.openai.model.startswith(p) for p in valid_prefixes
        ), f"Неизвестная модель: {settings.openai.model}"
    
    def test_rag_settings_valid(self, settings):
        """Проверяет корректность RAG настроек."""
        assert settings.rag.retriever_k > 0, "retriever_k должен быть > 0"
        assert settings.rag.max_question_length > 0, "max_question_length должен быть > 0"
        assert settings.rag.min_question_length >= 0, "min_question_length должен быть >= 0"


# =============================================================================
# FAQ Tests - проверяют корректность FAQ данных
# =============================================================================

class TestFAQ:
    """Тесты FAQ файла."""
    
    def test_faq_file_exists(self, project_root: Path):
        """Проверяет наличие FAQ файла."""
        faq_path = project_root / "data" / "faq.json"
        assert faq_path.exists(), "FAQ файл data/faq.json не найден"
    
    def test_faq_valid_json(self, project_root: Path):
        """Проверяет что FAQ - валидный JSON."""
        faq_path = project_root / "data" / "faq.json"
        if not faq_path.exists():
            pytest.skip("FAQ файл не найден")
        
        with open(faq_path, encoding="utf-8") as f:
            data = json.load(f)
        
        assert isinstance(data, dict), "FAQ должен быть словарём"
    
    def test_faq_has_required_sections(self, faq_data: dict):
        """Проверяет наличие обязательных секций в FAQ."""
        required_sections = {"master", "bachelor"}
        actual_sections = set(faq_data.keys())
        
        missing = required_sections - actual_sections
        assert not missing, f"В FAQ отсутствуют секции: {missing}"
    
    def test_faq_questions_not_empty(self, faq_data: dict):
        """Проверяет что в каждой секции есть вопросы."""
        for section, questions in faq_data.items():
            assert questions, f"Секция '{section}' пуста"
            assert isinstance(questions, dict), f"Секция '{section}' должна быть словарём"
            for key, item in questions.items():
                assert "question" in item, f"Вопрос '{key}' не содержит поле 'question'"


# =============================================================================
# API Tests - проверяют подключение к внешним сервисам (медленные)
# =============================================================================

class TestAPIConnections:
    """Тесты подключения к внешним API."""
    
    @pytest.mark.slow
    @pytest.mark.api
    def test_openai_connection(self, settings):
        """Проверяет подключение к OpenAI API."""
        from langchain_openai import ChatOpenAI
        
        chat = ChatOpenAI(
            model_name=settings.openai.model,
            openai_api_key=settings.openai.api_key,
            openai_api_base=settings.openai.api_base,
            temperature=0,
            max_tokens=10,
        )
        
        result = chat.invoke("Ответь одним словом: да")
        assert result.content, "Пустой ответ от OpenAI"
    
    @pytest.mark.slow
    @pytest.mark.api
    def test_openai_embeddings(self, settings):
        """Проверяет работу embeddings модели."""
        from langchain_openai import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings(
            model=settings.openai.embedding_model,
            openai_api_key=settings.openai.api_key,
            openai_api_base=settings.openai.api_base,
        )
        
        result = embeddings.embed_query("тест")
        assert isinstance(result, list), "Embeddings должны возвращать список"
        assert len(result) > 0, "Пустой вектор embeddings"


# =============================================================================
# RAG Engine Tests - проверяют RAG движок
# =============================================================================

class TestRAGEngine:
    """Тесты RAG движка."""
    
    def test_rag_engine_imports(self):
        """Проверяет импорт RAG движка."""
        from rag_bot_new import RAGEngine
        assert RAGEngine is not None
    
    def test_profanity_detection(self):
        """Проверяет детекцию нецензурной лексики."""
        from rag_bot_new import contains_profanity
        assert contains_profanity("привет") is False
        assert contains_profanity("нормальный вопрос") is False
    
    def test_dangerous_detection(self):
        """Проверяет детекцию опасных запросов."""
        from rag_bot_new import contains_dangerous_patterns
        assert contains_dangerous_patterns("как поступить в МФТИ") is False
        assert contains_dangerous_patterns("какие документы нужны") is False
    
    def test_no_info_phrases_defined(self):
        """Проверяет что фразы 'нет информации' определены."""
        from rag_bot_new import NO_INFO_PHRASES
        assert isinstance(NO_INFO_PHRASES, list)
        assert len(NO_INFO_PHRASES) > 0


# =============================================================================
# CLI Runner - для запуска без pytest
# =============================================================================

class StartupChecker:
    """Быстрая проверка перед запуском бота (без pytest)."""
    
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def check_modules(self) -> bool:
        """Проверяет установку модулей."""
        modules = ["aiomax", "langchain_openai", "faiss", "dotenv"]
        for module in modules:
            try:
                __import__(module)
            except ImportError:
                self.errors.append(f"Модуль '{module}' не установлен")
        return not any("Модуль" in e for e in self.errors)
    
    def check_env(self) -> bool:
        """Проверяет переменные окружения."""
        from settings import settings
        
        if not settings.bot.token:
            self.errors.append("MAX_VK_BOT_TOKEN не установлен")
        if not settings.openai.api_key:
            self.errors.append("OPENAI_API_KEY не установлен")
        if not settings.bot.username:
            self.warnings.append("MAX_VK_BOT_USERNAME не установлен")
        
        return not self.errors
    
    def check_indexes(self) -> bool:
        """Проверяет FAISS индексы."""
        from settings import settings
        
        indexes = [
            settings.rag.default_index_dir,
            settings.rag.bachelor_index_dir,
            settings.rag.master_index_dir,
        ]
        
        found = any(
            os.path.exists(os.path.join(idx, "index.faiss")) 
            for idx in indexes
        )
        
        if not found:
            self.errors.append("Не найдено ни одного FAISS-индекса")
        
        return found
    
    def check_faq(self) -> bool:
        """Проверяет FAQ файл."""
        faq_path = Path("data/faq.json")
        if not faq_path.exists():
            self.warnings.append("FAQ файл не найден")
            return True
        
        try:
            with open(faq_path, encoding="utf-8") as f:
                json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Ошибка парсинга FAQ: {e}")
            return False
    
    def check_openai(self) -> bool:
        """Проверяет OpenAI API."""
        from settings import settings
        from langchain_openai import ChatOpenAI
        
        try:
            chat = ChatOpenAI(
                model_name=settings.openai.model,
                openai_api_key=settings.openai.api_key,
                openai_api_base=settings.openai.api_base,
                temperature=0,
                max_tokens=10,
            )
            result = chat.invoke("OK")
            return bool(result.content)
        except Exception as e:
            self.errors.append(f"OpenAI API недоступен: {e}")
            return False
    
    def run(self, check_api: bool = False) -> bool:
        """Запускает все проверки."""
        print("🔍 Проверка конфигурации...\n")
        
        checks = [
            ("Модули", self.check_modules),
            ("Переменные окружения", self.check_env),
            ("FAISS индексы", self.check_indexes),
            ("FAQ файл", self.check_faq),
        ]
        
        if check_api:
            checks.append(("OpenAI API", self.check_openai))
        
        all_passed = True
        for name, check_func in checks:
            try:
                result = check_func()
                status = "✅" if result else "❌"
                print(f"  {status} {name}")
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {name}: {e}")
                all_passed = False
        
        print()
        
        if self.warnings:
            print("⚠️  Предупреждения:")
            for w in self.warnings:
                print(f"    • {w}")
            print()
        
        if self.errors:
            print("❌ Ошибки:")
            for e in self.errors:
                print(f"    • {e}")
            print()
        
        if all_passed:
            print("✅ Все проверки пройдены!\n")
        
        return all_passed


def run_startup_tests(check_api: bool = False, exit_on_fail: bool = True) -> bool:
    """
    Запускает быструю проверку перед стартом бота.
    
    Args:
        check_api: Проверять ли подключение к API (медленно)
        exit_on_fail: Завершить процесс при ошибке
        
    Returns:
        True если все проверки пройдены
    """
    checker = StartupChecker()
    passed = checker.run(check_api=check_api)
    
    if not passed and exit_on_fail:
        print("❌ Бот не может быть запущен. Исправьте ошибки выше.")
        sys.exit(1)
    
    return passed


# =============================================================================
# pytest configuration
# =============================================================================

def pytest_configure(config):
    """Регистрирует кастомные маркеры."""
    config.addinivalue_line("markers", "startup: быстрые тесты для проверки запуска")
    config.addinivalue_line("markers", "slow: медленные тесты (API запросы)")
    config.addinivalue_line("markers", "api: тесты внешних API")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Проверка конфигурации бота",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python tests.py                 Быстрая проверка
  python tests.py --check-api     С проверкой API ключей
  pytest tests.py -v              Все тесты через pytest
  pytest tests.py -v -m startup   Только startup тесты
  pytest tests.py -v -m "not slow" Без медленных тестов
        """
    )
    parser.add_argument(
        "--check-api", 
        action="store_true", 
        help="Проверить подключение к API (медленно)"
    )
    parser.add_argument(
        "--pytest",
        action="store_true",
        help="Запустить через pytest"
    )
    args = parser.parse_args()
    
    if args.pytest:
        pytest_args = [__file__, "-v"]
        if not args.check_api:
            pytest_args.extend(["-m", "not slow"])
        sys.exit(pytest.main(pytest_args))
    else:
        run_startup_tests(check_api=args.check_api, exit_on_fail=False)
