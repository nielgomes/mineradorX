# src/reels_agent/scraper.py (Versão Final: Requisição Enriquecida)

import os
import httpx
import json
import re
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Não precisamos mais do 'quote', então a importação pode ser removida.
# from urllib.parse import quote 

load_dotenv()

def extract_shopee_ids(url: str) -> Optional[Tuple[str, str]]:
    """Extrai o shop_id e o item_id de uma URL da Shopee."""
    match = re.search(r'-i\.(\d+)\.(\d+)', url)
    if match:
        shop_id, item_id = match.groups()
        return shop_id, item_id
    match = re.search(r'/product/(\d+)/(\d+)', url)
    if match:
        shop_id, item_id = match.groups()
        return shop_id, item_id
    return None

async def scrape_shopee_product(url: str) -> Optional[Dict]:
    """
    Usa o ZenRows com cabeçalhos customizados para simular um navegador real
    chamando a API interna da Shopee.
    """
    print(f"\n-> Iniciando raspagem de API via ZenRows para: {url}")
    
    ids = extract_shopee_ids(url)
    if not ids:
        print(f"❌ ERRO: Não foi possível extrair IDs da URL: {url}")
        return None
    shop_id, item_id = ids

    # A URL alvo, sem codificação manual.
    shopee_api_url = f"https://shopee.com.br/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
    print(f"   -> Alvo da API interna: {shopee_api_url}")

    api_key = os.getenv("ZENROWS_KEY")
    if not api_key:
        print("❌ ERRO: A chave ZENROWS_KEY não foi encontrada no .env.")
        return None

    # Parâmetros para o ZenRows, reativando js_render e ativando custom_headers
    params = {
        "url": shopee_api_url,
        "apikey": api_key,
        "premium_proxy": "true",
        "js_render": "true",       # Reativado para usar o ambiente de navegador completo do ZenRows
        "custom_headers": "true",  # Parâmetro que diz ao ZenRows para encaminhar nossos headers
    }
    zenrows_api_url = "https://api.zenrows.com/v1/"

    # Estes são os cabeçalhos que o ZenRows vai encaminhar para a Shopee.
    # Fazemos a requisição parecer um navegador de verdade.
    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8',
        'X-Requested-With': 'XMLHttpRequest', # Simula uma requisição feita por JavaScript
    }

    try:
        # A chamada agora inclui o parâmetro 'headers'
        async with httpx.AsyncClient(timeout=120.0) as client:
            print("   -> Enviando requisição ENRIQUECIDA para a API da Shopee via ZenRows...")
            response = await client.get(zenrows_api_url, params=params, headers=custom_headers)
            response.raise_for_status()
            
            json_data = response.json()
            print("   -> Resposta JSON da API recebida com sucesso!")

            if json_data.get('error') or not json_data.get('data'):
                error_msg = json_data.get('error_msg', 'Resposta da API vazia ou com erro.')
                print(f"❌ ERRO retornado pela API da Shopee: {error_msg}")
                return None

            item_data = json_data.get('data', {})
            product_data = {
                "source_url": url,
                "title": item_data.get("name", "Título não encontrado"),
                "price": f"R$ {item_data.get('price', 0) / 100000.0:.2f}",
                "rating_score": f"{item_data.get('item_rating', {}).get('rating_star', 0):.1f} estrelas",
                "units_sold": f"{item_data.get('historical_sold', 0)} vendidos", 
                "description": item_data.get("description", "Descrição não encontrada").replace('\n', ' ').strip(),
            }
            
            print("✅ Missão Cumprida! Dados do produto extraídos diretamente da API!")
            return product_data

    except httpx.HTTPStatusError as e:
        print(f"❌ ERRO HTTP do ZenRows: Status {e.response.status_code}")
        # Tenta imprimir a resposta do erro para mais detalhes
        try:
            print(f"   -> Detalhe do erro: {e.response.text}")
        except Exception:
            pass
        return None
    except Exception as e:
        print(f"❌ ERRO inesperado durante a raspagem da API: {e}")
        return None