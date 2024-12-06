# Python Blockchain Implementation

A decentralized blockchain system with wallet management, mining capabilities, and secure transactions.

## Quick Start

1. **Start Main Node (Terminal 1)**
```bash
python node.py
# Running on http://localhost:5000
```

2. **Start Web Interface (Terminal 2)**
```bash
python web_interface.py
# Running on http://localhost:5001
```

## Creating and Using Wallets

1. **Create New Wallet**
   - Web Interface: Click "New Wallet" button
   - CLI: `python blockchain_cli.py create_wallet`

2. **Load Existing Wallet**
   ```bash
   # Example loading existing wallets
   python blockchain_cli.py
   (blockchain) load_wallet aine.pem
   (blockchain) load_wallet chr.pem
   (blockchain) load_wallet mig.pem
   ```

## Making Transactions

1. **Through Web Interface**
   - Go to http://localhost:5001
   - Enter recipient's address (32-character wallet address)
   - Enter amount
   - Click "Send"

2. **Through CLI**
   ```bash
   (blockchain) send <recipient_address> <amount>
   # Example:
   (blockchain) send a6a1ab42e7d7691fc6be2bbd515227d2 1.0
   ```

## Mining Blocks

1. **Web Interface**
   - Click "Mine New Block" button
   - Mining reward: 1 coin

2. **CLI Mining**
   ```bash
   (blockchain) mine
   ```

## Checking Balances

1. **Web Interface**
   - Balance shown on main page
   - Transaction history visible

2. **CLI Balance**
   ```bash
   (blockchain) balance
   ```

## Database Structure

- **Blocks**: Stores blockchain blocks
- **Transactions**: Records all transactions
- **Nodes**: Tracks network nodes
- **Wallets**: Manages wallet information

## Example Workflow

1. **Start System**
   ```bash
   # Terminal 1
   python node.py

   # Terminal 2
   python web_interface.py
   ```

2. **Create/Load Wallets**
   ```bash
   # Load existing wallets
   (blockchain) load_wallet aine.pem
   ✅ Wallet loaded successfully
   Address: a6a1ab42e7d7691fc6be2bbd515227d2
   ```

3. **Mine Some Coins**
   ```bash
   (blockchain) mine
   ⛏️ Mining new block...
   ✅ Block mined successfully!
   ```

4. **Send Transaction**
   ```bash
   (blockchain) send a50e79cfa9b3128566e27b09f3a9a812 1.0
   ✅ Transaction sent successfully!
   ```

## Security Notes

- Keep wallet files (*.pem) secure
- Never share private keys
- Backup wallet files
- Verify recipient addresses

## File Descriptions

- `node.py`: Main blockchain node
- `models.py`: Database models and schema
- `wallet.py`: Wallet management and transactions
- `templates/index.html`: Web interface template

## Common Issues

1. **Transaction Failed**
   - Check sender balance
   - Verify recipient address
   - Ensure node is running

2. **Mining Issues**
   - Verify node connection
   - Check wallet is loaded

3. **Wallet Issues**
   - Ensure .pem file exists
   - Check file permissions
   - Verify wallet format