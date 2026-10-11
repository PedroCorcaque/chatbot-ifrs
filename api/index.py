"""API do chatbot (Flask). Ponto de entrada da Vercel: variável `app`."""
import os
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402

from chatbot import storage  # noqa: E402
from chatbot.retriever import FAQ  # noqa: E402
from chatbot.sentiment import NaiveBayesSentimento  # noqa: E402
from chatbot.summarizer import resumir  # noqa: E402

app = Flask(__name__)
app.json.ensure_ascii = False


class RoteadorVercel:
    """Na Vercel, o vercel.json encaminha /api/<rota> para /api/index?rota=<rota>.
    Este middleware restaura o caminho original antes do Flask escolher a rota,
    o que funciona independentemente de como o runtime repassa o PATH."""

    def __init__(self, wsgi):
        self.wsgi = wsgi

    def __call__(self, environ, start_response):
        qs = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True)
        rota = qs.pop("rota", [None])[0]
        if rota is not None:
            environ["SCRIPT_NAME"] = ""
            environ["PATH_INFO"] = "/api/" + rota.strip("/")
            environ["QUERY_STRING"] = urlencode(qs, doseq=True)
        return self.wsgi(environ, start_response)


app.wsgi_app = RoteadorVercel(app.wsgi_app)

faq = FAQ()
modelo = NaiveBayesSentimento()


@app.errorhandler(Exception)
def erro_geral(e):
    """Sempre responde em JSON, para a interface mostrar a causa."""
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        if e.code == 404:
            return jsonify(erro=f"404: rota '{request.path}' não encontrada."), 404
        return jsonify(erro=f"{e.code} {e.name}"), e.code
    app.logger.exception("Erro não tratado")
    return jsonify(erro=f"Erro interno: {type(e).__name__}: {e}"), 500


def _texto(valor, maximo):
    return str(valor or "").strip()[:maximo]


@app.get("/api/saude")
def saude():
    return jsonify(status="ok", armazenamento=storage.modo(), perguntas=len(faq.itens))


@app.get("/api/sugestoes")
def sugestoes():
    return jsonify(sugestoes=faq.sugestoes(6))


@app.post("/api/chat")
def chat():
    dados = request.get_json(silent=True) or {}
    pergunta = _texto(dados.get("mensagem"), 500)
    if len(pergunta) < 2:
        return jsonify(erro="Digite uma pergunta."), 400
    r = faq.responder(pergunta)
    r["chat_id"] = uuid.uuid4().hex[:12]
    r["pergunta"] = pergunta
    return jsonify(r)


@app.post("/api/avaliacao")
def avaliacao():
    dados = request.get_json(silent=True) or {}
    frase = _texto(dados.get("frase"), 300)
    if len(frase) < 3:
        return jsonify(erro="Escreva uma frase sobre a resposta."), 400
    sentimento = modelo.prever(frase)
    registro = {
        "chat_id": _texto(dados.get("chat_id"), 20),
        "pergunta": _texto(dados.get("pergunta"), 500),
        "resposta": _texto(dados.get("resposta"), 1500),
        "categoria": _texto(dados.get("categoria"), 40),
        "frase": frase,
        "sentimento": sentimento["rotulo"],
        "confianca": sentimento["confianca"],
        "data": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    try:
        storage.salvar(registro)
        salvo = True
    except Exception:  # falha de armazenamento não deve quebrar o chat
        salvo = False
    return jsonify(sentimento=sentimento["rotulo"], confianca=sentimento["confianca"], salvo=salvo)


@app.get("/api/admin/resumo")
def resumo():
    """Pipeline integrado: classificação + sumarização TextRank."""
    token = os.environ.get("ADMIN_TOKEN")
    if not token:
        return jsonify(erro="Defina a variável de ambiente ADMIN_TOKEN."), 503
    enviado = request.headers.get("X-Admin-Token") or request.args.get("token")
    if enviado != token:
        return jsonify(erro="Não autorizado."), 401

    registros = storage.listar()
    por_sentimento = Counter(r["sentimento"] for r in registros)
    resumos = {}
    for s in ("negativo", "neutro", "positivo"):
        frases = [r["frase"] for r in registros if r["sentimento"] == s]
        resumos[s] = resumir([f if f[-1] in ".!?" else f + "." for f in frases], k=3)
    temas_negativos = Counter(
        r["categoria"] for r in registros if r["sentimento"] == "negativo"
    ).most_common(5)
    return jsonify(
        total=len(registros),
        distribuicao=dict(por_sentimento),
        resumos=resumos,
        categorias_com_mais_negativas=temas_negativos,
        armazenamento=storage.modo(),
        recentes=registros[-10:][::-1],
    )


# Uso local: na Vercel os arquivos de /public são servidos pela CDN.
@app.get("/")
def index_local():
    return send_from_directory(ROOT / "public", "index.html")


@app.get("/admin")
def admin_local():
    return send_from_directory(ROOT / "public", "admin.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
