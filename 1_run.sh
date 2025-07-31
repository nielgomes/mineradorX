#!/bin/bash

echo "--- Iniciando o Servidor Gateway de IA ---"

# 1. Verifica se o servidor já está rodando
if pgrep -f "uvicorn servidor_modelo_local:app" > /dev/null; then
    echo "⚠️  AVISO: O servidor já está em execução. Use ./2_chat.sh para se conectar."
    exit 1
fi

# 2. Inicia o servidor Uvicorn em PRIMEIRO PLANO
echo "-> Iniciando o servidor Uvicorn..."
echo "   Por favor, configure os serviços quando solicitado pelo script."
echo "   Após a configuração, o servidor ficará rodando neste terminal."
echo "   Para desligá-lo, pressione CTRL+C nesta janela."
echo "   Após subir o servidor, você pode acessar a interface em outro terminal com:"
echo "   docker compose exec ia-gateway ./2_chat.sh"
echo "--------------------------------------------------------"

# Inicia o servidor diretamente
docker compose exec ia-gateway /bin/bash -c "uvicorn servidor_modelo_local:app --reload --host 0.0.0.0"
