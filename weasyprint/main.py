import logging
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from guardrails import Guard
from fpdf import FPDF
import dotenv
import os
import json
import uuid

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)

app = FastAPI()
templates = Jinja2Templates(directory="./templates")

# Diretório para salvar os PDFs
PDF_DIR = "pdfs"
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Variável de ambiente OPENAI_API_KEY não está definida")

llm = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=openai_api_key
)

rail_spec = """
<rail version="0.1">
<messages>
    <message role="system">
    You are a professional nutritionist specialized in creating personalized meal plans. You must respond only with valid JSON in the specified format.
    </message>
    <message role="user">
    Generate a diet plan based on the provided information.
    </message>
    <message role="assistant">
    I'll generate a personalized diet plan based on the information you provide. The plan will be in JSON format as specified.
    </message>
</messages>
<output>
    <object name="plano_dieta">
        <string name="calorias" description="Quantidade diária em kcal" />
        <string name="macronutrientes" description="Distribuição macro" />
        <string name="Consumo de água" description="Quantidade diária em ml" />
        <string name="Consumo de fibras" description="Quantidade diária em gramas" />
        <string name="Suplementação" description="Suplementos recomendados" />
        <object name="plano_refeicoes">
            <string name="detalhamento" description="Descrição do plano de refeições" />
        </object>
        <list name="refeições" description="5 refeições diárias">
            <object>
                <string name="refeicao" description="Nome da refeição" />
                <string name="nome" description="Nome da receita" />
                <list name="ingredientes" description="Lista de ingredientes">
                    <object>
                        <string name="nome" description="Nome do ingrediente" />
                        <string name="proteina" description="Valor nutricional de proteína em gramas (tabela TACO)" />
                        <string name="carboidrato" description="Valor nutricional de carboidrato em gramas (tabela TACO)" />
                        <string name="gordura" description="Valor nutricional de gordura em gramas (tabela TACO)" />
                    </object>
                </list>
                <string name="instrucoes" description="Passos para preparo" />
            </object>
        </list>
        <list name="dicas" description="Dicas de nutrição e estilo de vida">
            <string />
        </list>
        <string name="observacoes" description="Observações adicionais" />
    </object>
</output>
</rail>
"""

guard = Guard.for_rail_string(rail_spec)

prompt_template = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template("""
Você é um nutricionista profissional especializado em elaborar planos alimentares personalizados. Sua tarefa é fornecer um plano nutricional baseado nas seguintes informações:

- Idade: {idade}
- Peso: {peso}
- Altura: {altura}
- Gênero: {genero}
- Nível de Atividade: {nivel_atividade}
- Restrições Alimentares: {restricoes_alimentares}
- Objetivos: {objetivos}

O plano nutricional deve:

- Ser adequado às necessidades calóricas diárias calculadas com base nas informações fornecidas.
- Incluir a distribuição de macronutrientes (proteínas, carboidratos e gorduras) conforme recomendado para o objetivo especificado.
- Detalhar um plano de refeições composto por 5 refeições diárias: café da manhã, lanche da manhã, almoço, lanche da tarde e jantar.
- Fornecer receitas para cada refeição, incluindo ingredientes e instruções de preparo.
- Os ingredientes devem ser apresentados com seus valores nutricionais (proteína, carboidrato, gordura) em gramas, conforme a tabela TACO.
- Incluir 3 dicas adicionais para auxiliar no alcance dos objetivos.

Retorne exatamente no seguinte formato JSON:

{{
    "plano_dieta": {{
        "calorias": "quantidade diária em kcal",
        "macronutrientes": "distribuição macro",
        "Consumo de água": "quantidade diária em ml",
        "Consumo de fibras": "quantidade diária em gramas",
        "Suplementação": "suplementos recomendados",
        "plano_refeicoes": {{
            "detalhamento": "descrição do plano de refeições"
        }},
        "refeições": [
            {{
                "refeicao": "CAFÉ DA MANHÃ",
                "nome": "Nome da receita",
                "ingredientes": [
                    {{
                        "nome": "Nome do ingrediente",
                        "proteina": "valor em gramas (tabela TACO)",
                        "carboidrato": "valor em gramas (tabela TACO)",
                        "gordura": "valor em gramas (tabela TACO)"
                    }},
                    ...
                ],
                "instrucoes": "passos para preparo"
            }},
            {{
                "refeicao": "LANCHE DA MANHÃ",
                "nome": "Nome da receita",
                "ingredientes": [
                    {{
                        "nome": "Nome do ingrediente",
                        "proteina": "valor em gramas (tabela TACO)",
                        "carboidrato": "valor em gramas (tabela TACO)",
                        "gordura": "valor em gramas (tabela TACO)"
                    }},
                    ...
                ],
                "instrucoes": "passos para preparo"
            }},
            {{
                "refeicao": "ALMOÇO",
                "nome": "Nome da receita",
                "ingredientes": [
                    {{
                        "nome": "Nome do ingrediente",
                        "proteina": "valor em gramas (tabela TACO)",
                        "carboidrato": "valor em gramas (tabela TACO)",
                        "gordura": "valor em gramas (tabela TACO)"
                    }},
                    ...
                ],
                "instrucoes": "passos para preparo"
            }},
            {{
                "refeicao": "LANCHE DA TARDE",
                "nome": "Nome da receita",
                "ingredientes": [
                    {{
                        "nome": "Nome do ingrediente",
                        "proteina": "valor em gramas (tabela TACO)",
                        "carboidrato": "valor em gramas (tabela TACO)",
                        "gordura": "valor em gramas (tabela TACO)"
                    }},
                    ...
                ],
                "instrucoes": "passos para preparo"
            }},
            {{
                "refeicao": "JANTAR",
                "nome": "Nome da receita",
                "ingredientes": [
                    {{
                        "nome": "Nome do ingrediente",
                        "proteina": "valor em gramas (tabela TACO)",
                        "carboidrato": "valor em gramas (tabela TACO)",
                        "gordura": "valor em gramas (tabela TACO)"
                    }},
                    ...
                ],
                "instrucoes": "passos para preparo"
            }}
        ],
        "dicas": [
            "dica 1",
            "dica 2",
            "dica 3"
        ],
        "observacoes": "observações adicionais"
    }}
}}

Certifique-se de seguir rigorosamente o formato solicitado e preencher todos os campos com informações precisas.
""")
])

chain = LLMChain(llm=llm, prompt=prompt_template)

def generate_pdf_report(plano_dieta):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Plano de Dieta Personalizado", ln=True, align='C')

    # Adicionando informações gerais
    pdf.multi_cell(0, 10, txt=f"Calorias: {plano_dieta['calorias']}")
    pdf.multi_cell(0, 10, txt=f"Macronutrientes: {plano_dieta['macronutrientes']}")
    pdf.multi_cell(0, 10, txt=f"Consumo de água: {plano_dieta['Consumo de água']}")
    pdf.multi_cell(0, 10, txt=f"Consumo de fibras: {plano_dieta['Consumo de fibras']}")
    pdf.multi_cell(0, 10, txt=f"Suplementação: {plano_dieta['Suplementação']}")

    # Adicionando plano de refeições
    pdf.multi_cell(0, 10, txt=f"Plano de Refeições: {plano_dieta['plano_refeicoes']['detalhamento']}")

    # Adicionando refeições
    for refeicao in plano_dieta['refeições']:
        pdf.multi_cell(0, 10, txt=f"\n{refeicao['refeicao']} - {refeicao['nome']}")
        pdf.multi_cell(0, 10, txt="Ingredientes:")
        for ingrediente in refeicao['ingredientes']:
            pdf.multi_cell(0, 10, txt=f"- {ingrediente['nome']}: Proteína {ingrediente['proteina']}g, Carboidrato {ingrediente['carboidrato']}g, Gordura {ingrediente['gordura']}g")
        pdf.multi_cell(0, 10, txt=f"Instruções: {refeicao['instrucoes']}")

    # Adicionando dicas
    pdf.multi_cell(0, 10, txt="\nDicas:")
    for dica in plano_dieta['dicas']:
        pdf.multi_cell(0, 10, txt=f"- {dica}")

    # Adicionando observações
    pdf.multi_cell(0, 10, txt=f"\nObservações: {plano_dieta['observacoes']}")

    # Gerando um nome de arquivo único
    filename = f"plano_dieta_{uuid.uuid4()}.pdf"
    filepath = os.path.join(PDF_DIR, filename)

    # Salvando o PDF
    pdf.output(filepath)

    return filename

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/gerar_dieta")
async def gerar_dieta(
    idade: int = Form(...),
    genero: str = Form(...),
    peso: float = Form(...),
    altura: float = Form(...),
    nivel_atividade: str = Form(...),
    objetivos: str = Form(...),
    restricoes_alimentares: str = Form(...)
):
    try:
        logging.info("Iniciando geração de plano de dieta")
        input_data = {
            "idade": idade,
            "genero": genero,
            "peso": peso,
            "altura": altura,
            "nivel_atividade": nivel_atividade,
            "objetivos": objetivos,
            "restricoes_alimentares": restricoes_alimentares
        }
        logging.info(f"Dados de entrada: {input_data}")
        
        resposta = chain.invoke(input_data)
        logging.info("Resposta do modelo obtida")
        logging.info(f"Resposta do modelo: {resposta['text']}")
        
        validated_output = guard(lambda: resposta['text'])
        logging.info("JSON validado pelo guard")
        
        plano_dieta = json.loads(validated_output)['plano_dieta']
        logging.info("JSON parseado com sucesso")
        
        filename = generate_pdf_report(plano_dieta)
        logging.info(f"PDF gerado: {filename}")
        
        return JSONResponse(content={"message": "Plano de dieta gerado com sucesso", "filename": filename})
        
    except json.JSONDecodeError as e:
        logging.error(f"Erro ao decodificar JSON: {e}")
        return JSONResponse(status_code=500, content={"error": "Erro ao processar resposta do modelo"})
    except KeyError as e:
        logging.error(f"Chave não encontrada no JSON: {e}")
        return JSONResponse(status_code=500, content={"error": "Estrutura da resposta do modelo inválida"})
    except Exception as e:
        logging.error(f"Erro não esperado: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Erro ao processar: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)