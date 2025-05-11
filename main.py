import logging
import yfinance as yf
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configura tu token de Telegram
TELEGRAM_TOKEN = '7215806088:AAHsLeDCOIhU89jJTemHQ8XgKLYOYmhXZgM'

# Diccionario con símbolos y CoinGecko ids
CRIPTO_INFO = {
    'btc': {'ticker': 'BTC-USD', 'id': 'bitcoin'},
    'eth': {'ticker': 'ETH-USD', 'id': 'ethereum'},
    'sol': {'ticker': 'SOL-USD', 'id': 'solana'},
    'bnb': {'ticker': 'BNB-USD', 'id': 'binancecoin'}
}

# Función para obtener medias móviles
def obtener_medias(ticker):
    data = yf.download(ticker, period='1mo', interval='1d')
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['EMA21'] = data['Close'].ewm(span=21, adjust=False).mean()
    ultimo = data.iloc[-1]
    return round(ultimo['Close'], 2), round(ultimo['MA20'], 2), round(ultimo['EMA21'], 2)

# Función para obtener market cap desde CoinGecko
def obtener_marketcap(cripto_id):
    url = f"https://api.coingecko.com/api/v3/coins/{cripto_id}"
    response = requests.get(url)
    data = response.json()
    market_cap = data['market_data']['market_cap']['usd']
    return f"${market_cap:,.0f}"

# Interpretación MA20 vs EMA21
def interpretar_ma_ema(ma20, ema21, precio):
    if ema21 > ma20 and precio > ema21:
        return "📈 *Señal Alcista*: EMA 21 está sobre MA 20 y el precio por encima de ambas."
    elif ema21 < ma20 and precio < ema21:
        return "📉 *Señal Bajista*: EMA 21 está bajo MA 20 y el precio por debajo de ambas."
    else:
        return "⚖️ *Neutro*: Las medias están cruzándose o el precio aún no confirma."

# Comando /medias btc
async def medias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Usa el comando así: /medias btc, eth, sol o bnb.")
        return

    cripto = context.args[0].lower()
    if cripto not in CRIPTO_INFO:
        await update.message.reply_text("❗ Cripto no válida. Usa: btc, eth, sol o bnb.")
        return

    info = CRIPTO_INFO[cripto]
    try:
        precio, ma20, ema21 = obtener_medias(info['ticker'])
        marketcap = obtener_marketcap(info['id'])
        interpretacion = interpretar_ma_ema(ma20, ema21, precio)
        mensaje = (
            f"📊 *{cripto.upper()}*\n"
            f"Precio: ${precio}\n"
            f"MA 20: ${ma20}\n"
            f"EMA 21: ${ema21}\n"
            f"Market Cap: {marketcap}\n\n"
            f"{interpretacion}"
        )
    except Exception as e:
        mensaje = f"⚠️ Error al obtener datos de {cripto.upper()}"

    await update.message.reply_text(mensaje, parse_mode='Markdown')

# Iniciar el bot
def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("medias", medias))
    print("Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
