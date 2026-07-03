"""
Autenticacao do painel.

Senhas sao protegidas com Argon2id (vencedor da Password Hashing
Competition e recomendado atualmente pela OWASP), atraves da
biblioteca argon2-cffi. Cada hash embute automaticamente um salt
aleatorio unico, entao duas contas com a mesma senha geram hashes
diferentes, e o hash nunca e reversivel para a senha original.

A senha em si NUNCA e armazenada, logada ou enviada em texto puro
para lugar nenhum alem do formulario de login (via HTTPS/local).
"""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from flask_login import LoginManager, UserMixin

from core.database import Session, Usuario

_ph = PasswordHasher(
    time_cost=3,       # numero de iteracoes
    memory_cost=65536, # 64 MB de memoria por hash (dificulta ataques em GPU/ASIC)
    parallelism=2,
)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Faca login para acessar o painel."
login_manager.login_message_category = "warning"


class UsuarioLogado(UserMixin):
    """Wrapper exigido pelo Flask-Login em torno do modelo Usuario."""

    def __init__(self, usuario: Usuario):
        self.id = str(usuario.id)
        self.username = usuario.username


@login_manager.user_loader
def load_user(user_id: str):
    db = Session()
    usuario = db.get(Usuario, int(user_id))
    return UsuarioLogado(usuario) if usuario else None


def hash_senha(senha_texto_puro: str) -> str:
    """Gera o hash Argon2id de uma senha."""
    return _ph.hash(senha_texto_puro)


def verificar_senha(hash_armazenado: str, senha_texto_puro: str) -> bool:
    """Confere se a senha informada corresponde ao hash armazenado."""
    try:
        _ph.verify(hash_armazenado, senha_texto_puro)
    except (VerifyMismatchError, InvalidHashError):
        return False
    return True


def autenticar(username: str, senha: str) -> UsuarioLogado | None:
    """Valida credenciais e retorna o usuario logado, ou None se invalido."""
    db = Session()
    usuario = db.query(Usuario).filter_by(username=username).first()
    if usuario is None:
        # Ainda assim gasta tempo computando um hash "fantasma" para
        # que tentativas com usuario inexistente levem o mesmo tempo
        # de resposta de uma senha errada (mitiga user enumeration
        # por timing attack).
        _ph.hash(senha)
        return None

    if not verificar_senha(usuario.password_hash, senha):
        return None

    return UsuarioLogado(usuario)


def existe_algum_usuario() -> bool:
    db = Session()
    return db.query(Usuario).first() is not None


def criar_usuario(username: str, senha: str) -> Usuario:
    db = Session()
    usuario = Usuario(username=username, password_hash=hash_senha(senha))
    db.add(usuario)
    db.commit()
    return usuario
