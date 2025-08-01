import matplotlib.pyplot as plt
import matplotlib.patches as patches
import cv2
import json

imagem_path = "validacao_cnh.jpg"
img = cv2.imread(imagem_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

fig, ax = plt.subplots()
ax.imshow(img_rgb)

print("Clique com o mouse em dois pontos (canto superior esquerdo e inferior direito)")
print("Depois digite o nome do campo no terminal")
print("Pressione ESC para sair ou feche a janela quando terminar")

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

# Salvar resultado
with open("coordenadas_obtidas.json", "w") as f:
    json.dump(coordenadas, f, indent=4)

print("\nCoordenadas salvas em coordenadas_cnh.json:")
print(json.dumps(coordenadas, indent=4))
