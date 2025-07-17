import os
import json
import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

# (A função 'configurar_servicos_interativamente' original permanece aqui, sem alterações)
def configurar_servicos_interativamente():
    config_file_path = "config_modelo_local.json"
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ ERRO: Não foi possível ler o arquivo '{config_file_path}'. Verifique o arquivo. Erro: {e}")
        return False
    servicos_a_configurar = ["sumarizador", "gerador_principal"]
    for service_name in servicos_a_configurar:
        print(f"\n--- Configurando o serviço: '{service_name}' ---")
        print(f"  Tipo atual: {config_data['servicos'][service_name].get('tipo', 'não definido')}")
        print("  Escolha o novo tipo:")
        print("    1. Modelo Local (.gguf)")
        print("    2. Modelo na Nuvem (via OpenRouter)")
        tipo_escolhido = ""
        while True:
            load_dotenv()
            choice = input("  Digite sua escolha (1 ou 2): ")
            if choice == "1":
                tipo_escolhido = "local"
                break
            elif choice == "2":
                if not os.getenv("OPENROUTER_API_KEY"):
                    print("    ❌ ERRO: OPENROUTER_API_KEY não encontrada. Configure-a no .env para usar a nuvem.")
                    continue
                tipo_escolhido = "nuvem"
                break
            else:
                print("    Escolha inválida.")
        config_data['servicos'][service_name]['tipo'] = tipo_escolhido
        if tipo_escolhido == "local":
            models_dir = os.path.expanduser("~/.cache/instructlab/models/")
            if not os.path.isdir(models_dir):
                print(f"    ❌ ERRO: Diretório de modelos não encontrado em '{models_dir}'.")
                return False
            gguf_files = sorted([f for f in os.listdir(models_dir) if f.endswith(".gguf")])
            if not gguf_files:
                print(f"    ❌ ERRO: Nenhum modelo .gguf encontrado em '{models_dir}'.")
                return False
            print("\n    -> Selecione o modelo .gguf para este serviço:")
            for i, model_name in enumerate(gguf_files):
                print(f"      {i + 1}. {model_name}")
            while True:
                try:
                    choice_model = int(input("\n    Digite o número do modelo: "))
                    if 1 <= choice_model <= len(gguf_files):
                        selected_model_path = os.path.join(models_dir, gguf_files[choice_model - 1])
                        config_data['servicos'][service_name]['path_gguf'] = selected_model_path
                        print(f"    -> Serviço '{service_name}' usará o modelo local: {gguf_files[choice_model - 1]}")
                        break
                    else:
                        print("       Escolha inválida.")
                except ValueError:
                    print("       Entrada inválida. Digite um número.")
        elif tipo_escolhido == "nuvem":
            default_id = config_data['servicos'][service_name].get('id_openrouter', '')
            prompt_text = f"\n    -> Digite o ID do modelo OpenRouter para '{service_name}' (padrão: {default_id}): "
            cloud_model_id = input(prompt_text)
            if not cloud_model_id:
                cloud_model_id = default_id
            config_data['servicos'][service_name]['id_openrouter'] = cloud_model_id
            print(f"    -> Serviço '{service_name}' usará o modelo da nuvem: {cloud_model_id}")
    with open(config_file_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)
    print(f"\n✅ Configuração salva com sucesso em '{config_file_path}'.")
    print(f"Acessar a interface em outro terminal com o comando ./chat.sh.")
    return True

if not configurar_servicos_interativamente():
    exit()

class PromptRequest(BaseModel): prompt: str
class RagRequest(BaseModel):
    contexto: str
    pergunta: str
# O PdfAnalysisRequest não é mais necessário

print("\n-> Iniciando o Servidor Gateway...")
with open("config_modelo_local.json", 'r', encoding='utf-8') as f: CONFIG = json.load(f)
with open("prompts.json", 'r', encoding='utf-8') as f: PROMPTS_CONFIG = json.load(f)
loaded_local_models = {}

if Llama:
    for service_name, service_config in CONFIG.get("servicos", {}).items():
        if service_config.get("tipo") == "local":
            model_path = service_config.get("path_gguf")
            if model_path and os.path.exists(model_path):
                print(f"-> Carregando modelo local para o serviço '{service_name}': {os.path.basename(model_path)}")
                params = CONFIG.get("parametros_carregamento_local", {})
                loaded_local_models[service_name] = Llama(model_path=model_path, **params, verbose=False)
                print(f"✅ Modelo para '{service_name}' carregado.")

app = FastAPI()

async def execute_request(service_name: str, prompt_final: str):
    load_dotenv()
    OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
    service_config = CONFIG.get("servicos", {}).get(service_name)
    service_type = service_config.get("tipo")
    params_inferencia = CONFIG.get("parametros_inferencia_padrao", {})
    if service_type == "local":
        model_obj = loaded_local_models.get(service_name)
        if not model_obj: raise HTTPException(status_code=503, detail=f"Modelo local para '{service_name}' não carregado.")
        def blocking_call(): return model_obj(prompt_final, stop=["[/INST]", "</s>"], **params_inferencia)
        try:
            response = await asyncio.wait_for(asyncio.to_thread(blocking_call), timeout=180.0)
            return {"texto_gerado": response['choices'][0]['text'].strip()}
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail=f"A geração do serviço local '{service_name}' excedeu o limite.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no serviço local '{service_name}': {e}")
    elif service_type == "nuvem":
        if not OPENROUTER_KEY: raise HTTPException(status_code=401, detail="A chave OPENROUTER_API_KEY não foi encontrada.")
        model_id = service_config.get("id_openrouter")
        headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
        json_data = {"model": model_id, "messages": [{"role": "user", "content": prompt_final}], **params_inferencia}
        try:
            async with httpx.AsyncClient() as client:
                print(f"\n-> Roteando req. do serviço '{service_name}' para OpenRouter (Modelo: {model_id})...")
                response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json_data, timeout=180)
                response.raise_for_status()
                data = response.json()
                if "choices" not in data or not data["choices"]: raise Exception("Resposta da API inválida.")
                return {"texto_gerado": data['choices'][0]['message']['content'].strip()}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro da API do OpenRouter: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro na chamada do serviço de nuvem '{service_name}': {e}")

@app.post("/sumarizar")
async def endpoint_sumarizar(request: RagRequest):
    prompt_final = PROMPTS_CONFIG["sumarizacao_local"]["template"].format(pergunta=request.pergunta, contexto_completo=request.contexto)
    return await execute_request("sumarizador", prompt_final)

@app.post("/gerar")
async def endpoint_gerar(request: PromptRequest):
    return await execute_request("gerador_principal", request.prompt)

@app.post("/gerar_rag")
async def endpoint_gerar_rag(request: RagRequest):
    service_config = CONFIG.get("servicos", {}).get("gerador_principal", {})
    service_type = service_config.get("tipo")
    if service_type == 'local':
        template = PROMPTS_CONFIG["geracao_rag_local"]["template"]
        prompt_final = template.format(contexto=request.contexto, pergunta=request.pergunta)
    else:
        template = PROMPTS_CONFIG["geracao_rag_nuvem"]["template"]
        prompt_final = template.format(context=request.contexto, input=request.pergunta)
    return await execute_request("gerador_principal", prompt_final)

# para subir o servidor, use:
# uvicorn servidor_modelo_local:app --reload