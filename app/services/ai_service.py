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
    model_name = get_service_config('gemini', 'model') or 'gemini-2.0-flash'

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

        # Try to use the specified model
        try:
            model = genai.GenerativeModel(model_name)
        except Exception:
            # Fallback: auto-detect available model
            model = None
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    model = genai.GenerativeModel(m.name)
                    break
            if model is None:
                return {"error": "No se encontraron modelos disponibles para esta API Key."}

        # Build conversation with history
        full_prompt = system_prompt + "\n\n"
        for h in history[-8:]:  # Last 8 messages
            role_label = "Usuario" if h['role'] == 'user' else "Asistente"
            full_prompt += f"{role_label}: {h['content']}\n"
        full_prompt += f"Usuario: {user_prompt}\nAsistente:"

        response = model.generate_content(full_prompt)

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
