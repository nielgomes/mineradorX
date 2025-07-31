#!/bin/bash

echo "--- Iniciando o interface de interação Gateway de IA ---"

# Executa o script Python diretamente
docker compose exec ia-gateway /bin/bash -c '
    # 1. Verifica se o servidor está rodando
    if ! pgrep -f "uvicorn servidor_modelo_local:app" > /dev/null; then
        echo "❌ ERRO: O servidor não está em execução. Por favor, inicie-o primeiro com:"
        echo "   docker compose exec ia-gateway ./1_run.sh"
        exit 1
    fi
    python assistente_contextual.py
'
# 2. Inicia o assistente contextual
echo "-> Iniciando a interface de interação com o Agente IA..."
echo "   Após a configuração, a interação deverá ser feita neste terminal."
echo "   Para sair da interação digite 'sair'."
echo "--------------------------------------------------------"
