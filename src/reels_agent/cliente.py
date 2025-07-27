# src/reels_agent/cliente.py

import json
import requests
from typing import List, Dict, Any

# --- SEÇÃO 1: FUNÇÃO DE COMUNICAÇÃO COM O GATEWAY (AJUSTADA) ---

def chamar_servidor_gateway(payload: dict) -> Any:
    """
    Função ajustada para chamar o endpoint de geração de roteiros e 
    retornar a resposta JSON completa.
    """
    try:
        # O nome 'servidor' corresponde ao nome do serviço no docker-compose.yml
        url = "http://servidor:8000/gerar_roteiro_reels"
        print("-> Enviando URLs para análise do Mago dos Reels...")
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        # Retorna o objeto JSON completo recebido do servidor
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ERRO HTTP {e.response.status_code} do Servidor Gateway:")
        # Tenta mostrar a mensagem de erro detalhada vinda da API
        try:
            erro_detalhado = e.response.json().get('detail', e.response.text)
            print(f"   Detalhe: {erro_detalhado}")
        except json.JSONDecodeError:
            print(f"   Resposta não pôde ser decodificada: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERRO DE CONEXÃO com o Servidor Gateway: {e}")
        return None

# --- SEÇÃO 2: LÓGICA PRINCIPAL DO CLIENTE ---

def iniciar_cliente_reels():
    """
    Loop principal que interage com o usuário para gerar roteiros de Reels.
    """
    print("\n--- 🧙‍♂️ Mago dos Reels: Assistente de Criação de Roteiros ---")
    print("   Cole uma ou mais URLs de produtos da Shopee (separadas por vírgula).")
    print("   Digite 'sair' a qualquer momento para terminar.")
    
    while True:
        urls_input = input("\n🔗 URLs do(s) produto(s) da Shopee: ")
        
        if urls_input.strip().lower() == 'sair':
            break

        # Converte a string de entrada em uma lista de URLs limpas
        urls = [url.strip() for url in urls_input.split(',') if url.strip()]
        
        if not urls:
            print("   ⚠️ Nenhuma URL válida fornecida. Tente novamente.")
            continue

        # Monta o payload no formato esperado pela API
        payload = {"product_urls": urls}
        
        # Chama o servidor e recebe os roteiros
        roteiros_gerados = chamar_servidor_gateway(payload)
        
        # Apresenta o resultado de forma legível
        if roteiros_gerados:
            print("\n✨ Roteiro(s) Gerado(s) pelo Mago dos Reels! ✨")
            # Usa json.dumps para formatar a saída de forma bonita (pretty-print)
            print(json.dumps(roteiros_gerados, indent=2, ensure_ascii=False))

# --- EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    iniciar_cliente_reels()
    print("\n👋 Sessão encerrada. Até logo!")