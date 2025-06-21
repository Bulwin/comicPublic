# Руководство по GPT Assistants в DailyComicBot

Этот документ содержит полную информацию о том, как настроены и работают GPT ассистенты в системе DailyComicBot.

## Обзор системы

DailyComicBot использует OpenAI Assistants API для создания сценариев комиксов и их оценки. Система состоит из двух типов ассистентов:

- **5 ассистентов-сценаристов** (типы A, B, C, D, E) - создают сценарии комиксов
- **5 ассистентов-жюри** (типы A, B, C, D, E) - оценивают созданные сценарии

## Файлы с инструкциями

### 1. Промпты для сценаристов
**Файл**: `DailyComicBot/instructions/gpt_scriptwriter_prompt.md`

Содержит базовый промпт для всех сценаристов с:
- Описанием роли и задач
- Форматом сценария (4 панели)
- Правилами оформления
- Примерами юмора
- Инструкциями по вызову функции `submit_script`

### 2. Промпты для жюри
**Файл**: `DailyComicBot/instructions/gpt_jury_prompt.md`

Содержит инструкции для оценки сценариев с:
- Критериями оценки (5 категорий, 100 баллов)
- Описанием типов жюри
- Форматом результата в JSON
- Примерами оценок
- Инструкциями по вызову функции `submit_evaluation`

### 3. Различия между типами сценаристов
**Файл**: `DailyComicBot/instructions/scriptwriter_types.md`

Описывает 5 типов сценаристов и их особенности:
- A: Классический юмор
- B: Черный юмор  
- C: Провокационный юмор
- D: Ирония и постирония
- E: Каламбуры и игра слов

## Настройка ассистентов в OpenAI

### Переменные окружения
В файле `.env` должны быть указаны ID всех ассистентов:

```env
# Сценаристы
SCRIPTWRITER_A_ASSISTANT_ID=asst_xxx
SCRIPTWRITER_B_ASSISTANT_ID=asst_xxx
SCRIPTWRITER_C_ASSISTANT_ID=asst_xxx
SCRIPTWRITER_D_ASSISTANT_ID=asst_xxx
SCRIPTWRITER_E_ASSISTANT_ID=asst_xxx

# Жюри
JURY_A_ASSISTANT_ID=asst_xxx
JURY_B_ASSISTANT_ID=asst_xxx
JURY_C_ASSISTANT_ID=asst_xxx
JURY_D_ASSISTANT_ID=asst_xxx
JURY_E_ASSISTANT_ID=asst_xxx
```

### Создание ассистентов

#### Для сценаристов:
1. **Instructions**: Скопировать содержимое `gpt_scriptwriter_prompt.md`
2. **Model**: gpt-4 или gpt-4-turbo
3. **Tools**: Добавить функции:
   - `get_news_details` - получение новости дня
   - `submit_script` - отправка готового сценария

#### Для жюри:
1. **Instructions**: Скопировать содержимое `gpt_jury_prompt.md`
2. **Model**: gpt-4 или gpt-4-turbo  
3. **Tools**: Добавить функции:
   - `get_news_details` - получение новости дня
   - `get_script_details` - получение сценария для оценки
   - `submit_evaluation` - отправка оценки

## Схемы функций

### get_news_details
```json
{
  "name": "get_news_details",
  "description": "Получение деталей новости дня",
  "parameters": {
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "description": "Дата в формате YYYY-MM-DD. Если не указана, используется текущая дата."
      }
    },
    "required": []
  }
}
```

### submit_script
```json
{
  "name": "submit_script",
  "description": "Отправка готового сценария комикса. ОБЯЗАТЕЛЬНО вызови эту функцию с готовым сценарием в JSON формате.",
  "parameters": {
    "type": "object",
    "properties": {
      "script": {
        "type": "object",
        "description": "Готовый сценарий комикса в JSON-формате с полями: title (заголовок), description (описание), panels (массив панелей), caption (подпись)",
        "properties": {
          "title": {
            "type": "string",
            "description": "Заголовок комикса"
          },
          "description": {
            "type": "string", 
            "description": "Общее описание комикса"
          },
          "panels": {
            "type": "array",
            "description": "Массив из 4 панелей комикса",
            "items": {
              "type": "object",
              "properties": {
                "description": {"type": "string"},
                "dialog": {"type": "array"},
                "narration": {"type": "string"}
              }
            }
          },
          "caption": {
            "type": "string",
            "description": "Подпись под комиксом"
          }
        },
        "required": ["title", "description", "panels", "caption"]
      }
    },
    "required": ["script"]
  }
}
```

### get_script_details
```json
{
  "name": "get_script_details",
  "description": "Получение деталей сценария комикса",
  "parameters": {
    "type": "object",
    "properties": {
      "script_id": {
        "type": "string",
        "description": "Идентификатор сценария"
      }
    },
    "required": ["script_id"]
  }
}
```

### submit_evaluation
```json
{
  "name": "submit_evaluation",
  "description": "Отправка готовой оценки",
  "parameters": {
    "type": "object",
    "properties": {
      "evaluation": {
        "type": "object",
        "description": "Оценка сценария в JSON-формате",
        "properties": {
          "scores": {
            "type": "object",
            "properties": {
              "relevance": {"type": "integer", "minimum": 0, "maximum": 20},
              "originality": {"type": "integer", "minimum": 0, "maximum": 20},
              "humor": {"type": "integer", "minimum": 0, "maximum": 30},
              "structure": {"type": "integer", "minimum": 0, "maximum": 15},
              "visual": {"type": "integer", "minimum": 0, "maximum": 15}
            }
          },
          "comments": {
            "type": "object",
            "properties": {
              "relevance": {"type": "string"},
              "originality": {"type": "string"},
              "humor": {"type": "string"},
              "structure": {"type": "string"},
              "visual": {"type": "string"}
            }
          },
          "total_score": {"type": "integer", "minimum": 0, "maximum": 100},
          "overall_comment": {"type": "string"}
        },
        "required": ["scores", "comments", "total_score", "overall_comment"]
      }
    },
    "required": ["evaluation"]
  }
}
```

## Workflow системы

### 1. Создание сценариев
1. Система получает новость дня
2. Запускает 5 ассистентов-сценаристов параллельно
3. Каждый ассистент:
   - Вызывает `get_news_details()` для получения новости
   - Создает сценарий в своем стиле
   - Вызывает `submit_script()` с готовым сценарием

### 2. Оценка сценариев
1. Система запускает 5 ассистентов-жюри для каждого сценария
2. Каждый член жюри:
   - Получает новость через `get_news_details()`
   - Получает сценарий для оценки
   - Оценивает по 5 критериям
   - Вызывает `submit_evaluation()` с оценкой

### 3. Выбор лучшего сценария
1. Система усредняет оценки всех жюри
2. Выбирает сценарий с наивысшим средним баллом
3. Передает его для создания изображения

## Отладка и логирование

Система ведет подробные логи всех взаимодействий с GPT ассистентами:

- Полные ответы от ассистентов
- Аргументы функций
- Ошибки и исключения
- Время выполнения операций

Логи помогают диагностировать проблемы с:
- Неправильным форматом ответов
- Пустыми аргументами функций
- Ошибками парсинга JSON
- Проблемами с API

## Рекомендации по настройке

### Для стабильной работы:
1. Используйте модель gpt-4 или gpt-4-turbo
2. Установите temperature 0.7-0.8 для креативности
3. Добавьте все необходимые функции
4. Тщательно скопируйте промпты из файлов
5. Проверьте все ID ассистентов в .env

### Для улучшения качества:
1. Регулярно анализируйте логи
2. Обновляйте промпты на основе результатов
3. Настраивайте параметры модели
4. Добавляйте примеры в промпты
5. Тестируйте изменения на небольших выборках

## Устранение неполадок

### Проблема: Ассистент не вызывает функции
**Решение**: Проверьте схемы функций и добавьте явные инструкции в промпт

### Проблема: Неправильный формат JSON
**Решение**: Добавьте примеры правильного формата в промпт

### Проблема: Пустые аргументы функций
**Решение**: Улучшите описание параметров в схеме функции

### Проблема: Низкое качество сценариев
**Решение**: Обновите примеры юмора и добавьте больше контекста

Этот документ должен помочь понять и настроить всю систему GPT ассистентов в DailyComicBot.
