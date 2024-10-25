class I18N:
    _STRINGS = {
        'bot.default_text': {
            'ru':  """   🎉 Добро пожаловать в Smart Analytics!

Smart Analytics — это ваш персональный помощник в мире криптовалют и фондового рынка. Получайте актуальные данные, анализируйте рынок и принимайте взвешенные решения.

🔍 Исследуйте рынок: Отслеживайте изменения цен, активность торгов и рост активов в реальном времени.

📈 Анализируйте данные: Используйте эксклюзивные аналитические инструменты для глубокого понимания рыночных тенденций.

💼 Подписка: Откройте доступ к расширенным функциям и получайте максимум полезной информации.

Удачи в ваших инвестициях и успешных сделок! 🚀
""",
            'kk': """""",
            'en': """ 🎉 Welcome to Smart Analytics!

Smart Analytics is your personal assistant in the world of cryptocurrencies and the stock market. Get up-to-date data, analyze the market, and make informed decisions.

🔍 Explore the market: Track price changes, trading activity, and asset growth in real time.

📈 Analyze data: Use exclusive analytical tools for a deep understanding of market trends.

💼 Subscription: Unlock access to advanced features and get the most valuable information.

Good luck with your investments and successful deals! 🚀 """

        },
        'bot.error_message': {
            'ru': "",
            'kk': "",
            'en': "Sorry some trouble occurred! Please try again.",
        },
        'bot.success_message': {
            'ru': "",
            'kk': "",
            'en': "You have just get subscriber by ID: {referred_id}!",
        },
        'bot.help_message': {
            'ru': "",
            'kk': "",
            'en': """FAQ: How to Traid"""
        },
        'bot.invited_client_welcome_text': {
            'ru': "🎉Привет, {user_nickname}! ",
            'en': " 🎉Hello, {user_nickname}! "
        },
        'bot.client_welcome_text': {
            'ru': "🎉Привет, {user_nickname}! ",
            'en': " 🎉Hello, {user_nickname}! "
        },
        'bot.confirmation_text': {
            'ru': "Пожалуйста, подождите, пока наш администратор разрешит вам проверить наш продукт!",
            'kk': "",
            'en': "Please wait until our admin will allow you to check our product!",
        },
        "bot.impulse_positive": {
            "ru": "Торговая пара {active_name} дала импульс цены в {percent}% {time_text} 🟢📈",
            "en": "The trading pair {active_name} showed a price impulse of {percent}% {time_text} 🟢📈",
        },
        'bot.trading_pair_header': {
        'ru': "🔔Торговая пара: {ticker_name}🔔\n",
        'en': "🔔Trading Pair: {ticker_name}🔔\n",
        },
        'bot.price_up': {
            'ru': "– Текущая цена: {current_price}$ ({price_change}% за 15 мин.)🟢\n",
            'en': "– Current Price: {current_price}$ ({price_change}% in last 15 mins)🟢\n",
        },
        'bot.price_down': {
            'ru': "– Текущая цена: {current_price}$ ({price_change}% за 15 мин.)🔴\n",
            'en': "– Current Price: {current_price}$ ({price_change}% in last 15 mins)🔴\n",
        },
        'bot.volume_up': {
            'ru': "– Текущий объём торгов: {current_volume}$ ({volume_change}% за 15 мин.)🟢\n",
            'en': "– Current Trading Volume: {current_volume}$ ({volume_change}% in last 15 mins)🟢\n",
        },
        'bot.volume_down': {
            'ru': "– Текущий объём торгов: {current_volume}$ ({volume_change}% за 15 мин.)🔴\n",
            'en': "– Current Trading Volume: {current_volume}$ ({volume_change}% in last 15 mins)🔴\n",
        },
        'bot.top_place': {
            'ru': "– Актив входит в ТОП {top_place} по суточной процентности🔝\n",
            'en': "– Asset ranks in the TOP {top_place} by daily percentage🔝\n",
        },
        'bot.funding_rate': {
            'ru': " – Ставка финансирования: {current_funding_rate}% | 15 мин. назад: {funding_rate_change}%",
            'en': " – Funding Rate: {current_funding_rate}% | 15 mins ago: {funding_rate_change}%",
        },
    }

    def get_string(self, key, lang = 'en') -> str:
        return self._STRINGS.get(key, {}).get(str(lang), f'[INVALID_TRANSLATION:{lang}:{key}]')


i18n = I18N()