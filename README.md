# SIEM TCC — Painel de Monitoramento de Intrusoes

Aplicativo desktop (Windows) que monitora o Log de Seguranca do Windows em
busca de tentativas de logon falhadas (Event ID 4625), geolocaliza os IPs
de origem, envia alertas via Telegram e exibe tudo em um painel visual.

## ⚠️ Acao necessaria antes de tudo

O projeto original tinha um **token real de bot do Telegram exposto** em
`scripts/teste_telegram.py`. Se esse token ainda for valido:

1. Abra o Telegram, converse com **@BotFather**.
2. Envie `/revoke` para o bot correspondente e gere um token novo.
3. Nunca mais coloque tokens direto no codigo — use sempre o arquivo `.env`
   (veja abaixo).

## O que mudou em relacao ao projeto original

| Area | Problema encontrado | Correcao |
|---|---|---|
| Imports | `app.py` importava `from database import ...` mas o arquivo estava em `core/database.py` — quebrava ao rodar | Imports corrigidos para `core.database`, `core.notifications`, etc. |
| Dependencia faltando | `app.py` usava `import webview` mas `pywebview` nao estava no `requeriments.txt` | Adicionado ao `requirements.txt`, e o import foi movido para dentro do bloco que so roda como app desktop (assim o resto do app roda mesmo sem pywebview instalado) |
| Banco de dados no `.exe` | Caminho do banco era relativo ao codigo — dentro de um `.exe` gerado pelo PyInstaller (modo onefile) isso aponta para uma pasta **temporaria que e apagada ao fechar o programa** | `config.py` agora grava o banco em `%LOCALAPPDATA%\SIEM_TCC` (pasta persistente do usuario) quando rodando como executavel |
| Segredos no codigo | Token do Telegram, chat ID e a ausencia de uma `SECRET_KEY` do Flask estavam hardcoded/expostos | Tudo migrado para `.env` (nunca commitado); `SECRET_KEY` e gerada automaticamente na primeira execucao se nao existir |
| Autenticacao | Nao existia — qualquer pessoa na maquina podia abrir o painel | Tela de login com Flask-Login, protecao CSRF (Flask-WTF) e senhas com hash **Argon2id** |
| Tratamento de erros | Varios `except: pass` escondendo qualquer erro (inclusive `KeyboardInterrupt`) | Substituidos por excecoes especificas + `logging`, para que falhas fiquem visiveis nos logs |
| Portabilidade | `core/monitor.py` (antigo `alerts.py`) travava se rodado fora do Windows | Checagem de plataforma: fora do Windows o app avisa e continua funcionando (dashboard/login), so o monitoramento automatico fica indisponivel |
| Estrutura | Pasta `.venv` (53 MB) e `dist/app.exe` antigos estavam dentro do `.rar` do projeto; havia dois `.db` duplicados na raiz | `.gitignore` cobre `.venv/`, `dist/`, `build/`, `*.db`, `.env`; estrutura reorganizada (veja abaixo) |
| Requirements | Arquivo se chamava `requeriments.txt` (typo) e listava `PyMySQL` sem uso | Renomeado para `requirements.txt`, dependencia nao usada removida, dependencias novas adicionadas |

## Estrutura do projeto

```
SIEM_TCC/
├── app.py                  # ponto de entrada: Flask + janela desktop
├── config.py                # config central (.env, caminhos, banco)
├── requirements.txt
├── siem.spec                 # spec do PyInstaller
├── build_exe.bat             # gera o .exe com um clique (Windows)
├── .env.example               # modelo de configuracao (copie para .env)
├── core/
│   ├── database.py          # modelos (Alerta, Usuario) + sessao SQLAlchemy
│   ├── auth.py                # hashing Argon2id + Flask-Login
│   ├── monitor.py             # leitura do Log de Seguranca do Windows
│   └── notifications.py       # geolocalizacao de IP + envio ao Telegram
├── scripts/
│   ├── criar_usuario.py     # cria/redefine a senha do admin
│   ├── gerar_testes.py        # popula o banco com dados de demonstracao
│   ├── consultar_banco.py     # consulta rapida via terminal
│   └── teste_telegram.py      # testa a integracao com o Telegram
├── static/css/style.css
└── templates/
    ├── login.html
    └── dashboard.html
```

## Como rodar em modo desenvolvimento

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

copy .env.example .env        # depois edite o .env com seus dados

python scripts/criar_usuario.py   # cria o usuario admin (senha minima: 8 caracteres)

python app.py
```

O monitoramento real do Log de Seguranca (Event ID 4625) **so funciona no
Windows** e exige que o app rode com permissao para ler o Log de Seguranca
(normalmente e preciso executar como Administrador). Em outros sistemas o
painel funciona normalmente, apenas sem captura automatica de novos eventos
— util para desenvolver a interface sem precisar de uma maquina Windows.

## Como gerar o executavel (.exe)

O build precisa ser feito **em uma maquina Windows** (PyInstaller empacota
para a plataforma em que roda, e as dependencias `pywin32`/`pywebview`
usadas aqui sao especificas do Windows):

1. Clone/copie a pasta do projeto para o Windows.
2. Configure o `.env` (veja secao anterior).
3. Rode `python scripts/criar_usuario.py` para ja deixar um usuario criado
   (ou deixe para o usuario final rodar isso apos instalar).
4. De um duplo-clique em `build_exe.bat` (ou rode `pyinstaller siem.spec`
   manualmente dentro do venv).
5. O executavel final fica em `dist/SIEM_TCC.exe`.

Como o banco de dados e o `.env` ficam fora do bundle do PyInstaller
(gravados em `%LOCALAPPDATA%\SIEM_TCC`), o `.exe` pode ser movido para
qualquer pasta ou distribuido para outro computador sem perder dados a
cada execucao.

## Seguranca da senha (item pedido no TCC)

As senhas sao protegidas com **Argon2id**, o algoritmo vencedor da Password
Hashing Competition (2015) e atualmente recomendado pela OWASP para
armazenamento de senhas — superior a MD5/SHA1/SHA256 puros (rapidos demais,
vulneraveis a forca bruta em GPU) e ao bcrypt em resistencia a ataques com
hardware dedicado, pois exige quantidade configuravel de memoria
(`memory_cost=64MB` neste projeto) alem de tempo de CPU. Cada senha recebe
um salt aleatorio unico gerado automaticamente pela biblioteca, e a senha
em texto puro nunca e armazenada, logada ou persistida em lugar nenhum.

O login tambem inclui protecao CSRF (Flask-WTF) e um pequeno mecanismo de
mitigacao de "user enumeration" (o tempo de resposta e semelhante para
usuario inexistente e senha incorreta).

## Observacoes para a defesa do TCC

- O antigo `.venv` e `dist/app.exe` que vieram junto no `.rar` **nao devem
  ser versionados** — sao artefatos de build, e o `.gitignore` ja os
  ignora. Sempre gere o `.exe` na hora com `build_exe.bat`.
- Se for demonstrar sem estar em uma maquina Windows real com eventos de
  logon de verdade, use `python scripts/gerar_testes.py` para popular o
  painel com dados de exemplo.
