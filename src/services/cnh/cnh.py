import cv2
import pytesseract
import os, sys
import json
import numpy as np
from pdf2image import convert_from_path
from src.services.utils.utils_services import UtilsServices



class CNH:

  @staticmethod
  def processar_cnh(caminho_pdf, base_path):
      """
      Encapsula toda a lógica de extração de dados da CNH.
      Retorna um dicionário com os dados extraídos ou com informações de erro.
      """
      # --- Configuração de caminhos específicos da CNH ---
      tesseract_path = os.path.join(base_path, 'Tesseract-OCR', 'tesseract.exe')
      poppler_path = os.path.join(base_path, 'poppler', 'Library', 'bin')     
            
      if not os.path.exists(tesseract_path) or not os.path.exists(poppler_path):
          raise FileNotFoundError("Dependências (Tesseract ou Poppler) não encontradas.")
          
      pytesseract.pytesseract.tesseract_cmd = tesseract_path

      # --- Conversão de PDF para Imagem ---
      paginas = convert_from_path(caminho_pdf, dpi=300, poppler_path=poppler_path)
      imagem_pil = paginas[0]
      imagem = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)

      # --- Identificação do Modelo da CNH (Nacional, Digital, etc.) ---
      coord_cabecalho_path = os.path.join(base_path, 'data', 'coord_cabecalho_cnh.json')
      if not os.path.exists(coord_cabecalho_path):
          raise FileNotFoundError(f"Arquivo de coordenadas do cabeçalho não encontrado: {coord_cabecalho_path}")

      with open(coord_cabecalho_path, encoding="utf-8") as f:
          coords_cabecalho = json.load(f)

      texto_cabecalho = UtilsServices.ocr_regiao(imagem, coords_cabecalho["cabecalho"])
      
      texto_upper = texto_cabecalho.upper()

      if not UtilsServices.contem_semelhante(texto_upper, "HABILITAÇÃO") and "CNH DIGITAL" not in texto_upper:
          raise ValueError("Documento não parece ser uma CNH válida (cabeçalho não corresponde).")

      
      # --- Seleção do JSON de coordenadas apropriado ---
      if "DRIVER LICENSE" in texto_upper or "PERMISO DE CONDUCCIÓN" in texto_upper:
          arquivo_json_modelo = r"data\coord_cnh_nacional.json"
      elif "CNH DIGITAL" in texto_upper:
          if "NC" not in texto_upper:
              arquivo_json_modelo = r"data\coord_cnh_antiga.json"
          else:
              arquivo_json_modelo = r"data\coord_cnh_digital.json"    
      else:
          arquivo_json_modelo = r"data\coord_cnh_estadual.json"

      # --- Extração dos Dados ---
      caminho_json_coords = os.path.join(base_path, arquivo_json_modelo)
      if not os.path.exists(caminho_json_coords):
          raise FileNotFoundError(f"Arquivo de coordenadas do modelo não encontrado: {caminho_json_coords}")

      with open(caminho_json_coords, encoding="utf-8") as f:
          regioes = json.load(f)

      dados_extraidos = {}
      for campo, coords in regioes.items():
          dados_extraidos[campo] = UtilsServices.ocr_regiao(imagem, coords)
      
      dados_extraidos["status"] = "sucesso"
      dados_extraidos["mensagem"] = "Dados da CNH extraídos com sucesso."
      
      return dados_extraidos