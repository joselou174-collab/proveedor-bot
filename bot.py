import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

# -------------------------------------------
# VARIABLES DE ENTORNO
# -------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

# -------------------------------------------
# MENSAJES
# -------------------------------------------
WELCOME_TEXT = (
    "¡Hola! Somos *Proveedor*, vendemos lo mejor en el mercado. 🚀\n\n"
    "Puedo ayudarte a realizar tu pedido o resolver dudas sobre envíos, precios y pagos.\n\n"
    "Escribe por ejemplo:\n"
    "• *Quiero el de 1000*\n"
    "• *Quiero un paquete*\n"
    "• *Cómo hago el pedido*\n\n"
    "O pregunta:\n"
    "• *¿Cuánto tarda en llegar?*\n"
    "• *¿Dónde pago?*\n"
    "• *Precios*\n"
)

SHIPPING_TEXT = (
    "📦 *TIEMPOS DE ENVÍO*\n\n"
    "✅ Envío estándar: **GRATIS** (4 a 6 días)\n"
    "✅ Envío Express: *1 a 2 días* — **$149 MXN**\n"
)

PAY_PLACES_TEXT = (
    "💳 *MÉTODOS DE PAGO*\n\n"
    "Aceptamos:\n"
    "• Transferencia bancaria\n"
    "• Depósitos en OXXO\n"
    "• Depósitos en Farmacia Guadalajara\n"
    "• Cualquier tienda que haga depósitos\n\n"
    "Si eliges transferencia, te mando los datos al final del pedido ✅"
)

FAQ_TEXT = (
    "📌 *Preguntas Frecuentes*\n\n"
    "• Envío por DHL, FedEx o Estafeta 🚚\n"
    "• Entregas normalmente en *1–2 días*\n"
    "• Paquetes discretos: cajas de accesorios o tenis 👟\n\n"
    "¿Deseas ordenar ahora?"
)

GROUP_TEXT = (
    "📣 *Más información detallada aquí:*\n"
    "https://t.me/+KGNVqrk7J2VhOTY5\n\n"
    "Canal principal, calidades, referencias e información general."
)

PRICES_TEXT = (
    "💵 *LISTA DE PRECIOS OFICIALES*\n\n"
    "• $1,000  →  $6,000 MXN\n"
    "• $2,000  →  $15,000 MXN\n"
    "• $3,000  →  $22,000 MXN\n"
    "• $4,000  →  $30,000 MXN\n"
    "• $5,000  →  $45,000 MXN\n\n"
    "📣 *Promociones:* pregunta si hay ofertas activas con @El_Proveedor_confiable\n"
    "o revisa el canal de WhatsApp 📲.\n\n"
    "¿Quieres hacer tu pedido?"
)

PAYMENT_DETAILS = (
    "✅ *DATOS DE PAGO*\n\n"
    "*TRANSFERENCIA*\n"
    "`4152314184871096`\n"
    "Banco: **BBVA**\n"
    "Titular: **ELIZABET REYES**\n\n"
    "*DEPÓSITOS*\n"
    "`4815 1631 7306 7847`\n\n"
    "Cuando realices el pago, envía el comprobante aquí o a @El_Proveedor_confiable ✅"
)

OWNER_HANDLE = "@El_Proveedor_confiable"


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
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# -------------------------------------------
# INTENTS
# -------------------------------------------
def contains(text: str, kws):
    t = text.lower()
    return any(k in t for k in kws)

def intent_order(text):
    return contains(text, [
        "como encargo", "cómo encargo",
        "como hago el pedido", "cómo hago el pedido",
        "quiero el de", "quiero un paquete",
        "hacer pedido", "encargar", "ordenar", "comprar"
    ])

def intent_shipping(text):
    return contains(text, [
        "cuanto tarda", "cuánto tarda",
        "tarda en llegar", "donde lo mandan",
        "envio", "envío", "entrega"
    ])

def intent_payplaces(text):
    return contains(text, [
        "donde pago", "dónde pago",
        "donde transfiero", "dónde transfiero",
        "donde deposito", "dónde deposito",
        "como pago"
    ])

def intent_faq(text):
    return contains(text, [
        "preguntas frecuentes", "faq",
        "procedimiento", "cómo funciona"
    ])

def intent_group(text):
    return contains(text, [
        "grupo", "telegram", "más información", "mas informacion"
    ])

def intent_prices(text):
    return contains(text, [
        "precio", "precios",
        "cuánto cuesta", "cuanto cuesta",
        "cuánto vale", "cuanto vale",
        "cuanto cobran", "cuánto cobran",
        "lista de precios", "promo", "promoción", "promociones"
    ])

# -------------------------------------------
# VALIDACIÓN TELÉFONO
# -------------------------------------------
def phone_digits(s: str):
    return "".join(ch for ch in s if ch.isdigit())

def phone_valid(d: str):
    return len(d) >= 10

# -------------------------------------------
# COMANDOS
# -------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown_v2(WELCOME_TEXT)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Escribe *Quiero el de 1000* para iniciar tu pedido.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "✅ Proceso cancelado. Escribe *Quiero hacer el pedido* para comenzar de nuevo.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# -------------------------------------------
# FLUJO DE PEDIDO
# -------------------------------------------
async def order_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("1/5 📍 *Dirección completa de envío:*")
    return ADDRESS

async def ask_name(update, context):
    address = update.message.text.strip()
    if len(address) < 4:
        await update.message.reply_text("La dirección parece incompleta, escríbela otra vez:")
        return ADDRESS

    context.user_data["address"] = address
    await update.message.reply_text("2/5 🧑 *Nombre completo de quien recibe:*")
    return NAME

async def ask_phone(update, context):
    name = update.message.text.strip()
    if len(name.split()) < 2:
        await update.message.reply_text("Por favor escribe el *nombre completo*:")
        return NAME

    context.user_data["name"] = name
    await update.message.reply_text("3/5 📱 *Número de teléfono:*")
    return PHONE

async def ask_denom(update, context):
    raw = update.message.text.strip()
    digits = phone_digits(raw)

    if not phone_valid(digits):
        await update.message.reply_text("El número parece inválido, escribe uno correcto:")
        return PHONE

    context.user_data["phone"] = digits
    await update.message.reply_text("4/5 💵 *¿Qué denominaciones deseas? (ej. 1000, paquete, etc.)*")
    return DENOM

async def ask_paymethod(update, context):
    denom = update.message.text.strip()

    if not denom:
        await update.message.reply_text("Indica una denominación válida:")
        return DENOM

    context.user_data["denom"] = denom
    await update.message.reply_text("5/5 💳 *Elige tu método de pago:*", reply_markup=PAYMENT_KB)
    return PAYMETHOD

async def confirm_and_checkout(update, context):
    method = update.message.text.lower()

    if method not in ["transferencia", "depósito", "deposito"]:
        await update.message.reply_text("Selecciona una opción válida:", reply_markup=PAYMENT_KB)
        return PAYMETHOD

    method_clean = "Depósito" if "dep" in method else "Transferencia"

    d = context.user_data
    resumen = (
        "✅ *Resumen del pedido*\n\n"
        f"📍 Dirección: {d['address']}\n"
        f"👤 Recibe: {d['name']}\n"
        f"📱 Teléfono: {d['phone']}\n"
        f"💵 Denominaciones: {d['denom']}\n"
        f"💳 Método de pago: {method_clean}\n"
    )

    await update.message.reply_markdown_v2(resumen, reply_markup=ReplyKeyboardRemove())
    await update.message.reply_markdown_v2(PAYMENT_DETAILS)

    context.user_data.clear()
    return ConversationHandler.END

# -------------------------------------------
# ROUTER PRINCIPAL
# -------------------------------------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if intent_order(text):
        return await order_entry(update, context)

    if intent_shipping(text):
        await update.message.reply_markdown_v2(SHIPPING_TEXT)
        return ConversationHandler.END

    if intent_payplaces(text):
        await update.message.reply_markdown_v2(PAY_PLACES_TEXT)
        return ConversationHandler.END

    if intent_faq(text):
        await update.message.reply_markdown_v2(FAQ_TEXT)
        return ConversationHandler.END

    if intent_group(text):
        await update.message.reply_text(GROUP_TEXT, disable_web_page_preview=True)
        return ConversationHandler.END

    if intent_prices(text):
        await update.message.reply_markdown_v2(PRICES_TEXT)
        return ConversationHandler.END

    await update.message.reply_text(
        "¿Deseas hacer un pedido? Escribe: *Quiero el de 1000*.\n"
        "También respondo: *¿Cuánto tarda en llegar?*, *¿Dónde pago?*, *Precios*"
    )
    return ConversationHandler.END

# -------------------------------------------
# MAIN
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
            PAYMETHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_and_checkout)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(conv)

    print("✅ BOT PROVEEDOR INICIADO — LISTO PARA USAR")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
