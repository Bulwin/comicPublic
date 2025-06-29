# План реализации функции генерации анекдотов для DailyComicBot

## Обзор функции
Новая функция будет позволять генерировать анекдоты на основе новости дня, используя тех же авторов (GPT ассистентов), что и для комиксов. Пользователь сможет через Telegram бота выбирать лучший анекдот или запрашивать перегенерацию.

## ⚠️ КРИТИЧЕСКИ ВАЖНО: Сохранение существующего функционала
- **НЕ ИЗМЕНЯТЬ** существующие методы для комиксов
- **НЕ ИЗМЕНЯТЬ** структуру данных комиксов
- **НЕ ИЗМЕНЯТЬ** workflow комиксов в Telegram боте
- **ДОБАВЛЯТЬ** только новые методы и функции
- **ТЕСТИРОВАТЬ** совместимость на каждом этапе

## Архитектура решения

### 1. Модификация GPT Assistants
**Статус:** ⏳ Требует ручной настройки в UI OpenAI

#### Что нужно сделать в UI OpenAI:
- [ ] Обновить промпты всех 5 ассистентов (A, B, C, D, E)
- [ ] Добавить в инструкции возможность генерации анекдотов
- [ ] Добавить новую функцию `submit_joke` в tools каждого ассистента

#### Пример дополнения к промпту:
```
ДОПОЛНИТЕЛЬНАЯ ВОЗМОЖНОСТЬ: Генерация анекдотов
Кроме комиксов, ты можешь создавать анекдоты на основе новости дня.
Когда пользователь просит анекдот, создай короткую смешную историю (1-3 абзаца) 
на тему новости. Используй свой уникальный стиль юмора.
Для отправки анекдота используй функцию submit_joke.
```

### 2. Новые компоненты (НЕ ИЗМЕНЯЮТ существующие)

#### 2.1 Новый агент для анекдотов
**Файл:** `DailyComicBot/agents/joke_writer.py`
**Статус:** ⏳ Новый файл

```python
# Основные методы:
- generate_jokes(news) -> List[Dict]  # Генерация анекдотов всеми авторами
- select_best_joke(jokes) -> Dict     # Выбор лучшего анекдота (по умолчанию первый)
```

#### 2.2 Расширение хранения данных
**Файл:** `DailyComicBot/tools/storage_tools.py`
**Статус:** ⏳ Добавить новые функции (НЕ ИЗМЕНЯТЬ существующие)

```python
# Новые функции (добавить в конец файла):
- store_joke(joke, date=None) -> bool
- store_jokes(jokes, date=None) -> bool  
- load_jokes(date=None) -> List[Dict]
- store_joke_publication(publication_data, date=None) -> bool
```

#### 2.3 Расширение публикации
**Файл:** `DailyComicBot/tools/publishing_tools.py`
**Статус:** ⏳ Добавить новые функции (НЕ ИЗМЕНЯТЬ существующие)

```python
# Новые функции (добавить в конец файла):
- publish_joke_to_channel(joke_text, news_title, author_name) -> Dict
- format_joke_caption(joke_text, news_title, author_name) -> str
```

### 3. Расширение Telegram бота (ОСТОРОЖНО!)

#### 3.1 Новые команды и кнопки
**Файл:** `DailyComicBot/telegram_bot.py`
**Статус:** ⏳ Добавить новые методы (НЕ ИЗМЕНЯТЬ существующие)

**Изменения в главном меню:**
```python
# В методе start_command добавить новую кнопку:
[InlineKeyboardButton("🎭 Создать анекдот", callback_data="create_joke")]
```

**Новые callback handlers:**
```python
# Добавить в button_callback:
elif action == "create_joke":
    await self._create_joke(query)
elif action == "regenerate_jokes":
    await self._regenerate_jokes(query)
elif action.startswith("select_joke_"):
    author_type = action.split("_")[-1]
    await self._select_joke(query, author_type)
elif action == "publish_joke_now":
    await self._publish_joke_now(query)
elif action == "schedule_joke":
    await self._schedule_joke(query)
```

#### 3.2 Новые методы (добавить в конец класса)
```python
async def _create_joke(self, query)
async def _regenerate_jokes(self, query)
async def _select_joke(self, query, author_type)
async def _publish_joke_now(self, query)
async def _schedule_joke(self, query)
async def _send_jokes_for_selection(self, jokes)
```

### 4. Расширение manager.py (ОСТОРОЖНО!)

#### 4.1 Новые методы в ManagerAgent
**Файл:** `DailyComicBot/agents/manager.py`
**Статус:** ⏳ Добавить новые методы (НЕ ИЗМЕНЯТЬ существующие)

```python
# Добавить в конец класса ManagerAgent:
def generate_jokes(self) -> List[Dict[str, Any]]
def select_best_joke(self, jokes) -> Optional[Dict[str, Any]]
def publish_joke(self, joke) -> Optional[Dict[str, Any]]
def run_joke_process(self, force_new_news=False) -> Dict[str, Any]
```

#### 4.2 Новые атрибуты класса
```python
# Добавить в __init__:
self.jokes = []
self.selected_joke = None
self.joke_publication_results = None
```

### 5. Расширение assistants_api.py

#### 5.1 Новые функции
**Файл:** `DailyComicBot/utils/assistants_api.py`
**Статус:** ⏳ Добавить новые функции

```python
# Добавить в конец файла:
def invoke_joke_writer(news: Dict[str, Any], writer_type: str) -> Optional[Dict[str, Any]]
def _submit_joke(self, joke: Dict[str, Any]) -> Dict[str, Any]  # В класс AssistantsManager
```

#### 5.2 Новый tool для ассистентов
```python
# Добавить в create_scriptwriter_assistant:
{
    "type": "function",
    "function": {
        "name": "submit_joke",
        "description": "Отправка готового анекдота",
        "parameters": {
            "type": "object",
            "properties": {
                "joke": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["title", "content"]
                }
            },
            "required": ["joke"]
        }
    }
}
```

### 6. Структура данных для анекдота

```python
{
    "joke_id": "A_20250629123456",
    "writer_type": "A", 
    "writer_name": "Добряк Петрович",
    "title": "Заголовок анекдота",
    "content": "Текст анекдота...",
    "news": {
        "title": "Заголовок новости",
        "content": "Содержание новости"
    },
    "created_at": "2025-06-29T12:34:56"
}
```

### 7. Новые переменные окружения

```bash
# Добавить в .env:
JOKE_PUBLICATION_HOUR=14
JOKE_PUBLICATION_MINUTE=0
```

## Этапы реализации с чеклистом

### Этап 1: Базовая инфраструктура ✅ ЗАВЕРШЕН
- [x] **1.1** Создать `agents/joke_writer.py` ✅
- [x] **1.2** Добавить функции хранения анекдотов в `storage_tools.py` ✅
- [x] **1.3** Обновить `assistants_api.py` для поддержки анекдотов ✅
- [x] **1.4** Создать тестовый скрипт `test_jokes_generation.py` ✅
- [x] **1.5** Протестировать генерацию анекдотов без UI ✅

**Критерий готовности:** ✅ Можно генерировать анекдоты через код без Telegram бота

**Результаты тестирования:** 7/7 тестов пройдено успешно
- ✅ Импорт всех модулей работает
- ✅ Функции хранения анекдотов работают
- ✅ Генерация анекдотов с заглушками работает
- ✅ Выбор анекдотов по авторам работает
- ✅ Сохранение и загрузка анекдотов работает

### Этап 2: Интеграция в manager ✅ ЗАВЕРШЕН
- [x] **2.1** Добавить методы работы с анекдотами в `manager.py` ✅
- [x] **2.2** Обеспечить переиспользование новости дня ✅
- [x] **2.3** Создать тестовый скрипт `test_jokes_manager.py` ✅
- [x] **2.4** Протестировать полный цикл через manager ✅

**Критерий готовности:** ✅ Manager может создавать анекдоты независимо от комиксов

**Результаты тестирования:** 9/9 тестов пройдено успешно
- ✅ Импорт обновленного manager работает
- ✅ Новые атрибуты для анекдотов добавлены
- ✅ Все новые методы для анекдотов работают
- ✅ Генерация анекдотов через manager работает
- ✅ Выбор лучшего анекдота работает
- ✅ Получение анекдотов по авторам работает
- ✅ Полный процесс создания анекдотов работает
- ✅ Переиспользование новости между комиксами и анекдотами работает
- ✅ Совместимость со старыми методами сохранена

### Этап 3: Публикация анекдотов ✅ ЗАВЕРШЕН
- [x] **3.1** Добавить функции публикации в `publishing_tools.py` ✅
- [x] **3.2** Создать тестовый скрипт `test_jokes_publishing.py` ✅
- [x] **3.3** Протестировать публикацию анекдотов ✅

**Критерий готовности:** ✅ Можно публиковать анекдоты в канал

**Результаты тестирования:** 9/9 тестов пройдено успешно
- ✅ Импорт функций публикации анекдотов работает
- ✅ Форматирование подписи для анекдота работает (с датой, эмодзи 🎭, хештегами)
- ✅ Обрезание длинных подписей работает корректно
- ✅ **Реальная публикация в канал работает** (message_id: 28-32)
- ✅ Полная публикация анекдота работает (заголовок + содержание)
- ✅ Публикация на всех платформах работает (Telegram ✅, Instagram корректно отклонен)
- ✅ Публикация через manager работает с сохранением результатов
- ✅ Полный процесс создания и публикации анекдотов работает
- ✅ Совместимость с функциями комиксов сохранена

**Новые функции добавлены в `publishing_tools.py`:**
- `format_joke_caption()` - форматирование подписи для анекдота
- `publish_joke_to_channel()` - публикация анекдота в канал
- `publish_joke_complete()` - полная публикация анекдота
- `publish_joke_to_all_platforms()` - публикация на всех платформах

**Интеграция с manager:**
- Обновлен метод `publish_joke()` в manager для использования реальных функций публикации
- Полный цикл: генерация → выбор → публикация работает через manager

### Этап 4: Интеграция в Telegram бот ✅ ЗАВЕРШЕН
- [x] **4.1** Добавить новые команды и кнопки в `telegram_bot.py` ✅
- [x] **4.2** Реализовать workflow выбора анекдота ✅
- [x] **4.3** Добавить планирование публикации ✅
- [x] **4.4** Протестировать через Telegram бота ✅

**Критерий готовности:** ✅ Полный workflow анекдотов работает в Telegram боте

**Результаты тестирования:** 10/10 тестов пройдено успешно
- ✅ Импорт обновленного Telegram бота работает
- ✅ Инициализация бота с manager и admin_chat_id работает
- ✅ Все 8 новых методов для анекдотов присутствуют
- ✅ Команда /start обновлена с кнопкой "🎭 Создать анекдот"
- ✅ Обработчик кнопок содержит все 6 новых callback'ов для анекдотов
- ✅ Интеграция с manager: все методы и атрибуты для анекдотов работают
- ✅ Симуляция workflow анекдотов: полный цикл создания работает
- ✅ **Реальная публикация анекдотов работает** (message_id: 33-34)
- ✅ Совместимость с комиксами: все старые методы и callback'ы сохранены
- ✅ Переменные окружения для планирования публикации настроены (14:00)

**Новые функции в Telegram боте:**
- Кнопка "🎭 Создать анекдот" в главном меню
- Workflow выбора анекдота из 5 вариантов от разных авторов
- Возможность перегенерации анекдотов
- Немедленная публикация или планирование на 14:00
- Полная интеграция с существующим manager

**Новые методы в `telegram_bot.py`:**
- `_create_joke()` - создание анекдотов на основе новости дня
- `_regenerate_jokes()` - перегенерация анекдотов
- `_send_jokes_for_selection()` - отправка анекдотов для выбора
- `_select_joke()` - выбор конкретного анекдота
- `_send_joke_for_approval()` - отправка выбранного анекдота для одобрения
- `_publish_joke_now()` - немедленная публикация анекдота
- `_schedule_joke()` - планирование публикации анекдота
- `_approve_joke_publication()` - одобрение публикации анекдота

### Этап 4.5: Настройка GPT Assistants (РУЧНАЯ РАБОТА) ⏳ В ПРОЦЕССЕ
- [x] **4.5.0** Создать инструкции по настройке GPT Assistants ✅
- [x] **4.5.1** Обновить промпты всех 5 ассистентов (A, B, C, D, E) в UI OpenAI ✅
- [x] **4.5.2** Добавить в инструкции возможность генерации анекдотов ✅
- [x] **4.5.3** Добавить новую функцию `submit_joke` в код ассистентов ✅
- [ ] **4.5.4** Протестировать реальные GPT Assistants с анекдотами ⏳ ТЕСТИРУЕТСЯ
- [ ] **4.5.5** Убедиться, что комиксы по-прежнему работают

**Критерий готовности:** Реальные GPT Assistants генерируют и комиксы, и анекдоты

**Инструкции созданы:** ✅
- `GPT_ASSISTANTS_JOKES_SETUP.md` - пошаговая инструкция по настройке
- `instructions/gpt_scriptwriter_prompt_with_jokes.md` - обновленный промпт с поддержкой анекдотов
- Готовая JSON схема для функции `submit_joke`
- Список всех 5 ассистентов для обновления

**Пример дополнения к промпту:**
```
ДОПОЛНИТЕЛЬНАЯ ВОЗМОЖНОСТЬ: Генерация анекдотов
Кроме комиксов, ты можешь создавать анекдоты на основе новости дня.
Когда пользователь просит анекдот, создай короткую смешную историю (1-3 абзаца) 
на тему новости. Используй свой уникальный стиль юмора.
Для отправки анекдота используй функцию submit_joke.
```

**Новый tool для ассистентов:**
```json
{
    "type": "function",
    "function": {
        "name": "submit_joke",
        "description": "Отправка готового анекдота",
        "parameters": {
            "type": "object",
            "properties": {
                "joke": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["title", "content"]
                }
            },
            "required": ["joke"]
        }
    }
}
```

### Этап 5: Финальное тестирование
- [ ] **5.1** Протестировать совместную работу комиксов и анекдотов
- [ ] **5.2** Убедиться, что комиксы работают как раньше
- [ ] **5.3** Протестировать все edge cases
- [ ] **5.4** Обновить документацию

**Критерий готовности:** Обе функции работают независимо и не мешают друг другу

## Тестовые сценарии

### Тест совместимости с комиксами
1. Создать комикс через старый workflow
2. Убедиться, что все работает как раньше
3. Создать анекдот через новый workflow
4. Убедиться, что комиксы не сломались

### Тест независимости функций
1. Создать анекдот, не создавая комикс
2. Создать комикс, не создавая анекдот
3. Создать и то, и другое в один день
4. Убедиться, что данные не пересекаются

## Файлы для создания/изменения

### Новые файлы (безопасно):
- [ ] `DailyComicBot/agents/joke_writer.py`
- [ ] `DailyComicBot/test_jokes_generation.py`
- [ ] `DailyComicBot/test_jokes_manager.py`
- [ ] `DailyComicBot/test_jokes_publishing.py`
- [ ] `DailyComicBot/test_jokes_telegram.py`

### Файлы для расширения (ОСТОРОЖНО!):
- [ ] `DailyComicBot/tools/storage_tools.py` - добавить функции в конец
- [ ] `DailyComicBot/tools/publishing_tools.py` - добавить функции в конец
- [ ] `DailyComicBot/utils/assistants_api.py` - добавить функции в конец
- [ ] `DailyComicBot/agents/manager.py` - добавить методы в конец класса
- [ ] `DailyComicBot/telegram_bot.py` - добавить методы в конец класса

### Файлы конфигурации:
- [ ] `DailyComicBot/.env.example` - добавить новые переменные
- [ ] `DailyComicBot/config.example.py` - добавить новые настройки (если нужно)

## Принципы безопасной разработки

1. **Добавлять, не изменять** - все новые функции добавляются как дополнительные
2. **Тестировать на каждом этапе** - после каждого изменения проверять комиксы
3. **Использовать отдельные данные** - анекдоты хранятся отдельно от комиксов
4. **Независимые workflows** - анекдоты не влияют на процесс комиксов
5. **Обратная совместимость** - старые команды и API остаются неизменными

## Готовность к началу

Перед началом реализации убедиться:
- [ ] Создан бекап текущего состояния проекта
- [ ] Настроена среда разработки
- [ ] Доступны все необходимые API ключи
- [ ] Понятна текущая архитектура проекта

## Следующие шаги

1. Подтвердить план с командой
2. Создать бекап проекта
3. Начать с Этапа 1: Базовая инфраструктура
4. Тестировать на каждом шаге
5. Документировать изменения

---

**Автор плана:** AI Assistant  
**Дата создания:** 29.06.2025  
**Версия:** 1.0  
**Статус:** Готов к реализации
