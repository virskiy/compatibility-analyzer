from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

def calculate_arcan(day, month, year):
    day_arcan = day if day <= 22 else sum(int(d) for d in str(day))
    
    total = sum(int(d) for d in f"{day}{month}{year}")
    while total > 22:
        total = sum(int(d) for d in str(total))
    destiny_arcan = total
    
    return day_arcan, destiny_arcan

def get_arcan_name(number):
    names = {
        1: "Маг", 2: "Верховная Жрица", 3: "Императрица", 4: "Император",
        5: "Иерофант", 6: "Влюблённые", 7: "Колесница", 8: "Правосудие",
        9: "Отшельник", 10: "Колесо Фортуны", 11: "Сила", 12: "Повешенный",
        13: "Смерть", 14: "Умеренность", 15: "Дьявол", 16: "Башня",
        17: "Звезда", 18: "Луна", 19: "Солнце", 20: "Суд",
        21: "Мир", 22: "Шут"
    }
    return names.get(number, f"Аркан {number}")

def create_system_prompt():
    return """Ты — эксперт по нумерологии Таро (метод 22 арканов). Твоя задача — дать чёткий, практичный и понятный обычному человеку анализ совместимости двух людей по их датам рождения.

Ты получишь даты и уже рассчитанные арканы. Используй их для анализа.

Структура ответа (всегда строго по этому шаблону):

[Она]
Основной характер: (опиши характер, как это проявляется в быту, отношениях, сексе)
Её жизненная задача: (к чему она идёт, чему учится)

[Он]
Основной характер: ...
Его жизненная задача: ...

[Что вас связывает]
Аркан отношений: ... (что вы чувствуете друг к другу, на чём держится связь)
Кармическая задача: ... (зачем вы встретились, какой урок проходите)

[Совместное проживание]
Опиши максимально конкретно: как пойдут быт, деньги, секс, распределение ролей, если они начнут жить вместе. Учти разницу в возрасте, если она есть. Без общих фраз.

[Перспектива]
Прогноз на 1–3 года. Будет ли развитие? Что может разрушить союз? Что удержит?

[Вердикт]
Жирным шрифтом: Стоит пробовать или НЕ стоит.

Важно: 
- Не используй слово «аркан» в ответе, если оно не знакомо людям. Лучше говори «тип характера», «энергия».
- Не пиши «22 аркана», «расчёты», «формулы». Пиши просто и по-человечески.
- Будь честен, жёсток, но без оскорблений."""

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        man = data['man']
        woman = data['woman']
        
        man_day, man_destiny = calculate_arcan(man['day'], man['month'], man['year'])
        woman_day, woman_destiny = calculate_arcan(woman['day'], woman['month'], woman['year'])
        
        relation_arcan = man_day + woman_day
        while relation_arcan > 22:
            relation_arcan = sum(int(d) for d in str(relation_arcan))
        
        karmic_arcan = man_destiny + woman_destiny
        while karmic_arcan > 22:
            karmic_arcan = sum(int(d) for d in str(karmic_arcan))
        
        man_age = datetime.now().year - man['year']
        woman_age = datetime.now().year - woman['year']
        age_diff = abs(man_age - woman_age)
        
        user_prompt = f"""Проанализируй совместимость пары:

Мужчина: {man['day']}.{man['month']}.{man['year']} (возраст {man_age} лет)
Женщина: {woman['day']}.{woman['month']}.{woman['year']} (возраст {woman_age} лет)

Рассчитанные арканы (используй для анализа):
Мужчина - характер: {man_day} ({get_arcan_name(man_day)}), судьба: {man_destiny} ({get_arcan_name(man_destiny)})
Женщина - характер: {woman_day} ({get_arcan_name(woman_day)}), судьба: {woman_destiny} ({get_arcan_name(woman_destiny)})
Аркан отношений: {relation_arcan} ({get_arcan_name(relation_arcan)})
Кармический аркан: {karmic_arcan} ({get_arcan_name(karmic_arcan)})
Разница в возрасте: {age_diff} лет

Дай подробный анализ по шаблону."""
        
        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': create_system_prompt()},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }
        
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        
        if response.status_code != 200:
            return jsonify({'error': f'Ошибка DeepSeek API: {response.text}'}), 500
        
        result = response.json()
        analysis = result['choices'][0]['message']['content']
        
        return jsonify({'analysis': analysis})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)