import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

# TOKEN
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

# MENSAJES
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
    "Puedo mandarte los datos exactos al finalizar tu pedido ✅"
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
    "Canal principal, referencias e información general."
)

PRICES_TEXT = (
    "💵 *LISTA DE PRECIOS OFICIALES*\n\n"
    "• $1,000  →  $6,000 MXN\n"
    "• $2,000  →  $15,000 MXN\n"
    "• $3,000  →  $22,000 MXN\n"
    "• $4,000  →  $30,000 MXN\n"
    "• $5,000  →  $45,000 MXN\n"
)

PAYMENT_DETAILS = (
    "✅ *DATOS DE PAGO*\n\n"
    "*TRANSFERENCIA*\n"
    "`4152314184871096`\n"
    "Banco: **BBVA**\n"
    "Titular: **ELIZABET REYES**\n\n"
    "*DEPÓSITOS*\n"
    "`4815 1631 7306 7847`\n"
)

# ESTADOS
ADDRESS, NAME, PHONE, DENOM, PAYMETHOD = range(5)

PAYMENT_KB = ReplyKeyboardMarkup(
    [["Transferencia", "Depósito"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

logging.basicConfig(level=logging.INFO)

def contains(text: str, kws):
    t = text.lower()
    return any(k in t for k in kws)

def intent_order(t): return contains(t, ["quiero", "pedido", "paquete", "encargar"])
def intent_shipping(t): return contains(t, ["tarda", "llega", "envio"])
def intent_payplaces(t): return contains(t, ["donde pago", "deposito", "transferencia"])
def intent_faq(t): return contains(t, ["frecuentes", "faq"])
def intent_group(t): return contains(t, ["grupo", "canal", "info"])
def intent_prices(t): return contains(t, ["precio", "precios", "cuesta"])

def phone_digits(s): return "".join(ch for ch in s if ch.isdigit())
def phone_valid(d): return len(d) >= 10

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown_v2(WELCOME_TEXT)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Proceso cancelado ✅", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def order_entry(update, context):
    context.user_data.clear()
    await update.message.reply_text("📍 Dirección completa:")
    return ADDRESS

async def ask_name(update, context):
    context.user_data["address"] = update.message.text.strip()
    await update.message.reply_text("👤 Nombre completo:")
    return NAME

async def ask_phone(update, context):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("📱 Teléfono:")
    return PHONE

async def ask_denom(update, context):
    digits = phone_digits(update.message.text)
    if not phone_valid(digits):
        await update.message.reply_text("Número inválido, intenta otra vez:")
        return PHONE
    context.user_data["phone"] = digits
    await update.message.reply_text("💵 ¿Qué denominaciones deseas?")
    return DENOM

async def ask_paymethod(update, context):
    context.user_data["denom"] = update.message.text.strip()
    await update.message.reply_text("💳 Método de pago:", reply_markup=PAYMENT_KB)
    return PAYMETHOD

async def confirm_and_checkout(update, context):
    pm = update.message.text.lower()
    if pm not in ["transferencia", "depósito", "deposito"]:
        await update.message.reply_text("Elige una opción válida:", reply_markup=PAYMENT_KB)
        return PAYMETHOD

    d = context.user_data
    resumen = (
        "✅ *Resumen del pedido*\n\n"
        f"📍 Dirección: {d['address']}\n"
        f"👤 Nombre: {d['name']}\n"
        f"📱 Teléfono: {d['phone']}\n"
        f"💵 Denominaciones: {d['denom']}\n"
        f"💳 Método: {pm.capitalize()}\n"
    )

    await update.message.reply_markdown_v2(resumen)
    await update.message.reply_markdown_v2(PAYMENT_DETAILS)
    context.user_data.clear()
    return ConversationHandler.END

async def router(update, context):
    t = update.message.text.lower()

    if intent_order(t): return await order_entry(update, context)
    if intent_shipping(t): return await update.message.reply_markdown_v2(SHIPPING_TEXT)
    if intent_payplaces(t): return await update.message.reply_markdown_v2(PAY_PLACES_TEXT)
    if intent_faq(t): return await update.message.reply_markdown_v2(FAQ_TEXT)
    if intent_group(t): return await update.message.reply_text(GROUP_TEXT)
    if intent_prices(t): return await update.message.reply_markdown_v2(PRICES_TEXT)

    await update.message.reply_text("No entendí, ¿quieres hacer un pedido?")
    return ConversationHandler.END

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
    app.add_handler(conv)

    print("✅ BOT INICIADO ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
