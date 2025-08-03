# Usa a imagem Python oficial
FROM python:3.10-slim

# Configura variáveis de ambiente
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONPATH=/app

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências Python primeiro
COPY requirements.txt .

# --- PASSO DE DEBUG 1 ---
# Mostra o conteúdo do requirements.txt que o Docker está vendo.
#RUN echo "--- Verificando o conteúdo de requirements.txt ---" && cat requirements.txt && echo "---------------------------------------------"


RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- PASSO DE DEBUG 2 ---
# Mostra a lista de pacotes que foram realmente instalados.
#RUN echo "--- Verificando os pacotes instalados com pip list ---" && pip list && echo "----------------------------------------------------"


# Baixa os pacotes de dados do NLTK
RUN python -m nltk.downloader punkt stopwords wordnet omw-1.4 averaged_perceptron_tagger

# Copia o código-fonte e as configurações
COPY ./src /app/src
COPY ./config /app/config
COPY 2_chat.sh .
RUN chmod +x ./*.sh

# Porta exposta
EXPOSE 8000