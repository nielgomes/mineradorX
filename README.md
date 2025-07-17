Trata-se de uma solução para inteteração com Agentes de IA com uso de modelos .GGUF local ou com uso de modelos disponíveis no openrouter.ai.

Para iniciar o as interções com perguntas e respostas com o agente de IA:

1- Primeiro iniciar o servidor de modelos locais e em nuvem rodando o comando ./1_run.sh dentro da pasta mineradorX
1.1- ao ser perguntado qual servidor vc quer utilizar como Sumarizador, se vc indicar que vc quer modelos locais (.gguf) o sistema buscará todos os modelos do tipo GGUF estão disponíveis no path ~/.cache/instructlab/models/ e disponibilizará para que vc consiga escolher um deles como seu modelo de sumarização.
1.1.1- Se vc indicar que vc quer um modelo em nuvem (openrouter) como seu modelo Sumarizador, o sistema terá como padrão o modelo qwen/qwen3-235b-a22b-04-28:free, caso vc queira indicar um outro modelo basta entrar no portal https://openrouter.ai/models e escolher um dos modelos copiando seu nome no formato qwen/qwen3-235b-a22b-04-28:free, fique atento que existem modelos que são pagos.
1.2- ao ser perguntado qual servidor vc quer utilizar como Principal Geral, se vc indicar que vc quer modelos locais (.gguf) o sistema buscará todos os modelos do tipo GGUF estão disponíveis no path ~/.cache/instructlab/models/ e disponibilizará para que vc consiga escolher um deles como seu modelo de sumarização.
1.2.1- Se vc indicar que vc quer um modelo em nuvem (openrouter) como seu modelo Principal/Geral, o sistema terá como padrão o modelo deepseek/deepseek-chat:free, caso vc queira indicar um outro modelo basta entrar no portal https://openrouter.ai/models e escolher um dos modelos copiando seu nome no formato deepseek/deepseek-chat:free, fique atento que existem modelos que são pagos.

ATENÇÃO: Caso vc selecione um modelo local como Sumarizador e um modelo tambem local como Principal, sua maquina pode ficar lenta caso os dois modelos pesem para seu hardwares roda-los ao mesmo tempo. Para hardwares mais fracos, sugerimos rodar no máximo um modelo local.

Quando quiser utilizar outros modelos gguf locais, basta salva-los em ~/.cache/instructlab/models/ .
 
2- Para interagir com o modelo escolhido:
2.1- espere o servidor subir, depois de concluído o processo do servidor, basta abrir um outro teminal, navegar até a pasta mineradorX e rodar o comando ./2_chat.sh
2.2- o sistema perguntar qual o modo de operação vc usará:
2.2.1- modo Conversa Geral - Trata-se de modelo geral sem vinculo a nenhum indice RAG modelo não especialista
2.2-2- modo Especialistas RAG - Trata-se de modelos especialistas em algum assunto com base em RAGs.
2.2.2.1- o sistema iniciará o seu ambiente de interação verificará se vc possui agentes especialistas treinados com RAG e devidamente indexados com base no arquivo contexts.json. Ele pedira para que vc indique qual dos especialistas vc quer usar. 
2.2.2.2- Se vc selecionar algum dos especialistas, o sistema perguntará se vc quer utilizar o Sumarizador, devendo responder com s ou n. Se usar o sumarizador, o sistema resumirá seu prompt + pergunta + contexto RAG, antes de perguntar para o seu modelo Principal. Se vc não utilizar o sumarizador o prompt + pergunta + contexto RAG diretamente para o modelo Princialm sem passar por uma sumarização.
2.2.3- modo Analizar Documentos - Este modo só funciona com modelo Princial seja um modelo em nuvem. Esse modo não funciona com modelos locais.
2.2.3.1- ele se baseia no arquivo context.json na chave df_openrouter, na lista de fonte basta informar o path e nome dos arquivos do tipo texto (txt ou json) ou tipo pdf.

3- Criar embeedings RAG e especialistas para interagirem no modo especialista:
3.1- no arquivo contexts.json inserir/criar uma chave com as seguintes sub chaves: nome_exibicao e fontes.
3.2- após criado a chave e suas subchaves, dentro da pasta mineradorX, rodar o comando python gerenciador_indices --acao criar --contexto nomedasuachave, o sistem criará o novo especialista e o indexará para possibilitar interações com ele.

4- Apagar embeedings RAG e especialistas:
4.1- dentro da pasta mineradorX, rodar o comando python gerenciador_indices --acao deletar --contexto nomedasuachave, o sistem apagará as pastas de indices dp especialista.
4.2- no arquivo contexts.json apagar a chave com as suas seguintes sub chaves: nome_exibicao e fontes, para que ele não fique aparecendo durante a seleção do item 2.

5- Atualizar embeedings RAG de especialistas existentes:
5.1- dentro da pasta mineradorX, rodar o comando python gerenciador_indices --acao criar --contexto nomedasuachave(do arquivo contexts.json), o sistem atualizará o especialista e o indexará para possibilitar interações com ele.