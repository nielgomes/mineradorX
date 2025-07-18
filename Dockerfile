# Imagem base CUDA com toolkit e compiladores
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Configura variáveis de ambiente para instalações não interativas
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Instala todas as dependências do sistema necessárias, SEM venv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    python3-pip \
    python3-dev \
    python3-venv \
    libopenblas-dev \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncursesw5-dev \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    ccache \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria um link simbólico para que possamos usar 'python' em vez de 'python3'
RUN ln -s /usr/bin/python3 /usr/bin/python
# Cria um link simbólico para a biblioteca stub da CUDA em um local padrão.
# Isso força o linker a encontrar a 'libcuda.so.1' durante a compilação.
# Este caminho foi verificado com o seu comando 'find'.
RUN ln -s /usr/local/cuda-12.1/targets/x86_64-linux/lib/stubs/libcuda.so /usr/lib/x86_64-linux-gnu/libcuda.so.1

# Define APENAS as variáveis necessárias para o BUILD, sem conflitos.
# LDFLAGS aponta para o caminho exato que descobrimos com o comando 'find'.
ENV LDFLAGS="-L/usr/local/cuda-12.1/targets/x86_64-linux/lib/stubs"
ENV CMAKE_ARGS="-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52;61;70;75;80;86"
ENV FORCE_CMAKE=1

# Atualiza pip e instala as dependências Python no ambiente global do contêiner
RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Atualiza pip, setuptools, wheel e instala huggingface-hub para cache eficiente
RUN pip install --upgrade pip setuptools wheel huggingface-hub>=0.30.2
# Instala o pacote llama-cpp-python com suporte a CUDA
RUN pip install llama-cpp-python==0.3.13
# Baixa TODOS os pacotes de dados do NLTK de uma vez para garantir que 
# todas as dependências de idioma e tokenização estejam presentes. Descomente se quiser baixar todos os pacotes.
# RUN python -m nltk.downloader all
# Baixa apenas os pacotes essenciais do NLTK para tokenização e stopwords
# em múltiplos idiomas, incluindo português e inglês.
RUN python -m nltk.downloader punkt stopwords wordnet omw-1.4 averaged_perceptron_tagger


# Define o diretório de trabalho da aplicação
WORKDIR /app

# Copia o código da aplicação para dentro do container
COPY . .

# Deixa os scripts executáveis
RUN chmod +x ./*.sh

# Porta exposta para acesso externo
EXPOSE 8000

# Comando padrão
CMD ["bash"]