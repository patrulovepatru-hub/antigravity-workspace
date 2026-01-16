# BSC Genesis Contracts Security Audit Report

**Target:** BNB Chain Bug Bounty Program
**Repository:** https://github.com/bnb-chain/bsc-genesis-contract
**Date:** 2026-01-07
**Auditor:** l0ve

---

## Executive Summary

Audit of BSC genesis contracts including staking, slashing, governance, and token recovery modules. Found 9 potential vulnerabilities across different severity levels.

---

## Contracts Analyzed

| Contract | Size | Priority | Status |
|----------|------|----------|--------|
| StakeHub.sol | 52KB | Critical | Analyzed |
| BSCValidatorSet.sol | 48KB | Critical | Pending |
| SlashIndicator.sol | 17KB | High | Analyzed |
| StakeCredit.sol | 13KB | High | Analyzed |
| TokenHub.sol | 14KB | High | Analyzed |
| TokenRecoverPortal.sol | 11KB | Medium | Analyzed |
| BSCGovernor.sol | 13KB | Medium | Pending |
| GovToken.sol | 4KB | Medium | Analyzed |

---

## HIGH SEVERITY FINDINGS

### [H-01] Potential Reentrancy in StakeHub.redelegate()

**File:** `contracts/StakeHub.sol:553-599`

**Description:**
The `redelegate()` function makes multiple external calls before completing state changes:

```solidity
function redelegate(...) external ... enableReceivingFund {
    // ...
    uint256 bnbAmount = IStakeCredit(srcValInfo.creditContract).unbond(delegator, shares); // EXTERNAL CALL 1
    // checks after call...
    (bool success,) = dstValInfo.creditContract.call{ value: feeCharge }(""); // EXTERNAL CALL 2
    uint256 newShares = IStakeCredit(dstValInfo.creditContract).delegate{ value: bnbAmount }(delegator); // EXTERNAL CALL 3
}
```

**Impact:** Potential cross-contract reentrancy if creditContract is compromised or malicious.

**Recommendation:** Implement checks-effects-interactions pattern or add reentrancy guard.

**Status:** Needs PoC

---

### [H-02] Unchecked Return Value in distributeReward()

**File:** `contracts/StakeHub.sol:656`

```solidity
SYSTEM_REWARD_ADDR.call{ value: msg.value }(""); // Return value not checked
```

**Impact:** If the call fails, funds remain trapped in the contract with no error indication.

**Recommendation:** Check return value or use `transfer()`.

**Status:** Confirmed

---

## MEDIUM SEVERITY FINDINGS

### [M-01] Validator Array Unbounded Growth

**File:** `contracts/SlashIndicator.sol:121`

```solidity
validators.push(validator); // No size limit
```

**Impact:** Array can grow indefinitely. The `clean()` function has O(n) complexity and may hit gas limits.

**Status:** Needs further analysis

---

### [M-02] Flash Loan Attack Vector on Governance

**File:** `contracts/GovToken.sol:86-98`

**Attack Vector:**
1. Flash loan BNB
2. Delegate to validator (get shares)
3. Sync govBNB (get voting power)
4. Vote on governance proposal
5. Undelegate and repay flash loan

**Mitigation:** 7-day unbondPeriod should prevent this, but needs verification for bypass.

**Status:** Needs PoC

---

### [M-03] Token Recovery Timing Extension Attack

**File:** `contracts/TokenHub.sol:230-236`

```solidity
function _lockRecoverToken(...) internal {
    lockInfo.amount = lockInfo.amount.add(amount);
    lockInfo.unlockAt = block.timestamp + LOCK_PERIOD_FOR_TOKEN_RECOVER; // Resets each time
}
```

**Impact:** Attacker can extend victim's lock period indefinitely by sending small amounts.

**Status:** Needs PoC

---

### [M-04] Slash Reward Manipulation

**File:** `contracts/SlashIndicator.sol:260`

```solidity
uint256 amount = (address(SYSTEM_REWARD_ADDR).balance * felonySlashRewardRatio) / 100;
```

**Impact:** Attacker can inflate reward by sending funds to SYSTEM_REWARD_ADDR before reporting.

**Status:** Confirmed

---

## LOW SEVERITY FINDINGS

### [L-01] Hash Collision Risk in Merkle Proof

**File:** `contracts/TokenRecoverPortal.sol:119`

```solidity
bytes32 node = keccak256(abi.encodePacked(ownerAddr, tokenSymbol, amount));
```

**Impact:** `abi.encodePacked` with variable types can cause collisions (anti-pattern).

---

### [L-02] Gas Griefing in addNodeIDs()

**File:** `contracts/StakeHub.sol:1062-1080`

O(n^2) complexity in duplicate checking loops. Limited by maxNodeIDs=5.

---

### [L-03] Integer Division Precision Loss

**File:** `contracts/StakeCredit.sol:228-242`

```solidity
return (bnbAmount * totalSupply()) / totalPooledBNB;
```

**Impact:** Rounding errors in extreme cases.

---

## Severity Summary

| Severity | Count | Bounty Range |
|----------|-------|--------------|
| High | 2 | $10,000-$100,000 |
| Medium | 4 | $2,000-$10,000 |
| Low | 3 | $500-$2,000 |

---

## Next Steps

- [ ] Develop PoC for H-01 (Reentrancy)
- [ ] Verify M-02 (Flash loan) on mainnet fork
- [ ] Complete BSCValidatorSet.sol analysis
- [ ] Write Foundry exploit tests
- [ ] Prepare bug bounty submission

---

## References

- Bug Bounty: https://bugcrowd.com/binance
- BNB Chain Bounty: https://bugbounty.bnbchain.org/
- Repository: https://github.com/bnb-chain/bsc-genesis-contract
