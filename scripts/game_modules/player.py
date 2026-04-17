"""Classe do personagem controlado no labirinto."""

import math
from collections import deque

import pygame as pg


class Personagem:
    """Representa o robo: rotacao, movimento e renderizacao."""

    def __init__(self, caminho_imagem, x, y, larguraP, alturaP):
        self.imagem_original = pg.image.load(caminho_imagem).convert_alpha()
        self.imagem_original = pg.transform.scale(self.imagem_original, (larguraP, alturaP))
        self.imagem = self.imagem_original
        self.x = x
        self.y = y
        self.movimento = deque()
        self.velocidade = 15
        self.em_movimento = False
        self.distancia_restante = 0
        self.angulo_atual = 0
        self.angulo_desejado = 0
        self.velocidade_rotacao = 20
        self.girando = False

    def girar_para(self, graus):
        if not self.girando:
            self.angulo_desejado = (self.angulo_atual + graus) % 360
            self.girando = True

    def desenhar(self, tela):
        rect = self.imagem.get_rect(center=(self.x, self.y))
        tela.blit(self.imagem, rect.topleft)

    def iniciar_movimento(self, distancia):
        if not self.em_movimento:
            self.distancia_restante = distancia
            self.em_movimento = True

    def atualizar_movimento(self):
        if self.em_movimento:
            passo = min(self.velocidade, self.distancia_restante)
            dx = math.cos(math.radians(self.angulo_atual)) * passo
            dy = -math.sin(math.radians(self.angulo_atual)) * passo
            self.x += dx
            self.y += dy
            self.distancia_restante -= passo
            if self.distancia_restante <= 0:
                self.em_movimento = False

    def atualizar_rotacao(self):
        if self.girando:
            diff = (self.angulo_desejado - self.angulo_atual) % 360
            if diff > 180:
                diff -= 360
            passo = self.velocidade_rotacao if abs(diff) >= self.velocidade_rotacao else abs(diff)
            if diff < 0:
                self.angulo_atual -= passo
            else:
                self.angulo_atual += passo
            self.angulo_atual %= 360
            if round(self.angulo_atual) == round(self.angulo_desejado):
                self.angulo_atual = self.angulo_desejado
                self.girando = False
            self.imagem = pg.transform.rotate(self.imagem_original, self.angulo_atual)

    def pode_mover_frente(self, labirinto, tamanho_celula):
        coluna = int(self.x // tamanho_celula)
        linha = int(self.y // tamanho_celula)
        if linha < 0 or linha >= labirinto.linhas or coluna < 0 or coluna >= labirinto.colunas:
            return False
        celula = labirinto.labirinto[linha][coluna]
        if self.angulo_atual == 0:
            return not celula.paredes["direita"]
        if self.angulo_atual == 90:
            return not celula.paredes["cima"]
        if self.angulo_atual == 180:
            return not celula.paredes["esquerda"]
        if self.angulo_atual == 270:
            return not celula.paredes["baixo"]
        return False
