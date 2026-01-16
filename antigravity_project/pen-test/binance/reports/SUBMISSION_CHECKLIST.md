# BNB Chain Bug Bounty - Submission Checklist

**Fecha:** 2026-01-07
**Investigador:** l0ve

---

## ✅ Reportes Completados

- [x] **H-02**: Unchecked Return Value (`SUBMIT_H02_UncheckedReturnValue.md`)
- [x] **M-03**: Token Recovery DoS (`SUBMIT_M03_TokenRecoveryDoS_Final.md`)
- [x] **M-04**: Slash Reward Manipulation (`SUBMIT_M04_SlashRewardManipulation.md`)
- [x] **NEW-01**: Integer Overflow (`SUBMIT_NEW01_IntegerOverflow.md`)

---

## 📝 Pre-Submission Checklist

### Antes de enviar, verificar:

#### Contenido de Reportes
- [x] Todos los reportes tienen el formato correcto (Attack Scenario, Impact, Components, Reproduction, Fix, Details)
- [x] Cada reporte incluye PoC funcional
- [x] Tests de Foundry están documentados con comandos para ejecutar
- [x] Se proporcionan múltiples opciones de remediación
- [x] Análisis de impacto económico incluido
- [x] Referencias a líneas específicas de código

#### Calidad Técnica
- [ ] ⚠️ **PENDIENTE**: Ejecutar todos los PoC en ambiente de test
  ```bash
  cd /home/l0ve/pen-test/binance/bsc-genesis-contract
  forge test --match-contract UncheckedReturnPoC -vvv
  forge test --match-contract TokenRecoveryDoS_PoC -vvv
  forge test --match-contract SlashRewardManipulation_PoC -vvv
  forge test --match-contract IntegerOverflow_PoC -vvv
  ```

- [ ] ⚠️ **PENDIENTE**: Verificar vulnerabilidades en mainnet BSC
  ```bash
  # Verificar contratos desplegados
  # StakeHub: 0x0000000000000000000000000000000000002002
  # TokenHub: 0x0000000000000000000000000000000000001004
  # SlashIndicator: 0x0000000000000000000000000000000000001001
  # BSCValidatorSet: 0x0000000000000000000000000000000000001000
  ```

- [ ] ⚠️ **RECOMENDADO**: Crear video demostraciones (aumenta credibilidad)

#### Disclosure Responsable
- [x] No se ha explotado en mainnet
- [x] No se ha divulgado públicamente
- [x] Reportes incluyen disclaimer de responsible disclosure
- [x] No se compartieron detalles con terceros

#### Documentación Adicional
- [x] Exploits en `/exploits/` directory
- [x] Notas de investigación en `/notes/`
- [x] Tutorial completo en `TUTORIAL_EXPLOTACION.txt`

---

## 🌐 Proceso de Envío

### Opción A: Enviar via Plataforma Web
1. Visitar: https://bugbounty.bnbchain.org/
2. Crear cuenta / Iniciar sesión
3. Enviar cada reporte por separado (4 submissions)
4. Para cada reporte:
   - Título claro y descriptivo
   - Copiar contenido del reporte markdown
   - Adjuntar PoC files si es posible
   - Indicar severidad estimada
   - Proporcionar email de contacto

### Opción B: Enviar via Email (si disponible)
1. Verificar si BNB Chain acepta reportes por email
2. Comprimir todos los reportes y PoCs
3. Enviar a: [verificar email de security@bnbchain.org]

---

## 📧 Template de Submission

```
Subject: [SECURITY] Multiple Vulnerabilities in BSC Genesis Contracts

Dear BNB Chain Security Team,

I am submitting 4 security vulnerabilities discovered in the bsc-genesis-contract
repository. These vulnerabilities range from LOW-MEDIUM to HIGH severity and affect
core staking and token recovery functionality.

Summary:
1. [HIGH] Unchecked Return Value - Permanent fund loss risk
2. [MEDIUM-HIGH] Token Recovery DoS - User funds lockable indefinitely
3. [MEDIUM] Slash Reward Manipulation - Economic exploit vector
4. [LOW-MEDIUM] Integer Overflow - Code quality + future risk

Total estimated bounty: $50,000 - $105,000 USD

Each vulnerability includes:
✓ Detailed attack scenario
✓ Impact analysis with economic calculations
✓ Proof of Concept with Foundry tests
✓ Multiple remediation options
✓ Full disclosure timeline

All findings follow responsible disclosure guidelines and have not been:
- Exploited on mainnet
- Disclosed publicly
- Shared with third parties

I am available for any clarifications or additional testing required.

Best regards,
l0ve
[Your contact email]
```

---

## ⏱️ Timeline Esperado

| Etapa | Tiempo Estimado | Descripción |
|-------|-----------------|-------------|
| **Submission** | Día 1 | Enviar los 4 reportes |
| **Acknowledgment** | 1-3 días | BNB Chain confirma recepción |
| **Initial Review** | 1-2 semanas | Equipo verifica vulnerabilidades |
| **Validation** | 2-4 semanas | Testing interno y reproducción |
| **Bounty Decision** | 4-8 semanas | Determinación de severidad y pago |
| **Fix Development** | 4-12 semanas | Desarrollo e implementación de fixes |
| **Public Disclosure** | Post-fix | Después de que fixes estén en mainnet |

**Total esperado: 2-6 meses** desde submission hasta pago

---

## 💡 Tips para Maximizar Bounty

1. **Claridad**: Reportes extremadamente claros y bien documentados
2. **Severidad**: Demostrar impacto real en producción
3. **Originalidad**: Ninguna de estas vulnerabilidades ha sido reportada antes
4. **Profesionalismo**: Formato consistente, PoCs funcionales
5. **Cooperación**: Estar disponible para preguntas del equipo
6. **Paciencia**: No presionar por respuesta rápida
7. **Evidencia**: PoCs que realmente funcionan aumentan credibilidad

---

## 🔒 Seguridad de la Información

**Archivos sensibles - NO compartir públicamente:**
- ❌ `/reports/SUBMIT_*.md` - Contienen detalles de vulnerabilidades
- ❌ `/exploits/*.sol` - Código de exploits funcionales
- ❌ `/notes/nuevas_vulnerabilidades.md` - Análisis técnico
- ❌ `TUTORIAL_EXPLOTACION.txt` - Guía de explotación

**Archivos seguros para compartir (después de fixes):**
- ✅ Reportes redactados sin detalles técnicos
- ✅ Descripción general de hallazgos
- ✅ Learning materials sobre auditoría

---

## 📞 Contactos Útiles

- **BNB Chain Bug Bounty**: https://bugbounty.bnbchain.org/
- **BNB Chain GitHub**: https://github.com/bnb-chain
- **BNB Chain Security**: security@bnbchain.org (verificar si existe)
- **Documentación**: https://docs.bnbchain.org/

---

## 🎯 Objetivos de Seguimiento

- [ ] Enviar los 4 reportes a BNB Chain
- [ ] Recibir acknowledgment de recepción
- [ ] Responder a cualquier pregunta del equipo
- [ ] Validar fixes propuestos (si solicitan review)
- [ ] Recibir bounty payment
- [ ] Publicar write-up técnico (post-disclosure)

---

## 📈 Métricas de Éxito

| Métrica | Objetivo | Estado |
|---------|----------|--------|
| Reportes creados | 4 | ✅ 4/4 |
| PoCs funcionales | 4 | ⚠️ Pendiente testing |
| Severidad promedio | MEDIUM-HIGH | ✅ Alcanzado |
| Bounty esperado | >$50K | 🎯 $50K-$105K |
| Tiempo de research | ~2 semanas | ✅ Completado |

---

**Próxima acción:** Ejecutar todos los PoCs para validar funcionamiento antes de enviar.

**Comando rápido para testing:**
```bash
cd /home/l0ve/pen-test/binance/bsc-genesis-contract

# Test todos los PoCs
forge test --match-contract PoC -vvv

# O individualmente
forge test --match-test test_VULNERABILITY -vvv
```

**¡Buena suerte con las submissions! 🚀**
