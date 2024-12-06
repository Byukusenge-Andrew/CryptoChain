import hashlib
import json
from time import time
from urllib.parse import urlparse
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
from models import Block, Transaction, Node, init_db
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from wallet import Wallet

class Blockchain:
    def __init__(self):
        self.db = init_db()
        self.pending_transactions = []
        
        # Create genesis block if not exists
        if not self.db.query(Block).first():
            self.create_block(proof=100, previous_hash="0")

    def create_block(self, proof, previous_hash):
        # Create new block in database
        block = Block(
            index=len(self.get_chain()) + 1,
            proof=proof,
            previous_hash=previous_hash
        )
        self.db.add(block)
        
        # Add pending transactions to block
        for tx in self.pending_transactions:
            transaction = Transaction(
                sender=tx['sender'],
                recipient=tx['recipient'],
                amount=tx['amount'],
                block=block
            )
            self.db.add(transaction)
        
        # Reset pending transactions
        self.pending_transactions = []
        
        self.db.commit()
        print(f"Block {block.index} created with {len(block.transactions)} transactions.")
        return block

    def get_last_block(self):
        """Get the last block in a serializable format"""
        block = self.db.query(Block).order_by(Block.index.desc()).first()
        if block:
            return {
                'index': block.index,
                'timestamp': block.timestamp.timestamp(),
                'proof': block.proof,
                'previous_hash': block.previous_hash,
                'transactions': [
                    {
                        'sender': tx.sender,
                        'recipient': tx.recipient,
                        'amount': tx.amount
                    } for tx in block.transactions
                ]
            }
        return None

    def get_chain(self):
        """Get the full chain"""
        chain = []
        blocks = self.db.query(Block).order_by(Block.index).all()
        return chain

    @property
    def chain_length(self):
        """Get the length of the chain"""
        return self.db.query(Block).count()

    def new_transaction(self, sender, recipient, amount, signature=None, public_key=None):
        """Creates a new transaction to go into the next mined block"""
        try:
            # Create transaction object
            transaction = {
                'sender': sender,
                'recipient': recipient,
                'amount': float(amount),
                'timestamp': datetime.utcnow().timestamp(),
                'public_key': public_key
            }
            
            # Mining rewards don't need verification
            if sender != "0":  # "0" is our mining reward sender
                if not signature or not public_key:
                    raise ValueError("Transaction must be signed and include public key")
                    
                # Verify sender has sufficient balance
                balance = self.get_balance(sender)
                if balance < float(amount):
                    raise ValueError(f"Insufficient balance: {balance} < {amount}")
                    
                # Verify signature
                if not self.verify_transaction(transaction, signature, public_key):
                    raise ValueError("Invalid transaction signature")
            
            # Add to pending transactions
            self.pending_transactions.append(transaction)
            
            # Save to database
            try:
                tx = Transaction(
                    sender=sender,
                    recipient=recipient,
                    amount=float(amount)
                )
                self.db.add(tx)
                self.db.commit()
                print(f"Transaction from {sender} to {recipient} for {amount} added to blockchain.")
            except Exception as e:
                self.db.rollback()
                print(f"Database error: {str(e)}")
                raise
                
            return self.get_last_block()['index'] + 1
            
        except Exception as e:
            print(f"Transaction error: {str(e)}")
            raise

    def get_balance(self, address):
        """Calculate balance for an address"""
        balance = 0
        chain = self.get_chain()
        
        for block in chain:
            for tx in block['transactions']:
                if tx['recipient'] == address:
                    balance += float(tx['amount'])
                if tx['sender'] == address:
                    balance -= float(tx['amount'])
                    
        print(f"Balance for {address}: {balance} coins")
        return balance

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a block
        """
        # We must sort the dictionary to ensure consistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        """Simple Proof of Work Algorithm"""
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        print(f"Proof of work found: {proof}")
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        """
        Validates the proof: Does hash(last_proof, proof, last_hash) contain 4 leading zeroes?
        """
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def is_chain_valid(self, chain):
        """
        Determine if a given blockchain is valid
        """
        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(previous_block):
                print(f"Invalid previous hash at block {block['index']}")
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(previous_block['proof'], block['proof'], block['previous_hash']):
                print(f"Invalid proof of work at block {block['index']}")
                return False

            previous_block = block
            current_index += 1

        return True 

    def register_node(self, address):
        """Add a new node to the list of nodes"""
        try:
            existing_node = self.db.query(Node).filter_by(address=address).first()
            if not existing_node:
                node = Node(address=address)
                self.db.add(node)
                self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error registering node {address}: {str(e)}")
            raise

    def resolve_conflicts(self):
        """Consensus algorithm: replaces chain with longest valid chain"""
        nodes = self.db.query(Node).all()
        new_chain = None
        max_length = self.chain_length
        
        for node in nodes:
            response = requests.get(f'{node.address}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            # Clear existing chain
            self.db.query(Block).delete()
            self.db.query(Transaction).delete()
            
            # Add new chain
            for block_data in new_chain:
                block = Block(
                    index=block_data['index'],
                    timestamp=datetime.fromtimestamp(block_data['timestamp']),
                    proof=block_data['proof'],
                    previous_hash=block_data['previous_hash']
                )
                self.db.add(block)
                
                # Add transactions
                for tx_data in block_data['transactions']:
                    tx = Transaction(
                        sender=tx_data['sender'],
                        recipient=tx_data['recipient'],
                        amount=tx_data['amount'],
                        block=block
                    )
                    self.db.add(tx)
            
            self.db.commit()
            print("Blockchain was replaced with the new longer valid chain.")
            return True
        
        print("No conflicts detected. Our chain is authoritative.")
        return False

    @staticmethod
    def verify_transaction(transaction, signature, public_key_pem):
        """Verify the signature of a transaction"""
        try:
            print("\nVerifying transaction signature...")
            
            # Create the same message format used for signing
            message_dict = {
                'sender': transaction['sender'],
                'recipient': transaction['recipient'],
                'amount': float(transaction['amount'])
            }

            # Create message string in exactly the same way
            message = json.dumps(message_dict, sort_keys=True)
            print(f"Message to verify: {message}")
            message_bytes = message.encode('utf-8')
            
            # Convert hex signature back to bytes
            try:
                signature_bytes = bytes.fromhex(signature)
                print(f"Signature length: {len(signature_bytes)} bytes")
            except ValueError as e:
                print(f"Invalid signature format: {str(e)}")
                return False

            # Load public key
            try:
                public_key = serialization.load_pem_public_key(public_key_pem.encode())
            except Exception as e:
                print(f"Error loading public key: {str(e)}")
                return False

            # Verify signature
            try:
                public_key.verify(
                    signature_bytes,
                    message_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                print("✓ Signature verified successfully")
                return True
            except InvalidSignature:
                print("✗ Invalid signature")
                return False
            except Exception as e:
                print(f"Verification error: {str(e)}")
                return False

        except Exception as e:
            print(f"Error in verify_transaction: {str(e)}")
            return False