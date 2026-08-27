"""SIEM TCC - painel administrativo de monitoramento de intrusoes.

Ponto de entrada da aplicacao: sobe um servidor Flask local, abre uma
janela desktop (pywebview) apontando para ele, e inicia em segundo
plano o monitoramento do Log de Seguranca do Windows.
"""
import csv
import logging
import threading
from io import StringIO

from flask import Flask, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import CSRFProtect
from sqlalchemy import func

import config
from core.auth import autenticar, existe_algum_usuario, login_manager
from core.database import Alerta, Session, init_db
from core.monitor import monitorar_windows

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("siem.app")

app = Flask(
    __name__,
    template_folder=str(config.TEMPLATE_DIR),
    static_folder=str(config.STATIC_DIR),
)
app.config["SECRET_KEY"] = config.SECRET_KEY

login_manager.init_app(app)
csrf = CSRFProtect(app)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if not existe_algum_usuario():
        flash(
            "Nenhum usuario cadastrado ainda. Rode "
            "'python scripts/criar_usuario.py' para criar o administrador.",
            "warning",
        )

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")

        usuario = autenticar(username, senha)
        if usuario is None:
            flash("Usuario ou senha invalidos.", "danger")
            return render_template("login.html"), 401

        login_user(usuario)
        logger.info("Login bem-sucedido: %s", username)
        proxima = request.args.get("next")
        return redirect(proxima or url_for("index"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    db = Session()
    alertas = db.query(Alerta).order_by(Alerta.id.desc()).limit(20).all()
    stats_ip = db.query(Alerta.ip_origem, func.count(Alerta.id)).group_by(Alerta.ip_origem).all()
    ips_bloqueados = [ip for ip, total in stats_ip if total > 3]
    stats_usuario = db.query(Alerta.usuario, func.count(Alerta.id)).group_by(Alerta.usuario).all()

    return render_template(
        "dashboard.html",
        alertas=alertas,
        labels=[s[0] for s in stats_usuario],
        valores=[s[1] for s in stats_usuario],
        ips_bloqueados=ips_bloqueados,
        total_eventos=sum(s[1] for s in stats_usuario) if stats_usuario else 0,
    )


@app.route("/exportar")
@login_required
def exportar_csv():
    db = Session()
    alertas = db.query(Alerta).order_by(Alerta.id.desc()).all()

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ID", "Data/Hora", "Usuario", "IP Origem", "Pais", "Mensagem"])
    for alerta in alertas:
        writer.writerow(
            [alerta.id, alerta.data_hora, alerta.usuario, alerta.ip_origem, alerta.pais, alerta.mensagem_bruta]
        )

    resposta = make_response(buffer.getvalue())
    resposta.headers["Content-Disposition"] = "attachment; filename=relatorio_siem.csv"
    resposta.headers["Content-Type"] = "text/csv; charset=utf-8"
    return resposta


def iniciar_servidor_flask() -> None:
    init_db()
    threading.Thread(target=monitorar_windows, daemon=True).start()
    app.run(host="127.0.0.1", port=config.SIEM_PORT, debug=False, use_reloader=False)


def _abrir_janela_desktop() -> None:
    """Importa o pywebview so aqui dentro, para que o resto do app
    (rotas Flask, testes) continue funcionando em maquinas onde o
    pywebview/GTK nao estao instalados (ex.: servidores Linux, CI)."""
    import webview

    # Por padrao o pywebview BLOQUEIA downloads de arquivos dentro da
    # janela (protecao de seguranca da biblioteca). Sem isso, o botao
    # "Exportar" do dashboard simplesmente nao faz nada.
    webview.settings["ALLOW_DOWNLOADS"] = True

    webview.create_window(
        title="SIEM Cyber Security - Painel Administrativo",
        url=f"http://127.0.0.1:{config.SIEM_PORT}",
        width=1280,
        height=800,
        min_size=(1024, 640),
        resizable=True,
    )
    webview.start()


if __name__ == "__main__":
    t_flask = threading.Thread(target=iniciar_servidor_flask, daemon=True)
    t_flask.start()
    _abrir_janela_desktop()
