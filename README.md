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

# mineradorX only cloud (English)

## This is a solution for interacting with AI Agents using models available on openrouter.ai.

### INSTALLATION:

**Requirements:**
- Docker Compose (V2) - the more modern version of Docker Compose (V2), which functions as a direct Docker plugin and is invoked with `docker compose` (without the hyphen).
- If you want to change the cloud model before building the image, go to item 1, then return to letter a).

**Initial Procedures:**

a) Create a `.env` file in the mineradorX project folder containing:
```
#OpenRouter API Key

OPENROUTER_API_KEY="your openrouter.ai api key"
```
b) Enter the mineradorX project folder and run the command:

`docker compose up --build -d`

c) After the image has been created and Docker is configured, type the following command in the terminal:
```
docker compose exec ia_gateway /bin/bash
```
and then proceed to item 2.

### To start the question and answer interactions with the AI agent:

**1- `config_modelo_local.json` File**

1.1- This file is responsible for specifying which Main model you will use for interaction. If you want to change the Main General cloud model (openrouter) to be your **Main/General** model, the system will default to the `deepseek/deepseek-chat:free` model. If you wish to specify another model, simply go to the <https://openrouter.ai/models> portal, choose a model, copy its name (in the `deepseek/deepseek-chat:free` format), and replace it in the **id_openrouter** key of the **gerador_principal** key in the `config_modelo_local.json` file. Be aware that some models are paid.

**2- To interact with the chosen model:**

2.1- Wait for the container to start up. After the server process is complete, run `docker compose exec ia_gateway /bin/bash` and then run the command `./2_chat.sh`.

2.2- Begin the interaction according to the on-screen instructions.

**3- `prompts.json` File**

3.1- This is the meta-prompt file for constructing a technical prompt for use during interactions with the Agent. Feel free to customize it to your needs.

**4- After any changes you might make to the files, you must stop the container with `docker compose down` and start it up again with `docker compose up --build -d`.**

