import os
import gspread
import pandas as pd
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

class PlanilhaUtils:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        self.client = gspread.authorize(creds)

    def carregar_dados_planilha_google(self):
        worksheet = self.client.open_by_key(self.sheet_id).sheet1
        dados = worksheet.get_all_records()
        return dados

    def salvar_excel_conciliado(self, conciliados: list, nao_conciliados: list, output_path="conciliados/Conciliados.xls"):
        dados_conciliados = pd.DataFrame(conciliados)
        dados_nao_conciliados = pd.DataFrame(nao_conciliados)

        with pd.ExcelWriter(output_path) as writer:
            dados_conciliados.to_excel(writer, sheet_name="Conciliados", index=False)
            dados_nao_conciliados.to_excel(writer, sheet_name="Não Conciliados", index=False)
