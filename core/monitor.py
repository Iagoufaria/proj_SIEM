"""Monitoramento do Log de Seguranca do Windows (Event ID 4625 - logon falho).

Esta funcionalidade depende do PowerShell/Get-WinEvent e so existe no
Windows. No projeto original, o modulo era importado incondicionalmente
e travava caso executado em outro sistema. Aqui, a checagem de
plataforma evita esse erro e permite inclusive rodar o restante do
painel (dashboard, login) em outros SOs durante o desenvolvimento.
"""
import json
import logging
import subprocess
import time

import config
from core.database import Alerta, Session
from core.notifications import enviar_alerta_telegram, obter_geolocalizacao

logger = logging.getLogger("siem.monitor")

_PS_COMANDO = (
    'Get-WinEvent -FilterHashtable @{{LogName="Security"; Id=4625; '
    'StartTime=(Get-Date).AddMinutes(-{janela})}} '
    '| Select-Object TimeCreated, @{{n="U";e={{$_.Properties[5].Value}}}}, '
    '@{{n="I";e={{$_.Properties[19].Value}}}} '
    "| ConvertTo-Json"
)


def _processar_eventos(db, eventos) -> None:
    if not isinstance(eventos, list):
        eventos = [eventos]

    for evento in eventos:
        usuario = str(evento.get("U"))
        ip = str(evento.get("I"))

        ja_existe = (
            db.query(Alerta).filter_by(usuario=usuario, ip_origem=ip).first()
            is not None
        )
        if ja_existe:
            continue

        pais, codigo = obter_geolocalizacao(ip)
        novo_alerta = Alerta(usuario=usuario, ip_origem=ip, pais=pais, codigo_pais=codigo)
        db.add(novo_alerta)
        db.commit()
        enviar_alerta_telegram(usuario, ip, pais)
        logger.info("Novo alerta: usuario=%s ip=%s pais=%s", usuario, ip, pais)


def monitorar_windows() -> None:
    """Loop infinito que varre o Log de Seguranca do Windows periodicamente."""
    if not config.IS_WINDOWS:
        logger.warning(
            "Monitoramento do Log de Seguranca do Windows indisponivel: "
            "este recurso depende do PowerShell/Get-WinEvent e so funciona "
            "no Windows. O painel continuara funcionando normalmente, mas "
            "sem captura automatica de novos eventos neste sistema."
        )
        return

    comando = _PS_COMANDO.format(janela=config.SCAN_WINDOW_MINUTES)

    while True:
        try:
            db = Session()
            processo = subprocess.run(
                ["powershell", "-NoProfile", "-Command", comando],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if processo.returncode != 0:
                logger.warning("PowerShell retornou erro: %s", processo.stderr.strip())
            elif processo.stdout.strip():
                eventos = json.loads(processo.stdout)
                _processar_eventos(db, eventos)
        except subprocess.TimeoutExpired:
            logger.warning("Consulta ao Log de Seguranca excedeu o tempo limite.")
        except json.JSONDecodeError as exc:
            logger.warning("Saida do PowerShell nao era um JSON valido: %s", exc)
        except Exception:
            # Ultima linha de defesa: o loop de monitoramento roda em uma
            # thread em background e NUNCA pode derrubar o processo por
            # causa de um erro inesperado - mas o erro fica registrado
            # no log em vez de ser silenciosamente ignorado.
            logger.exception("Erro inesperado no loop de monitoramento.")
        finally:
            Session.remove()

        time.sleep(config.SCAN_INTERVAL_SECONDS)
