# src/reels_agent/servidor.py

import os
import json
import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

# Importa o nosso scraper
from src.reels_agent.scraper import scrape_shopee_product

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

# --- Modelos Pydantic para as Requisições da API ---
class UrlRequest(BaseModel):
    product_urls: List[str] = Field(..., example=["https://shopee.com.br/produto-exemplo-aqui"])

# --- Inicialização do FastAPI ---
app = FastAPI(
    title="API do Mago dos Reels",
    description="Um serviço para transformar URLs da Shopee em roteiros virais para o Instagram Reels.",
    version="1.0"
)

# --- Funções Auxiliares ---
def construir_prompt_final(dados_produto: dict) -> str:
    """
    Combina as partes relevantes do "Prompt Mestre" com os dados do produto
    para criar uma instrução clara e direta para a IA.
    """
    persona = PROMPTS_CONFIG.get("persona", {})
    output_protocol = PROMPTS_CONFIG.get("output_generation_protocol", {})
    final_mandate = PROMPTS_CONFIG.get("final_review_mandate", "")
    
    contexto_produto = "\n".join([f"- {chave}: {valor}" for chave, valor in dados_produto.items()])

    prompt_completo = f"""
### PERSONA:
Você é '{persona.get('nickname', 'Mestre dos Reels')}', um {persona.get('role', 'copywriter de elite')}.
Sua crença principal é: "{persona.get('core_belief', '')}".
Seu objetivo é analisar os dados de um produto e criar um roteiro de vídeo curto e irresistível para o Instagram Reels, com foco total em conversão.

### DADOS BRUTOS DO PRODUTO PARA ANÁLISE:
{contexto_produto}

### PROTOCOLO DE SAÍDA:
Sua resposta final DEVE SER um único objeto JSON. NÃO inclua nenhuma outra palavra ou explicação antes ou depois do JSON.
O objeto JSON deve ter a seguinte estrutura:
{json.dumps(output_protocol.get('object_structure', {}), indent=2, ensure_ascii=False)}

### REVISÃO FINAL OBRIGATÓRIA:
{final_mandate}

Agora, com base nos dados do produto fornecido, gere a saída JSON.
"""
    return prompt_completo.strip()

async def execute_openrouter_request(prompt_final: str) -> dict:
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=401, detail="A chave OPENROUTER_API_KEY não foi encontrada no ambiente.")

    service_config = CONFIG.get("servicos", {}).get("gerador_principal", {})
    model_id = service_config.get("id_openrouter")
    if not model_id:
        raise HTTPException(status_code=404, detail="ID do modelo OpenRouter não encontrado para o serviço 'gerador_principal'.")

    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
    params_inferencia = CONFIG.get("parametros_inferencia_padrao", {})
    
    json_data = {
        "model": model_id,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt_final}],
        **params_inferencia
    }

    try:
        async with httpx.AsyncClient() as client:
            print(f"\n-> Enviando análise para o modelo: {model_id}...")
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data, timeout=300)
            response.raise_for_status()
            data = response.json()
            
            content_str = data['choices'][0]['message']['content']
            return json.loads(content_str)
            
    except httpx.HTTPStatusError as e:
        print(f"❌ DETALHE DO ERRO DA API: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Erro da API do OpenRouter: {e.response.text}")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ ERRO: A IA não retornou um JSON válido. Resposta recebida: {content_str}")
        raise HTTPException(status_code=500, detail="A resposta da IA não estava no formato JSON esperado.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado na chamada do serviço de nuvem: {e}")

# --- Endpoint Principal da API ---
@app.post("/gerar_roteiro_reels", summary="Gera Roteiros de Reels a partir de URLs da Shopee")
async def gerar_roteiro_reels(request: UrlRequest):
    roteiros_finais = []
    
    for url in request.product_urls:
        dados_produto = await scrape_shopee_product(url)
        
        if not dados_produto:
            roteiros_finais.append({"source_url": url, "error": "Falha ao coletar dados do produto."})
            continue

        prompt_final = construir_prompt_final(dados_produto)
        
        # --- INÍCIO DA ADIÇÃO PARA DEBUG ---
        print("\n" + "="*20 + " INÍCIO DO PROMPT ENVIADO " + "="*20)
        print(prompt_final)
        print("="*22 + " FIM DO PROMPT ENVIADO " + "="*23 + "\n")
        # --- FIM DA ADIÇÃO PARA DEBUG ---

        try:
            roteiro_gerado = await execute_openrouter_request(prompt_final)
            roteiros_finais.append(roteiro_gerado)
        except HTTPException as e:
            roteiros_finais.append({"source_url": url, "error": f"Falha na geração pela IA: {e.detail}"})

    return roteiros_finais