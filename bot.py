import os
import ast
import operator as op

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)


# =========================
# Diamond Calculator
# =========================

PRICE, PERCENT = range(2)


async def diamond_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 Diamond Price Calculator\n\n"
        "မူရင်းဈေးကို ထည့်ပေးပါ။\n"
        "ဥပမာ - 100000"
    )

    return PRICE


async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = float(update.message.text.replace(",", "").strip())

        if price <= 0:
            raise ValueError

        context.user_data["diamond_price"] = price

        await update.message.reply_text(
            "📈 ဘယ်နှစ် % တင်မလဲ?\n"
            "ဥပမာ - 15"
        )

        return PERCENT

    except ValueError:
        await update.message.reply_text(
            "❌ ဈေးနှုန်းမမှန်ပါ။\n"
            "ဥပမာ - 100000"
        )

        return PRICE


async def get_percent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        percent = float(update.message.text.replace("%", "").strip())

        if percent < 0:
            raise ValueError

        price = context.user_data["diamond_price"]

        increase = price * percent / 100
        final_price = price + increase

        await update.message.reply_text(
            f"💎 မူရင်းဈေး = {price:,.0f} Ks\n"
            f"📈 တင်မည့် % = {percent:g}%\n"
            f"➕ တိုးဈေး = {increase:,.0f} Ks\n\n"
            f"💰 ရောင်းဈေး = {final_price:,.0f} Ks"
        )

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ % မမှန်ပါ။\n"
            "ဥပမာ - 15"
        )

        return PERCENT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Diamond တွက်ချက်မှု ပယ်ဖျက်လိုက်ပါပြီ။"
    )

    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 မင်္ဂလာပါ!\n\n"
        "💎 Diamond ဈေးတွက်ရန်\n"
        "/diamond ကိုနှိပ်ပါ။\n\n"
        "🧮 Math တွက်ရန်လည်း ရပါတယ်။"
    )


# =========================
# Safe Math Calculator
# =========================

OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def safe_calculate(expression):

    expression = (
        expression
        .replace("×", "*")
        .replace("÷", "/")
        .replace("^", "**")
    )

    tree = ast.parse(expression, mode="eval")

    def calculate_node(node):

        if isinstance(node, ast.Expression):
            return calculate_node(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value

            raise ValueError

        if isinstance(node, ast.BinOp):

            operator = OPERATORS.get(type(node.op))

            if operator is None:
                raise ValueError

            left = calculate_node(node.left)
            right = calculate_node(node.right)

            return operator(left, right)

        if isinstance(node, ast.UnaryOp):

            operator = OPERATORS.get(type(node.op))

            if operator is None:
                raise ValueError

            return operator(calculate_node(node.operand))

        raise ValueError

    return calculate_node(tree)


async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    try:

        result = safe_calculate(text)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        await update.message.reply_text(
            f"🧮 Answer = {result}"
        )

    except Exception:

        await update.message.reply_text(
            "❌ တွက်ချက်လို့မရပါ။"
        )


# =========================
# Main
# =========================

def main():

    TOKEN = os.getenv("BOT_TOKEN")

    if not TOKEN:
        print("❌ BOT_TOKEN မတွေ့ပါ။")
        return

    app = Application.builder().token(TOKEN).build()

    # /start
    app.add_handler(
        CommandHandler("start", start)
    )

    # /diamond conversation
    diamond_handler = ConversationHandler(

        entry_points=[
            CommandHandler("diamond", diamond_start)
        ],

        states={

            PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_price
                )
            ],

            PERCENT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_percent
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ],
    )

    app.add_handler(diamond_handler)

    # Normal math
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            calculate
        )
    )

    print("🤖 Diamond Math Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()