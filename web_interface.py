from flask import Flask, render_template, request, jsonify, redirect, url_for
from blockchain import Blockchain
from wallet import Wallet
import requests
import os
import json
import traceback

# Initialize Flask with template folder explicitly
app = Flask(__name__, 
    template_folder=os.path.abspath('templates'))

# Enable debug mode
app.debug = True

# Initialize blockchain and wallet
blockchain = Blockchain()
wallet = Wallet()

# Add a simple route to test if server is running
@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'running',
        'routes': [str(rule) for rule in app.url_map.iter_rules()]
    })

@app.route('/')
def index():
    # Calculate balance
    balance = 0
    total_transactions = 0
    blocks_mined = 0
    mining_rewards = 0
    
    for block in blockchain.get_chain():
        total_transactions += len(block['transactions'])
        for tx in block['transactions']:
            if tx['recipient'] == wallet.address:
                balance += tx['amount']
                if tx['sender'] == "0":  # Mining reward
                    blocks_mined += 1
                    mining_rewards += tx['amount']
            if tx['sender'] == wallet.address:
                balance -= tx['amount']

    return render_template('index.html', 
                         address=wallet.address,
                         chain=blockchain.get_chain(),
                         pending=blockchain.pending_transactions,
                         balance=balance,
                         total_transactions=total_transactions,
                         blocks_mined=blocks_mined,
                         mining_rewards=mining_rewards)

@app.route('/transaction', methods=['POST'])
def new_transaction():
    try:
        # Check if wallet exists
        if not wallet:
            return jsonify({'error': 'No wallet available. Please create or load a wallet first.'}), 400

        # Get and validate form data
        recipient = request.form.get('recipient')
        amount_str = request.form.get('amount')

        if not recipient:
            return jsonify({'error': 'Recipient address is required'}), 400
        if not amount_str:
            return jsonify({'error': 'Amount is required'}), 400

        try:
            amount = float(amount_str)
        except ValueError:
            return jsonify({'error': 'Invalid amount format'}), 400

        print(f"Creating transaction: recipient={recipient}, amount={amount}")
        
        # Create and sign transaction
        try:
            transaction = wallet.create_transaction(recipient, amount)
            print(f"Transaction created: {transaction}")
        except Exception as e:
            print(f"Failed to create transaction: {str(e)}")
            return jsonify({'error': f'Failed to create transaction: {str(e)}'}), 400

        # Send transaction to blockchain
        try:
            # Only pass the required fields to new_transaction
            blockchain.new_transaction(
                sender=transaction['sender'],
                recipient=transaction['recipient'],
                amount=transaction['amount'],
                signature=transaction['signature'],
                public_key=transaction['public_key']
            )
            print("Transaction added to blockchain successfully")
            return redirect(url_for('index'))
        except ValueError as ve:
            print(f"Validation error: {str(ve)}")
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            print(f"Blockchain error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/mine', methods=['POST'])
def mine():
    try:
        # Mine a new block
        last_block = blockchain.get_last_block()
        proof = blockchain.proof_of_work(last_block)
        
        # Reward for mining
        blockchain.new_transaction(
            sender="0",
            recipient=wallet.address,
            amount=1
        )
        
        # Create new block
        previous_hash = blockchain.hash(last_block)
        block = blockchain.create_block(proof, previous_hash)
        
        print(f"New block mined: {block.index}")
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Mining error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/wallet/new', methods=['POST'])
def new_wallet():
    global wallet
    wallet = Wallet()
    print(f"New wallet created: {wallet.address}")
    return redirect(url_for('index'))

@app.route('/wallet/save', methods=['POST'])
def save_wallet():
    try:
        # Ensure filename has .pem extension
        filename = request.form.get('filename', 'wallet.pem')
        if not filename.endswith('.pem'):
            filename += '.pem'
            
        # Ensure wallet directory exists
        wallet_dir = 'wallets'
        if not os.path.exists(wallet_dir):
            os.makedirs(wallet_dir)
            
        # Full path for wallet file
        filepath = os.path.join(wallet_dir, filename)
        
        # Save wallet
        wallet.save_to_file(filepath)
        print(f"Wallet saved to {filepath}")
        return jsonify({
            'message': f'Wallet saved to {filename}',
            'address': wallet.address
        })
    except Exception as e:
        print(f"Error saving wallet: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/wallet/load', methods=['POST'])
def load_wallet():
    try:
        # Ensure filename has .pem extension
        filename = request.form.get('filename', 'wallet.pem')
        if not filename.endswith('.pem'):
            filename += '.pem'
            
        # Full path for wallet file
        filepath = os.path.join('wallets', filename)
        
        # Check if file exists
        if not os.path.exists(filepath):
            return jsonify({'error': f'Wallet file {filename} not found'}), 404
            
        # Load wallet
        global wallet
        wallet = Wallet.load_from_file(filepath)
        print(f"Wallet loaded from {filepath}: {wallet.address}")
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error loading wallet: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/wallet/list', methods=['GET'])
def list_wallets():
    """List all available wallet files"""
    try:
        wallet_dir = 'wallets'
        if not os.path.exists(wallet_dir):
            os.makedirs(wallet_dir)
            
        # Get all .pem files
        wallet_files = [f for f in os.listdir(wallet_dir) if f.endswith('.pem')]
        
        wallets = []
        for filename in wallet_files:
            filepath = os.path.join(wallet_dir, filename)
            try:
                # Try to load each wallet to get its address
                temp_wallet = Wallet.load_from_file(filepath)
                wallets.append({
                    'filename': filename,
                    'address': temp_wallet.address
                })
            except Exception as e:
                print(f"Error loading wallet {filename}: {str(e)}")
                
        return jsonify({
            'wallets': wallets
        })
    except Exception as e:
        print(f"Error listing wallets: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/connect', methods=['POST'])
def connect_to_blockchain():
    try:
        # Get current port
        current_port = request.host.split(":")[-1]
        
        # Connect to main blockchain node
        response = requests.post(
            'http://localhost:5000/nodes/register',
            json={'nodes': [f'http://localhost:{current_port}']}
        )
        
        if response.status_code == 201:
            # Sync with blockchain
            sync_response = requests.get('http://localhost:5000/nodes/resolve')
            return jsonify({
                'message': 'Successfully connected to blockchain network',
                'sync_status': sync_response.json()
            })
        else:
            return jsonify({'error': 'Failed to connect', 'details': response.json()}), 400
            
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test_transaction', methods=['GET'])
def test_transaction():
    try:
        print("\nStarting test transaction...")
        
        # Create a test wallet if none exists
        if not hasattr(test_transaction, 'test_wallet'):
            test_transaction.test_wallet = Wallet()
            print(f"Test wallet created: {test_transaction.test_wallet.address}")
        
        # Mine a block to get some coins
        print("Mining a block for initial coins...")
        mine_response = mine()
        if isinstance(mine_response, tuple):
            print(f"Mining failed: {mine_response}")
            return mine_response
        
        # Create a test transaction
        recipient = Wallet().address  # Create a new wallet as recipient
        amount = 0.1  # Small test amount
        
        print(f"\nCreating test transaction:")
        print(f"From: {wallet.address}")
        print(f"To: {recipient}")
        print(f"Amount: {amount}")
        
        transaction = wallet.create_transaction(recipient, amount)
        print("\nTransaction created:", json.dumps(transaction, indent=2))
        
        # Try to add it to blockchain
        result = blockchain.new_transaction(
            sender=transaction['sender'],
            recipient=transaction['recipient'],
            amount=transaction['amount'],
            signature=transaction['signature'],
            public_key=transaction['public_key']
        )
        
        print("\nTest transaction added successfully")
        return jsonify({
            'success': True,
            'message': 'Test transaction completed',
            'transaction': transaction,
            'result': result
        })
        
    except Exception as e:
        print(f"\nTest transaction failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test_signature', methods=['GET'])
def test_signature():
    """Test signature creation and verification"""
    print("\n=== Test Signature Endpoint Called ===")
    try:
        # Create test data
        recipient = "1234567890123456789012345678901a"  # 32 chars
        amount = 1.0

        print("\n=== Creating Transaction ===")
        # Create transaction
        transaction = wallet.create_transaction(recipient, amount)
        print(f"Transaction created: {json.dumps(transaction, indent=2)}")
        
        print("\n=== Verifying Transaction ===")
        # Verify the transaction
        result = blockchain.verify_transaction(
            transaction,
            transaction['signature'],
            transaction['public_key']
        )
        print(f"Verification result: {result}")

        return jsonify({
            'success': result,
            'transaction': transaction,
            'verification_result': result
        })

    except Exception as e:
        print(f"Test failed: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'pong'})

if __name__ == '__main__':
    try:
        # Print registered routes
        print("\nRegistered routes:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint}: {rule.methods} {rule.rule}")
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5001))
        print(f"\nStarting server on port {port}")
        
        # Run with debug mode
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f"Error starting server: {str(e)}")
        traceback.print_exc() 