from blockchain import Blockchain
import json

def main():
    # Initialize blockchain
    blockchain = Blockchain()

    # Add some transactions
    blockchain.new_transaction("Alice", "Bob", 50)
    blockchain.new_transaction("Bob", "Charlie", 30)

    # Mine a new block
    last_block = blockchain.get_last_block()
    proof = blockchain.proof_of_work(last_block)
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(proof, previous_hash)

    print("New block added:")
    print(json.dumps(block, indent=2))
    
    # Verify the blockchain
    print("\nBlockchain valid?", blockchain.is_chain_valid(blockchain.chain))

if __name__ == "__main__":
    main() 