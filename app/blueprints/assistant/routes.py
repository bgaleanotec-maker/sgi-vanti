import os
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.decorators import role_required
from app.config import Config
from app.blueprints.assistant import assistant_bp


@assistant_bp.route('/ask_gema', methods=['POST'])
@login_required
def ask_gema_route():
    data = request.get_json()
    user_prompt = data.get('prompt')
    if not user_prompt:
        return {"error": "No se proporcionó ninguna pregunta"}, 400

    from app.services.ai_service import ask_gema
    result = ask_gema(user_prompt, current_user.rol, current_user.username)

    if 'error' in result:
        return {"error": result['error']}, 500
    return result


@assistant_bp.route('/admin/configurar_asistente', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def configurar_asistente():
    if request.method == 'POST':
        if 'instrucciones' in request.form:
            instrucciones = request.form['instrucciones']
            with open(Config.INSTRUCTIONS_FILE, 'w', encoding='utf-8') as f:
                f.write(instrucciones)
            flash('Instrucciones del asistente actualizadas.', 'success')

        if 'knowledge_file' in request.files:
            file = request.files['knowledge_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(Config.KNOWLEDGE_DIR, filename))
                flash(f"Archivo '{filename}' añadido a la base de conocimiento.", 'success')

        return redirect(url_for('assistant.configurar_asistente'))

    try:
        with open(Config.INSTRUCTIONS_FILE, 'r', encoding='utf-8') as f:
            instrucciones_actuales = f.read()
    except FileNotFoundError:
        instrucciones_actuales = "Eres 'SGI', asistente virtual del Sistema de Gestión de Imposibilidades (SGI) de VANTI."

    knowledge_files = os.listdir(Config.KNOWLEDGE_DIR) if os.path.exists(Config.KNOWLEDGE_DIR) else []
    return render_template('configurar_asistente.html',
                           instrucciones=instrucciones_actuales,
                           knowledge_files=knowledge_files)


@assistant_bp.route('/admin/knowledge/delete/<filename>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_conocimiento(filename):
    try:
        os.remove(os.path.join(Config.KNOWLEDGE_DIR, filename))
        flash(f"Archivo '{filename}' eliminado.", 'success')
    except OSError as e:
        flash(f"Error: {e}", 'danger')
    return redirect(url_for('assistant.configurar_asistente'))
