"""Modelos e utilitarios do labirinto."""

import random

import pygame as pg


class Celula:
    def __init__(self, linha, coluna):
        self.linha = linha
        self.coluna = coluna
        self.visitada = False
        self.paredes = {
            "cima": True,
            "baixo": True,
            "esquerda": True,
            "direita": True,
        }


class GeradorLabirinto:
    """Gera e desenha um labirinto usando DFS com backtracking."""

    def __init__(self, linhas, colunas):
        self.linhas = linhas
        self.colunas = colunas
        self.labirinto = [[Celula(l, c) for c in range(colunas)] for l in range(linhas)]

    def pegar_vizinhos(self, celula):
        vizinhos = []
        l, c = celula.linha, celula.coluna
        if l > 0:
            cima = self.labirinto[l - 1][c]
            if not cima.visitada:
                vizinhos.append(("cima", cima))
        if l < self.linhas - 1:
            baixo = self.labirinto[l + 1][c]
            if not baixo.visitada:
                vizinhos.append(("baixo", baixo))
        if c > 0:
            esquerda = self.labirinto[l][c - 1]
            if not esquerda.visitada:
                vizinhos.append(("esquerda", esquerda))
        if c < self.colunas - 1:
            direita = self.labirinto[l][c + 1]
            if not direita.visitada:
                vizinhos.append(("direita", direita))
        return vizinhos

    def remover_parede(self, atual, vizinho, direcao):
        opostos = {
            "cima": "baixo",
            "baixo": "cima",
            "esquerda": "direita",
            "direita": "esquerda",
        }
        atual.paredes[direcao] = False
        vizinho.paredes[opostos[direcao]] = False

    def encontrar_celula_distante(self, min_distancia):
        inicio = self.labirinto[0][0]
        max_dist = 0
        mais_distante = inicio
        for linha in self.labirinto:
            for celula in linha:
                if celula.visitada:
                    dist = abs(celula.linha - inicio.linha) + abs(celula.coluna - inicio.coluna)
                    if dist >= min_distancia and dist > max_dist:
                        max_dist = dist
                        mais_distante = celula
        return mais_distante

    def gerar(self):
        pilha = []
        atual = self.labirinto[0][0]
        atual.visitada = True
        while True:
            vizinhos = self.pegar_vizinhos(atual)
            if vizinhos:
                direcao, proxima = random.choice(vizinhos)
                self.remover_parede(atual, proxima, direcao)
                pilha.append(atual)
                proxima.visitada = True
                atual = proxima
                self.ultima_celula = atual
            elif pilha:
                atual = pilha.pop()
            else:
                break
        self.ultima_celula = self.encontrar_celula_distante(min_distancia=8)

    def desenhar(self, tela, tamanho_celula, desenhar_linhas_guia=True, sprite_parede=None):
        for l in range(self.linhas):
            for c in range(self.colunas):
                x = c * tamanho_celula
                y = l * tamanho_celula
                celula = self.labirinto[l][c]

                if celula.paredes["cima"]:
                    pg.draw.line(tela, (0, 0, 0), (x, y), (x + tamanho_celula, y), 4)
                if celula.paredes["baixo"]:
                    pg.draw.line(
                        tela,
                        (0, 0, 0),
                        (x, y + tamanho_celula),
                        (x + tamanho_celula, y + tamanho_celula),
                        4,
                    )
                if celula.paredes["esquerda"]:
                    pg.draw.line(tela, (0, 0, 0), (x, y), (x, y + tamanho_celula), 4)
                if celula.paredes["direita"]:
                    pg.draw.line(
                        tela,
                        (0, 0, 0),
                        (x + tamanho_celula, y),
                        (x + tamanho_celula, y + tamanho_celula),
                        4,
                    )

                if not desenhar_linhas_guia:
                    continue

                centro_x = x + tamanho_celula // 2
                centro_y = y + tamanho_celula // 2
                faixa_tamanho = int(tamanho_celula * 0.5)
                cor_faixa = (255, 255, 0)

                conexoes = []
                if l > 0 and not celula.paredes["cima"]:
                    conexoes.append("cima")
                if l < self.linhas - 1 and not celula.paredes["baixo"]:
                    conexoes.append("baixo")
                if c > 0 and not celula.paredes["esquerda"]:
                    conexoes.append("esquerda")
                if c < self.colunas - 1 and not celula.paredes["direita"]:
                    conexoes.append("direita")

                if len(conexoes) == 1:
                    direcao = conexoes[0]
                    if direcao in ["esquerda", "direita"]:
                        pg.draw.line(
                            tela,
                            cor_faixa,
                            (centro_x - faixa_tamanho // 2, centro_y),
                            (centro_x + faixa_tamanho // 2, centro_y),
                            2,
                        )
                    else:
                        pg.draw.line(
                            tela,
                            cor_faixa,
                            (centro_x, centro_y - faixa_tamanho // 2),
                            (centro_x, centro_y + faixa_tamanho // 2),
                            2,
                        )
                elif len(conexoes) == 2:
                    if set(conexoes) == {"esquerda", "direita"}:
                        pg.draw.line(
                            tela,
                            cor_faixa,
                            (centro_x - faixa_tamanho // 2, centro_y),
                            (centro_x + faixa_tamanho // 2, centro_y),
                            2,
                        )
                    elif set(conexoes) == {"cima", "baixo"}:
                        pg.draw.line(
                            tela,
                            cor_faixa,
                            (centro_x, centro_y - faixa_tamanho // 2),
                            (centro_x, centro_y + faixa_tamanho // 2),
                            2,
                        )
                    else:
                        self._desenhar_curva(tela, conexoes, centro_x, centro_y, faixa_tamanho, cor_faixa)
                elif len(conexoes) > 2:
                    if "esquerda" in conexoes or "direita" in conexoes:
                        pg.draw.line(
                            tela,
                            cor_faixa,
                            (centro_x - faixa_tamanho // 2, centro_y),
                            (centro_x + faixa_tamanho // 2, centro_y),
                            2,
                        )
                    elif "cima" in conexoes or "baixo" in conexoes:
                        pg.draw.line(
                            tela,
                            cor_faixa,
                            (centro_x, centro_y - faixa_tamanho // 2),
                            (centro_x, centro_y + faixa_tamanho // 2),
                            2,
                        )

        if hasattr(self, "parede_sprites") and sprite_parede is not None:
            for l, c in self.parede_sprites:
                x = c * tamanho_celula
                y = l * tamanho_celula
                tela.blit(sprite_parede, (x, y))

    def _desenhar_curva(self, tela, conexoes, centro_x, centro_y, faixa_tamanho, cor_faixa):
        if set(conexoes) == {"cima", "direita"}:
            pg.draw.line(
                tela,
                cor_faixa,
                (centro_x, centro_y - faixa_tamanho // 2),
                (centro_x, centro_y),
                2,
            )
            pg.draw.line(
                tela,
                cor_faixa,
                (centro_x, centro_y),
                (centro_x + faixa_tamanho // 2, centro_y),
                2,
            )
        elif set(conexoes) == {"cima", "esquerda"}:
            pg.draw.line(
                tela,
                cor_faixa,
                (centro_x, centro_y - faixa_tamanho // 2),
                (centro_x, centro_y),
                2,
            )
            pg.draw.line(
                tela,
                cor_faixa,
                (centro_x, centro_y),
                (centro_x - faixa_tamanho // 2, centro_y),
                2,
            )
        elif set(conexoes) == {"baixo", "direita"}:
            pg.draw.line(
                tela,
                cor_faixa,
                (centro_x, centro_y + faixa_tamanho // 2),
                (centro_x, centro_y),
                2,
            )
            pg.draw.line(
                tela,
                cor_faixa,
                (centro_x, centro_y),
                (centro_x + faixa_tamanho // 2, centro_y),
                2,
            )
        elif set(conexoes) == {"baixo", "esquerda"}:
            pg.draw.line(
                tela,
                cor_faixa,
                (centro_x, centro_y + faixa_tamanho // 2),
                (centro_x, centro_y),
                2,
            )
            pg.draw.line(
                tela,
                cor_faixa,
                (centro_x, centro_y),
                (centro_x - faixa_tamanho // 2, centro_y),
                2,
            )


def escolher_objetivo_aleatorio(linhas, colunas):
    cols_alvo = [c for c in (3, 4) if c < colunas]
    opcoes = [(l, c) for l in range(linhas) for c in cols_alvo]
    if opcoes:
        return random.choice(opcoes)
    return linhas - 1, colunas - 1


def abrir_todas_as_paredes(labirinto):
    for linha in labirinto.labirinto:
        for celula in linha:
            celula.paredes = {
                "cima": False,
                "baixo": False,
                "esquerda": False,
                "direita": False,
            }


def configurar_modo_facil(labirinto):
    abrir_todas_as_paredes(labirinto)
    meio = labirinto.colunas // 2
    linhas_parede = [0, 1, 2, 3]

    for l in linhas_parede:
        labirinto.labirinto[l][meio].paredes = {
            "cima": True,
            "baixo": True,
            "esquerda": True,
            "direita": True,
        }

    labirinto.parede_sprites = [(l, meio) for l in linhas_parede]
    return escolher_objetivo_aleatorio(labirinto.linhas, labirinto.colunas)


def preparar_labirinto(valores):
    linhas, colunas, tamanho_celula = valores[:3]
    tag_dificuldade = valores[3] if len(valores) == 4 else None

    labirinto = GeradorLabirinto(linhas, colunas)
    modo_muito_facil = tag_dificuldade == "muito_facil"
    is_facil = tag_dificuldade == "facil"

    if modo_muito_facil:
        abrir_todas_as_paredes(labirinto)
        objetivo_linha, objetivo_coluna = escolher_objetivo_aleatorio(linhas, colunas)
    elif is_facil:
        objetivo_linha, objetivo_coluna = configurar_modo_facil(labirinto)
    else:
        labirinto.gerar()
        objetivo_linha = labirinto.ultima_celula.linha
        objetivo_coluna = labirinto.ultima_celula.coluna

    return {
        "linhas": linhas,
        "colunas": colunas,
        "tamanho_celula": tamanho_celula,
        "labirinto": labirinto,
        "modo_muito_facil": modo_muito_facil,
        "is_facil": is_facil,
        "objetivo_linha": objetivo_linha,
        "objetivo_coluna": objetivo_coluna,
    }
