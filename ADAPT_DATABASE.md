# Adaptação do Projeto para Outro Banco e Schema

Este documento descreve o que você precisa configurar para adaptar o projeto a outro banco de dados e schema diferente. Ele assume que você quer subir um conjunto de dados novo e garantir que o projeto continue usando validação centralizada antes de expor qualquer SQL ao agente.

## Visão geral

O projeto divide a lógica em:

- contrato de schema e registry: `app/domain/sales_model.py`
- ingestão e transformação: `app/ingestion/`
- persistência e inspeção de banco: `app/db/database.py`
- política de SQL seguro: `app/db/sql_validator.py`
- agente e prompts: `app/agent/`

A regra de ouro é: qualquer schema pode ser usado desde que esteja corretamente registrado e validado pelo projeto.

## 1. Atualizar o contrato do modelo de dados (registry)

O ponto central do schema é `app/domain/sales_model.py`.
Para um novo conjunto de dados, atualize principalmente essas constantes:

- `TABLES` — mapeamento entre nomes de abas/entidades de origem e tabelas do banco
- `EXPECTED_SCHEMAS` — colunas esperadas por entidade/tabela
- `FACT_TABLE` — tabela fato principal usada para consultas de negócio
- `SALES_EXPRESSION` — expressão de negócio usada pelo agente para calcular métricas
- `RELATIONSHIPS` — relacionamentos esperados entre fato e dimensões
- `ALLOWED_TABLES` — conjunto de tabelas que o validador aceita
- `INDEXES` — índices físicos recomendados para acelerar joins
- `DIMENSION_KEYS` — chaves únicas das tabelas de dimensão

### Por que isso é importante

O arquivo `sales_model.py` atua como registry do schema:

- `app/ingestion/` usa esse registry para validar e carregar dados
- `app/db/database.py` usa esse registry para inspecionar o banco existente
- `app/agent/` usa esse registry para construir o prompt e validar o SQL
- `app/db/sql_validator.py` usa as tabelas permitidas e a tabela fato do registry

Se o registry estiver correto, você poderá subir qualquer schema.

### Exemplo de fluxo de atualização

1. defina as tabelas e colunas no registry
2. confirme que `EXPECTED_SCHEMAS` corresponde ao layout do seu Excel ou fonte
3. ajuste `RELATIONSHIPS` para refletir as chaves de junção reais
4. adicione índices em `INDEXES` para as colunas de join mais usadas

## 2. Ajustar ingestão de dados

A ingestão atual está em `app/ingestion/excel_to_sqlite.py`.

- `validate_required_sheets()` valida as abas obrigatórias com base em `TABLES`
- `read_and_prepare_workbook()` prepara o workbook e transforma cada aba
- `load_excel_to_sqlite()` grava os dados no banco dentro de uma transação

### O que ajustar para outro dataset

- se o novo schema vier de outras abas Excel, ajuste `TABLES` e `EXPECTED_SCHEMAS`
- se as colunas tiverem nomes diferentes, atualize `app/ingestion/transformations.py`
- se o dado vier de outra fonte (CSV, API, parquet), mantenha a lógica de validação e transformação, mas substitua a leitura do Excel
- se o banco não for SQLite, verifique o uso de `DataFrame.to_sql()` e se o driver suporta os tipos usados

### Dica

Mantenha `TABLES` como o único ponto de verdade do registry. A ingestão deve apenas consumir esse registro para saber quais abas/tabelas carregar.

## 3. Atualizar validação do banco

`app/db/database.py` inspeciona o banco antes de aceitar reutilizá-lo.

- `inspect_existing_data()` verifica tabelas, colunas e contagens
- `validate_relationship_integrity()` valida duplicatas e registros órfãos

### Se o schema mudar

- atualize as checagens de tabela e coluna via `TABLES` e `EXPECTED_SCHEMAS`
- se tiver novos relacionamentos, ajuste `RELATIONSHIPS`
- se a integridade relacional precisar de regras novas, estenda `find_orphan_relationships()` ou adicione validações adicionais

### Observação sobre o registry

A inspeção do banco é feita com base no registry. Portanto, qualquer schema validado no registry será considerado compatível se o banco corresponder a esse registro.

## 4. Ajustar a política SQL

O validador de SQL está em `app/db/sql_validator.py`.
Ele protege a aplicação de consultas perigosas e garante que apenas SELECTs no modelo autorizado sejam executados.

### O que configurar

- `ALLOWED_TABLES` deve conter todas as tabelas do novo schema que o agente pode consultar
- `FACT_TABLE` deve ser a tabela de fato principal usada pelas análises
- `SALES_EXPRESSION` deve refletir a fórmula ou métrica específica do dataset

### Por que isso importa

Mesmo com um novo schema, o agente só deve poder gerar SQL dentro das regras registradas. O registry define o que é permitido, e o validador garante que o modelo não fuja desse escopo.

## 5. Revisar agente e prompts

O fluxo de `SalesAgent` depende de:

- relevante prompt em `app/agent/prompts.py`
- a lista de ferramentas e suas assinaturas em `app/llm/tools.py`
- fallback SQL em `app/agent/sales_agent.py`

### Ajustes recomendados

- atualize `SALES_AGENT_PROMPT` para explicar ao modelo o novo domínio e o novo dataset
- ajuste `SALES_EXPRESSION` para lhe dizer ao modelo como calcular a métrica chave
- se quiser suporte a novas perguntas de negócio, adapte os exemplos e restrições do prompt
- se houver consultas padrões específicas, atualize `_build_fallback_sql()`

## 6. Configurar o novo banco

Se você mudar para outro motor de banco (Postgres, MySQL, SQL Server etc.):

- defina `DB_PATH` em `.env` com a URL SQLAlchemy correta
- instale o driver correto para o banco escolhido
- mantenha `create_database_engine()` em `app/db/database.py` porque ele já usa SQLAlchemy
- teste a criação de conexões e a escrita de tabelas antes de rodar o fluxo completo

### Quando não for SQLite

- revise tipos de dados e limites do driver
- confirme se `DataFrame.to_sql()` funciona para o target escolhido
- considere adicionar uma camada de compatibilidade se houver comandos SQL específicos do banco

## 7. Como subir qualquer schema válido

A ideia-chave é:

> você pode subir qualquer schema desde que ele esteja validado no registry

Isso significa que:

- o schema deve estar registrado em `app/domain/sales_model.py`
- a origem dos dados deve ser consumida pela camada de ingestão
- o banco deve corresponder ao registry quando inspecionado
- o validador SQL deve aceitar apenas as tabelas e joins permitidos

Se essas quatro condições forem verdadeiras, o projeto aceitará o novo schema.

## 8. Testes e validação

Depois de adaptar o schema, valide cada camada:

- `inspect_existing_data()` deve reconhecer o banco como `usable`
- `load_excel_to_sqlite()` deve carregar dados sem erros
- `SqlValidator` deve aceitar queries válidas e bloquear queries fora do registry
- o agente deve receber o schema correto via `inspect_schema()` e operar com `run_sql_query`

### Boas práticas

- mantenha testes unitários para o novo schema
- escreva testes de integração que carreguem um banco de exemplo
- use um conjunto de dados pequeno para validar o fluxo antes de subir tudo

## Resumo de passos detalhado

1. descreva o novo schema em `app/domain/sales_model.py`
2. adapte a ingestão em `app/ingestion/`, mantendo o registry como base
3. confirme a inspeção do banco em `app/db/database.py`
4. ajuste o validador de SQL em `app/db/sql_validator.py`
5. atualize prompts e métricas em `app/agent/`
6. configure o banco em `.env` e instale o driver apropriado
7. faça testes de schema, ingestão e fluxo do agente

## Exemplo de checklist para um novo dataset

- [ ] mapa de tabelas e abas definido em `TABLES`
- [ ] colunas esperadas definidas em `EXPECTED_SCHEMAS`
- [ ] relacionamento entre fato e dimensões definido em `RELATIONSHIPS`
- [ ] chave de fato (`FACT_TABLE`) e expressão de negócio (`SALES_EXPRESSION`) atualizadas
- [ ] índice de joins configurados em `INDEXES`
- [ ] ingestão preparada para a fonte de dados real
- [ ] banco conectado e inspecionado corretamente
- [ ] SQL validado pelo registry
- [ ] prompts ajustados para o novo domínio

Se quiser, posso criar um template de registry para outro domínio específico, como financeiro, logística ou saúde.