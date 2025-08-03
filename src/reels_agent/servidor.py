# src/reels_agent/servidor.py

import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# O import do scraper foi removido, pois ele não é mais usado.
# from src.reels_agent.scraper import scrape_shopee_product

# --- Carregamento de Configurações ---
print("-> Iniciando o Servidor do Mago dos Reels...")
try:
    with open("/app/config/config_modelo_local.json", 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
    with open("/app/config/prompts.json", 'r', encoding='utf-8') as f:
        PROMPTS_CONFIG = json.load(f)
    print("✅ DNA do Agente e configurações carregados.")
except FileNotFoundError as e:
    print(f"❌ ERRO CRÍTICO: Não foi possível encontrar o arquivo de configuração {e.filename}. Encerrando.")
    exit()

# --- NOVO Modelo Pydantic para a Requisição ---
# Agora esperamos os dados do produto, não apenas uma URL.
class ProductInput(BaseModel):
    source_url: str = Field(..., example="https://shopee.com.br/produto-exemplo")
    title: str = Field(..., example="Título incrível do produto")
    description: str = Field(..., example="Descrição detalhada e persuasiva do produto.")

# --- Inicialização do FastAPI ---
app = FastAPI(
    title="API do Mago dos Reels",
    description="Um serviço para transformar dados de produtos em roteiros virais para o Instagram Reels.",
    version="2.0" # Nova versão do projeto
)

# --- Funções Auxiliares (A mesma lógica de prompt) ---
def construir_prompt_final(dados_produto: dict) -> str:
    """
    Combina as partes OTIMIZADAS do prompt com os dados do produto.
    """
    persona = PROMPTS_CONFIG.get("persona", {})
    output_protocol = PROMPTS_CONFIG.get("output_generation_protocol", {})
    final_mandate = PROMPTS_CONFIG.get("final_review_mandate", "")
    
    # Converte o dicionário de dados do produto em uma string legível
    contexto_produto = "\n".join([f"- {chave}: {valor}" for chave, valor in dados_produto.items()])

    # Monta um prompt muito mais enxuto e direto
    prompt_completo = f"""
### INSTRUÇÕES:
- **Sua Persona:** {persona.get('role', '')}
- **Tarefa:** Analise os dados brutos do produto abaixo e crie um roteiro para um vídeo no Instagram Reels.
- **Regra Final:** {final_mandate}

### DADOS BRUTOS DO PRODUTO:
{contexto_produto}

### ESTRUTURA DE SAÍDA JSON OBRIGATÓRIA:
{json.dumps(output_protocol.get('object_structure', {}), indent=2, ensure_ascii=False)}
"""
    return prompt_completo.strip()

async def execute_openrouter_request(prompt_final: str) -> dict:
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=401, detail="A chave OPENROUTER_API_KEY não foi encontrada no ambiente.")

    service_config = CONFIG.get("servicos", {}).get("gerador_principal", {})
    model_id = service_config.get("id_openrouter")
    
    # --- CABEÇALHOS ENRIQUECIDOS ---
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        # Informa à OpenRouter a origem da requisição (boa prática)
        "HTTP-Referer": "https://github.com/seu-usuario/reels-shopee", 
        # Identifica sua aplicação (substitua pelo nome do seu projeto)
        "X-Title": "MagoDosReels",
    }
    
    params_inferencia = CONFIG.get("parametros_inferencia_padrao", {})
    
    json_data = {
        "model": model_id,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt_final}],
        **params_inferencia
    }

    try:
        # Aumentamos o timeout como uma garantia extra
        async with httpx.AsyncClient(timeout=600.0) as client:
            print(f"\n-> Enviando análise para o modelo: {model_id}...")
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            content_str = data['choices'][0]['message']['content']
            return json.loads(content_str)
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="A requisição para a OpenRouter expirou (Timeout). O modelo pode estar sobrecarregado ou a rede instável.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Erro da API do OpenRouter: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado na chamada do serviço de nuvem: {e}")

# --- Endpoint Principal Simplificado ---
@app.post("/gerar_roteiro_reels", summary="Gera Roteiro de Reels a partir de dados manuais")
async def gerar_roteiro_reels(request: ProductInput):
    # A lógica de scraping e o loop foram removidos.
    # Agora processamos uma entrada de cada vez.
    
    # Construímos o dicionário de dados diretamente da requisição.
    dados_produto = {
        "source_url": request.source_url,
        "title": request.title,
        "description": request.description
    }

    prompt_final = construir_prompt_final(dados_produto)
    
    try:
        roteiro_gerado = await execute_openrouter_request(prompt_final)
        return roteiro_gerado
    except HTTPException as e:
        return {"source_url": request.source_url, "error": f"Falha na geração pela IA: {e.detail}"}