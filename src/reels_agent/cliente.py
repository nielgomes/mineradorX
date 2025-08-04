# src/reels_agent/cliente.py (VERSÃO FINAL COM PALAVRA-CHAVE)

import json
import requests
import sys
from typing import Dict, Any

def chamar_servidor_gateway(payload: dict) -> Any:
    # Esta função permanece a mesma
    try:
        url = "http://servidor:8000/gerar_roteiro_reels"
        print("-> Enviando dados para análise do Mago dos Reels...")
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ERRO HTTP {e.response.status_code} do Servidor Gateway:")
        try:
            erro_detalhado = e.response.json().get('detail', e.response.text)
            print(f"   Detalhe: {erro_detalhado}")
        except json.JSONDecodeError:
            print(f"   Resposta não pôde ser decodificada: {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERRO DE CONEXÃO com o Servidor Gateway: {e}")
        return None

def formatar_descricao(texto_bruto: str) -> str:
    # Esta função permanece a mesma
    linhas = texto_bruto.splitlines()
    linhas_limpas = [linha.strip() for linha in linhas if linha.strip()]
    return "\n".join(linhas_limpas)

# --- FUNÇÃO DE ENTRADA ATUALIZADA PARA USAR PALAVRA-CHAVE ---
def obter_descricao_multilinha() -> str:
    """
    Permite que o usuário cole ou digite um texto de múltiplas linhas.
    A entrada termina quando o usuário digita 'FIM' em uma linha nova.
    """
    print("📄 Descrição do produto (cole o texto e digite FIM em uma nova linha para finalizar):")
    linhas = []
    while True:
        try:
            linha = input()
            # Verifica se a linha, sem espaços e em minúsculas, é a nossa palavra-chave
            if linha.strip().lower() == "fim":
                break
            linhas.append(linha)
        except EOFError:
            # Mantemos isso como uma segurança extra
            break
    return "\n".join(linhas)

def iniciar_cliente_reels():
    """Loop principal que interage com o usuário para gerar roteiros de Reels."""
    print("\n--- 🧙‍♂️ Mago dos Reels v2.5: Assistente de Criação de Roteiros ---")
    print("   Cole os dados do produto para gerar o roteiro.")
    print("   Digite 'sair' a qualquer momento para terminar.")
    
    while True:
        url_input = input("\n🔗 URL do produto da Shopee: ")
        if url_input.strip().lower() == 'sair':
            break

        title_input = input("📝 Título do produto: ")
        if title_input.strip().lower() == 'sair':
            break
        
        # Chamando a função atualizada
        desc_input = obter_descricao_multilinha()
        
        if not all([url_input, title_input, desc_input]):
            print("   ⚠️ Todos os campos são obrigatórios. Tente novamente.")
            continue

        print("   -> Formatando e limpando a descrição...")
        descricao_formatada = formatar_descricao(desc_input)

        payload = {
            "source_url": url_input.strip(),
            "title": title_input.strip(),
            "description": descricao_formatada
        }
        
        roteiro_gerado = chamar_servidor_gateway(payload)
        
        if roteiro_gerado:
            print("\n✨ Roteiro Gerado pelo Mago dos Reels! ✨")
            print(json.dumps(roteiro_gerado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    iniciar_cliente_reels()
    print("\n👋 Sessão encerrada. Até logo!")