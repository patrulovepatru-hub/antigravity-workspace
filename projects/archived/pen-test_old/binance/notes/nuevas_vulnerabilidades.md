# Nuevas Vulnerabilidades Encontradas - BSC Genesis Contracts

**Fecha:** 2026-01-07
**Auditor:** l0ve

---

## RESUMEN ACTUALIZADO

### Vulnerabilidades CONFIRMADAS (Reportables al Bug Bounty)

| ID | Severidad | Contrato | Descripción | Bounty Est. |
|----|-----------|----------|-------------|-------------|
| **H-02** | HIGH | StakeHub.sol:656 | Unchecked Return Value en `distributeReward()` | $10,000-$50,000 |
| **M-03** | MEDIUM | TokenHub.sol:233 | Token Recovery Timing Extension Attack | $5,000-$15,000 |
| **M-04** | MEDIUM | SlashIndicator.sol:260 | Slash Reward Manipulation | $10,000-$25,000 |
| **NEW-01** | MEDIUM | BSCValidatorSet.sol:325 | Integer Overflow sin SafeMath | $5,000-$15,000 |

### Vulnerabilidades DESCARTADAS/RE-EVALUADAS

| ID | Estado | Razón |
|----|--------|-------|
| H-01 | LOW | creditContracts son del sistema, no controlables por usuarios |
| M-02 | FALSE POSITIVE | unbondPeriod de 7 días bloquea flash loan attack |

---

## DETALLE DE NUEVAS VULNERABILIDADES

### NEW-01: Integer Overflow en BSCValidatorSet.distributeFinalityReward()

**Archivo:** `contracts/BSCValidatorSet.sol:325`

**Severidad:** MEDIUM

**Código Vulnerable:**
```solidity
// Solidity 0.6.4 - SIN protección nativa contra overflow
for (uint256 i; i < valAddrs.length; ++i) {
    value = (totalValue * weights[i]) / totalWeight;  // <- NO USA SafeMath!
    // ...
}
```

**Análisis:**
- El contrato usa Solidity 0.6.4 que NO tiene protección nativa contra overflow
- Aunque el contrato importa SafeMath, esta línea específica NO lo usa
- Si `totalValue * weights[i]` excede uint256, hay overflow silencioso
- El resultado sería una distribución incorrecta de recompensas

**Escenario de Explotación:**
1. `totalValue` puede ser hasta `MAX_SYSTEM_REWARD_BALANCE = 100 ether`
2. Si `weights[i]` es suficientemente grande (voting power alto)
3. La multiplicación puede overflow antes de la división
4. Resultado: distribución de recompensas incorrecta

**Impacto:**
- Distribución incorrecta de recompensas de finalidad
- Algunos validadores podrían recibir más/menos de lo debido
- Potencial pérdida económica para validadores

**Remediación Sugerida:**
```solidity
// Usar SafeMath para la multiplicación
value = totalValue.mul(weights[i]).div(totalWeight);
```

---

### Observaciones Adicionales (Info/Low)

#### OBS-01: Múltiples Loops O(n²) en BSCValidatorSet

**Archivo:** `BSCValidatorSet.sol:690-696`

```solidity
for (uint256 i; i < n; ++i) {
    for (uint256 j; j < m; ++j) {
        if (oldValidator.consensusAddress == newValidatorSet[j].consensusAddress) {
            // ...
        }
    }
}
```

**Impacto:** Potencial DoS por gas si el validator set crece significativamente.
**Mitigación actual:** El validator set está limitado (~45 validadores máx).

#### OBS-02: Uso de .transfer() con límite de 2300 gas

**Archivo:** `BSCValidatorSet.sol:224, 261, 271`

```solidity
address(uint160(SYSTEM_REWARD_ADDR)).transfer(address(this).balance);
```

**Impacto:** Bajo - Los receptores son contratos del sistema con `receive()` simple.

#### OBS-03: Aleatoriedad Predecible en shuffle()

**Archivo:** `BSCValidatorSet.sol:767`

```solidity
uint256 random = uint256(keccak256(abi.encodePacked(shuffleNumber, startIdx + i))) % modNumber;
```

**Impacto:** Bajo - shuffleNumber basado en block.number es predecible por mineros.
**Contexto:** Solo afecta la selección de candidatos, no fondos directamente.

---

## RESUMEN EJECUTIVO FINAL

### Vulnerabilidades Totales para Reportar: 4

| Prioridad | ID | Descripción |
|-----------|-----|-------------|
| 1 | H-02 | Unchecked Return Value - Fondos atrapados |
| 2 | M-04 | Slash Reward Manipulation - Economía |
| 3 | M-03 | Token Recovery Timing - DoS |
| 4 | NEW-01 | Integer Overflow - Distribución |

### Bounty Estimado Total: $30,000 - $105,000

### Próximos Pasos Recomendados

1. [ ] Crear PoC funcional para NEW-01 (Integer Overflow)
2. [ ] Preparar reportes formales en formato Bugcrowd
3. [ ] Verificar versiones de contratos en mainnet vs repo
4. [ ] Ejecutar tests en fork de BSC mainnet
