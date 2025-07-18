# mineradorX
## Trata-se de uma solução para interação com Agentes de IA com uso de modelos .GGUF local ou com uso de modelos disponíveis no openrouter.ai.

### INSTALAÇÃO:

Requisitos:
- Docker Compose (a V2) - versão mais moderna do Docker Compose (a V2), que funciona como um plugin direto do Docker e é invocada com docker compose (sem o hífen).
- Possuir placa de vídeo Nvidia na maquina host do container
- Estar com os drives da placa de vídeo atualizados
- Instalar o toolkit CUDA na maquina host do container
- Testado em uma maquina com Windows 11 com container rodando no WSL Ubuntu e placa de vídeo Nvidia RTX 4060.

a) criar um arquivo .env na pasta do projeto mineradorX contendo:
```
# Chave da API do OpenRouter
OPENROUTER_API_KEY="sua chave api do openrouter.ai"
```
b) entrar na pasta do projeto mineradorX e rodar o comando:
`docker compose up --build -d`

c) após criação da imagem e a configuração do docker, digite o comando a seguir no terminal e vá para o item 1:
```
docker compose exec ia-gateway /bin/bash
```
d) após carregado o servidor item c, abra um novo terminal e digite o comando abaixo e vá para o item 2:
```
docker compose exec ia-gateway /bin/bash
```
### Para iniciar o as interações com perguntas e respostas com o agente de IA:

1- Primeiro iniciar o servidor de modelos locais e em nuvem rodando o comando `./1_run.sh` dentro da pasta mineradorX

1.1- ao ser perguntado qual servidor vc quer utilizar como Sumarizador, se vc indicar que vc quer modelos locais (.gguf) o sistema buscará todos os modelos do tipo GGUF estão disponíveis no path `~/.cache/instructlab/models/` e disponibilizará para que vc consiga escolher um deles como seu modelo de sumarização.

1.1.1- Se vc indicar que vc quer um modelo em nuvem (openrouter) como seu modelo Sumarizador, o sistema terá como padrão o modelo `qwen/qwen3-235b-a22b-04-28:free`, caso vc queira indicar um outro modelo basta entrar no portal [https://openrouter.ai/models](https://openrouter.ai/models) e escolher um dos modelos copiando seu nome no formato `qwen/qwen3-235b-a22b-04-28:free`, fique atento que existem modelos que são pagos.

1.2- ao ser perguntado qual servidor vc quer utilizar como Principal Geral, se vc indicar que vc quer modelos locais (.gguf) o sistema buscará todos os modelos do tipo GGUF estão disponíveis no path `~/.cache/instructlab/models/` e disponibilizará para que vc consiga escolher um deles como seu modelo de sumarização.

1.2.1- Se vc indicar que vc quer um modelo em nuvem (openrouter) como seu modelo __Principal/Geral__, o sistema terá como padrão o modelo `deepseek/deepseek-chat:free`, caso vc queira indicar um outro modelo basta entrar no portal <https://openrouter.ai/models> e escolher um dos modelos copiando seu nome no formato `deepseek/deepseek-chat:free`, fique atento que existem modelos que são pagos.

__ATENÇÃO__: Caso vc selecione um modelo local como Sumarizador e um modelo tambem local como Principal, sua maquina pode ficar lenta caso os dois modelos pesem para seu hardwares roda-los ao mesmo tempo. Para hardwares mais fracos, sugerimos rodar no máximo um modelo local.

Quando quiser utilizar outros modelos gguf locais, basta salva-los em `~/.cache/instructlab/models/`.
 
2- Para interagir com o modelo escolhido:

2.1- espere o servidor subir, depois de concluído o processo do servidor, basta abrir um outro teminal, navegar até a pasta mineradorX e rodar o comando `./2_chat.sh`

2.2- o sistema perguntar qual o modo de operação vc usará:

2.2.1- __modo Conversa Geral__ - Trata-se de modelo geral sem vinculo a nenhum indice RAG modelo não especialista

2.2-2- __modo Especialistas RAG__ - Trata-se de modelos especialistas em algum assunto com indices em RAGs.

2.2.2.1- o sistema iniciará o seu ambiente de interação verificará se vc possui agentes especialistas treinados com RAG e devidamente indexados com base no arquivo `contexts.json`. Ele pedira para que vc indique qual dos especialistas vc quer usar.

2.2.2.2- Se vc selecionar algum dos especialistas, o sistema perguntará se vc quer utilizar o __Sumarizador__, devendo responder com __s__ ou __n__. Se usar o sumarizador, o sistema resumirá seu prompt + pergunta + contexto RAG, antes de perguntar para o seu modelo __Principal__. Se vc não utilizar o sumarizador o prompt + pergunta + contexto RAG diretamente para o modelo __Princial__ sem passar por uma sumarização.

2.2.3- __modo Analizar Documentos__ - Este modo __só funciona desde que o modelo Princial seja um modelo em nuvem no openrouter__. Esse modo __não funciona com modelos locais__.

2.2.3.1- ele se baseia no arquivo `context.json` na chave `df_openrouter`, na lista de fonte basta informar o path e nome dos arquivos do tipo texto (txt ou json) ou tipo pdf.

3- Criar embeedings RAG e especialistas para interagirem no modo especialista:

3.1- no arquivo `contexts.json` inserir/criar uma chave (alias escolhido por vc para ser usado como parametro contexto no gerenciador_indices.py) com as seguintes sub chaves: nome_exibicao e fontes (pode ser uma lista de URLs ou uma lista de arquivos TXT como base de conhecimento).

`nomedasuachave`: um alias para a sua chave dentro do `contexts.json`, ela servirá para vc mapea-la durante o uso do gerenciador_indices.py esse alias será o parametro __--contexto nomedasuachave__

`nome_exibicao`: esse é o nome do especialista que aparecerá para vc escolher no modo Especialista (item 2.2.2)

`fontes`: essa chave recebe uma lista [] com os path e arquivo da base deconhecimento, podendo ser arquivos TXT ou URL da internet.

3.2- após criado a chave e suas subchaves, entre na pasta mineradorX, rodar o comando `python gerenciador_indices --acao criar --contexto nomedasuachave`, o sistema criará o novo especialista e o indexará com os indices RAG do banco de dados vetorial para possibilitar interações com ele. A persistência dos banco de dados vetorial (FAISS) é pasta `indices_rag`, nela são salvos os indices de base de conhecimento dos seus especialistas.

4- Apagar embeedings RAG e especialistas:

4.1- dentro da pasta mineradorX, rodar o comando `python gerenciador_indices.py --acao deletar --contexto nomedasuachave`(do arquivo contexts.json), o sistem apagará as pastas de indices do especialista que fica dentro da pasta __indices_rag__.

4.2- no arquivo `contexts.json` vc tem que apagar a chave do __nomedasuachave__ com as suas seguintes sub chaves: __nome_exibicao__ e __fontes__, para que ele não fique aparecendo durante a seleção do item 2.2.2.

5- Atualizar embeedings RAG de especialistas existentes:

5.1- dentro da pasta `mineradorX`, rodar o comando `python gerenciador_indices.py --acao criar --contexto nomedasuachave`(do arquivo contexts.json), se você utilizar um __nomedasuachave__ que já existe no arquivo __contexts.json__, o sistem atualizará o respectivo especialista e o indexará para possibilitar interações com ele, considerando a atualização do sua base de conhecimento.
