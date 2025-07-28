import re
import json
import httpx
from typing import Dict, Optional, Tuple
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async # Importamos nossa ferramenta de camuflagem

def extract_shopee_ids(url: str) -> Optional[Tuple[str, str]]:
    """Extrai o shop_id e o item_id de uma URL da Shopee de forma mais robusta."""
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
    Implementa a estratégia de ataque híbrido com camuflagem (stealth) e diagnóstico.
    """
    print(f"\n-> Iniciando raspagem CAMUFLADA para a URL: {url}")
    
    async with async_playwright() as p:
        browser = None # Inicializa a variável do browser
        try:
            # --- FASE 1: INFILTRAÇÃO COM PLAYWRIGHT E STEALTH ---
            print("   -> Fase 1: Lançando navegador camuflado...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            # ** APLICA A CAMUFLAGEM ANTES DE QUALQUER NAVEGAÇÃO **
            await stealth_async(page)

            print("   -> Navegando para a página do produto...")
            await page.goto(url, timeout=60000, wait_until='domcontentloaded')

            # ** LÓGICA DE DIAGNÓSTICO E ESPERA **
            try:
                # Aumentamos o timeout e esperamos por um seletor mais genérico primeiro
                print("   -> Aguardando o carregamento dinâmico da página...")
                await page.wait_for_selector('div[class*="page-product"]', timeout=45000)
                print("   -> Seletor do produto encontrado. Página principal carregada.")
            except Exception as e:
                # Se o seletor não for encontrado, salvamos um screenshot para diagnóstico
                screenshot_path = "shopee_debug_screenshot.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"❌ ERRO: O seletor esperado não foi encontrado (Timeout).")
                print(f"   -> A página pode ter um CAPTCHA ou layout inesperado.")
                print(f"   -> Screenshot de depuração salvo em: {screenshot_path}")
                raise e # Propaga o erro para ser capturado pelo bloco principal

            print("   -> Extraindo cookies...")
            cookies = await context.cookies()
            
            if not cookies:
                print("❌ ERRO: Não foi possível obter cookies mesmo com a página carregada.")
                return None

            csrf_token_cookie = next((cookie for cookie in cookies if cookie['name'] == 'csrftoken'), None)
            if not csrf_token_cookie:
                print("❌ ERRO: 'csrftoken' não encontrado nos cookies extraídos.")
                return None
            
            csrf_token = csrf_token_cookie['value']
            print(f"   -> Cookie 'csrftoken' obtido com sucesso: ...{csrf_token[-6:]}")
            
            # --- FASE 2: EXTRAÇÃO COM HTTPX ---
            print("   -> Fase 2: Preparando cliente HTTP com os cookies obtidos...")
            ids = extract_shopee_ids(page.url)
            if not ids:
                print(f"❌ ERRO: Não foi possível extrair IDs da URL final: {page.url}")
                return None
            shop_id, item_id = ids

            async with httpx.AsyncClient(cookies={c['name']: c['value'] for c in cookies}) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrf_token,
                    'Referer': page.url,
                }
                client.headers.update(headers)
                
                api_url = f"https://shopee.com.br/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
                print(f"   -> Acessando a API interna com sessão validada...")
                
                api_response = await client.get(api_url)
                api_response.raise_for_status()
                json_data = api_response.json()

                if json_data.get('error') or not json_data.get('data'):
                    error_msg = json_data.get('error_msg', 'Resposta da API vazia ou com erro.')
                    print(f"❌ ERRO da API: {error_msg}")
                    return None

                item_data = json_data.get('data', {})
                product_data = {
                    "source_url": url,
                    "title": item_data.get("name", "Título não encontrado"),
                    "price": f"R$ {item_data.get('price', 0) / 100000.0:.2f}",
                    "rating_score": f"{item_data.get('item_rating', {}).get('rating_star', 0):.1f} estrelas",
                    "units_sold": f"{item_data.get('historical_sold', 0)} vendidos", 
                    "description": item_data.get("description", "Descrição não encontrada").replace('\n', ' ').strip()
                }
                
                print("✅ Dados do produto extraídos com sucesso via ATAQUE HÍBRIDO CAMUFLADO!")
                return product_data

        except Exception as e:
            print(f"❌ ERRO GERAL durante a raspagem híbrida: {e}")
            return None
        finally:
            # Garante que o navegador seja sempre fechado
            if browser:
                await browser.close()