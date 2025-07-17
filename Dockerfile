# Imagem base CUDA com toolkit e compiladores
FROM nvidia/cuda:12.0.1-devel-ubuntu22.04

# Configura variáveis de ambiente para instalações não interativas e Python UTF-8 
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    CUDA_HOME=/usr/local/cuda \
    PATH=/opt/venv/bin:/usr/local/cuda/bin:$PATH \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

# Instala dependências do sistema necessárias para build, Python e CUDA
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

# Cria e ativa ambiente virtual Python
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Define as flags que o pip usará para compilar o llama-cpp-python com suporte a GPU
ENV CMAKE_ARGS="-DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=52;61;70;75;80;86"
ENV FORCE_CMAKE=1

# Atualiza pip, setuptools, wheel e instala huggingface-hub para cache eficiente
RUN pip install --upgrade pip setuptools wheel huggingface-hub>=0.30.2

# Copia arquivo de requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Clone e build do llama.cpp com CUDA ativado (sem LD_LIBRARY_PATH para stubs)
RUN pip install llama-cpp-python

# Define diretório de trabalho da aplicação
WORKDIR /app

# Copia o código da aplicação para dentro do container
COPY . .

# Deixa os scripts executáveis
RUN chmod +x 1_run.sh 2_chat.sh

# Porta exposta para acesso externo
EXPOSE 8000

# Comando padrão, pode ser substituído na hora do run
CMD ["bash"]