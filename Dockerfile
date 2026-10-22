FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt pytest==8.3.3
COPY itb itb
COPY scripts scripts
COPY tests tests
COPY data data
ENV PYTHONUNBUFFERED=1
# No key is baked in. A live run needs KEYPAIR_PATH pointing at a mounted file.
CMD ["sh", "scripts/demo.sh"]
