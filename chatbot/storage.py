"""Armazenamento das avaliações.

Na Vercel o disco é efêmero (só /tmp é gravável e é apagado entre execuções).
Por isso, se as variáveis do Upstash Redis (Vercel Marketplace) existirem, as
avaliações são gravadas lá; caso contrário usa-se um arquivo em /tmp, útil
apenas para testes e demonstração."""
import json
import os
import tempfile
import urllib.request
from pathlib import Path

CHAVE = "avaliacoes"
_ARQUIVO = Path(tempfile.gettempdir()) / "avaliacoes.jsonl"


def _redis_cfg():
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    return (url, token) if url and token else None


def _redis(cmd: list):
    url, token = _redis_cfg()
    req = urllib.request.Request(
        url,
        data=json.dumps(cmd).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=4) as r:
        return json.load(r)["result"]


def modo() -> str:
    return "redis" if _redis_cfg() else "arquivo_temporario"


def salvar(registro: dict) -> None:
    linha = json.dumps(registro, ensure_ascii=False)
    if _redis_cfg():
        _redis(["RPUSH", CHAVE, linha])
    else:
        with open(_ARQUIVO, "a", encoding="utf-8") as f:
            f.write(linha + "\n")


def listar(limite: int = 1000) -> list[dict]:
    if _redis_cfg():
        linhas = _redis(["LRANGE", CHAVE, str(-limite), "-1"]) or []
    elif _ARQUIVO.exists():
        linhas = _ARQUIVO.read_text(encoding="utf-8").splitlines()[-limite:]
    else:
        linhas = []
    return [json.loads(x) for x in linhas]
