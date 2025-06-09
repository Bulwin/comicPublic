"""
Модуль агентов-жюри для проекта DailyComicBot.
Отвечает за оценку сценариев комиксов.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import random

# Импорт модулей проекта
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import logger, handle_exceptions, measure_execution_time
from config import SCRIPTWRITERS


class JuryAgent:
    """
    Агент-жюри, оценивающий сценарии комиксов.
    """
    
    def __init__(self, jury_type: str):
        """
        Инициализация агента-жюри.
        
        Args:
            jury_type (str): Тип жюри (A, B, C, D, E).
        """
        if jury_type not in SCRIPTWRITERS:
            raise ValueError(f"Неизвестный тип жюри: {jury_type}")
        
        self.jury_type = jury_type
        self.jury_info = SCRIPTWRITERS[jury_type]
        self.name = self.jury_info["name"]
        self.description = self.jury_info["description"]
        
        logger.info(f"Агент-жюри {self.name} (тип {jury_type}) инициализирован")
    
    @measure_execution_time
    def evaluate_script(self, script: Dict[str, Any], news: Dict[str, Any]) -> Dict[str, Any]:
        """
        Оценка сценария комикса.
        
        Args:
            script (Dict[str, Any]): Сценарий комикса.
            news (Dict[str, Any]): Информация о новости дня.
            
        Returns:
            Dict[str, Any]: Результат оценки.
        """
        logger.info(f"Жюри {self.name} начинает оценку сценария {script.get('script_id', 'без ID')}")
        
        # Формирование запроса для OpenAI API
        prompt = self._create_prompt(script, news)
        
        # Вызов OpenAI API для оценки сценария
        evaluation = self._generate_evaluation(prompt, script)
        
        # Добавление метаданных
        evaluation["jury_type"] = self.jury_type
        evaluation["jury_name"] = self.name
        evaluation["script_id"] = script.get("script_id", "unknown")
        
        # Логирование оценки сценария
        logger.log_script_evaluation(
            self.name,
            script.get('script_id', 'unknown'),
            evaluation.get('total_score', 0)
        )
        return evaluation
    
    def _create_prompt(self, script: Dict[str, Any], news: Dict[str, Any]) -> str:
        """
        Создание промпта для оценки сценария.
        
        Args:
            script (Dict[str, Any]): Сценарий комикса.
            news (Dict[str, Any]): Информация о новости дня.
            
        Returns:
            str: Промпт для оценки сценария.
        """
        # Базовая информация о новости и сценарии
        news_title = news.get("title", "")
        news_content = news.get("content", "")
        script_title = script.get("title", "")
        script_description = script.get("description", "")
        script_panels = script.get("panels", [])
        script_caption = script.get("caption", "")
        
        # Формирование текстового представления сценария
        script_text = f"Заголовок: {script_title}\n\nОписание: {script_description}\n\n"
        
        for i, panel in enumerate(script_panels):
            script_text += f"Панель {i+1}:\n"
            script_text += f"Описание: {panel.get('description', '')}\n"
            
            dialogs = panel.get("dialog", [])
            if dialogs:
                script_text += "Диалоги:\n"
                for dialog in dialogs:
                    character = dialog.get("character", "")
                    text = dialog.get("text", "")
                    note = dialog.get("note", "")
                    
                    if note:
                        script_text += f"- {character} ({note}): \"{text}\"\n"
                    else:
                        script_text += f"- {character}: \"{text}\"\n"
            
            narration = panel.get("narration", "")
            if narration:
                script_text += f"Текст от автора: {narration}\n"
            
            script_text += "\n"
        
        script_text += f"Подпись: {script_caption}"
        
        # Формирование промпта в зависимости от типа жюри
        prompt = f"""
        Ты - член жюри, оценивающий сценарии комиксов. Твой стиль оценки соответствует: {self.description}
        
        Оцени следующий сценарий комикса, созданный на основе новости дня:
        
        НОВОСТЬ ДНЯ:
        Заголовок: {news_title}
        
        Содержание: {news_content}
        
        СЦЕНАРИЙ КОМИКСА:
        {script_text}
        
        Оцени сценарий по следующим критериям (в сумме максимум 100 баллов):
        1. Релевантность (0-20 баллов): насколько сценарий связан с новостью дня
        2. Оригинальность (0-20 баллов): новизна идеи и подхода
        3. Юмористический потенциал (0-30 баллов): насколько сценарий действительно смешной
        4. Структура и логика (0-15 баллов): наличие четкой структуры и логичность развития сюжета
        5. Визуальный потенциал (0-15 баллов): насколько хорошо сценарий можно визуализировать
        
        Для каждого критерия укажи баллы и краткое обоснование оценки.
        В конце предоставь итоговую оценку (сумму баллов) и общий комментарий.
        """
        
        # Дополнительные инструкции в зависимости от типа жюри
        if self.jury_type == "A":
            prompt += """
            Как ценитель классического юмора, обрати особое внимание на доступность шуток для широкой аудитории,
            отсутствие грубости и пошлости, универсальность юмора.
            Высоко оценивай семейный юмор и шутки, понятные людям всех возрастов.
            """
        elif self.jury_type == "B":
            prompt += """
            Как ценитель черного юмора, обрати особое внимание на оригинальность, неожиданность, глубину,
            умение балансировать на грани. Высоко оценивай смелость и умение говорить о сложных темах с юмором.
            """
        elif self.jury_type == "C":
            prompt += """
            Как ценитель провокационного юмора, обрати особое внимание на смелость, провокационность,
            умение вызвать реакцию. Высоко оценивай шутки, которые бросают вызов политкорректности,
            но не переходят в прямые оскорбления.
            """
        elif self.jury_type == "D":
            prompt += """
            Как ценитель иронии и постиронии, обрати особое внимание на многослойность, интеллектуальность,
            отсылки к поп-культуре. Высоко оценивай сложные шутки, требующие определенного уровня знаний
            и понимания контекста.
            """
        elif self.jury_type == "E":
            prompt += """
            Как ценитель каламбуров, обрати особое внимание на изобретательность, оригинальность,
            языковое мастерство. Высоко оценивай умное использование языка, многозначности слов и созвучий.
            """
        
        return prompt
    
    def _generate_evaluation(self, prompt: str, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерация оценки с помощью OpenAI API.
        
        Args:
            prompt (str): Промпт для оценки сценария.
            script (Dict[str, Any]): Сценарий комикса.
            
        Returns:
            Dict[str, Any]: Результат оценки.
        """
        try:
            # Попытка использовать OpenAI API через MCP сервер
            from utils import use_mcp_tool
            
            # Вызов OpenAI API через MCP сервер
            response = use_mcp_tool(
                server_name="openai",
                tool_name="chat",
                arguments={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": f"Ты - член жюри комиксов с именем {self.name}. {self.description}"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }
            )
            
            # Если получен ответ от API
            if response and "content" in response:
                # Парсинг ответа для извлечения оценок и комментариев
                return self._parse_gpt_response(response["content"], script)
            
            # Если не удалось получить ответ от API, используем заглушку
            logger.warning(f"Не удалось получить ответ от OpenAI API, используется заглушка для функции _generate_evaluation (тип: {self.jury_type})")
            return self._generate_fallback_evaluation(script)
            
        except Exception as e:
            # В случае ошибки используем заглушку
            logger.error(f"Ошибка при вызове OpenAI API: {str(e)}")
            logger.warning(f"Используется заглушка для функции _generate_evaluation (тип: {self.jury_type})")
            return self._generate_fallback_evaluation(script)
    
    def _parse_gpt_response(self, response_text: str, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсинг ответа от GPT для извлечения оценок и комментариев.
        
        Args:
            response_text (str): Текст ответа от GPT.
            script (Dict[str, Any]): Сценарий комикса.
            
        Returns:
            Dict[str, Any]: Результат оценки.
        """
        try:
            # Инициализация оценок и комментариев
            scores = {
                "relevance": 0,
                "originality": 0,
                "humor": 0,
                "structure": 0,
                "visual": 0
            }
            comments = {
                "relevance": "",
                "originality": "",
                "humor": "",
                "structure": "",
                "visual": ""
            }
            overall_comment = ""
            total_score = 0
            
            # Поиск оценок в тексте ответа
            for line in response_text.split('\n'):
                line = line.strip()
                
                # Поиск оценки релевантности
                if "релевантность" in line.lower() and "балл" in line.lower():
                    scores["relevance"] = self._extract_score(line)
                    comments["relevance"] = self._extract_comment(line)
                
                # Поиск оценки оригинальности
                elif "оригинальность" in line.lower() and "балл" in line.lower():
                    scores["originality"] = self._extract_score(line)
                    comments["originality"] = self._extract_comment(line)
                
                # Поиск оценки юмора
                elif "юмористический" in line.lower() and "балл" in line.lower():
                    scores["humor"] = self._extract_score(line)
                    comments["humor"] = self._extract_comment(line)
                
                # Поиск оценки структуры
                elif "структура" in line.lower() and "балл" in line.lower():
                    scores["structure"] = self._extract_score(line)
                    comments["structure"] = self._extract_comment(line)
                
                # Поиск оценки визуального потенциала
                elif "визуальный" in line.lower() and "балл" in line.lower():
                    scores["visual"] = self._extract_score(line)
                    comments["visual"] = self._extract_comment(line)
                
                # Поиск итоговой оценки
                elif ("итоговая оценка" in line.lower() or "общая оценка" in line.lower() or "всего" in line.lower()) and "балл" in line.lower():
                    total_score = self._extract_score(line)
                
                # Поиск общего комментария
                elif "общий комментарий" in line.lower() or "итоговый комментарий" in line.lower():
                    # Общий комментарий может быть на следующей строке
                    if line.lower().startswith("общий комментарий") or line.lower().startswith("итоговый комментарий"):
                        # Ищем следующую непустую строку
                        for next_line in response_text.split('\n')[response_text.split('\n').index(line) + 1:]:
                            if next_line.strip():
                                overall_comment = next_line.strip()
                                break
                    else:
                        # Комментарий в той же строке
                        overall_comment = line.split(":", 1)[1].strip() if ":" in line else line
            
            # Если не удалось найти итоговую оценку, вычисляем ее
            if total_score == 0:
                total_score = sum(scores.values())
            
            # Если не удалось найти общий комментарий, генерируем его
            if not overall_comment:
                if total_score >= 80:
                    overall_comment = f"Отличный сценарий! {self._get_positive_comment(script)}"
                elif total_score >= 60:
                    overall_comment = f"Хороший сценарий. {self._get_neutral_comment(script)}"
                else:
                    overall_comment = f"Сценарий нуждается в доработке. {self._get_negative_comment(script)}"
            
            return {
                "scores": scores,
                "comments": comments,
                "total_score": total_score,
                "overall_comment": overall_comment
            }
            
        except Exception as e:
            # В случае ошибки при парсинге используем заглушку
            logger.error(f"Ошибка при парсинге ответа от GPT: {str(e)}")
            return self._generate_fallback_evaluation(script)
    
    def _extract_score(self, line: str) -> int:
        """
        Извлечение оценки из строки текста.
        
        Args:
            line (str): Строка текста.
            
        Returns:
            int: Оценка.
        """
        try:
            # Поиск числа в строке
            import re
            numbers = re.findall(r'\d+', line)
            if numbers:
                return int(numbers[0])
            return 0
        except Exception:
            return 0
    
    def _extract_comment(self, line: str) -> str:
        """
        Извлечение комментария из строки текста.
        
        Args:
            line (str): Строка текста.
            
        Returns:
            str: Комментарий.
        """
        try:
            # Поиск комментария после двоеточия или тире
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    # Удаление оценки из комментария
                    comment = parts[1].strip()
                    import re
                    comment = re.sub(r'\d+/\d+', '', comment).strip()
                    return comment
            elif "-" in line:
                parts = line.split("-", 1)
                if len(parts) > 1:
                    # Удаление оценки из комментария
                    comment = parts[1].strip()
                    import re
                    comment = re.sub(r'\d+/\d+', '', comment).strip()
                    return comment
            
            # Если не удалось найти комментарий, возвращаем всю строку
            return line
        except Exception:
            return line
    
    def _generate_fallback_evaluation(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерация заглушки для оценки сценария.
        
        Args:
            script (Dict[str, Any]): Сценарий комикса.
            
        Returns:
            Dict[str, Any]: Результат оценки.
        """
        # Базовые оценки для всех типов жюри
        base_scores = {
            "relevance": 15,  # из 20
            "originality": 15,  # из 20
            "humor": 20,  # из 30
            "structure": 10,  # из 15
            "visual": 10  # из 15
        }
        
        # Модификация оценок в зависимости от типа жюри и сценариста
        writer_type = script.get("writer_type", "")
        
        if self.jury_type == writer_type:
            # Жюри оценивает выше сценарий своего типа
            for key in base_scores:
                base_scores[key] = min(base_scores[key] + 3, 20 if key in ["relevance", "originality"] else 30 if key == "humor" else 15)
        elif (self.jury_type == "A" and writer_type == "C") or (self.jury_type == "C" and writer_type == "A"):
            # Противоположные типы жюри оценивают ниже
            for key in base_scores:
                base_scores[key] = max(base_scores[key] - 3, 0)
        
        # Случайные вариации для реалистичности
        for key in base_scores:
            base_scores[key] = max(0, min(base_scores[key] + random.randint(-2, 2), 20 if key in ["relevance", "originality"] else 30 if key == "humor" else 15))
        
        # Вычисление общей оценки
        total_score = sum(base_scores.values())
        
        # Формирование комментариев
        comments = {
            "relevance": self._generate_comment("relevance", base_scores["relevance"], script),
            "originality": self._generate_comment("originality", base_scores["originality"], script),
            "humor": self._generate_comment("humor", base_scores["humor"], script),
            "structure": self._generate_comment("structure", base_scores["structure"], script),
            "visual": self._generate_comment("visual", base_scores["visual"], script)
        }
        
        # Формирование общего комментария
        if total_score >= 80:
            overall_comment = f"Отличный сценарий! {self._get_positive_comment(script)}"
        elif total_score >= 60:
            overall_comment = f"Хороший сценарий. {self._get_neutral_comment(script)}"
        else:
            overall_comment = f"Сценарий нуждается в доработке. {self._get_negative_comment(script)}"
        
        return {
            "scores": base_scores,
            "comments": comments,
            "total_score": total_score,
            "overall_comment": overall_comment
        }
    
    def _generate_comment(self, criterion: str, score: int, script: Dict[str, Any]) -> str:
        """
        Генерация комментария для критерия оценки.
        
        Args:
            criterion (str): Критерий оценки.
            score (int): Оценка по критерию.
            script (Dict[str, Any]): Сценарий комикса.
            
        Returns:
            str: Комментарий.
        """
        # Заглушки для комментариев
        if criterion == "relevance":
            if score >= 15:
                return "Сценарий отлично связан с новостью дня, обыгрывает ключевые аспекты."
            elif score >= 10:
                return "Сценарий в целом связан с новостью дня, но некоторые аспекты упущены."
            else:
                return "Сценарий слабо связан с новостью дня, многие ключевые аспекты упущены."
        
        elif criterion == "originality":
            if score >= 15:
                return "Очень оригинальный подход, свежие идеи и неожиданные повороты."
            elif score >= 10:
                return "Достаточно оригинальный подход, хотя некоторые идеи кажутся знакомыми."
            else:
                return "Недостаточно оригинальный подход, много клише и предсказуемых решений."
        
        elif criterion == "humor":
            if score >= 20:
                return "Очень смешной сценарий, вызывает искренний смех, отличные шутки."
            elif score >= 15:
                return "Достаточно смешной сценарий, есть несколько удачных шуток."
            else:
                return "Недостаточно смешной сценарий, шутки слабые или отсутствуют."
        
        elif criterion == "structure":
            if score >= 10:
                return "Хорошая структура с четкой завязкой, развитием и кульминацией."
            else:
                return "Структура нуждается в доработке, не хватает логики развития сюжета."
        
        elif criterion == "visual":
            if score >= 10:
                return "Отличный визуальный потенциал, сценарий легко представить в виде комикса."
            else:
                return "Визуальный потенциал ограничен, сложно представить некоторые сцены в виде комикса."
        
        return "Нет комментария."
    
    def _get_positive_comment(self, script: Dict[str, Any]) -> str:
        """
        Получение положительного комментария в зависимости от типа жюри.
        
        Args:
            script (Dict[str, Any]): Сценарий комикса.
            
        Returns:
            str: Положительный комментарий.
        """
        if self.jury_type == "A":
            return "Отличный пример классического юмора, понятного широкой аудитории."
        elif self.jury_type == "B":
            return "Отличный пример черного юмора, балансирующего на грани без перехода границ."
        elif self.jury_type == "C":
            return "Отличный пример провокационного юмора, вызывающего реакцию без прямых оскорблений."
        elif self.jury_type == "D":
            return "Отличный пример иронии и постиронии, с многослойными шутками и отсылками."
        elif self.jury_type == "E":
            return "Отличный пример использования каламбуров и игры слов, демонстрирующий языковое мастерство."
        
        return "Отличная работа!"
    
    def _get_neutral_comment(self, script: Dict[str, Any]) -> str:
        """
        Получение нейтрального комментария в зависимости от типа жюри.
        
        Args:
            script (Dict[str, Any]): Сценарий комикса.
            
        Returns:
            str: Нейтральный комментарий.
        """
        if self.jury_type == "A":
            return "Неплохой пример классического юмора, но можно сделать шутки более доступными."
        elif self.jury_type == "B":
            return "Неплохой пример черного юмора, но можно добавить больше глубины и неожиданности."
        elif self.jury_type == "C":
            return "Неплохой пример провокационного юмора, но можно добавить больше смелости."
        elif self.jury_type == "D":
            return "Неплохой пример иронии, но можно добавить больше слоев и отсылок."
        elif self.jury_type == "E":
            return "Неплохой пример использования каламбуров, но можно добавить больше языкового мастерства."
        
        return "Неплохая работа, но есть куда расти."
    
    def _get_negative_comment(self, script: Dict[str, Any]) -> str:
        """
        Получение отрицательного комментария в зависимости от типа жюри.
        
        Args:
            script (Dict[str, Any]): Сценарий комикса.
            
        Returns:
            str: Отрицательный комментарий.
        """
        if self.jury_type == "A":
            return "Не соответствует стандартам классического юмора, шутки непонятны широкой аудитории."
        elif self.jury_type == "B":
            return "Не соответствует стандартам черного юмора, не хватает глубины и неожиданности."
        elif self.jury_type == "C":
            return "Не соответствует стандартам провокационного юмора, не вызывает реакции."
        elif self.jury_type == "D":
            return "Не соответствует стандартам иронии и постиронии, шутки однослойные и без отсылок."
        elif self.jury_type == "E":
            return "Не соответствует стандартам каламбуров, не хватает языкового мастерства."
        
        return "Требуется серьезная доработка."


# Функция для создания агента-жюри
def create_jury(jury_type: str) -> JuryAgent:
    """
    Создание агента-жюри.
    
    Args:
        jury_type (str): Тип жюри (A, B, C, D, E).
        
    Returns:
        JuryAgent: Агент-жюри.
    """
    return JuryAgent(jury_type)


# Функция для оценки сценария
def evaluate_script(jury_type: str, script: Dict[str, Any], news: Dict[str, Any]) -> Dict[str, Any]:
    """
    Оценка сценария комикса.
    
    Args:
        jury_type (str): Тип жюри (A, B, C, D, E).
        script (Dict[str, Any]): Сценарий комикса.
        news (Dict[str, Any]): Информация о новости дня.
        
    Returns:
        Dict[str, Any]: Результат оценки.
    """
    jury = create_jury(jury_type)
    return jury.evaluate_script(script, news)
