from flask import Flask, request, send_file, jsonify, url_for
import openai
from fpdf import FPDF
import os
import tempfile
import guardrails as gr
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configurando a chave da API OpenAI a partir das variáveis de ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")

# Função principal para gerar o plano nutricional
def gerar_plano_dieta(idade, peso, altura, genero, nivel_atividade, objetivos, restricoes_alimentares):
    # Definindo o rail_spec conforme especificado
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

    # Geração do prompt com base nas informações recebidas
    prompt = f"""
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

    Certifique-se de seguir rigorosamente o formato solicitado e preencher todos os campos com informações precisas.
    """

    try:
        # Chamada à API da OpenAI atualizada
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional nutritionist specialized in creating personalized meal plans."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extraindo resposta gerada pela LLM como texto
        if response.choices and len(response.choices) > 0:
            plano_dieta_text = response.choices[0].message['content']
        else:
            raise ValueError("A resposta da API OpenAI não contém escolhas válidas.")
    except Exception as e:
        print(f"Erro ao chamar a API OpenAI: {e}")
        raise e

    # Gerando o PDF a partir do plano de dieta
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Plano de Dieta Personalizado", ln=True, align='C')

    # Adicionando informações do plano ao PDF
    pdf.multi_cell(0, 10, txt=plano_dieta_text)

    # Salvando o PDF em um arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)

    return temp_file.name

# Endpoint Flask para receber requisições do frontend
@app.route('/gerar_plano', methods=['POST'])
def gerar_plano():
    try:
        request_data = request.get_json()  # Garantir que está recebendo JSON
        if not request_data:
            return jsonify({"error": "Invalid input data"}), 400

        # Gera o plano de dieta e obtém o caminho do arquivo PDF
        pdf_path = gerar_plano_dieta(
            request_data.get("idade"),
            request_data.get("peso"),
            request_data.get("altura"),
            request_data.get("genero"),
            request_data.get("nivel_atividade"),
            request_data.get("objetivos"),
            request_data.get("restricoes_alimentares", "")
        )
        
        # Retornar um link para baixar o arquivo
        return jsonify({"download_url": request.url_root + 'baixar_plano/' + os.path.basename(pdf_path)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/baixar_plano/<filename>', methods=['GET'])
def baixar_plano(filename):
    try:
        file_path = os.path.join(tempfile.gettempdir(), filename)
        return send_file(file_path, as_attachment=True, download_name="plano_dieta.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Executa o servidor Flask
    app.run(host='0.0.0.0', port=5000)
