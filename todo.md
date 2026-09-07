# TODO

- [ ] Migrar as integrações dlt e dbt do usuário compartilhado `LOADER` para usuários `TYPE=SERVICE` separados, autenticados por key pairs.
- [ ] Fixar dependências analíticas
  - Declarar versões compatíveis de dbt Core e adapter Snowflake em `dw/snowflake/analytics/requirements.txt`.
  - Reutilizar o padrão de `pipelines/ecommerce_bronze/requirements.txt`.
  - Validar a instalação em um ambiente virtual limpo.
  - Confirmar com `dbt --version` que core e adapter são compatíveis e não emitem avisos de incompatibilidade.
  - Commit futuro: `chore(dbt): pin snowflake analytics dependencies`.
