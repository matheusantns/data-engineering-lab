# Runbook operacional Snowflake

Este runbook prepara um clone novo, aplica a infraestrutura do laboratório e executa o pipeline diário na ordem `PostgreSQL -> Bronze -> Silver -> Gold`.

Os comandos usam PowerShell e partem da raiz do repositório.

## Limites operacionais

- Git é a fonte de verdade para infraestrutura, acessos e transformações.
- Edite SQL, modelos e testes no repositório. Aplique mudanças pelo terminal.
- Não crie, altere ou exclua objetos diretamente no Snowsight. Use o Snowsight somente para investigação e consultas de leitura. Converta qualquer correção necessária em código versionado antes de aplicá-la.
- `python`, `dbt parse`, cópias de exemplos e leitura de logs são ações locais.
- `snow sql`, a extração dlt, `dbt debug`, `dbt build` e o runner conectam a serviços remotos. O bootstrap altera o Snowflake. Execute-os somente no ambiente de laboratório autorizado.
- Não faça commit de `profiles.yml`, `secrets.toml`, senhas, chaves, logs, `target/` ou arquivos `*.lock`.

## Pré-requisitos

Instale:

- Git;
- Python 3.12 ou versão compatível com as dependências;
- Docker Desktop com Docker Compose, para o PostgreSQL de exemplo;
- PowerShell;
- Snowflake CLI;
- acesso administrativo ao Snowflake de laboratório;
- acesso ao warehouse existente `SNOWFLAKE_LEARNING_WH`.

Confirme os executáveis:

```powershell
git --version
python --version
docker compose version
$PSVersionTable.PSVersion
snow --version
```

Se `snow` não existir, instale a CLI fora do ambiente Python do projeto:

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
pipx install snowflake-cli
```

Feche e abra o terminal após `ensurepath`. Depois repita `snow --version`.

## Preparar um clone novo

Clone, entre no repositório e crie um ambiente virtual:

```powershell
git clone <repository-url> data-engineering-lab
Set-Location data-engineering-lab
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r pipelines\ecommerce_bronze\requirements.txt
```

Confirme que o adapter Snowflake está disponível:

```powershell
dbt --version
python -m pip check
```

Se a ativação de scripts estiver bloqueada, libere apenas a sessão atual e ative novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Iniciar e validar o PostgreSQL de origem

Suba o banco de exemplo:

```powershell
docker compose -f erp\sample-postgres\docker-compose.yml up -d
docker compose -f erp\sample-postgres\docker-compose.yml ps
```

O serviço deve aparecer como ativo na porta local `5433`. As credenciais de laboratório da origem já estão descritas no exemplo dlt.

Se o container não iniciar, veja o erro antes de tentar novamente:

```powershell
docker compose -f erp\sample-postgres\docker-compose.yml logs postgres
docker compose -f erp\sample-postgres\docker-compose.yml up -d
```

Não use `docker compose down -v` durante um diagnóstico. Esse comando remove os dados locais.

## Configurar e aplicar o bootstrap Snowflake

Esta seção altera o Snowflake. Use uma conexão administrativa humana no ambiente de laboratório.

Crie a conexão fora do repositório e teste a autenticação:

```powershell
snow connection add --connection-name data_lab_admin
snow connection test --connection data_lab_admin
```

Informe a conta, o usuário administrativo, a role administrativa e o warehouse `SNOWFLAKE_LEARNING_WH` quando solicitado. Não grave credenciais em arquivos do repositório.

Defina a senha temporária do user `LOADER` sem colocá-la no histórico do PowerShell:

```powershell
$securePassword = Read-Host "Senha temporária do LOADER" -AsSecureString
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $env:SNOWFLAKE_LOADER_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
}
```

Use uma senha que não contenha aspas simples, pois o placeholder está dentro de um literal SQL.

Aplique os scripts na ordem numérica:

```powershell
snow sql -c data_lab_admin -f dw\snowflake\bootstrap\001_database.sql
snow sql -c data_lab_admin -f dw\snowflake\bootstrap\002_roles.sql
snow sql -c data_lab_admin -f dw\snowflake\bootstrap\003_schemas.sql
snow sql -c data_lab_admin -f dw\snowflake\bootstrap\004_grants.sql
snow sql -c data_lab_admin -f dw\snowflake\bootstrap\005_service_users.sql -D "loader_password=$env:SNOWFLAKE_LOADER_PASSWORD"
Remove-Item Env:SNOWFLAKE_LOADER_PASSWORD
```

Os scripts são idempotentes. Reaplique a sequência inteira se uma etapa falhar depois de corrigir a causa.

Valide os objetos e acessos:

```powershell
snow sql -c data_lab_admin -q "SHOW DATABASES LIKE 'DATA_LAB'"
snow sql -c data_lab_admin -q "SHOW ROLES LIKE 'DLT_LOADER_ROLE'"
snow sql -c data_lab_admin -q "SHOW ROLES LIKE 'DBT_TRANSFORMER_ROLE'"
snow sql -c data_lab_admin -q "SHOW SCHEMAS IN DATABASE DATA_LAB"
snow sql -c data_lab_admin -q "SHOW GRANTS TO ROLE DLT_LOADER_ROLE"
snow sql -c data_lab_admin -q "SHOW GRANTS TO ROLE DBT_TRANSFORMER_ROLE"
snow sql -c data_lab_admin -q "SHOW GRANTS TO USER LOADER"
```

Se um script retornar erro de privilégio, confirme a conexão e a role:

```powershell
snow connection test --connection data_lab_admin
snow sql -c data_lab_admin -q "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()"
```

Corrija a role da conexão administrativa. Não contorne o erro criando objetos manualmente no Snowsight.

## Configurar credenciais locais

Crie a configuração dlt local a partir do exemplo:

```powershell
Copy-Item pipelines\ecommerce_bronze\.dlt\secrets.toml.example pipelines\ecommerce_bronze\.dlt\secrets.toml
```

Edite somente `pipelines\ecommerce_bronze\.dlt\secrets.toml` e substitua:

- `<postgres-password>` pela senha do PostgreSQL local;
- `<snowflake-password>` pela senha do `LOADER`;
- `<organization-account>` pelo identificador da conta Snowflake.

Crie o profile dbt local:

```powershell
Copy-Item dw\snowflake\analytics\profiles.yml.example dw\snowflake\analytics\profiles.yml
$env:DBT_SNOWFLAKE_ACCOUNT = "<organization-account>"
$env:DBT_SNOWFLAKE_USER = "LOADER"
$securePassword = Read-Host "Senha do LOADER" -AsSecureString
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
try {
    $env:DBT_ENV_SECRET_SNOWFLAKE_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
}
$env:DBT_ENGINE_PROFILES_DIR = (Resolve-Path dw\snowflake\analytics)
```

As variáveis valem somente para o processo atual do PowerShell. Defina-as novamente em cada novo terminal. Não salve a senha em um script versionado.

Confirme que os arquivos locais estão ignorados:

```powershell
git check-ignore pipelines\ecommerce_bronze\.dlt\secrets.toml
git check-ignore dw\snowflake\analytics\profiles.yml
git status --short
```

`git status --short` não deve listar nenhum arquivo de credencial.

## Validar a instalação até `dbt debug`

Valide primeiro a estrutura local e depois a conexão remota:

```powershell
dbt parse --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics
dbt debug --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics
```

O bootstrap do clone termina quando `dbt debug` informa que todas as verificações passaram.
O projeto já define `warn_error_options.error: all`. Não combine essa configuração com a opção `--warn-error`, pois o dbt rejeita as duas formas simultâneas.

Se `dbt parse` falhar, confirme o ambiente e os caminhos:

```powershell
Get-Command dbt
dbt --version
Test-Path dw\snowflake\analytics\dbt_project.yml
Test-Path dw\snowflake\analytics\profiles.yml
```

Corrija a instalação ou a cópia do profile e execute `dbt parse` novamente.

Se `dbt debug` falhar, confira as variáveis sem imprimir a senha:

```powershell
Test-Path Env:DBT_SNOWFLAKE_ACCOUNT
Test-Path Env:DBT_SNOWFLAKE_USER
Test-Path Env:DBT_ENV_SECRET_SNOWFLAKE_PASSWORD
dbt debug --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics
```

Erros de autenticação exigem corrigir conta, usuário ou senha. Erros de autorização exigem reaplicar e verificar os grants. Erros de rede exigem restaurar o acesso ao Snowflake antes da reexecução.

## Executar o pipeline diário

Confirme antes de iniciar:

- PostgreSQL ativo;
- variáveis dbt definidas no terminal;
- `secrets.toml` local preenchido;
- nenhuma outra execução ativa;
- Snowflake e warehouse disponíveis.

Execute Bronze, Silver, Gold e testes com um único comando:

```powershell
pwsh -NoProfile -File dw\snowflake\scripts\run_daily.ps1
```

Se `pwsh` não estiver disponível, use o Windows PowerShell:

```powershell
powershell -NoProfile -File dw\snowflake\scripts\run_daily.ps1
```

O runner:

1. cria `dw\snowflake\scripts\run_daily.lock`;
2. executa a extração Bronze com `write_disposition="replace"`;
3. executa `dbt build`, respeitando a DAG Silver antes de Gold e a política de warnings do projeto;
4. grava um log em `dw\snowflake\analytics\logs`;
5. remove o lock no sucesso ou na falha;
6. retorna código diferente de zero na primeira etapa que falhar.

Considere a execução concluída somente quando o log contiver `Daily pipeline completed successfully`.

## Validar uma execução

Localize o log mais recente e procure falhas:

```powershell
$latestLog = Get-ChildItem dw\snowflake\analytics\logs\run_daily_*.log |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
Get-Content $latestLog.FullName
Select-String -Path $latestLog.FullName -Pattern "failed|error|warn"
```

Valide novamente todos os modelos e testes quando necessário:

```powershell
dbt build --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics
```

Gere os artefatos de documentação local:

```powershell
dbt docs generate --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics
```

## Diagnóstico por etapa

### A extração Bronze falhou

Sinais: o log contém `Bronze extraction failed`; `Starting dbt build` não aparece.

Verifique o PostgreSQL e execute a extração isoladamente:

```powershell
docker compose -f erp\sample-postgres\docker-compose.yml ps
python pipelines\ecommerce_bronze\ecommerce_bronze_pipeline.py
```

Corrija a conexão indicada pela exceção. Depois execute o runner completo novamente. Não execute somente dbt se a Bronze diária ainda não concluiu.

### O build dbt falhou

Sinais: o log contém `dbt build failed` e identifica o modelo ou teste causador.

Reproduza com o mesmo projeto e profile:

```powershell
dbt build --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics
```

Corrija a Bronze, o modelo ou o teste no Git. Se a Bronze válida já foi carregada, reexecute somente transformação e testes:

```powershell
pwsh -NoProfile -File dw\snowflake\scripts\run_daily.ps1 -SkipExtract
```

Não marque uma execução parcial como concluída.

### O Snowflake está indisponível

Sinais: timeout, falha DNS, erro de autenticação ou warehouse indisponível.

Valide a conexão:

```powershell
dbt debug --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics
```

Restaure a conectividade ou o warehouse. Depois use o runner completo se a Bronze não concluiu, ou `-SkipExtract` se a Bronze válida já concluiu.

### Um teste crítico falhou

O nome do teste e a consulta compilada ficam no log e em `dw\snowflake\analytics\target`. Execute o recurso indicado de forma focada:

```powershell
dbt build --project-dir dw\snowflake\analytics --profiles-dir dw\snowflake\analytics --select <resource-name>+
```

Investigue os registros retornados pelo teste. Corrija dados de origem ou código versionado. Não altere dados ou testes diretamente no Snowsight para forçar aprovação.

### Uma moeda não suportada apareceu

Sinais: falha em `assert_supported_currencies`.

Confirme o valor na Bronze ou Silver com consulta de leitura. Decida e versione o suporte à nova moeda antes de reconstruir. Não converta nem misture moedas manualmente.

### A Bronze está vazia

Confirme se a origem realmente não possui dados. Relações Silver e Gold vazias são válidas; o pipeline não deve fabricar vendas. Se a origem deveria ter dados, corrija a origem ou as credenciais e execute o runner completo.

### Já existe um lock

Sinal: `Daily pipeline is already in progress`.

Leia o PID registrado:

```powershell
Get-Content dw\snowflake\scripts\run_daily.lock
Get-Process -Id (Get-Content dw\snowflake\scripts\run_daily.lock) -ErrorAction SilentlyContinue
```

Se o processo existir, aguarde. Remova o lock somente depois de comprovar que o processo não existe:

```powershell
Remove-Item dw\snowflake\scripts\run_daily.lock
pwsh -NoProfile -File dw\snowflake\scripts\run_daily.ps1
```

## Política de reexecução

- Não há retry automático.
- Preserve o log da falha e corrija a causa antes de reexecutar.
- Use o runner completo quando a Bronze falhou, não iniciou ou precisa ser recarregada.
- Use `-SkipExtract` somente quando a Bronze válida já concluiu e a falha ocorreu no dbt.
- O runner reconstrói a Gold e pode ser repetido. Sem alteração da Bronze ou do código, contagens e somas por moeda devem permanecer iguais.
- Nunca inicie uma segunda execução enquanto o primeiro processo estiver ativo.

Ao terminar a sessão, remova as variáveis sensíveis:

```powershell
Remove-Item Env:DBT_ENV_SECRET_SNOWFLAKE_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:SNOWFLAKE_LOADER_PASSWORD -ErrorAction SilentlyContinue
deactivate
```
