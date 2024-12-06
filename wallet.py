from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import json
import hashlib
from datetime import datetime

class Wallet:
    def __init__(self):
        # Generate private/public key pair
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # Generate address from public key
        public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.address = hashlib.sha256(public_key_bytes).hexdigest()[:32]
        
    def create_transaction(self, recipient, amount):
        """Create and sign a transaction"""
        message_dict = {
            'sender': self.address,
            'recipient': recipient,
            'amount': amount
        }
        signature = self.private_key.sign(...)
        return transaction

    def sign_transaction(self, transaction):
        """Sign a transaction with private key"""
        try:
            # Create message from only essential fields in a consistent order
            message_dict = {
                'sender': transaction['sender'],
                'recipient': transaction['recipient'],
                'amount': float(transaction['amount'])
            }
            
            # Sort keys to ensure consistent ordering for signature
            message = json.dumps(message_dict, sort_keys=True).encode('utf-8')
            print(f"\nSigning message:")
            print(json.dumps(message_dict, sort_keys=True))
            
            signature = self.private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return signature
            
        except Exception as e:
            print(f"Error signing transaction: {str(e)}")
            raise

    def save_to_file(self, filename):
        """Save wallet to file"""
        data = {
            'private_key': self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode(),
            'public_key': self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode(),
            'address': self.address
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f)

    @classmethod
    def load_from_file(cls, filename):
        """Load wallet from file"""
        with open(filename, 'r') as f:
            data = json.load(f)
            
        wallet = cls.__new__(cls)
        wallet.private_key = serialization.load_pem_private_key(
            data['private_key'].encode(),
            password=None
        )
        wallet.public_key = serialization.load_pem_public_key(
            data['public_key'].encode()
        )
        wallet.address = data['address']
        
        # Verify address matches public key
        public_key_bytes = wallet.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        computed_address = hashlib.sha256(public_key_bytes).hexdigest()[:32]
        
        if computed_address != wallet.address:
            raise ValueError("Address does not match public key")
            
        return wallet

    @staticmethod
    def verify_address(address, public_key_pem):
        """Verify that an address matches a public key"""
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            computed_address = hashlib.sha256(public_key_bytes).hexdigest()[:32]
            return computed_address == address
        except Exception:
            return False

    @staticmethod
    def verify_transaction(transaction, signature, public_key_pem):
        """Verify a transaction signature"""
        try:
            # Recreate the same message that was signed
            message_dict = {
                'sender': transaction['sender'],
                'recipient': transaction['recipient'],
                'amount': float(transaction['amount']),
                'timestamp': float(transaction['timestamp'])
            }
            message = json.dumps(message_dict, sort_keys=True).encode('utf-8')
            
            # Load the public key
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            
            # Verify the signature
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {str(e)}")
            return False