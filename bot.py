
import os
import re
import json
import asyncio
from pathlib import Path

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_URL = os.getenv("API_URL", "").strip()
API_KEY = os.getenv("API_KEY", "").strip()

VEHICLE_PATTERN = re.compile(
    r"^[A-Z]{2}[0-9]{1,2}[A-Z]{0,3}[0-9]{1,4}$"
)

SAFE_FIELDS = {
    "registration_number",
    "vehicle_number",
    "vehicle_type",
    "vehicle_class",
    "manufacturer",
    "model",
    "fuel_type",
    "registration_date",
    "fitness_validity",
    "insurance_status",
    "pollution_status",
    "vehicle_status",
    "rto",
    "state",
}


def valid_vehicle_number(number):
    return bool(
        VEHICLE_PATTERN.fullmatch(number.strip().upper())
    )


def call_vehicle_api(number):
    response = requests.get(
        API_URL,
        params={
            "api": API_KEY,
            "q": number
        },
        timeout=20
    )

    print("API STATUS:", response.status_code)
    print("API RAW RESPONSE:", response.text[:3000])

    response.raise_for_status()
    return response.json()


def sanitize_response(data):

    if isinstance(data, dict):
        cleaned = {}

        for key, value in data.items():

            normalized = re.sub(
                r"[^a-z0-9_]",
                "_",
                str(key).lower()
            ).strip("_")

            if normalized in SAFE_FIELDS:
                if isinstance(value, (str, int, float, bool)):
                    cleaned[str(key)] = value

            elif isinstance(value, (dict, list)):
                nested = sanitize_response(value)

                if nested:
                    cleaned[str(key)] = nested

        return cleaned

    if isinstance(data, list):
        return [
            sanitize_response(item)
            for item in data
            if isinstance(item, (dict, list))
        ]

    return {}


def format_result(data):

    cleaned = sanitize_response(data)

    if not cleaned:
        return (
            "⚠️ API response received, but no supported "
            "vehicle fields were found.\n\n"
            "Please check the API provider response format."
        )

    return json.dumps(
        cleaned,
        ensure_ascii=False,
        indent=2
    )[:3500]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🚗 VEHICLE INFORMATION BOT\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome!\n\n"
        "Send a vehicle registration number "
        "to perform an authorized single lookup.\n\n"
        "📌 Available Commands:\n"
        "/start - Start Bot\n"
        "/help - Help\n\n"
        "🔎 Normal Search System Active"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🚗 VEHICLE SEARCH HELP\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "1. Send a valid vehicle registration number.\n"
        "2. Wait while the authorized API is checked.\n"
        "3. Available non-personal vehicle information "
        "will be displayed.\n\n"
        "Example format: MH12AB1234\n\n"
        "Commands:\n"
        "/start - Start\n"
        "/help - Help"
    )


async def vehicle_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    number = update.message.text.strip().upper()

    if not valid_vehicle_number(number):
        await update.message.reply_text(
            "❌ Invalid vehicle registration format.\n\n"
            "Please enter a valid registration number."
        )
        return

    status = await update.message.reply_text(
        "🔎 Checking authorized vehicle API...\n"
        "Please wait."
    )

    try:
        data = await asyncio.to_thread(
            call_vehicle_api,
            number
        )

        result = format_result(data)

        await status.edit_text(
            "🚘 VEHICLE SEARCH RESULT\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            + result
        )

    except requests.exceptions.Timeout:

        await status.edit_text(
            "⏳ API request timed out.\n"
            "Please try again later."
        )

    except requests.exceptions.HTTPError as exc:

        code = (
            exc.response.status_code
            if exc.response is not None
            else "Unknown"
        )

        await status.edit_text(
            f"⚠️ API Provider Error: HTTP {code}"
        )

    except requests.exceptions.RequestException:

        await status.edit_text(
            "⚠️ Could not connect to the API provider."
        )

    except (ValueError, json.JSONDecodeError):

        await status.edit_text(
            "⚠️ API returned invalid JSON."
        )

    except Exception as exc:

        print("Unexpected error:", repr(exc))

        await status.edit_text(
            "❌ Unexpected error occurred. "
            "Please check the VS Code terminal."
        )


def main():

    if not BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN missing in .env file."
        )

    if not API_URL or not API_KEY:
        raise ValueError(
            "API_URL or API_KEY missing in .env file."
        )

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    # Normal single vehicle search only
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            vehicle_lookup
        )
    )

    print("Vehicle Search Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()