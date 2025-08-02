import time
import random
import requests
import numpy as np
from web3 import Web3
from config import DexBotConfig

def get_optimal_gas_price(web3):
    """Obtiene el precio óptimo de gas"""
    try:
        response = requests.get(
            "https://api.bscscan.com/api?module=gastracker&action=gasoracle"
        ).json()
        fast_gas = float(response["result"]["FastGasPrice"])
        return min(fast_gas, DexBotConfig.MAX_GAS_GWEI)
    except:
        current_gas = web3.eth.gas_price / 1e9
        return min(current_gas * 1.1, DexBotConfig.MAX_GAS_GWEI)

def send_telegram_alert(message):
    """Envía alertas por Telegram"""
    if not DexBotConfig.TELEGRAM_API_KEY:
        return
        
    try:
        requests.post(
            f"https://api.telegram.org/bot{DexBotConfig.TELEGRAM_API_KEY}/sendMessage",
            json={
                'chat_id': DexBotConfig.TELEGRAM_CHAT_ID,
                'text': f"[DEX Bot] {message}",
                'disable_notification': False
            }
        )
    except Exception as e:
        print(f"Error enviando alerta Telegram: {e}")

def anti_mev_delay():
    """Retraso aleatorio para protección MEV"""
    time.sleep(random.uniform(1.0, 3.0))

def calculate_volatility(prices, window=30):
    """Calcula la volatilidad histórica"""
    if len(prices) < 2:
        return 0
    log_returns = np.log(prices[1:] / prices[:-1])
    return np.std(log_returns) * np.sqrt(365) * 100