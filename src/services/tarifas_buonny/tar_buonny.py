import os
import re
import json
import pdfplumber

class TarifasBuonny:
    """
    Classe para processar arquivos PDF de demonstrativo de serviços.
    """

    @staticmethod
    def ExtrairTarifasPDF(caminho_pdf, base_path):
        """
        Lê um arquivo PDF de demonstrativo de serviços, extrai os dados relevantes
        e salva em um arquivo JSON com um nome único no diretório de saída.

        Args:
            caminho_pdf (str): O caminho completo para o arquivo PDF de entrada.
            diretorio_saida (str): O caminho para o diretório onde o JSON será salvo.

        Returns:
            str: O caminho completo para o arquivo JSON gerado em caso de sucesso.

        Raises:
            FileNotFoundError: Se o arquivo PDF ou o diretório de saída não forem encontrados.
            Exception: Para outros erros durante o processamento do PDF.
        """
        # --- 1. Validação dos caminhos ---
        if not os.path.exists(caminho_pdf):
            raise FileNotFoundError(f"Arquivo PDF não encontrado em: {caminho_pdf}")
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"Diretório de saída não encontrado em: {base_path}")

        # --- 2. Extração de texto do PDF ---
        texto_completo_pdf = ""
        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                for page in pdf.pages:
                    texto_pagina = page.extract_text()
                    if texto_pagina:
                        texto_completo_pdf += texto_pagina + "\n"
        except Exception as e:
            raise Exception(f"Erro ao ler o arquivo PDF: {e}")

        # --- 3. Lógica de extração de dados (parsing do texto) ---
        servicos_extraidos = []
        # Regex para capturar linhas de serviço: Data, Conteúdo do Meio, Valor
        linha_servico_pattern = re.compile(r'^(\d{2}\/\d{2}\/\d{4})\s+(.+?)\s+(R\$\s*[\d,.]+)$')
        placa_pattern = re.compile(r'^[A-Z0-9]{7}$')

        for linha in texto_completo_pdf.splitlines():
            match = linha_servico_pattern.match(linha.strip())
            if not match:
                continue

            data = match.group(1)
            conteudo_meio = match.group(2).strip()
            valor = match.group(3)

            partes = conteudo_meio.split()
            nome, rg, cavalo = "N/A", "N/A", None

            # Lógica para separar nome, rg e cavalo
            indice_cavalo = -1
            for i in range(len(partes) - 1, -1, -1):
                # A placa do cavalo é um identificador confiável
                if placa_pattern.match(partes[i]):
                    cavalo = partes[i]
                    indice_cavalo = i
                    break

            if cavalo:
                # Se encontrou cavalo, o RG é a palavra anterior
                if indice_cavalo > 0:
                    rg = partes[indice_cavalo - 1]
                    nome = ' '.join(partes[:indice_cavalo - 1])
                else: # Caso raro
                    nome = ''
            else:
                # Se não tem cavalo, o RG é geralmente a penúltima palavra antes do "Tipo"
                # (o "Tipo" já foi filtrado pela regex de valor no final da linha)
                if len(partes) >= 2:
                    # Assumimos que o último item é o RG e o resto é o nome
                    rg = partes[-1]
                    nome = ' '.join(partes[:-1])
                elif len(partes) == 1:
                    rg = partes[0]
                    nome = ''
            
            servicos_extraidos.append({
                "data": data,
                "nome": nome.strip(),
                "rg": rg.strip(),
                "cavalo": cavalo,
                "valor": valor
            })

        # --- 4. Geração e salvamento do arquivo JSON ---
        if not servicos_extraidos:
            print("Aviso: Nenhum dado de serviço foi extraído do PDF.")
            return None
            
        resultado_final = {"servicos": servicos_extraidos}

        # Cria um nome de arquivo exclusivo baseado no nome do PDF
        nome_base_pdf = os.path.splitext(os.path.basename(caminho_pdf))[0]
        nome_arquivo_json = f"{nome_base_pdf}_extraido.json"
        caminho_completo_json = os.path.join(diretorio_saida, nome_arquivo_json)

        with open(caminho_completo_json, 'w', encoding='utf-8') as f:
            json.dump(resultado_final, f, indent=2, ensure_ascii=False)

        return caminho_completo_json

