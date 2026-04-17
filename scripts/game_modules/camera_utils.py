"""Deteccao de cores e QR, alem do estado de leitura da camera."""

import time
from collections import Counter, deque

import cv2
import numpy as np

from game_modules.config import (
    AREA_EARLY_EXIT_FACTOR,
    AREA_MIN_OFF,
    AREA_MIN_ON,
    BLUR,
    CAMERA_INPUT_MODE,
    COMANDO_POR_COR,
    DETECT_EVERY_N,
    DETECT_MAJORITY_MIN,
    DETECT_RECENT_LEN,
    DETECT_REFRACTORY_SEC,
    DILATE_IT,
    ERODE_IT,
    HSV_RANGES,
    QR_COMMAND_MAP,
    ROI_H,
    ROI_W,
    SHOW_CAMERA,
    SKIN_RANGE,
)


def detectar_cor(camera):
    """Detecta uma das cores configuradas no centro do frame da camera."""
    ret, frame = camera.read()
    if not ret:
        return None, None

    altura, largura, _ = frame.shape
    w = int(ROI_W)
    h = int(ROI_H)

    centro_x = largura // 2
    centro_y = altura // 2
    x1 = centro_x - w // 2
    y1 = centro_y - h // 2
    x2 = centro_x + w // 2
    y2 = centro_y + h // 2

    roi = frame[y1:y2, x1:x2]
    proc = roi.copy()
    blur_k = int(BLUR)
    if blur_k and blur_k % 2 == 1 and blur_k >= 3:
        proc = cv2.GaussianBlur(proc, (blur_k, blur_k), 0)
    hsv = cv2.cvtColor(proc, cv2.COLOR_BGR2HSV)

    erode_it = int(ERODE_IT)
    dilate_it = int(DILATE_IT)
    lower_skin = np.array(SKIN_RANGE.get("lower", [0, 0, 0]))
    upper_skin = np.array(SKIN_RANGE.get("upper", [0, 0, 0]))
    skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

    best_cor = None
    best_area = 0
    early_exit_threshold = AREA_MIN_ON * AREA_EARLY_EXIT_FACTOR

    cores = list(HSV_RANGES.items())
    for i, (cor, rng) in enumerate(cores):
        lower_np = np.array(rng.get("lower", [0, 0, 0]))
        upper_np = np.array(rng.get("upper", [179, 255, 255]))

        mask = cv2.inRange(hsv, lower_np, upper_np)
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
            if best_area >= early_exit_threshold and i < len(cores) - 1:
                break

    if best_area >= AREA_MIN_ON:
        cor_final = best_cor
    elif best_area >= AREA_MIN_OFF and best_cor is not None:
        cor_final = best_cor
    else:
        cor_final = None

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
    return cor_final, frame


def normalizar_qr(data):
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
            if not data or not data.strip():
                continue

            comando = normalizar_qr(data)
            if not comando:
                continue

            origem = data.strip()
            if points is not None and len(points) > idx:
                pts = np.int32(points[idx]).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, (0, 255, 255), 3)
                x, y = pts[0][0]
                cv2.putText(
                    frame,
                    origem,
                    (x, max(30, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2,
                )
            return comando, frame, origem

    return None, frame, None


def detectar_comando_camera(camera, qr_detector=None):
    if CAMERA_INPUT_MODE == "qr":
        return detectar_qr(camera, qr_detector)

    cor_detectada, frame = detectar_cor(camera)
    comando = COMANDO_POR_COR.get(cor_detectada)
    if comando:
        return comando, frame, cor_detectada
    return None, frame, None


def descrever_comando_camera(comando, origem):
    origem_txt = (origem or comando or "CAMERA").upper()
    if comando == "LEFT":
        return f"Detectado: {origem_txt} -> ESQUERDA"
    if comando == "RIGHT":
        return f"Detectado: {origem_txt} -> DIREITA"
    if comando == "SPACE":
        return f"Detectado: {origem_txt} -> FRENTE"
    return f"Detectado: {origem_txt}"


def criar_estado_camera():
    return {
        "recentes": deque(maxlen=DETECT_RECENT_LEN),
        "ultimo_disparo": 0.0,
        "ultimo_token_camera": None,
        "qr_detector": cv2.QRCodeDetector() if CAMERA_INPUT_MODE == "qr" else None,
        "frame": None,
        "frame_count": 0,
    }


def processar_entrada_camera(estado_camera, camera, camera_ok):
    estado_camera["frame_count"] += 1
    detection_run = (estado_camera["frame_count"] % DETECT_EVERY_N == 0)
    if not camera_ok or not detection_run:
        return None, None

    comando, frame, origem = detectar_comando_camera(camera, estado_camera["qr_detector"])
    estado_camera["frame"] = frame
    return comando, origem


def coletar_comandos_por_cor(estado_camera, origem_camera, tempo_atual):
    recentes = estado_camera["recentes"]
    recentes.append(origem_camera if origem_camera else "_")

    if tempo_atual - estado_camera["ultimo_disparo"] < DETECT_REFRACTORY_SEC:
        return []
    if len(recentes) != DETECT_RECENT_LEN:
        return []

    contagem = Counter([cor for cor in recentes if cor != "_"])
    if not contagem:
        return []

    cor_maj, votos = contagem.most_common(1)[0]
    if votos < DETECT_MAJORITY_MIN:
        return []

    comando = COMANDO_POR_COR.get(cor_maj)
    if not comando:
        return []

    estado_camera["ultimo_disparo"] = tempo_atual
    return [(comando, cor_maj)]


def coletar_comandos_camera(estado_camera, comando_camera, origem_camera):
    tempo_atual = time.time()

    if CAMERA_INPUT_MODE == "qr":
        if not comando_camera:
            estado_camera["ultimo_token_camera"] = None
            return []

        token_camera = f"{origem_camera}|{comando_camera}"
        if (
            token_camera != estado_camera["ultimo_token_camera"]
            and tempo_atual - estado_camera["ultimo_disparo"] >= DETECT_REFRACTORY_SEC
        ):
            estado_camera["ultimo_disparo"] = tempo_atual
            estado_camera["ultimo_token_camera"] = token_camera
            return [(comando_camera, origem_camera)]

        estado_camera["ultimo_token_camera"] = token_camera
        return []

    return coletar_comandos_por_cor(estado_camera, origem_camera, tempo_atual)


def abrir_camera():
    camera = cv2.VideoCapture(0)
    camera_ok = camera.isOpened()
    if SHOW_CAMERA and camera_ok:
        try:
            cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
        except Exception:
            pass
    if camera_ok:
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera, camera_ok


def mostrar_camera(frame):
    if SHOW_CAMERA and frame is not None:
        cv2.imshow("Camera", frame)
        cv2.waitKey(1)
