"""Общие компоненты для ботов."""
import logging
from datetime import datetime


def setup_logging() -> tuple[logging.Logger, logging.Logger]:
    """Настраивает и возвращает (main_logger, user_logger)."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    main_logger = logging.getLogger('MAIN')
    user_logger = logging.getLogger('USER')
    
    logging.getLogger('aiomax').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    return main_logger, user_logger


class UserTracker:
    """Трекер уникальных пользователей за сессию."""
    
    def __init__(self):
        self.active_users: set[int] = set()
        self.start_time: datetime = datetime.now()
    
    def add_user(self, user_id: int) -> bool:
        """Регистрирует пользователя. Возвращает True если новый."""
        is_new = user_id not in self.active_users
        self.active_users.add(user_id)
        return is_new
    
    @property
    def count(self) -> int:
        return len(self.active_users)
    
    def get_stats(self) -> str:
        uptime = datetime.now() - self.start_time
        h, rem = divmod(int(uptime.total_seconds()), 3600)
        m, _ = divmod(rem, 60)
        return f"Пользователей: {self.count} | Uptime: {h}ч {m}м"
