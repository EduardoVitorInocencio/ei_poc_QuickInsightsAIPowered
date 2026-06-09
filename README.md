# Quick Insights AI Powered

Aplicacao com dois agentes especializados:

- `SalesAgent`: consulta vendas no SQLite e produz insights.
- `ExternalToolsAgent`: consulta ferramentas externas, atualmente meteorologia.

## Visao Geral

O projeto expoe a mesma capacidade por dois canais:

- CLI interativa em `main.py`.
- API HTTP em `app/api/main.py`.

O fluxo central e o mesmo nos dois casos:

1. preparar a base de dados;
2. receber perguntas;
3. classificar cada pergunta como vendas ou externa;
4. executar o agente correspondente;
5. registrar insights de vendas;
6. exportar somente sob demanda.

Os arquivos exportados sao nomeados com data e hora.
O Markdown exportado inclui o cabecalho `GENERATE BY AI` e a data de geracao.

## Arquitetura

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
streamlit_app.py
tests/
```

## Responsabilidades

- `main.py`: entrypoint da CLI.
- `streamlit_app.py`: entrypoint da interface Streamlit.
- `app/bootstrap.py`: monta o grafo completo da aplicacao.
- `app/config.py`: carrega configuracao do ambiente e define defaults.
- `app/domain/sales_model.py`: fonte de verdade do modelo estrela.
- `app/db/database.py`: cria engine, inspeciona banco e valida integridade.
- `app/ingestion/`: normaliza e carrega Excel para SQLite.
- `app/agent/`: regras de cada agente, prompts, tools e validacao de SQL.
- `app/llm/`: adaptacao dos provedores e dos schemas de function calling.
- `app/services/`: processamento, armazenamento de resultados e exportacao.
- `app/cli/`: experiencia interativa no terminal.
- `app/api/`: rotas HTTP, schemas e adaptacao da camada web.
- `tests/`: cobertura automatizada dos contratos principais.

### Arquivos-chave

- `app/agent/sales_agent.py`: orquestra o ciclo de SQL, insights e tool-calling.
- `app/agent/external_tools_agent.py`: responde perguntas externas sem tocar o banco.
- `app/agent/sql_validator.py`: bloqueia SQL fora da politica permitida.
- `app/services/question_processing.py`: roteia perguntas entre os agentes.
- `app/services/insights.py`: valida e executa consultas seguras no SQLite.
- `app/services/exports.py`: coordena exportacao para PowerPoint ou Markdown.
- `app/services/markdown.py`: gera o Markdown final com timestamp e cabecalho.
- `app/services/powerpoint.py`: gera o PPTX final com timestamp no nome.
- `app/api/service.py`: controla estado da API, carga e execucao das perguntas.

## Fluxo De Funcionamento

### CLI

1. O usuario executa `python main.py`.
2. A aplicacao pergunta as perguntas uma por linha.
3. O sistema avalia se existem dados validos no banco.
4. Se necessario, o usuario confirma se pode reutilizar a base atual.
5. As perguntas sao classificadas em vendas ou externas.
6. O `SalesAgent` consulta o SQLite por meio de tools autorizadas.
7. O `ExternalToolsAgent` consulta somente ferramentas externas.
8. Os insights de vendas sao registrados em memoria.
9. A exportacao e oferecida somente ao final, se o usuario confirmar.
10. O arquivo final recebe data e hora no nome.

### API

1. O servidor sobe em `app/api/main.py`.
2. `GET /data/status` mostra o estado atual da base.
3. `POST /data/load` carrega um Excel ou reutiliza o banco atual.
4. `POST /questions` recebe perguntas em JSON.
5. `POST /questions/excel` recebe perguntas em planilha.
6. O `QuestionProcessingService` classifica e executa as perguntas.
7. Se houver vendas e `output_format` for `pptx` ou `markdown`, a exportacao acontece sob demanda.
8. O arquivo gerado inclui timestamp no nome.
9. O Markdown inclui `GENERATE BY AI` e a data de geracao.

## Pontos Importantes

- O modelo de vendas usa a tabela `fact` como fato principal.
- `ValorVenda` nao existe; a regra e `SUM(fact.QtdItens * fact.ValorUnitario)`.
- O `SalesAgent` nao recebe ferramentas externas.
- O `ExternalToolsAgent` nao recebe acesso ao SQLite.
- O SQL passa por validacao antes de tocar o banco.
- Exportacao nao acontece automaticamente; depende da escolha do usuario.
- Arquivos exportados nao sobrescrevem o nome base, pois recebem timestamp.
- O Markdown exportado sempre inclui o cabeçalho exigido pela aplicacao.
- `ollama` e o provedor padrao quando nenhuma variavel de provider e definida.

## Execucao

```powershell
uv sync
uv run python main.py
```

Para abrir a interface visual em Streamlit:

```powershell
uv run streamlit run streamlit_app.py
```

A interface Streamlit usa a mesma camada de dominio da CLI, mas e isolada da
API HTTP. Ela permite escolher o provider no painel lateral e envia as
mensagens para o mesmo fluxo de agentes.

Na tela existem tres areas:

- `Chat`: conversa com o bot usando o provider selecionado.
- `Carregar dados`: envia um Excel de vendas e popula o SQLite.
- `Excel de perguntas`: extrai a lista de perguntas de um Excel e gera um
  Markdown executando o fluxo de LLM e exportação do projeto.

Para iniciar a API com Swagger:

```powershell
uv run python -m app.api.main --host 127.0.0.1 --port 8000
```

Informe varias perguntas e finalize com uma linha vazia:

```text
Pergunta 1: Total de vendas por UF
Pergunta 2: Como esta o clima em Sao Paulo, Brasil?
Pergunta 3:
```

Perguntas de vendas usam o banco. Perguntas meteorologicas usam a Open-Meteo e
retornam somente texto.

Depois dos insights de vendas, o sistema pergunta:

```text
Deseja gerar um output com os insights de vendas? [s/n]:
```

Ao responder `s`, escolha:

```text
Escolha o formato do output [pptx/markdown]:
```

O PowerPoint possui uma pagina por insight. O Markdown inclui perguntas,
headlines, analises breves e tabelas. Respostas do `ExternalToolsAgent` nunca
sao adicionadas aos arquivos.

## API HTTP

A API expõe o mesmo nucleo da CLI, mas por rotas. O Swagger fica em
`http://127.0.0.1:8000/docs` e o schema OpenAPI em
`http://127.0.0.1:8000/openapi.json`.

- `POST /data/load` carrega ou reutiliza os dados do SQLite;
- `POST /questions` recebe perguntas em JSON;
- `POST /questions/excel` recebe um Excel com perguntas;
- `GET /data/status` mostra o estado atual da base.

Fluxo recomendado:

1. carregar os dados com `POST /data/load`;
2. enviar perguntas com `POST /questions` ou `POST /questions/excel`;
3. informar `output_format=none`, `pptx` ou `markdown`.

### Como testar no Swagger

1. Abra `http://127.0.0.1:8000/docs`.
2. Execute `POST /data/load` para carregar um arquivo Excel ou reutilizar o
   banco existente.
3. Execute `POST /questions` para perguntas em JSON.
4. Execute `POST /questions/excel` para enviar uma planilha com perguntas.
5. Em cada chamada, escolha `output_format` como `none`, `pptx` ou
   `markdown`.

### Como testar no Postman

1. Crie uma requisição `POST http://127.0.0.1:8000/data/load`.
2. Para recarregar dados, envie `multipart/form-data` com:
   - campo `reuse_existing=false`;
   - arquivo `excel_file`.
3. Crie uma requisição `POST http://127.0.0.1:8000/questions`.
4. Envie um JSON como:

```json
{
  "questions": ["Total de vendas por UF"],
  "output_format": "markdown"
}
```

5. Para perguntas em planilha, use `POST /questions/excel` com
   `multipart/form-data`, um arquivo `questions_file` e o campo
   `output_format`.

O mesmo fluxo pode ser validado no Swagger e no Postman sem alterar a lógica
de negocio.

## Configuracao

Todos os provedores usam o pacote oficial `openai`. Para usar a mesma
configuracao nos dois agentes:

```dotenv
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
DB_PATH=sqlite:///app/data/database.db
PPTX_OUTPUT_PATH=app/data/output/insight_slide.pptx
MARKDOWN_OUTPUT_PATH=app/data/output/insights.md
```

Se `LLM_PROVIDER` nao for definido, o padrao atual e `ollama`.

Provedores aceitos em `LLM_PROVIDER`:

- `openai`
- `ollama`
- `gemini`
- `deepseek`
- `custom`

Cada agente pode usar um modelo diferente. Variaveis com prefixo `SALES_` ou
`EXTERNAL_` prevalecem sobre as globais:

```dotenv
SALES_LLM_PROVIDER=gemini
SALES_LLM_MODEL=gemini-3.5-flash
GEMINI_API_KEY=...

EXTERNAL_LLM_PROVIDER=ollama
EXTERNAL_LLM_MODEL=llama3.2
```

Para Ollama, mantenha o servidor local ativo e baixe o modelo configurado:

```powershell
ollama serve
ollama pull llama3.2
```

Exemplo com DeepSeek:

```dotenv
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
DEEPSEEK_API_KEY=...
```

Um novo endpoint OpenAI-compatible pode ser usado sem alterar os agentes:

```dotenv
LLM_PROVIDER=custom
LLM_MODEL=nome-do-modelo
LLM_BASE_URL=https://provedor.example/v1
LLM_API_KEY=...
```

Tambem existem overrides especificos:
`SALES_LLM_API_KEY`, `SALES_LLM_BASE_URL`,
`EXTERNAL_LLM_API_KEY` e `EXTERNAL_LLM_BASE_URL`.
`OPENAI_MODEL` continua aceito para compatibilidade com configuracoes antigas.

## Testes

```powershell
uv run python -m unittest discover -s tests -v
```

Consulte `SPEC.md` para os contratos dos agentes e regras de arquitetura.
