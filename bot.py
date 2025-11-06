
import os
import logging
from typing import Dict
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

WELCOME_TEXT = (
    "¡Hola! Somos *El Proveedor Confiable*, vendemos lo mejor en el mercado. \n\n"
    "Puedo ayudarte a realizar tu pedido o resolver dudas sobre envíos y pagos.\n"
    "Escribe: *Quiero el de 1000*, *Quiero un paquete*, *Cómo hago el pedido*, o *Como encargo* para comenzar.\n"
    "También puedo responder: *¿Cuánto tarda en llegar?*, *¿Dónde pago?*, *Más información*, etc."
)
SHIPPING_TEXT = (
    "Envío estándar: **GRATIS**, tarda de *4 a 6 días*.\n"
    "Envío *Express*: tarda *1 a 2 días* con costo extra de **$149 MXN**."
)
PAY_PLACES_TEXT = (
    "Aceptamos **transferencia** y **depósitos en efectivo**.\n"
    "Puedes depositar en **OXXO**, **Farmacia Guadalajara** y otras tiendas con depósitos.\n"
    "Si eliges *transferencia*, te comparto los datos al finalizar el pedido."
)
FAQ_TEXT = (
    "Procedimiento de compra:\n"
    "• Envío por **DHL, FedEx o Estafeta** 🚚\n"
    "• Paquetes llegan en **1–2 días** (según ubicación)\n"
    "• Discretos: cajas de **accesorios** o **tenis** 👟\n\n"
    "¿Deseas crear tu pedido ahora?"
)
GROUP_TEXT = (
    "Más información en el grupo: https://t.me/+KGNVqrk7J2VhOTY5\n"
    "Ahí verás canal principal, calidades, referencias e información en general."
)
PAYMENT_DETAILS = (
    "*Para transferencias*\n"
    "`4152314184871096`\n"
    "Banco **BBVA**\n"
    "**ELIZABET REYES**\n\n"
    "*Para depósitos*\n"
    "`4815 1631 7306 7847`\n\n"
    "Cuando hagas el pago, envía el comprobante **aquí** o a **@El_Proveedor_confiable** "
    "para la garantía y procedemos con el pedido."
)
OWNER_HANDLE = "@El_Proveedor_confiable"

ADDRESS, NAME, PHONE, DENOM, PAYMETHOD = range(5)
PAYMENT_KB = ReplyKeyboardMarkup([["Transferencia", "Depósito"]], one_time_keyboard=True, resize_keyboard=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def contains(text: str, kws):
    t = text.lower()
    return any(k in t for k in kws)

def intent_order(text: str): 
    return contains(text, ["como encargo", "cómo encargo", "como hago el pedido", "cómo hago el pedido",
                           "quiero el de 1000", "quiero un paquete", "quiero el de mil", "quiero comprar",
                           "hacer pedido", "hacer el pedido", "quiero ordenar", "encargar"])

def intent_shipping(text: str):
    return contains(text, ["cuantos dias tarda", "cuánto tarda", "cuanto tarda", "donde lo mandan", "dónde lo mandan",
                           "tarda en llegar", "envio", "envío", "entrega"])

def intent_payplaces(text: str):
    return contains(text, ["donde pago", "dónde pago", "donde transfiero", "dónde transfiero",
                           "donde deposito", "dónde deposito", "como pago", "cómo pago", "metodo de pago", "método de pago"])

def intent_faq(text: str):
    return contains(text, ["preguntas frecuentes", "faq", "procedimiento", "como funciona", "cómo funciona"])

def intent_group(text: str):
    return contains(text, ["grupo de telegram", "más información", "mas informacion", "ver grupo", "canal principal"])

def phone_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def phone_valid(d: str) -> bool:
    return len(d) >= 10

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown_v2(WELCOME_TEXT)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Escribe 'Quiero el de 1000' para iniciar el pedido, o pregunta sobre envíos y pagos.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Proceso cancelado. Escribe 'Quiero hacer el pedido' para empezar de nuevo.",
                                    reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ---- Conversación guiada ----
async def order_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Perfecto, vamos a crear tu pedido.\n1/5 Dirección completa de envío:")
    return ADDRESS

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = (update.message.text or "").strip()
    if len(address) < 5:
        await update.message.reply_text("La dirección parece corta. ¿Puedes escribirla completa?")
        return ADDRESS
    context.user_data["address"] = address
    await update.message.reply_text("2/5 Nombre completo de quien recibe:")
    return NAME

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    if len(name.split()) < 2:
        await update.message.reply_text("Por favor escribe el *nombre completo* de quien recibe.")
        return NAME
    context.user_data["name"] = name
    await update.message.reply_text("3/5 Número de teléfono de contacto:")
    return PHONE

async def ask_denom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = (update.message.text or "").strip()
    digits = phone_digits(raw)
    if not phone_valid(digits):
        await update.message.reply_text("El teléfono parece inválido. Escribe uno de al menos 10 dígitos.")
        return PHONE
    context.user_data["phone"] = digits
    await update.message.reply_text("4/5 ¿Qué *denominaciones* deseas? (ej. '1000', 'paquete')")
    return DENOM

async def ask_paymethod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    denom = (update.message.text or "").strip()
    if len(denom) < 2:
        await update.message.reply_text("Indica una denominación válida (ej. '1000', 'paquete').")
        return DENOM
    context.user_data["denom"] = denom
    await update.message.reply_text("5/5 ¿Método de pago? Elige una opción:", reply_markup=PAYMENT_KB)
    return PAYMETHOD

async def confirm_and_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    method = (update.message.text or "").strip().lower()
    if method not in ["transferencia", "depósito", "deposito"]:
        await update.message.reply_text("Elige *Transferencia* o *Depósito*.", reply_markup=PAYMENT_KB)
        return PAYMETHOD
    context.user_data["paymethod"] = "Depósito" if "dep" in method else "Transferencia"

    d = context.user_data
    resumen = (
        "✅ *Resumen del pedido*\n"
        f"• Dirección: {d.get('address')}\n"
        f"• Recibe: {d.get('name')}\n"
        f"• Teléfono: {d.get('phone')}\n"
        f"• Denominaciones: {d.get('denom')}\n"
        f"• Método de pago: {d.get('paymethod')}"
    )
    await update.message.reply_markdown_v2(resumen, reply_markup=ReplyKeyboardRemove())
    await update.message.reply_markdown_v2(PAYMENT_DETAILS)
    await update.message.reply_text(
        f"Cuando tengas el comprobante, envíalo aquí o a {OWNER_HANDLE}. ¡Gracias por tu compra!"
    )
    context.user_data.clear()
    return ConversationHandler.END

# ---- Router de intents ----
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").lower().strip()
    if intent_order(text):
        return await order_entry(update, context)
    if intent_shipping(text):
        await update.message.reply_markdown_v2(SHIPPING_TEXT); return ConversationHandler.END
    if intent_payplaces(text):
        await update.message.reply_markdown_v2(PAY_PLACES_TEXT); return ConversationHandler.END
    if intent_faq(text):
        await update.message.reply_markdown_v2(FAQ_TEXT); return ConversationHandler.END
    if intent_group(text):
        await update.message.reply_text(GROUP_TEXT, disable_web_page_preview=True); return ConversationHandler.END

    await update.message.reply_text(
        "¿Deseas hacer un pedido? Escribe: *Quiero el de 1000* o *Cómo hago el pedido*. "
        "También respondo *¿cuánto tarda en llegar?* y *¿dónde pago?*"
    )
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
        allow_reentry=True,
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(conv)
    print("BOT Proveedor (Opción A) corriendo ✅")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
