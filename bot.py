import os
import logging
from typing import Final

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# --------------------------------------------------------------------
# KEEP ALIVE (opcional para Replit). Si no usas keep_alive.py, comenta estas 2 líneas.
# --------------------------------------------------------------------
try:
    from keep_alive import keep_alive  # Debe existir keep_alive.py con función keep_alive()
    keep_alive()
except Exception:
    pass

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
TELEGRAM_TOKEN: Final[str] = os.getenv("TELEGRAM_TOKEN", "").strip()
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("proveedor-bot")

# --------------------------------------------------------------------
# TEXTOS
# --------------------------------------------------------------------
WELCOME_TEXT = (
    "✅ *Bot Proveedor activo*\n\n"
    "¡Hola! Somos *Proveedor*, vendemos lo mejor del mercado. 🚀\n"
    "Puedo ayudarte a *hacer tu pedido* o resolver dudas sobre *envíos, precios y pagos*.\n\n"
    "Escribe por ejemplo:\n"
    "• *Quiero el de 1000*\n"
    "• *Quiero un paquete*\n"
    "• *¿Cómo hago el pedido?*\n\n"
    "O pregunta:\n"
    "• *¿Cuánto tarda en llegar?*\n"
    "• *¿Dónde pago?*\n"
    "• *Precios*"
)

SHIPPING_TEXT = (
    "📦 *TIEMPOS DE ENVÍO*\n\n"
    "• Envío *estándar*: **GRATIS** (4–6 días)\n"
    "• Envío *express*: *1–2 días* — **$149 MXN**\n"
    "• Paquetes discretos (cajas de accesorios o tenis) 🚚"
)

PAY_PLACES_TEXT = (
    "💳 *MÉTODOS DE PAGO*\n\n"
    "Aceptamos:\n"
    "• Transferencia bancaria\n"
    "• Depósitos en OXXO\n"
    "• Depósitos en Farmacia Guadalajara\n"
    "• Y tiendas que acepten depósitos\n\n"
    "Al finalizar tu pedido te mandamos los *datos exactos* ✅"
)

FAQ_TEXT = (
    "📌 *Preguntas Frecuentes*\n\n"
    "• Mensajería: DHL, FedEx o Estafeta 🚚\n"
    "• Entregas típicas en *1–2 días* (express)\n"
    "• Paquetes discretos 👟\n"
    "• Soporte por Telegram y WhatsApp\n\n"
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
    "📣 *Promociones:* pregunta si hay ofertas activas con *@El_Proveedor_confiable*\n"
    "o revisa el canal de *WhatsApp* 📲.\n\n"
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
    "Cuando realices el pago, envía el *comprobante* aquí o a *@El_Proveedor_confiable* ✅"
)

FALLBACK_TEXT = (
    "¿Deseas hacer un pedido? Escribe: *Quiero el de 1000*.\n"
    "También respondo: *¿Cuánto tarda en llegar?*, *¿Dónde pago?*, *Precios*"
)

# --------------------------------------------------------------------
# INTENTS / MATCHERS
# --------------------------------------------------------------------
def contains(text: str, kws) -> bool:
    t = (text or "").lower()
    return any(k in t for k in kws)

def intent_order(t: str) -> bool:
    return contains(t, [
        "como encargo", "cómo encargo",
        "como hago el pedido", "cómo hago el pedido",
        "quiero el de", "quiero un paquete",
        "hacer pedido", "encargar", "ordenar", "comprar"
    ])

def intent_shipping(t: str) -> bool:
    return contains(t, ["cuanto tarda", "tarda en llegar", "envío", "envio", "entrega"])

def intent_payplaces(t: str) -> bool:
    return contains(t, ["donde pago", "transfiero", "deposito", "depósito", "cómo pago"])

def intent_faq(t: str) -> bool:
    return contains(t, ["preguntas frecuentes", "faq", "procedimiento", "cómo funciona"])

def intent_group(t: str) -> bool:
    return contains(t, ["grupo", "telegram", "más info", "información", "informacion"])

def intent_prices(t: str) -> bool:
    return contains(t, [
        "precio", "precios", "cuánto cuesta", "cuanto cuesta",
        "cuánto vale", "cuanto vale", "lista de precios",
        "promo", "promoción", "promociones"
    ])

# --------------------------------------------------------------------
# VALIDACIÓN TELÉFONO
# --------------------------------------------------------------------
def phone_digits(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())

def phone_valid(d: str) -> bool:
    return len(d) >= 10

# --------------------------------------------------------------------
# ESTADOS CONVERSACIÓN
# --------------------------------------------------------------------
ADDRESS, NAME, PHONE, DENOM, PAYMETHOD = range(5)

PAYMENT_KB = ReplyKeyboardMarkup(
    [["Transferencia", "Depósito"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

# --------------------------------------------------------------------
# COMANDOS
# --------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_markdown_v2(WELCOME_TEXT)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_markdown_v2("Para iniciar un pedido escribe: *Quiero el de 1000*")

async def prices_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_markdown_v2(PRICES_TEXT)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "✅ Proceso cancelado. Escribe *Quiero hacer el pedido* para comenzar de nuevo.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# --------------------------------------------------------------------
# FLUJO DE PEDIDO
# --------------------------------------------------------------------
async def order_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_markdown_v2("1/5 📍 *Dirección completa de envío:*")
    return ADDRESS

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    addr = (update.message.text or "").strip()
    context.user_data["address"] = addr
    await update.message.reply_markdown_v2("2/5 🧑 *Nombre completo de quien recibe:*")
    return NAME

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    context.user_data["name"] = name
    await update.message.reply_markdown_v2("3/5 📱 *Número de teléfono:*")
    return PHONE

async def ask_denom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_raw = (update.message.text or "").strip()
    digits = phone_digits(phone_raw)

    if not phone_valid(digits):
        await update.message.reply_text("Número inválido, intenta de nuevo (mínimo 10 dígitos):")
        return PHONE

    context.user_data["phone"] = digits
    await update.message.reply_markdown_v2("4/5 💵 *¿Qué denominaciones deseas?*")
    return DENOM

async def ask_paymethod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    denom = (update.message.text or "").strip()
    context.user_data["denom"] = denom

    await update.message.reply_markdown_v2("5/5 💳 *Elige tu método de pago:*", reply_markup=PAYMENT_KB)
    return PAYMETHOD

async def confirm_and_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pm = (update.message.text or "").lower().strip()

    if pm not in ["transferencia", "depósito", "deposito"]:
        await update.message.reply_text("Selecciona una opción válida:", reply_markup=PAYMENT_KB)
        return PAYMETHOD

    method_clean = "Depósito" if "dep" in pm else "Transferencia"

    d = context.user_data
    resumen = (
        "✅ *Resumen del pedido*\n\n"
        f"📍 Dirección: {d.get('address','')}\n"
        f"👤 Recibe: {d.get('name','')}\n"
        f"📱 Teléfono: {d.get('phone','')}\n"
        f"💵 Denominaciones: {d.get('denom','')}\n"
        f"💳 Método de pago: {method_clean}\n"
    )

    await update.message.reply_markdown_v2(resumen, reply_markup=ReplyKeyboardRemove())
    await update.message.reply_markdown_v2(PAYMENT_DETAILS)

    context.user_data.clear()
    return ConversationHandler.END

# --------------------------------------------------------------------
# ROUTER (texto libre)
# --------------------------------------------------------------------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = (update.message.text or "").lower().strip()

    if intent_order(t):
        return await order_entry(update, context)

    if intent_shipping(t):
        await update.message.reply_markdown_v2(SHIPPING_TEXT)
        return ConversationHandler.END

    if intent_payplaces(t):
        await update.message.reply_markdown_v2(PAY_PLACES_TEXT)
        return ConversationHandler.END

    if intent_faq(t):
        await update.message.reply_markdown_v2(FAQ_TEXT)
        return ConversationHandler.END

    if intent_group(t):
        await update.message.reply_text(GROUP_TEXT, disable_web_page_preview=True)
        return ConversationHandler.END

    if intent_prices(t):
        await update.message.reply_markdown_v2(PRICES_TEXT)
        return ConversationHandler.END

    await update.message.reply_markdown_v2(FALLBACK_TEXT)
    return ConversationHandler.END

# --------------------------------------------------------------------
# ERROR HANDLER
# --------------------------------------------------------------------
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Excepción no controlada", exc_info=context.error)

# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------
def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, router)],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_denom)],
            DENOM:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_paymethod)],
            PAYMETHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_and_checkout)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("prices", prices_cmd))
    app.add_handler(conv)

    app.add_error_handler(on_error)

    print("✅ BOT PROVEEDOR INICIADO — LISTO PARA USAR ✅")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
