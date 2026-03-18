# Imagem Oficial Python Leve
FROM python:3.10-slim

# Impede o Python de gerar arquivos .pyc e de fazer buffer no stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Define o nível padrão de logs para stdout/stderr do K8s
ENV LOG_LEVEL INFO

WORKDIR /app

# Copia dependências (assumindo requirements.txt)
COPY requirements.txt .

# Instala bibliotecas
RUN pip install --no-cache-dir -r requirements.txt

# Copia os códigos-fonte da aplicação
COPY core/ ./core/
COPY services/ ./services/
COPY storage/ ./storage/
COPY scripts/main_polling.py .
COPY scripts/main_backfill.py .

# Copia os scripts de execução Linux
COPY scripts/run_bot.sh .
COPY scripts/run_backfill.sh .
RUN chmod +x run_bot.sh run_backfill.sh

# Ponto de entrada padrão: Polling
CMD ["./run_bot.sh"]
