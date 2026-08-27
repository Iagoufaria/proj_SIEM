"""
Cria ou redefine a senha de um usuario do painel SIEM.

Uso:
    python scripts/criar_usuario.py

A senha e digitada de forma oculta (getpass) e nunca fica salva em
texto puro - apenas o hash Argon2id vai para o banco de dados.
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.auth import criar_usuario, hash_senha
from core.database import Session, Usuario, init_db


def main() -> None:
    init_db()
    db = Session()

    username = input("Nome de usuario [admin]: ").strip() or "admin"

    senha = getpass.getpass("Senha: ")
    if len(senha) < 8:
        print("[!] A senha deve ter pelo menos 8 caracteres.")
        sys.exit(1)

    confirmacao = getpass.getpass("Confirme a senha: ")
    if senha != confirmacao:
        print("[!] As senhas nao coincidem.")
        sys.exit(1)

    existente = db.query(Usuario).filter_by(username=username).first()
    if existente:
        existente.password_hash = hash_senha(senha)
        db.commit()
        print(f"[V] Senha do usuario '{username}' atualizada com sucesso.")
    else:
        criar_usuario(username, senha)
        print(f"[V] Usuario '{username}' criado com sucesso.")


if __name__ == "__main__":
    main()
