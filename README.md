# SIEM TCC — Painel de Monitoramento e Alerta de Intrusões

Aplicativo desktop (Windows) para Trabalho de Conclusão de Curso que monitora
o **Log de Segurança do Windows** em busca de tentativas de logon falhadas
(**Event ID 4625**), geolocaliza os IPs de origem, envia alertas em tempo
real via **Telegram** e exibe tudo em um painel visual protegido por login.

---

## Sumário

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Arquitetura e stack tecnológica](#arquitetura-e-stack-tecnológica)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação e execução (modo desenvolvimento)](#instalação-e-execução-modo-desenvolvimento)
- [Variáveis de ambiente (.env)](#variáveis-de-ambiente-env)
- [Scripts utilitários](#scripts-utilitários)
- [Modelo de dados](#modelo-de-dados)
- [Rotas da aplicação](#rotas-da-aplicação)
- [Geração do executável (.exe)](#geração-do-executável-exe)
- [Segurança implementada](#segurança-implementada)
- [Limitações conhecidas](#limitações-conhecidas)
- [Possíveis evoluções futuras](#possíveis-evoluções-futuras)
- [Observações para a defesa do TCC](#observações-para-a-defesa-do-tcc)

---

## Visão geral

O **SIEM TCC** (Security Information and Event Management) é uma aplicação
desktop que roda localmente na máquina do usuário. Ela combina:

- um **backend Flask** que expõe um painel web local (autenticado);
- uma **janela desktop nativa** (via `pywebview`) que carrega esse painel,
  dando a experiência de um aplicativo instalado, sem depender de um
  navegador externo;
- uma **thread de monitoramento em segundo plano** que varre periodicamente
  o Log de Segurança do Windows, detecta tentativas de logon falhadas,
  geolocaliza o IP de origem e dispara um alerta no Telegram.

O objetivo é demonstrar, na prática, os conceitos centrais de um SIEM em
escala reduzida: **coleta de eventos → correlação/registro → alerta em
tempo real → visualização**.

## Funcionalidades

- 🔒 **Login protegido** (Flask-Login) com senha em hash Argon2id e proteção CSRF.
- 🖥️ **Monitoramento automático** do Log de Segurança do Windows (Event ID 4625).
- 🌍 **Geolocalização** do IP de origem de cada tentativa de logon (via `ip-api.com`).
- 📲 **Alertas instantâneos no Telegram** para cada nova intrusão detectada.
- 📊 **Dashboard visual** com lista dos últimos eventos, gráfico por usuário
  atacado e destaque para IPs com mais de 3 tentativas (possíveis IPs a bloquear).
- 📁 **Exportação em CSV** de todos os alertas registrados.
- 💻 **Multiplataforma para desenvolvimento**: fora do Windows o painel
  continua funcionando normalmente (login, dashboard, exportação); apenas a
  captura automática de eventos reais fica indisponível.
- 📦 **Empacotável em `.exe`** único via PyInstaller, com banco de dados e
  configurações persistidos fora do bundle.

## Arquitetura e stack tecnológica

| Camada | Tecnologia |
|---|---|
| Backend / servidor local | Flask 3 |
| Janela desktop | pywebview |
| Autenticação | Flask-Login + Argon2id (argon2-cffi) |
| Proteção CSRF | Flask-WTF |
| ORM / banco de dados | SQLAlchemy 2 + SQLite |
| Geolocalização de IP | API pública `ip-api.com` |
| Notificações | Telegram Bot API |
| Configuração/segredos | python-dotenv (arquivo `.env`) |
| Empacotamento | PyInstaller (modo onefile, `.exe` Windows) |
| Frontend | HTML + CSS (Jinja2 templates), sem framework JS pesado |

**Fluxo de funcionamento:**

```
Log de Segurança do Windows (Event ID 4625)
            │  (PowerShell / Get-WinEvent, a cada N segundos)
            ▼
   core/monitor.py  ──►  geolocalização (core/notifications.py)
            │
            ▼
   banco de dados SQLite (core/database.py)
            │
            ├──► Telegram (alerta em tempo real)
            └──► Dashboard web (app.py + templates/dashboard.html)
```

## Estrutura do projeto

```
SIEM_TCC/
├── app.py                    # ponto de entrada: servidor Flask + janela desktop
├── config.py                 # configuração central (.env, caminhos, banco)
├── requirements.txt          # dependências Python
├── siem.spec                 # especificação do PyInstaller
├── build_exe.bat             # gera o .exe com um clique (Windows)
├── .env.example               # modelo de configuração (copie para .env)
├── .gitignore
├── core/
│   ├── __init__.py
│   ├── database.py           # modelos (Alerta, Usuario) + sessão SQLAlchemy
│   ├── auth.py                # hashing Argon2id + Flask-Login
│   ├── monitor.py             # leitura do Log de Segurança do Windows
│   └── notifications.py       # geolocalização de IP + envio ao Telegram
├── scripts/
│   ├── criar_usuario.py      # cria/redefine a senha do usuário admin
│   ├── gerar_testes.py        # popula o banco com dados de demonstração
│   ├── consultar_banco.py     # consulta rápida via terminal
│   └── teste_telegram.py      # testa a integração com o Telegram
├── static/
│   └── css/style.css
└── templates/
    ├── login.html
    └── dashboard.html
```

## Pré-requisitos

- **Python 3.11+** instalado (recomendado 3.11 ou 3.12).
- **Windows 10/11** para o monitoramento real de eventos e para gerar o `.exe`.
  Em Linux/Mac é possível rodar o painel em modo desenvolvimento (sem captura
  automática de eventos).
- Permissão para **executar como Administrador** ao rodar no Windows, pois a
  leitura do Log de Segurança normalmente exige privilégios elevados.
- Uma conta no **Telegram** e um bot criado via [@BotFather](https://t.me/BotFather),
  caso deseje receber alertas.

## Instalação e execução (modo desenvolvimento)

```bash
# 1. Clone/baixe o projeto e entre na pasta
cd SIEM_TCC

# 2. Crie e ative um ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
copy .env.example .env        # Windows
# cp .env.example .env        # Linux/Mac
# edite o .env com seus dados (veja a seção abaixo)

# 5. Crie o usuário administrador do painel
python scripts/criar_usuario.py

# 6. Rode a aplicação
python app.py
```

Ao rodar, o Flask sobe em `http://127.0.0.1:5001` (porta configurável) e uma
janela desktop é aberta automaticamente apontando para esse endereço.

> O monitoramento real do Log de Segurança (Event ID 4625) **só funciona no
> Windows** e exige permissão para ler o Log de Segurança (normalmente é
> preciso executar como Administrador). Em outros sistemas o painel funciona
> normalmente, apenas sem captura automática de novos eventos — útil para
> desenvolver a interface sem precisar de uma máquina Windows.

## Variáveis de ambiente (.env)

Copie `.env.example` para `.env` e preencha:

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SECRET_KEY` | Não | Chave usada pelo Flask para assinar sessões/cookies. Se não for definida, é gerada automaticamente e persistida na primeira execução. |
| `TELEGRAM_TOKEN` | Para alertas | Token do bot, obtido com o @BotFather. |
| `TELEGRAM_CHAT_ID` | Para alertas | ID do chat/usuário que receberá os alertas, obtido com @userinfobot. |
| `SIEM_PORT` | Não (padrão `5001`) | Porta local usada pelo servidor Flask embutido. |
| `SIEM_SCAN_WINDOW_MINUTES` | Não (padrão `5`) | Janela de tempo, em minutos, verificada a cada varredura do log. |
| `SIEM_SCAN_INTERVAL_SECONDS` | Não (padrão `10`) | Intervalo, em segundos, entre cada varredura do log de eventos. |

**Nunca** commite o arquivo `.env` — ele já está listado no `.gitignore`.

## Scripts utilitários

| Script | Uso |
|---|---|
| `scripts/criar_usuario.py` | Cria ou redefine a senha de um usuário do painel. Solicita a senha de forma oculta (mínimo 8 caracteres) e nunca a grava em texto puro. |
| `scripts/gerar_testes.py` | Insere alertas de exemplo no banco (e tenta enviá-los ao Telegram, se configurado) — útil para demonstrar o painel sem depender de tentativas reais de logon. |
| `scripts/consultar_banco.py` | Lista via terminal os 10 últimos alertas registrados no banco. |
| `scripts/teste_telegram.py` | Envia uma mensagem de teste ao Telegram usando as credenciais do `.env`, para validar a integração isoladamente. |

Exemplos:

```bash
python scripts/criar_usuario.py
python scripts/gerar_testes.py
python scripts/consultar_banco.py
python scripts/teste_telegram.py
```

## Modelo de dados

Banco SQLite (`eventos_seguranca.db`), gerenciado via SQLAlchemy.

**Tabela `alertas`**

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | Integer (PK) | Identificador do alerta |
| `data_hora` | DateTime | Data/hora de registro do alerta |
| `usuario` | String | Nome de usuário alvo da tentativa de logon |
| `ip_origem` | String | IP de origem da tentativa |
| `pais` | String | País resolvido a partir do IP |
| `codigo_pais` | String | Código do país (ex.: `br`, `us`, `ru`) |
| `mensagem_bruta` | String | Texto/observação bruta associada ao evento |

**Tabela `usuarios`**

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | Integer (PK) | Identificador do usuário do painel |
| `username` | String (único) | Nome de login |
| `password_hash` | String | Hash Argon2id da senha |
| `criado_em` | DateTime | Data de criação da conta |

## Rotas da aplicação

| Rota | Método | Protegida por login | Descrição |
|---|---|---|---|
| `/login` | GET/POST | Não | Formulário de autenticação |
| `/logout` | GET | Sim | Encerra a sessão |
| `/` | GET | Sim | Dashboard: últimos 20 alertas, estatísticas por usuário e IPs com mais de 3 tentativas |
| `/exportar` | GET | Sim | Exporta todos os alertas em CSV |

## Geração do executável (.exe)

O build precisa ser feito **em uma máquina Windows**, pois `pywin32` e
`pywebview` são específicos dessa plataforma:

1. Copie a pasta do projeto para o Windows.
2. Configure o `.env` (veja a seção acima).
3. Rode `python scripts/criar_usuario.py` para já deixar um usuário criado
   (ou deixe essa etapa para o usuário final).
4. Dê duplo-clique em `build_exe.bat`, ou rode manualmente dentro do venv:
   ```bash
   pyinstaller siem.spec
   ```
5. O executável final fica em `dist/SIEM_TCC.exe`.

Como o banco de dados e o `.env` ficam **fora** do bundle do PyInstaller
(gravados em `%LOCALAPPDATA%\SIEM_TCC`), o `.exe` pode ser movido para
qualquer pasta ou distribuído para outro computador sem perder dados a cada
execução.

## Segurança implementada

- **Hash de senha com Argon2id** (vencedor da Password Hashing Competition e
  atualmente recomendado pela OWASP), com `memory_cost=64MB`, superior a
  MD5/SHA1/SHA256 puros (rápidos demais, vulneráveis a força bruta em GPU) e
  ao bcrypt em resistência a hardware dedicado. Cada senha recebe um salt
  aleatório único gerado automaticamente; a senha em texto puro nunca é
  armazenada, logada ou persistida.
- **Proteção CSRF** em todos os formulários (Flask-WTF).
- **Mitigação de user enumeration**: o tempo de resposta é semelhante tanto
  para usuário inexistente quanto para senha incorreta (um hash "fantasma" é
  computado mesmo quando o usuário não existe).
- **Segredos fora do código-fonte**: token do Telegram, chat ID e
  `SECRET_KEY` vêm de um `.env` nunca commitado; a `SECRET_KEY` é gerada
  automaticamente e persistida na primeira execução, se ausente.
- **Tratamento de erros explícito**: exceções específicas + `logging`, sem
  `except: pass` silenciosos que poderiam mascarar falhas.

## Limitações conhecidas

- O monitoramento automático de eventos depende do PowerShell/`Get-WinEvent`
  e só funciona no Windows.
- A geolocalização depende de uma API pública gratuita (`ip-api.com`), sujeita
  a limite de requisições e indisponibilidade eventual.
- O envio de alertas depende de conectividade com a API do Telegram; falhas
  de rede são logadas, mas não há fila de reenvio.
- O banco de dados é local (SQLite) — não há sincronização entre múltiplas
  instalações/instâncias.

## Possíveis evoluções futuras

- Suporte a outros Event IDs (ex.: criação de contas, elevação de
  privilégio, alterações de política de auditoria).
- Regras de correlação mais sofisticadas (ex.: geovelocidade, múltiplos
  países em curto intervalo).
- Bloqueio automático de IP (integração com firewall) para os IPs
  destacados no dashboard.
- Suporte a múltiplos canais de alerta (e-mail, Slack, webhook genérico).
- Paginação e filtros (por usuário, país, período) no dashboard.

## Observações para a defesa do TCC

- Se for demonstrar sem estar em uma máquina Windows real com eventos de
  logon de verdade, use `python scripts/gerar_testes.py` para popular o
  painel com dados de exemplo.
- Sempre gere o `.exe` na hora com `build_exe.bat` — artefatos de build
  antigos (`.venv/`, `dist/`) não devem ser versionados e já estão cobertos
  pelo `.gitignore`.
- Se o projeto foi herdado de uma versão anterior que teve um token do
  Telegram exposto no código, revogue-o no @BotFather (`/revoke`) e gere um
  novo antes de qualquer demonstração pública.
