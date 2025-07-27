#!/bin/bash

echo "--- Iniciando a interface do cliente no contêiner ---"

# Executa o serviço 'cliente' definido no docker-compose.yml de forma interativa
docker compose run --rm cliente