# src/reels_agent/servidor.py (VERSÃO REVERTIDA PARA ENTRADA MANUAL)

import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

# O import do scraper foi removido, pois ele não é mais usado.

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

# --- VOLTAMOS A USAR O MODELO DE ENTRADA MANUAL ---
class ProductInput(BaseModel):
    source_url: str = Field(..., example="https://shopee.com.br/produto-exemplo")
    title: str = Field(..., example="Título incrível do produto")
    description: str = Field(..., example="Descrição detalhada e persuasiva do produto.")

# --- Inicialização do FastAPI ---
app = FastAPI(
    title="API do Mago dos Reels",
    description="Um serviço para transformar dados de produtos em roteiros virais para o Instagram Reels.",
    version="2.5" # Versão de fluxo manual com prompt enriquecido
)

# --- Funções Auxiliares (Adaptadas) ---
def construir_prompt_final(title: str, description: str) -> str:
    """
    Combina o PROMPT COMPLETO com os dados do produto fornecidos manualmente.
    """
    # Usamos o prompt.json inteiro como o DNA e as instruções para a IA
    instrucoes_dna = json.dumps(PROMPTS_CONFIG, indent=2, ensure_ascii=False)
    
    # Criamos um objeto com os dados que o usuário forneceu
    dados_manuais = {
        "title": title,
        "description": description
    }
    dados_formatados = json.dumps(dados_manuais, indent=2, ensure_ascii=False)

    prompt_final = f"""
Você seguirá RIGOROSAMENTE as regras, persona e formato de saída definidos no JSON de instruções abaixo.
Sua tarefa é analisar os DADOS BRUTOS DO PRODUTO fornecidos e gerar a saída solicitada.

### INSTRUÇÕES (SEU DNA):
{instrucoes_dna}

### DADOS BRUTOS DO PRODUTO PARA ANÁLISE:
{dados_formatados}
"""
    return prompt_final.strip()

async def execute_openrouter_request(prompt_final: str) -> dict:
    # Esta função não precisa de alterações, ela continua perfeita.
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=401, detail="A chave OPENROUTER_API_KEY não foi encontrada no ambiente.")

    service_config = CONFIG.get("servicos", {}).get("gerador_principal", {})
    model_id = service_config.get("id_openrouter")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://github.com/nielgomes/mineradorX", 
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
        async with httpx.AsyncClient(timeout=600.0) as client:
            print(f"\n-> Enviando análise para o modelo: {model_id}...")
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            content_str = data['choices'][0]['message']['content']
            return json.loads(content_str)
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="A requisição para a OpenRouter expirou (Timeout).")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Erro da API do OpenRouter: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado na chamada do serviço de nuvem: {e}")

# --- Endpoint Principal (Lógica Revertida para Fluxo Único) ---
@app.post("/gerar_roteiro_reels", summary="Gera Roteiro de Reels a partir de dados manuais")
async def gerar_roteiro_reels(request: ProductInput):
    # A lógica de loop e chamada ao scraper foi removida.
    # Processamos uma entrada de cada vez, diretamente.
    try:
        prompt_final = construir_prompt_final(request.title, request.description)
        roteiro_gerado = await execute_openrouter_request(prompt_final)
        # Adicionamos a source_url na resposta final para manter a consistência
        roteiro_gerado["source_url"] = request.source_url
        return roteiro_gerado
    except HTTPException as e:
        return {"source_url": request.source_url, "error": f"Falha na geração pela IA: {e.detail}"}
    except Exception as e:
        return {"source_url": request.source_url, "error": f"Erro inesperado no processamento: {str(e)}"}