# src/reels_agent/scraper.py

import os
import json
import requests
import time
from typing import Dict, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

def scrape_shopee_product(url: str) -> Optional[Dict]:
    """
    Função refatorada para usar o Async Scraper da ScraperAPI,
    com lógica de parsing de JSON mais robusta.
    """
    SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
    if not SCRAPERAPI_KEY:
        print("❌ ERRO: Chave da ScraperAPI não encontrada no arquivo .env.")
        return None

    job_submission_payload = {
        'apiKey': SCRAPERAPI_KEY,
        'urls': [url],
        'apiParams': { 'render': 'true', 'country_code': 'br' }
    }
    
    print(f"-> Submetendo trabalho de scraping para a ScraperAPI: {url}")

    try:
        submit_response = requests.post('https://async.scraperapi.com/jobs', json=job_submission_payload, timeout=60)
        submit_response.raise_for_status()
        job_data = submit_response.json()
        status_url = job_data.get("statusUrl")

        if not status_url:
            print(f"❌ ERRO: A API não retornou uma URL de status. Resposta: {job_data}")
            return None

        print(f"   -> Trabalho submetido. Aguardando o resultado em: {status_url}")
        time.sleep(45)

        for attempt in range(3):
            result_response = requests.get(status_url, timeout=60)
            result_data = result_response.json()

            if result_data.get("status") == 'finished':
                print("   -> Trabalho concluído! Processando o HTML...")
                html_content = result_data['response']['body']
                soup = BeautifulSoup(html_content, 'html.parser')
                
                script_tag = soup.find("script", type="application/ld+json")
                if not script_tag:
                    print("❌ ERRO: O HTML foi retornado, mas os dados estruturados (JSON-LD) não foram encontrados.")
                    return None
                
                json_ld_data = json.loads(script_tag.string)
                
                product_info = None
                if isinstance(json_ld_data, list):
                    for item in json_ld_data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            product_info = item
                            break
                elif isinstance(json_ld_data, dict) and json_ld_data.get('@type') == 'Product':
                    product_info = json_ld_data

                if not product_info:
                    print("❌ ERRO: Objeto do tipo 'Product' não encontrado nos dados estruturados.")
                    return None

                # --- INÍCIO DA CORREÇÃO FINAL ---
                # Lógica "defensiva" para extrair os dados
                
                offers_data = product_info.get('offers', {})
                # Se 'offers' for uma lista, pega o primeiro item
                if isinstance(offers_data, list) and offers_data:
                    offers_data = offers_data[0]
                
                rating_data = product_info.get('aggregateRating', {})
                # Se 'aggregateRating' for uma lista, pega o primeiro item
                if isinstance(rating_data, list) and rating_data:
                    rating_data = rating_data[0]

                product_data = {
                    "source_url": url,
                    "title": product_info.get("name", "Título não encontrado"),
                    "price": f"{offers_data.get('priceCurrency', '')} {offers_data.get('price', 'Preço não encontrado')}",
                    "rating_score": f"{rating_data.get('ratingValue', 'N/A')} estrelas",
                    "review_count": f"{rating_data.get('reviewCount', '0')} avaliações",
                    "description": product_info.get("description", "Descrição não encontrada.").replace('\n', ' ')
                }
                # --- FIM DA CORREÇÃO FINAL ---
                
                print("✅ Dados do produto extraídos com sucesso via Async ScraperAPI!")
                return product_data
            
            elif result_data.get("status") == 'failed':
                print(f"❌ ERRO: O trabalho de scraping falhou. Motivo: {result_data.get('failReason', 'desconhecido')}")
                return None

            print(f"   -> O trabalho ainda está em andamento (status: {result_data.get('status')}). Tentando novamente em 15 segundos...")
            time.sleep(15)

        print("❌ ERRO: O trabalho de scraping não foi concluído a tempo.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ ERRO ao conectar com a ScraperAPI: {e}")
        return None
    except Exception as e:
        print(f"❌ ERRO inesperado durante a coleta de dados com a ScraperAPI: {e}")
        return None