import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from PIL import Image

# guardrails
from guardrails import Guard
from guardrails.hub import RestrictToTopic
from guardrails.validators import ValidationResult

load_dotenv()

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Definir Guardrails para restringir o chatbot a tópicos específicos
# https://hub.guardrailsai.com/validator/tryolabs/restricttotopic
guard = Guard().use(
    RestrictToTopic(
        valid_topics=["nutrition", "diet", "food", "health"],
        invalid_topics=["politics", "entertainment", "technology", "sports", "music", "history", "science", "finance", "business", "policy", "religion", "travel", "pornography", "violence", "hate speech", "spam"],
        disable_classifier=True,
        disable_llm=False,
        device=-1,
        model="facebook/bart-large-mnli",
        on_fail="exception"
    )
)

def load_image(image_path, alt_message):
    if os.path.exists(image_path):
        return Image.open(image_path)
    else:
        st.warning(alt_message)
        return None

def get_response(user_input):
    # Define o backstory e o prompt
    backstory = """
    Você é uma referência global no campo da nutrição, apelidado de "Mestre dos Alimentos" ou o "Nutrólogo Supremo". 
    Consultado por celebridades, atletas e profissionais de saúde, você desenvolve planos alimentares personalizados, equilibrando saúde, desempenho e sustentabilidade. 
    Com vasto conhecimento em bioquímica e dietas globais (como a mediterrânea, cetogênica e ayurvédica), você é defensor do consumo consciente e da preservação ambiental. 
    Agora,você expande sua expertise para o mundo digital, oferecendo orientação de alta qualidade para ajudar pessoas a montarem suas próprias dietas e responder dúvidas sobre alimentação.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": backstory},
                {"role": "user", "content": f"Responda apenas a perguntas relacionadas a dieta e nutrição. Usuário: {user_input}"}
            ],
            max_tokens=2048,
            n=1,
            stop=None,
            temperature=0.7,
        )
    except Exception as e:
        return f"Erro na API da OpenAI: {str(e)}"

    assistant_response = response.choices[0].message.content.strip()

    try:
        # Aplica o Guardrails para validar a resposta
        validation_result = guard.validate(assistant_response)
        if isinstance(validation_result, ValidationResult):
            if validation_result.passed:
                return assistant_response
            else:
                return f"Erro de validação: {validation_result.error_message}"
        else:
            return assistant_response
    except Exception as e:
        return f"Erro ao aplicar Guardrails: {str(e)}"

# --------------------------------
# Interface com Streamlit
# --------------------------------

st.set_page_config(page_title="Mestre dos Alimentos", page_icon="🥦", layout="centered")

# Exibir logotipo ou banner
# logo = load_image('./assets/logo.png', "Logo não encontrado. Certifique-se de que 'assets/logo.png' está no diretório do projeto.")
# if logo:
#     st.image(logo, use_container_width=True)

st.title("🥗 Chatbot Assistente de Nutrição - Mestre dos Alimentos")

st.markdown("""
Bem-vindo ao **Mestre dos Alimentos**, seu assistente digital de nutrição! Faça suas perguntas sobre dieta, alimentação saudável, nutrientes e muito mais.

---
""")

nutrients_img = load_image('./assets/nutrients_lab.png.png', "Adicione uma imagem de laboratório de nutrientes para enriquecer a interface.")
if nutrients_img:
    st.image(nutrients_img, use_container_width=True)

user_input = st.text_input("Faça uma pergunta sobre dieta ou nutrição:")

if st.button("Enviar"):
    if user_input.strip():
        with st.spinner("Pensando..."):
            response = get_response(user_input)
            if response.startswith("Erro"):
                st.error(response)
            else:
                st.success("Resposta:")
                st.write(response)
    else:
        st.warning("Por favor, insira uma pergunta.")

