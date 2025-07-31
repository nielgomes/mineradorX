#!/bin/bash

# ==============================================================================
#           SCRIPT PARA INICIAR O SERVIDOR GATEWAY DE IA NO DOCKER
# ==============================================================================
#
# Este script verifica se o servidor Uvicorn já está em execução DENTRO do
# container 'ia-gateway'. Se não estiver, ele o inicia. Se já estiver,
# apenas exibe um aviso.
#
# A lógica inteira é executada no container para garantir a verificação
# correta do processo.
#
# ==============================================================================

echo "--- Verificando e Iniciando o Servidor Gateway de IA no container ---"

# Executa um script shell multilinhas dentro do container 'ia-gateway'
# Este comando único faz a verificação e a inicialização no mesmo contexto.
docker compose exec ia-gateway /bin/bash -c '
    # 1. Verifica se o processo do servidor já está rodando DENTRO deste container
    if pgrep -f "uvicorn servidor_modelo_local:app" > /dev/null; then
        # Se já estiver rodando, exibe um aviso claro e sai com sucesso
        echo "✅ AVISO: O servidor já está em execução no container."
        echo "   Para interagir com ele, execute em outro terminal:"
        echo "   docker compose exec ia-gateway ./2_chat.sh"
        exit 0
    fi

    # 2. Se não estiver rodando, inicia o servidor Uvicorn
    echo "-> Servidor não encontrado. Iniciando um novo processo Uvicorn..."
    echo "   O servidor ficará rodando em primeiro plano neste terminal."
    echo "   Para pará-lo, pressione CTRL+C."
    echo "---------------------------------------------------------------------"

    # Inicia o servidor em modo de recarga, acessível de fora do container
    uvicorn servidor_modelo_local:app --reload --host 0.0.0.0 --port 8000
'

echo "---------------------------------------------------------------------"
echo "   Script finalizado. O servidor (se iniciado) está no processo acima."
echo "---"
