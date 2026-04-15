"""Excel template download endpoints."""
from flask import send_file
from app.services.excel_service import generate_imposibilidades_template, generate_usuarios_template
from app.blueprints.api import api_bp


@api_bp.route('/templates/imposibilidades')
def download_imposibilidades_template():
    output = generate_imposibilidades_template(with_examples=False)
    return send_file(output, download_name='plantilla_imposibilidades.xlsx', as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@api_bp.route('/templates/imposibilidades/ejemplo')
def download_imposibilidades_example():
    output = generate_imposibilidades_template(with_examples=True)
    return send_file(output, download_name='ejemplo_imposibilidades.xlsx', as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@api_bp.route('/templates/usuarios')
def download_usuarios_template():
    output = generate_usuarios_template(with_examples=False)
    return send_file(output, download_name='plantilla_usuarios.xlsx', as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@api_bp.route('/templates/usuarios/ejemplo')
def download_usuarios_example():
    output = generate_usuarios_template(with_examples=True)
    return send_file(output, download_name='ejemplo_usuarios.xlsx', as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
