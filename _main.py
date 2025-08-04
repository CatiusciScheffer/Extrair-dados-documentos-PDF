# -*- coding: utf-8 -*-
import pytesseract
from pdf2image import convert_from_path
import cv2
import json
import numpy as np
import os
import sys

def get_base_path():
    """ Obtém o caminho base para o executável ou script, essencial para o PyInstaller. """
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como um .exe (congelado pelo PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Se estiver rodando como um script .py normal
        return os.path.dirname(os.path.abspath(__file__))


def processar_cnh(caminho_pdf):
    """
    Função principal que encapsula toda a lógica de extração de dados da CNH.
    """
    try:
        # === CONFIGURAÇÃO DOS CAMINHOS DINÂMICOS ===
        BASE_PATH = get_base_path()
        TESSERACT_PATH = os.path.join(BASE_PATH, 'Tesseract-OCR', 'tesseract.exe')
        POPPLER_PATH = os.path.join(BASE_PATH, 'poppler', 'Library', 'bin')
        
        # Valida se os caminhos essenciais existem
        if not os.path.exists(TESSERACT_PATH):
            raise FileNotFoundError(f"Tesseract não encontrado em: {TESSERACT_PATH}")
        if not os.path.exists(POPPLER_PATH):
            raise FileNotFoundError(f"Poppler não encontrado em: {POPPLER_PATH}")

        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

        # === CONVERTE O PDF EM IMAGEM ===
        paginas = convert_from_path(caminho_pdf, dpi=300, poppler_path=POPPLER_PATH)
        imagem_pil = paginas[0]
        imagem = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)

        # === CARREGA AS COORDENADAS DO CABEÇALHO ===
        CAMINHO_COORD_CABECALHO = os.path.join(BASE_PATH, 'data', 'coord_cabecalho.json')
        with open(CAMINHO_COORD_CABECALHO, encoding="utf-8") as f:
            coords_cabecalho = json.load(f)

        # === FUNÇÃO OCR DE REGIÃO ===
        def ocr_regiao(imagem, coords):
            x1, y1, x2, y2 = min(coords[0], coords[2]), min(coords[1], coords[3]), max(coords[0], coords[2]), max(coords[1], coords[3])
            if x1 >= x2 or y1 >= y2:
                return ""
            recorte = imagem[y1:y2, x1:x2]
            gray = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
            _, binarizada = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            texto = pytesseract.image_to_string(binarizada, lang='por')
            return texto.strip().replace('\n', ' ') # Remove quebras de linha

        # === EXTRAI TEXTO DO CABEÇALHO E IDENTIFICA O TIPO DE CNH ===
        texto_cabecalho = ocr_regiao(imagem, coords_cabecalho["cabecalho"])
        
        if "HABILITAÇÃO" not in texto_cabecalho:
          raise FileNotFoundError(f"Documento verificado não parece ser uma CNH válida.")  
        
        if "DRIVER LICENSE" in texto_cabecalho or "PERMISO DE CONDUCCIÓN" in texto_cabecalho:
            arquivo_json_modelo = r"data\coord_cnh_nacional.json"
        elif "CNH Digital" in texto_cabecalho:
            arquivo_json_modelo = r"data\coord_cnh_digital.json"
        else:
            # Padrão para estadual se os outros não forem encontrados
            arquivo_json_modelo = r"data\coord_cnh_estadual.json"

        # === CARREGA AS COORDENADAS ESPECÍFICAS DO TIPO DETECTADO ===
        caminho_json_coords = os.path.join(BASE_PATH, arquivo_json_modelo)
        if not os.path.exists(caminho_json_coords):
            raise FileNotFoundError(f"Arquivo de coordenadas não encontrado: {caminho_json_coords}")

        with open(caminho_json_coords, encoding="utf-8") as f:
            regioes = json.load(f)

        # === EXTRAI OS DADOS DAS REGIÕES ===
        dados_extraidos = {}
        for campo, coords in regioes.items():
            dados_extraidos[campo] = ocr_regiao(imagem, coords)
        
        # Adiciona um status de sucesso
        dados_extraidos["status"] = "sucesso"
        dados_extraidos["mensagem"] = "Dados extraídos com sucesso."

        # === GERA O ARQUIVO JSON DE SAÍDA ===
        caminho_saida_json = os.path.join(BASE_PATH, 'dados_cnh.json')
        with open(caminho_saida_json, 'w', encoding='utf-8') as f_out:
            json.dump(dados_extraidos, f_out, indent=4, ensure_ascii=False)

    except Exception as e:
        # === EM CASO DE ERRO, GERA UM JSON DE ERRO ===
        BASE_PATH = get_base_path() # Garante que BASE_PATH exista
        caminho_saida_json = os.path.join(BASE_PATH, 'dados_cnh.json')
        erro_info = {
            "status": "erro",
            "mensagem": str(e)
        }
        with open(caminho_saida_json, 'w', encoding='utf-8') as f_out:
            json.dump(erro_info, f_out, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    # Verifica se o caminho do PDF foi passado como argumento
    if len(sys.argv) > 1:
        caminho_pdf_arg = sys.argv[1]
        if os.path.exists(caminho_pdf_arg):
            processar_cnh(caminho_pdf_arg)
        else:
            # Gera um JSON de erro se o arquivo não existir
            erro_info = {
                "status": "erro",
                "mensagem": f"Arquivo PDF não encontrado no caminho: {caminho_pdf_arg}"
            }
            caminho_saida_json = os.path.join(get_base_path(), 'dados_cnh.json')
            with open(caminho_saida_json, 'w', encoding='utf-8') as f_out:
                json.dump(erro_info, f_out, indent=4, ensure_ascii=False)
    else:
        # Gera um JSON de erro se nenhum argumento for passado
        erro_info = {
            "status": "erro",
            "mensagem": "Nenhum caminho de PDF foi fornecido como argumento."
        }
        caminho_saida_json = os.path.join(get_base_path(), 'dados_cnh.json')
        with open(caminho_saida_json, 'w', encoding='utf-8') as f_out:
            json.dump(erro_info, f_out, indent=4, ensure_ascii=False)