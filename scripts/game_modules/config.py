"""Configuracoes compartilhadas do jogo."""

FPS = 60
COR_TELA = (100, 103, 97)

SHOW_CAMERA = True
CAMERA_INPUT_MODE = "qr"

HSV_RANGES = {
    "amarelo": {"lower": [22, 40, 130], "upper": [36, 255, 255]},
    "azul": {"lower": [95, 20, 120], "upper": [130, 255, 255]},
    "verde": {"lower": [35, 20, 120], "upper": [90, 255, 255]},
}

SKIN_RANGE = {"lower": [0, 48, 80], "upper": [20, 255, 255]}
ROI_W = 220
ROI_H = 220
BLUR = 5
ERODE_IT = 1
DILATE_IT = 1
AREA_MIN_ON = 2600
AREA_MIN_OFF = 1800
DETECT_RECENT_LEN = 7
DETECT_MAJORITY_MIN = 4
DETECT_REFRACTORY_SEC = 0.7
DETECT_EVERY_N = 2
AREA_EARLY_EXIT_FACTOR = 2.5

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

COMANDO_POR_COR = {
    "amarelo": "LEFT",
    "azul": "RIGHT",
    "verde": "SPACE",
}

DELAY_ENTRE_MOVIMENTOS = 500

COMANDO_VERIFICADOR = "CHECK_WALL"
TECLA_VERIFICADOR = "v"
QR_VERIFICADOR_PALAVRAS = {
    "CHECK",
    "CHECK_WALL",
    "VERIFICAR",
    "VERIFICADOR",
    "PAREDE",
}
