# 📊 Projeto de Conciliação Bancária com Google Sheets e CSV

Este projeto em Python realiza a conciliação entre uma planilha do Google Sheets (com informações de pagamento) e arquivos CSV de extrato bancário. O resultado da conciliação é exportado para um arquivo Excel chamado `Conciliados.xls`, dentro da pasta `conciliados`.

## ✅ Funcionalidades

- 📥 Acessa a planilha do Google Sheets usando API do Google.
- 📄 Lê todos os arquivos `.csv` de uma pasta chamada `extrato-bancario`.
- 🤝 Compara as informações do extrato com os dados do Google Sheets.
- ✅ Detecta entradas conciliadas (por nome e valor).
- 🧾 Gera um arquivo `Conciliados.xls` com as colunas:
  - `NOME COMPLETO` (planilha)
  - `@ DO INSTAGRAM` (planilha)
  - `NOME DO PAGADOR:` (planilha)
  - `VALOR PAGO:` (planilha)
  - `DETALHES DO PAGAMENTO` (planilha)
- 🚫 Evita duplicidade: considera o par `NOME COMPLETO` + `@ DO INSTAGRAM` para identificar registros únicos já conciliados.

## 📁 Estrutura do Projeto

```
project-root/
│
├── applications/
│   ├── src/
│   │   ├── main.py
│   │   ├── conciliador.py
│   │   ├── planilha_utils.py
│   │   ├── gerar_excel.py
│   │   └── models/
│   │       └── extrato.py
│
├── extrato-bancario/         # CSVs com extratos bancários
├── conciliados/              # Excel gerado com conciliações
├── credentials/              # Contém o arquivo credentials.json
├── .env                      # Variáveis de ambiente
├── requirements.txt          # Dependências do projeto
├── Makefile                  # Automação de tarefas
└── run.bat                   # Executável para Windows
```

## 🔐 Configuração do Ambiente

### 1. Crie o `.env`

Crie um arquivo `.env` com o seguinte conteúdo:

```
GOOGLE_CREDENTIALS_PATH=credentials/credentials.json
GOOGLE_SHEET_ID=SEU_ID_DA_PLANILHA
```

- Substitua `SEU_ID_DA_PLANILHA` pelo ID da sua planilha do Google (aquele trecho entre `/d/` e `/edit` na URL).
- O caminho para o `credentials.json` pode ser relativo (como acima).

### 2. Credenciais do Google Sheets

1. Acesse o [console do Google Cloud](https://console.cloud.google.com/).
2. Crie um projeto e habilite a API do Google Sheets e Google Drive.
3. Crie uma conta de serviço.
4. Baixe o arquivo `credentials.json` e coloque na pasta `credentials/`.
5. Compartilhe sua planilha com o e-mail da conta de serviço (como **Editor**).

## ▶️ Como Executar

### No Windows:

```
run.bat
```

### Com Makefile:

```
make run
```

### Para gerar o executável:

```
make deploy
```

> O executável será salvo na pasta `dist/` com todas as dependências incluídas.

## 📦 Requisitos

Instale as dependências com:

```
pip install -r requirements.txt
```

Ou use o ambiente virtual com:

```
python -m venv venv
venv\Scripts\activate  # No Windows
source venv/bin/activate  # No Linux/macOS
```

## ❓ Dúvidas Frequentes

**🧩 Como saber o ID da planilha?**  
Pegue na URL do Google Sheets:  
`https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit#gid=0`

**📄 O arquivo `.env` é obrigatório?**  
Sim. O programa não roda sem ele. Se ele não for encontrado, o script lançará um erro.

**🔒 Preciso de conta no Google Cloud?**  
Sim, para obter credenciais de API e autorizar o acesso ao Google Sheets.

## 🛠️ Autor e Licença

Desenvolvido com ❤️ para fins de automação e organização.

Licença: MIT
