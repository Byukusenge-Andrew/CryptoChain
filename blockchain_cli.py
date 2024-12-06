import click
import requests
from wallet import Wallet
import json
from datetime import datetime

class BlockchainCLI:
    def __init__(self, node_url="http://localhost:5000"):
        self.node_url = node_url
        self.wallet = None

    def create_wallet(self):
        """Create a new wallet"""
        self.wallet = Wallet()
        print(f"✅ New wallet created!")
        print(f"Address: {self.wallet.address}")
        return self.wallet

    def get_balance(self):
        """Get wallet balance"""
        if not self.wallet:
            print("❌ No wallet loaded. Create or load a wallet first.")
            return
        
        response = requests.get(f"{self.node_url}/chain")
        if response.status_code != 200:
            print("❌ Failed to get blockchain data")
            return

        chain = response.json()['chain']
        balance = 0

        # Calculate balance from blockchain
        for block in chain:
            for tx in block['transactions']:
                if tx['recipient'] == self.wallet.address:
                    balance += tx['amount']
                if tx['sender'] == self.wallet.address:
                    balance -= tx['amount']

        print(f"\n💰 Balance for {self.wallet.address}:")
        print(f"   {balance} coins")
        return balance

    def send_transaction(self, recipient, amount):
        """Send a transaction"""
        try:
            if not self.wallet:
                print("❌ No wallet loaded. Create or load a wallet first.")
                return

            # Create transaction
            transaction = self.wallet.create_transaction(recipient, amount)
            print(f"Transaction created: {transaction}")

            # Send to node
            response = requests.post(
                f"{self.node_url}/transactions/new",
                json=transaction  # Send the complete transaction
            )

            if response.status_code == 201:
                print(f"✅ Transaction sent successfully!")
                print(f"   From: {self.wallet.address}")
                print(f"   To: {recipient}")
                print(f"   Amount: {amount}")
            else:
                print("❌ Failed to send transaction")
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to node. Is the blockchain node running?")
            print("   Start the node with: python node.py")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def mine(self):
        """Mine a new block"""
        if not self.wallet:
            print("❌ No wallet loaded. Create or load a wallet first.")
            return

        print("⛏️ Mining new block...")
        response = requests.get(f"{self.node_url}/mine")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Block mined successfully!")
            print(f"   Block index: {result['index']}")
            print(f"   Transactions: {len(result['transactions'])}")
            print(f"   Mining reward: 1 coin")
        else:
            print("❌ Mining failed")
            print(response.text)

    def show_chain(self):
        """Show the current blockchain"""
        response = requests.get(f"{self.node_url}/chain")
        if response.status_code != 200:
            print("❌ Failed to get blockchain")
            return

        chain = response.json()
        print("\n📦 Blockchain:")
        print(f"Length: {chain['length']} blocks")
        
        for block in chain['chain']:
            print(f"\nBlock #{block['index']}")
            print(f"Timestamp: {datetime.fromtimestamp(block['timestamp'])}")
            print(f"Transactions: {len(block['transactions'])}")
            for tx in block['transactions']:
                print(f"  {tx['sender']} -> {tx['recipient']}: {tx['amount']} coins")

@click.group()
def cli():
    pass

@cli.command()
def create():
    """Create a new wallet"""
    blockchain = BlockchainCLI()
    blockchain.create_wallet()

@cli.command()
def balance():
    """Check wallet balance"""
    blockchain = BlockchainCLI()
    blockchain.create_wallet()  # For testing, create new wallet
    blockchain.get_balance()

@cli.command()
@click.argument('recipient')
@click.argument('amount', type=float)
def send(recipient, amount):
    """Send coins to an address"""
    blockchain = BlockchainCLI()
    blockchain.create_wallet()  # For testing, create new wallet
    blockchain.send_transaction(recipient, amount)

@cli.command()
def mine_block():
    """Mine a new block"""
    blockchain = BlockchainCLI()
    blockchain.create_wallet()  # For testing, create new wallet
    blockchain.mine()

@cli.command()
def chain():
    """Show the blockchain"""
    blockchain = BlockchainCLI()
    blockchain.show_chain()

if __name__ == '__main__':
    cli() 