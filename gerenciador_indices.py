import os
import json
import shutil  # Biblioteca para operações de sistema de arquivos, como deletar diretórios
import argparse  # Biblioteca para parsear argumentos de linha de comando
from typing import List

# Dependências para processamento e indexação
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Dependência para extração de conteúdo web
from newspaper import Article, Config

# --- SEÇÃO DE COLETA WEB (sem alterações) ---

def configurar_coletor_web() -> Config:
    config = Config()
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    config.request_timeout = 20
    return config

def raspar_conteudo_url(url: str, config: Config) -> Document:
    try:
        print(f"      -> Processando URL: {url}")
        article = Article(url, config=config)
        article.download()
        article.parse()
        texto_limpo = article.text
        titulo = article.title
        data_publicacao = article.publish_date
        page_content = f"Título: {titulo}\n\n{texto_limpo}"
        metadata = {
            "source": url,
            "title": titulo,
            "publish_date": data_publicacao.strftime("%Y-%m-%d") if data_publicacao else "N/A"
        }
        print(f"      -> Título encontrado: '{titulo}'")
        return Document(page_content=page_content, metadata=metadata)
    except Exception as e:
        print(f"      ❌ ERRO ao processar a URL {url}: {e}")
        return None

# --- SEÇÃO DE PROCESSAMENTO DE DOCUMENTOS (sem alterações) ---

def carregar_e_dividir_documentos(fontes: List[str]) -> List[Document]:
    documentos_finais = []
    config_coletor = configurar_coletor_web()
    for fonte in fontes:
        if fonte.startswith("http://") or fonte.startswith("https://"):
            documento_raspado = raspar_conteudo_url(fonte, config_coletor)
            if documento_raspado:
                documentos_finais.append(documento_raspado)
        elif os.path.isfile(fonte):
            try:
                with open(fonte, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    doc = Document(page_content=conteudo, metadata={"source": fonte})
                    documentos_finais.append(doc)
            except Exception as e:
                print(f"  ❌ ERRO ao ler o arquivo {fonte}: {e}")
        else:
            print(f"  ⚠️ AVISO: A fonte '{fonte}' não é uma URL válida nem um arquivo encontrado. Será ignorada.")
    if not documentos_finais:
        return []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    documentos_divididos = text_splitter.split_documents(documentos_finais)
    print(f"\n  -> Total de documentos carregados: {len(documentos_finais)}")
    print(f"  -> Total de chunks gerados após a divisão: {len(documentos_divididos)}")
    return documentos_divididos

# --- SEÇÃO DE GERENCIAMENTO DE ÍNDICES (com nova função 'deletar') ---

def criar_ou_atualizar_indice(id_contexto: str, definicao_contexto: dict, embeddings_model):
    pasta_base_indices = "indices_rag"
    pasta_indice_final = os.path.join(pasta_base_indices, id_contexto)
    print(f"\n--- Processando Contexto: '{definicao_contexto['nome_exibicao']}' (ID: {id_contexto}) ---")
    fontes = definicao_contexto.get("fontes", [])
    if not fontes:
        print("  ⚠️ AVISO: Nenhuma fonte definida para este contexto. Pulando.")
        return
    print("  -> Fase 1: Carregando e dividindo documentos das fontes...")
    documentos_divididos = carregar_e_dividir_documentos(fontes)
    if not documentos_divididos:
        print("  ❌ ERRO: Nenhum documento pôde ser carregado. O índice não será criado.")
        return
    print("\n  -> Fase 2: Gerando embeddings e criando o índice FAISS...")
    db = FAISS.from_documents(documentos_divididos, embeddings_model)
    os.makedirs(pasta_indice_final, exist_ok=True)
    db.save_local(pasta_indice_final)
    print(f"✅ Índice para '{definicao_contexto['nome_exibicao']}' salvo com sucesso em '{pasta_indice_final}'")

def deletar_indice(id_contexto: str):
    """
    Deleta o diretório de um índice FAISS específico.
    """
    pasta_base_indices = "indices_rag"
    pasta_indice_final = os.path.join(pasta_base_indices, id_contexto)
    print(f"\n--- Tentando deletar o índice para o contexto: '{id_contexto}' ---")
    
    if os.path.isdir(pasta_indice_final):
        try:
            shutil.rmtree(pasta_indice_final)
            print(f"✅ Índice e diretório '{pasta_indice_final}' deletados com sucesso.")
        except OSError as e:
            print(f"❌ ERRO ao deletar o diretório '{pasta_indice_final}': {e}")
    else:
        print(f"⚠️ AVISO: Nenhum índice encontrado para '{id_contexto}' em '{pasta_indice_final}'. Nada a ser feito.")


# --- BLOCO PRINCIPAL DE EXECUÇÃO (Totalmente reescrito) ---

if __name__ == "__main__":
    # 1. Configura o parser de argumentos da linha de comando
    parser = argparse.ArgumentParser(
        description="Gerenciador de Índices RAG para criar, atualizar ou deletar índices.",
        formatter_class=argparse.RawTextHelpFormatter # Melhora a formatação da ajuda
    )
    parser.add_argument(
        "--acao",
        type=str,
        required=True,
        choices=["criar", "deletar"],
        help="A ação a ser executada:\n'criar'   - Cria um novo índice ou atualiza um existente.\n'deletar' - Deleta um índice existente."
    )
    parser.add_argument(
        "--contexto",
        type=str,
        required=True,
        help="O ID do contexto a ser processado (deve ser uma chave do arquivo 'contexts.json')."
    )
    
    # 2. Parseia os argumentos fornecidos pelo usuário
    args = parser.parse_args()
    
    # 3. Carrega as definições de contexto do arquivo JSON
    try:
        with open("contexts.json", 'r', encoding='utf-8') as f:
            CONTEXTOS_DISPONIVEIS = json.load(f)
    except FileNotFoundError:
        print("ERRO CRÍTICO: Arquivo 'contexts.json' não encontrado.")
        exit()
        
    # 4. Verifica se o contexto especificado existe no JSON
    if args.contexto not in CONTEXTOS_DISPONIVEIS:
        print(f"❌ ERRO: O contexto com ID '{args.contexto}' não foi encontrado em 'contexts.json'.")
        print("   Contextos disponíveis:", list(CONTEXTOS_DISPONIVEIS.keys()))
        exit()

    # 5. Executa a ação solicitada
    print(f"--- Gerenciador de Índices RAG (Ação: {args.acao.upper()}, Contexto: {args.contexto}) ---")
    
    if args.acao == 'criar':
        print("-> Carregando o modelo de embeddings (pode levar um momento)...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        print("✅ Modelo de embeddings carregado.")
        
        definicao_especifica = CONTEXTOS_DISPONIVEIS[args.contexto]
        criar_ou_atualizar_indice(args.contexto, definicao_especifica, embeddings)
        
    elif args.acao == 'deletar':
        deletar_indice(args.contexto)
        
    print("\n--- Operação concluída. ---")