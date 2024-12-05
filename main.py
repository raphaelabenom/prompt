from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain_anthropic import ChatAnthropic
from guardrails import Guard
from weasyprint import HTML
import dotenv
import os
import json

dotenv.load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="./templates")

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    raise ValueError("Variável de ambiente ANTHROPIC_API_KEY não está definida")

llm = ChatAnthropic(
    anthropic_api_key=anthropic_api_key,
    model_name="claude-3-sonnet-20240229",
    max_tokens=4096,
    temperature=0.7
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
        <list name="Refeições" description="5 refeições diárias">
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

def generate_html_report(plano_dieta):
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            h2 {{ color: #34495e; margin-top: 20px; }}
            h3 {{ color: #2980b9; }}
            ul {{ padding-left: 20px; }}
            .recipe {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 15px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Plano de Dieta Personalizado</h1>
        
        <h2>Informações Gerais</h2>
        <ul>
            <li><strong>Calorias Diárias:</strong> {plano_dieta['calorias']}</li>
            <li><strong>Macronutrientes:</strong> {plano_dieta['macronutrientes']}</li>
            <li><strong>Consumo de Água:</strong> {plano_dieta['Consumo de água']}</li>
            <li><strong>Consumo de Fibras:</strong> {plano_dieta['Consumo de fibras']}</li>
            <li><strong>Suplementação:</strong> {plano_dieta['Suplementação']}</li>
        </ul>
        
        <h2>Plano de Refeições</h2>
        <p>{plano_dieta['plano_refeicoes']['detalhamento']}</p>
        
        <h2>Refeições</h2>
        {''.join([f"""
        <div class="recipe">
            <h3>{receita['refeicao']} - {receita['nome']}</h3>
            <h4>Ingredientes:</h4>
            <table>
                <tr>
                    <th>Ingrediente</th>
                    <th>Proteína (g)</th>
                    <th>Carboidrato (g)</th>
                    <th>Gordura (g)</th>
                </tr>
                {''.join([f"""
                <tr>
                    <td>{ingrediente['nome']}</td>
                    <td>{ingrediente['proteina']}</td>
                    <td>{ingrediente['carboidrato']}</td>
                    <td>{ingrediente['gordura']}</td>
                </tr>
                """ for ingrediente in receita['ingredientes']])}
            </table>
            <h4>Instruções:</h4>
            <p>{receita['instrucoes']}</p>
        </div>
        """ for receita in plano_dieta['refeições']])}
        
        <h2>Dicas de Nutrição e Estilo de Vida</h2>
        <ul>
            {''.join([f'<li>{dica}</li>' for dica in plano_dieta['dicas']])}
        </ul>

        <h2>Observações Adicionais</h2>
        <p>{plano_dieta['observacoes']}</p>
    </body>
    </html>
    """
    return html_content

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
        input_data = {
            "idade": idade,
            "genero": genero,
            "peso": peso,
            "altura": altura,
            "nivel_atividade": nivel_atividade,
            "objetivos": objetivos,
            "restricoes_alimentares": restricoes_alimentares
        }
        
        resposta = chain.invoke(input_data)
        print("Resposta do modelo:", resposta)  # Para debug
        
        # Extrair o conteúdo da resposta
        if isinstance(resposta, dict) and 'text' in resposta:
            conteudo = resposta['text']
        else:
            conteudo = str(resposta)
        
        try:
            plano_dieta = json.loads(conteudo)['plano_dieta']
        except json.JSONDecodeError:
            raise ValueError("A resposta do modelo não está no formato JSON esperado")
        
        html_content = generate_html_report(plano_dieta)
        
        pdf_path = "plano_dieta.pdf"
        HTML(string=html_content).write_pdf(pdf_path)
        
        return FileResponse(pdf_path, filename="seu_plano_dieta.pdf", media_type="application/pdf")
        
    except Exception as e:
        return {"error": f"Erro ao processar: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)