# Setup TradingView + Fundex Bot

## 1. Deploy el Bot (5 min)

```bash
# Primero configura gcloud con tu proyecto
~/google-cloud-sdk/bin/gcloud auth login
~/google-cloud-sdk/bin/gcloud config set project TU_PROJECT_ID

# Habilitar servicios
~/google-cloud-sdk/bin/gcloud services enable run.googleapis.com
~/google-cloud-sdk/bin/gcloud services enable cloudbuild.googleapis.com

# Deploy
cd ~/fundex
chmod +x deploy.sh
./deploy.sh
```

Tu URL será algo como: `https://fundex-bot-xxxxx.run.app`

## 2. Configurar Indicadores en TradingView

En TradingView, abre el gráfico de SOLUSD y añade:
- EMA 9 (color verde)
- EMA 20 (color rojo)
- RSI 14

## 3. Crear Alertas en TradingView

### Alerta de COMPRA:
```
Condición: EMA 9 cruza arriba de EMA 20
Webhook URL: https://tu-url.run.app/webhook
Mensaje:
{
    "secret": "fundex2024",
    "action": "BUY",
    "symbol": "SOLUSD",
    "price": {{close}}
}
```

### Alerta de VENTA:
```
Condición: EMA 9 cruza abajo de EMA 20
Webhook URL: https://tu-url.run.app/webhook
Mensaje:
{
    "secret": "fundex2024",
    "action": "SELL",
    "symbol": "SOLUSD",
    "price": {{close}}
}
```

### Alerta RSI Overbought (venta de emergencia):
```
Condición: RSI cruza arriba de 80
Webhook URL: https://tu-url.run.app/webhook
Mensaje:
{
    "secret": "fundex2024",
    "action": "SELL",
    "symbol": "SOLUSD",
    "price": {{close}}
}
```

## 4. Verificar

```bash
# Check salud
curl https://tu-url.run.app/health

# Ver estado
curl https://tu-url.run.app/status
```

## 5. Flujo Automático

```
TradingView detecta cruce EMA
        ↓
Envía webhook a Cloud Run
        ↓
Bot recibe señal
        ↓
Ejecuta lógica (paper trading)
        ↓
Loggea operación
        ↓
Espera siguiente señal
```

## IMPORTANTE

⚠️ Este bot hace PAPER TRADING (simulado)
⚠️ Para operar REAL en Fundex necesitarías conectar via MT4/MT5 API
⚠️ Verifica con soporte de Fundex si permiten bots antes de automatizar
