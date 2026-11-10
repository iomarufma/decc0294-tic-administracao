---
name: Analise Economica
description: Criar relatorios e visualizacoes de indicadores economicos brasileiros (IPCA, inflacao, poder de compra) em padrao profissional de analise economica e inteligencia de negocios. Use quando o usuario pedir analise economica, relatorio de inflacao, graficos de indicadores ou painel economico.
---

# Skill de Analise Economica

## Quando usar

- Gerar relatorios, graficos e tabelas com indicadores economicos oficiais (IPCA, Selic, PIB, salario minimo).
- Analisar inflacao e seu impacto no poder de compra e no planejamento administrativo.
- Padronizar a apresentacao de resultados economicos para entrega em PDF ou painel.

## Identidade visual

- Paleta fixa: azul-marinho `#1B2A4A` (titulos e textos fortes), azul-claro `#7FA8D4` (series secundarias e fundos de destaque), branco `#FFFFFF` (fundo geral), dourado `#C9A227` (detalhes discretos: filetes, marcadores de destaque, numeros-chave).
- Nao usar mais de duas cores de dados por grafico. Dourado apenas para destacar o maximo, o minimo ou o periodo em foco.
- Tipografia: Helvetica/Arial. Corpo 9-10pt, titulos de secao 13-14pt, titulos de grafico 10-11pt.
- Fundo branco, sem sombras pesadas, sem 3D, sem gradientes.

## Estrutura de relatorio economico

1. Capa: titulo, subtitulo, periodo analisado, fonte de dados, data da consulta.
2. Introducao: contexto e objetivo (ate 1 paragrafo curto por item).
3. Metodologia e fonte: indicador, serie, API, periodo, forma de calculo.
4. Evolucao: graficos em ordem cronologica, cada um com titulo, unidade e fonte.
5. Analise dos resultados: leitura dos graficos, comparacoes, extremos.
6. Impactos na Administracao: leitura administrativa dos numeros.
7. Consideracoes finais: sintese e limitacoes.
8. Referencias: fonte oficial de cada dado.

## Apresentacao de indicadores e graficos

- Grafico de linha para series mensais; barras para comparacao anual.
- Todo grafico: titulo em cima, unidade no eixo, legenda quando houver mais de uma serie, fonte embaixo ("Fonte: BCB/SGS, serie 433").
- Tabelas: cabecalho em azul-marinho com texto branco, linhas alternadas em azul-claro muito claro (`#EEF3FA`), filete dourado no topo.
- Numeros-chave em caixas de destaque (fundo azul-claro claro, valor em azul-marinho, rotulo menor).
- Percentuais com 2 casas decimais e sinal de %; datas no formato "MM/AAAA".

## Tratamento e validacao de dados

- Consultar sempre a fonte oficial (API do BCB/SGS). Nao usar valores de memoria.
- Registrar data da consulta e ultimo periodo disponivel na serie.
- Verificar duplicados (mesma data), valores ausentes e datas fora de ordem antes de calcular.
- Acumulado em 12 meses: composicao das taxas mensais, `((1+r1)*...*(1+r12)-1)`.
- Nao estimar, nao interpolat, nao suavizar dados ausentes: se houver lacuna, informar.
- Anos completos e periodos parciais devem ser identificados como tais.
- Distinguir correlacao de causalidade na interpretacao.

## Linguagem

- Academica, clara e objetiva. Frases curtas. Sem adjetivo promocional.
- Todo termo tecnico definido na primeira ocorrencia (IPCA, acumulado em 12 meses, poder de compra).
- Todo numero com fonte e periodo. Sem numero sem origem declarada.
- Sem jargao nao explicado.

## Interpretacao de indicadores

- IPCA mensal: variação de preços no mês de referencia.
- IPCA acumulado em 12 meses: inflação observada nos 12 meses anteriores ao periodo indicado.
- Inflacao anual: variacao entre dezembro e dezembro do ano anterior (ano completo) ou acumulada no periodo parcial (declarar).
- Relacionar inflacao a poder de compra quando a renda nominal nao acompanha a variacao de precos, sem afirmar causa sem evidencia.
- Separar fatos (dados da fonte) de interpretacoes (analise) no texto.

## Relacao com a Administracao

- Custo empresarial: precos de insumos e folha reajustados pela inflacao.
- Precos: necessidade de revisar tabela quando custo e demanda mudam.
- Planejamento financeiro: orcamento realista exige premissa de inflacao declarada.
- Decisao administrativa: indicador macro entra como variavel de cenario, nao como unico determinante.

## Regras fixas

- Nunca inventar referencia bibliografica: se nao souber, escrever NAO SEI.
- Nunca apresentar numero sem dizer de onde veio (serie, fonte, periodo).
- Nunca substituir dado ausente por estimativa silenciosa.
- Nunca escrever conclusao causal sem suporte nos dados apresentados.
- Produzir minuta para revisao humana e apontar decisoes pendentes.

## Workflow

1. Consultar a API oficial e salvar o JSON bruto com data da consulta.
2. Validar: duplicados, lacunas, ordenacao, ultimo periodo.
3. Calcular acumulados (12 meses e anuais) e identificar extremos.
4. Gerar graficos na identidade visual acima.
5. Montar o relatorio seguindo a estrutura e aplicando linguagem e interpretacao.
6. Revisar com o checklist antes de entregar.

## Checklist de entrega

- [ ] Data da consulta e ultimo periodo disponivel declarados
- [ ] Cada grafico com titulo, unidade, legenda e fonte
- [ ] Cada tabela com cabecalho e fonte
- [ ] Periodos parciais identificados como parciais
- [ ] Numeros-chave sem duplicacao de texto repetitivo
- [ ] Referencias oficiais completas
- [ ] Paleta marinho/azul-claro/branco/dourado respeitada
