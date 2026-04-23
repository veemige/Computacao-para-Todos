"""Setup, eventos, renderizacao e loop principal do jogo."""

import sys

import cv2
import pygame as pg

from game_modules.camera_utils import (
    abrir_camera,
    coletar_comandos_camera,
    criar_estado_camera,
    descrever_comando_camera,
    mostrar_camera,
    processar_entrada_camera,
)
from game_modules.config import (
    COMANDO_VERIFICADOR,
    COR_TELA,
    DELAY_ENTRE_MOVIMENTOS,
    FPS,
    TECLA_VERIFICADOR,
    VERIFICADOR_GIRO_DIRECAO,
)
from game_modules.maze import preparar_labirinto
from game_modules.player import Personagem
from game_modules.ui import escolher_dificuldade_tkinter


def init_jogo(tamanho_celula, linhas, colunas):
    pg.init()
    largura_labirinto = colunas * tamanho_celula
    largura_terminal = 300
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
    surf = pg.Surface((colunas * tamanho_celula, linhas * tamanho_celula), pg.SRCALPHA)
    for i in range(linhas + 1):
        y = i * tamanho_celula
        pg.draw.line(surf, (211, 211, 211), (0, y), (colunas * tamanho_celula, y), 1)
    for j in range(colunas + 1):
        x = j * tamanho_celula
        pg.draw.line(surf, (211, 211, 211), (x, 0), (x, linhas * tamanho_celula), 1)
    return surf


def build_maze_surface(labirinto, tamanho_celula, is_facil, sprite_parede):
    surf = pg.Surface(
        (labirinto.colunas * tamanho_celula, labirinto.linhas * tamanho_celula),
        pg.SRCALPHA,
    )
    labirinto.desenhar(
        surf,
        tamanho_celula,
        desenhar_linhas_guia=(not is_facil),
        sprite_parede=sprite_parede,
    )
    return surf


def carregar_sprite_parede(tamanho_celula, is_facil):
    if not is_facil:
        return None
    try:
        sprite = pg.image.load("docs/assets/parede.png").convert_alpha()
        return pg.transform.scale(sprite, (tamanho_celula, tamanho_celula))
    except Exception:
        return None


def criar_surfaces_jogo(linhas, colunas, tamanho_celula, labirinto, modo_muito_facil, is_facil):
    sprite_parede = carregar_sprite_parede(tamanho_celula, is_facil)
    grid_surf = build_grid_surface(linhas, colunas, tamanho_celula)
    maze_surf = (
        pg.Surface((colunas * tamanho_celula, linhas * tamanho_celula), pg.SRCALPHA)
        if modo_muito_facil
        else build_maze_surface(labirinto, tamanho_celula, is_facil, sprite_parede)
    )
    return grid_surf, maze_surf


def criar_fog_surface(linhas, colunas, tamanho_celula):
    largura = colunas * tamanho_celula
    altura = linhas * tamanho_celula
    fog_surf = pg.Surface((largura, altura), pg.SRCALPHA)
    fog_surf.fill((0, 0, 0, 255))
    return fog_surf


def obter_celula_personagem(personagem, tamanho_celula, linhas, colunas):
    coluna = int(personagem.x // tamanho_celula)
    linha = int(personagem.y // tamanho_celula)
    coluna = max(0, min(colunas - 1, coluna))
    linha = max(0, min(linhas - 1, linha))
    return linha, coluna


def revelar_celula(fog_surf, linha, coluna, tamanho_celula):
    area = pg.Rect(
        coluna * tamanho_celula,
        linha * tamanho_celula,
        tamanho_celula,
        tamanho_celula,
    )
    fog_surf.fill((0, 0, 0, 0), area)


def criar_terminal():
    log_terminal = []
    limite_linhas = 15
    fonte = pg.font.SysFont("Segoe UI Emoji", 16)

    def adicionar_log(msg):
        log_terminal.append(msg)
        if len(log_terminal) > limite_linhas:
            log_terminal.pop(0)

    def desenhar_terminal(tela, largura_terminal, altura_tela, largura_total):
        x_terminal = largura_total - largura_terminal
        altura_linha = 18
        pg.draw.rect(tela, (30, 30, 30), (x_terminal, 0, largura_terminal, altura_tela))
        pg.draw.rect(tela, (255, 255, 255), (x_terminal, 0, largura_terminal, altura_tela), 2)
        for i, linha in enumerate(log_terminal):
            texto = fonte.render(linha, True, (200, 200, 200))
            tela.blit(texto, (x_terminal + 10, i * altura_linha))

    return adicionar_log, desenhar_terminal, fonte


def registrar_comando_em_fila(personagem, comando, origem, adicionar_log):
    personagem.movimento.append(comando)
    adicionar_log(descrever_comando_camera(comando, origem))
    return 1


def girar_verificador(personagem):
    if VERIFICADOR_GIRO_DIRECAO == "LEFT":
        personagem.girar_para(90)
    else:
        personagem.girar_para(-90)


def executar_comando_verificador(personagem, labirinto, tamanho_celula, modo_muito_facil):
    if pode_avancar(personagem, labirinto, tamanho_celula, modo_muito_facil):
        personagem.iniciar_movimento(tamanho_celula)
        return "move"

    girar_verificador(personagem)
    return "turn"


def pode_avancar(personagem, labirinto, tamanho_celula, modo_muito_facil):
    return modo_muito_facil or personagem.pode_mover_frente(labirinto, tamanho_celula)


def aplicar_comando_direto(personagem, comando, origem, adicionar_log,
                           labirinto, tamanho_celula, modo_muito_facil):
    if comando == "LEFT":
        personagem.girar_para(90)
        adicionar_log(descrever_comando_camera("LEFT", origem))
        return 1
    if comando == "RIGHT":
        personagem.girar_para(-90)
        adicionar_log(descrever_comando_camera("RIGHT", origem))
        return 1
    if (
        comando == "SPACE"
        and not personagem.em_movimento
        and not personagem.girando
        and pode_avancar(personagem, labirinto, tamanho_celula, modo_muito_facil)
    ):
        personagem.iniciar_movimento(tamanho_celula)
        adicionar_log(descrever_comando_camera("SPACE", origem))
        return 1
    return 0


def tratar_eventos_saida(tela, eventos):
    rodando = True
    for evento in eventos:
        if evento.type == pg.QUIT:
            rodando = False
        elif evento.type == pg.VIDEORESIZE:
            tela = pg.display.set_mode((evento.w, evento.h), pg.RESIZABLE)
    return rodando, tela


def tratar_eventos_modo_comando(eventos, tela, personagem, adicionar_log, tipo_verificador):
    rodando, tela = tratar_eventos_saida(tela, eventos)
    executar_movimento = False
    contador = 0
    tecla_verificador = getattr(pg, f"K_{TECLA_VERIFICADOR.lower()}", None)

    for evento in eventos:
        if evento.type != pg.KEYDOWN or personagem.em_movimento:
            continue
        if evento.key == pg.K_LEFT:
            personagem.movimento.append("LEFT")
            adicionar_log("Detectado: ESQUERDA")
            contador += 1
        elif evento.key == pg.K_RIGHT:
            personagem.movimento.append("RIGHT")
            adicionar_log("Detectado: DIREITA")
            contador += 1
        elif evento.key == pg.K_SPACE:
            personagem.movimento.append("SPACE")
            adicionar_log("Detectado: FRENTE")
            contador += 1
        elif tipo_verificador == "tecla" and tecla_verificador is not None and evento.key == tecla_verificador:
            personagem.movimento.append(COMANDO_VERIFICADOR)
            adicionar_log("Detectado: VERIFICADOR")
            contador += 1
        elif evento.key == pg.K_RETURN:
            executar_movimento = True

    return rodando, tela, contador, executar_movimento


def tratar_eventos_modo_direto(eventos, tela, personagem, adicionar_log,
                               labirinto, tamanho_celula, modo_muito_facil):
    rodando, tela = tratar_eventos_saida(tela, eventos)
    contador = 0

    for evento in eventos:
        if evento.type != pg.KEYDOWN or personagem.em_movimento:
            continue
        if evento.key == pg.K_LEFT:
            personagem.girar_para(90)
            adicionar_log("ESQUERDA")
            contador += 1
        elif evento.key == pg.K_RIGHT:
            personagem.girar_para(-90)
            adicionar_log("DIREITA")
            contador += 1
        elif evento.key == pg.K_SPACE and not personagem.girando:
            if pode_avancar(personagem, labirinto, tamanho_celula, modo_muito_facil):
                personagem.iniciar_movimento(tamanho_celula)
                adicionar_log("FRENTE")
                contador += 1

    return rodando, tela, contador


def executar_fila_comandos(personagem, executar_movimento, command_in_progress,
                           comando_atual, subacao_verificador,
                           last_command_finished_at, delay_entre_movimentos,
                           labirinto, tamanho_celula, modo_muito_facil):
    now_ticks = pg.time.get_ticks()

    if command_in_progress and not personagem.girando and not personagem.em_movimento:
        if comando_atual == COMANDO_VERIFICADOR and subacao_verificador == "turn":
            subacao_verificador = executar_comando_verificador(
                personagem, labirinto, tamanho_celula, modo_muito_facil
            )
        else:
            command_in_progress = False
            comando_atual = None
            subacao_verificador = None
            last_command_finished_at = now_ticks

    if not command_in_progress and not personagem.girando and not personagem.em_movimento:
        if personagem.movimento:
            if now_ticks - last_command_finished_at >= delay_entre_movimentos:
                comando = personagem.movimento.popleft()
                comando_atual = comando
                if comando == "LEFT":
                    personagem.girar_para(90)
                    command_in_progress = True
                elif comando == "RIGHT":
                    personagem.girar_para(-90)
                    command_in_progress = True
                elif comando == "SPACE":
                    if pode_avancar(personagem, labirinto, tamanho_celula, modo_muito_facil):
                        personagem.iniciar_movimento(tamanho_celula)
                        command_in_progress = True
                    else:
                        comando_atual = None
                        last_command_finished_at = now_ticks
                elif comando == COMANDO_VERIFICADOR:
                    subacao_verificador = executar_comando_verificador(
                        personagem, labirinto, tamanho_celula, modo_muito_facil
                    )
                    command_in_progress = True
        else:
            executar_movimento = False

    return (
        executar_movimento,
        command_in_progress,
        comando_atual,
        subacao_verificador,
        last_command_finished_at,
    )


def desenhar_objetivo(tela, objetivo_linha, objetivo_coluna, tamanho_celula):
    x_obj = objetivo_coluna * tamanho_celula + tamanho_celula // 4
    y_obj = objetivo_linha * tamanho_celula + tamanho_celula // 4
    tamanho_objetivo = tamanho_celula // 2
    pg.draw.rect(tela, (0, 255, 0), (x_obj, y_obj, tamanho_objetivo, tamanho_objetivo))


def renderizar_jogo(tela, grid_surf, maze_surf, modo_muito_facil, personagem,
                    desenhar_terminal, largura_terminal, objetivo_linha,
                    objetivo_coluna, tamanho_celula, fonte_terminal, contador,
                    fog_surf):
    pg.event.pump()
    tela.fill(COR_TELA)
    tela.blit(grid_surf, (0, 0))
    if not modo_muito_facil:
        tela.blit(maze_surf, (0, 0))

    desenhar_objetivo(tela, objetivo_linha, objetivo_coluna, tamanho_celula)
    tela.blit(fog_surf, (0, 0))
    personagem.desenhar(tela)
    desenhar_terminal(tela, largura_terminal, tela.get_height(), tela.get_width())

    texto = fonte_terminal.render("Movimentos: " + str(contador), True, (200, 200, 200))
    tela.blit(texto, (10, 10))


def objetivo_foi_atingido(personagem, tamanho_celula, objetivo_linha, objetivo_coluna):
    col_atual = int(personagem.x // tamanho_celula)
    lin_atual = int(personagem.y // tamanho_celula)
    return col_atual == objetivo_coluna and lin_atual == objetivo_linha


def encerrar_jogo(camera):
    pg.quit()
    camera.release()
    cv2.destroyAllWindows()
    sys.exit()


def executar_jogo():
    valores, tipo_movimento, tipo_verificador = escolher_dificuldade_tkinter()
    modo_comando = tipo_movimento == "comando"

    contexto_labirinto = preparar_labirinto(valores)
    linhas = contexto_labirinto["linhas"]
    colunas = contexto_labirinto["colunas"]
    tamanho_celula = contexto_labirinto["tamanho_celula"]
    labirinto = contexto_labirinto["labirinto"]
    modo_muito_facil = contexto_labirinto["modo_muito_facil"]
    objetivo_linha = contexto_labirinto["objetivo_linha"]
    objetivo_coluna = contexto_labirinto["objetivo_coluna"]

    camera, camera_ok = abrir_camera()
    tela, relogio, personagem, largura_terminal = init_jogo(tamanho_celula, linhas, colunas)
    grid_surf, maze_surf = criar_surfaces_jogo(
        linhas,
        colunas,
        tamanho_celula,
        labirinto,
        modo_muito_facil,
        contexto_labirinto["is_facil"],
    )
    adicionar_log, desenhar_terminal, fonte_terminal = criar_terminal()
    estado_camera = criar_estado_camera()
    fog_surf = criar_fog_surface(linhas, colunas, tamanho_celula)
    linha_inicial, coluna_inicial = obter_celula_personagem(
        personagem, tamanho_celula, linhas, colunas
    )
    revelar_celula(fog_surf, linha_inicial, coluna_inicial, tamanho_celula)

    last_command_finished_at = pg.time.get_ticks()
    command_in_progress = False
    comando_atual = None
    subacao_verificador = None
    rodando = True
    executar_movimento = False
    contador = 0

    while rodando:
        eventos = pg.event.get()
        comando_camera, origem_camera = processar_entrada_camera(estado_camera, camera, camera_ok)

        if modo_comando and not executar_movimento:
            rodando, tela, contador_local, iniciar_execucao = tratar_eventos_modo_comando(
                eventos, tela, personagem, adicionar_log, tipo_verificador
            )
            contador += contador_local
            if iniciar_execucao:
                executar_movimento = True

            if not personagem.em_movimento:
                for comando, origem in coletar_comandos_camera(
                    estado_camera, comando_camera, origem_camera
                ):
                    if comando == COMANDO_VERIFICADOR and tipo_verificador != "qr":
                        continue
                    contador += registrar_comando_em_fila(
                        personagem, comando, origem, adicionar_log
                    )

        elif not modo_comando:
            rodando, tela, contador_local = tratar_eventos_modo_direto(
                eventos, tela, personagem, adicionar_log,
                labirinto, tamanho_celula, modo_muito_facil
            )
            contador += contador_local

            if not personagem.em_movimento:
                for comando, origem in coletar_comandos_camera(
                    estado_camera, comando_camera, origem_camera
                ):
                    contador += aplicar_comando_direto(
                        personagem, comando, origem, adicionar_log,
                        labirinto, tamanho_celula, modo_muito_facil
                    )

        else:
            rodando, tela = tratar_eventos_saida(tela, eventos)
            (
                executar_movimento,
                command_in_progress,
                comando_atual,
                subacao_verificador,
                last_command_finished_at,
            ) = executar_fila_comandos(
                personagem,
                executar_movimento,
                command_in_progress,
                comando_atual,
                subacao_verificador,
                last_command_finished_at,
                DELAY_ENTRE_MOVIMENTOS,
                labirinto,
                tamanho_celula,
                modo_muito_facil,
            )

        renderizar_jogo(
            tela,
            grid_surf,
            maze_surf,
            modo_muito_facil,
            personagem,
            desenhar_terminal,
            largura_terminal,
            objetivo_linha,
            objetivo_coluna,
            tamanho_celula,
            fonte_terminal,
            contador,
            fog_surf,
        )

        personagem.atualizar_rotacao()
        personagem.atualizar_movimento()
        linha_atual, coluna_atual = obter_celula_personagem(
            personagem, tamanho_celula, linhas, colunas
        )
        revelar_celula(fog_surf, linha_atual, coluna_atual, tamanho_celula)

        if objetivo_foi_atingido(personagem, tamanho_celula, objetivo_linha, objetivo_coluna):
            rodando = False

        pg.display.flip()
        mostrar_camera(estado_camera["frame"])
        relogio.tick(FPS)

    encerrar_jogo(camera)
