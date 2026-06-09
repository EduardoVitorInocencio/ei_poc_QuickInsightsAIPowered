# Relatorio de Insights de Vendas

## 1. Faturamento total por mês e ano

**Pergunta:** Qual é o faturamento total por mês e ano?

**Headline:** Janeiro/2019 lidera o faturamento no período analisado

### Analise

O faturamento por DataEmissao soma R$ 708.579,96 em janeiro/2019, R$ 293.594,32 em fevereiro/2019 e R$ 44.026,73 em março/2019. Há queda mês a mês no resultado retornado, com janeiro concentrando o maior volume de vendas.

### Dados

| Ano | MesNum | Mes | Faturamento |
| --- | --- | --- | --- |
| 2019 | 1 | Janeiro | 708,579.96 |
| 2019 | 2 | Fevereiro | 293,594.32 |
| 2019 | 3 | Março | 44,026.73 |

## 2. Top 10 clientes por faturamento

**Pergunta:** Quais são os 10 clientes com maior faturamento?

**Headline:** Bruna e Raimunda Atacado ME lidera o faturamento com R$ 92.893,90.

### Analise

Entre os 10 maiores clientes, todos estão no PR. O maior faturamento é de Bruna e Raimunda Atacado ME, em Curitiba, com R$ 92.893,90, valor significativamente acima do segundo colocado, Marcos e Isabelly Distribuidora ME, com R$ 53.208,83.

### Dados

| cdCliente | RazaoSocial | Cidade | UF | Faturamento |
| --- | --- | --- | --- | --- |
| 2955204 | Bruna e Raimunda Atacado ME | Curitiba | PR | 92,893.90 |
| 4088384 | Marcos e Isabelly Distribuidora ME | Sao Mateus do Sul | PR | 53,208.83 |
| 1156855 | Elaine e Yuri Ltda | Lapa | PR | 34,799.38 |
| 2956923 | Benício e Theo Ltda | Ponta Grossa | PR | 15,445.10 |
| 3826536 | Eliane e Alessandra Supermercado ME | Sao Joao do Triunfo | PR | 14,744.39 |
| 2959783 | Teresinha e Yuri ME | Bocaiuva do Sul | PR | 12,160.71 |
| 672177 | Eloá e Cláudio Ltda | Contenda | PR | 12,116.38 |
| 4036013 | Elaine e Regina Supermercado Ltda | Sao Joao do Triunfo | PR | 10,349.31 |
| 3674579 | Cauã e Lucca Ltda | Cerro Azul | PR | 10,235.34 |
| 632881 | Jorge e Rafael Ltda | Paulo Frontin | PR | 9,911.93 |

## 3. Clientes com queda de compra nos últimos períodos

**Pergunta:** Quais clientes apresentam queda de compra nos últimos períodos?

**Headline:** Bruna e Raimunda Atacado ME lidera a queda, saindo de R$ 21.810,00 em 2019-02 para zero no período atual analisado.

### Analise

Entre os 15 maiores recuos retornados, predominam clientes com queda de 100%, ou seja, tiveram compra em 2019-02 e não registraram venda no período atual. O maior impacto absoluto é de Bruna e Raimunda Atacado ME, seguida por Benício e Theo Ltda e Eliane e Alessandra Supermercado ME. Há também queda parcial relevante em Marcos e Isabelly Distribuidora ME, com redução de 71,3%, de R$ 5.545,66 para R$ 1.592,18.

### Dados

| cliente | cidade | uf | periodo_anterior | periodo_atual | venda_anterior | venda_atual | queda_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bruna e Raimunda Atacado ME | Curitiba | PR | 2019-02 |  | 21,810.00 | 0.00 | -100.00 |
| Benício e Theo Ltda | Ponta Grossa | PR | 2019-02 |  | 11,498.79 | 0.00 | -100.00 |
| Eliane e Alessandra Supermercado ME | Sao Joao do Triunfo | PR | 2019-02 |  | 6,409.81 | 0.00 | -100.00 |
| Kaique e Calebe ME | Curitiba | PR | 2019-02 |  | 6,238.36 | 0.00 | -100.00 |
| Eloá e Cláudio Ltda | Contenda | PR | 2019-02 |  | 5,415.39 | 0.00 | -100.00 |
| Fabiana e Theo Ltda | Ponta Grossa | PR | 2019-02 |  | 5,398.21 | 0.00 | -100.00 |
| Agatha e Aurora Armazém Ltda | Curitiba | PR | 2019-02 |  | 5,011.59 | 0.00 | -100.00 |
| Bárbara e Lavínia Atacado Ltda | Paranagua | PR | 2019-02 |  | 4,267.20 | 0.00 | -100.00 |
| Jéssica e Yasmin Ltda | Cerro Azul | PR | 2019-02 |  | 3,971.04 | 0.00 | -100.00 |
| Marcos e Isabelly Distribuidora ME | Sao Mateus do Sul | PR | 2019-02 | 2019-03 | 5,545.66 | 1,592.18 | -71.30 |
| Jorge e Rafael Ltda | Paulo Frontin | PR | 2019-02 |  | 3,875.60 | 0.00 | -100.00 |
| Luís e Leandro Lanchonete ME | Curitiba | PR | 2019-02 |  | 3,599.74 | 0.00 | -100.00 |
| Bryan e Tiago Ltda | Sao Mateus do Sul | PR | 2019-02 |  | 3,429.30 | 0.00 | -100.00 |
| Teresinha e Yuri ME | Bocaiuva do Sul | PR | 2019-02 |  | 3,413.28 | 0.00 | -100.00 |
| Isabelly e Jaqueline Supermercado Ltda | Ponta Grossa | PR | 2019-02 |  | 3,367.04 | 0.00 | -100.00 |

## 4. Clientes sem compra recente

**Pergunta:** Quais clientes deixaram de comprar recentemente?

**Headline:** Nenhum cliente identificado sem compras entre 90 e 180 dias da data mais recente da base.

### Analise

A consulta não retornou clientes cuja última compra esteja no intervalo de 90 a 180 dias antes da data mais recente registrada. Portanto, com este critério de recência, não há evidência de clientes que deixaram de comprar recentemente.

### Dados

| cdCliente | RazaoSocial | Cidade | UF | ultima_compra | dias_sem_comprar | qtd_notas | vendas_total |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 5. Produtos com maior receita

**Pergunta:** Quais produtos geram maior receita para o negócio?

**Headline:** Produto 845 lidera a receita, seguido de perto pelo Produto 1968.

### Analise

Entre os 15 produtos de maior receita, o Produto 845 gerou 95.294,01 e o Produto 1968 gerou 92.724,37, ficando bem acima dos demais. O terceiro colocado, Produto 2445, registrou 37.581,12, indicando forte concentração da receita nos dois primeiros produtos.

### Dados

| cdProduto | Produto | Receita |
| --- | --- | --- |
| 845 | Produto 845 | 95,294.01 |
| 1968 | Produto 1968 | 92,724.37 |
| 2445 | Produto 2445 | 37,581.12 |
| 662 | Produto 662 | 28,554.54 |
| 2233 | Produto 2233 | 24,374.60 |
| 120 | Produto 120 | 19,232.10 |
| 235 | Produto 235 | 16,011.00 |
| 2467 | Produto 2467 | 14,962.08 |
| 2392 | Produto 2392 | 13,534.79 |
| 2272 | Produto 2272 | 12,618.76 |
| 2460 | Produto 2460 | 12,330.00 |
| 157 | Produto 157 | 11,677.26 |
| 1769 | Produto 1769 | 10,929.72 |
| 839 | Produto 839 | 10,734.03 |
| 2622 | Produto 2622 | 10,085.28 |

## 6. Produtos com maior volume vendido em quantidade

**Pergunta:** Quais produtos têm maior volume vendido em quantidade?

**Headline:** Produto 2445 lidera em quantidade vendida, com 26.616 itens.

### Analise

Entre os 15 produtos com maior volume, o Produto 2445 aparece na liderança com 26.616 unidades, seguido pelo Produto 845 com 22.182 e Produto 2233 com 19.990. A liderança mostra concentração relevante nos três primeiros itens do ranking.

### Dados

| cdProduto | Produto | QuantidadeVendida |
| --- | --- | --- |
| 2445 | Produto 2445 | 26616 |
| 845 | Produto 845 | 22182 |
| 2233 | Produto 2233 | 19990 |
| 235 | Produto 235 | 17160 |
| 1968 | Produto 1968 | 12341 |
| 318 | Produto 318 | 10320 |
| 2460 | Produto 2460 | 8856 |
| 321 | Produto 321 | 8064 |
| 238 | Produto 238 | 7200 |
| 839 | Produto 839 | 6291 |
| 320 | Produto 320 | 5808 |
| 2472 | Produto 2472 | 5240 |
| 838 | Produto 838 | 5112 |
| 1216 | Produto 1216 | 5010 |
| 210 | Produto 210 | 4620 |

## 7. Participação no faturamento por grupo de produto

**Pergunta:** Quais grupos de produto possuem maior participação no faturamento?

**Headline:** Farinhas de Trigo lidera o faturamento com 29,57% de participação.

### Analise

Entre os 15 maiores grupos, Farinhas de Trigo é o principal destaque, com faturamento de 309.347,36 e 29,57% de participação. Os três maiores grupos — Farinhas de Trigo, Farinhas e Óleos — somam 57,75% do faturamento analisado, indicando forte concentração em grupos da linha Alimentos.

### Dados

| grupo_produto | linha | faturamento | participacao_pct |
| --- | --- | --- | --- |
| Farinhas de Trigo | Alimentos | 309,347.36 | 29.57 |
| Farinhas | Alimentos | 152,628.66 | 14.59 |
| Óleos | Alimentos | 142,190.49 | 13.59 |
| Cachaça | Bebidas | 78,727.67 | 7.53 |
| Fermentos | Alimentos | 75,649.18 | 7.23 |
| Temperos | Alimentos | 51,817.77 | 4.95 |
| Azeites | Alimentos | 31,072.62 | 2.97 |
| Leite em Pó | Alimentos | 29,699.73 | 2.84 |
| Pipocas | Alimentos | 26,314.14 | 2.52 |
| Farofas | Alimentos | 24,982.43 | 2.39 |
| Doces | Alimentos | 21,093.72 | 2.02 |
| Açúcares | Alimentos | 21,060.50 | 2.01 |
| Hortifruti | Alimentos | 19,108.89 | 1.83 |
| Café em Cápsulas | Alimentos | 16,273.64 | 1.56 |
| Café Moído | Alimentos | 9,146.25 | 0.87 |

## 8. Linhas de produto sem variação de relevância no período disponível

**Pergunta:** Quais linhas de produto estão crescendo ou perdendo relevância ao longo do tempo?

**Headline:** Alimentos mantém 89,75% do share e Bebidas 10,25%; não há crescimento ou perda de relevância detectável.

### Analise

O resultado retornado contém apenas o ano de 2019 como ano inicial e final. Assim, as duas linhas analisadas aparecem estáveis: Alimentos concentra R$ 939.014,01 em vendas e 89,75% de participação, enquanto Bebidas soma R$ 107.187,00 e 10,25%. Como não há outro ano no resultado, não é possível identificar tendência temporal de crescimento ou perda de relevância.

### Dados

| linha | periodo | vendas_ano_inicial | share_inicial_pct | vendas_ano_final | share_final_pct | variacao_share_pp | tendencia |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Alimentos | 2019→2019 | 939,014.01 | 89.75 | 939,014.01 | 89.75 | 0.00 | Estavel |
| Bebidas | 2019→2019 | 107,187.00 | 10.25 | 107,187.00 | 10.25 | 0.00 | Estavel |

## 9. Concentração de vendas por estado

**Pergunta:** Quais estados concentram a maior parte das vendas?

**Headline:** O Paraná concentra 100% das vendas registradas.

### Analise

A análise por UF retornou apenas o estado PR, com R$ 1.046.201,01 em vendas, representando 100% do total no resultado consultado. Não há evidência de vendas em outros estados nos dados retornados.

### Dados

| estado | vendas | percentual_vendas | percentual_acumulado |
| --- | --- | --- | --- |
| PR | 1,046,201.01 | 100.00 | 100.00 |

## 10. Cidades líderes em faturamento e clientes ativos

**Pergunta:** Quais cidades possuem maior faturamento e maior número de clientes ativos?

**Headline:** Curitiba lidera com R$ 270,9 mil de faturamento e 239 clientes ativos.

### Analise

Entre as 15 cidades com maior faturamento, Curitiba se destaca com ampla vantagem: faturamento de R$ 270.865,64 e 239 clientes ativos. Em seguida aparecem Sao Mateus do Sul, com R$ 123.951,34 e 63 clientes, e Ponta Grossa, com R$ 102.403,29 e 90 clientes. O resultado indica forte concentração comercial em Curitiba, que combina maior receita e maior base ativa de clientes.

### Dados

| Cidade | UF | Faturamento | ClientesAtivos |
| --- | --- | --- | --- |
| Curitiba | PR | 270,865.64 | 239 |
| Sao Mateus do Sul | PR | 123,951.34 | 63 |
| Ponta Grossa | PR | 102,403.29 | 90 |
| Araucaria | PR | 92,648.36 | 111 |
| Lapa | PR | 83,347.00 | 78 |
| Paranagua | PR | 82,165.66 | 100 |
| Sao Joao do Triunfo | PR | 50,194.41 | 15 |
| Contenda | PR | 33,101.66 | 17 |
| Cerro Azul | PR | 32,686.22 | 35 |
| Bocaiuva do Sul | PR | 27,515.82 | 12 |
| Colombo | PR | 25,553.59 | 57 |
| Uniao da Vitoria | PR | 20,948.14 | 56 |
| Paulo Frontin | PR | 20,784.43 | 10 |
| Adrianopolis | PR | 19,474.96 | 12 |
| Antonio Olinto | PR | 13,189.87 | 5 |

## 11. Concentração de receita por cliente, produto e região

**Pergunta:** Existe concentração excessiva de receita em poucos clientes, produtos ou regiões?

**Headline:** A concentração regional é total em PR; já clientes e produtos apresentam baixa concentração relativa.

### Analise

A receita total analisada foi de 1.046.201,01. Em UF, há apenas uma região registrada: PR, concentrando 100% da receita. Em produtos, o maior item representa 9,11% e os top 5 somam 26,62%, indicando concentração moderada. Em clientes, o maior cliente representa 8,88% e os top 5 somam 20,18%, sugerindo baixa dependência de poucos clientes.

### Dados

| dimensao | qtd_itens | maior_item | receita_maior_item | pct_top1 | pct_top5 | receita_total |
| --- | --- | --- | --- | --- | --- | --- |
| UF | 1 | PR | 1,046,201.01 | 100.00 | 100.00 | 1,046,201.01 |
| Produto | 490 | Produto 845 | 95,294.01 | 9.11 | 26.62 | 1,046,201.01 |
| Cliente | 980 | Bruna e Raimunda Atacado ME | 92,893.90 | 8.88 | 20.18 | 1,046,201.01 |

## 12. Ranking de vendedores por faturamento

**Pergunta:** Quais vendedores possuem melhor desempenho em faturamento?

**Headline:** Carla Ferreira lidera o faturamento com R$ 190.033,91, seguida por Mateus Costa com R$ 147.213,93.

### Analise

A análise por vendedor mostra Carla Ferreira como destaque em faturamento, com 345 notas, superando o segundo colocado, Mateus Costa, em R$ 42.819,98. Entre os cinco maiores faturamentos, há representantes das equipes Varejo, Online e Distribuidoras, indicando desempenho forte distribuído entre canais.

### Dados

| Vendedor | Equipe | Supervisor | Faturamento | Qtde_Notas |
| --- | --- | --- | --- | --- |
| Carla Ferreira | Varejo | Diego Araujo | 190,033.91 | 345 |
| Mateus Costa | Online | Sofia Ribeiro | 147,213.93 | 316 |
| Julio Lima | Distribuidoras | Diogo Carvalho | 116,448.66 | 332 |
| Julia Silva | Online | Sofia Ribeiro | 94,272.04 | 353 |
| Gustavo Gomes | Distribuidoras | Diogo Carvalho | 94,236.16 | 270 |
| Gustavo Barros | Varejo | Emily Rocha | 87,505.44 | 307 |
| Felipe Goncalves | Online | Sofia Ribeiro | 82,165.66 | 270 |
| Estevan Souza | Distribuidoras | Diogo Carvalho | 74,339.77 | 343 |
| Kaua Araujo | Varejo | Fernando Silva | 65,161.22 | 182 |
| Leonardo Cardoso | Varejo | Diego Araujo | 47,272.67 | 184 |
| Isabella Sousa | Varejo | Emily Rocha | 31,669.65 | 53 |
| Julieta Gomes | Varejo | Emily Rocha | 15,881.90 | 59 |

## 13. Vendedores com mais clientes ativos atendidos

**Pergunta:** Quais vendedores atendem mais clientes ativos?

**Headline:** Julia Silva lidera em clientes ativos atendidos, com 103 clientes, seguida de Mateus Costa com 102.

### Analise

Entre os vendedores analisados, Julia Silva aparece no topo em cobertura de clientes ativos, com 103 clientes atendidos e R$ 91.066,41 em vendas. Mateus Costa está praticamente empatado em alcance, com 102 clientes ativos, mas apresenta maior volume de vendas, R$ 143.537,68. Felipe Goncalves completa o top 3 com 96 clientes ativos atendidos.

### Dados

| vendedor | clientes_ativos_atendidos | vendas |
| --- | --- | --- |
| Julia Silva | 103 | 91,066.41 |
| Mateus Costa | 102 | 143,537.68 |
| Felipe Goncalves | 96 | 80,951.36 |
| Estevan Souza | 92 | 71,749.41 |
| Julio Lima | 91 | 106,793.55 |
| Leonardo Cardoso | 86 | 46,604.87 |
| Carla Ferreira | 84 | 187,593.84 |
| Gustavo Barros | 79 | 85,310.86 |
| Kaua Araujo | 69 | 64,820.33 |
| Gustavo Gomes | 67 | 92,078.05 |
| Julieta Gomes | 38 | 15,644.26 |
| Isabella Sousa | 36 | 31,669.65 |

## 14. Vendedores com queda de performance ao longo do tempo

**Pergunta:** Quais vendedores apresentam queda de performance ao longo do tempo?

**Headline:** 11 vendedores apresentam tendência mensal negativa; Carla Ferreira lidera a queda em valor absoluto.

### Analise

A análise de vendas mensais por vendedor identificou 11 vendedores com tendência mensal negativa em pelo menos 3 meses ativos. As maiores quedas de tendência foram de Carla Ferreira (-66.991,37 por mês), Mateus Costa (-52.495,89) e Julio Lima (-40.537,16). Em termos percentuais entre o primeiro e o último mês, Leonardo Cardoso, Felipe Goncalves e Gustavo Barros tiveram retrações próximas ou superiores a 98%.

### Dados

| Vendedor | meses_ativos | venda_primeiro_mes | venda_ultimo_mes | queda_abs_inicio_fim | pct_queda_inicio_fim | tendencia_mensal | venda_total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Carla Ferreira | 3 | 139,264.89 | 5,282.15 | -133,982.74 | -96.21 | -66,991.37 | 190,033.91 |
| Mateus Costa | 3 | 107,236.35 | 2,244.56 | -104,991.79 | -97.91 | -52,495.89 | 147,213.93 |
| Julio Lima | 3 | 85,132.45 | 4,058.13 | -81,074.32 | -95.23 | -40,537.16 | 116,448.66 |
| Gustavo Gomes | 3 | 64,152.97 | 3,312.58 | -60,840.39 | -94.84 | -30,420.19 | 94,236.16 |
| Felipe Goncalves | 3 | 60,950.95 | 603.99 | -60,346.96 | -99.01 | -30,173.48 | 82,165.66 |
| Julia Silva | 3 | 63,155.44 | 7,843.32 | -55,312.12 | -87.58 | -27,656.06 | 94,272.04 |
| Estevan Souza | 3 | 55,642.25 | 1,652.62 | -53,989.63 | -97.03 | -26,994.82 | 74,339.77 |
| Gustavo Barros | 3 | 50,036.65 | 1,030.17 | -49,006.48 | -97.94 | -24,503.24 | 87,505.44 |
| Kaua Araujo | 3 | 37,532.02 | 1,067.27 | -36,464.75 | -97.16 | -18,232.38 | 65,161.22 |
| Leonardo Cardoso | 3 | 30,692.65 | 292.38 | -30,400.27 | -99.05 | -15,200.13 | 47,272.67 |
| Julieta Gomes | 3 | 7,808.38 | 1,785.73 | -6,022.65 | -77.13 | -3,011.32 | 15,881.90 |

## 15. Ticket médio por nota fiscal, cliente e vendedor

**Pergunta:** Qual é o ticket médio por nota fiscal, cliente e vendedor?

**Headline:** Maior ticket médio observado: R$ 15.482,32 por nota em Bruna e Raimunda Atacado ME com Mateus Costa.

### Analise

A análise agrupou vendas por cliente e vendedor, calculando o ticket médio como vendas totais divididas pela quantidade de notas fiscais distintas. Entre os 15 maiores resultados, Bruna e Raimunda Atacado ME com Mateus Costa lidera com 6 notas, R$ 92.893,90 em vendas e ticket médio de R$ 15.482,32, bem acima dos demais pares listados.

### Dados

| Cliente | Vendedor | QtdeNotas | Vendas | TicketMedioPorNota |
| --- | --- | --- | --- | --- |
| Bruna e Raimunda Atacado ME | Mateus Costa | 6 | 92,893.90 | 15,482.32 |
| Priscila e Martin ME | Isabella Sousa | 1 | 9,823.80 | 9,823.80 |
| Marcos e Isabelly Distribuidora ME | Carla Ferreira | 8 | 53,208.83 | 6,651.10 |
| Kaique e Calebe ME | Isabella Sousa | 1 | 6,238.36 | 6,238.36 |
| Enrico e Mariah Atacado ME | Estevan Souza | 2 | 5,515.20 | 2,757.60 |
| Elaine e Yuri Ltda | Julio Lima | 13 | 34,799.38 | 2,676.88 |
| Luiz e Daiane Ltda | Felipe Goncalves | 1 | 2,666.93 | 2,666.93 |
| Mariane e Aurora Atacado ME | Julia Silva | 3 | 6,504.80 | 2,168.27 |
| Luís e Leandro Lanchonete ME | Kaua Araujo | 2 | 4,202.16 | 2,101.08 |
| Kauê e Andrea Pousada ME | Isabella Sousa | 1 | 1,719.64 | 1,719.64 |
| Benício e Theo Ltda | Gustavo Barros | 10 | 15,445.10 | 1,544.51 |
| Enzo e Caio Ltda | Carla Ferreira | 5 | 7,556.49 | 1,511.30 |
| Eliane e Alessandra Supermercado ME | Carla Ferreira | 10 | 14,744.39 | 1,474.44 |
| Jorge e Rafael Ltda | Leonardo Cardoso | 7 | 9,911.93 | 1,415.99 |
| Eloá e Cláudio Ltda | Julio Lima | 9 | 12,116.38 | 1,346.26 |

## 16. Preço médio ao longo do tempo

**Pergunta:** O preço médio dos produtos está aumentando ou diminuindo ao longo do tempo?

**Headline:** Não há base temporal suficiente para concluir aumento ou queda

### Analise

O resultado retornou apenas o ano de 2019, com preço médio ponderado de 3,00, vendas de 1.046.201,01 e 348.989 itens. Como não há outros períodos no resultado, não é possível identificar tendência de aumento ou diminuição ao longo do tempo.

### Dados

| Ano | preco_medio_ponderado | variacao_vs_ano_anterior | vendas | qtd_itens |
| --- | --- | --- | --- | --- |
| 2019 | 3.00 |  | 1,046,201.01 | 348,989.00 |

## 17. Clientes concentrados em uma única linha para cross-sell

**Pergunta:** Quais clientes compram apenas uma linha de produto e poderiam receber ações de cross-sell?

**Headline:** Bruna e Raimunda Atacado ME lidera os clientes mono-linha, com R$ 92,9 mil em vendas apenas em Alimentos.

### Analise

Entre os 15 maiores clientes que compram somente uma linha de produto, há forte concentração em Alimentos. O principal alvo para cross-sell é Bruna e Raimunda Atacado ME, em Curitiba/PR, com 23.555 itens e R$ 92.893,90 em vendas, seguido por Eliane e Alessandra Supermercado ME e Jorge e Rafael Ltda. Esses clientes já demonstram volume relevante e podem ser priorizados para introdução de linhas complementares, especialmente os que têm alto faturamento e variedade de produtos dentro da linha atual.

### Dados

| cdCliente | RazaoSocial | Cidade | UF | LinhaComprada | ProdutosComprados | ItensComprados | Vendas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2955204 | Bruna e Raimunda Atacado ME | Curitiba | PR | Alimentos | 6 | 23555 | 92,893.90 |
| 3826536 | Eliane e Alessandra Supermercado ME | Sao Joao do Triunfo | PR | Alimentos | 49 | 2378 | 14,744.39 |
| 632881 | Jorge e Rafael Ltda | Paulo Frontin | PR | Alimentos | 27 | 2202 | 9,911.93 |
| 931479 | Priscila e Martin ME | Ponta Grossa | PR | Alimentos | 1 | 210 | 9,823.80 |
| 5263059 | Murilo e Malu Ltda | Ponta Grossa | PR | Alimentos | 102 | 3305 | 9,611.92 |
| 5392539 | Thales e Gabriela ME | Araucaria | PR | Alimentos | 81 | 2421 | 8,862.49 |
| 5504276 | Luís e Carla ME | Contenda | PR | Alimentos | 57 | 1874 | 8,412.97 |
| 1144926 | Jéssica e Yasmin Ltda | Cerro Azul | PR | Alimentos | 56 | 1746 | 7,845.05 |
| 2967889 | Enzo e Caio Ltda | Sao Joao do Triunfo | PR | Alimentos | 46 | 1556 | 7,556.49 |
| 5244610 | Bárbara e Lavínia Atacado Ltda | Paranagua | PR | Alimentos | 16 | 4769 | 7,480.55 |
| 4896500 | Márcia e Kamilly ME | Sao Mateus do Sul | PR | Alimentos | 62 | 2366 | 7,337.09 |
| 4691396 | Fabiana e Theo Ltda | Ponta Grossa | PR | Alimentos | 31 | 1328 | 6,797.75 |
| 1338872 | Agatha e Aurora Armazém Ltda | Curitiba | PR | Bebidas | 37 | 167 | 6,531.25 |
| 930651 | Mariane e Aurora Atacado ME | Araucaria | PR | Alimentos | 5 | 3730 | 6,504.80 |
| 5246043 | Kaique e Calebe ME | Curitiba | PR | Alimentos | 14 | 3676 | 6,238.36 |

## 18. Sem evidência de produtos com alta venda regional e baixa penetração em outra UF

**Pergunta:** Quais produtos vendem bem em algumas regiões, mas têm baixa penetração em outras?

**Headline:** A consulta não retornou produtos que atendam ao critério comparativo entre UFs.

### Analise

Com base no resultado retornado, não foram identificados produtos com venda forte em uma UF e penetração inferior em outra UF dentro dos critérios aplicados. O conjunto analisado retornou zero linhas, portanto não há produtos ou regiões específicos a destacar.

### Dados

| produto | uf_forte | venda_uf_forte | penetracao_forte_pct | uf_baixa | venda_uf_baixa | penetracao_baixa_pct | gap_penetracao_pp |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 19. Sazonalidade concentrada no 1º trimestre observado

**Pergunta:** Existe sazonalidade nas vendas em determinados meses ou trimestres?

**Headline:** Janeiro concentrou 67,73% das vendas do período analisado, com queda forte em fevereiro e março.

### Analise

Os dados retornados incluem apenas janeiro, fevereiro e março, todos no 1º trimestre. Nesse recorte, há forte concentração em janeiro, com R$ 708.579,96 em vendas, seguido por fevereiro com R$ 293.594,32 e março com R$ 44.026,73. Assim, o resultado sugere sazonalidade dentro do trimestre observado, mas não permite comparar trimestres diferentes.

### Dados

| MesNum | Mes | Trimestre | AvgVendaMensal | TotalVenda | PctTotal | TotalTrimestre | RankMes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Janeiro | 1 | 708,579.96 | 708,579.96 | 67.73 | 1,046,201.01 | 1 |
| 2 | Fevereiro | 1 | 293,594.32 | 293,594.32 | 28.06 | 1,046,201.01 | 2 |
| 3 | Março | 1 | 44,026.73 | 44,026.73 | 4.21 | 1,046,201.01 | 3 |

## 20. Oportunidades comerciais prioritárias por cliente, produto, região e vendedor

**Pergunta:** Quais oportunidades comerciais podem ser priorizadas com base em cliente, produto, região e vendedor?

**Headline:** Bruna e Raimunda Atacado ME no PR concentra a maior oportunidade, liderada por Farinhas com Mateus Costa.

### Analise

Entre as 15 maiores combinações, todas estão no PR. A principal prioridade é Bruna e Raimunda Atacado ME com Mateus Costa: Produto 845 em Farinhas soma R$ 64.290 em vendas, além de Produto 1968 em Farinhas de Trigo com R$ 21.810 e Produto 2233 em Óleos com R$ 4.480. Também aparecem oportunidades relevantes em Farinhas de Trigo, especialmente Produto 1968 com clientes atendidos por Julio Lima, Carla Ferreira e Gustavo Barros.

### Dados

| cliente | regiao_uf | grupo_produto | produto | vendedor | pedidos | qtd_itens | vendas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bruna e Raimunda Atacado ME | PR | Farinhas | Produto 845 | Mateus Costa | 2 | 15000 | 64,290.00 |
| Bruna e Raimunda Atacado ME | PR | Farinhas de Trigo | Produto 1968 | Mateus Costa | 1 | 3000 | 21,810.00 |
| Elaine e Yuri Ltda | PR | Farinhas de Trigo | Produto 1968 | Julio Lima | 1 | 1500 | 11,550.00 |
| Marcos e Isabelly Distribuidora ME | PR | Farinhas de Trigo | Produto 1968 | Carla Ferreira | 1 | 1500 | 11,475.00 |
| Benício e Theo Ltda | PR | Farinhas de Trigo | Produto 1968 | Gustavo Barros | 1 | 1500 | 11,340.00 |
| Priscila e Martin ME | PR | Doces | Produto 2669 | Isabella Sousa | 1 | 210 | 9,823.80 |
| Enrico e Mariah Atacado ME | PR | Farinhas | Produto 581 | Estevan Souza | 2 | 1440 | 5,515.20 |
| Cauã e Lucca Ltda | PR | Farinhas | Produto 662 | Gustavo Gomes | 1 | 600 | 4,734.00 |
| Fabiana e Theo Ltda | PR | Farinhas de Trigo | Produto 1968 | Gustavo Barros | 1 | 600 | 4,632.00 |
| Eloá e Cláudio Ltda | PR | Farinhas de Trigo | Produto 1968 | Julio Lima | 1 | 600 | 4,494.00 |
| Bruna e Raimunda Atacado ME | PR | Óleos | Produto 2233 | Mateus Costa | 1 | 3500 | 4,480.00 |
| Márcia e Kamilly ME | PR | Farinhas | Produto 845 | Carla Ferreira | 1 | 900 | 3,861.00 |
| Enzo e Caio Ltda | PR | Temperos | Produto 120 | Carla Ferreira | 1 | 360 | 3,715.20 |
| Jorge e Rafael Ltda | PR | Farinhas | Produto 662 | Leonardo Cardoso | 1 | 480 | 3,715.20 |
| Eliane e Alessandra Supermercado ME | PR | Temperos | Produto 120 | Carla Ferreira | 1 | 360 | 3,690.00 |
