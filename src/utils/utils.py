import json
import sys, os
import tempfile
import uuid

class Utils:
  
  @staticmethod
  def write_json_output(data, output_path):
      """Escreve o dicionário de dados em um arquivo JSON de saída."""
      with open(output_path, 'w', encoding='utf-8') as f_out:
          json.dump(data, f_out, indent=4, ensure_ascii=False)
          
  @staticmethod 
  def get_base_path():
      """
      Obtém o caminho raiz do projeto, funcionando tanto para script quanto para executável PyInstaller.
      """
      if getattr(sys, 'frozen', False):
          return os.path.dirname(sys.executable)
      else:
          # __file__ -> .../src/utils/utils.py
          # dirname  -> .../src/utils
          # dirname  -> .../src
          # dirname  -> .../ (Raiz do projeto)
          return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
      
  @staticmethod    
  def get_temp_output_path():
    """Cria um caminho de arquivo de saída único na pasta temporária do sistema."""
    # Gera um nome de arquivo único para evitar conflitos entre usuários
    unique_filename = f"dados_{uuid.uuid4()}.json"
    return os.path.join(tempfile.gettempdir(), unique_filename)      