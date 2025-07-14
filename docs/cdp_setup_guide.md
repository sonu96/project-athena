# CDP (Coinbase Developer Platform) Setup Guide

This guide will help you set up CDP AgentKit for the Athena DeFi Agent.

## Prerequisites

- Python 3.10+ (Already installed ✅)
- CDP SDK (Already installed ✅)
- Coinbase Developer Platform Account

## Step 1: Create a Coinbase Developer Platform Account

1. Go to [https://portal.cdp.coinbase.com/](https://portal.cdp.coinbase.com/)
2. Sign up or log in with your Coinbase account
3. Complete any required verification steps

## Step 2: Create an API Key

1. In the CDP Portal, navigate to **API Keys**
2. Click **"Create API Key"**
3. Configure your API key:
   - **Name**: `athena-defi-agent` (or any descriptive name)
   - **Network**: Select `Base Sepolia` (testnet for Phase 1)
   - **Permissions**: 
     - ✅ Read wallet data
     - ✅ Create wallets
     - ✅ Request testnet tokens
     - ✅ Read blockchain data
     - ❌ Execute transactions (not needed for Phase 1)

4. Click **"Create"**
5. **IMPORTANT**: Save the API credentials shown:
   - `API Key Name`: This is your `CDP_API_KEY_NAME`
   - `Private Key`: This is your `CDP_API_KEY_SECRET`
   
   ⚠️ **The private key is shown only once! Save it securely.**

## Step 3: Configure Environment Variables

1. Open your `.env` file (or create from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Add your CDP credentials:
   ```env
   # CDP Configuration
   CDP_API_KEY_NAME="your-api-key-name-here"
   CDP_API_KEY_SECRET="-----BEGIN EC PRIVATE KEY-----
   your-private-key-content-here
   -----END EC PRIVATE KEY-----"
   
   # Network Configuration
   NETWORK="base-sepolia"  # Using testnet for Phase 1
   ```

   **Note**: The private key is multi-line. Make sure to include the entire key including the BEGIN/END markers.

## Step 4: Test Your Setup

Run this test script to verify CDP is working:

```python
# test_cdp.py
import asyncio
from src.integrations.cdp_integration import CDPIntegration

async def test_cdp():
    cdp = CDPIntegration()
    
    # Initialize wallet
    print("Initializing wallet...")
    success = await cdp.initialize_wallet()
    if not success:
        print("❌ Failed to initialize wallet")
        return
    
    # Get wallet info
    print("\nGetting wallet balance...")
    balance = await cdp.get_wallet_balance()
    print(f"Wallet balance: {balance}")
    
    # Request testnet tokens
    print("\nRequesting testnet tokens...")
    faucet_success = await cdp.get_testnet_tokens()
    if faucet_success:
        print("✅ Testnet tokens requested successfully")
    else:
        print("❌ Failed to request testnet tokens")

if __name__ == "__main__":
    asyncio.run(test_cdp())
```

Run with:
```bash
cd /Users/abhisonu/Projects/project\ Athena
source venv310/bin/activate
python test_cdp.py
```

## Step 5: Understanding the Wallet File

After initialization, CDP creates a wallet file at:
```
wallet_data/athena_wallet.json
```

This file contains:
- Wallet seed phrase (encrypted)
- Wallet addresses
- Network information

⚠️ **Keep this file secure!** It contains your wallet's private keys.

## Step 6: Base Sepolia Testnet

The agent operates on Base Sepolia testnet in Phase 1:

- **Network Name**: Base Sepolia
- **Chain ID**: 84532
- **RPC URL**: https://sepolia.base.org
- **Block Explorer**: https://sepolia.basescan.org/
- **Faucet**: Automatically requested via CDP

### Getting Additional Testnet Tokens

If you need more testnet tokens:
1. The agent automatically requests tokens on startup
2. You can also use: https://www.coinbase.com/faucets/base-sepolia-faucet

## Step 7: Monitor Your Agent

Once running, you can monitor your agent's wallet:
1. Check the wallet address in logs
2. View on Base Sepolia explorer: `https://sepolia.basescan.org/address/[your-wallet-address]`
3. Monitor balance changes as the agent operates

## Troubleshooting

### "CDP SDK not available" Error
- Ensure you're using Python 3.10+
- Activate the correct virtual environment: `source venv310/bin/activate`

### "Invalid API credentials" Error
- Double-check your CDP_API_KEY_NAME and CDP_API_KEY_SECRET
- Ensure the private key includes BEGIN/END markers
- Make sure there are no extra spaces or line breaks

### "Network error" Issues
- CDP requires internet connection
- Firewall may block CDP API calls
- Try using a different network

### Rate Limiting
- CDP has rate limits on API calls
- The agent respects these limits automatically
- If you hit limits, wait a few minutes

## Next Steps

1. Run the agent with CDP enabled:
   ```bash
   python -m src.core.agent
   ```

2. The agent will:
   - Create/load a wallet on Base Sepolia
   - Request initial testnet tokens
   - Monitor wallet balance in each consciousness cycle
   - Adjust behavior based on treasury balance

3. Monitor the agent's emotional state as treasury changes!

## Security Notes

- **Never share your CDP API private key**
- **Keep wallet_data directory secure**
- **Use testnet only for Phase 1**
- **Don't send real funds to testnet addresses**

## Resources

- [CDP Documentation](https://docs.cdp.coinbase.com/)
- [Base Network Docs](https://docs.base.org/)
- [CDP SDK Python Reference](https://github.com/coinbase/cdp-sdk-python)