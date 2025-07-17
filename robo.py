import numpy as np
import pygame as pg
import cv2
import random
import sys
import math
import time
import threading
import PySimpleGUI as sg

HEIGHT = 500
WIDTH = 700
FPS = 60

cordatela = (137,137,137)
intervalos_cores = {
    "vermelho": ((0, 120, 70), (10, 255, 255)),
    "azul": ((100, 180, 50), (130, 255, 255)),
    "verde": ((40, 70, 70), (90, 255, 255))
}

import tkinter as tk

def escolher_dificuldade_tkinter():
    dificuldade = {"valores": None}

    def selecionar(valores):
        dificuldade["valores"] = valores
        root.destroy()

    root = tk.Tk()
    root.title("Escolha a Dificuldade")

    tk.Label(root, text="Escolha a Dificuldade:", font=("Arial", 16)).pack(pady=20)

    tk.Button(root, text="Muito Fácil", bg="green", width=20, height=2,
              command=lambda: selecionar((5, 5, 80))).pack(pady=10)

    tk.Button(root, text="Fácil", bg="lightgreen", width=20, height=2,
              command=lambda: selecionar((10, 10, 50))).pack(pady=10)

    tk.Button(root, text="Médio", bg="khaki", width=20, height=2,
              command=lambda: selecionar((15, 15, 40))).pack(pady=10)

    tk.Button(root, text="Difícil", bg="salmon", width=20, height=2,
              command=lambda: selecionar((25, 25, 25))).pack(pady=10)
    
    tk.Button(root, text="Muito Difícil", bg="red", width=20, height=2,
              command=lambda: selecionar((35, 35, 20))).pack(pady=10)

    root.mainloop()
    return dificuldade["valores"]


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



    
    def desenhar(self, tela, tamanho_celula):
        for l in range(self.linhas):
            for c in range(self.colunas):
                x = c * tamanho_celula
                y = l * tamanho_celula
                celula = self.labirinto[l][c]

                if celula.paredes["cima"]:
                    pg.draw.line(tela, (0,0,0), (x, y), (x + tamanho_celula, y), 2)
                if celula.paredes["baixo"]:
                    pg.draw.line(tela, (0,0,0), (x, y + tamanho_celula), (x + tamanho_celula, y + tamanho_celula), 2)
                if celula.paredes["esquerda"]:
                    pg.draw.line(tela, (0,0,0), (x, y), (x, y + tamanho_celula), 2)
                if celula.paredes["direita"]:
                    pg.draw.line(tela, (0,0,0), (x + tamanho_celula, y), (x + tamanho_celula, y + tamanho_celula), 2)


class Personagem:
    def __init__(self, caminho_imagem, x, y,larguraP, alturaP):
        self.imagem_original = pg.image.load(caminho_imagem).convert_alpha()
        self.imagem_original = pg.transform.scale(self.imagem_original, (larguraP, alturaP))
        self.imagem = self.imagem_original
        self.x = x
        self.y = y
        self.angulo = 0
        self.movimento = list()

    def girar(self, graus):
        self.angulo = (self.angulo + graus) % 360
        self.imagem = pg.transform.rotate(self.imagem_original, self.angulo)

    def desenhar(self, tela):
        rect = self.imagem.get_rect(center=(self.x, self.y))
        tela.blit(self.imagem, rect.topleft)
    
    def mover_para_frente(self, velocidade):
    # Calcula deslocamento baseado no ângulo atual
        dx = math.cos(math.radians(self.angulo)) * velocidade
        dy = -math.sin(math.radians(self.angulo)) * velocidade

        self.x += dx
        self.y += dy
    
    def pode_mover_frente(self, labirinto, tamanho_celula):
        # Determina a célula atual
        coluna = int(self.x // tamanho_celula)
        linha = int(self.y // tamanho_celula)

        # Garante que não vai dar índice fora do labirinto
        if linha < 0 or linha >= labirinto.linhas or coluna < 0 or coluna >= labirinto.colunas:
            return False

        celula = labirinto.labirinto[linha][coluna]

        # Verifica qual parede ele tá tentando atravessar
        if self.angulo == 0:
            return not celula.paredes["direita"]
        elif self.angulo == 90:
            return not celula.paredes["cima"]
        elif self.angulo == 180:
            return not celula.paredes["esquerda"]
        elif self.angulo == 270:
            return not celula.paredes["baixo"]
        
        return False  # ângulo inválido


def init_jogo(tamanho_celula,linhas,colunas):
        pg.init()
        largura = colunas * tamanho_celula
        altura = linhas * tamanho_celula
        tela = pg.display.set_mode((largura, altura))
        pg.display.set_caption("ROBO")
        relogio = pg.time.Clock()

        personagem = Personagem("carro.png", tamanho_celula // 2, tamanho_celula // 2,tamanho_celula*2,tamanho_celula*2)

        return tela, relogio, personagem
def main():
        linhas, colunas, tamanho_celula = escolher_dificuldade_tkinter()
        camera = cv2.VideoCapture(0)
        tela, relogio, personagem = init_jogo(tamanho_celula,linhas,colunas)
        rodando = True
        executarMovimento = False
        indice = 0
        labirinto = GeradorLabirinto(linhas, colunas)
        labirinto.gerar()
        objetivo_linha = labirinto.ultima_celula.linha
        objetivo_coluna = labirinto.ultima_celula.coluna
        ultima_cor_detectada = None
        tempo_ultima_detecao = 0
        cooldown = 1.0  # segundos


        while rodando:
            if executarMovimento == False:
                for evento in pg.event.get():
                    if evento.type == pg.QUIT:
                        rodando = False

                    elif evento.type == pg.KEYDOWN:
                        if evento.key == pg.K_LEFT:
                            personagem.movimento.append("LEFT")
                            #personagem.girar(90)
                        if evento.key == pg.K_RIGHT:
                            personagem.movimento.append("RIGHT")
                            #personagem.girar(-90)
                        if evento.key == pg.K_SPACE:
                            personagem.movimento.append("SPACE")
                            #personagem.mover_para_frente(10)
                        if evento.key == pg.K_RETURN:
                            executarMovimento = True
                
                cor_detectada, frame = detectar_cor(camera, intervalos_cores)
                tempo_atual = time.time()

                # Só adiciona movimento se passou o cooldown OU a cor é diferente da anterior
                if cor_detectada and (cor_detectada != ultima_cor_detectada or tempo_atual - tempo_ultima_detecao > cooldown):
                    if cor_detectada == "vermelho":
                        personagem.movimento.append("LEFT")
                        print("Detectado: VERMELHO -> LEFT")
                    elif cor_detectada == "azul":
                        personagem.movimento.append("RIGHT")
                        print("Detectado: AZUL -> RIGHT")
                    elif cor_detectada == "verde":
                        personagem.movimento.append("SPACE")
                        print("Detectado: VERDE -> SPACE")
                if not cor_detectada:
                    ultima_cor_detectada = None
                    # Atualiza histórico
                ultima_cor_detectada = cor_detectada
                tempo_ultima_detecao = tempo_atual

                if frame is not None:
                    cv2.imshow("Camera", frame)
                    cv2.waitKey(1)

            else:
                if personagem.movimento[indice] == "LEFT":
                    personagem.girar(90)
                elif personagem.movimento[indice] == "RIGHT":
                    personagem.girar(-90)
                elif personagem.movimento[indice] == "SPACE":
                    if personagem.pode_mover_frente(labirinto, tamanho_celula):
                        personagem.mover_para_frente(tamanho_celula)
                time.sleep(0.5)
                indice += 1
                if indice == len(personagem.movimento):
                    personagem.movimento.clear()
                    executarMovimento = False
                    indice = 0
            



            tela.fill(cordatela)
            labirinto.desenhar(tela, tamanho_celula)
            x_obj = objetivo_coluna * tamanho_celula + tamanho_celula // 4
            y_obj = objetivo_linha * tamanho_celula + tamanho_celula // 4
            tamanho_objetivo = tamanho_celula // 2

            pg.draw.rect(tela, (0, 255, 0), (x_obj, y_obj, tamanho_objetivo, tamanho_objetivo))
            personagem.desenhar(tela)
            

            col_atual = int(personagem.x // tamanho_celula)
            lin_atual = int(personagem.y // tamanho_celula)

            if col_atual == objetivo_coluna and lin_atual == objetivo_linha:
                rodando = False


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