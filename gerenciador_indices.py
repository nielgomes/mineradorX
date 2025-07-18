import os
import json
import shutil
import argparse
import re # Importado para expressões regulares
import nltk # Importado para tokenização de sentenças
from typing import List

# Dependências Langchain
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Dependência para extração de conteúdo web
from newspaper import Article, Config

# --- INÍCIO DA NOVA SEÇÃO DE PROCESSAMENTO DE DOCUMENTOS ---

# Garante que o 'punkt' do NLTK esteja disponível
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("-> Pacote 'punkt' do NLTK não encontrado. Baixando agora...")
    nltk.download('punkt', quiet=True)
    print("✅ Pacote 'punkt' pronto.")

def aplicar_limpeza_e_formatacao(texto: str) -> str:
    """
    Combina as melhores técnicas de limpeza e formatação dos seus scripts.
    - Remove espaços excessivos e linhas em branco.
    - Aplica formatação inline para caminhos e variáveis.
    """
    # Remove múltiplos espaços, deixando apenas um
    texto = re.sub(r' +', ' ', texto)
    # Remove múltiplas quebras de linha, deixando no máximo duas
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    
    # Aplica formatação inline (` `) para elementos técnicos (do refatorador_rag.py)
    texto = re.sub(r'((?<=[\s,(])(/|./)[\w./\-_]+)', r'`\1`', texto) # Caminhos de arquivo
    texto = re.sub(r'(\$\w+)', r'`\1`', texto) # Variáveis de ambiente
    texto = re.sub(r'(\b[A-Z_]{3,}=[\w"\./\-_]+)', r'`\1`', texto) # Constantes
    return texto.strip()

def chunkificar_texto_aprimorado(texto_completo: str, metadados_origem: dict) -> List[Document]:
    """
    Função de chunking que une as lógicas do chunker_customizado.py e refatorador_rag.py.
    - Protege blocos de código.
    - Divide o texto em sentenças.
    - Agrupa sentenças até atingir um tamanho mínimo.
    - Retorna uma lista de `Document` do Langchain.
    """
    TAMANHO_MINIMO_CHUNK = 250 # Um bom ponto de partida

    # 1. Proteger blocos de código
    blocos_codigo = re.findall(r'(```.*?```)', texto_completo, re.DOTALL)
    placeholder_template = "__CODE_BLOCK_PLACEHOLDER_{}__"
    for i, bloco in enumerate(blocos_codigo):
        texto_completo = texto_completo.replace(bloco, placeholder_template.format(i), 1)

    # 2. Limpeza do texto principal
    texto_processado = aplicar_limpeza_e_formatacao(texto_completo)
    
    # 3. Chunking baseado em sentenças
    sentencas = nltk.sent_tokenize(texto_processado, language='portuguese')
    
    chunks_texto = []
    chunk_temporario = []
    char_count_temporario = 0

    for sentenca in sentencas:
        chunk_temporario.append(sentenca)
        char_count_temporario += len(sentenca)
        # Se o chunk atingiu o tamanho mínimo E termina com pontuação final, nós o fechamos.
        if char_count_temporario >= TAMANHO_MINIMO_CHUNK and sentenca.strip().endswith(('.', '!', '?')):
            chunks_texto.append(" ".join(chunk_temporario).strip())
            chunk_temporario = []
            char_count_temporario = 0
    
    # Adiciona o último chunk se sobrou algum
    if chunk_temporario:
        chunks_texto.append(" ".join(chunk_temporario).strip())

    # 4. Restaurar blocos de código e criar os Documentos finais
    documentos_finais = []
    for chunk in chunks_texto:
        # Verifica se algum placeholder está no chunk e o substitui
        for i, bloco in enumerate(blocos_codigo):
            placeholder = placeholder_template.format(i)
            if placeholder in chunk:
                chunk = chunk.replace(placeholder, bloco)
        documentos_finais.append(Document(page_content=chunk, metadata=metadados_origem.copy()))

    # 5. Adicionar os blocos de código como Documentos individuais para garantir a indexação
    for bloco in blocos_codigo:
        documentos_finais.append(Document(page_content=bloco, metadata=metadados_origem.copy()))
        
    return documentos_finais

def carregar_e_dividir_documentos(fontes: List[str]) -> List[Document]:
    """
    Função totalmente refeita para carregar, pré-processar e dividir documentos
    usando a lógica de chunking aprimorada.
    """
    todos_os_chunks = []
    config_coletor = configurar_coletor_web()

    for fonte in fontes:
        documento_bruto = None
        if fonte.startswith("http://") or fonte.startswith("https://"):
            documento_bruto = raspar_conteudo_url(fonte, config_coletor)
        elif os.path.isfile(fonte):
            try:
                with open(fonte, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    documento_bruto = Document(page_content=conteudo, metadata={"source": fonte})
            except Exception as e:
                print(f"  ❌ ERRO ao ler o arquivo {fonte}: {e}")
        else:
            print(f"  ⚠️ AVISO: A fonte '{fonte}' não é uma URL válida nem um arquivo encontrado. Será ignorada.")

        if documento_bruto:
            # Em vez de usar um splitter genérico, aplicamos nossa lógica robusta
            chunks_do_documento = chunkificar_texto_aprimorado(
                documento_bruto.page_content, 
                documento_bruto.metadata
            )
            todos_os_chunks.extend(chunks_do_documento)
    
    print(f"\n  -> Total de fontes processadas: {len(fontes)}")
    print(f"  -> Total de chunks gerados após o processamento: {len(todos_os_chunks)}")
    return todos_os_chunks
    
# --- FIM DA NOVA SEÇÃO ---


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

# --- SEÇÃO DE GERENCIAMENTO DE ÍNDICES (sem alterações) ---

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


# --- BLOCO PRINCIPAL DE EXECUÇÃO (sem alterações) ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gerenciador de Índices RAG para criar, atualizar ou deletar índices.",
        formatter_class=argparse.RawTextHelpFormatter
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
    
    args = parser.parse_args()
    
    try:
        with open("contexts.json", 'r', encoding='utf-8') as f:
            CONTEXTOS_DISPONIVEIS = json.load(f)
    except FileNotFoundError:
        print("ERRO CRÍTICO: Arquivo 'contexts.json' não encontrado.")
        exit()
        
    if args.contexto not in CONTEXTOS_DISPONIVEIS:
        print(f"❌ ERRO: O contexto com ID '{args.contexto}' não foi encontrado em 'contexts.json'.")
        print("   Contextos disponíveis:", list(CONTEXTOS_DISPONIVEIS.keys()))
        exit()

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