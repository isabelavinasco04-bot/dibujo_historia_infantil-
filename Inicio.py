import os
import streamlit as st
import base64
from openai import OpenAI
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# -----------------------------
# Utilidades
# -----------------------------
def encode_image_to_base64(image_path: str) -> str:
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return ""

def build_wattpad_prompt(image_desc: str) -> str:
    return f"""
Eres una autora bestseller de Wattpad en español. Escribe una historia ULTRA dramática, romántica y adictiva inspirada en este boceto descrito así: "{image_desc}".

Requisitos:
- TÍTULO pegajoso (máx. 8 palabras).
- SINOPSIS corta (2-3 líneas) con gancho.
- CAPÍTULO 1 (700-1000 palabras), presente en 1ra persona (protagonista femenina).
- Tropes: enemigos-a-amantes, destino/crush imposible, secreto familiar, lluvia o tormenta simbólica.
- Ritmo rápido, cliffhanger al final del capítulo.
- Estilo Wattpad: emocional, intenso, frases cortas potentes, diálogos naturales.
- NO digas “este dibujo muestra…”. Integra los elementos del boceto como metáforas o símbolos visuales (colores, formas, trazos) que reflejen el estado emocional.
- Tono: dramón delicioso pero verosímil.

Estructura Markdown:
# <TÍTULO>
**Sinopsis:** <sinopsis>
## Capítulo 1
<texto del capítulo con diálogos y cliffhanger>
""".strip()

def build_kids_prompt(image_desc: str) -> str:
    return f"""
Crea una historia infantil breve y entretenida en español (450-600 palabras)
a partir de esta descripción: "{image_desc}".
Usa un tono tierno, con moraleja sencilla y final feliz. Incluye título.
""".strip()

# -----------------------------
# Estado de sesión
# -----------------------------
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "full_response" not in st.session_state:
    st.session_state.full_response = ""
if "base64_image" not in st.session_state:
    st.session_state.base64_image = ""

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Tablero Inteligente")
st.title("Tablero Inteligente")
with st.sidebar:
    st.subheader("Acerca de:")
    st.write("Esta app interpreta tu boceto y genera historias 🤖✍️")

st.subheader("Dibuja el boceto y presiona el botón para analizarlo")

# Canvas
drawing_mode = "freedraw"
stroke_width = st.sidebar.slider("Selecciona el ancho de línea", 1, 30, 5)
stroke_color = "#000000"
bg_color = "#FFFFFF"

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=300,
    width=400,
    drawing_mode=drawing_mode,
    key="canvas",
)

# Clave
ke = st.text_input("Ingresa tu Clave", type="password")
if ke:
    os.environ["OPENAI_API_KEY"] = ke
api_key = os.environ.get("OPENAI_API_KEY", "")

# Cliente OpenAI (nuevo SDK unificado)
client = OpenAI(api_key=api_key) if api_key else None

# Botón: Analizar
analyze_button = st.button("🔍 Analiza la imagen", type="secondary")

# -----------------------------
# Análisis del dibujo (visión)
# -----------------------------
if canvas_result.image_data is not None and api_key and analyze_button:
    with st.spinner("Analizando..."):
        try:
            input_numpy_array = np.array(canvas_result.image_data)
            input_image = Image.fromarray(input_numpy_array.astype("uint8")).convert("RGBA")
            input_image.save("img.png")

            base64_image = encode_image_to_base64("img.png")
            st.session_state.base64_image = base64_image

            prompt_text = "Describe brevemente en español lo que ves en la imagen. Menciona formas, composición y sensaciones."

            # Llamada visión
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )

            full_response = response.choices[0].message.content if response.choices else ""
            if not full_response:
                st.error("No se obtuvo descripción de la imagen. Intenta de nuevo.")
            else:
                st.session_state.full_response = full_response
                st.session_state.analysis_done = True
                st.success("¡Listo! Ya interpreté tu boceto.")
                st.markdown("**Descripción detectada:**")
                st.write(full_response)

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# -----------------------------
# Generación de historias
# -----------------------------
if st.session_state.analysis_done:
    st.divider()
    st.subheader("📚 ¿Quieres crear una historia?")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✨ Historia infantil"):
            with st.spinner("Creando historia infantil..."):
                try:
                    story_prompt = build_kids_prompt(st.session_state.full_response)
                    story_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": story_prompt}],
                        max_tokens=1000,
                    )
                    st.markdown("**📖 Tu historia infantil:**")
                    st.write(story_response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Ocurrió un error al crear la historia: {e}")

    with col2:
        if st.button("💔 Historia dramática estilo Wattpad"):
            with st.spinner("Escribiendo dramón..."):
                try:
                    wattpad_prompt = build_wattpad_prompt(st.session_state.full_response)
                    wattpad_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": wattpad_prompt}],
                        max_tokens=2200,
                        temperature=1.0,
                    )
                    st.markdown("**📖 Tu historia Wattpad:**")
                    st.write(wattpad_response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Ocurrió un error al crear la historia Wattpad: {e}")

# Advertencia si falta API key
if not api_key:
    st.warning("Por favor ingresa tu API key.")

