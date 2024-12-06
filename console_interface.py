import cmd
import json
import requests
from blockchain import Blockchain
from wallet import Wallet
from datetime import datetime

class BlockchainCLI(cmd.Cmd):
    intro = 'Welcome to blockchain console. Type help or ? to list commands.\n'
    prompt = '(blockchain) '

    def __init__(self):
        super().__init__()
        self.node_url = "http://localhost:5000"  # Default node
        self.wallet = None
        self.mining_reward = 1
        self.difficulty = 4

    def do_create_wallet(self, arg):
        'Create a new wallet'
        self.wallet = Wallet()
        print(f"New wallet created with address: {self.wallet.address}")

    def do_get_balance(self, arg):
        'Get wallet balance'
        try:
            if not self.wallet:
                print("❌ No wallet loaded. Create or load a wallet first.")
                return

            response = requests.get(f"{self.node_url}/chain")
            if response.status_code != 200:
                print(f"❌ Failed to get chain. Status code: {response.status_code}")
                return

            chain_data = response.json()
            balance = 0
            
            for block in chain_data['chain']:
                for tx in block['transactions']:
                    if tx['recipient'] == self.wallet.address:
                        balance += tx['amount']
                    if tx['sender'] == self.wallet.address:
                        balance -= tx['amount']
            
            print(f"💰 Balance for {self.wallet.address}: {balance} coins")
            
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to node. Is the blockchain node running?")
            print("   Start the node with: python node.py")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def do_send(self, arg):
        'Send coins: send <recipient> <amount>'
        try:
            if not self.wallet:
                print("❌ No wallet loaded. Create or load a wallet first.")
                return

            recipient, amount = arg.split()
            amount = float(amount)
            
            # Create transaction with public key
            transaction = self.wallet.create_transaction(recipient, amount)
            
            # Sign the transaction
            signature = self.wallet.sign_transaction(transaction)
            
            # Prepare payload with signature
            payload = {
                **transaction,  # This includes sender, recipient, amount, timestamp, and public_key
                'signature': signature.hex()  # Convert signature to hex
            }
            
            # Send transaction
            response = requests.post(
                f"{self.node_url}/transactions/new", 
                json=payload
            )
            
            if response.status_code == 201:
                print(f"✅ Transaction created successfully!")
                print(f"   From: {self.wallet.address}")
                print(f"   To: {recipient}")
                print(f"   Amount: {amount}")
                print("   Mine a new block to confirm the transaction.")
            else:
                print(f"❌ Transaction failed. Status code: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to node. Is the blockchain node running?")
            print("   Start the node with: python node.py")
        except ValueError:
            print("❌ Usage: send <recipient> <amount>")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def do_mine(self, arg):
        'Mine a new block'
        try:
            if not self.wallet:
                print("❌ No wallet loaded. Create or load a wallet first.")
                return

            print("⛏️ Mining new block...")
            
            # Set the node identifier to our wallet address
            headers = {'X-Node-Identifier': self.wallet.address}
            response = requests.get(f"{self.node_url}/mine", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Block mined successfully!")
                print(f"   Block index: {result['block']['index']}")
                print(f"   Mining reward: 1 coin")
                
                # Verify the mining reward transaction
                transactions = result['block']['transactions']
                reward_tx = next((tx for tx in transactions if tx['sender'] == "0"), None)
                if reward_tx and reward_tx['recipient'] == self.wallet.address:
                    print(f"   Reward received: {reward_tx['amount']} coins")
                else:
                    print("❌ Warning: Mining reward transaction not found!")
            else:
                print(f"❌ Mining failed. Status code: {response.status_code}")
                print(response.text)
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to node. Is the blockchain node running?")
            print("   Start the node with: python node.py")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def do_chain(self, arg):
        'Print the current blockchain'
        try:
            response = requests.get(f"{self.node_url}/chain")
            if response.status_code == 200:
                chain_data = response.json()
                print("\n📦 Blockchain:")
                print(f"Length: {chain_data['length']} blocks")
                
                for block in chain_data['chain']:
                    print(f"\nBlock #{block['index']}")
                    print(f"Previous Hash: {block['previous_hash']}")
                    print(f"Proof: {block['proof']}")
                    print("Transactions:")
                    for tx in block['transactions']:
                        print(f"  {tx['sender']} -> {tx['recipient']}: {tx['amount']} coins")
            else:
                print(f"❌ Failed to get chain. Status code: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to node. Is the blockchain node running?")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def do_save_wallet(self, arg):
        'Save wallet to file: save_wallet <filename>'
        if not self.wallet:
            print("❌ No wallet to save. Create a wallet first.")
            return
            
        filename = arg or 'wallet.pem'
        try:
            self.wallet.save_to_file(filename)
            print(f"✅ Wallet saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving wallet: {e}")

    def do_load_wallet(self, arg):
        'Load wallet from file: load_wallet <filename>'
        filename = arg or 'wallet.pem'
        try:
            self.wallet = Wallet.load_from_file(filename)
            print(f"✅ Wallet loaded from {filename}")
            print(f"   Address: {self.wallet.address}")
        except Exception as e:
            print(f"❌ Error loading wallet: {e}")

    def do_status(self, arg):
        'Show blockchain status'
        try:
            response = requests.get(f"{self.node_url}/chain")
            if response.status_code == 200:
                chain_data = response.json()
                print("\n📊 Blockchain Status:")
                print(f"Chain length: {chain_data['length']} blocks")
                print(f"Latest block: #{chain_data['chain'][-1]['index']}")
                print(f"Total transactions: {sum(len(block['transactions']) for block in chain_data['chain'])}")
            else:
                print("❌ Failed to get blockchain status")
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to node. Is the blockchain node running?")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def do_exit(self, arg):
        'Exit the console'
        print("Goodbye!")
        return True

if __name__ == '__main__':
    BlockchainCLI().cmdloop() 