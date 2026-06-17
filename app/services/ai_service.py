import os
import pandas as pd
from docx import Document as DocxDocument
from flask import session
from app.config import get_service_config, Config


# --- Document Parsing for RAG ---
def parse_document(filepath):
    """Parse file content to text."""
    filename = filepath.lower()
    content = ""
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
            content = df.to_string()
        elif filename.endswith('.docx'):
            doc = DocxDocument(filepath)
            content = "\n".join([p.text for p in doc.paragraphs if p.text])
        elif filename.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return content


def get_knowledge_context(query):
    """Search knowledge base for relevant content using TF-IDF-like scoring."""
    query_words = set(query.lower().split())
    relevant_chunks = []
    knowledge_dir = Config.KNOWLEDGE_DIR

    if not os.path.exists(knowledge_dir):
        return ""

    for filename in os.listdir(knowledge_dir):
        filepath = os.path.join(knowledge_dir, filename)
        text = parse_document(filepath)
        if not text:
            continue

        # Score by word overlap (better than simple any())
        text_lower = text.lower()
        matches = sum(1 for word in query_words if word in text_lower and len(word) > 2)
        if matches >= 1:
            # Truncate long documents
            truncated = text[:3000] if len(text) > 3000 else text
            relevant_chunks.append((matches, f"--- {filename} ---\n{truncated}"))

    # Sort by relevance score, take top 3
    relevant_chunks.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([chunk for _, chunk in relevant_chunks[:3]])


# --- Role capabilities for context ---
ROLE_CAPABILITIES = {
    'admin': 'Puedes: gestionar usuarios, cargar/descargar Excel, ver analítica, mapa geográfico, configurar integraciones, gestionar catálogos, resetear base de datos.',
    'contratista': 'Puedes: ver tus tareas asignadas, gestionar imposibilidades (agregar comentarios y adjuntos), llenar datos de carta.',
    'gestor': 'Puedes: ver tareas asignadas, cerrar o devolver imposibilidades gestionadas por los contratistas.',
    'ejecutivo': 'Puedes: revisar y editar datos de carta, marcar cartas como enviadas, descargar documentos Word.',
}


def ask_gema(user_prompt, user_role='admin', username='usuario'):
    """Send prompt to Gemini with role-aware context and conversation history."""
    import google.generativeai as genai

    api_key = get_service_config('gemini', 'api_key')
    model_name = get_service_config('gemini', 'model') or 'gemini-flash-latest'

    if not api_key:
        return {"error": "La IA no está configurada. El admin debe configurar la API Key de Gemini en Integraciones."}

    try:
        genai.configure(api_key=api_key)

        # Load instructions
        instructions_file = Config.INSTRUCTIONS_FILE
        try:
            with open(instructions_file, 'r', encoding='utf-8') as f:
                base_instructions = f.read()
        except FileNotFoundError:
            base_instructions = "Eres un asistente útil del sistema SGI."

        # Get knowledge context
        knowledge = get_knowledge_context(user_prompt)
        role_caps = ROLE_CAPABILITIES.get(user_role, '')

        # Build system prompt
        system_prompt = f"""
{base_instructions}

USUARIO ACTUAL: {username} | ROL: {user_role}
CAPACIDADES DE ESTE ROL: {role_caps}

{"CONTEXTO DE CONOCIMIENTO:" if knowledge else ""}
{knowledge}

REGLAS:
- Nunca pidas datos personales (nombres reales, cédulas, etc.)
- Sé conciso y profesional
- Responde en español
- Si no sabes algo, dilo honestamente
- Adapta tus respuestas al rol del usuario
"""

        # Conversation history from session
        history = session.get('gema_history', [])

        # Build conversation with history
        full_prompt = system_prompt + "\n\n"
        for h in history[-8:]:  # Last 8 messages
            role_label = "Usuario" if h['role'] == 'user' else "Asistente"
            full_prompt += f"{role_label}: {h['content']}\n"
        full_prompt += f"Usuario: {user_prompt}\nAsistente:"

        # Genera con el modelo configurado; si el nombre quedo obsoleto (404) o falla,
        # reintenta con modelos vigentes y, en ultimo caso, autodetecta uno disponible.
        candidatos = [model_name, 'gemini-flash-latest', 'gemini-2.5-flash']
        response = None
        ultimo_error = None
        for nombre in candidatos:
            try:
                response = genai.GenerativeModel(nombre).generate_content(full_prompt)
                break
            except Exception as e:
                ultimo_error = e
                continue
        if response is None:
            # Autodeteccion: primer modelo flash que soporte generateContent
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                        response = genai.GenerativeModel(m.name).generate_content(full_prompt)
                        break
            except Exception as e:
                ultimo_error = e
        if response is None:
            return {"error": f"No se pudo generar respuesta con la API Key/modelo. Detalle: {ultimo_error}"}

        if response and response.text:
            # Save to history
            history.append({'role': 'user', 'content': user_prompt})
            history.append({'role': 'assistant', 'content': response.text})
            session['gema_history'] = history[-20:]  # Keep last 20

            return {"response": response.text}
        else:
            return {"response": "El modelo no generó respuesta. Intenta reformular tu pregunta."}

    except Exception as e:
        print(f"Gemini error: {e}")
        return {"error": f"Error de conexión con IA: {str(e)[:100]}"}
