# Use uma imagem base oficial do Python correspondente à sua versão local (3.9)
FROM python:3.9-slim

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Instale o Poetry
# Recomendado fixar a versão do Poetry para builds consistentes
ARG POETRY_VERSION=1.8.3
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# Copie apenas os arquivos de definição de dependência primeiro
# Isso aproveita o cache do Docker: se esses arquivos não mudarem,
# as dependências não serão reinstaladas a cada build.
COPY pyproject.toml poetry.lock* ./

# Instale as dependências do projeto usando o poetry.lock
# --no-dev: Não instala dependências de desenvolvimento (pytest, etc.)
# --no-interaction: Não faz perguntas interativas
# --no-ansi: Desativa saída colorida (melhor para logs de build)
# --no-root: Não instala o próprio pacote medflowai ainda (faremos isso depois de copiar o código)
RUN poetry install --no-dev --no-interaction --no-ansi --no-root

# Copie o código da sua aplicação para o diretório de trabalho no container
# Atenção: Certifique-se que o contexto do build (o diretório onde você roda 'docker build')
# está correto para que este comando COPY funcione. Geralmente, você roda 'docker build'
# a partir de 'packages/libs/medflowai/'.
COPY . /app

# Agora, instale o pacote medflowai em modo editável (ou normal)
# Isso garante que os pontos de entrada definidos no pyproject.toml funcionem.
# A instalação ocorre após copiar o código para pegar a versão mais recente.
RUN poetry install --no-dev --no-interaction --no-ansi --only-root

# Exponha a porta que sua aplicação usa (se for um serviço web, ex: FastAPI)
# EXPOSE 8000 # Descomente e ajuste se necessário

# Comando para executar sua aplicação
# Ajuste conforme necessário para o ponto de entrada da sua aplicação
# Exemplo para um script principal:
# CMD ["poetry", "run", "python", "medflowai/main.py"]
# Exemplo para FastAPI com uvicorn:
# CMD ["poetry", "run", "uvicorn", "medflowai.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["echo", "Configure o comando de inicialização da sua aplicação aqui"]
