import os
import gspread
import pandas as pd
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

class PlanilhaUtils:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        credentials_path = os.getenv("GOOGLE_SHEET_CREDENTIALS_PATH")

        scope = ["https://www.googleapis.com/auth/spreadsheets"]

        # Resolve o caminho absoluto, baseado no local do main.py
        main_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.abspath(os.path.join(main_dir, credentials_path))

        print("Usando credenciais em:", full_path)

        creds = ServiceAccountCredentials.from_json_keyfile_name(full_path, scope)
        self.client = gspread.authorize(creds)

    def carregar_dados_planilha_google(self):
        worksheet = self.client.open_by_key(self.sheet_id).sheet1
        dados = worksheet.get_all_records()
        return dados

    def salvar_excel_conciliado(self, conciliados: list, nao_conciliados: list, output_path="conciliado/Conciliados.xls"):
        dados_conciliados = pd.DataFrame(conciliados)
        dados_nao_conciliados = pd.DataFrame(nao_conciliados)

        with pd.ExcelWriter(output_path) as writer:
            dados_conciliados.to_excel(writer, sheet_name="Conciliados", index=False)
            dados_nao_conciliados.to_excel(writer, sheet_name="Não Conciliados", index=False)
