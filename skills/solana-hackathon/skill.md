---
name: solana-hackathon
description: Hackathon Solana Colosseum Frontier 2026 — deadline 11 mayo 2026, $2.5M fondo venture, track IA Agents $100K. Stack técnico Solana, recursos gratuitos (Helius RPC, QuickNode créditos, Replit), proceso de submission y estrategia de proyecto.
tools: Bash, Read, Write, WebSearch, WebFetch
---

# Hackathon Solana — Colosseum Frontier 2026

## Datos clave

| Campo | Detalle |
|-------|---------|
| **URL registro** | https://arena.colosseum.org/hackathon |
| **Recursos** | https://colosseum.com/breakout/resources |
| **Fechas** | 6 abril – 11 mayo 2026 |
| **Deadline submission** | 11 mayo 2026 |
| **Premio principal** | $2.5M+ fondo de venture (inversión real en proyectos ganadores) |
| **Track IA Agents** | $100K prize pool |
| **Pre-seed funding** | Hasta $250K para ganadores seleccionados |
| **Formato** | Global online, cualquier nivel |

---

## Tracks disponibles

### Track General — Frontier
Cualquier proyecto sobre Solana. Foco en: DeFi, NFTs, gaming, infraestructura.

### Track IA Agents en Solana ⭐ (más relevante para el equipo)
Agentes IA que operan on-chain:
- Trading agents autónomos
- Agentes que gestionan wallets
- IA que interactúa con protocolos DeFi
- Agentes multi-modelo con tool use
- Agentes que generan/venden contenido on-chain

---

## Stack técnico Solana

### JavaScript/TypeScript (recomendado para el equipo)
```typescript
// @solana/web3.js — SDK principal
import { Connection, PublicKey, Transaction, SystemProgram } from "@solana/web3.js";

const connection = new Connection("https://api.mainnet-beta.solana.com");
// O con Helius (más rápido, gratuito para hackathon):
const connection = new Connection("https://mainnet.helius-rpc.com/?api-key=TU_KEY");

// Obtener balance
const balance = await connection.getBalance(new PublicKey("WALLET_ADDRESS"));
console.log(`Balance: ${balance / 1e9} SOL`);

// Transferir SOL
const tx = new Transaction().add(
    SystemProgram.transfer({
        fromPubkey: sender.publicKey,
        toPubkey: recipient,
        lamports: 0.01 * 1e9,  // 0.01 SOL
    })
);
await connection.sendTransaction(tx, [sender]);
```

### Python (para IA + Solana)
```python
# pip install solana solders
from solana.rpc.api import Client
from solders.pubkey import Pubkey

client = Client("https://api.mainnet-beta.solana.com")

# Balance
pubkey = Pubkey.from_string("WALLET_ADDRESS")
balance = client.get_balance(pubkey)
print(f"Balance: {balance.value / 1e9} SOL")
```

### Anchor (contratos inteligentes Solana)
```rust
// Rust — para smart contracts en Solana
use anchor_lang::prelude::*;

#[program]
pub mod mi_programa {
    use super::*;
    
    pub fn initialize(ctx: Context<Initialize>, data: u64) -> Result<()> {
        ctx.accounts.mi_cuenta.data = data;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = user, space = 8 + 8)]
    pub mi_cuenta: Account<'info, MiCuenta>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}
```

---

## Agente IA + Solana (idea ganadora para el track IA)

```python
"""
Agente IA autónomo que monitorea precios y ejecuta trades on-chain.
Usa Claude/Gemini para tomar decisiones + Solana para ejecutar.
"""
import anthropic
from solana.rpc.api import Client

client_ai = anthropic.Anthropic()
client_sol = Client("https://mainnet.helius-rpc.com/?api-key=KEY")

TOOLS = [{
    "name": "get_token_price",
    "description": "Obtiene el precio actual de un token en Solana",
    "input_schema": {
        "type": "object",
        "properties": {
            "token_mint": {"type": "string", "description": "Mint address del token"},
        },
        "required": ["token_mint"]
    }
}, {
    "name": "execute_swap",
    "description": "Ejecuta un swap en Jupiter DEX (Solana)",
    "input_schema": {
        "type": "object",
        "properties": {
            "input_mint": {"type": "string"},
            "output_mint": {"type": "string"},
            "amount": {"type": "number", "description": "Cantidad en SOL"},
        },
        "required": ["input_mint", "output_mint", "amount"]
    }
}]

def run_agent(task: str):
    messages = [{"role": "user", "content": task}]
    
    while True:
        response = client_ai.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        
        if response.stop_reason == "end_turn":
            return response.content[0].text
        
        # Ejecutar tools
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "get_token_price":
                    result = get_token_price(block.input["token_mint"])
                elif block.name == "execute_swap":
                    result = execute_swap(**block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result)
                })
        
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

---

## Recursos gratuitos para el hackathon

| Recurso | Qué da | URL |
|---------|--------|-----|
| **Helius** | RPC gratis con alta velocidad | helius.dev → signup |
| **QuickNode** | $500 en créditos para hackathon | quicknode.com |
| **Replit** | IDE en la nube + despliegue | replit.com |
| **Triton One** | RPC gratuito | triton.one |
| **Metaplex** | NFT/token standards | metaplex.com |
| **Wormhole** | Cross-chain bridge | wormhole.com |
| **Privy** | Auth wallets sin fricción | privy.io |

---

## Estrategia de proyecto recomendada (14 días)

### Semana 1 — Construir
- Días 1-2: Setup (Helius RPC + wallet + ambiente dev)
- Días 3-5: Core feature del agente IA
- Días 6-7: UI básica + integración on-chain

### Semana 2 — Pulir y presentar
- Días 8-10: Testing + bug fixes
- Días 11-12: Demo video (2 min máx)
- Días 13-14: Submission + landing page del proyecto

### Ideas de proyecto con alto potencial de ganar
1. **DeFi AI Agent** — agente que analiza yields y mueve fondos automáticamente
2. **Content monetization agent** — genera contenido, lo publica y cobra en SOL
3. **DAO governance assistant** — agente que resume propuestas y vota según preferencias
4. **On-chain analytics agent** — monitorea wallets y alerta sobre movimientos

---

## Checklist de submission

- [ ] Registrar equipo en arena.colosseum.org (crear cuenta cada miembro)
- [ ] Definir líder y track (IA Agents recomendado)
- [ ] Obtener API key Helius (gratis)
- [ ] Crear repositorio GitHub del proyecto
- [ ] Demo video de 2 minutos (obligatorio)
- [ ] Descripción del proyecto (problema, solución, tech stack)
- [ ] Deploy del MVP (Replit o Vercel)
- [ ] Wallet Solana del equipo para recibir premios
