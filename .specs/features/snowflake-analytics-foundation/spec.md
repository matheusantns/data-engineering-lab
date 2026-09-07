# Fundação Analítica Snowflake

## Problem Statement

A carga do e-commerce já entrega 16 tabelas no schema `DATA_LAB.BRONZE`, mas ainda não existe uma camada analítica reproduzível. O projeto precisa transformar essa carga em dados Silver confiáveis e em uma Gold de vendas, mantendo código, testes e instruções operacionais no Git para execução humana.

## Goals

- [ ] Versionar toda a lógica de infraestrutura e transformação do Snowflake sem armazenar segredos.
- [ ] Disponibilizar uma Silver source-conformed para as 16 tabelas Bronze.
- [ ] Disponibilizar uma Gold dimensional de vendas com métricas financeiras não ambíguas.
- [ ] Permitir uma execução manual diária, repetível e validada por testes.
- [ ] Entregar um plano detalhado para implementação humana.

## Out of Scope

| Feature | Reason |
| --- | --- |
| Ferramenta de BI | Será escolhida depois da fundação de dados |
| Bot Telegram e agente de IA | Será planejado depois da Gold |
| Orquestração e agendamento automático | O primeiro ciclo será executado manualmente |
| Ambientes Snowflake separados | O primeiro ciclo usará um único ambiente de laboratório |
| Carga Bronze incremental | A carga existente com `replace` será mantida neste ciclo |
| Modelos Gold incrementais | O volume atual permite reconstrução integral |
| SCD Tipo 2 | As dimensões usarão estado atual no primeiro ciclo |
| Conversão cambial | Não existe fonte de taxas de câmbio |
| Publicação atômica da DAG completa | Exigiria isolamento e promoção entre ambientes |
| DCM Projects ou ferramenta de migrations | Scripts idempotentes e dbt cobrem o primeiro ciclo |
| Indicadores de carrinho, estoque e fulfillment | A primeira Gold cobrirá somente vendas |

## Assumptions & Open Questions

Every ambiguity is resolved or recorded here.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --- | --- | --- | --- |
| Ferramenta de transformação | dbt Core com adapter Snowflake | Mantém SQL, dependências, testes e documentação no Git | Sim |
| Materialização Silver | Views | Mantém a camada source-conformed simples e sempre alinhada à Bronze | Sim |
| Materialização Gold | Tables reconstruídas integralmente | Oferece consultas rápidas sem antecipar complexidade incremental | Sim |
| Cobertura Silver | As 16 tabelas carregadas pelo dlt | Decisão do usuário | Sim |
| Domínio Gold inicial | Vendas | Decisão do usuário | Sim |
| Modelo Gold | Esquema estrela com fatos e dimensões | Decisão do usuário | Sim |
| Receita reconhecida | Soma de pagamentos com status `captured` | Decisão do usuário; representa valor efetivamente capturado | Sim |
| Histórico dimensional | SCD Tipo 1 | Decisão do usuário | Sim |
| Segurança dos dados | Excluir `password_hash` da extração; PII necessária somente na Silver; Gold sem PII direta | Decisão do usuário | Sim |
| Fuso analítico | UTC | Decisão do usuário | Sim |
| Moedas | Métricas permanecem separadas por código de moeda | Decisão do usuário | Sim |
| Frequência | Uma execução manual por dia | Combina a cadência diária escolhida com a automação adiada | Sim |
| Ambiente | Um database e os schemas `BRONZE`, `SILVER` e `GOLD` | Decisão do usuário para o laboratório inicial | Sim |
| Execução | Snowflake CLI para infraestrutura e dbt Core no terminal | Decisão do usuário | Sim |
| Severidade dos testes | Violações críticas interrompem o build | Decisão do usuário | Sim |
| Controle de concorrência | Apenas uma execução por vez | Evita disputa e estados parciais no ambiente único | Sim |
| Falha externa | Interromper, preservar evidências e permitir reexecução manual; sem retry automático | Condiz com operação manual e torna falhas visíveis | Sim |
| Ciclo de vida dos dados | N/A porque retenção, arquivamento e exclusão não mudam neste ciclo | A Bronze continua sendo substituída pela carga existente | Sim |
| Papéis Snowflake | Separar loader e transformer; nenhum deles administra a conta | Aplica menor privilégio sem exigir ambientes adicionais | Sim |

**Open questions:** none.

## User Stories

### P1: Código Snowflake versionado e seguro

**User Story**: Como mantenedor humano, quero que infraestrutura e transformações estejam no Git para reproduzir e revisar cada mudança.

**Why P1**: Sem código versionado, o estado do Snowflake não pode ser reconstruído nem auditado.

**Acceptance Criteria**:

1. The projeto analítico SHALL manter no Git os scripts de database, schemas, roles e grants, além do projeto dbt.
2. The projeto analítico SHALL manter senhas, chaves privadas, tokens e arquivos de credenciais fora do Git.
3. WHEN um script de infraestrutura for reaplicado ao mesmo ambiente THEN o Snowflake SHALL terminar no mesmo estado desejado sem falha por objeto já existente.
4. The role de carga SHALL possuir somente os privilégios necessários para gravar na Bronze.
5. The role de transformação SHALL possuir leitura na Bronze e criação ou atualização somente na Silver e Gold.
6. IF o arquivo de configuração local contiver `password_hash`, e-mail, telefone ou endereço THEN o Git SHALL ignorar esse arquivo.

**Independent Test**: Clonar o repositório em outro diretório, configurar credenciais locais e validar os scripts e o projeto dbt sem recuperar segredos do histórico Git.

### P1: Silver source-conformed

**User Story**: Como engenheiro de dados, quero uma Silver limpa e testada para usar entidades operacionais sem depender diretamente da Bronze.

**Why P1**: A Gold precisa de contratos estáveis e dados críticos validados.

**Acceptance Criteria**:

1. WHEN a Bronze válida estiver disponível THEN o dbt SHALL criar uma view Silver para cada uma das 16 tabelas carregadas.
2. The modelo Silver de usuários SHALL excluir a coluna `password_hash`.
3. The carga Bronze de usuários SHALL deixar de extrair a coluna `password_hash`.
4. The modelos Silver SHALL preservar as chaves naturais, granularidade e semântica de cada tabela de origem.
5. The modelos Silver SHALL normalizar timestamps analíticos para UTC.
6. The testes Silver SHALL validar unicidade e não nulidade de todas as chaves primárias.
7. The testes Silver SHALL validar relacionamentos das chaves estrangeiras usadas pela Gold.
8. The testes Silver SHALL validar os valores aceitos para status de pedido e pagamento.
9. IF um teste Silver crítico falhar THEN o processo SHALL interromper a construção da Gold.

**Independent Test**: Executar somente a seleção Silver e obter 16 views com todos os testes críticos aprovados e sem a coluna `password_hash`.

### P1: Gold dimensional de vendas

**User Story**: Como futuro consumidor analítico, quero fatos e dimensões de vendas para calcular indicadores consistentes por tempo, cliente e produto.

**Why P1**: A Gold é o contrato de consumo para o futuro BI e bot.

**Acceptance Criteria**:

1. WHEN a Silver válida estiver disponível THEN o dbt SHALL construir dimensões Tipo 1 de data, cliente e produto.
2. WHEN a Silver válida estiver disponível THEN o dbt SHALL construir uma fato no grão de um registro por pedido.
3. WHEN a Silver válida estiver disponível THEN o dbt SHALL construir uma fato no grão de um registro por combinação de pedido e variante vendida.
4. The dimensão de cliente SHALL excluir nome, e-mail, telefone e endereço direto.
5. The dimensão de produto SHALL permitir análise por produto, variante e categoria.
6. The dimensão de data SHALL derivar dia, mês, trimestre e ano em UTC.
7. The fato de pedidos SHALL expor valor capturado, valor reembolsado, frete, subtotal, desconto, total do pedido, status e moeda.
8. The fato de itens SHALL expor quantidade, preço unitário, desconto, valor da linha e indicador de pagamento capturado.
9. The receita reconhecida SHALL ser a soma de pagamentos cujo status seja `captured`.
10. IF existirem moedas diferentes THEN as métricas financeiras SHALL permanecer particionadas por código de moeda.
11. The Gold SHALL permitir calcular receita reconhecida, pedidos pagos, ticket médio, unidades vendidas e receita de mercadorias sem juntar tabelas Bronze.
12. The testes Gold SHALL validar os grãos únicos das duas fatos e as referências às dimensões.
13. The testes Gold SHALL reconciliar subtotal menos desconto mais frete com o total do pedido.
14. The testes Gold SHALL reconciliar receita reconhecida com pagamentos capturados.

**Independent Test**: Executar a seleção Gold, consultar as cinco métricas por mês e moeda e reconciliar os totais com Silver.

### P1: Operação manual diária

**User Story**: Como operador humano, quero executar e diagnosticar o pipeline diário com comandos documentados.

**Why P1**: O primeiro ciclo precisa ser operável antes de ser automatizado.

**Acceptance Criteria**:

1. WHEN a carga diária for iniciada THEN o operador SHALL executar Bronze antes de Silver e Gold.
2. IF a carga Bronze falhar THEN o operador SHALL interromper a execução antes do dbt.
3. WHEN a carga Bronze concluir THEN o operador SHALL executar um comando dbt que construa modelos e testes na ordem de dependência.
4. IF um teste crítico falhar THEN o processo SHALL retornar código de saída diferente de zero e registrar o teste causador.
5. WHEN o pipeline for reexecutado sem alteração da Bronze ou do código THEN os modelos Gold SHALL produzir as mesmas contagens e somas por moeda.
6. WHILE uma execução estiver ativa, o procedimento operacional SHALL impedir o início de uma segunda execução.
7. The runbook SHALL documentar configuração inicial, execução diária, validação, diagnóstico e reexecução.
8. The execução SHALL preservar logs e artefatos dbt locais ignorados pelo Git.

**Independent Test**: Seguir o runbook a partir de um clone configurado, concluir uma execução e repetir o processo com os mesmos resultados.

## Edge Cases

- IF a Bronze estiver vazia THEN o build SHALL produzir relações válidas sem fabricar vendas.
- IF um pedido não possuir pagamento capturado THEN a receita reconhecida desse pedido SHALL ser zero.
- IF um pagamento estiver `refunded` THEN seu valor SHALL ficar fora da receita reconhecida e aparecer como valor reembolsado.
- IF um pedido possuir mais de um pagamento capturado THEN a receita reconhecida SHALL somar os valores capturados sem duplicar os itens do pedido.
- IF uma categoria possuir hierarquia THEN a dimensão de produto SHALL preservar ao menos a categoria direta sem exigir expansão recursiva.
- IF uma chave estrangeira crítica não encontrar dimensão correspondente THEN o teste SHALL falhar antes da conclusão do build.
- IF uma moeda não reconhecida estiver presente THEN o teste SHALL falhar em vez de misturar seu valor com outra moeda.
- IF o Snowflake estiver indisponível THEN o comando SHALL falhar sem marcar a execução como concluída.

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| --- | --- | --- | --- |
| REPO-01 | Código Snowflake versionado e seguro | Tasks | In Progress (T1, T4, T11 complete) |
| SEC-01 | Código Snowflake versionado e seguro | Tasks | In Progress (T1 complete) |
| SEC-02 | Código Snowflake versionado e seguro | Tasks | In Tasks |
| SILVER-01 | Silver source-conformed | Tasks | In Progress (T4, T11, T12, T22-T27 complete) |
| SILVER-02 | Silver source-conformed | Tasks | In Tasks |
| SILVER-03 | Silver source-conformed | Tasks | In Progress (T22-T26 complete) |
| SILVER-04 | Silver source-conformed | Tasks | In Progress (T27 complete) |
| GOLD-01 | Gold dimensional de vendas | Tasks | In Progress (T4, T11, T12 complete) |
| GOLD-02 | Gold dimensional de vendas | Tasks | In Tasks |
| GOLD-03 | Gold dimensional de vendas | Tasks | In Tasks |
| GOLD-04 | Gold dimensional de vendas | Tasks | In Tasks |
| GOLD-05 | Gold dimensional de vendas | Tasks | In Tasks |
| GOLD-06 | Gold dimensional de vendas | Tasks | In Tasks |
| GOLD-07 | Gold dimensional de vendas | Tasks | In Tasks |
| QUALITY-01 | Silver source-conformed | Tasks | In Progress (T22-T27 complete) |
| QUALITY-02 | Gold dimensional de vendas | Tasks | In Tasks |
| QUALITY-03 | Gold dimensional de vendas | Tasks | In Tasks |
| OPS-01 | Operação manual diária | Tasks | In Tasks |
| OPS-02 | Operação manual diária | Tasks | In Tasks |
| OPS-03 | Operação manual diária | Tasks | In Tasks |
| OPS-04 | Operação manual diária | Tasks | In Tasks |

**Coverage:** 21 requirements, 21 mapped to tasks, 0 unmapped.

## Success Criteria

- [ ] Um clone limpo contém todo o código necessário e nenhum segredo.
- [ ] As 16 tabelas Bronze possuem uma view Silver correspondente.
- [ ] `password_hash` deixa de ser extraído e não existe na Silver ou Gold.
- [ ] A Gold contém três dimensões e duas fatos com grãos testados.
- [ ] As cinco métricas de vendas reconciliam com Silver por moeda.
- [ ] Todos os testes críticos passam em uma execução diária completa.
- [ ] Uma segunda execução sem mudanças produz as mesmas contagens e somas.
- [ ] O runbook permite que o mantenedor execute e diagnostique o pipeline pelo terminal.
