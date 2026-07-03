"""Geolocalizacao de IPs e envio de alertas via Telegram."""
import logging

import requests

import config

logger = logging.getLogger("siem.notifications")

_IP_API_URL = "http://ip-api.com/json/{ip}"
_TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"


def obter_geolocalizacao(ip: str) -> tuple[str, str]:
    """Retorna (pais, codigo_pais) para um IP publico.

    IPs locais/privados retornam ("Local", "br") sem consultar a API
    externa, tanto por performance quanto por privacidade.
    """
    if ip in {"-", "127.0.0.1", "::1"} or ip.startswith(("192.168.", "10.", "172.16.")):
        return "Local", "br"

    try:
        resposta = requests.get(_IP_API_URL.format(ip=ip), timeout=5)
        resposta.raise_for_status()
        dados = resposta.json()
        if dados.get("status") == "success":
            return dados.get("country", "Desconhecido"), dados.get("countryCode", "un").lower()
    except requests.RequestException as exc:
        logger.warning("Falha ao consultar geolocalizacao para %s: %s", ip, exc)
    except ValueError as exc:
        logger.warning("Resposta invalida da API de geolocalizacao para %s: %s", ip, exc)

    return "Desconhecido", "un"


def enviar_alerta_telegram(usuario: str, ip: str, pais: str) -> bool:
    """Envia um alerta de intrusao para o Telegram, se configurado.

    Retorna True se o envio foi bem-sucedido, False caso contrario
    (inclusive quando o Telegram nao foi configurado no .env).
    """
    if not config.TELEGRAM_ENABLED:
        logger.info("Telegram nao configurado (.env) - alerta nao enviado.")
        return False

    emoji = "\U0001F6A8" if ip != "127.0.0.1" else "\U0001F6E0"
    mensagem = (
        f"{emoji} *INTRUSAO DETECTADA*\n\n"
        f"\U0001F464 Usuario: `{usuario}`\n"
        f"\U0001F310 IP: `{ip}`\n"
        f"\U0001F4CD Pais: {pais}"
    )
    url = _TELEGRAM_URL.format(token=config.TELEGRAM_TOKEN)

    try:
        resposta = requests.post(
            url,
            data={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": mensagem,
                "parse_mode": "Markdown",
            },
            timeout=5,
        )
        resposta.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning("Falha ao enviar alerta ao Telegram: %s", exc)
        return False
