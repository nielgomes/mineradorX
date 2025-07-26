import os
import json
import requests

# --- SEÇÃO 1: FUNÇÃO DE COMUNICAÇÃO COM O GATEWAY (Sem alterações) ---

def chamar_servidor_gateway(endpoint: str, payload: dict) -> str:
    """Função centralizada para chamar endpoints do nosso servidor gateway."""
    try:
        # Usando o nome do serviço Docker para a comunicação
        url = f"http://ia_gateway:8000/{endpoint.strip('/')}"
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json().get("texto_gerado", f"ERRO: Resposta inválida do endpoint /{endpoint}")
    except requests.exceptions.RequestException as e:
        return f"ERRO DE CONEXÃO com o Servidor Gateway: {e}"

# --- SEÇÃO 2: FUNÇÕES PARA CRIAÇÃO DE PROMPT (Sem alterações) ---

def criar_prompt_tecnico(instrucoes_json: dict, pergunta_usuario: str) -> str:
    """
    Constrói um prompt detalhado combinando as instruções do prompts.json
    com a pergunta do usuário.
    """
    persona = instrucoes_json.get("instructions", {}).get("persona", {})
    regras = instrucoes_json.get("instructions", {}).get("rules", [])
    objetivo = instrucoes_json.get("objective", "")
    regras_formatadas = "\n".join(regras)
    prompt_final = f"""
Você é um agente especialista. Siga estritamente as instruções, regras e persona definidas abaixo para formular sua resposta.

### Persona: {persona.get('title', 'Assistente Especialista')}
{persona.get('description', '')}

### Objetivo Principal
{objetivo}

### Regras a Seguir
{regras_formatadas}

### Pergunta do Usuário:
"{pergunta_usuario}"

### Resposta Especialista:
"""
    return prompt_final.strip()

# --- SEÇÃO 3: LÓGICA DE CHAT (Atualizada para receber o nome do modelo) ---

def loop_chat_com_prompt_tecnico(instrucoes_base: dict, nome_modelo: str):
    """
    Loop de chat que utiliza o prompt técnico antes de cada chamada.
    """
    agent_name = instrucoes_base.get("agent_name", "Agente")
    print(f"\n✅ Chat iniciado com o agente especialista: '{agent_name}'.")
    print(f"   -> Modelo em uso: {nome_modelo}") # Exibe o nome do modelo
    print("   Digite 'sair' a qualquer momento para terminar.")
    
    while True:
        pergunta_usuario = input("\n🤖 Você pergunta: ")
        if pergunta_usuario.strip().lower() == 'sair':
            break
        
        print("   -> Construindo prompt técnico...")
        prompt_completo = criar_prompt_tecnico(instrucoes_base, pergunta_usuario)
        
        print("   ...pensando (via servidor gateway)...")
        response = chamar_servidor_gateway("gerar", {"prompt": prompt_completo})
        
        print("\n💡 Resposta do Especialista:")
        print(response)

# --- EXECUÇÃO PRINCIPAL (Atualizada para carregar o nome do modelo) ---

if __name__ == "__main__":
    print("--- Assistente de IA com Prompt Técnico ---")
    
    PROMPTS_CONFIG = {}
    nome_modelo_ativo = "Não especificado"

    try:
        # Carrega o arquivo de prompts que define o comportamento do agente
        with open("prompts.json", 'r', encoding='utf-8') as f:
            PROMPTS_CONFIG = json.load(f)
        print("✅ Instruções do agente carregadas de 'prompts.json'.")

        # --- INÍCIO DA CORREÇÃO ---
        # Carrega o arquivo de configuração para descobrir o nome do modelo
        with open("config_modelo_local.json", 'r', encoding='utf-8') as f:
            CONFIG = json.load(f)
        
        # Assume que o gerador principal está configurado para a nuvem
        serv_princ_cfg = CONFIG.get("servicos", {}).get("gerador_principal", {})
        nome_modelo_ativo = serv_princ_cfg.get('id_openrouter', "Modelo de Nuvem Padrão")
        print(f"✅ Nome do modelo ('{nome_modelo_ativo}') carregado de 'config_modelo_local.json'.")
        # --- FIM DA CORREÇÃO ---

    except FileNotFoundError as e:
        print(f"❌ ERRO CRÍTICO: Arquivo de configuração '{e.filename}' não encontrado.")
        exit()
    except json.JSONDecodeError as e:
        print(f"❌ ERRO CRÍTICO: Arquivo de configuração contém um erro de formatação (JSON inválido).")
        exit()

    # Inicia o loop de chat, passando as instruções e o nome do modelo
    loop_chat_com_prompt_tecnico(PROMPTS_CONFIG, nome_modelo_ativo)
        
    print("\n👋 Sessão encerrada. Até logo!")