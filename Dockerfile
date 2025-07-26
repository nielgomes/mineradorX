# Usa a imagem Python oficial, leve e na versão correta
FROM python:3.10-slim

# Configura variáveis de ambiente essenciais
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Instala apenas as dependências de sistema mínimas (git para o pip)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Atualiza pip e instala as dependências Python
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baixa os pacotes de dados do NLTK
RUN python -m nltk.downloader punkt stopwords wordnet omw-1.4 averaged_perceptron_tagger

# Define o diretório de trabalho da aplicação
WORKDIR /app

# Copia o código da aplicação
COPY . .

# Deixa os scripts executáveis
RUN chmod +x ./*.sh

# Porta exposta para acesso externo
EXPOSE 8000