# import matplotlib.pyplot as plt
# import matplotlib.patches as patches
# import cv2
# import json

# imagem_path = "validacao_cnh.jpg"
# img = cv2.imread(imagem_path)
# img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# fig, ax = plt.subplots()
# ax.imshow(img_rgb)

# print("Clique com o mouse em dois pontos (canto superior esquerdo e inferior direito)")
# print("Depois digite o nome do campo no terminal")
# print("Pressione ESC para sair ou feche a janela quando terminar")

# coordenadas = {}
# pontos = []

# def onclick(event):
#     if event.xdata and event.ydata:
#         x, y = int(event.xdata), int(event.ydata)
#         pontos.append((x, y))

#         if len(pontos) == 2:
#             (x1, y1), (x2, y2) = pontos
#             nome = input(f"Campo para área ({x1}, {y1}, {x2}, {y2}): ").strip()
#             if nome:
#                 coordenadas[nome] = (x1, y1, x2, y2)
#                 # desenha o retângulo
#                 rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor='lime', facecolor='none')
#                 ax.add_patch(rect)
#                 ax.text(x1, y1 - 5, nome, color='lime', fontsize=10, weight='bold')
#                 fig.canvas.draw()
#             pontos.clear()

# cid = fig.canvas.mpl_connect('button_press_event', onclick)
# plt.show()

# # Salvar resultado
# with open("coordenadas_obtidas.json", "w") as f:
#     json.dump(coordenadas, f, indent=4)

# print("\nCoordenadas salvas em coordenadas_cnh.json:")
# print(json.dumps(coordenadas, indent=4))

import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
import os
import sys
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from tkinter import Tk, filedialog

# === Funções auxiliares ===

def get_project_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# === Seleciona o PDF via caixa de diálogo ===
Tk().withdraw()  # Oculta a janela principal do tkinter
caminho_pdf = filedialog.askopenfilename(
    title="Selecione o arquivo PDF da CNH",
    filetypes=[("Arquivos PDF", "*.pdf")]
)

if not caminho_pdf:
    print("Nenhum arquivo selecionado.")
    sys.exit()

# === Define caminhos do projeto ===
PROJECT_PATH = get_project_path()
TESSERACT_PATH = os.path.join(PROJECT_PATH, 'Tesseract-OCR', 'tesseract.exe')
POPPLER_PATH = os.path.join(PROJECT_PATH, r'poppler\Library\bin')
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# === Converte a primeira página do PDF em imagem ===
paginas = convert_from_path(caminho_pdf, dpi=300, poppler_path=POPPLER_PATH)
imagem_pil = paginas[0]
imagem = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)

# === Salva a imagem ===
imagem_path = os.path.join(PROJECT_PATH, "imagem_a_mapear.jpg")
cv2.imwrite(imagem_path, imagem)
print(f"Imagem salva como: {imagem_path}")

# === Inicia a marcação das coordenadas ===
img = cv2.imread(imagem_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

fig, ax = plt.subplots()
ax.imshow(img_rgb)

print("\n--- Marcação de coordenadas ---")
print("Clique com o mouse em dois pontos (canto superior esquerdo e inferior direito)")
print("Depois digite o nome do campo no terminal")
print("Pressione ESC ou feche a janela quando terminar")

coordenadas = {}
pontos = []

def onclick(event):
    if event.xdata and event.ydata:
        x, y = int(event.xdata), int(event.ydata)
        pontos.append((x, y))

        if len(pontos) == 2:
            (x1, y1), (x2, y2) = pontos
            nome = input(f"Campo para área ({x1}, {y1}, {x2}, {y2}): ").strip()
            if nome:
                coordenadas[nome] = (x1, y1, x2, y2)
                # desenha o retângulo
                rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor='lime', facecolor='none')
                ax.add_patch(rect)
                ax.text(x1, y1 - 5, nome, color='lime', fontsize=10, weight='bold')
                fig.canvas.draw()
            pontos.clear()

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()

# === Salvar resultado ===
saida_json = os.path.join(PROJECT_PATH, "coordenadas_obtidas.json")
with open(saida_json, "w", encoding="utf-8") as f:
    json.dump(coordenadas, f, indent=4)

print(f"\nCoordenadas salvas em {saida_json}:")
print(json.dumps(coordenadas, indent=4, ensure_ascii=False))
