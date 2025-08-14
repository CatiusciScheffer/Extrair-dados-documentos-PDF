import difflib
import cv2
import pytesseract


class UtilsServices:

  @staticmethod
  def contem_semelhante(texto, termo, limiar=0.8):
    palavras = texto.upper().split()
    for palavra in palavras:
        if difflib.SequenceMatcher(None, palavra, termo.upper()).ratio() >= limiar:
            return True
    return False
  
  @staticmethod
  def ocr_regiao(imagem, coords):
    """Executa OCR em uma região específica da imagem."""
    x1, y1, x2, y2 = min(coords[0], coords[2]), min(coords[1], coords[3]), max(coords[0], coords[2]), max(coords[1], coords[3])
    if x1 >= x2 or y1 >= y2:
        return ""
    recorte = imagem[y1:y2, x1:x2]
    gray = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    _, binarizada = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    texto = pytesseract.image_to_string(binarizada, lang='por')
    return texto.strip().replace('\n', ' ')