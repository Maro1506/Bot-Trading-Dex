import time
import schedule
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from config import DexBotConfig
from contracts import ContractManager
from strategy import TradingStrategy
from utils import send_telegram_alert, calculate_volatility

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dex_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DexBot:
    def __init__(self):
        self.config = DexBotConfig
        self.web3 = self.init_web3()
        self.cm = ContractManager(self.web3)
        self.strategy = TradingStrategy(self.web3, self.cm)
        self.price_history = {}
        self.starting_balance = self.get_portfolio_value()
        
    def init_web3(self):
        """Inicializa la conexión Web3"""
        w3 = Web3(Web3.HTTPProvider(self.config.RPC_URL))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        if not w3.is_connected():
            raise ConnectionError("Error de conexión a la blockchain")
            
        logger.info(f"Conectado a {self.config.RPC_URL}")
        logger.info(f"Block más reciente: {w3.eth.block_number}")
        
        return w3
    
    def get_portfolio_value(self):
        """Calcula el valor total del portfolio en BNB"""
        # Implementar según tokens en tu wallet
        return 0  # Placeholder
    
    def check_daily_loss_limit(self):
        """Verifica el límite de pérdida diaria"""
        current_balance = self.get_portfolio_value()
        loss_percentage = (self.starting_balance - current_balance) / self.starting_balance
        
        if loss_percentage >= self.config.MAX_DAILY_LOSS:
            msg = f"🚨 ALERTA: Pérdida diaria excedida ({loss_percentage*100:.2f}%)"
            logger.error(msg)
            send_telegram_alert(msg)
            return False
        return True
    
    def execute_trading_strategy(self):
        """Ejecuta la estrategia de trading principal"""
        if not self.check_daily_loss_limit():
            return schedule.CancelJob  # Detener el bot
            
        try:
            for pair in self.config.TARGET_PAIRS:
                self.process_pair(pair)
        except Exception as e:
            logger.error(f"Error en estrategia: {e}")
            send_telegram_alert(f"❌ Error en estrategia: {str(e)}")
    
    def process_pair(self, pair_config):
        """Procesa un par de trading específico"""
        symbol = pair_config["symbol"]
        current_price = self.strategy.get_price(pair_config)
        
        # Actualizar historial de precios
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            
        self.price_history[symbol].append(current_price)
        self.price_history[symbol] = self.price_history[symbol][-100:]  # Mantener últimos 100 puntos
        
        # Calcular cambio porcentual
        if len(self.price_history[symbol]) > 6:  # 30 min para intervalo de 5 min
            price_change = ((current_price - self.price_history[symbol][-6]) / self.price_history[symbol][-6]) * 100
        else:
            price_change = 0
            
        # Calcular volatilidad
        volatility = calculate_volatility(self.price_history[symbol])
        position_size = max(0.01, min(0.5, 0.1 / max(0.01, volatility/100)))
        
        # Lógica de trading aquí...
        # (Implementar según estrategia específica)
        
        logger.info(f"{symbol} | Precio: {current_price:.6f} | Cambio: {price_change:.2f}% | Vol: {volatility:.2f}%")
    
    def run(self):
        """Inicia el bot"""
        logger.info("🚀 Iniciando Dex Trading Bot")
        logger.info(f"Red: {self.config.NETWORK}")
        logger.info(f"Monitoreando {len(self.config.TARGET_PAIRS)} pares")
        
        # Programar ejecución periódica
        schedule.every(self.config.CHECK_INTERVAL).seconds.do(self.execute_trading_strategy)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Bot detenido manualmente")
            send_telegram_alert("🛑 Bot detenido manualmente")

if __name__ == "__main__":
    bot = DexBot()
    bot.run()