"""Admin catalog management (task statuses, impossibility types)."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from app.extensions import db
from app.models.catalog import EstadoTareaConfig, TipoImposibilidadConfig
from app.decorators import role_required
from app.blueprints.admin import admin_bp


@admin_bp.route('/catalogos')
@login_required
@role_required('admin')
def catalogos():
    estados = EstadoTareaConfig.query.order_by(EstadoTareaConfig.order_index).all()
    tipos = TipoImposibilidadConfig.query.order_by(TipoImposibilidadConfig.name).all()
    return render_template('admin_catalogos.html', estados=estados, tipos=tipos)


@admin_bp.route('/catalogos/estado', methods=['POST'])
@login_required
@role_required('admin')
def guardar_estado():
    action = request.form.get('action')
    if action == 'create':
        name = request.form.get('name', '').strip().lower().replace(' ', '_')
        display_name = request.form.get('display_name', '').strip()
        color = request.form.get('color', '#94a3b8')
        is_done = request.form.get('is_done_state') == 'on'

        if name and display_name:
            if not EstadoTareaConfig.query.filter_by(name=name).first():
                max_order = db.session.query(db.func.max(EstadoTareaConfig.order_index)).scalar() or 0
                db.session.add(EstadoTareaConfig(
                    name=name, display_name=display_name, color=color,
                    order_index=max_order + 1, is_done_state=is_done
                ))
                db.session.commit()
                flash(f"Estado '{display_name}' creado.", "success")
            else:
                flash("Ya existe un estado con ese nombre.", "warning")

    elif action == 'update':
        estado_id = request.form.get('estado_id')
        estado = EstadoTareaConfig.query.get(estado_id)
        if estado:
            estado.display_name = request.form.get('display_name', estado.display_name)
            estado.color = request.form.get('color', estado.color)
            estado.is_done_state = request.form.get('is_done_state') == 'on'
            db.session.commit()
            flash(f"Estado '{estado.display_name}' actualizado.", "success")

    elif action == 'delete':
        estado_id = request.form.get('estado_id')
        estado = EstadoTareaConfig.query.get(estado_id)
        if estado:
            db.session.delete(estado)
            db.session.commit()
            flash(f"Estado eliminado.", "success")

    return redirect(url_for('admin.catalogos'))


@admin_bp.route('/catalogos/tipo', methods=['POST'])
@login_required
@role_required('admin')
def guardar_tipo():
    action = request.form.get('action')
    if action == 'create':
        name = request.form.get('name', '').strip()
        if name and not TipoImposibilidadConfig.query.filter_by(name=name).first():
            db.session.add(TipoImposibilidadConfig(name=name))
            db.session.commit()
            flash(f"Tipo '{name}' creado.", "success")
        else:
            flash("Tipo duplicado o vacío.", "warning")

    elif action == 'delete':
        tipo_id = request.form.get('tipo_id')
        tipo = TipoImposibilidadConfig.query.get(tipo_id)
        if tipo:
            db.session.delete(tipo)
            db.session.commit()
            flash("Tipo eliminado.", "success")

    return redirect(url_for('admin.catalogos'))
