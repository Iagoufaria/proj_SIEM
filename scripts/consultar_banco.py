"""Consulta rapida dos ultimos alertas registrados no banco de dados."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from core.database import engine


def main() -> None:
    print(f"{'ID':<5} | {'Data/Hora':<20} | {'Usuario':<15} | {'IP':<15} | {'Pais'}")
    print("-" * 75)

    with engine.connect() as conexao:
        resultado = conexao.execute(
            text(
                "SELECT id, data_hora, usuario, ip_origem, pais "
                "FROM alertas ORDER BY id DESC LIMIT 10"
            )
        )
        linhas = resultado.fetchall()

    if not linhas:
        print("(nenhum alerta registrado ainda)")
        return

    for linha in linhas:
        print(f"{linha[0]:<5} | {str(linha[1]):<20} | {linha[2]:<15} | {linha[3]:<15} | {linha[4]}")


if __name__ == "__main__":
    main()
