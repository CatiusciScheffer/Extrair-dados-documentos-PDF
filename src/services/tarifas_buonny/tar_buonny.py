import os
import re
import pdfplumber

class TarifasBuonny:
    """
    Classe para processar arquivos PDF de demonstrativo de serviços da Buonny.
    """

    @staticmethod
    def ExtrairTarifasPDF(caminho_pdf, base_path):
        """
        Lê um arquivo PDF de demonstrativo de serviços, extrai os dados relevantes
        e retorna um dicionário com os dados. (Versão com lógica de parsing aprimorada)
        """
        # --- 1. Validação do caminho do PDF ---
        if not os.path.exists(caminho_pdf):
            raise FileNotFoundError(f"Arquivo PDF não encontrado em: {caminho_pdf}")

        # --- 2. Extração de texto do PDF ---
        texto_completo_pdf = ""
        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                for page in pdf.pages:
                    texto_pagina = page.extract_text(x_tolerance=2, y_tolerance=2) # Tolera pequenos desvios de alinhamento
                    if texto_pagina:
                        texto_completo_pdf += texto_pagina + "\n"
        except Exception as e:
            raise Exception(f"Erro ao ler o arquivo PDF: {e}")

        # --- 3. Lógica de extração de dados (parsing do texto) ---
        servicos_extraidos = []
        linha_servico_pattern = re.compile(r'^(\d{2}\/\d{2}\/\d{4})\s+(.+?)\s+(R\$\s*[\d,.]+)$')
        # Placa de veículo (padrão Mercosul e anterior)
        placa_pattern = re.compile(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$')

        for linha in texto_completo_pdf.splitlines():
            match = linha_servico_pattern.match(linha.strip())
            if not match:
                continue

            data = match.group(1)
            conteudo_meio = match.group(2).strip()
            valor = match.group(3)

            partes = conteudo_meio.split()

            # --- NOVA LÓGICA DE PARSING (DA DIREITA PARA A ESQUERDA) ---
            
            # Inicializa as variáveis
            nome, rg, cavalo, carreta, tipo = "N/A", "N/A", None, None, None

            # O último item é quase sempre o "Tipo" (AGREGADO, CARRETEIRO, etc.)
            if partes:
                tipo = partes.pop() # Remove e armazena o tipo

            # O novo último item pode ser a 'Carreta'. Se for uma placa, assume e remove.
            if partes and placa_pattern.match(partes[-1]):
                carreta = partes.pop()

            # O novo último item pode ser o 'Cavalo'. Se for uma placa, assume e remove.
            if partes and placa_pattern.match(partes[-1]):
                cavalo = partes.pop()

            # O novo último item deve ser o 'RG'. Assume e remove.
            if partes:
                rg = partes.pop()
            
            # Tudo o que sobrou na lista de 'partes' pertence ao nome.
            nome = ' '.join(partes)

            # Lógica de fallback: se não encontrou um cavalo, mas a carreta sim,
            # significa que a única placa era do cavalo.
            if not cavalo and carreta:
                cavalo = carreta
                carreta = None

            servicos_extraidos.append({
                "data": data,
                "nome": nome.strip(),
                "rg": rg.strip(),
                "cavalo": cavalo,
                "valor": valor
            })

        # --- 4. Geração do dicionário de retorno ---
        if not servicos_extraidos:
            raise ValueError("Nenhum dado de serviço foi encontrado no documento PDF.")
            
        dados_finais = {
            "status": "sucesso",
            "mensagem": "Dados das tarifas extraídos com sucesso.",
            "servicos": servicos_extraidos
        }
        
        return dados_finais

