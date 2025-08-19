
#Projeto Computação para Todos, objetivo: popularização do pensamento computacional
#Demonstração de algoritmos de forma lúdica, forma interativa
import numpy as np
import pygame as pg
import cv2
import random
import sys
import math
import time
import tkinter as tk
from collections import deque

HEIGHT = 500
WIDTH = 700
FPS = 60

cordatela = (100,103,97)
intervalos_cores = {
    "vermelho": ((0, 120, 70), (10, 255, 255)),
    "azul": ((100, 180, 50), (130, 255, 255)),
    "verde": ((40, 70, 70), (90, 255, 255))
}

def escolher_dificuldade_tkinter():
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


def detectar_cor(camera, intervalos_cores, roi_tamanho=(200, 200)):
    ret, frame = camera.read()
    if not ret:
        return None, None

    altura, largura, _ = frame.shape
    w, h = roi_tamanho

    # Calcula o centro da imagem
    centro_x = largura // 2
    centro_y = altura // 2

    # Define a área de interesse (ROI)
    x1 = centro_x - w // 2
    y1 = centro_y - h // 2
    x2 = centro_x + w // 2
    y2 = centro_y + h // 2

    roi = frame[y1:y2, x1:x2]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    for cor, (lower, upper) in intervalos_cores.items():
        lower_np = np.array(lower)
        upper_np = np.array(upper)

        mask = cv2.inRange(hsv, lower_np, upper_np)
        contornos, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if contornos and cv2.contourArea(max(contornos, key=cv2.contourArea)) > 2000:
            return cor, frame  # Cor detectada na ROI

    # Desenha um retângulo na imagem original (só visual)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)

    return None, frame


class Celula:
    def __init__(self, linha, coluna):
        self.linha = linha
        self.coluna = coluna
        self.visitada = False
        self.paredes = {
            "cima": True,
            "baixo": True,
            "esquerda": True,
            "direita": True
        }

class GeradorLabirinto:
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
            "direita": "esquerda"
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
    def __init__(self, caminho_imagem, x, y, larguraP, alturaP):
        self.imagem_original = pg.image.load(caminho_imagem).convert_alpha()
        self.imagem_original = pg.transform.scale(self.imagem_original, (larguraP, alturaP))
        self.imagem = self.imagem_original
        self.x = x
        self.y = y
        self.movimento = deque()
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
        global tempo_ultimo_movimento
        tempo_ultimo_movimento = pg.time.get_ticks()

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


def init_jogo(tamanho_celula,linhas,colunas):
        pg.init()
        largura_labirinto = colunas * tamanho_celula
        largura_terminal = 300  # Largura da "extensão" lateral
        largura = largura_labirinto + largura_terminal
        altura = linhas * tamanho_celula
        tela = pg.display.set_mode((largura, altura))
        pg.display.set_caption("ROBO")
        relogio = pg.time.Clock()

        personagem = Personagem("carro.png", tamanho_celula // 2, tamanho_celula // 2,tamanho_celula*2,tamanho_celula*2)

        return tela, relogio, personagem, largura_terminal

def main():
        valores,tipo_movimento = escolher_dificuldade_tkinter()
        modo_comando = tipo_movimento == "comando"
        tempo_ultimo_movimento = 0
        delay_entre_movimentos = 500
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
                objetivo_linha = linhas - 1
                objetivo_coluna = colunas - 1
            else:
                labirinto.gerar()
                objetivo_linha = labirinto.ultima_celula.linha
                objetivo_coluna = labirinto.ultima_celula.coluna
        else:
            objetivo_linha = linhas - 1
            objetivo_coluna = colunas - 1

        camera = cv2.VideoCapture(0)
        tela, relogio, personagem, largura_terminal = init_jogo(tamanho_celula,linhas,colunas)
        rodando = True
        executarMovimento = False
        indice = 0
        contador = 0
        ultima_cor_detectada = None
        tempo_ultima_detecao = 0
        cooldown = 1.0  # segundos

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


        while rodando:
            if modo_comando and not executarMovimento:
                for evento in pg.event.get():
                    if evento.type == pg.QUIT:
                        rodando = False
                    elif evento.type == pg.KEYDOWN:
                        if not personagem.em_movimento:
                            if evento.key == pg.K_LEFT:
                                personagem.movimento.append("LEFT")
                                contador += 1
                                adicionar_log("Detectado: 🔁 ESQUERDA")
                                #personagem.girar(90)
                            if evento.key == pg.K_RIGHT:
                                personagem.movimento.append("RIGHT")
                                contador += 1
                                adicionar_log("Detectado: 🔁 DIREITA")
                                #personagem.girar(-90)
                            if evento.key == pg.K_SPACE:
                                personagem.movimento.append("SPACE")
                                contador += 1
                                adicionar_log("Detectado: ⬇️ FRENTE")
                                #personagem.mover_para_frente(10)
                            if evento.key == pg.K_RETURN:
                                executarMovimento = True
                
                cor_detectada, frame = detectar_cor(camera, intervalos_cores)
                tempo_atual = time.time()

                # Só adiciona movimento se passou o cooldown OU a cor é diferente da anterior
                if not personagem.em_movimento:
                    if cor_detectada and (cor_detectada != ultima_cor_detectada or tempo_atual - tempo_ultima_detecao > cooldown):
                        if cor_detectada == "vermelho":
                            personagem.movimento.append("LEFT")
                            contador += 1
                            adicionar_log("Detectado: VERMELHO -> 🔁 ESQUERDA")
                        elif cor_detectada == "azul":
                            personagem.movimento.append("RIGHT")
                            contador += 1
                            adicionar_log("Detectado: AZUL -> 🔁 DIREITA")
                        elif cor_detectada == "verde":
                            personagem.movimento.append("SPACE")
                            contador += 1
                            adicionar_log("Detectado: 🟩 -> ⬇️ FRENTE")
                    if not cor_detectada:
                        ultima_cor_detectada = None
                        # Atualiza histórico
                ultima_cor_detectada = cor_detectada
                tempo_ultima_detecao = tempo_atual

                if frame is not None:
                    cv2.imshow("Camera", frame)
                    cv2.waitKey(1)
            
            elif not modo_comando:
                for evento in pg.event.get():
                    if not personagem.em_movimento:
                        if evento.type == pg.QUIT:
                            rodando = False
                        elif evento.type == pg.KEYDOWN:
                            if evento.key == pg.K_LEFT:
                                personagem.girar_para(90)
                                contador += 1
                                adicionar_log("🔁 ESQUERDA")
                            elif evento.key == pg.K_RIGHT:
                                personagem.girar_para(-90)
                                contador += 1
                                adicionar_log("🔁 DIREITA")
                            elif evento.key == pg.K_SPACE:
                                if modo_muito_facil or personagem.pode_mover_frente(labirinto, tamanho_celula):
                                    if not personagem.em_movimento and not personagem.girando and personagem.pode_mover_frente(labirinto, tamanho_celula):
                                        personagem.iniciar_movimento(tamanho_celula)
                                        contador += 1
                                        adicionar_log("⬇️ FRENTE")
                    
                
                cor_detectada, frame = detectar_cor(camera, intervalos_cores)
                tempo_atual = time.time()
                if not personagem.em_movimento:
                    if cor_detectada and (cor_detectada != ultima_cor_detectada or tempo_atual - tempo_ultima_detecao > cooldown):
                        if cor_detectada == "vermelho":
                            personagem.girar_para(90)
                            contador += 1
                            adicionar_log("Detectado: VERMELHO -> 🔁 ESQUERDA")
                        elif cor_detectada == "azul":
                            personagem.girar_para(-90)
                            contador += 1
                            adicionar_log("Detectado: AZUL -> 🔁 DIREITA")
                        elif cor_detectada == "verde":
                            if modo_muito_facil or personagem.pode_mover_frente(labirinto, tamanho_celula):
                                if not personagem.em_movimento and not personagem.girando and personagem.pode_mover_frente(labirinto, tamanho_celula):
                                        personagem.iniciar_movimento(tamanho_celula)
                                        contador += 1
                                        adicionar_log("Detectado: 🟩 -> ⬇️ FRENTE")
                                
                    if not cor_detectada:
                        ultima_cor_detectada = None
                        # Atualiza histórico
                    ultima_cor_detectada = cor_detectada
                    tempo_ultima_detecao = tempo_atual

                if frame is not None:
                    cv2.imshow("Camera", frame)
                    cv2.waitKey(1)


            else:
                if not personagem.girando and not personagem.em_movimento:
                    if personagem.movimento:
                        if tempo_atual - tempo_ultimo_movimento >= delay_entre_movimentos:
                            comando = personagem.movimento.popleft()
                            if comando == "LEFT":
                                personagem.girar_para(90)
                            elif comando == "RIGHT":
                                personagem.girar_para(-90)
                            elif comando == "SPACE":
                                if modo_muito_facil or personagem.pode_mover_frente(labirinto, tamanho_celula):
                                    personagem.iniciar_movimento(tamanho_celula)
                    else:
                        executarMovimento = False
            

            tela.fill(cordatela)

            altura_terminal = 100  # ou o valor que tu estiver usando

            # Linhas horizontais
            for i in range(linhas + 1):
                y = i * tamanho_celula
                pg.draw.line(tela, (211, 211, 211), (0, y), (colunas * tamanho_celula, y), 1)

            # Linhas verticais
            for j in range(colunas + 1):
                x = j * tamanho_celula
                pg.draw.line(tela, (211, 211, 211), (x, 0), (x, linhas * tamanho_celula), 1)

            if not modo_muito_facil:
                if len(valores) == 4 and valores[3] == "facil":
                    sprite_parede = pg.image.load("parede.png").convert_alpha()
                    sprite_parede = pg.transform.scale(sprite_parede, (tamanho_celula, tamanho_celula))
                    labirinto.desenhar(tela, tamanho_celula, desenhar_linhas_guia=False, sprite_parede=sprite_parede)
                else:
                    labirinto.desenhar(tela, tamanho_celula, desenhar_linhas_guia=True)
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

            pg.display.update()
            cv2.imshow("Camera", frame)
            cv2.waitKey(1)
            relogio.tick(FPS)

        pg.quit()
        camera.release()
        cv2.destroyAllWindows()
        sys.exit()

if __name__ == "__main__":
    main()