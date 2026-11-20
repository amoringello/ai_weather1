def suggest_clothing(weather: dict) -> list:
    temp = weather['temperature_c']
    feels_like = weather['feels_like_c']
    desc = weather['description'].lower()
    humidity = weather.get('humidity', 50)
    wind = weather.get('wind_speed_ms', 0)

    recommendations = []

    if temp < 0:
        recommendations.append('🧥 Heavy winter coat / down jacket')
        recommendations.append('🧣 Thick scarf & thermal underwear')
        recommendations.append('👖 Insulated pants')
    elif temp < 10:
        recommendations.append('🧥 Warm coat or heavy jacket')
        recommendations.append('🧣 Scarf recommended')
        recommendations.append('👖 Long pants / jeans')
    elif temp < 20:
        recommendations.append('🧥 Light jacket or sweater')
        recommendations.append('👖 Long pants recommended')
    else:
        recommendations.append('👕 T-shirt or light top')

    if any(w in desc for w in ['rain', 'drizzle', 'snow', 'shower']):
        recommendations.append('☂️ Umbrella or raincoat essential')
        if temp < 5:
            recommendations.append('🥾 Waterproof boots')
        else:
            recommendations.append('👞 Water-resistant shoes')

    if wind > 5:
        recommendations.append('💨 Windbreaker or wind-resistant outer layer')

    if humidity > 80:
        recommendations.append('💧 Choose breathable, moisture-wicking fabrics')

    if feels_like < temp - 5:
        recommendations.append('🧊 Wind chill makes it feel colder — add layers')

    if any(w in desc for w in ['clear', 'sunny', 'cloudless']):
        recommendations.append('🕶️ Sunglasses & sunscreen recommended')

    if temp > 32:
        recommendations.append('☀️ Stay hydrated, wear loose light-colored clothing')

    return recommendations


def format_clothing_suggestions(suggestions: list) -> str:
    body = chr(10).join(f'   • {item}' for item in suggestions)
    return f'👔 Clothing Suggestions:' + chr(10) + body


if __name__ == '__main__':
    sample_weather = {
        'temperature_c': 8, 'feels_like_c': 4, 'description': 'Rainy',
        'humidity': 90, 'wind_speed_ms': 7,
    }
    recs = suggest_clothing(sample_weather)
    print(format_clothing_suggestions(recs))
