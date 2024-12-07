# Autores:

---

\*Felipe Galvão Lagares

\*Hailton David Lemos

\*Raphael Abenom dos Santos Silva

# Guia de Instalação da Aplicação

Este guia irá ajudá-lo a configurar e executar a aplicação.

## Pré-requisitos

- Python 3.9 ou superior
- pip (Gerenciador de pacotes Python)

## Passos para Instalação

1. Clone o repositório ou baixe o código fonte:

```bash
git clone <url-do-repositorio>
cd <diretorio-do-projeto>
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # Para Linux/Mac
venv\Scripts\activate  # Para Windows
```

3. Instale as dependências necessárias:

Primeira etapa:
```bash
pip install -r requirements.txt
```
Segunda etapa:
```bash
guardrails configure
```
Necessário a api-key do guardrails

Terceira etapa:
```bash
guardrails hub install hub://tryolabs/restricttotopic
```

Isso instalará:
- streamlit - Para criar aplicações web
- openai - Para integração com a API OpenAI
- guardrails-ai - Para proteções de segurança da IA
- codecov - Para relatórios de cobertura de código
- python-dotenv - Para gerenciamento de variáveis de ambiente
- Pillow - Para processamento de imagens

## Configuração

1. Crie um arquivo `.env` no diretório raiz do projeto
2. Adicione suas variáveis de configuração:

```env
OPENAI_API_KEY=sua_chave_api_aqui
# Adicione outras variáveis de ambiente conforme necessário
```

## Executando a Aplicação

Para iniciar a aplicação Streamlit:

```bash
streamlit run app.py
```

## Licença

Este projeto está licenciado sob a Licença MIT