import logging
import requests
import feedparser
import yfinance as yf
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue

# Diccionarios
SYMBOLS = {
    'btc': 'BTC-USD',
    'eth': 'ETH-USD',
    'bnb': 'BNB-USD',
    'sol': 'SOL-USD'
}
COINGECKO_IDS = {
    'btc': 'bitcoin',
    'eth': 'ethereum',
    'bnb': 'binancecoin',
    'sol': 'solana'
}

# Palabras clave y escala de impacto
CLAVES = {
    "inflación": "Negativo",
    "Fed": "Negativo",
    "tasas de interés": "Negativo",
    "IPC": "Negativo",
    "aranceles": "Negativo",
    "PIB": "Positivo",
    "empleo": "Positivo"
}

# Almacenar chat_id
CHAT_ID_FILE = "chat_id.txt"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    with open(CHAT_ID_FILE, "w") as f:
        f.write(str(chat_id))
    await update.message.reply_text("✅ ¡Bot activo! Usaré este chat para enviarte noticias importantes.")

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
            await update.message.reply_text(f"No hay suficientes datos para {coin.upper()}.")
            return

        ma20 = close.rolling(window=20).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()

        last_price = float(close.iloc[-1])
        last_ma20 = float(ma20.iloc[-1])
        last_ema21 = float(ema21.iloc[-1])

        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={cg_id}"
        response = requests.get(url)
        response.raise_for_status()
        marketcap = response.json()[0]['market_cap']
        marketcap_formatted = f"${marketcap:,.0f}"

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
            f"🏦 Market Cap: {marketcap_formatted}\n\n"
            f"{interpretacion}"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al obtener datos de {coin.upper()}: {e}")

def interpretar_titulo(titulo: str) -> str:
    for palabra, impacto in CLAVES.items():
        if palabra.lower() in titulo.lower():
            return impacto
    return "Neutro"

def extraer_noticias():
    url = "https://finance.yahoo.com/topic/crypto/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    noticias = soup.find_all('h3')

    resultados = []
    for noticia in noticias:
        texto = noticia.get_text()
        link_tag = noticia.find('a')
        if not link_tag:
            continue
        enlace = "https://finance.yahoo.com" + link_tag.get('href')
        impacto = interpretar_titulo(texto)
        if impacto != "Neutro":
            resultados.append((texto, enlace, impacto))
    return resultados

async def verificar_noticias(context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(CHAT_ID_FILE, "r") as f:
            chat_id = int(f.read().strip())
    except:
        return  # No hay chat registrado

    noticias = extraer_noticias()
    for titulo, enlace, impacto in noticias:
        mensaje = f"📰 *Noticia Detectada*\n\n*{titulo}*\n🔗 {enlace}\n📊 Impacto estimado en BTC: *{impacto}*"
        await context.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token("7215806088:AAHsLeDCOIhU89jJTemHQ8XgKLYOYmhXZgM").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("medias", medias))

    job_queue: JobQueue = app.job_queue
    job_queue.run_repeating(verificar_noticias, interval=3600, first=10)

    app.run_polling()
