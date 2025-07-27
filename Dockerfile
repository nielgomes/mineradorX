# Usa a imagem Python oficial, leve e na versão correta
FROM python:3.10-slim

# Configura variáveis de ambiente essenciais
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONPATH=/app

# O apt-get agora é mínimo, não precisamos de Chrome nem git
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho da aplicação
WORKDIR /app

# Atualiza pip e instala as dependências Python
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baixa os pacotes de dados do NLTK
RUN python -m nltk.downloader punkt stopwords wordnet omw-1.4 averaged_perceptron_tagger

# Copia o código-fonte e as configurações para dentro da imagem
COPY ./src /app/src
COPY ./config /app/config
COPY 2_chat.sh .
RUN chmod +x ./*.sh

# Porta exposta para acesso externo
EXPOSE 8000