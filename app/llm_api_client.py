import json
from collections import Counter

from google import genai
from datetime import datetime
import requests
import config
from search import find_bird


def parse_bird_observations(text):
    observations = {}

    blocks = text.strip().split("\n\n")

    bird_counter = 1

    for block in blocks:
        if not block.strip():
            continue

        fields = {}
        for line in block.split("\n"):
            if " — " in line:
                key, value = line.split(" — ", 1)
                fields[key.strip()] = value.strip()

        if "Название птицы" not in fields:
            continue

        observation = {
            "название": fields.get("Название птицы", ""),
            "точная_дата": None,
            "точное_время": None,
            "ключевые_фразы": []
        }

        if "Точная дата" in fields and fields["Точная дата"]:
            try:
                date_str = fields["Точная дата"]
                for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]:
                    try:
                        observation["точная_дата"] = datetime.strptime(date_str, fmt).date()
                        break
                    except ValueError:
                        continue
            except Exception:
                observation["точная_дата"] = None

        if "Точное время" in fields and fields["Точное время"]:
            try:
                time_str = fields["Точное время"]
                for fmt in ["%H:%M", "%H:%M:%S"]:
                    try:
                        observation["точное_время"] = datetime.strptime(time_str, fmt).time()
                        break
                    except ValueError:
                        continue
            except Exception:
                observation["точное_время"] = None

        if "Ключевые фразы" in fields and fields["Ключевые фразы"]:
            phrases = fields["Ключевые фразы"]

            observation["ключевые_фразы"] = [
                p.strip() for p in phrases.split("—") if p.strip()
            ]

        observations[bird_counter] = observation
        bird_counter += 1

    return observations

def model_settings(user_note):
    system_prompt = """Ты — анализатор заметок пользователя о птицах.
            Твоя задача — на основе предоставленного контекста выбрать ключевые данные: 
            Первое предложение, состоящее из "Название птицы — Название". Если названия нет, то "Название птицы — "
            
            Для каждой птицы новым предложением все слова, связанные со временем (прямое указание времени, например, 18:00 или косвенное, например, час назад). В начале этого предложения всегда "Выделенное время — ", даже если дальше будет пусто.;
            Следующим предложением с началом "Точное время — " выдели точное время, когда видели птицу. Если в тексте указание косвенное, то используй Время сейчас (данное в заметке), например, сейчас 14:42, видел птицу два часа назад - точное время 12:42. 
            Если указано только время суток, поставь любое время в этом промежутке (например, утро - 9:00); 
            
            Для каждой птицы новым предложением все слова, связанные с датой (прямое указание, например, 12 сентября или косвенное, например, позавчера). В начале этого предложения всегда "Выделенная дата — ", даже если дальше будет пусто. 
            Следующим предложением с началом "Точная дата — " выдели точную дату, когда видели птицу. Если в тексте указание косвенное, то используй Дата сейчас (данное в заметке), например, сейчас 23.12.2028, видел птицу позавчера - точная дата 21.12.2028. 
            Если указано только время суток (например, вечером), предполагай что это ближайшее прошедшее, например, если сейчас 12:00, то утром - это сегодня утром, а вечером - это вчера вечером (так как вечер сегодня еще не наступил). Точная дата - самая поздняя из возможных; 
            
            Для каждой птицы новым предложением все слова, связанные с местом: среда (вода, лес), объекты на которых птица (на земле, дерево, под елкой, в воде и другие). В начале этого предложения всегда "Выделенное место — ";
            
            Для каждой птицы напиши два коротких описания без лишних слов: ее внешность (только внешность, если описана, иначе ничего), ее место и поведение (только место и\или поведение,если описаны, иначе ничего). Структура этого предложения всегда "Ключевые фразы — Фраза1 — Фраза2".
            
            Информацию о каждой следующей птице выделяй, добавляя перед началом одну пустую строку.
            
            ИНСТРУКЦИИ:
            1. Используй ТОЛЬКО информацию из предоставленной заметки.
            2. Не выдумывай и не добавляй факты, которых нет в контексте.
            3. Если в контексте нет каких-то данных, не заполняй их
            4. Структурируй ответ четко по указанным правилам.
            5. Не добавляй ничего, кроме запрошенной структуры.
            6. Для каждой описанной птицы анализируй, какие время, даты и места с ней связаны (Точная дата и Точное время обязательны).
            7. У каждой птицы может быть только одна Точная дата и одно Точное время."""

    user_prompt = f"""
           ЗАМЕТКА ПОЛЬЗОВАТЕЛЯ: Дата сейчас: {datetime.today().date()}. Время сейчас: {datetime.today().time()} {user_note}
    
           Проведи анализ и дай ответ, строго следуя инструкциям выше. Отвечай на русском языке."""

    payload = {
        "model": "google/gemini-3.1-flash-lite",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0.3,
        "max_tokens": 700,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }

    return payload

def enhance_answer(user_note: str):
    GEMINI_API_KEY = config.GEMINI_API_KEY

    payload = model_settings(user_note)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=json.dumps(payload),

        )

        result = response.text

        dict_b = parse_bird_observations(result)
        print(dict_b)

        count = -1
        list_to_keep_lists = []
        for v in dict_b.values():
            v["ключевые_фразы"].append(" ".join(x for x in v["ключевые_фразы"]))
            phrases = v["ключевые_фразы"]
            for phrase in phrases:
                list_to_keep = []
                count += 1
                birds = find_bird(phrase)
                bird_list = birds['ids'][0]
                for b in bird_list:
                    list_to_keep.append(b.split("_")[0].strip())
                list_to_keep = list(set(list_to_keep))
                list_to_keep_lists.append(list_to_keep)

        counter = Counter()
        for sublist in list_to_keep_lists:
            counter.update(sublist)

        max_count = max(counter.values()) if counter else 0

        result_birds = [(item, count) for item, count in counter.items() if count == max_count]

        return dict_b, result_birds
    except requests.exceptions.Timeout:
        print("[ERROR] Таймаут запроса к OpenRouter API")
        raise
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Ошибка соединения: {e}")
        raise