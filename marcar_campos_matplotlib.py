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
    """Retorna o caminho do diretório do projeto."""
    if getattr(sys, 'frozen', False):
        # Se o script estiver rodando como um executável (pyinstaller)
        return os.path.dirname(sys.executable)
    else:
        # Se estiver rodando como um script .py normal
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
print("Convertendo PDF para imagem...")
paginas = convert_from_path(caminho_pdf, dpi=300, poppler_path=POPPLER_PATH)
imagem_pil = paginas[0]
# Converte a imagem para o formato que o OpenCV usa (BGR)
imagem_opencv = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)

# === Salva a imagem original (sem marcações) ===
imagem_original_path = os.path.join(PROJECT_PATH, "imagem_a_mapear.jpg")
cv2.imwrite(imagem_original_path, imagem_opencv)
print(f"Imagem original salva como: {imagem_original_path}")

# === Inicia a marcação das coordenadas ===
# Para o matplotlib, precisamos da imagem em formato RGB
img_rgb_para_plot = cv2.cvtColor(imagem_opencv, cv2.COLOR_BGR2RGB)

fig, ax = plt.subplots(figsize=(12, 8)) # Aumenta o tamanho da janela de marcação
ax.imshow(img_rgb_para_plot)

print("\n--- Marcação de Coordenadas ---")
print("1. Clique no canto superior esquerdo da área desejada.")
print("2. Clique no canto inferior direito da mesma área.")
print("3. Digite o nome do campo no terminal e pressione Enter.")
print("Repita o processo para todos os campos.")
print("\nFeche a janela de imagem quando terminar.")

coordenadas = {}
pontos = []

def onclick(event):
    # Ignora cliques fora da área da imagem
    if event.xdata and event.ydata:
        x, y = int(event.xdata), int(event.ydata)
        pontos.append((x, y))
        
        # Desenha um pequeno círculo no ponto clicado para feedback visual
        ax.plot(x, y, 'g+', markersize=10)
        fig.canvas.draw()

        if len(pontos) == 2:
            (x1, y1), (x2, y2) = pontos
            
            # Garante que o primeiro ponto seja sempre o superior-esquerdo
            x_start, y_start = min(x1, x2), min(y1, y2)
            x_end, y_end = max(x1, x2), max(y1, y2)

            nome = input(f"Digite o nome para a área ({x_start}, {y_start}, {x_end}, {y_end}): ").strip()
            if nome:
                coordenadas[nome] = (x_start, y_start, x_end, y_end)
                # Desenha o retângulo na janela interativa
                rect = patches.Rectangle((x_start, y_start), x_end - x_start, y_end - y_start, linewidth=2, edgecolor='lime', facecolor='none')
                ax.add_patch(rect)
                ax.text(x_start, y_start - 10, nome, color='lime', fontsize=10, weight='bold')
                fig.canvas.draw()
            
            # Limpa os pontos para a próxima marcação
            pontos.clear()

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show() # Esta linha pausa o script até a janela ser fechada

# === Salva o resultado das coordenadas em JSON ===
saida_json = os.path.join(PROJECT_PATH, "coordenadas_obtidas.json")
with open(saida_json, "w", encoding="utf-8") as f:
    json.dump(coordenadas, f, indent=4)

print(f"\nCoordenadas salvas em {saida_json}:")
print(json.dumps(coordenadas, indent=4, ensure_ascii=False))


# === NOVO: Desenha as marcações na imagem usando OpenCV e salva o arquivo ===
print("\nDesenhando marcações na imagem para salvar...")
imagem_com_marcacoes = imagem_opencv.copy() # Cria uma cópia para não alterar a original

for nome, (x1, y1, x2, y2) in coordenadas.items():
    # Desenha o retângulo verde
    cv2.rectangle(imagem_com_marcacoes, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # Escreve o nome do campo um pouco acima do retângulo
    cv2.putText(imagem_com_marcacoes, nome, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

# Salva a imagem final com as anotações
imagem_mapeada_path = os.path.join(PROJECT_PATH, "imagem_final_mapeada.jpg")
cv2.imwrite(imagem_mapeada_path, imagem_com_marcacoes)

print(f"\nImagem com as marcações em verde salva em: {imagem_mapeada_path}")