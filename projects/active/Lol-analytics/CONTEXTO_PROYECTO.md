# LoL Meta Analytics - Contexto del Proyecto

## Estado Actual: EN PROGRESO

### Archivos Creados
- [x] `requirements.txt` - Dependencias Python
- [x] `config.py` - Configuración y variables de entorno
- [x] `database.py` - Esquema SQLite completo
- [ ] `riot_api.py` - Cliente para API de Riot
- [ ] `collectors/` - Módulos de recolección
- [ ] `analyzers/` - Módulos de análisis
- [ ] `main.py` - CLI principal

---

## Objetivo
Crear una aplicación Python que recopile datos de la API de Riot Games y los almacene en SQLite para analizar el meta de League of Legends.

---

## Pasos para Obtener API Key de Riot Games

1. Ir a https://developer.riotgames.com/
2. Iniciar sesión con cuenta de Riot
3. En el Dashboard, copiar la **Development API Key** (dura 24h)
4. Crear archivo `.env` con: `RIOT_API_KEY=tu_api_key_aqui`

---

## Estructura Final del Proyecto

```
Lol-analytics/
├── config.py           # Configuración y API key
├── database.py         # Modelos SQLite y conexión
├── riot_api.py         # Cliente para la API de Riot
├── collectors/
│   ├── __init__.py
│   ├── champions.py    # Recolector de datos de campeones
│   ├── matches.py      # Recolector de partidas
│   └── builds.py       # Recolector de builds
├── analyzers/
│   ├── __init__.py
│   ├── meta.py         # Análisis del meta (win/pick/ban rates)
│   └── compositions.py # Análisis de composiciones
├── main.py             # Punto de entrada
└── requirements.txt
```

---

## Tablas de Base de Datos (YA CREADAS)

- **champions** - Datos estáticos de campeones
- **items** - Items del juego
- **runes** - Runas
- **summoners** - Jugadores rastreados
- **matches** - Partidas recopiladas
- **match_participants** - Participantes por partida
- **champion_stats** - Estadísticas del meta
- **builds** - Builds óptimas
- **team_compositions** - Composiciones de equipo

---

## Próximos Pasos (Para Continuar)

1. Crear `riot_api.py` - Cliente con rate limiting
2. Crear `collectors/__init__.py`
3. Crear `collectors/champions.py` - Cargar datos de Data Dragon
4. Crear `collectors/matches.py` - Recolectar partidas de alto elo
5. Crear `collectors/builds.py` - Extraer builds de partidas
6. Crear `analyzers/__init__.py`
7. Crear `analyzers/meta.py` - Calcular win/pick/ban rates
8. Crear `analyzers/compositions.py` - Analizar composiciones
9. Crear `main.py` - CLI con argparse
10. Crear `.env.example` y `.gitignore`

---

## Comandos de Uso (Cuando esté completo)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Sincronizar datos estáticos (campeones, items, runas)
python main.py --sync-static

# Recolectar partidas
python main.py --collect --matches 100

# Analizar y calcular estadísticas
python main.py --analyze

# Ver el meta actual
python main.py --meta
```

---

## Endpoints de Riot API a Usar

| Endpoint | Uso |
|----------|-----|
| Data Dragon | Datos estáticos (campeones, items, runas) - NO requiere API key |
| /lol/league/v4/challengerleagues | Top players para obtener PUUIDs |
| /lol/match/v5/matches/by-puuid | Lista de partidas de un jugador |
| /lol/match/v5/matches/{matchId} | Detalles de una partida |

---

## Notas Importantes

- Rate limits: 20 req/s, 100 req/2min
- API key de desarrollo dura 24 horas
- Data Dragon es público (sin API key)
- Región configurada: EUW (cambiar en .env si necesario)
