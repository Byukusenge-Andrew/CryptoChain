from flask import Flask, jsonify, request
from blockchain import Blockchain
from models import Node, Block, Transaction
from uuid import uuid4
import requests
from urllib.parse import urlparse
import os
import traceback

# Initialize Flask app
app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    try:
        # Get miner's wallet address from headers
        miner_address = request.headers.get('X-Node-Identifier')
        if not miner_address:
            return jsonify({"error": "No miner address provided"}), 400
            
        # Mine a new block
        last_block = blockchain.get_last_block()
        proof = blockchain.proof_of_work(last_block)
        
        # Reward the miner
        blockchain.new_transaction(
            sender="0",  # 0 signifies mining reward
            recipient=miner_address,
            amount=1.0, 
            signature=None  
        )
        
        # Create the new block
        previous_hash = blockchain.hash(last_block)
        block = blockchain.create_block(proof, previous_hash)

        block_data = {
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
        
        return jsonify({
            'message': "New Block Mined",
            'block': block_data
        }), 200
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Error in mining: {error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    try:
        values = request.get_json()
        
        # Check required fields
        required = ['sender', 'recipient', 'amount', 'timestamp', 'signature', 'public_key']
        if not all(k in values for k in required):
            missing = [k for k in required if k not in values]
            return jsonify({
                'error': 'Missing values',
                'missing_fields': missing,
                'received_fields': list(values.keys())
            }), 400
            
        # Create new transaction
        try:
            index = blockchain.new_transaction(
                sender=values['sender'],
                recipient=values['recipient'],
                amount=values['amount'],
                signature=values['signature'],
                public_key=values['public_key']
            )
            
            response = {
                'message': f'Transaction will be added to Block {index}',
                'transaction': {
                    'sender': values['sender'],
                    'recipient': values['recipient'],
                    'amount': values['amount']
                }
            }
            return jsonify(response), 201
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': f"Transaction failed: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({'error': f"Request failed: {str(e)}"}), 500

@app.route('/chain', methods=['GET'])
def full_chain():
    try:
        chain = blockchain.get_chain()
        response = {
            'chain': chain,
            'length': len(chain)
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    try:
        values = request.get_json()
        nodes = values.get('nodes')
        
        if nodes is None:
            return jsonify({"error": "Please supply a valid list of nodes"}), 400
        
        # Register each node
        registered_nodes = []
        errors = []
        
        for node_address in nodes:
            try:
                blockchain.register_node(node_address)
                registered_nodes.append(node_address)
            except Exception as e:
                errors.append(f"Failed to register {node_address}: {str(e)}")
        
        response = {
            'message': 'Nodes registration completed',
            'registered_nodes': registered_nodes,
            'errors': errors,
            'total_nodes': [node.address for node in blockchain.db.query(Node).all()]
        }
        return jsonify(response), 201
        
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"Error in register_nodes: {error_traceback}")
        return jsonify({
            "error": str(e),
            "traceback": error_traceback
        }), 500

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    try:
        replaced = blockchain.resolve_conflicts()
        
        if replaced:
            response = {
                'message': 'Our chain was replaced',
                'new_chain': blockchain.get_chain()
            }
        else:
            response = {
                'message': 'Our chain is authoritative',
                'chain': blockchain.get_chain()
            }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 