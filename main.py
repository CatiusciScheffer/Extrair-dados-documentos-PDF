import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.utils.utils import Utils
from src.services.cnh.cnh import CNH
from src.services.crlv.crlv import CRLV
from src.services.tarifas_buonny.tar_buonny import TarifasBuonny



if __name__ == '__main__':
    
    # Garante que o caminho de saída seja definido mesmo em caso de erro inicial
    output_path = Utils.get_temp_output_path()
    
    try:
        # --- Validação dos Argumentos de Linha de Comando ---
        if len(sys.argv) != 3:
            raise ValueError("Uso incorreto. É necessário fornecer 2 argumentos: TIPO_DOCUMENTO e CAMINHO_PDF")

        doc_type = sys.argv[1].upper()
        caminho_pdf_arg = sys.argv[2]
        #Debug
        # doc_type = "CNH"
        # caminho_pdf_arg = r"C:\Users\cpcsc\Downloads\documentos_teste\documentos\CNH_0.pdf"
        
        if not os.path.exists(caminho_pdf_arg):
            raise FileNotFoundError(f"Arquivo PDF não encontrado no caminho: {caminho_pdf_arg}")

        # --- Obtenção dos Caminhos Base ---
        BASE_PATH = Utils.get_base_path()
        
        # --- Dicionário de Processadores ---
        PROCESSADORES = {
            "CNH": CNH.processar_cnh,
            "CRLV": CRLV.processar_crlv,
            "TARIFAS_BUONNY": TarifasBuonny.ExtrairTarifasPDF 
        }
        

        # --- Despacho para a Função Correta ---
        if doc_type in PROCESSADORES:
            funcao_processadora = PROCESSADORES[doc_type]
            # Chama a função específica do documento
            dados_finais = funcao_processadora(caminho_pdf_arg, BASE_PATH)
        else:
            raise ValueError(f"Tipo de documento desconhecido: '{doc_type}'. Tipos suportados: {list(PROCESSADORES.keys())}")

        # --- Escrita do JSON de Sucesso ---
        Utils.write_json_output(dados_finais, output_path)

    except Exception as e:
        # --- Tratamento Centralizado de Erros ---
        # Qualquer exceção lançada durante o processo será capturada aqui.
        erro_info = {
            "status": "erro",
            "mensagem": str(e)
        }
        # Escreve o arquivo JSON com a mensagem de erro
        Utils.write_json_output(erro_info, output_path)
    
    finally:
        # --- Retorno para a Aplicação Delphi ---
        # Imprime o caminho completo do arquivo de saída (seja sucesso ou erro).
        # A aplicação Delphi deve capturar este output.
        print(output_path)