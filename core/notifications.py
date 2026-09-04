"""Geolocalizacao de IPs e envio de alertas via Telegram."""
import html
import ipaddress
import logging

import requests

import config

logger = logging.getLogger("siem.notifications")

_IP_API_URL = "http://ip-api.com/json/{ip}"
_TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _is_privado(ip: str) -> bool:
    """Detecta IP local/privado sem depender só de startswith."""
    if ip in {"-", "127.0.0.1", "::1", "0.0.0.0", "::", "localhost"}:
        return True
    try:
        # Cobre 10.0.0.0/8, 172.16.0.0/12 (172.16-31.*), 192.168.0.0/16, fc00::/7, fe80::/10
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        # Fallback para formatos estranhos do Event 4625 (ex: "-")
        return ip.startswith(("192.168.", "10.", "172.", "fe80:", "fc", "fd"))


def obter_geolocalizacao(ip: str) -> tuple[str, str]:
    """Retorna (pais, codigo_pais) para um IP publico.

    IPs locais/privados retornam ("Local", "br") sem consultar a API
    externa, tanto por performance quanto por privacidade.
    """
    if _is_privado(ip):
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

    emoji = "\U0001F6A8" if not _is_privado(ip) else "\U0001F6E0"
    # HTML em vez de Markdown: evita quebra quando usuario/ip contem _ * ` [ ]
    usuario_h = html.escape(usuario)
    ip_h = html.escape(ip)
    pais_h = html.escape(pais)
    mensagem = (
        f"{emoji} <b>INTRUSAO DETECTADA</b>\n\n"
        f"\U0001F464 Usuario: <code>{usuario_h}</code>\n"
        f"\U0001F310 IP: <code>{ip_h}</code>\n"
        f"\U0001F4CD Pais: {pais_h}"
    )
    url = _TELEGRAM_URL.format(token=config.TELEGRAM_TOKEN)

    try:
        resposta = requests.post(
            url,
            data={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": mensagem,
                "parse_mode": "HTML",
            },
            timeout=5,
        )
        resposta.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning("Falha ao enviar alerta ao Telegram: %s", exc)
        return False