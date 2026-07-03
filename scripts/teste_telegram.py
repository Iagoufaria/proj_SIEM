"""Envia uma mensagem de teste para o Telegram usando as credenciais do .env.

IMPORTANTE: as credenciais NAO ficam mais escritas neste arquivo.
Configure TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no seu ".env" (veja .env.example).
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

import config


def disparar_teste_manual() -> None:
    if not config.TELEGRAM_ENABLED:
        print("[!] TELEGRAM_TOKEN e/ou TELEGRAM_CHAT_ID nao configurados no .env.")
        print("    Copie .env.example para .env e preencha os valores antes de testar.")
        sys.exit(1)

    print("[*] Iniciando teste de envio para o Telegram...")

    usuario = "Teste_TCC"
    ip = "1.1.1.1"
    pais = "Australia"

    mensagem = (
        "\U0001F9EA *TESTE DE INTEGRACAO SIEM*\n\n"
        "O sistema de notificacoes esta operando corretamente.\n"
        f"\U0001F464 *Usuario:* `{usuario}`\n"
        f"\U0001F310 *IP Teste:* `{ip}`\n"
        f"\U0001F4CD *Pais:* {pais}\n"
        f"\u23F0 *Enviado em:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )

    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
    }

    try:
        resposta = requests.post(url, data=payload, timeout=10)
        if resposta.status_code == 200:
            print("[V] Mensagem enviada com sucesso! Verifique seu Telegram.")
        else:
            print(f"[-] Falha no envio. Codigo: {resposta.status_code}")
            print(f"[-] Resposta do Telegram: {resposta.text}")
    except requests.RequestException as exc:
        print(f"[-] Erro de conexao: {exc}")


if __name__ == "__main__":
    disparar_teste_manual()
