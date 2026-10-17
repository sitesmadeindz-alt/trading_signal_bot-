import os
import json
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Import services (we'll create these files next)
from services.bingx_service import BingXService
from services.claude_analyzer import ClaudeAnalyzer
from services.telegram_service import TelegramService

# Initialize services
bingx_service = BingXService()
claude_analyzer = ClaudeAnalyzer()
telegram_service = TelegramService()

@app.post("/webhook")
async def tradingview_webhook(request: Request, background_tasks: BackgroundTasks):
    # Verify webhook secret (optional but recommended)
    # For simplicity, we skip signature verification in this example, but you can add it.
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Extract essential data from TradingView alert
    # Expected payload from TradingView:
    # {
    #   "symbol": "XAUUSD",
    #   "action": "buy" or "sell",
    #   "price": 1950.50,   # entry price
    #   "time": "2024-05-20T10:30:00Z"
    # }
    symbol = payload.get("symbol")
    action = payload.get("action")
    entry_price = payload.get("price")
    time = payload.get("time")

    if not all([symbol, action, entry_price]):
        raise HTTPException(status_code=400, detail="Missing required fields: symbol, action, price")

    # Fetch additional market data from BingX (e.g., recent klines for confirmation)
    market_data = bingx_service.get_market_data(symbol)

    # Prepare data for Claude analysis
    analysis_input = {
        "symbol": symbol,
        "action": action,
        "entry_price": float(entry_price),
        "time": time,
        "market_data": market_data
    }

    # Get analysis from Claude (including SL, TP1, TP2, confidence, and logic)
    analysis_result = claude_analyzer.analyze_trade(analysis_input)

    # If Claude rejects the trade, we do not send a signal
    if not analysis_result.get("take_trade", False):
        # Optionally log or send a rejection message
        return JSONResponse(content={"status": "trade rejected by Claude", "reason": analysis_result.get("reason")})

    # Format the message for Telegram
    message = telegram_service.format_signal(
        symbol=symbol,
        action=action,
        entry_price=analysis_result["entry_price"],
        stop_loss=analysis_result["stop_loss"],
        tp1=analysis_result["tp1"],
        tp2=analysis_result["tp2"],
        risk_reward=analysis_result["risk_reward"],
        confidence=analysis_result["confidence"],
        logic=analysis_result["logic"]
    )

    # Send to Telegram in the background so we don't block the webhook response
    background_tasks.add_task(telegram_service.send_message, message)

    return JSONResponse(content={"status": "signal sent to Telegram", "details": analysis_result})

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "TradingView to Telegram Signal Bot is running"}
