import sys
import os
import json
import difflib
import uuid
import tempfile
import numpy as np
import cv2
import pytesseract
from pdf2image import convert_from_path

# =============================================================================
# 1. CONFIGURAÇÃO E FUNÇÕES AUXILIARES (HELPERS)
# =============================================================================

def get_base_path():
    """Obtém o caminho base para o executável ou script (essencial para o PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_temp_output_path():
    """Cria um caminho de arquivo de saída único na pasta temporária do sistema."""
    # Gera um nome de arquivo único para evitar conflitos entre usuários
    unique_filename = f"dados_{uuid.uuid4()}.json"
    return os.path.join(tempfile.gettempdir(), unique_filename)

def write_json_output(data, output_path):
    """Escreve o dicionário de dados em um arquivo JSON de saída."""
    with open(output_path, 'w', encoding='utf-8') as f_out:
        json.dump(data, f_out, indent=4, ensure_ascii=False)

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

def contem_semelhante(texto, termo, limiar=0.8):
    palavras = texto.upper().split()
    for palavra in palavras:
        if difflib.SequenceMatcher(None, palavra, termo.upper()).ratio() >= limiar:
            return True
    return False

# =============================================================================
# 2. PROCESSADORES DE DOCUMENTOS
# =============================================================================

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

    texto_cabecalho = ocr_regiao(imagem, coords_cabecalho["cabecalho"])
    
    texto_upper = texto_cabecalho.upper()

    if not contem_semelhante(texto_upper, "HABILITAÇÃO") and "CNH DIGITAL" not in texto_upper:
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
        dados_extraidos[campo] = ocr_regiao(imagem, coords)
    
    dados_extraidos["status"] = "sucesso"
    dados_extraidos["mensagem"] = "Dados da CNH extraídos com sucesso."
    
    return dados_extraidos

def processar_crlv(caminho_pdf, base_path):
    """
    Encapsula toda a lógica de extração de dados da CRLV.
    Retorna um dicionário com os dados extraídos ou com informações de erro.
    """
    # --- Configuração de caminhos específicos
    tesseract_path = os.path.join(base_path, 'Tesseract-OCR', 'tesseract.exe')
    poppler_path = os.path.join(base_path, 'poppler', 'Library', 'bin')
    
    if not os.path.exists(tesseract_path) or not os.path.exists(poppler_path):
        raise FileNotFoundError("Dependências (Tesseract ou Poppler) não encontradas.")
        
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

    # --- Conversão de PDF para Imagem ---
    paginas = convert_from_path(caminho_pdf, dpi=300, poppler_path=poppler_path)
    imagem_pil = paginas[0]
    imagem = cv2.cvtColor(np.array(imagem_pil), cv2.COLOR_RGB2BGR)

    # --- Identificação do Modelo dO CRLV ---
    coord_cabecalho_path = os.path.join(base_path, 'data', 'coord_cabecalho_crlv.json')
    if not os.path.exists(coord_cabecalho_path):
        raise FileNotFoundError(f"Arquivo de coordenadas do cabeçalho não encontrado: {coord_cabecalho_path}")

    with open(coord_cabecalho_path, encoding="utf-8") as f:
        coords_cabecalho = json.load(f)

    texto_cabecalho = ocr_regiao(imagem, coords_cabecalho["cabecalho"])
    
    if "LICENCIAMENTO DE VEÍCULO" not in texto_cabecalho.upper():
        raise ValueError("Documento não parece ser uma CRLV válido (cabeçalho não corresponde).")
    
    arquivo_json_modelo = r"data\coord_crlv.json"

    # --- Extração dos Dados ---
    caminho_json_coords = os.path.join(base_path, arquivo_json_modelo)
    if not os.path.exists(caminho_json_coords):
        raise FileNotFoundError(f"Arquivo de coordenadas do modelo não encontrado: {caminho_json_coords}")

    with open(caminho_json_coords, encoding="utf-8") as f:
        regioes = json.load(f)

    dados_extraidos = {}
    for campo, coords in regioes.items():
        dados_extraidos[campo] = ocr_regiao(imagem, coords)
    
    dados_extraidos["status"] = "sucesso"
    dados_extraidos["mensagem"] = "Dados do CRLV extraídos com sucesso."
    
    return dados_extraidos


# =============================================================================
# 3. BLOCO PRINCIPAL (ORQUESTRADOR)
# =============================================================================

if __name__ == '__main__':
    
    # Garante que o caminho de saída seja definido mesmo em caso de erro inicial
    output_path = get_temp_output_path()
    
    try:
        # --- Validação dos Argumentos de Linha de Comando ---
        if len(sys.argv) != 3:
            raise ValueError("Uso incorreto. É necessário fornecer 2 argumentos: TIPO_DOCUMENTO e CAMINHO_PDF")

        doc_type = sys.argv[1].upper()
        caminho_pdf_arg = sys.argv[2]
        # Debug
        # doc_type = "CNH"
        # caminho_pdf_arg = r"C:\Users\cpcsc\Downloads\documentos_teste\documentos\cnh_0.pdf"
        
        if not os.path.exists(caminho_pdf_arg):
            raise FileNotFoundError(f"Arquivo PDF não encontrado no caminho: {caminho_pdf_arg}")

        # --- Obtenção dos Caminhos Base ---
        BASE_PATH = get_base_path()
        
        # --- Dicionário de Processadores ---
        # Mapeia o argumento de tipo de documento para a função correspondente
        PROCESSADORES = {
            "CNH": processar_cnh,
            "CRLV": processar_crlv 
        }
        

        # --- Despacho para a Função Correta ---
        if doc_type in PROCESSADORES:
            funcao_processadora = PROCESSADORES[doc_type]
            # Chama a função específica do documento
            dados_finais = funcao_processadora(caminho_pdf_arg, BASE_PATH)
        else:
            raise ValueError(f"Tipo de documento desconhecido: '{doc_type}'. Tipos suportados: {list(PROCESSADORES.keys())}")

        # --- Escrita do JSON de Sucesso ---
        write_json_output(dados_finais, output_path)

    except Exception as e:
        # --- Tratamento Centralizado de Erros ---
        # Qualquer exceção lançada durante o processo será capturada aqui.
        erro_info = {
            "status": "erro",
            "mensagem": str(e)
        }
        # Escreve o arquivo JSON com a mensagem de erro
        write_json_output(erro_info, output_path)
    
    finally:
        # --- Retorno para a Aplicação Delphi ---
        # Imprime o caminho completo do arquivo de saída (seja sucesso ou erro).
        # A aplicação Delphi deve capturar este output.
        print(output_path)