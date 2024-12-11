# Folosim o imagine Python minimă
FROM python:3.9-slim

# Setăm directorul de lucru
WORKDIR /app

# Copiem dependințele și le instalăm
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem fișierele aplicației în directorul de lucru
COPY app.py .
COPY templates/ templates/

# Expunem portul pe care va rula aplicația
EXPOSE 7000

# Comanda pentru a porni aplicația
CMD ["python", "app.py"]
