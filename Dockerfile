FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install -r requirements.lock.txt
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .
COPY app.py ./
COPY .streamlit ./.streamlit
COPY data/raw ./data/raw
COPY data/support_cases ./data/support_cases
RUN useradd --create-home --uid 10001 verithra && mkdir -p data/index data/cache && chown -R verithra:verithra /app
USER verithra
EXPOSE 8501
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
