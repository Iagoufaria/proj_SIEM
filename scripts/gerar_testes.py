"""Insere alertas de teste no banco de dados e dispara notificacoes no Telegram
(se configurado no .env), util para demonstrar o painel sem depender de
tentativas reais de logon."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import Alerta, Session, init_db
from core.notifications import enviar_alerta_telegram

DADOS_TESTE = [
    {"usuario": "admin", "ip": "185.156.177.22", "pais": "Russia", "codigo": "ru"},
    {"usuario": "root", "ip": "43.153.1.240", "pais": "China", "codigo": "cn"},
    {"usuario": "guest", "ip": "157.240.22.35", "pais": "USA", "codigo": "us"},
    {"usuario": "operador", "ip": "127.0.0.1", "pais": "Local", "codigo": "br"},
]


def gerar_dados_teste() -> None:
    init_db()
    db = Session()

    print("[*] Inserindo dados de teste...")
    for item in DADOS_TESTE:
        novo = Alerta(
            data_hora=datetime.now(),
            usuario=item["usuario"],
            ip_origem=item["ip"],
            pais=item["pais"],
            codigo_pais=item["codigo"],
            mensagem_bruta="Ataque simulado (dados de teste)",
        )
        db.add(novo)
        enviado = enviar_alerta_telegram(item["usuario"], item["ip"], item["pais"])
        status = "enviado" if enviado else "nao enviado (Telegram nao configurado ou falhou)"
        print(f"    - {item['usuario']} @ {item['ip']}: alerta {status}")

    db.commit()
    print("[V] Dados de teste salvos com sucesso.")


if __name__ == "__main__":
    gerar_dados_teste()
