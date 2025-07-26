# mineradorX only cloud
## Trata-se de uma solução para interação com Agentes de IA com uso de modelos disponíveis no openrouter.ai.

### INSTALAÇÃO:

Requisitos:
- Docker Compose (a V2) - versão mais moderna do Docker Compose (a V2), que funciona como um plugin direto do Docker e é invocada com docker compose (sem o hífen).
- Se quiser alterar o modelo em nuvem antes de construir a imagem, vá para o item 1, depois volte para a letra a).

Procedimentos iniciais:

a) criar um arquivo .env na pasta do projeto mineradorX contendo:
```
# Chave da API do OpenRouter
OPENROUTER_API_KEY="sua chave api do openrouter.ai"
```
b) entrar na pasta do projeto mineradorX e rodar o comando:
`docker compose up --build -d`

c) após criação da imagem e a configuração do docker, digite o comando a seguir no terminal:
```
docker compose exec ia_gateway /bin/bash
```
e vá para o item 2

### Para iniciar o as interações com perguntas e respostas com o agente de IA:

1- Arquivo `config_modelo_local.json`

1.1- Esse arquivo é o resposável pelo apontamenteo de qual modelo Principal vc irá usar para interação. Se vc quiser alterar o modelo Principal Geral em nuvem (openrouter) como seu modelo __Principal/Geral__, o sistema terá como padrão o modelo `deepseek/deepseek-chat:free`, caso vc queira indicar um outro modelo basta entrar no portal <https://openrouter.ai/models> e escolher um dos modelos copiando seu nome no formato `deepseek/deepseek-chat:free` e substituindo na chave __id_openrouter__ da chave __gerador_principal__ no arquivo `config_modelo_local.json`, fique atento que existem modelos que são pagos.
 
2- Para interagir com o modelo escolhido:

2.1- espere o container subir, depois de concluído o processo do servidor, `docker compose exec ia_gateway /bin/bash` e depois rodar o comando `./2_chat.sh`

2.2- inicie a interação conforme orietações em tela.

3- Arquivo `prompts.json`

3.1- É o arquivo de meta-prompt para construção de prompt técnico para uso durante as interações com o Agente. Fique a vontade para customizá-lo conforme a sua necessidade.

4- Após cada alteração que, por ventura, vc fizer nos aquivos, vc deve parar o container `docker compose down` e subí-lo novamente `docker compose up --build -d`.
