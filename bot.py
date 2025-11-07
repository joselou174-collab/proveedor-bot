import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

# -------------------------------------------
# TOKEN DE TELEGRAM (Render lo toma del ENV)
# -------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("⚠️ ERROR: Falta TELEGRAM_TOKEN en variables de entorno.")

# -------------------------------------------
# MENSAJES FIJOS
# -------------------------------------------
WELCOME_TEXT = (
    "¡Hola! Somos *Proveedor*, vendemos lo mejor en el mercado. 🚀\n\n"
    "Puedo ayudarte a realizar tu pedido o resolver dudas.\n\n"
    "Ejemplos:\n"
    "• *Quiero el de 1000*\n"
    "• *Quiero un paquete*\n"
    "• *Cómo hago el pedido*\n\n"
    "Preguntas comunes:\n"
    "• *¿Cuánto tarda en llegar?*\n"
    "• *¿Dónde pago?*\n"
    "• *Precios*\n"
)

SHIPPING_TEXT = (
    "📦 *ENVÍOS*\n\n"
    "✅ Estándar GRATIS: 4–6 días.\n"
    "✅ Express 1–2 días: $149 MXN.\n"
)

PAY_PLACES_TEXT = (
    "💳 *MÉTODOS DE PAGO*\n\n"
    "Aceptamos:\n"
    "• Transferencia\n"
    "• Depósitos en OXXO\n"
    "• Depósitos en Farmacia Guadalajara\n"
    "• Tiendas con depósito\n\n"
    "Puedo darte los datos exactos cuando finalices tu pedido ✅"
)

FAQ_TEXT = (
    "📌 *Preguntas Frecuentes*\n\n"
    "• Envío por DHL, FedEx o Estafeta 🚚\n"
    "• Tiempos de entrega: 1–2 días\n"
    "• Envíos discretos (cajas de accesorios o tenis) 👟\n"
)

GROUP_TEXT = (
    "📣 Más información completa aquí:\n"
    "https://t.me/+KGNVqrk7J2VhOTY5"
)

PRICES_TEXT = (
    "💵 *LISTA DE PRECIOS OFICIALES*\n\n"
    "• $1,000  →  $6,000 MXN\n"
    "• $2,000  →  $15,000 MXN\n"
    "• $3,000  →  $22,000 MXN\n"
    "• $4,000  →  $30,000 MXN\n"
    "• $5,000  →  $45,000 MXN\n\n"
    "📣 Pregunta si hay promociones con @El_Proveedor_confiable."
)

PAYMENT_DETAILS = (
    "✅ *DATOS DE PAGO*\n\n"
    "*TRANSFERENCIA*\n"
    "`4152314184871096`\n"
    "Banco: **BBVA**\n"
    "Titular: **ELIZABET REYES**\n\n"
    "*DEPÓSITOS*\n"
    "`4815 1631 7306 7847`\n\n"
    "Cuando pagues, envía tu comprobante aquí o a @El_Proveedor_confiable ✅"
)

# -------------------------------------------
# ESTADOS DE CONVERSACIÓN
# -------------------------------------------
ADDRESS, NAME, PHONE, DENOM, PAYMETHOD = range(5)

PAYMENT_KB = ReplyKeyboardMarkup(
    [["Transferencia", "Depósito"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

# -------------------------------------------
# LOGGING
# -------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------
# INTENTS (DETECCIÓN DE MENSAJES)
# -------------------------------------------
def contains(text, keywords):
    t = text.lower()
    return any(k in t for k in keywords)

def is_order(text):
    return contains(text, [
        "quiero", "pedir", "pedido", "encargo", "ordenar", "comprar"
    ])

def is_shipping(text): return contains(text, ["tarda", "llega", "envío", "entrega"])
def is_payplaces(text): return contains(text, ["donde pago", "deposito", "depósito", "transferencia"])
def is_faq(text): return contains(text, ["preguntas", "faq", "procedimiento"])
def is_group(text): return contains(text, ["grupo", "telegram"])
def is_prices(text): return contains(text, ["precio", "precios", "cuánto"])

# -------------------------------------------
# VALIDACIÓN TELÉFONO
# -------------------------------------------
def digits_only(text): return "".join(c for c in text if c.isdigit())
def is_phone_valid(phone): return len(phone) >= 10

# -------------------------------------------
# COMANDOS
# -------------------------------------------
async def start(update, context):
    await update.message.reply_markdown_v2(WELCOME_TEXT)

async def help_cmd(update, context):
    await update.message.reply_text("Para iniciar un pedido, escribe: *Quiero el de 1000*")

async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text(
        "✅ Proceso cancelado. Escribe *Quiero hacer el pedido* para empezar de nuevo.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# -------------------------------------------
# FLUJO DE PEDIDO
# -------------------------------------------
async def order_entry(update, context):
    context.user_data.clear()
    await update.message.reply_text("1/5 📍 *Dirección completa:*")
    return ADDRESS

async def ask_name(update, context):
    context.user_data["address"] = update.message.text.strip()
    await update.message.reply_text("2/5 🧑 *Nombre de quien recibe:*")
    return NAME

async def ask_phone(update, context):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("3/5 📱 *Teléfono:*")
    return PHONE

async def ask_denom(update, context):
    phone = digits_only(update.message.text)
    if not is_phone_valid(phone):
        await update.message.reply_text("El número es inválido, intenta de nuevo:")
        return PHONE
    context.user_data["phone"] = phone
    await update.message.reply_text("4/5 💵 *Denominaciones que deseas:*")
    return DENOM

async def ask_paymethod(update, context):
    context.user_data["denom"] = update.message.text.strip()
    await update.message.reply_text(
        "5/5 💳 *Método de pago:*",
        reply_markup=PAYMENT_KB
    )
    return PAYMETHOD

async def finish_checkout(update, context):
    pm = update.message.text.lower()
    if pm not in ["transferencia", "depósito", "deposito"]:
        await update.message.reply_text("Selecciona una opción válida:")
        return PAYMETHOD

    d = context.user_data

    resumen = (
        "✅ *Resumen del pedido*\n\n"
        f"📍 Dirección: {d['address']}\n"
        f"👤 Recibe: {d['name']}\n"
        f"📱 Teléfono: {d['phone']}\n"
        f"💵 Denominaciones: {d['denom']}\n"
        f"💳 Método de pago: {pm.capitalize()}\n"
    )

    await update.message.reply_markdown_v2(resumen, reply_markup=ReplyKeyboardRemove())
    await update.message.reply_markdown_v2(PAYMENT_DETAILS)

    context.user_data.clear()
    return ConversationHandler.END

# -------------------------------------------
# ROUTER PRINCIPAL (INTELIGENCIA)
# -------------------------------------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if is_order(text): return await order_entry(update, context)
    if is_shipping(text): return await update.message.reply_markdown_v2(SHIPPING_TEXT)
    if is_payplaces(text): return await update.message.reply_markdown_v2(PAY_PLACES_TEXT)
    if is_faq(text): return await update.message.reply_markdown_v2(FAQ_TEXT)
    if is_group(text): return await update.message.reply_text(GROUP_TEXT)
    if is_prices(text): return await update.message.reply_markdown_v2(PRICES_TEXT)

    await update.message.reply_text("¿Deseas hacer un pedido? Escribe *Quiero el de 1000* ✅")

# -------------------------------------------
# MAIN — INICIA EL BOT
# -------------------------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, router)],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_denom)],
            DENOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_paymethod)],
            PAYMETHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_checkout)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(conv)

    print("✅ BOT PROVEEDOR INICIADO ✅")
    app.run_polling(drop_pending_updates=True)

# -------------------------------------------
# START
# -------------------------------------------
if __name__ == "__main__":
    main()
