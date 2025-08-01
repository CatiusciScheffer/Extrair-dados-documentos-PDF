import pytesseract
from pdf2image import convert_from_path
import cv2
import json
import numpy as np
import os
import sys

# === CONFIGURAÇÃO DOS CAMINHOS ===
caminho_pdf = r"C:/Users/cpcsc/Downloads/documentos_teste/documentos/cnh_9.pdf"

def get_project_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

PROJECT_PATH = get_project_path()
TESSERACT_PATH = os.path.join(PROJECT_PATH, 'Tesseract-OCR', 'tesseract.exe')
POPPLER_PATH = os.path.join(PROJECT_PATH, r'poppler\Library\bin')
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# === CONVERTE O PDF EM IMAGEM ===
paginas = convert_from_path(caminho_pdf, dpi=300, poppler_path=POPPLER_PATH)
imagem_pil = paginas[0]
imagem = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)

# === CARREGA AS COORDENADAS DO CABEÇALHO ===
CAMINHO_COORD_CABECALHO = os.path.join(PROJECT_PATH, r"data\coord_cabecalho.json")

with open(CAMINHO_COORD_CABECALHO, encoding="utf-8") as f:
    coords_cabecalho = json.load(f)

# === FUNÇÃO OCR DE REGIÃO ===
def ocr_regiao(imagem, coords):
    x1, y1, x2, y2 = min(coords[0], coords[2]), min(coords[1], coords[3]), max(coords[0], coords[2]), max(coords[1], coords[3])
    if x1 == x2 or y1 == y2:
        return ""
    recorte = imagem[y1:y2, x1:x2]
    gray = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    _, binarizada = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    texto = pytesseract.image_to_string(binarizada, lang='por')
    return texto.strip()

# === EXTRAI TEXTO DO CABEÇALHO ===
texto_cabecalho = ocr_regiao(imagem, coords_cabecalho["cabecalho"])

# === IDENTIFICA O TIPO DE CNH ===
if "DRIVER LICENSE" in texto_cabecalho or "PERMISO DE CONDUCCIÓN" in texto_cabecalho:
    arquivo_json = r"data\coord_cnh_nacional.json"
elif "CNH Digital" in texto_cabecalho:
    arquivo_json = r"data\coord_cnh_digital.json"
else:
    arquivo_json = r"data\coord_cnh_estadual.json"

# === CARREGA AS COORDENADAS ESPECÍFICAS DO TIPO DETECTADO ===
caminho_json_coords = os.path.join(PROJECT_PATH, arquivo_json)

if not os.path.exists(caminho_json_coords):
    raise FileNotFoundError(f"Arquivo de coordenadas não encontrado: {arquivo_json}")

with open(caminho_json_coords, encoding="utf-8") as f:
    regioes = json.load(f)

# === MOSTRA VISUALMENTE OS CAMPOS (opcional) ===
imagem_com_caixas = imagem.copy()
for campo, (x1, y1, x2, y2) in regioes.items():
    cv2.rectangle(imagem_com_caixas, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(imagem_com_caixas, campo, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

cv2.imwrite("validacao_cnh.jpg", imagem_com_caixas)
print("Imagem de validação salva como: validacao_cnh.jpg")

# === EXTRAI OS DADOS DAS REGIÕES ===
dados_extraidos = {}
for campo, coords in regioes.items():
    dados_extraidos[campo] = ocr_regiao(imagem, coords)

# === IMPRIME OS DADOS EXTRAÍDOS EM FORMATO JSON ===
print(json.dumps(dados_extraidos, indent=4, ensure_ascii=False))
