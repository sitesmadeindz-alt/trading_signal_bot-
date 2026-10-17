# TradingView to Telegram Signal Bot with Claude AI Analysis

This project connects TradingView alerts (or BingX webhook) to Telegram via a FastAPI server, using Claude AI to analyze and validate trading signals before sending them to your Telegram chat.

## Features

- Receives webhook alerts from TradingView (via Pine Script) or BingX
- Uses Claude AI (Anthropic) to analyze the signal:
  - Validates the trade setup
  - Calculates precise Stop Loss, TP1, TP2 levels
  - Computes risk-reward ratio (RR)
  - Provides confidence score and logical explanation
- Sends formatted, plain-text signals to Telegram
- No emojis, clean and professional message format

## Project Structure

```
trading_signal_bot/
├── main.py                 # FastAPI server, webhook endpoint
├── config.py               # Configuration loader (environment variables)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── services/
│   ├── bingx_service.py    # Fetch market data from BingX (klines, ticker)
│   ├── claude_analyzer.py  # Send data to Claude, get analysis
│   └── telegram_service.py # Format and send messages to Telegram
├── pine_scripts/
│   └── tradingview_alert.pine # Pine Script v6 example (EMA crossover)
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Accounts:
  - [TradingView](https://www.tradingview.com/) (for alerts)
  - [BingX](https://bingx.com/) (optional, for market data)
  - [Anthropic Claude API](https://console.anthropic.com/) (for AI analysis)
  - [Telegram Bot](https://core.telegram.org/bots#6-botfather) (get token from BotFather)

### 2. Clone & Install

```bash
# Clone or copy this folder to your machine
cd trading_signal_bot

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
# Edit .env with your keys:
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
ANTHROPIC_API_KEY=your_anthropic_api_key
BINGX_API_KEY=your_bingx_api_key
BINGX_API_SECRET=your_bingx_api_secret
WEBHOOK_SECRET=a_random_secret_string_for_security
HOST=0.0.0.0
PORT=8000
```

### 4. Create TradingView Alert (Pine Script)

1. Open TradingView and go to **Chart** for XAU/USD (or any symbol).
2. Add a new indicator: **Pine Editor** → paste the code from `pine_scripts/tradingview_alert.pine`.
3. Save and add to chart.
4. Click the **Alarm** button (clock icon) → **Create Alert**.
   - Condition: Select the script you just added.
   - Options: Choose `Once per bar close`.
   - Alert Actions: **Webhook URL**.
   - URL: `http://YOUR_SERVER_IP:PORT/webhook` (replace with your server's public IP or ngrok URL).
   - Message: Leave default or customize (the script sends `symbol:action:price`).
   - Create.

### 5. Run the Bot

```bash
# Ensure .env is set
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will start and listen for POST requests at `/webhook`.

### 6. (Optional) Expose Local Server to Public Internet

If running locally, use [ngrok](https://ngrok.com/) to create a public URL:

```bash
ngrok http 8000
```
Then use the `https://xxxx.ngrok.io/webhook` URL in your TradingView alert.

## How It Works

1. TradingView sends an alert (via Pine Script) to your server's `/webhook` endpoint.
2. The server validates the webhook (secret optional) and extracts `{symbol, action, price}`.
3. It fetches recent market data from BingX (klines and ticker) for context.
4. All data is sent to Claude AI with a prompt asking:
   - Should we take this trade?
   - If yes: exact entry, SL, TP1, TP2, RR, confidence, and logic.
5. If Claude approves (`take_trade: true`), a formatted plain-text message is sent to Telegram.
6. If Claude rejects, no message is sent (you can log or notify if desired).

## Customization

- **Signal Logic**: Edit `pine_scripts/tradingview_alert.pine` to use any indicator or strategy (RSI, MACD, price action, etc.).
- **Claude Prompt**: Modify `services/claude_analyzer.py` `_build_prompt` method to change analysis criteria.
- **Telegram Format**: Adjust `services/telegram_service.py` `format_signal` method if you want different fields.
- **Risk Management**: The Claude analyzer enforces RR >= 1.2; you can adjust this threshold in the prompt.

## Notes & Disclaimer

- **This is not financial advice.** The bot automates signal validation but does not guarantee profits.
- Test thoroughly on demo/paper trading before using with real funds.
- Keep your API keys secure; never commit `.env` to public repositories.
- The BingX service uses public endpoints; no signature needed for market data.
- For production, consider adding webhook signature verification (HMAC) in `main.py`.

## License

MIT
