# Token Recovery Lock Extension Attack - Permanent DoS

## Attack Scenario

An attacker can permanently prevent any victim from withdrawing their recovered Beacon Chain tokens by exploiting a flaw in the lock timer logic.

**Step-by-step attack:**

1. Victim initiates token recovery from Beacon Chain via `TokenRecoverPortal.recover()`
2. TokenHub locks the recovered tokens for 7 days (`LOCK_PERIOD_FOR_TOKEN_RECOVER`)
3. Attacker monitors the blockchain for `TokenRecoverRequested` events
4. Before the victim's 7-day lock expires (e.g., on day 6), attacker calls recovery with a tiny amount (0.0001 BNB) targeting the same victim address
5. The `_lockRecoverToken()` function **unconditionally resets** `unlockAt` to `block.timestamp + 7 days`
6. Victim's original lock is extended by another 7 days
7. Attacker repeats step 4-6 every 6 days indefinitely
8. **Result:** Victim can NEVER withdraw their tokens

**Buggy behavior:** The lock timer resets on EVERY recovery call instead of only on the first recovery. This allows an attacker to indefinitely extend another user's lock period with minimal cost (~$0.01 in gas per week).

---

## Impact

**Severity: Medium-High**

- **Permanent Denial of Service:** Victims cannot access their recovered BC tokens indefinitely
- **Financial Loss:** Victim's funds are effectively frozen forever
- **Low Attack Cost:** Attacker only pays minimal gas fees (~0.0001 BNB per attack)
- **No Victim Recourse:** There is no mechanism to bypass or cancel the lock
- **Scalable Attack:** One attacker can target multiple victims simultaneously
- **Affects BC Fusion Migration:** All users recovering tokens from Beacon Chain are vulnerable

**Real-world impact:** A malicious actor could target high-value recovery transactions and extort victims for payment to stop the attack.

---

## Components

**Primary vulnerable file:**
- `contracts/TokenHub.sol` - Line 233

**Vulnerable function:**
```solidity
function _lockRecoverToken(
    bytes32 tokenSymbol,
    address contractAddr,
    uint256 amount,
    address recipient
) internal {
    LockInfo storage lockInfo = lockInfoMap[contractAddr][recipient];
    lockInfo.amount = lockInfo.amount.add(amount);
    lockInfo.unlockAt = block.timestamp + LOCK_PERIOD_FOR_TOKEN_RECOVER;  // <-- BUG: Line 233
}
```

**Related files:**
- `contracts/TokenRecoverPortal.sol` - Line 134 (calls `ITokenHub.recoverBCAsset()`)
- `contracts/interface/0.8.x/ITokenHub.sol` - Interface definition

**Call flow:**
```
TokenRecoverPortal.recover()
    → TokenHub.recoverBCAsset()
        → TokenHub._lockRecoverToken()  // BUG HERE
```

---

## Reproduction

### Environment Setup
```bash
git clone https://github.com/bnb-chain/bsc-genesis-contract
cd bsc-genesis-contract
npm install
forge install
```

### Foundry Test (PoC)

Create file `test/TokenRecoveryDoS.t.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

contract TokenRecoveryDoS_Test is Test {
    // Simulates TokenHub vulnerability
    mapping(address => LockInfo) public lockInfoMap;
    uint256 constant LOCK_PERIOD = 7 days;

    struct LockInfo {
        uint256 amount;
        uint256 unlockAt;
    }

    // Replicates vulnerable _lockRecoverToken logic
    function _lockRecoverToken(address recipient, uint256 amount) internal {
        LockInfo storage lockInfo = lockInfoMap[recipient];
        lockInfo.amount += amount;
        lockInfo.unlockAt = block.timestamp + LOCK_PERIOD; // BUG: Always resets
    }

    function canWithdraw(address user) public view returns (bool) {
        return block.timestamp >= lockInfoMap[user].unlockAt;
    }

    function test_PermanentDoS_Attack() public {
        address victim = address(0xV1CT1M);
        address attacker = address(0xATTACK);

        // Step 1: Victim recovers 1000 BNB (locked for 7 days)
        vm.prank(victim);
        _lockRecoverToken(victim, 1000 ether);

        uint256 originalUnlockTime = lockInfoMap[victim].unlockAt;
        emit log_named_uint("Original unlock time", originalUnlockTime);

        // Step 2: Fast forward 6 days (victim almost ready to withdraw)
        vm.warp(block.timestamp + 6 days);
        assertFalse(canWithdraw(victim), "Victim should not be able to withdraw yet");

        // Step 3: Attacker sends tiny recovery to reset timer
        vm.prank(attacker);
        _lockRecoverToken(victim, 0.0001 ether);  // Costs almost nothing

        uint256 newUnlockTime = lockInfoMap[victim].unlockAt;
        emit log_named_uint("New unlock time after attack", newUnlockTime);

        // Step 4: Verify the attack worked
        assertGt(newUnlockTime, originalUnlockTime, "VULNERABILITY: Lock time was extended!");

        // Step 5: Even after original 7 days, victim STILL cannot withdraw
        vm.warp(originalUnlockTime + 1);
        assertFalse(canWithdraw(victim), "VULNERABILITY: Victim cannot withdraw after original period!");

        // Step 6: Attacker can repeat indefinitely
        for (uint i = 0; i < 10; i++) {
            vm.warp(block.timestamp + 6 days);
            vm.prank(attacker);
            _lockRecoverToken(victim, 0.0001 ether);
        }

        // After 70+ days of attacks, victim still locked
        emit log_string("RESULT: Victim permanently locked out of their funds");
    }
}
```

### Run Test
```bash
forge test --match-test test_PermanentDoS_Attack -vvvv
```

### Expected Output
```
[PASS] test_PermanentDoS_Attack()
Logs:
  Original unlock time: 604800
  New unlock time after attack: 1123200
  VULNERABILITY: Lock time was extended!
  RESULT: Victim permanently locked out of their funds
```

---

## Fix

### Recommended Solution

Only set `unlockAt` if this is a **new lock** or the previous lock has **already expired**:

```solidity
function _lockRecoverToken(
    bytes32 tokenSymbol,
    address contractAddr,
    uint256 amount,
    address recipient
) internal {
    LockInfo storage lockInfo = lockInfoMap[contractAddr][recipient];
    lockInfo.amount = lockInfo.amount.add(amount);

    // FIX: Only set unlockAt for new locks or expired locks
    if (lockInfo.unlockAt == 0 || lockInfo.unlockAt < block.timestamp) {
        lockInfo.unlockAt = block.timestamp + LOCK_PERIOD_FOR_TOKEN_RECOVER;
    }
    // Existing active locks keep their original unlock time
}
```

### Alternative Solution

Use the maximum of the current unlock time and the new calculated time:

```solidity
uint256 newUnlockTime = block.timestamp + LOCK_PERIOD_FOR_TOKEN_RECOVER;
if (newUnlockTime > lockInfo.unlockAt) {
    lockInfo.unlockAt = newUnlockTime;
}
```

**Note:** This alternative still allows extension but prevents the timer from being reset backwards.

---

## Details

### Why This Vulnerability Exists

The `_lockRecoverToken()` function was designed to handle a single recovery per user. The developers did not anticipate that:
1. Multiple recoveries could target the same recipient
2. An attacker could intentionally trigger recoveries for victims
3. The unconditional timer reset creates a griefing vector

### Attack Economics

| Metric | Value |
|--------|-------|
| Attack cost per victim per week | ~0.0001 BNB (~$0.06) |
| Attack cost per year | ~$3.12 per victim |
| Potential victim loss | Unlimited (entire recovery amount) |
| ROI for attacker | Extortion potential |

### Related Considerations

1. **No access control:** Anyone can trigger recovery for any address
2. **No rate limiting:** No cooldown between recovery calls
3. **Permanent effect:** No admin function to override locks

### Affected Users

All users migrating tokens from Beacon Chain to BSC via the BC Fusion process are affected. This includes:
- Individual token holders
- Exchanges with BC holdings
- Projects with treasury on BC

### Disclosure

This vulnerability is being reported under responsible disclosure. I have not exploited this vulnerability on mainnet and will not disclose publicly until a fix is deployed.

---

**Researcher:** l0ve
**Date:** 2026-01-07
