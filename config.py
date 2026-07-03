"""
Configuracao central do SIEM TCC.

Resolve dois problemas do projeto original:

1. Segredos (token do Telegram, chave secreta do Flask) estavam
   escritos diretamente no codigo-fonte. Agora vem de um arquivo
   ".env" (nunca commitado) via python-dotenv.

2. O banco de dados era gravado dentro da pasta onde o script/exe
   esta rodando. Quando o app e empacotado com o PyInstaller no modo
   "onefile", o executavel roda a partir de uma pasta TEMPORARIA
   (sys._MEIPASS) que e apagada ao fechar o programa -> o banco de
   dados (e o .env) seriam perdidos a cada execucao.
   Agora usamos uma pasta persistente do usuario:
     Windows: %LOCALAPPDATA%\\SIEM_TCC
     Linux/Mac (uso em desenvolvimento): ~/.siem_tcc
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _is_frozen() -> bool:
    """Retorna True quando rodando como executavel gerado pelo PyInstaller."""
    return getattr(sys, "frozen", False)


def _base_bundle_dir() -> Path:
    """Pasta onde os arquivos estaticos (templates, etc.) foram extraidos.

    Em modo congelado (exe), o PyInstaller extrai tudo para sys._MEIPASS.
    Em desenvolvimento, e a propria pasta do projeto.
    """
    if _is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def _persistent_data_dir() -> Path:
    """Pasta GRAVAVEL e persistente para banco de dados e .env do usuario.

    Nunca aponta para dentro do bundle do PyInstaller, pois essa pasta
    e temporaria e some quando o programa fecha.
    """
    if _is_frozen():
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA") or str(Path.home())
        else:
            base = str(Path.home())
        data_dir = Path(base) / "SIEM_TCC"
    else:
        # Em desenvolvimento, mantemos tudo dentro do projeto para
        # facilitar inspecionar o banco de dados.
        data_dir = Path(__file__).resolve().parent / "data"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


BASE_DIR = _base_bundle_dir()
DATA_DIR = _persistent_data_dir()
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Carrega o .env de dentro da pasta persistente (para que o usuario
# consiga editar suas credenciais mesmo depois de gerar o .exe) e,
# como fallback, o .env dentro da pasta do projeto (uso em dev).
load_dotenv(DATA_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

DB_PATH = DATA_DIR / "eventos_seguranca.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if not SECRET_KEY:
    # Gera e persiste uma chave aleatoria na primeira execucao, para que
    # o app nunca rode com uma chave secreta previsivel/vazia.
    import secrets

    SECRET_KEY = secrets.token_hex(32)
    env_path = DATA_DIR / ".env"
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"\nSECRET_KEY={SECRET_KEY}\n")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_ENABLED = bool(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)

SIEM_PORT = int(os.environ.get("SIEM_PORT", "5001"))
SCAN_WINDOW_MINUTES = int(os.environ.get("SIEM_SCAN_WINDOW_MINUTES", "5"))
SCAN_INTERVAL_SECONDS = int(os.environ.get("SIEM_SCAN_INTERVAL_SECONDS", "10"))

IS_WINDOWS = sys.platform == "win32"
