import time
import logging
from web3 import Web3
from .contracts import ContractManager
from .utils import get_optimal_gas_price, send_telegram_alert, anti_mev_delay, calculate_volatility
from .config import DexBotConfig

logger = logging.getLogger(__name__)

class TradingStrategy:
    def __init__(self, web3, contract_manager):
        self.web3 = web3
        self.cm = contract_manager
        self.entry_prices = {}
        self.token_approvals = set()
        
    def ensure_approval(self, token_symbol):
        """Aprueba tokens si es necesario"""
        token_address = DexBotConfig.get_contract_address(token_symbol)
        if token_address in self.token_approvals:
            return True
            
        token_contract = self.cm.get_contract(token_symbol)
        router_address = DexBotConfig.get_contract_address("ROUTER")
        
        try:
            tx = token_contract.functions.approve(
                router_address,
                2**256 - 1  # Aprobación máxima
            ).build_transaction({
                'from': DexBotConfig.WALLET_ADDRESS,
                'nonce': self.web3.eth.get_transaction_count(DexBotConfig.WALLET_ADDRESS),
                'gas': 100000,
                'gasPrice': self.web3.to_wei(get_optimal_gas_price(self.web3), 'gwei')
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, DexBotConfig.PRIVATE_KEY)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                self.token_approvals.add(token_address)
                send_telegram_alert(f"✅ Aprobación exitosa para {token_symbol}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error en aprobación: {e}")
            return False

    def get_price(self, pair_config):
        """Obtiene precio actual del par"""
        pair_contract = self.cm.get_pair_contract(
            pair_config["token_in"],
            pair_config["token_out"]
        )
        reserves = pair_contract.functions.getReserves().call()
        
        # Determinar qué reserva corresponde a cada token
        token0 = pair_contract.functions.token0().call()
        token_in_address = DexBotConfig.get_contract_address(pair_config["token_in"])
        
        if token0.lower() == token_in_address.lower():
            reserve_in = reserves[0]
            reserve_out = reserves[1]
        else:
            reserve_in = reserves[1]
            reserve_out = reserves[0]
        
        return reserve_out / reserve_in if reserve_in > 0 else 0

    def execute_swap(self, pair_config, amount_in, is_buy):
        """Ejecuta un swap en PancakeSwap"""
        try:
            anti_mev_delay()  # Protección MEV
            
            router = self.cm.get_contract("ROUTER")
            token_in = DexBotConfig.get_contract_address(pair_config["token_in"])
            token_out = DexBotConfig.get_contract_address(pair_config["token_out"])
            
            # Obtener ruta y cantidades
            path = [Web3.to_checksum_address(token_in), 
                    Web3.to_checksum_address(token_out)]
            
            amounts_out = router.functions.getAmountsOut(
                int(amount_in),
                path
            ).call()
            
            amount_out_min = int(amounts_out[-1] * (1 - DexBotConfig.SLIPPAGE / 100))
            
            # Construir transacción
            tx = router.functions.swapExactTokensForTokens(
                int(amount_in),
                amount_out_min,
                path,
                DexBotConfig.WALLET_ADDRESS,
                int(time.time()) + 1200  # Deadline
            ).build_transaction({
                'from': DexBotConfig.WALLET_ADDRESS,
                'nonce': self.web3.eth.get_transaction_count(DexBotConfig.WALLET_ADDRESS),
                'gas': 250000,
                'gasPrice': self.web3.to_wei(get_optimal_gas_price(self.web3), 'gwei')
            })
            
            # Firmar y enviar
            signed_tx = self.web3.eth.account.sign_transaction(tx, DexBotConfig.PRIVATE_KEY)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            return receipt.status == 1, tx_hash.hex()
        except Exception as e:
            logger.error(f"Error en swap: {e}")
            return False, None