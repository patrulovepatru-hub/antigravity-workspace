# Web3 Vulnerability Patterns

## Smart Contract Vulnerabilities

### Reentrancy
- Classic: external call before state update
- Cross-function: shared state across functions
- Cross-contract: callbacks between contracts
- Read-only: view functions returning stale data

### Access Control
- Missing onlyOwner/admin checks
- Unprotected initializers (proxy patterns)
- Signature replay attacks
- tx.origin vs msg.sender

### Logic Errors
- Incorrect math/rounding (favor protocol or user?)
- Off-by-one errors in loops
- Incorrect comparison operators
- Missing input validation

### Oracle Manipulation
- Flash loan price manipulation
- TWAP window too short
- Spot price vs time-weighted
- Stale price data

### Economic Exploits
- Flash loan attacks
- Sandwich attacks
- Frontrunning vulnerabilities
- MEV extraction

### Token Issues
- ERC20 fee-on-transfer tokens
- Rebasing tokens breaking accounting
- ERC777 hooks (reentrancy vector)
- Missing return value checks

### Upgradability
- Storage collision in proxies
- Unprotected upgrade functions
- Implementation self-destruct

## DeFi-Specific

### Lending
- Liquidation threshold manipulation
- Interest rate model exploits
- Collateral factor manipulation

### AMMs/DEXs
- Slippage exploitation
- LP token pricing errors
- Imbalanced pool attacks

### Bridges
- Message validation bypass
- Replay across chains
- Signature verification flaws

### Staking/Vaults
- Share inflation attacks (first depositor)
- Reward calculation errors
- Withdrawal queue manipulation

## Checklist Questions
- [ ] Can an attacker drain funds?
- [ ] Can an attacker grief other users?
- [ ] Can an attacker manipulate prices/oracles?
- [ ] Are there flash loan vectors?
- [ ] Is access control properly implemented?
- [ ] Are all external calls safe?
- [ ] Is the math correct for edge cases?
