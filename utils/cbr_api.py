import requests

def get_usd_rate() -> float:
    """Получает актуальный курс доллара к рублю."""
    try:
        # Делаем запрос к бесплатному API
        response = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
        data = response.json()
        # Достаем значение доллара
        return data['Valute']['USD']['Value']
    except Exception as e:
        print(f"Ошибка получения курса: {e}")
        return 73.00  # Резервный курс на случай падения серверов ЦБ