import os
import shutil
from wallet import Wallet

def cleanup_wallets():
    """Clean up wallet files and organize them"""
    print("Starting wallet cleanup...")
    
    # Create wallets directory if it doesn't exist
    if not os.path.exists('wallets'):
        os.makedirs('wallets')
        
    # Get all potential wallet files
    wallet_files = []
    for file in os.listdir('.'):
        if file.endswith(('.pem', '.pen')) and os.path.isfile(file):
            wallet_files.append(file)
            
    print(f"Found {len(wallet_files)} potential wallet files")
    
    # Process each file
    valid_wallets = []
    invalid_files = []
    
    for file in wallet_files:
        try:
            # Try to load the wallet to verify it's valid
            wallet = Wallet.load_from_file(file)
            
            # Create new filename based on address
            new_filename = f"wallet_{wallet.address[:8]}.pem"
            new_path = os.path.join('wallets', new_filename)
            
            # Move to wallets directory
            shutil.move(file, new_path)
            valid_wallets.append({
                'original_file': file,
                'new_file': new_filename,
                'address': wallet.address
            })
            print(f"✓ Valid wallet moved: {file} -> {new_filename}")
            
        except Exception as e:
            print(f"✗ Invalid wallet file {file}: {str(e)}")
            invalid_files.append(file)
            
            # Move invalid files to 'invalid' directory
            if not os.path.exists('invalid_wallets'):
                os.makedirs('invalid_wallets')
            try:
                shutil.move(file, os.path.join('invalid_wallets', file))
                print(f"  Moved to invalid_wallets directory")
            except Exception as move_error:
                print(f"  Error moving file: {str(move_error)}")
    
    # Print summary
    print("\nCleanup Summary:")
    print(f"Valid wallets: {len(valid_wallets)}")
    print(f"Invalid files: {len(invalid_files)}")
    
    if valid_wallets:
        print("\nValid Wallets:")
        for wallet in valid_wallets:
            print(f"- {wallet['new_file']} (Address: {wallet['address']})")
    
    if invalid_files:
        print("\nInvalid Files (moved to invalid_wallets/):")
        for file in invalid_files:
            print(f"- {file}")

if __name__ == "__main__":
    cleanup_wallets() 