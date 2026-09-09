# Fundação Analítica Snowflake: Tarefas

## Execution Protocol

Este plano será executado por uma pessoa. Execute as fases e tarefas em ordem. Cada tarefa termina somente após seu gate passar e gera um commit Conventional Commit próprio. Não faça push, alteração remota ou execução no Snowflake sem a decisão humana correspondente.

**Design**: `.specs/features/snowflake-analytics-foundation/design.md`
**Status**: Approved

## Test Coverage Matrix

> Gerada a partir do código, da especificação e da ausência de padrões de teste prévios. Guidelines encontrados: nenhum; strong defaults aplicados. Estratégia confirmada: dbt unit tests + data tests + build integrado no Snowflake.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| --- | --- | --- | --- | --- |
| Bootstrap SQL | integration | Cada script reaplica sem erro e produz somente os objetos ou privilégios declarados | `dw/snowflake/bootstrap/*.sql` | `snow sql -f <arquivo>` seguido da consulta de verificação da tarefa |
| Extração dlt | integration | Happy path, ausência de `password_hash` e falha de conexão visível | `pipelines/ecommerce_bronze/` | `python ecommerce_bronze_pipeline.py` e consulta em `INFORMATION_SCHEMA` |
| Configuração dbt | static + integration | Dependências instaláveis, parse sem warnings e conexão válida | `dw/snowflake/analytics/` | `dbt deps && dbt debug && dbt parse` |
| Modelos Silver | data + integration | Todos os ACs Silver; PKs, FKs, domínios e empty state | `models/silver/stg_*` | `dbt build --select <modelo>+` |
| Modelos Gold | unit + data + integration | Lógica 1:1 com ACs Gold e todos os edge cases financeiros | `models/gold/*` | `dbt build --select <modelo>+` |
| Testes de reconciliação | data + integration | Cada regra retorna zero linhas inválidas | `tests/assert_*.sql` | `dbt test --select <teste>` |
| Runner PowerShell | integration | Happy path, lock, falha Bronze, falha dbt e reexecução | `dw/snowflake/scripts/*.ps1` | `pwsh -File dw/snowflake/scripts/run_daily.ps1` |
| Documentação | smoke | Um clone configurado segue o runbook sem conhecimento implícito | `dw/snowflake/*.md` | Executar os comandos documentados em ordem |

## Gate Check Commands

> Execute a partir da raiz do repositório. Configure `DBT_ENGINE_PROFILES_DIR` para o diretório local que contém `profiles.yml`.

| Gate Level | When to Use | Command |
| --- | --- | --- |
| Static | Configuração ou segurança sem transformação | `dbt parse --project-dir dw/snowflake/analytics` com `warn_error_options.error: all` no projeto, ou verificação específica da tarefa |
| Infrastructure | Cada script de bootstrap | `snow sql -f <arquivo>` duas vezes, seguido da consulta `SHOW` ou `INFORMATION_SCHEMA` indicada |
| Extraction | Mudanças no pipeline dlt | Executar `python pipelines/ecommerce_bronze/ecommerce_bronze_pipeline.py` e a consulta de schema indicada |
| Focused | Um modelo ou teste dbt | `dbt build --project-dir dw/snowflake/analytics --select <recurso>+ --warn-error` |
| Full | Fim de fase com acesso ao Snowflake | `dbt build --project-dir dw/snowflake/analytics --warn-error` |
| Final | Encerramento do plano | Executar runner duas vezes e comparar contagens e somas Gold por moeda |

## Execution Plan

As fases e tarefas são estritamente sequenciais.

### Phase 1: Segurança e bootstrap

```text
T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T8
```

### Phase 2: Fundação dbt

```text
T9 -> T10 -> T11 -> T12 -> T13
```

### Phase 3: Silver de cadastros

```text
T14 -> T15 -> T16 -> T17 -> T18 -> T19 -> T20 -> T21
```

### Phase 4: Silver transacional

```text
T22 -> T23 -> T24 -> T25 -> T26 -> T27 -> T28 -> T29
```

### Phase 5: Dimensões Gold

```text
T30 -> T31 -> T32
```

### Phase 6: Fatos e qualidade Gold

```text
T33 -> T34 -> T35 -> T36 -> T37 -> T38 -> T39
```

### Phase 7: Operação e handoff

```text
T40 -> T41 -> T42
```

## Task Breakdown

### Phase 1: Segurança e bootstrap

#### T1: Proteger segredos e artefatos locais

**What**: Atualizar regras Git para ignorar chaves privadas, perfis locais, logs, locks e artefatos dbt sem ignorar exemplos.
**Where**: `.gitignore`
**Depends on**: None
**Reuses**: `pipelines/ecommerce_bronze/.gitignore`
**Requirement**: REPO-01, SEC-01
**Tools**: Editor, Git.
**Done when**:
- [x] `git check-ignore` confirma arquivos fictícios `*.pem`, `profiles.yml`, `target/`, `logs/` e `*.lock`.
- [x] `profiles.yml.example` e `secrets.toml.example` permanecem rastreáveis.
- [x] `git status --short` não mostra segredo real.
**Tests**: static security check
**Gate**: Static
**Commit**: `chore(security): ignore local credentials and dbt artifacts`

#### T2: Criar database idempotente

**What**: Criar o script que garante a existência de `DATA_LAB`.
**Where**: `dw/snowflake/bootstrap/001_database.sql`
**Depends on**: T1
**Reuses**: `dw/snowflake/setup.sql`
**Requirement**: REPO-01
**Tools**: Snowflake CLI.
**Done when**:
- [x] O script contém somente a responsabilidade de database.
- [x] Duas execuções consecutivas passam.
- [x] `SHOW DATABASES LIKE 'DATA_LAB'` retorna exatamente um database.
**Tests**: integration
**Gate**: Infrastructure
**Commit**: `feat(snowflake): add idempotent database bootstrap`

#### T3: Criar roles idempotentes

**What**: Criar `DLT_LOADER_ROLE` e `DBT_TRANSFORMER_ROLE` sem grants.
**Where**: `dw/snowflake/bootstrap/002_roles.sql`
**Depends on**: T2
**Reuses**: `dw/snowflake/setup.sql`
**Requirement**: SEC-02
**Tools**: Snowflake CLI.
**Done when**:
- [x] Duas execuções consecutivas passam.
- [x] `SHOW ROLES` encontra as duas roles.
- [x] Nenhuma role administrativa é concedida às roles criadas.
**Tests**: integration
**Gate**: Infrastructure
**Commit**: `feat(snowflake): add analytics service roles`

#### T4: Criar schemas analíticos

**What**: Criar `BRONZE`, `SILVER` e `GOLD` dentro de `DATA_LAB`.
**Where**: `dw/snowflake/bootstrap/003_schemas.sql`
**Depends on**: T3
**Reuses**: Dataset `bronze` do pipeline dlt.
**Requirement**: REPO-01, SILVER-01, GOLD-01
**Tools**: Snowflake CLI.
**Done when**:
- [x] Duas execuções consecutivas passam.
- [x] `SHOW SCHEMAS IN DATABASE DATA_LAB` encontra os três schemas.
- [x] Nenhum schema adicional é criado.
**Tests**: integration
**Gate**: Infrastructure
**Commit**: `feat(snowflake): add medallion schemas`

#### T5: Aplicar grants de menor privilégio

**What**: Conceder ao loader somente Bronze e ao transformer leitura Bronze e administração Silver/Gold.
**Where**: `dw/snowflake/bootstrap/004_grants.sql`
**Depends on**: T4
**Reuses**: Warehouse `SNOWFLAKE_LEARNING_WH`.
**Requirement**: SEC-02
**Tools**: Snowflake CLI.
**Done when**:
- [x] As duas roles têm `USAGE` no warehouse e database.
- [x] Loader cria e altera relações em Bronze, mas falha em Silver e Gold.
- [x] Transformer lê Bronze e cria relações em Silver/Gold, mas não grava Bronze.
- [x] Grants de objetos existentes e futuros obedecem aos mesmos limites.
**Tests**: integration privilege tests
**Gate**: Infrastructure
**Commit**: `feat(snowflake): enforce least privilege grants`

#### T6: Configurar o usuário LOADER para as integrações

**What**: Reutilizar somente o user `LOADER` para dlt e dbt, com autenticação por usuário e senha no laboratório local.
**Where**: `dw/snowflake/bootstrap/005_service_users.sql`
**Depends on**: T5
**Reuses**: User `LOADER` existente e roles da T3.
**Requirement**: SEC-01, SEC-02
**Tools**: Snowflake CLI.
**Done when**:
- [x] O script contém somente placeholders, nunca senhas reais.
- [x] `LOADER` não usa `TYPE=SERVICE`, que bloqueia autenticação por senha.
- [x] `LOADER` recebe `DLT_LOADER_ROLE` e `DBT_TRANSFORMER_ROLE`, mantendo `DLT_LOADER_ROLE` como default.
- [x] Uma conexão por usuário e senha passa para `LOADER`.
- [x] Não é criado um segundo user para o dbt.
**Tests**: integration authentication tests
**Gate**: Infrastructure
**Commit**: `feat(snowflake): reuse loader integration user`

#### T7: Documentar credenciais dlt por usuário e senha

**What**: Documentar `username` e `password` no exemplo, mantendo a senha real somente no `secrets.toml` local ignorado pelo Git.
**Where**: `pipelines/ecommerce_bronze/.dlt/secrets.toml.example`
**Depends on**: T6
**Reuses**: Estrutura de configuração dlt existente.
**Requirement**: SEC-01
**Tools**: Editor, documentação dlt.
**Done when**:
- [x] O exemplo contém host, database, warehouse, role, username e senha fictícia.
- [x] Nenhuma credencial real aparece.
- [x] A cópia local ignorada autentica o loader.
**Tests**: static secret scan + integration connection
**Gate**: Extraction
**Commit**: `docs(dlt): use password credentials example`

#### T8: Excluir password hash da Bronze

**What**: Restringir a extração de `users` para nunca selecionar `password_hash`.
**Where**: `pipelines/ecommerce_bronze/ecommerce_bronze_pipeline.py`
**Depends on**: T7
**Reuses**: `sql_database` e lista de tabelas existentes.
**Requirement**: SEC-01, SILVER-02
**Tools**: Python, dlt, Snowflake CLI.
**Done when**:
- [x] As 16 tabelas continuam carregadas.
- [x] `DATA_LAB.BRONZE.USERS` não contém `PASSWORD_HASH` após replace.
- [x] Uma falha de conexão retorna código diferente de zero.
- [x] A carga completa passa.
**Tests**: integration extraction and schema test
**Gate**: Extraction
**Commit**: `fix(dlt): exclude password hashes from bronze`

### Phase 2: Fundação dbt

#### T10: Criar profile de exemplo

**What**: Documentar target oficial com usuário e senha fornecidos por variáveis de ambiente.
**Where**: `dw/snowflake/analytics/profiles.yml.example`
**Depends on**: T9
**Reuses**: User `LOADER`, `DBT_TRANSFORMER_ROLE` e `SNOWFLAKE_LEARNING_WH`.
**Requirement**: SEC-01, OPS-01
**Tools**: dbt Core.
**Done when**:
- [x] O target se chama `prod`.
- [x] O profile usa o user `LOADER` com `DBT_TRANSFORMER_ROLE`.
- [x] Username e password são referenciados por variáveis de ambiente.
- [x] Nenhum segredo real aparece.
- [x] Uma cópia local permite `dbt debug`.
**Tests**: static secret scan + integration connection
**Gate**: Static
**Commit**: `docs(dbt): add password profile example`

#### T11: Criar projeto dbt

**What**: Definir nome, profile, paths e materializações por camada.
**Where**: `dw/snowflake/analytics/dbt_project.yml`
**Depends on**: T10
**Reuses**: Schemas definidos na T4 e profile da T10.
**Requirement**: REPO-01, SILVER-01, GOLD-01
**Tools**: dbt Core.
**Done when**:
- [x] Silver está configurada como view e Gold como table.
- [x] `dbt parse` passa com a cópia local do profile e todos os warnings são fatais, exceto `UnusedResourceConfigPath` enquanto as pastas ainda não contêm modelos.
- [x] Artefatos são gerados somente em paths ignorados.
**Tests**: static dbt parse
**Gate**: Static
**Commit**: `feat(dbt): initialize snowflake analytics project`

#### T12: Mapear schemas por ambiente

**What**: Habilitar o macro oficial environment-aware para resolver Silver e Gold no target oficial.
**Where**: `dw/snowflake/analytics/macros/generate_schema_name.sql`
**Depends on**: T11
**Reuses**: Macro dbt `generate_schema_name_for_env`.
**Requirement**: SILVER-01, GOLD-01
**Tools**: dbt Core.
**Done when**:
- [x] Target `prod` compila modelos para `SILVER` ou `GOLD`.
- [x] Target não-prod compila para o schema padrão do profile.
- [x] O macro nunca retorna schema nulo.
- [x] `dbt parse --warn-error` passa.
**Tests**: dbt macro unit/static test
**Gate**: Static
**Commit**: `feat(dbt): add environment aware schema naming`

#### T13: Declarar fontes Bronze

**What**: Declarar as 16 tabelas Bronze, descrições e testes básicos de disponibilidade.
**Where**: `dw/snowflake/analytics/models/sources/ecommerce.yml`
**Depends on**: T12
**Reuses**: `TABLES` do pipeline dlt.
**Requirement**: SILVER-01, QUALITY-01
**Tools**: dbt Core, Snowflake.
**Done when**:
- [x] Todas as 16 tabelas estão declaradas uma vez.
- [x] Database e schema resolvem para `DATA_LAB.BRONZE`.
- [x] `dbt ls --resource-type source` lista 16 fontes e `dbt parse --warn-error` passa.
**Tests**: source integration tests
**Gate**: Focused
**Commit**: `feat(dbt): declare ecommerce bronze sources`

### Phase 3: Silver de cadastros

#### T14: Modelar usuários Silver

**What**: Criar view source-conformed de usuários e seus testes, sem `password_hash`.
**Where**: `dw/snowflake/analytics/models/silver/stg_users.*`
**Depends on**: T13
**Reuses**: Source `users`.
**Requirement**: SILVER-01, SILVER-02, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `user_id` é único e não nulo.
- [x] Timestamps usam UTC.
- [x] `password_hash` não compila no modelo.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model users`

#### T15: Modelar endereços Silver

**What**: Criar view source-conformed de endereços e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_addresses.*`
**Depends on**: T14
**Reuses**: Source `addresses`, `stg_users`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `address_id` é único e não nulo.
- [x] `user_id` referencia usuários.
- [x] Country code e timestamps preservam contrato.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model addresses`

#### T16: Modelar categorias Silver

**What**: Criar view source-conformed de categorias e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_categories.*`
**Depends on**: T15
**Reuses**: Source `categories`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `category_id` e `slug` são únicos e não nulos.
- [x] Categoria pai referencia categoria existente quando preenchida.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model categories`

#### T17: Modelar produtos Silver

**What**: Criar view source-conformed de produtos e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_products.*`
**Depends on**: T16
**Reuses**: Source `products`, `stg_categories`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `product_id` e `slug` são únicos e não nulos.
- [x] `category_id` referencia categorias.
- [x] Atributos sem equivalente analítico são preservados sem coerção destrutiva.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model products`

#### T18: Modelar variantes Silver

**What**: Criar view source-conformed de variantes e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_product_variants.*`
**Depends on**: T17
**Reuses**: Source `product_variants`, `stg_products`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `variant_id` e SKU são únicos e não nulos.
- [x] `product_id` referencia produtos.
- [x] Preço é não negativo e moeda é preservada.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model product variants`

#### T19: Modelar imagens Silver

**What**: Criar view source-conformed de imagens de produto e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_product_images.*`
**Depends on**: T18
**Reuses**: Source `product_images`, `stg_products`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `image_id` é único e não nulo.
- [x] `product_id` referencia produtos.
- [x] A combinação produto e ordem é única.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model product images`

#### T20: Modelar estoque Silver

**What**: Criar view source-conformed do snapshot de estoque e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_inventory.*`
**Depends on**: T19
**Reuses**: Source `inventory`, `stg_product_variants`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `variant_id` é único, não nulo e referencia variantes.
- [x] Quantidades são não negativas.
- [x] Timestamp está em UTC.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model inventory`

#### T21: Modelar transportadoras Silver

**What**: Criar view source-conformed de transportadoras e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_carriers.*`
**Depends on**: T20
**Reuses**: Source `carriers`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `carrier_id` e nome são únicos e não nulos.
- [x] Timestamp está em UTC.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model carriers`

### Phase 4: Silver transacional

#### T22: Modelar carrinhos Silver

**What**: Criar view source-conformed de carrinhos e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_carts.*`
**Depends on**: T21
**Reuses**: Source `carts`, `stg_users`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `cart_id` e session token são únicos e não nulos.
- [x] User opcional referencia usuários.
- [x] Status aceita somente `active`, `converted`, `abandoned`.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model carts`

#### T23: Modelar itens de carrinho Silver

**What**: Criar view source-conformed de itens de carrinho e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_cart_items.*`
**Depends on**: T22
**Reuses**: Source `cart_items`, carts e variantes Silver.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] O grão `cart_id, variant_id` é único.
- [x] As duas FKs são válidas.
- [x] Quantidade é maior que zero.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model cart items`

#### T24: Modelar pedidos Silver

**What**: Criar view source-conformed de pedidos e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_orders.*`
**Depends on**: T23
**Reuses**: Source `orders`, `stg_users`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `order_id` e `order_number` são únicos e não nulos.
- [x] User referencia usuários.
- [x] Status aceita somente valores da origem.
- [x] Valores são não negativos e timestamps estão em UTC.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model orders`

#### T25: Modelar itens de pedido Silver

**What**: Criar view source-conformed de itens de pedido e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_order_items.*`
**Depends on**: T24
**Reuses**: Source `order_items`, orders e variantes Silver.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] O grão `order_id, variant_id` é único.
- [x] As duas FKs são válidas.
- [x] Quantidade, preço, desconto e line total respeitam limites.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model order items`

#### T26: Modelar histórico de status Silver

**What**: Criar view source-conformed do histórico de pedidos e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_order_status_history.*`
**Depends on**: T25
**Reuses**: Source `order_status_history`, `stg_orders`.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `history_id` é único e não nulo.
- [x] Order referencia pedidos.
- [x] Status é aceito e `changed_at` está em UTC.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model order status history`

#### T27: Modelar pagamentos Silver

**What**: Criar view source-conformed de pagamentos e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_payments.*`
**Depends on**: T26
**Reuses**: Source `payments`, `stg_orders`.
**Requirement**: SILVER-01, SILVER-04, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `payment_id` é único e não nulo.
- [x] Order referencia pedidos.
- [x] Status e provider aceitam somente valores da origem.
- [x] Amount é não negativo e moeda está preenchida.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model payments`

#### T28: Modelar entregas Silver

**What**: Criar view source-conformed de entregas e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_shipments.*`
**Depends on**: T27
**Reuses**: Source `shipments`, orders e carriers Silver.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `shipment_id` é único e não nulo.
- [x] Order e carrier referenciam dimensões operacionais.
- [x] Entrega nunca antecede envio quando ambos existem.
- [x] O build focado passa.
**Tests**: data + integration
**Gate**: Focused
**Commit**: `feat(silver): model shipments`

#### T29: Modelar movimentos de estoque Silver

**What**: Criar view source-conformed do ledger de estoque e seus testes.
**Where**: `dw/snowflake/analytics/models/silver/stg_inventory_movements.*`
**Depends on**: T28
**Reuses**: Source `inventory_movements`, variantes e pedidos Silver.
**Requirement**: SILVER-01, SILVER-03, QUALITY-01
**Tools**: dbt Core.
**Done when**:
- [x] `movement_id` é único e não nulo.
- [x] Variant e order opcional têm relacionamentos válidos.
- [x] Delta nunca é zero e reason é aceito.
- [x] O build completo da Silver passa com 16 views.
**Tests**: data + integration
**Gate**: Full
**Commit**: `feat(silver): model inventory movements`

### Phase 5: Dimensões Gold

#### T30: Criar dimensão de data

**What**: Criar dimensão Tipo 1 das datas UTC presentes em pedidos, com testes e unit fixtures.
**Where**: `dw/snowflake/analytics/models/gold/dim_date.*`
**Depends on**: T29
**Reuses**: `stg_orders`.
**Requirement**: GOLD-01, GOLD-03, QUALITY-02
**Tools**: dbt Core.
**Done when**:
- [x] `date_key` é inteiro `YYYYMMDD`, único e não nulo.
- [x] Dia, semana, mês, trimestre e ano estão corretos nas fixtures.
- [x] Bronze vazia produz dimensão vazia válida.
- [x] O build focado passa.
**Tests**: unit + data + integration
**Gate**: Focused
**Commit**: `feat(gold): add date dimension`

#### T31: Criar dimensão de cliente

**What**: Criar dimensão Tipo 1 sem PII direta, com testes e unit fixtures.
**Where**: `dw/snowflake/analytics/models/gold/dim_customer.*`
**Depends on**: T30
**Reuses**: `stg_users`.
**Requirement**: GOLD-01, GOLD-04, SEC-01, QUALITY-02
**Tools**: dbt Core.
**Done when**:
- [x] Uma linha existe por `user_id`.
- [x] Estado ativo, criação e exclusão estão corretos.
- [x] Nome, empresa, e-mail, telefone e endereço não existem.
- [x] O build focado passa.
**Tests**: unit + data + integration
**Gate**: Focused
**Commit**: `feat(gold): add customer dimension`

#### T32: Criar dimensão de produto

**What**: Criar dimensão Tipo 1 no grão de variante, com testes e unit fixtures.
**Where**: `dw/snowflake/analytics/models/gold/dim_product.*`
**Depends on**: T31
**Reuses**: categorias, produtos e variantes Silver.
**Requirement**: GOLD-01, GOLD-05, QUALITY-02
**Tools**: dbt Core.
**Done when**:
- [x] Uma linha existe por `variant_id`.
- [x] Produto, variante e categoria direta estão corretos.
- [x] Preço, moeda e flags atuais seguem Tipo 1.
- [x] O build focado passa.
**Tests**: unit + data + integration
**Gate**: Focused
**Commit**: `feat(gold): add product dimension`

### Phase 6: Fatos e qualidade Gold

#### T33: Criar fato de pedidos

**What**: Criar fato no grão de pedido com pagamentos previamente agregados e cobertura unitária completa.
**Where**: `dw/snowflake/analytics/models/gold/fct_orders.*`
**Depends on**: T32
**Reuses**: orders, payments, dim_date e dim_customer.
**Requirement**: GOLD-02, GOLD-06, GOLD-07, QUALITY-02
**Tools**: dbt Core.
**Done when**:
- [x] Uma linha existe por pedido.
- [x] Fixtures cobrem captura, pendência, falha, refund, múltiplas capturas e ausência de pagamento.
- [x] Receita reconhecida e refund são somas condicionais por status.
- [x] Moeda permanece explícita.
- [x] O build focado passa.
**Tests**: unit + data + integration
**Gate**: Focused
**Commit**: `feat(gold): add orders fact`

#### T34: Criar fato de itens

**What**: Criar fato no grão de pedido e variante sem multiplicação por pagamentos.
**Where**: `dw/snowflake/analytics/models/gold/fct_order_items.*`
**Depends on**: T33
**Reuses**: itens, fato de pedidos, dim_date, dim_customer e dim_product.
**Requirement**: GOLD-02, GOLD-06, GOLD-07, QUALITY-02
**Tools**: dbt Core.
**Done when**:
- [x] O grão `order_id, product_key` é único.
- [x] Múltiplos pagamentos não duplicam item nem quantidade.
- [x] Indicador de captura, moeda e medidas estão corretos nas fixtures.
- [x] O build focado passa.
**Tests**: unit + data + integration
**Gate**: Focused
**Commit**: `feat(gold): add order items fact`

#### T35: Reconciliar total de pedidos

**What**: Criar teste que rejeita divergência entre subtotal, desconto, frete e total.
**Where**: `dw/snowflake/analytics/tests/assert_order_totals_reconcile.sql`
**Depends on**: T34
**Reuses**: Check 2 de `verify-ecommerce.sql`.
**Requirement**: QUALITY-03
**Tools**: dbt Core.
**Done when**:
- [x] Dataset válido retorna zero linhas.
- [x] Fixture mutante com total incorreto faz o teste falhar.
- [x] O teste usa precisão monetária explícita.
**Tests**: data + mutation check
**Gate**: Focused
**Commit**: `test(dbt): reconcile order totals`

#### T36: Reconciliar total de itens

**What**: Criar teste que compara soma das linhas com subtotal menos desconto.
**Where**: `dw/snowflake/analytics/tests/assert_item_totals_reconcile.sql`
**Depends on**: T35
**Reuses**: Check 3 de `verify-ecommerce.sql`.
**Requirement**: QUALITY-03
**Tools**: dbt Core.
**Done when**:
- [ ] Dataset válido retorna zero linhas.
- [ ] Fixture mutante com line total incorreto faz o teste falhar.
- [ ] Tolerância monetária está documentada e testada.
**Tests**: data + mutation check
**Gate**: Focused
**Commit**: `test(dbt): reconcile order item totals`

#### T37: Reconciliar receita capturada

**What**: Criar teste que compara receita Gold com pagamentos Silver capturados por moeda.
**Where**: `dw/snowflake/analytics/tests/assert_captured_revenue_reconciles.sql`
**Depends on**: T36
**Reuses**: Regra de pagamentos de `verify-ecommerce.sql`.
**Requirement**: GOLD-06, QUALITY-03
**Tools**: dbt Core.
**Done when**:
- [ ] Dataset válido retorna zero linhas.
- [ ] Pendentes, falhos e refunded ficam fora do capturado.
- [ ] Mutante que inclui refunded faz o teste falhar.
**Tests**: data + mutation check
**Gate**: Focused
**Commit**: `test(dbt): reconcile captured revenue`

#### T38: Impedir mistura de moedas

**What**: Criar teste que valida código de moeda e reconciliações particionadas por moeda.
**Where**: `dw/snowflake/analytics/tests/assert_supported_currencies.sql`
**Depends on**: T37
**Reuses**: Moedas de orders, items e payments Silver.
**Requirement**: GOLD-07, QUALITY-03
**Tools**: dbt Core.
**Done when**:
- [ ] Código nulo ou fora do formato ISO de três letras falha.
- [ ] Fixture com USD e EUR permanece em grupos distintos.
- [ ] Nenhum total financeiro remove a moeda do grão.
**Tests**: data + mutation check
**Gate**: Focused
**Commit**: `test(dbt): enforce currency boundaries`

#### T39: Impedir PII direta na Gold

**What**: Criar teste de metadados que falha se colunas proibidas aparecerem em relações Gold.
**Where**: `dw/snowflake/analytics/tests/assert_gold_has_no_direct_pii.sql`
**Depends on**: T38
**Reuses**: `INFORMATION_SCHEMA.COLUMNS`.
**Requirement**: SEC-01, GOLD-04
**Tools**: dbt Core, Snowflake.
**Done when**:
- [ ] Nome, e-mail, telefone, endereço e password hash são proibidos.
- [ ] Uma coluna mutante proibida faz o teste falhar.
- [ ] O build Gold completo passa com três dimensões e duas fatos.
**Tests**: data + mutation check
**Gate**: Full
**Commit**: `test(dbt): block direct pii in gold`

### Phase 7: Operação e handoff

#### T40: Criar runner manual diário

**What**: Encadear extração e dbt build com lock, logs, `SkipExtract` e fail-fast.
**Where**: `dw/snowflake/scripts/run_daily.ps1`
**Depends on**: T39
**Reuses**: Pipeline dlt e comandos dbt aprovados.
**Requirement**: OPS-01, OPS-02, OPS-03
**Tools**: PowerShell, Python, dbt Core.
**Done when**:
- [ ] Happy path executa Bronze antes do dbt.
- [ ] Falha Bronze impede dbt.
- [ ] Falha dbt retorna código não zero.
- [ ] Segunda execução simultânea é recusada.
- [ ] Lock é removido no sucesso e na falha.
- [ ] `SkipExtract` executa somente dbt.
**Tests**: integration runner scenarios
**Gate**: Full
**Commit**: `feat(ops): add manual daily pipeline runner`

#### T41: Escrever runbook operacional

**What**: Documentar pré-requisitos, bootstrap, credenciais, execução, validação, diagnóstico e reexecução.
**Where**: `dw/snowflake/RUNBOOK.md`
**Depends on**: T40
**Reuses**: Todos os comandos aprovados nas tarefas anteriores.
**Requirement**: OPS-01, OPS-02, OPS-04
**Tools**: Editor, terminal.
**Done when**:
- [ ] Um clone limpo chega a `dbt debug` sem instrução implícita.
- [ ] O runbook diferencia comandos locais de mudanças remotas.
- [ ] Falha de cada etapa possui diagnóstico e próximo comando seguro.
- [ ] A política de não editar diretamente no Snowsight está explícita.
**Tests**: documentation smoke test
**Gate**: Full
**Commit**: `docs(snowflake): add analytics operations runbook`

#### T42: Documentar arquitetura e resultados esperados

**What**: Criar a página de entrada com DAG, schemas, modelos, métricas e critérios finais de aceitação.
**Where**: `dw/snowflake/README.md`
**Depends on**: T41
**Reuses**: Spec, design e runbook.
**Requirement**: REPO-01, OPS-04
**Tools**: Editor, dbt docs.
**Done when**:
- [ ] A página aponta para bootstrap, analytics e runbook.
- [ ] As 16 relações Silver e cinco relações Gold estão listadas.
- [ ] As cinco métricas possuem definição e grão.
- [ ] Runner executado duas vezes produz as mesmas contagens e somas por moeda.
- [ ] `dbt docs generate` passa.
- [ ] Gate Final passa.
**Tests**: documentation smoke + full integration + idempotency
**Gate**: Final
**Commit**: `docs(snowflake): document analytics foundation`

## Phase Execution Map

```text
Phase 1: T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T8
Phase 2: T9 -> T10 -> T11 -> T12 -> T13
Phase 3: T14 -> T15 -> T16 -> T17 -> T18 -> T19 -> T20 -> T21
Phase 4: T22 -> T23 -> T24 -> T25 -> T26 -> T27 -> T28 -> T29
Phase 5: T30 -> T31 -> T32
Phase 6: T33 -> T34 -> T35 -> T36 -> T37 -> T38 -> T39
Phase 7: T40 -> T41 -> T42
```

## Task Granularity Check

| Tasks | Scope | Status |
| --- | --- | --- |
| T1 | Um arquivo de regras Git | ✅ Granular |
| T2-T6 | Um script de bootstrap por tarefa | ✅ Granular |
| T7-T13 | Um arquivo de configuração ou componente por tarefa | ✅ Granular |
| T14-T29 | Um modelo Silver com seu contrato co-localizado por tarefa | ✅ Granular |
| T30-T34 | Um modelo Gold com testes co-localizados por tarefa | ✅ Granular |
| T35-T39 | Um teste singular por tarefa | ✅ Granular |
| T40 | Um runner | ✅ Granular |
| T41-T42 | Um documento por tarefa | ✅ Granular |

## Diagram-Definition Cross-Check

| Phase | Tasks checked | Body dependencies | Diagram | Status |
| --- | --- | --- | --- | --- |
| 1 | T1-T8 | Cadeia T1 até T8 | Cadeia T1 até T8 | ✅ Match |
| 2 | T9-T13 | Cadeia T9 até T13; T9 depende da fase 1 | Cadeia T9 até T13 | ✅ Match |
| 3 | T14-T21 | Cadeia T14 até T21; T14 depende da fase 2 | Cadeia T14 até T21 | ✅ Match |
| 4 | T22-T29 | Cadeia T22 até T29; T22 depende da fase 3 | Cadeia T22 até T29 | ✅ Match |
| 5 | T30-T32 | Cadeia T30 até T32; T30 depende da fase 4 | Cadeia T30 até T32 | ✅ Match |
| 6 | T33-T39 | Cadeia T33 até T39; T33 depende da fase 5 | Cadeia T33 até T39 | ✅ Match |
| 7 | T40-T42 | Cadeia T40 até T42; T40 depende da fase 6 | Cadeia T40 até T42 | ✅ Match |

## Test Co-location Validation

| Tasks | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| --- | --- | --- | --- | --- |
| T1 | Git security config | static | static security | ✅ OK |
| T2-T6 | Bootstrap SQL | integration | integration | ✅ OK |
| T7 | dlt credentials example | static + integration | static + integration | ✅ OK |
| T8 | dlt extraction | integration | integration | ✅ OK |
| T9-T12 | dbt config | static + integration | static or integration | ✅ OK |
| T13 | dbt sources | integration | source integration | ✅ OK |
| T14-T29 | Silver models | data + integration | data + integration | ✅ OK |
| T30-T34 | Gold models | unit + data + integration | unit + data + integration | ✅ OK |
| T35-T39 | Singular business tests | data + integration | data + mutation | ✅ OK |
| T40 | Runner | integration | integration scenarios | ✅ OK |
| T41-T42 | Documentation | smoke | smoke + integration | ✅ OK |
