import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf
import requests

# CoinGecko mapping
COINGECKO_IDS = {
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'bnb': 'binancecoin',
    'sol': 'solana'
}

SYMBOLS = {
    'btc': 'BTC-USD',
    'eth': 'ETH-USD',
    'bnb': 'BNB-USD',
    'sol': 'SOL-USD'
}

# Comando /medias
async def medias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usa el comando así: /medias btc")
        return

    coin = context.args[0].lower()

    if coin not in SYMBOLS:
        await update.message.reply_text("Criptomoneda no válida. Usa btc, eth, sol o bnb.")
        return

    symbol = SYMBOLS[coin]
    cg_id = COINGECKO_IDS[coin]

    try:
        data = yf.download(symbol, period='1mo', interval='1d')
        close = data['Close'].dropna()

        if len(close) < 21:
            await update.message.reply_text(f"No hay suficientes datos para calcular medias de {coin.upper()}.")
            return

        ma20 = close.rolling(window=20).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()

        last_price = close.iloc[-1]
        last_ma20 = ma20.iloc[-1]
        last_ema21 = ema21.iloc[-1]

        # CoinGecko MarketCap
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={cg_id}"
        response = requests.get(url)
        response.raise_for_status()
        marketcap = response.json()[0]['market_cap']
        marketcap = f"${marketcap:,.0f}"

        # Interpretación simple
        if last_price > last_ma20 and last_price > last_ema21:
            interpretacion = "📈 *Tendencia Alcista*: El precio está por encima de MA20 y EMA21."
        elif last_price < last_ma20 and last_price < last_ema21:
            interpretacion = "📉 *Tendencia Bajista*: El precio está por debajo de MA20 y EMA21."
        else:
            interpretacion = "⚖️ *Zona de indecisión*: El precio está entre las medias, cuidado."

        msg = (
            f"📊 *Análisis de {coin.upper()}*\n\n"
            f"💰 Precio actual: ${last_price:,.2f}\n"
            f"📈 MA20: ${last_ma20:,.2f}\n"
            f"📉 EMA21: ${last_ema21:,.2f}\n"
            f"🏦 Market Cap: {marketcap}\n\n"
            f"{interpretacion}"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al obtener datos de {coin.upper()}: {e}")

# Iniciar el bot
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token("7215806088:AAHsLeDCOIhU89jJTemHQ8XgKLYOYmhXZgM").build()
    app.add_handler(CommandHandler("medias", medias))
    app.run_polling()
