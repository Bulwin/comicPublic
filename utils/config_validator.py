"""
Валидация конфигурации и переменных окружения.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigValidationError(Exception):
    """Ошибка валидации конфигурации."""
    pass


class ConfigValidator:
    """Валидатор конфигурации."""
    
    # Обязательные переменные окружения
    REQUIRED_ENV_VARS = {
        'OPENAI_API_KEY': 'OpenAI API ключ для генерации сценариев и изображений',
        'PERPLEXITY_API_KEY': 'Perplexity API ключ для получения новостей'
    }
    
    # Опциональные переменные окружения
    OPTIONAL_ENV_VARS = {
        'TELEGRAM_BOT_TOKEN': 'Токен Telegram бота для управления',
        'TELEGRAM_ADMIN_CHAT_ID': 'Chat ID администратора Telegram бота',
        'TELEGRAM_CHANNEL_ID': 'ID канала для публикации в Telegram',
        'INSTAGRAM_USERNAME': 'Имя пользователя Instagram',
        'INSTAGRAM_PASSWORD': 'Пароль Instagram',
        'INSTAGRAM_ACCOUNT_ID': 'ID аккаунта Instagram'
    }
    
    # Переменные Assistants API
    ASSISTANTS_ENV_VARS = {
        'SCRIPTWRITER_A_ASSISTANT_ID': 'ID ассистента-сценариста типа A',
        'SCRIPTWRITER_B_ASSISTANT_ID': 'ID ассистента-сценариста типа B',
        'SCRIPTWRITER_C_ASSISTANT_ID': 'ID ассистента-сценариста типа C',
        'SCRIPTWRITER_D_ASSISTANT_ID': 'ID ассистента-сценариста типа D',
        'SCRIPTWRITER_E_ASSISTANT_ID': 'ID ассистента-сценариста типа E',
        'JURY_A_ASSISTANT_ID': 'ID ассистента-жюри типа A',
        'JURY_B_ASSISTANT_ID': 'ID ассистента-жюри типа B',
        'JURY_C_ASSISTANT_ID': 'ID ассистента-жюри типа C',
        'JURY_D_ASSISTANT_ID': 'ID ассистента-жюри типа D',
        'JURY_E_ASSISTANT_ID': 'ID ассистента-жюри типа E'
    }
    
    @classmethod
    def validate_required_env_vars(cls) -> List[str]:
        """
        Проверка обязательных переменных окружения.
        
        Returns:
            List[str]: Список отсутствующих переменных
        """
        missing_vars = []
        
        for var_name, description in cls.REQUIRED_ENV_VARS.items():
            value = os.getenv(var_name)
            if not value or value.strip() == '':
                missing_vars.append(f"{var_name} - {description}")
        
        return missing_vars
    
    @classmethod
    def validate_api_keys(cls) -> Dict[str, bool]:
        """
        Проверка валидности API ключей.
        
        Returns:
            Dict[str, bool]: Результаты проверки ключей
        """
        results = {}
        
        # Проверка OpenAI API ключа
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            results['openai'] = cls._validate_openai_key(openai_key)
        else:
            results['openai'] = False
        
        # Проверка Perplexity API ключа
        perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        if perplexity_key:
            results['perplexity'] = cls._validate_perplexity_key(perplexity_key)
        else:
            results['perplexity'] = False
        
        return results
    
    @classmethod
    def _validate_openai_key(cls, api_key: str) -> bool:
        """Проверка OpenAI API ключа."""
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            # Простая проверка - получение списка моделей
            models = client.models.list()
            return True
        except Exception as e:
            logger.warning(f"Ошибка валидации OpenAI API ключа: {e}")
            return False
    
    @classmethod
    def _validate_perplexity_key(cls, api_key: str) -> bool:
        """Проверка Perplexity API ключа."""
        try:
            import requests
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            # Простой тестовый запрос
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=headers,
                json={
                    'model': 'llama-3.1-sonar-small-128k-online',
                    'messages': [{'role': 'user', 'content': 'test'}],
                    'max_tokens': 1
                },
                timeout=10
            )
            return response.status_code in [200, 400]  # 400 тоже OK - значит ключ валиден
        except Exception as e:
            logger.warning(f"Ошибка валидации Perplexity API ключа: {e}")
            return False
    
    @classmethod
    def validate_assistants_config(cls) -> Dict[str, Any]:
        """
        Проверка конфигурации Assistants API.
        
        Returns:
            Dict[str, Any]: Результаты проверки
        """
        results = {
            'use_assistants': False,
            'missing_assistants': [],
            'available_assistants': []
        }
        
        # Проверяем, включен ли Assistants API
        try:
            from config import USE_ASSISTANTS_API
            results['use_assistants'] = USE_ASSISTANTS_API
        except ImportError:
            results['use_assistants'] = False
        
        if not results['use_assistants']:
            return results
        
        # Проверяем наличие ID ассистентов
        for var_name, description in cls.ASSISTANTS_ENV_VARS.items():
            value = os.getenv(var_name)
            if value and value.strip():
                results['available_assistants'].append(var_name)
            else:
                results['missing_assistants'].append(f"{var_name} - {description}")
        
        return results
    
    @classmethod
    def validate_telegram_config(cls) -> Dict[str, Any]:
        """
        Проверка конфигурации Telegram.
        
        Returns:
            Dict[str, Any]: Результаты проверки
        """
        results = {
            'bot_token': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
            'admin_chat_id': bool(os.getenv('TELEGRAM_ADMIN_CHAT_ID')),
            'channel_id': bool(os.getenv('TELEGRAM_CHANNEL_ID')),
            'ready_for_bot': False,
            'ready_for_publishing': False
        }
        
        # Готовность для Telegram бота
        results['ready_for_bot'] = results['bot_token'] and results['admin_chat_id']
        
        # Готовность для публикации в Telegram
        results['ready_for_publishing'] = results['bot_token'] and results['channel_id']
        
        return results
    
    @classmethod
    def validate_directories(cls) -> Dict[str, bool]:
        """
        Проверка необходимых директорий.
        
        Returns:
            Dict[str, bool]: Результаты проверки директорий
        """
        try:
            from config import DATA_DIR, LOGS_DIR, HISTORY_DIR, IMAGES_DIR
            
            directories = {
                'data': DATA_DIR,
                'logs': LOGS_DIR,
                'history': HISTORY_DIR,
                'images': IMAGES_DIR
            }
            
            results = {}
            for name, path in directories.items():
                try:
                    path = Path(path)
                    results[name] = path.exists() and path.is_dir()
                    if not results[name]:
                        # Попытка создать директорию
                        path.mkdir(parents=True, exist_ok=True)
                        results[name] = path.exists()
                except Exception as e:
                    logger.warning(f"Ошибка проверки директории {name}: {e}")
                    results[name] = False
            
            return results
            
        except ImportError as e:
            logger.error(f"Ошибка импорта конфигурации директорий: {e}")
            return {}
    
    @classmethod
    def validate_all(cls, strict: bool = False) -> Dict[str, Any]:
        """
        Полная валидация конфигурации.
        
        Args:
            strict: Если True, поднимает исключение при критических ошибках
            
        Returns:
            Dict[str, Any]: Полные результаты валидации
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'env_vars': {},
            'api_keys': {},
            'assistants': {},
            'telegram': {},
            'directories': {}
        }
        
        # Проверка обязательных переменных окружения
        missing_required = cls.validate_required_env_vars()
        if missing_required:
            results['valid'] = False
            results['errors'].extend([f"Отсутствует обязательная переменная: {var}" for var in missing_required])
        
        # Проверка API ключей
        results['api_keys'] = cls.validate_api_keys()
        for service, valid in results['api_keys'].items():
            if not valid:
                results['warnings'].append(f"Проблема с API ключом {service}")
        
        # Проверка Assistants API
        results['assistants'] = cls.validate_assistants_config()
        if results['assistants']['use_assistants'] and results['assistants']['missing_assistants']:
            results['warnings'].extend([f"Отсутствует ассистент: {assistant}" for assistant in results['assistants']['missing_assistants']])
        
        # Проверка Telegram
        results['telegram'] = cls.validate_telegram_config()
        if not results['telegram']['ready_for_bot']:
            results['warnings'].append("Telegram бот не настроен (отсутствует токен или admin_chat_id)")
        
        # Проверка директорий
        results['directories'] = cls.validate_directories()
        for dir_name, exists in results['directories'].items():
            if not exists:
                results['errors'].append(f"Не удалось создать директорию: {dir_name}")
                results['valid'] = False
        
        # Если strict режим и есть ошибки
        if strict and not results['valid']:
            error_msg = "Критические ошибки конфигурации:\n" + "\n".join(results['errors'])
            raise ConfigValidationError(error_msg)
        
        return results
    
    @classmethod
    def print_validation_report(cls, results: Dict[str, Any]):
        """Вывод отчета о валидации."""
        print("\n" + "="*50)
        print("ОТЧЕТ О ВАЛИДАЦИИ КОНФИГУРАЦИИ")
        print("="*50)
        
        if results['valid']:
            print("✅ Конфигурация валидна")
        else:
            print("❌ Обнаружены критические ошибки")
        
        if results['errors']:
            print("\n🚨 ОШИБКИ:")
            for error in results['errors']:
                print(f"  - {error}")
        
        if results['warnings']:
            print("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
            for warning in results['warnings']:
                print(f"  - {warning}")
        
        # API ключи
        print("\n🔑 API КЛЮЧИ:")
        for service, valid in results['api_keys'].items():
            status = "✅" if valid else "❌"
            print(f"  {status} {service.upper()}")
        
        # Telegram
        telegram = results['telegram']
        print("\n📱 TELEGRAM:")
        print(f"  {'✅' if telegram['ready_for_bot'] else '❌'} Бот готов к работе")
        print(f"  {'✅' if telegram['ready_for_publishing'] else '❌'} Публикация готова")
        
        # Assistants API
        assistants = results['assistants']
        if assistants['use_assistants']:
            print("\n🤖 ASSISTANTS API:")
            print(f"  ✅ Включен")
            print(f"  📊 Доступно ассистентов: {len(assistants['available_assistants'])}")
            if assistants['missing_assistants']:
                print(f"  ⚠️  Отсутствует: {len(assistants['missing_assistants'])}")
        
        print("\n" + "="*50)


def validate_config_on_startup(strict: bool = True):
    """
    Валидация конфигурации при запуске приложения.
    
    Args:
        strict: Если True, завершает приложение при критических ошибках
    """
    try:
        results = ConfigValidator.validate_all(strict=False)
        ConfigValidator.print_validation_report(results)
        
        if strict and not results['valid']:
            print("\n❌ Приложение не может быть запущено из-за критических ошибок конфигурации.")
            print("Исправьте ошибки и попробуйте снова.")
            sys.exit(1)
        
        return results
        
    except Exception as e:
        logger.error(f"Ошибка валидации конфигурации: {e}")
        if strict:
            sys.exit(1)
        return None
