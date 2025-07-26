import os
import json
import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Carregamento de Configurações ---
print("-> Iniciando o Servidor Gateway (Modo: Somente Nuvem)...")
try:
    with open("config_modelo_local.json", 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
    with open("prompts.json", 'r', encoding='utf-8') as f:
        PROMPTS_CONFIG = json.load(f)
except FileNotFoundError as e:
    print(f"❌ ERRO CRÍTICO: Não foi possível encontrar o arquivo de configuração {e.filename}. Encerrando.")
    exit()

# --- Modelos Pydantic para as Requisições ---
class PromptRequest(BaseModel):
    prompt: str

class RagRequest(BaseModel):
    contexto: str
    pergunta: str

# --- Inicialização do FastAPI ---
app = FastAPI()

# --- Função de Execução Refatorada ---
async def execute_openrouter_request(service_name: str, prompt_final: str):
    """Função otimizada para fazer requisições apenas para a API do OpenRouter."""
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_KEY:
        raise HTTPException(status_code=401, detail="A chave OPENROUTER_API_KEY não foi encontrada no ambiente.")

    service_config = CONFIG.get("servicos", {}).get(service_name, {})
    model_id = service_config.get("id_openrouter")
    if not model_id:
        raise HTTPException(status_code=404, detail=f"ID do modelo OpenRouter não encontrado para o serviço '{service_name}'.")

    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
    params_inferencia = CONFIG.get("parametros_inferencia_padrao", {})

    # Payload compatível com modelos multimodais (VL)
    json_data = {
        "model": model_id,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt_final}]}],
        **params_inferencia
    }

    try:
        async with httpx.AsyncClient() as client:
            print(f"\n-> Roteando req. do serviço '{service_name}' para OpenRouter (Modelo: {model_id})...")
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data, timeout=180)
            response.raise_for_status()
            data = response.json()
            if "choices" not in data or not data["choices"]:
                raise Exception("Resposta da API do OpenRouter inválida ou sem 'choices'.")
            return {"texto_gerado": data['choices'][0]['message']['content'].strip()}
    except httpx.HTTPStatusError as e:
        print(f"❌ DETALHE DO ERRO DA API: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Erro da API do OpenRouter: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na chamada do serviço de nuvem '{service_name}': {e}")

# --- Endpoints da API ---
@app.post("/sumarizar")
async def endpoint_sumarizar(request: RagRequest):
    template = PROMPTS_CONFIG["sumarizacao_nuvem"]["template"]
    prompt_final = template.format(pergunta=request.pergunta, contexto_completo=request.contexto)
    return await execute_openrouter_request("sumarizador", prompt_final)

@app.post("/gerar")
async def endpoint_gerar(request: PromptRequest):
    return await execute_openrouter_request("gerador_principal", request.prompt)

@app.post("/gerar_rag")
async def endpoint_gerar_rag(request: RagRequest):
    template = PROMPTS_CONFIG["geracao_rag_nuvem"]["template"]
    prompt_final = template.format(context=request.contexto, input=request.pergunta)
    return await execute_openrouter_request("gerador_principal", prompt_final)