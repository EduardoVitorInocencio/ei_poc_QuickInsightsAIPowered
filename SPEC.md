# Quick Insights - Especificacao

## 1. Objetivo

Aplicacao com agentes especializados para:

- consultar um modelo estrela de vendas no SQLite;
- obter informacoes de ferramentas externas;
- responder varias perguntas em uma execucao;
- exportar insights de vendas, opcionalmente, para PowerPoint ou Markdown;
- expor a mesma capacidade via API HTTP com FastAPI e Swagger.

Nenhum arquivo deve ser gerado antes da confirmacao do usuario.

## 2. Agentes

### SalesAgent

Responsavel exclusivamente por perguntas sobre os dados de vendas.

Ferramentas permitidas:

- `inspect_sales_schema`
- `run_sql_query`
- `submit_sales_insight`

Fluxo:

1. inspecionar o schema quando necessario;
2. gerar e executar SQL SELECT;
3. analisar somente o resultado retornado;
4. registrar `result_id`, titulo, headline e breve analise;
5. retornar o insight em texto;
6. nao criar arquivos.

Depois das respostas, a interface pergunta se o usuario deseja gerar output.
As opcoes sao:

- nenhum arquivo;
- PowerPoint (`pptx`);
- Markdown (`markdown`).

### ExternalToolsAgent

Responsavel exclusivamente por perguntas que dependem de fontes externas.

Ferramentas atuais:

- `get_current_weather`

Regras:

- nao acessa o SQLite;
- nao usa ferramentas do SalesAgent;
- nao registra insights para exportacao;
- nao gera PowerPoint ou Markdown;
- retorna apenas uma resposta textual fundamentada na ferramenta.

## 3. Roteamento

`QuestionProcessingService` classifica cada pergunta:

- termos meteorologicos sao enviados ao `ExternalToolsAgent`;
- demais perguntas sao enviadas ao `SalesAgent`.

O roteador e deterministico e pode ser substituido futuramente por um agente
especializado de classificacao.

Se todas as perguntas forem externas, a interface nao solicita banco ou Excel.

## 4. Arquitetura

```text
app/
|-- agent/
|   |-- external_tools_agent.py
|   |-- prompts.py
|   |-- sales_agent.py
|   |-- sql_validator.py
|   `-- tools.py
|-- api/
|   |-- app.py
|   |-- main.py
|   |-- question_loader.py
|   |-- schemas.py
|   `-- service.py
|-- cli/
|   |-- console.py
|   |-- data_source.py
|   `-- runner.py
|-- db/
|   `-- database.py
|-- domain/
|   `-- sales_model.py
|-- ingestion/
|   |-- excel_to_sqlite.py
|   `-- transformations.py
|-- llm/
|   |-- chat_tools.py
|   `-- providers.py
|-- services/
|   |-- exports.py
|   |-- insights.py
|   |-- markdown.py
|   |-- powerpoint.py
|   |-- query_results.py
|   |-- question_processing.py
|   |-- sales_insights.py
|   `-- weather.py
|-- bootstrap.py
`-- config.py

main.py
tests/
```

### Dependencias

- `domain` nao depende de agentes ou infraestrutura;
- `services` implementam capacidades reutilizaveis;
- cada agente recebe apenas seu proprio `ToolRegistry`;
- `llm` concentra configuracao e adaptacao dos provedores;
- `cli/console.py` trata somente entrada, validacao e apresentacao;
- `cli/data_source.py` coordena reutilizacao do banco e ingestao do Excel;
- `cli/runner.py` executa o fluxo interativo usando dependencias injetaveis;
- `bootstrap.py` conecta implementacoes concretas;
- `main.py` e somente o entrypoint e delega o fluxo para `run_cli`.

## 5. API HTTP

A API usa FastAPI, expõe Swagger em `/docs` e OpenAPI em `/openapi.json`, e
reutiliza o mesmo núcleo de serviços da CLI.

### Rotas

- `GET /health`
  - retorna status de disponibilidade.
- `GET /data/status`
  - expõe o estado atual da base e se uma carga foi feita.
- `POST /data/load`
  - carrega um workbook Excel enviado por upload;
  - opcionalmente reutiliza o banco atual se `reuse_existing=true`;
  - marca a sessão da API como pronta para perguntas.
- `POST /questions`
  - recebe uma lista de perguntas em JSON;
  - aceita `output_format` com `none`, `pptx` ou `markdown`.
- `POST /questions/excel`
  - recebe um Excel com perguntas;
  - extrai as perguntas de uma ou mais abas;
  - executa o mesmo fluxo da rota JSON.

### Regras

- a API nao substitui a CLI; ela reutiliza os mesmos servicos;
- perguntas so podem ser processadas depois de uma carga explicita;
- upload de perguntas em Excel aceita uma coluna nomeada `Pergunta`,
  `Question`, `Perguntas` ou similares, ou usa a primeira coluna da aba;
- exportacao continua sob demanda, nunca automatica;
- o servidor e iniciado por `python -m app.api.main`;
- o Swagger UI e a documentacao oficial da API;
- o Postman deve consumir os mesmos endpoints descritos no Swagger.

## 6. Modelos e provedores

Os agentes usam o pacote oficial `openai` com Chat Completions e function
calling. O historico e mantido pela aplicacao para evitar dependencia de
recursos proprietarios de continuidade.

Provedores nativos:

- OpenAI;
- Ollama local;
- Gemini;
- DeepSeek.

Todos sao tratados como endpoints OpenAI-compatible. O contrato comum fica em
`ModelConfig`, que define:

- `provider`;
- `model`;
- `api_key`;
- `base_url`.

`SalesAgent` e `ExternalToolsAgent` possuem configuracoes independentes. A
precedencia das variaveis e:

1. configuracao especifica do agente, como `SALES_LLM_MODEL`;
2. configuracao global, como `LLM_MODEL`;
3. default cadastrado para o provedor.

O valor de `model` e livre, permitindo trocar modelos sem alterar codigo. Para
um novo endpoint compativel, usar `LLM_PROVIDER=custom` com modelo, base URL e
chave. Um provedor com regras proprias deve ser adicionado somente ao catalogo
em `app/llm/providers.py`, sem alterar os agentes.

Os schemas internos das tools sao convertidos por `chat_tools.py`. Recursos
nao universais, como strict mode, nao sao enviados aos outros provedores; a
validacao dos argumentos continua sendo responsabilidade da aplicacao.

## 7. Modelo de vendas

Tabela fato: `fact`.

Dimensoes:

- `dim_cliente`
- `dim_produto`
- `dim_grupo_produto`
- `dim_vendedor`
- `dim_data`

Regra de vendas:

```sql
SUM(fact.QtdItens * fact.ValorUnitario)
```

`ValorVenda` nao existe.

Relacionamentos:

- `fact.cdCliente = dim_cliente.cdCliente`
- `fact.cdVendedor = dim_vendedor.cdVendedor`
- `fact.cdProduto = dim_produto.cdProduto`
- `fact.DataEmissao = dim_data.Data`
- `fact.DataVencimento = dim_data.Data`
- `dim_produto.cdGrupo = dim_grupo_produto.cdGrupo`

## 8. Fonte de dados

Quando existe pelo menos uma pergunta de vendas:

1. verificar tabelas, colunas e registros do banco;
2. validar duplicidades e relacionamentos orfaos;
3. perguntar se os dados existentes devem ser usados;
4. se nao, solicitar um `.xlsx` ou `.xlsm`;
5. validar e carregar o modelo em uma transacao.

Perguntas exclusivamente externas ignoram esse fluxo.

## 9. Seguranca SQL

- somente uma instrucao `SELECT`;
- `fact` obrigatoria como tabela principal;
- somente tabelas autorizadas;
- comentarios SQL bloqueados;
- comandos de escrita, DDL, `PRAGMA`, `ATTACH`, `DETACH` e `VACUUM`
  bloqueados;
- toda consulta passa por `SqlValidator`.

## 10. Insights e exportacao

`submit_sales_insight` registra:

- pergunta;
- `result_id`;
- titulo;
- headline;
- analise breve.

O resultado SQL permanece no `QueryResultStore`.

### PowerPoint

- um slide por insight;
- titulo e headline;
- tabela com ate 15 linhas e 8 colunas.

### Markdown

- uma secao por insight;
- pergunta;
- headline;
- analise;
- tabela com os dados.

Variaveis:

```dotenv
PPTX_OUTPUT_PATH=app/data/output/insight_slide.pptx
MARKDOWN_OUTPUT_PATH=app/data/output/insights.md
```

## 11. Meteorologia

`WeatherService` usa Open-Meteo:

1. geocodifica cidade e pais;
2. consulta condicoes atuais;
3. retorna local, horario, condicao, temperatura, sensacao, umidade,
   precipitacao e vento.

Nao exige chave adicional e nao gera artefatos.

## 12. Testes

```powershell
python -m unittest discover -s tests -v
```

Os testes devem cobrir:

- ingestao e integridade;
- seguranca SQL;
- isolamento das tools de cada agente;
- configuracao global e independente de provedores/modelos;
- adaptacao dos schemas para Chat Completions;
- roteamento;
- API com FastAPI, Swagger e OpenAPI;
- meteorologia sem rede;
- ausencia de exportacao automatica;
- PowerPoint e Markdown sob demanda.
