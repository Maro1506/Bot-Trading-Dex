import os
from dotenv import load_dotenv

load_dotenv()

class DexBotConfig:
    # Configuración de red
    NETWORK = "MAINNET"  # TESTNET o MAINNET
    RPC_URL = os.getenv("RPC_URL", "https://bsc-dataseed.binance.org/")
    
    # Configuración de wallet
    WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
    PRIVATE_KEY = os.getenv("PRIVATE_KEY")
    
    # Parámetros de trading
    TARGET_PAIRS = [
        {"symbol": "CAKE/BNB", "token_in": "WBNB", "token_out": "CAKE"},
        # Agregar más pares aquí
    ]
    CHECK_INTERVAL = 30  # segundos
    DIP_THRESHOLD = -5.0  # % para comprar
    PROFIT_TARGET = 10.0  # % para vender
    STOP_LOSS = -5.0      # % para stop-loss
    MAX_DAILY_LOSS = 0.05 # 5% del capital
    SLIPPAGE = 1.0        # 1%
    MAX_GAS_GWEI = 15     # Límite de gas
    
    # Direcciones de contratos
    CONTRACTS = {
        "MAINNET": {
            "ROUTER": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
            "FACTORY": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73",
            "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
            "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"
        },
        "TESTNET": {
            "ROUTER": "0xD99D1c33F9fC3444f8101754aBC46c52416550D1",
            "FACTORY": "0x6725F303b657a9451d8BA641348b6761A6CC7a17",
            "WBNB": "0xae13d989daC2f0dEbFf460aC112a837C89BAa7cd",
            "CAKE": "0xFa60D973F7642B748046464e165A65B7323b0DEE"
        }
    }
    
    # Configuración de notificaciones
    TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    @classmethod
    def get_contract_address(cls, contract_name):
        return cls.CONTRACTS[cls.NETWORK][contract_name]