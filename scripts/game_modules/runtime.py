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
)
from game_modules.maze import preparar_labirinto
from game_modules.player import Personagem
from game_modules.ui import escolher_dificuldade_tkinter

RAMO_LIVRE = "livre"
RAMO_PAREDE = "parede"
NOMES_RAMOS = {
    RAMO_LIVRE: "LIVRE",
    RAMO_PAREDE: "PAREDE",
}


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


def criar_editor_comandos(fila_principal):
    return {
        "pilha": [
            {
                "lista": fila_principal,
                "verificador": None,
                "ramo": None,
            }
        ],
        "proximo_id": 1,
    }


def obter_lista_editor(editor_comandos):
    return editor_comandos["pilha"][-1]["lista"]


def descrever_posicao_editor(editor_comandos):
    partes = []
    for nivel in editor_comandos["pilha"][1:]:
        partes.append(f"V{nivel['verificador']['id']}:{NOMES_RAMOS[nivel['ramo']]}")
    if not partes:
        return "lista principal"
    return " > ".join(partes)


def adicionar_comando_ao_editor(editor_comandos, comando):
    obter_lista_editor(editor_comandos).append(comando)


def criar_verificador_no_editor(editor_comandos):
    verificador = {
        "tipo": COMANDO_VERIFICADOR,
        "id": editor_comandos["proximo_id"],
        RAMO_LIVRE: [],
        RAMO_PAREDE: [],
    }
    editor_comandos["proximo_id"] += 1
    obter_lista_editor(editor_comandos).append(verificador)
    editor_comandos["pilha"].append(
        {
            "lista": verificador[RAMO_LIVRE],
            "verificador": verificador,
            "ramo": RAMO_LIVRE,
        }
    )
    return verificador


def alternar_ramo_editor(editor_comandos):
    if len(editor_comandos["pilha"]) <= 1:
        return None

    nivel = editor_comandos["pilha"][-1]
    novo_ramo = RAMO_PAREDE if nivel["ramo"] == RAMO_LIVRE else RAMO_LIVRE
    nivel["ramo"] = novo_ramo
    nivel["lista"] = nivel["verificador"][novo_ramo]
    return nivel


def fechar_verificador_editor(editor_comandos):
    if len(editor_comandos["pilha"]) <= 1:
        return None
    return editor_comandos["pilha"].pop()


def voltar_editor_para_lista_principal(editor_comandos):
    estava_em_verificador = len(editor_comandos["pilha"]) > 1
    editor_comandos["pilha"] = editor_comandos["pilha"][:1]
    return estava_em_verificador


def registrar_comando_no_editor(editor_comandos, comando, origem, adicionar_log):
    if comando == COMANDO_VERIFICADOR:
        verificador = criar_verificador_no_editor(editor_comandos)
        adicionar_log(f"Verificador V{verificador['id']} criado: ramo LIVRE.")
    else:
        adicionar_comando_ao_editor(editor_comandos, comando)
        adicionar_log(descrever_comando_camera(comando, origem))
    return 1


def executar_comando_verificador(personagem, labirinto, tamanho_celula, modo_muito_facil):
    if pode_avancar(personagem, labirinto, tamanho_celula, modo_muito_facil):
        personagem.iniciar_movimento(tamanho_celula)
        return "move"
    return "blocked"


def registrar_resultado_verificador(adicionar_log, resultado):
    if resultado == "move":
        adicionar_log("Verificador: caminho livre. Executando avanco.")
    else:
        adicionar_log("Verificador: parede detectada. Seguindo para o proximo comando da fila.")


def escolher_ramo_verificador(personagem, labirinto, tamanho_celula, modo_muito_facil):
    if pode_avancar(personagem, labirinto, tamanho_celula, modo_muito_facil):
        return RAMO_LIVRE
    return RAMO_PAREDE


def registrar_ramo_verificador(adicionar_log, verificador, ramo):
    adicionar_log(f"Verificador V{verificador['id']}: executando ramo {NOMES_RAMOS[ramo]}.")


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
    if comando == COMANDO_VERIFICADOR and not personagem.girando and not personagem.em_movimento:
        adicionar_log(descrever_comando_camera(COMANDO_VERIFICADOR, origem))
        resultado_verificador = executar_comando_verificador(
            personagem, labirinto, tamanho_celula, modo_muito_facil
        )
        registrar_resultado_verificador(adicionar_log, resultado_verificador)
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


def tratar_eventos_modo_comando(eventos, tela, personagem, adicionar_log,
                                tipo_verificador, editor_comandos):
    rodando, tela = tratar_eventos_saida(tela, eventos)
    executar_movimento = False
    contador = 0
    tecla_verificador = getattr(pg, f"K_{TECLA_VERIFICADOR.lower()}", None)

    for evento in eventos:
        if evento.type != pg.KEYDOWN or personagem.em_movimento:
            continue
        if evento.key == pg.K_LEFT:
            adicionar_comando_ao_editor(editor_comandos, "LEFT")
            adicionar_log("Detectado: ESQUERDA")
            contador += 1
        elif evento.key == pg.K_RIGHT:
            adicionar_comando_ao_editor(editor_comandos, "RIGHT")
            adicionar_log("Detectado: DIREITA")
            contador += 1
        elif evento.key == pg.K_SPACE:
            adicionar_comando_ao_editor(editor_comandos, "SPACE")
            adicionar_log("Detectado: FRENTE")
            contador += 1
        elif tipo_verificador == "tecla" and tecla_verificador is not None and evento.key == tecla_verificador:
            verificador = criar_verificador_no_editor(editor_comandos)
            adicionar_log(f"Verificador V{verificador['id']} criado: ramo LIVRE.")
            contador += 1
        elif evento.key == pg.K_TAB:
            nivel = alternar_ramo_editor(editor_comandos)
            if nivel:
                adicionar_log(
                    f"V{nivel['verificador']['id']}: editando ramo {NOMES_RAMOS[nivel['ramo']]}."
                )
        elif evento.key == pg.K_BACKSPACE:
            nivel = fechar_verificador_editor(editor_comandos)
            if nivel:
                adicionar_log(
                    f"Fechou V{nivel['verificador']['id']}. Editando {descrever_posicao_editor(editor_comandos)}."
                )
        elif evento.key == pg.K_RETURN:
            if voltar_editor_para_lista_principal(editor_comandos):
                adicionar_log("Executando lista principal.")
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
                           comando_atual,
                           last_command_finished_at, delay_entre_movimentos,
                           labirinto, tamanho_celula, modo_muito_facil,
                           adicionar_log):
    now_ticks = pg.time.get_ticks()

    if command_in_progress and not personagem.girando and not personagem.em_movimento:
        command_in_progress = False
        comando_atual = None
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
                    resultado_verificador = executar_comando_verificador(
                        personagem, labirinto, tamanho_celula, modo_muito_facil
                    )
                    registrar_resultado_verificador(adicionar_log, resultado_verificador)
                    if resultado_verificador == "move":
                        command_in_progress = True
                    else:
                        comando_atual = None
                        last_command_finished_at = now_ticks
                elif isinstance(comando, dict) and comando.get("tipo") == COMANDO_VERIFICADOR:
                    ramo = escolher_ramo_verificador(
                        personagem, labirinto, tamanho_celula, modo_muito_facil
                    )
                    registrar_ramo_verificador(adicionar_log, comando, ramo)
                    for comando_do_ramo in reversed(comando[ramo]):
                        personagem.movimento.appendleft(comando_do_ramo)
                    comando_atual = None
                    last_command_finished_at = now_ticks
        else:
            executar_movimento = False

    return (
        executar_movimento,
        command_in_progress,
        comando_atual,
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
    rodando = True
    executar_movimento = False
    contador = 0
    editor_comandos = criar_editor_comandos(personagem.movimento)

    while rodando:
        eventos = pg.event.get()
        comando_camera, origem_camera = processar_entrada_camera(estado_camera, camera, camera_ok)

        if modo_comando and not executar_movimento:
            rodando, tela, contador_local, iniciar_execucao = tratar_eventos_modo_comando(
                eventos, tela, personagem, adicionar_log, tipo_verificador, editor_comandos
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
                    contador += registrar_comando_no_editor(
                        editor_comandos, comando, origem, adicionar_log
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
                last_command_finished_at,
            ) = executar_fila_comandos(
                personagem,
                executar_movimento,
                command_in_progress,
                comando_atual,
                last_command_finished_at,
                DELAY_ENTRE_MOVIMENTOS,
                labirinto,
                tamanho_celula,
                modo_muito_facil,
                adicionar_log,
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
