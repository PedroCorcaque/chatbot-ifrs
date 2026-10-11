"""Sumarização extrativa com TextRank (Fase 4)."""
import math
import re

from .nlp import tokenizar


def _sentencas(textos: list[str]) -> list[str]:
    vistas, saida = set(), []
    for texto in textos:
        for s in re.split(r"(?<=[.!?])\s+|\n+", texto.strip()):
            s = s.strip()
            chave = s.lower().rstrip(".!? ")
            if len(s) > 3 and chave not in vistas:
                vistas.add(chave)
                saida.append(s)
    return saida


def _similaridade(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / (math.log(len(a) + 1) + math.log(len(b) + 1))


def resumir(textos: list[str], k: int = 3, d: float = 0.85, iteracoes: int = 50):
    sents = _sentencas(textos)
    if len(sents) <= k:
        return sents
    toks = [set(tokenizar(s)) for s in sents]
    n = len(sents)
    w = [[_similaridade(toks[i], toks[j]) if i != j else 0.0 for j in range(n)]
         for i in range(n)]
    soma = [sum(linha) or 1.0 for linha in w]
    score = [1.0] * n
    for _ in range(iteracoes):
        score = [
            (1 - d) + d * sum(w[j][i] / soma[j] * score[j] for j in range(n))
            for i in range(n)
        ]
    top = sorted(sorted(range(n), key=lambda i: score[i], reverse=True)[:k])
    return [sents[i] for i in top]
