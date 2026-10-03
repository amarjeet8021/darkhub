# Vehicle Telegram Bot (VS Code)

1. Extract this folder.
2. Copy `.env.example` to a file named `.env` in the same folder as `bot.py`.
3. Put your real Telegram BotFather token in `BOT_TOKEN`.
4. Install dependencies in the VS Code terminal:
   `python -m pip install -r requirements.txt`
5. Run:
   `python bot.py`

If Windows hides extensions, ensure the file is `.env`, not `.env.txt`.

The bot displays only allowlisted non-personal vehicle fields. Bulk CSV mode validates
authorized records and returns a CSV format report; it does not perform mass API lookups.
Use the API only where you have permission and follow its provider terms.
