import logging
import threading

# 1) Общий буфер
log_buffer = list() # хранит последние N сообщений
log_buffer_lock = threading.Lock() # защита при многопоточности
MAX_LINES = 500 # сколько строк держим в памяти

# 2) Кастомный обработчик, который кладёт каждую запись в log_buffer
class UIHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        with log_buffer_lock:
            log_buffer.append(msg)
            if len(log_buffer) > MAX_LINES:
                del log_buffer[:len(log_buffer) - MAX_LINES]

# 3) Функция, возвращающая настроенный логгер
def get_logger(name: str = "FinAtlas") -> logging.Logger:
    logger = logging.getLogger(name)
    if not any(isinstance(h, UIHandler) for h in logger.handlers):
        logger.setLevel(logging.INFO)
        # Например, простой формат: <время> — <сообщение>
        fmt = logging.Formatter("%(asctime)s — %(message)s", datefmt="%H:%M:%S")
        handler_ui = UIHandler()
        handler_ui.setFormatter(fmt)
        logger.addHandler(handler_ui)
        logger.addHandler(logging.StreamHandler())  # чтобы логи всё еще шли в консоль
    return logger

# 4) Обёртка print_info, чтобы не заимпортить logging в каждый модуль
def logger_print(message: str):
    """
    Вызывайте print_info(...) вместо print(), 
    чтобы строка ушла и в консоль, и в общий буфер log_buffer.
    """
    logger = get_logger()
    logger.info(message)
