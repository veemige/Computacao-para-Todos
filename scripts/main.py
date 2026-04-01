"""
Projeto Computação para Todos — demonstração lúdica e interativa de algoritmos.

Este arquivo contém o jogo principal com geração de labirinto, detecção de cores
via OpenCV, renderização com Pygame e uma UI inicial em Tkinter para escolher
modo e dificuldade. O objetivo é manter o código acessível e bem comentado, sem
alterar o comportamento atual.
"""
#uashduasasdasdas
# Demonstração de algoritmos de forma lúdica, forma interativa
import numpy as np
import pygame as pg
import cv2
import random
import sys
import math
import time
import tkinter as tk
from collections import deque, Counter
import os
import DefMQTT as mqtt

# ==============================
# Configurações e Constantes
# ==============================
HEIGHT = 500
WIDTH = 700
FPS = 60

# Cor de fundo da área do labirinto
COR_TELA = (100, 103, 97)

# Mostrar janela da câmera (pode desativar se interferir no Pygame)
SHOW_CAMERA = True

# Modo de entrada da câmera: "qr" ou "color"
CAMERA_INPUT_MODE = "qr"

# Configuração fixa de detecção (HSV, ROI, filtros) com parâmetros robustos
HSV_RANGES = {
    # Ajustados para cores fracas/pastel; amarelo restringido em H e com S/V moderados
    "amarelo": {"lower": [22, 40, 130], "upper": [36, 255, 255]},
    "azul": {"lower": [95, 20, 120], "upper": [130, 255, 255]},
    "verde": {"lower": [35, 20, 120], "upper": [90, 255, 255]},
}

# Faixa de pele em HSV para excluir da detecção do amarelo (evita falsos positivos)
SKIN_RANGE = {"lower": [0, 48, 80], "upper": [20, 255, 255]}
ROI_W, ROI_H = 220, 220
BLUR = 5           # ímpar >=3; 0/1 desativa
ERODE_IT = 1
DILATE_IT = 1
# Histerese por área: ON para disparar, OFF para sumir
AREA_MIN_ON = 2600
AREA_MIN_OFF = 1800
# Estabilidade de decisão
DETECT_RECENT_LEN = 7
DETECT_MAJORITY_MIN = 4
DETECT_REFRACTORY_SEC = 0.7
DETECT_EVERY_N = 2  # roda detecção a cada N frames

QR_COMMAND_MAP = {
    "LEFT": "LEFT",
    "ESQUERDA": "LEFT",
    "L": "LEFT",
    "RIGHT": "RIGHT",
    "DIREITA": "RIGHT",
    "R": "RIGHT",
    "SPACE": "SPACE",
    "FRENTE": "SPACE",
    "FORWARD": "SPACE",
    "GO": "SPACE",
    "UP": "SPACE",
    "S": "SPACE",
}

def escolher_dificuldade_tkinter():
    """Abre uma pequena janela Tkinter para selecionar dificuldade e tipo de movimento.

    Retorna:
        tuple: (valores, tipo_movimento)
            - valores: (linhas, colunas, tamanho_celula[, tag])
            - tipo_movimento: "comando" ou "direto"
    """
    dificuldade = {"valores": None, "tipo_movimento": None}

    def selecionar(valores, tipo_movimento):
        dificuldade["valores"] = valores
        dificuldade["tipo_movimento"] = tipo_movimento
        root.destroy()

    root = tk.Tk()
    root.title("Configurações do Jogo")

    tk.Label(root, text="Escolha a Dificuldade:", font=("Arial", 16)).pack(pady=10)

    dificuldades = [
        ("Muito Fácil", "green", (5, 5, 120, "muito_facil")),
        ("Fácil", "lightgreen", (5, 5, 120, "facil")),
        ("Médio", "khaki", (5, 5, 120)),
        ("Difícil", "salmon", (7, 7, 80)),
        ("Muito Difícil", "red", (10, 10, 60)),
    ]

    dificuldade_var = tk.StringVar()
    for texto, cor, valores in dificuldades:
        tk.Radiobutton(root, text=texto, bg=cor, variable=dificuldade_var,
                       value=str(valores), width=20, indicatoron=0).pack(pady=2)

    tk.Label(root, text="Tipo de Movimento:", font=("Arial", 16)).pack(pady=10)

    tipo_movimento_var = tk.StringVar(value="comando")
    tk.Radiobutton(root, text="Movimento por Comando (⌨️ ENTER)", variable=tipo_movimento_var, value="comando").pack()
    tk.Radiobutton(root, text="Movimento Imediato (⬅️ ➡️ ⬇️)", variable=tipo_movimento_var, value="direto").pack()

    def confirmar():
        if dificuldade_var.get():
            valores = eval(dificuldade_var.get())
            tipo = tipo_movimento_var.get()
            selecionar(valores, tipo)

    tk.Button(root, text="Confirmar", command=confirmar, bg="gray").pack(pady=20)

    root.mainloop()
    return dificuldade["valores"], dificuldade["tipo_movimento"]


def detectar_cor(camera):
    """Detecta uma das cores configuradas no centro do frame da câmera, com filtros.

    Usa blur e morfologia (erode/dilate) e valida por área mínima.
    """
    ret, frame = camera.read()
    if not ret:
        return None, None

    altura, largura, _ = frame.shape
    w = int(ROI_W)
    h = int(ROI_H)

    # Calcula o centro da imagem
    centro_x = largura // 2
    centro_y = altura // 2

    # Define a área de interesse (ROI)
    x1 = centro_x - w // 2
    y1 = centro_y - h // 2
    x2 = centro_x + w // 2
    y2 = centro_y + h // 2

    roi = frame[y1:y2, x1:x2]
    # Pré-processamento
    proc = roi.copy()
    blur_k = int(BLUR)
    if blur_k and blur_k % 2 == 1 and blur_k >= 3:
        proc = cv2.GaussianBlur(proc, (blur_k, blur_k), 0)
    hsv = cv2.cvtColor(proc, cv2.COLOR_BGR2HSV)

    erode_it = int(ERODE_IT)
    dilate_it = int(DILATE_IT)

    # Máscara de pele para excluir da detecção de amarelo
    lower_skin = np.array(SKIN_RANGE.get("lower", [0, 0, 0]))
    upper_skin = np.array(SKIN_RANGE.get("upper", [0, 0, 0]))
    skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

    best_cor = None
    best_area = 0
    for cor, rng in HSV_RANGES.items():
        lower_np = np.array(rng.get("lower", [0, 0, 0]))
        upper_np = np.array(rng.get("upper", [179, 255, 255]))

        mask = cv2.inRange(hsv, lower_np, upper_np)
        # Exclui tons de pele da máscara do amarelo
        if cor == "amarelo":
            mask = cv2.bitwise_and(mask, cv2.bitwise_not(skin_mask))
        if erode_it > 0:
            mask = cv2.erode(mask, None, iterations=erode_it)
        if dilate_it > 0:
            mask = cv2.dilate(mask, None, iterations=dilate_it)

        contornos, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if contornos:
            area = cv2.contourArea(max(contornos, key=cv2.contourArea))
            if area > best_area:
                best_area = area
                best_cor = cor

    # Aplica limiar de histerese para evitar flicker
    if best_area >= AREA_MIN_ON:
        cor_final = best_cor
    elif best_area >= AREA_MIN_OFF and best_cor is not None:
        cor_final = best_cor  # mantém enquanto acima de OFF
    else:
        cor_final = None

    # Desenha ROI para visualização
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
    return cor_final, frame

    # Desenha um retângulo na imagem original (só visual)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

    return None, frame


def normalizar_qr(data):
    """Converte o texto do QR em um comando canônico do jogo."""
    if not data:
        return None
    return QR_COMMAND_MAP.get(data.strip().upper())


def detectar_qr(camera, qr_detector):
    """Detecta QR code e retorna (comando, frame, origem_lida)."""
    ret, frame = camera.read()
    if not ret:
        return None, None, None

    try:
        ok, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)
    except Exception:
        ok = False
        decoded_info, points = [], None

    if ok and decoded_info:
        for idx, data in enumerate(decoded_info):
            comando = normalizar_qr(data)
            if not comando:
                continue

            origem = data.strip()
            if points is not None and len(points) > idx:
                pts = np.int32(points[idx]).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 255, 255), 3)
                x, y = pts[0][0]
                cv2.putText(frame, origem, (x, max(30, y - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            return comando, frame, origem

    data, points, _ = qr_detector.detectAndDecode(frame)
    comando = normalizar_qr(data)
    origem = data.strip() if comando and data else None
    if comando and points is not None:
        pts = np.int32(points).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], True, (0, 255, 255), 3)
        x, y = pts[0][0]
        cv2.putText(frame, origem, (x, max(30, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    return comando, frame, origem


def detectar_comando_camera(camera, qr_detector=None):
    """Abstrai a origem do comando da câmera."""
    if CAMERA_INPUT_MODE == "qr":
        return detectar_qr(camera, qr_detector)

    cor_detectada, frame = detectar_cor(camera)
    if cor_detectada == "amarelo":
        return "LEFT", frame, cor_detectada
    if cor_detectada == "azul":
        return "RIGHT", frame, cor_detectada
    if cor_detectada == "verde":
        return "SPACE", frame, cor_detectada
    return None, frame, None


def descrever_comando_camera(comando, origem):
    """Gera a mensagem mostrada no terminal lateral."""
    origem_txt = (origem or comando or "CAMERA").upper()
    if comando == "LEFT":
        return f"Detectado: {origem_txt} -> ESQUERDA"
    if comando == "RIGHT":
        return f"Detectado: {origem_txt} -> DIREITA"
    if comando == "SPACE":
        return f"Detectado: {origem_txt} -> FRENTE"
    return f"Detectado: {origem_txt}"


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
        """Retorna vizinhos não visitados com a direção relativa."""
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
        """Remove pared(es) entre duas células adjacentes."""
        opostos = {
            "cima": "baixo",
            "baixo": "cima",
            "esquerda": "direita",
            "direita": "esquerda"
        }

        atual.paredes[direcao] = False
        vizinho.paredes[opostos[direcao]] = False

    def encontrar_celula_distante(self, min_distancia):
        """Seleciona uma célula distante o suficiente da origem (0,0)."""
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
        """Gera o labirinto via DFS/backtracking e define a última célula-alvo."""
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
        """Desenha as paredes e, opcionalmente, linhas guia amarelas.

        No modo fácil pode receber um sprite para paredes especiais.
        """
        for l in range(self.linhas):
            for c in range(self.colunas):
                x = c * tamanho_celula
                y = l * tamanho_celula
                celula = self.labirinto[l][c]

                # Desenhar paredes
                if celula.paredes["cima"]:
                    pg.draw.line(tela, (0, 0, 0), (x, y), (x + tamanho_celula, y), 4)
                if celula.paredes["baixo"]:
                    pg.draw.line(tela, (0, 0, 0), (x, y + tamanho_celula), (x + tamanho_celula, y + tamanho_celula), 4)
                if celula.paredes["esquerda"]:
                    pg.draw.line(tela, (0, 0, 0), (x, y), (x, y + tamanho_celula), 4)
                if celula.paredes["direita"]:
                    pg.draw.line(tela, (0, 0, 0), (x + tamanho_celula, y), (x + tamanho_celula, y + tamanho_celula), 4)

                if not desenhar_linhas_guia:
                    continue  # Pula o desenho das linhas amarelas

                centro_x = x + tamanho_celula // 2
                centro_y = y + tamanho_celula // 2
                faixa_tamanho = int(tamanho_celula * 0.5)
                cor_faixa = (255, 255, 0)

                # Verifica conexões (sem parede)
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
                        pg.draw.line(tela, cor_faixa,
                                    (centro_x - faixa_tamanho // 2, centro_y),
                                    (centro_x + faixa_tamanho // 2, centro_y), 2)
                    else:
                        pg.draw.line(tela, cor_faixa,
                                    (centro_x, centro_y - faixa_tamanho // 2),
                                    (centro_x, centro_y + faixa_tamanho // 2), 2)

                elif len(conexoes) == 2:
                    # Cruzamento em linha reta
                    if set(conexoes) == {"esquerda", "direita"}:
                        pg.draw.line(tela, cor_faixa,
                                    (centro_x - faixa_tamanho // 2, centro_y),
                                    (centro_x + faixa_tamanho // 2, centro_y), 2)
                    elif set(conexoes) == {"cima", "baixo"}:
                        pg.draw.line(tela, cor_faixa,
                                    (centro_x, centro_y - faixa_tamanho // 2),
                                    (centro_x, centro_y + faixa_tamanho // 2), 2)
                    else:
                        # Desenho do "L" com orientação baseada nas direções
                        if set(conexoes) == {"cima", "direita"}:
                            pg.draw.line(tela, cor_faixa,
                                        (centro_x, centro_y - faixa_tamanho // 2),
                                        (centro_x, centro_y), 2)
                            pg.draw.line(tela, cor_faixa,
                                        (centro_x, centro_y),
                                        (centro_x + faixa_tamanho // 2, centro_y), 2)

                        elif set(conexoes) == {"cima", "esquerda"}:
                            pg.draw.line(tela, cor_faixa,
                                        (centro_x, centro_y - faixa_tamanho // 2),
                                        (centro_x, centro_y), 2)
                            pg.draw.line(tela, cor_faixa,
                                        (centro_x, centro_y),
                                        (centro_x - faixa_tamanho // 2, centro_y), 2)

                        elif set(conexoes) == {"baixo", "direita"}:
                            pg.draw.line(tela, cor_faixa,
                                        (centro_x, centro_y + faixa_tamanho // 2),
                                        (centro_x, centro_y), 2)
                            pg.draw.line(tela, cor_faixa,
                                        (centro_x, centro_y),
                                        (centro_x + faixa_tamanho // 2, centro_y), 2)

                        elif set(conexoes) == {"baixo", "esquerda"}:
                            pg.draw.line(tela, cor_faixa,
                                        (centro_x, centro_y + faixa_tamanho // 2),
                                        (centro_x, centro_y), 2)
                            pg.draw.line(tela, cor_faixa,
                                        (centro_x, centro_y),
                                        (centro_x - faixa_tamanho // 2, centro_y), 2)

                elif len(conexoes) > 2:
                    # Prioriza linha horizontal para evitar cruz
                    if "esquerda" in conexoes or "direita" in conexoes:
                        pg.draw.line(tela, cor_faixa,
                                    (centro_x - faixa_tamanho // 2, centro_y),
                                    (centro_x + faixa_tamanho // 2, centro_y), 2)
                    elif "cima" in conexoes or "baixo" in conexoes:
                        pg.draw.line(tela, cor_faixa,
                                    (centro_x, centro_y - faixa_tamanho // 2),
                                    (centro_x, centro_y + faixa_tamanho // 2), 2)
        # Desenhar sprites de parede especiais (modo fácil)
        if hasattr(self, 'parede_sprites') and sprite_parede is not None:
            for l, c in self.parede_sprites:
                x = c * tamanho_celula
                y = l * tamanho_celula
                tela.blit(sprite_parede, (x, y))


class Personagem:
    """Representa o robô: rotação, movimento e renderização."""
    def __init__(self, caminho_imagem, x, y, larguraP, alturaP):
        self.imagem_original = pg.image.load(caminho_imagem).convert_alpha()
        self.imagem_original = pg.transform.scale(self.imagem_original, (larguraP, alturaP))
        self.imagem = self.imagem_original
        self.x = x
        self.y = y
        self.movimento = deque()
        # Variáveis legadas não utilizadas (mantidas para compatibilidade)
        tempo_ultimo_movimento = 0
        delay_entre_movimentos = 200
        self.velocidade = 15  # pixels por frame
        self.em_movimento = False
        self.distancia_restante = 0
        self.angulo_atual = 0  # ângulo atual (real)
        self.angulo_desejado = 0  # ângulo alvo
        self.velocidade_rotacao = 20  # graus por frame
        self.girando = False

    def girar_para(self, graus):
        """Agenda uma rotação incremental até o ângulo alvo."""
        if not self.girando:
            self.angulo_desejado = (self.angulo_atual + graus) % 360
            self.girando = True


    def desenhar(self, tela):
        """Desenha o sprite do personagem no centro atual."""
        rect = self.imagem.get_rect(center=(self.x, self.y))
        tela.blit(self.imagem, rect.topleft)

    def iniciar_movimento(self, distancia):
        """Inicia um movimento reto de 'distancia' pixels na direção atual."""
        if not self.em_movimento:
            self.distancia_restante = distancia
            self.em_movimento = True
        global tempo_ultimo_movimento
        tempo_ultimo_movimento = pg.time.get_ticks()

    def atualizar_movimento(self):
        """Atualiza a translação por frame até consumir a distância."""
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
        """Interpola a rotação até atingir o ângulo desejado e atualiza o sprite."""
        if self.girando:
            diff = (self.angulo_desejado - self.angulo_atual) % 360
            if diff > 180:
                diff -= 360  # menor caminho

            passo = self.velocidade_rotacao if abs(diff) >= self.velocidade_rotacao else abs(diff)
            if diff < 0:
                self.angulo_atual -= passo
            else:
                self.angulo_atual += passo

            self.angulo_atual %= 360

            if round(self.angulo_atual) == round(self.angulo_desejado):
                self.angulo_atual = self.angulo_desejado
                self.girando = False

            # Atualiza imagem girada
            self.imagem = pg.transform.rotate(self.imagem_original, self.angulo_atual)

    def pode_mover_frente(self, labirinto, tamanho_celula):
        """Verifica colisão com paredes, baseado no ângulo cardinal atual."""
        # Determina a célula atual
        coluna = int(self.x // tamanho_celula)
        linha = int(self.y // tamanho_celula)

        # Garante que não vai dar índice fora do labirinto
        if linha < 0 or linha >= labirinto.linhas or coluna < 0 or coluna >= labirinto.colunas:
            return False

        celula = labirinto.labirinto[linha][coluna]

        # Verifica qual parede ele tá tentando atravessar
        if self.angulo_atual == 0:
            return not celula.paredes["direita"]
        elif self.angulo_atual == 90:
            return not celula.paredes["cima"]
        elif self.angulo_atual == 180:
            return not celula.paredes["esquerda"]
        elif self.angulo_atual == 270:
            return not celula.paredes["baixo"]
        
        return False  # ângulo inválido


def init_jogo(tamanho_celula, linhas, colunas):
    """Inicializa Pygame, janela e personagem. Retorna (tela, relógio, personagem, largura_terminal)."""
    pg.init()
    largura_labirinto = colunas * tamanho_celula
    largura_terminal = 300  # Largura da "extensão" lateral
    largura = largura_labirinto + largura_terminal
    altura = linhas * tamanho_celula
    tela = pg.display.set_mode((largura, altura), pg.RESIZABLE)
    pg.display.set_caption("ROBO")
    relogio = pg.time.Clock()

    personagem = Personagem(
        "docs/assets/carro.png",
        tamanho_celula // 2,
        tamanho_celula // 2,
        tamanho_celula * 2,
        tamanho_celula * 2,
    )

    return tela, relogio, personagem, largura_terminal


def build_grid_surface(linhas, colunas, tamanho_celula):
    """Pré-renderiza a grade (linhas cinza) em uma Surface transparente."""
    surf = pg.Surface((colunas * tamanho_celula, linhas * tamanho_celula), pg.SRCALPHA)
    # Linhas horizontais
    for i in range(linhas + 1):
        y = i * tamanho_celula
        pg.draw.line(surf, (211, 211, 211), (0, y), (colunas * tamanho_celula, y), 1)
    # Linhas verticais
    for j in range(colunas + 1):
        x = j * tamanho_celula
        pg.draw.line(surf, (211, 211, 211), (x, 0), (x, linhas * tamanho_celula), 1)
    return surf


def build_maze_surface(labirinto, tamanho_celula, is_facil, sprite_parede):
    """Pré-renderiza o labirinto (paredes e, se aplicável, sprites)."""
    surf = pg.Surface((labirinto.colunas * tamanho_celula, labirinto.linhas * tamanho_celula), pg.SRCALPHA)
    labirinto.desenhar(surf, tamanho_celula, desenhar_linhas_guia=(not is_facil), sprite_parede=sprite_parede)
    return surf


def main():
    """Loop principal: entrada, geração do labirinto, renderização e lógica de jogo."""
    valores,tipo_movimento = escolher_dificuldade_tkinter()
    modo_comando = tipo_movimento == "comando"
    delay_entre_movimentos = 500  # ms de pausa entre comandos executados no modo comando
    modo_muito_facil = False
    
    linhas, colunas, tamanho_celula = valores[:3]
    labirinto = GeradorLabirinto(linhas, colunas) 

    if len(valores) == 4 and valores[3] == "muito_facil":
        linhas, colunas, tamanho_celula = valores[:3]
        modo_muito_facil = True
        # Remove todas as paredes no modo muito fácil
        for l in range(linhas):
            for c in range(colunas):
                labirinto.labirinto[l][c].paredes = {
                    "cima": False,
                    "baixo": False,
                    "esquerda": False,
                    "direita": False
                }
    if not modo_muito_facil:
        if len(valores) == 4 and valores[3] == "facil":
            # Remove todas as paredes
            for l in range(linhas):
                for c in range(colunas):
                    labirinto.labirinto[l][c].paredes = {
                        "cima": False,
                        "baixo": False,
                        "esquerda": False,
                        "direita": False
                    }
            # Adiciona uma parede de sprites cobrindo 4 das 5 células da coluna do meio
            meio = colunas // 2
            linhas_parede = [0, 1, 2, 3]  # cobre 4 das 5 linhas
            for l in linhas_parede:
                labirinto.labirinto[l][meio].paredes["cima"] = True
                labirinto.labirinto[l][meio].paredes["baixo"] = True
                labirinto.labirinto[l][meio].paredes["esquerda"] = True
                labirinto.labirinto[l][meio].paredes["direita"] = True
            # Salva as posições para desenhar os sprites depois
            parede_sprites = [(l, meio) for l in linhas_parede]
            labirinto.parede_sprites = parede_sprites
            # Define objetivo aleatório nas colunas 4 e 5 (índices 3 e 4)
            cols_alvo = [c for c in (3, 4) if c < colunas]
            opcoes = [(l, c) for l in range(linhas) for c in cols_alvo]
            if opcoes:
                objetivo_linha, objetivo_coluna = random.choice(opcoes)
            else:
                objetivo_linha = linhas - 1
                objetivo_coluna = colunas - 1
        else:
            labirinto.gerar()
            objetivo_linha = labirinto.ultima_celula.linha
            objetivo_coluna = labirinto.ultima_celula.coluna
    else:
        # Modo muito fácil: objetivo aleatório nas colunas 4 e 5 (índices 3 e 4)
        cols_alvo = [c for c in (3, 4) if c < colunas]
        opcoes = [(l, c) for l in range(linhas) for c in cols_alvo]
        if opcoes:
            objetivo_linha, objetivo_coluna = random.choice(opcoes)
        else:
            objetivo_linha = linhas - 1
            objetivo_coluna = colunas - 1

    camera = cv2.VideoCapture(0)
    camera_ok = camera.isOpened()
    if SHOW_CAMERA and camera_ok:
        # Janela redimensionável para permitir maximizar
        try:
            cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
        except Exception:
            pass
    if camera_ok:
        # Define resolução moderada para aliviar CPU
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    tela, relogio, personagem, largura_terminal = init_jogo(tamanho_celula, linhas, colunas)
    # Pré-carrega sprite (modo fácil) e superfícies estáticas
    is_facil = (not modo_muito_facil) and (len(valores) == 4 and valores[3] == "facil")
    sprite_parede = None
    if is_facil:
        try:
            sprite_parede = pg.image.load("docs/assets/parede.png").convert_alpha()
            sprite_parede = pg.transform.scale(sprite_parede, (tamanho_celula, tamanho_celula))
        except Exception:
            sprite_parede = None
    grid_surf = build_grid_surface(linhas, colunas, tamanho_celula)
    maze_surf = pg.Surface((colunas * tamanho_celula, linhas * tamanho_celula), pg.SRCALPHA) if modo_muito_facil else build_maze_surface(labirinto, tamanho_celula, is_facil, sprite_parede)
    # Estado do detector da câmera
    recentes = deque(maxlen=DETECT_RECENT_LEN)
    ultimo_disparo = 0.0
    ultimo_token_camera = None
    qr_detector = cv2.QRCodeDetector() if CAMERA_INPUT_MODE == "qr" else None
    # Controle do modo comando: pausa entre execuções
    last_command_finished_at = pg.time.get_ticks()
    command_in_progress = False

    rodando = True
    executarMovimento = False
    contador = 0

    log_terminal = []  # Lista pra armazenar as mensagens do terminal
    limite_linhas_terminal = 15  # Quantas linhas queremos mostrar
    fonte_terminal = pg.font.SysFont("Segoe UI Emoji", 16)

    def adicionar_log(msg):
        log_terminal.append(msg)
        if len(log_terminal) > limite_linhas_terminal:
            log_terminal.pop(0)
    
    def desenhar_terminal(tela, largura_terminal, altura_tela, largura_total):
        x_terminal = largura_total - largura_terminal
        y_terminal = 0
        altura_linha = 18

        # Fundo do terminal
        pg.draw.rect(tela, (30, 30, 30), (x_terminal, y_terminal, largura_terminal, altura_tela))

        # Borda
        pg.draw.rect(tela, (255, 255, 255), (x_terminal, y_terminal, largura_terminal, altura_tela), 2)

        # Linhas de texto
        for i, linha in enumerate(log_terminal):
            texto = fonte_terminal.render(linha, True, (200, 200, 200))
            tela.blit(texto, (x_terminal + 10, y_terminal + i * altura_linha))

    frame = None
    frame_count = 0

    while rodando:
        frame_count += 1
        detection_run = (frame_count % DETECT_EVERY_N == 0)

        if modo_comando and not executarMovimento:
            # Coleta comandos na fila
            for evento in pg.event.get():
                if evento.type == pg.QUIT:
                    rodando = False
                elif evento.type == pg.VIDEORESIZE:
                    tela = pg.display.set_mode((evento.w, evento.h), pg.RESIZABLE)
                elif evento.type == pg.KEYDOWN and not personagem.em_movimento:
                    if evento.key == pg.K_LEFT:
                        personagem.movimento.append("LEFT")
                        contador += 1
                        adicionar_log("Detectado: 🔁 ESQUERDA")
                    elif evento.key == pg.K_RIGHT:
                        personagem.movimento.append("RIGHT")
                        contador += 1
                        adicionar_log("Detectado: 🔁 DIREITA")
                    elif evento.key == pg.K_SPACE:
                        personagem.movimento.append("SPACE")
                        contador += 1
                        adicionar_log("Detectado: ⬇️ FRENTE")
                    elif evento.key == pg.K_RETURN:
                        executarMovimento = True

            if camera_ok and detection_run:
                comando_camera, frame, origem_camera = detectar_comando_camera(camera, qr_detector)
                tempo_atual = time.time()
                if not personagem.em_movimento:
                    if CAMERA_INPUT_MODE == "qr":
                        if comando_camera:
                            token_camera = f"{origem_camera}|{comando_camera}"
                            if token_camera != ultimo_token_camera or tempo_atual - ultimo_disparo >= DETECT_REFRACTORY_SEC:
                                personagem.movimento.append(comando_camera)
                                contador += 1
                                adicionar_log(descrever_comando_camera(comando_camera, origem_camera))
                                ultimo_disparo = tempo_atual
                            ultimo_token_camera = token_camera
                        else:
                            ultimo_token_camera = None
                    else:
                        recentes.append(origem_camera if origem_camera else "_")
                        if tempo_atual - ultimo_disparo >= DETECT_REFRACTORY_SEC and len(recentes) == DETECT_RECENT_LEN:
                            cont = Counter([c for c in recentes if c != "_"])
                            if cont:
                                cor_maj, votos = cont.most_common(1)[0]
                                if votos >= DETECT_MAJORITY_MIN:
                                    comando_por_cor = {
                                        "amarelo": "LEFT",
                                        "azul": "RIGHT",
                                        "verde": "SPACE",
                                    }.get(cor_maj)
                                    if comando_por_cor:
                                        personagem.movimento.append(comando_por_cor)
                                        contador += 1
                                        adicionar_log(descrever_comando_camera(comando_por_cor, cor_maj))
                                        ultimo_disparo = tempo_atual

        elif not modo_comando:
            # Controle imediato
            for evento in pg.event.get():
                if evento.type == pg.QUIT:
                    rodando = False
                elif evento.type == pg.VIDEORESIZE:
                    tela = pg.display.set_mode((evento.w, evento.h), pg.RESIZABLE)
                elif evento.type == pg.KEYDOWN and not personagem.em_movimento:
                    if evento.key == pg.K_LEFT:
                        mqtt.send_message("LEFT")
                        personagem.girar_para(90)
                        contador += 1
                        adicionar_log("🔁 ESQUERDA")
                    elif evento.key == pg.K_RIGHT:
                        mqtt.send_message("RIGHT")
                        personagem.girar_para(-90)
                        contador += 1
                        adicionar_log("🔁 DIREITA")
                    elif evento.key == pg.K_SPACE:
                        if not personagem.em_movimento and not personagem.girando:
                            if modo_muito_facil or personagem.pode_mover_frente(labirinto, tamanho_celula):
                                mqtt.send_message("SPACE")
                                personagem.iniciar_movimento(tamanho_celula)
                                contador += 1
                                adicionar_log("⬇️ FRENTE")

            if camera_ok and detection_run:
                comando_camera, frame, origem_camera = detectar_comando_camera(camera, qr_detector)
                tempo_atual = time.time()
                if not personagem.em_movimento:
                    comandos_prontos = []
                    if CAMERA_INPUT_MODE == "qr":
                        if comando_camera:
                            token_camera = f"{origem_camera}|{comando_camera}"
                            if token_camera != ultimo_token_camera or tempo_atual - ultimo_disparo >= DETECT_REFRACTORY_SEC:
                                comandos_prontos.append((comando_camera, origem_camera))
                                ultimo_disparo = tempo_atual
                            ultimo_token_camera = token_camera
                        else:
                            ultimo_token_camera = None
                    else:
                        recentes.append(origem_camera if origem_camera else "_")
                        if tempo_atual - ultimo_disparo >= DETECT_REFRACTORY_SEC and len(recentes) == DETECT_RECENT_LEN:
                            cont = Counter([c for c in recentes if c != "_"])
                            if cont:
                                cor_maj, votos = cont.most_common(1)[0]
                                if votos >= DETECT_MAJORITY_MIN:
                                    comando_por_cor = {
                                        "amarelo": "LEFT",
                                        "azul": "RIGHT",
                                        "verde": "SPACE",
                                    }.get(cor_maj)
                                    if comando_por_cor:
                                        comandos_prontos.append((comando_por_cor, cor_maj))
                                        ultimo_disparo = tempo_atual

                    for comando_camera, origem_camera in comandos_prontos:
                        if comando_camera == "LEFT":
                            mqtt.send_message("LEFT")
                            personagem.girar_para(90)
                            contador += 1
                            adicionar_log(descrever_comando_camera("LEFT", origem_camera))
                        elif comando_camera == "RIGHT":
                            mqtt.send_message("RIGHT")
                            personagem.girar_para(-90)
                            contador += 1
                            adicionar_log(descrever_comando_camera("RIGHT", origem_camera))
                        elif comando_camera == "SPACE":
                            if not personagem.em_movimento and not personagem.girando:
                                if modo_muito_facil or personagem.pode_mover_frente(labirinto, tamanho_celula):
                                    mqtt.send_message("SPACE")
                                    personagem.iniciar_movimento(tamanho_celula)
                                    contador += 1
                                    adicionar_log(descrever_comando_camera("SPACE", origem_camera))

        else:
            # Execução com pausas no modo comando
            for evento in pg.event.get():
                if evento.type == pg.QUIT:
                    rodando = False
                elif evento.type == pg.VIDEORESIZE:
                    tela = pg.display.set_mode((evento.w, evento.h), pg.RESIZABLE)
            now_ticks = pg.time.get_ticks()
            if command_in_progress and not personagem.girando and not personagem.em_movimento:
                command_in_progress = False
                last_command_finished_at = now_ticks

            if not command_in_progress and not personagem.girando and not personagem.em_movimento:
                if personagem.movimento:
                    if now_ticks - last_command_finished_at >= delay_entre_movimentos:
                        comando = personagem.movimento.popleft()
                        if comando == "LEFT":
                            personagem.girar_para(90)
                            mqtt.send_message("LEFT")
                            command_in_progress = True
                        elif comando == "RIGHT":
                            personagem.girar_para(-90)
                            mqtt.send_message("RIGHT")
                            command_in_progress = True
                        elif comando == "SPACE":
                            if modo_muito_facil or personagem.pode_mover_frente(labirinto, tamanho_celula):
                                personagem.iniciar_movimento(tamanho_celula)
                                mqtt.send_message("SPACE")
                                command_in_progress = True
                            else:
                                last_command_finished_at = now_ticks
                else:
                    executarMovimento = False

        # Renderização comum
        pg.event.pump()
        tela.fill(COR_TELA)
        tela.blit(grid_surf, (0, 0))
        if not modo_muito_facil:
            tela.blit(maze_surf, (0, 0))

        x_obj = objetivo_coluna * tamanho_celula + tamanho_celula // 4
        y_obj = objetivo_linha * tamanho_celula + tamanho_celula // 4
        tamanho_objetivo = tamanho_celula // 2
        pg.draw.rect(tela, (0, 255, 0), (x_obj, y_obj, tamanho_objetivo, tamanho_objetivo))
        personagem.desenhar(tela)
        desenhar_terminal(tela, largura_terminal, tela.get_height(), tela.get_width())

        col_atual = int(personagem.x // tamanho_celula)
        lin_atual = int(personagem.y // tamanho_celula)
        if col_atual == objetivo_coluna and lin_atual == objetivo_linha:
            rodando = False

        personagem.atualizar_rotacao()
        personagem.atualizar_movimento()
        texto = fonte_terminal.render("Movimentos: " + str(contador), True, (200,200,200))
        tela.blit(texto,(10,10))

        pg.display.flip()
        if SHOW_CAMERA and camera_ok and frame is not None:
            cv2.imshow("Camera", frame)
            cv2.waitKey(1)

        relogio.tick(FPS)

    pg.quit()
    camera.release()
    cv2.destroyAllWindows()
    sys.exit()

if __name__ == "__main__":
    main()
