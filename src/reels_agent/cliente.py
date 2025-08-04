# src/reels_agent/cliente.py

import json
import requests
from typing import Dict, Any

def chamar_servidor_gateway(payload: dict) -> Any:
    """Chama o endpoint de geração de roteiros e retorna a resposta JSON."""
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
    """
    Limpa e formata um bloco de texto para ser compatível com JSON.
    - Remove espaços/tabs no início e fim de cada linha.
    - Remove linhas que ficam completamente em branco.
    - Junta as linhas limpas com um caractere de nova linha '\\n'.
    """
    # 1. Divide o texto em uma lista de linhas
    linhas = texto_bruto.splitlines()
    
    # 2. Limpa cada linha e remove as que ficam vazias.
    #    A list comprehension torna isso conciso e eficiente.
    linhas_limpas = [linha.strip() for linha in linhas if linha.strip()]
    
    # 3. Junta as linhas limpas de volta em uma única string
    return "\n".join(linhas_limpas)

def iniciar_cliente_reels():
    """Loop principal que interage com o usuário para gerar roteiros de Reels."""
    print("\n--- 🧙‍♂️ Mago dos Reels v2.0: Assistente de Criação de Roteiros ---")
    print("   Cole os dados do produto para gerar o roteiro.")
    print("   Digite 'sair' a qualquer momento para terminar.")
    
    while True:
        url_input = input("\n🔗 URL do produto da Shopee: ")
        if url_input.strip().lower() == 'sair':
            break

        title_input = input("📝 Título do produto: ")
        if title_input.strip().lower() == 'sair':
            break
        
        desc_input = input("📄 Descrição do produto: ")
        if desc_input.strip().lower() == 'sair':
            break

        if not all([url_input, title_input, desc_input]):
            print("   ⚠️ Todos os campos são obrigatórios. Tente novamente.")
            continue

        # --- APLICAÇÃO DA NOSSA FUNÇÃO DE LIMPEZA ---
        print("   -> Formatando e limpando a descrição...")
        descricao_formatada = formatar_descricao(desc_input)
        # ---------------------------------------------

        # Monta o payload no novo formato esperado pela API com a descrição já tratada
        payload = {
            "source_url": url_input.strip(),
            "title": title_input.strip(),
            "description": descricao_formatada # Usamos a variável formatada aqui
        }
        
        roteiro_gerado = chamar_servidor_gateway(payload)
        
        if roteiro_gerado:
            print("\n✨ Roteiro Gerado pelo Mago dos Reels! ✨")
            print(json.dumps(roteiro_gerado, indent=2, ensure_ascii=False))

        # Monta o payload no novo formato esperado pela API
        payload = {
            "source_url": url_input.strip(),
            "title": title_input.strip(),
            "description": desc_input.strip()
        }
        
        roteiro_gerado = chamar_servidor_gateway(payload)
        
        if roteiro_gerado:
            print("\n✨ Roteiro Gerado pelo Mago dos Reels! ✨")
            print(json.dumps(roteiro_gerado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    iniciar_cliente_reels()
    print("\n👋 Sessão encerrada. Até logo!")