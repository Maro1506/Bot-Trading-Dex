import json
from web3 import Web3
from config import DexBotConfig

class ContractManager:
    def __init__(self, web3):
        self.web3 = web3
        self.contracts = {}
        
    def load_abi(self, contract_name):
        """Carga el ABI desde el archivo JSON"""
        try:
            with open(f"abis/{contract_name}.json") as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"ABI para {contract_name} no encontrado")
    
    def get_contract(self, contract_name):
        """Obtiene una instancia del contrato"""
        if contract_name in self.contracts:
            return self.contracts[contract_name]
            
        address = DexBotConfig.get_contract_address(contract_name)
        abi = self.load_abi(contract_name)
        
        contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi
        )
        self.contracts[contract_name] = contract
        return contract
    
    def get_pair_contract(self, token_a, token_b):
        """Obtiene el contrato del par LP"""
        factory = self.get_contract("FACTORY")
        pair_address = factory.functions.getPair(
            Web3.to_checksum_address(DexBotConfig.get_contract_address(token_a)),
            Web3.to_checksum_address(DexBotConfig.get_contract_address(token_b))
        ).call()
        
        return self.web3.eth.contract(
            address=Web3.to_checksum_address(pair_address),
            abi=self.load_abi("Pair")
        )