"""Classificador de sentimento: Naive Bayes multinomial com suavização de
Laplace, treinado na inicialização com data/sentimento_treino.json."""
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from .nlp import tokenizar_sentimento

DATA = Path(__file__).resolve().parent.parent / "data" / "sentimento_treino.json"
CLASSES = ("negativo", "neutro", "positivo")


class NaiveBayesSentimento:
    def __init__(self, caminho: Path = DATA):
        with open(caminho, encoding="utf-8") as f:
            amostras = json.load(f)
        self.contagem = defaultdict(Counter)
        self.docs = Counter()
        for a in amostras:
            self.docs[a["rotulo"]] += 1
            self.contagem[a["rotulo"]].update(tokenizar_sentimento(a["texto"]))
        self.vocab = {t for c in self.contagem.values() for t in c}
        self.total = {c: sum(self.contagem[c].values()) for c in CLASSES}
        self.n_docs = sum(self.docs.values())

    def prever(self, texto: str) -> dict:
        tokens = [t for t in tokenizar_sentimento(texto) if t in self.vocab]
        if not tokens:
            return {"rotulo": "neutro", "confianca": 0.34}
        log_p = {}
        for c in CLASSES:
            lp = math.log(self.docs[c] / self.n_docs)
            for t in tokens:
                lp += math.log(
                    (self.contagem[c][t] + 1) / (self.total[c] + len(self.vocab))
                )
            log_p[c] = lp
        m = max(log_p.values())
        exp = {c: math.exp(v - m) for c, v in log_p.items()}
        z = sum(exp.values())
        probs = {c: v / z for c, v in exp.items()}
        melhor = max(probs, key=probs.get)
        return {"rotulo": melhor, "confianca": round(probs[melhor], 3)}
