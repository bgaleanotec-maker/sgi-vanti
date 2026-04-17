import os
import io
import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file, send_from_directory
from flask_login import login_required, logout_user, current_user
from werkzeug.security import generate_password_hash
import pandas as pd
from sqlalchemy import or_

from app.extensions import db
from app.models import Usuario, Imposibilidad, Carta
from app.decorators import role_required
from app.helpers import aplicar_filtros_comunes
from app.services.notification_service import notify_user
from app.config import Config
from app.blueprints.admin import admin_bp


@admin_bp.route('/')
@login_required
@role_required('admin')
def dashboard():
    query = Imposibilidad.query
    query, filtros = aplicar_filtros_comunes(query)
    bp_firma = request.args.get('bp_firma')
    if bp_firma:
        query = query.filter(Imposibilidad.bp_firma.ilike(f'%{bp_firma}%'))
        filtros['bp_firma'] = bp_firma
    tareas = query.all()
    return render_template('dashboard_admin.html', tareas=tareas, user=current_user, filtros=filtros)


@admin_bp.route('/analitica')
@login_required
@role_required('admin')
def analitica():
    query = Imposibilidad.query
    query, filtros = aplicar_filtros_comunes(query)
    bp_firma = request.args.get('bp_firma')
    if bp_firma:
        query = query.filter(Imposibilidad.bp_firma.ilike(f'%{bp_firma}%'))
        filtros['bp_firma'] = bp_firma
    tareas_filtradas = query.all()
    total = len(tareas_filtradas)
    pendientes = len([t for t in tareas_filtradas if t.estado_tarea in ['pendiente', 'devuelta', 'carta_pendiente_revision']])
    gestionadas = len([t for t in tareas_filtradas if t.estado_tarea == 'gestionado'])
    cerradas = len([t for t in tareas_filtradas if t.estado_tarea in ['cerrada', 'carta_enviada']])
    return render_template('dashboard_analitica.html',
                           total=total, pendientes=pendientes,
                           gestionadas=gestionadas, cerradas=cerradas, filtros=filtros)


@admin_bp.route('/mapa_geografico')
@login_required
@role_required('admin')
def mapa_geografico():
    query = Imposibilidad.query
    query, _ = aplicar_filtros_comunes(query)
    bp_firma = request.args.get('bp_firma')
    if bp_firma:
        query = query.filter(Imposibilidad.bp_firma.ilike(f'%{bp_firma}%'))
    tareas_filtradas = query.all()
    locations = []
    for tarea in tareas_filtradas:
        try:
            lat = float(str(tarea.latitud).replace(',', '.'))
            lon = float(str(tarea.longitud).replace(',', '.'))
            locations.append({
                'lat': lat, 'lon': lon, 'orden': tarea.orden,
                'direccion': tarea.direccion,
                'estado': tarea.estado_tarea.replace('_', ' ').capitalize()
            })
        except (ValueError, TypeError):
            continue
    return render_template('mapa_geografico.html', locations=json.dumps(locations))


@admin_bp.route('/cargar_excel', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def cargar_excel():
    if request.method == 'POST':
        archivo = request.files.get('archivo')
        if not archivo or archivo.filename == '':
            flash("Debe seleccionar un archivo Excel válido.", "warning")
            return redirect(request.url)
        try:
            df = pd.read_excel(archivo)
            required_cols = ['Orden', 'BP_Firma', 'Gestor', 'Ejecutivo', 'Tarea']
            if not all(col in df.columns for col in required_cols):
                flash(f"Columnas requeridas: {', '.join(required_cols)}.", "danger")
                return redirect(request.url)

            ordenes_existentes = {i.orden for i in Imposibilidad.query.with_entities(Imposibilidad.orden).all()}
            df['Orden'] = df['Orden'].astype(str)
            df_nuevos = df[~df['Orden'].isin(ordenes_existentes)]
            duplicados_count = len(df) - len(df_nuevos)

            if df_nuevos.empty:
                flash(f"No se encontraron registros nuevos. {duplicados_count} duplicados omitidos.", "info")
                return redirect(url_for('admin.dashboard'))

            tasks_by_firm = {}

            def _safe(val):
                """Return stripped string or None for NaN/empty."""
                if val is None:
                    return None
                try:
                    if pd.isna(val):
                        return None
                except Exception:
                    pass
                s = str(val).strip()
                return s if s and s.lower() != 'nan' else None

            for _, row in df_nuevos.iterrows():
                ejecutivo = _safe(row.get('Ejecutivo'))
                tipo_tarea = (_safe(row.get('Tarea')) or 'estandar').lower()
                firma = _safe(row.get('BP_Firma'))
                tipo_asignacion = (_safe(row.get('Tipo_Asignacion')) or 'contratista').lower()
                filial = _safe(row.get('Filial'))
                codigo_raw = row.get('Codigo_Imposibilidad')
                try:
                    codigo_imp = int(codigo_raw) if codigo_raw is not None and not pd.isna(codigo_raw) else None
                except (ValueError, TypeError):
                    codigo_imp = None

                if ejecutivo and not Usuario.query.filter_by(username=ejecutivo).first():
                    db.session.add(Usuario(
                        username=ejecutivo,
                        password=generate_password_hash(ejecutivo, method='pbkdf2:sha256'),
                        rol='ejecutivo', must_change_password=True
                    ))
                if firma and not Usuario.query.filter_by(username=firma).first():
                    db.session.add(Usuario(
                        username=firma,
                        password=generate_password_hash(firma, method='pbkdf2:sha256'),
                        rol='contratista',
                        tipo_firma=tipo_asignacion if tipo_asignacion in ('firma', 'contratista') else 'contratista',
                        bp_firma=firma,
                        must_change_password=True
                    ))

                tarea = Imposibilidad(
                    sociedad=_safe(row.get('Sociedad')),
                    cuenta_contrato=_safe(row.get('Cuenta_Contrato')),
                    orden=str(row.get('Orden')),
                    estatus_usuario=_safe(row.get('Estatus_de_ Usuario')),
                    bp_firma=firma,
                    tipo_asignacion=tipo_asignacion,
                    filial=filial,
                    codigo_imposibilidad=codigo_imp,
                    malla=_safe(row.get('Malla')),
                    direccion=_safe(row.get('Direccion_Punto_Suministro')),
                    solicitante=_safe(row.get('Nombre_del_solicitante')),
                    descripcion_mercado=_safe(row.get('Descripcion_Mercado')),
                    municipio=_safe(row.get('N_Municipio')),
                    n_bp_firma=_safe(row.get('N_BP_Firma')),
                    estado_cliente=_safe(row.get('Estado')),
                    tipo_imposibilidad=_safe(row.get('Imposibilidad_1')),
                    latitud=_safe(row.get('latitud')),
                    longitud=_safe(row.get('longitud')),
                    gestor_asignado=_safe(row.get('Gestor')),
                    ejecutivo_asignado=ejecutivo,
                    tipo_tarea=tipo_tarea,
                    estado_tarea='pendiente',
                    fecha_cargue=datetime.now()
                )
                if tipo_tarea == 'carta':
                    tarea.carta = Carta()
                db.session.add(tarea)

                if firma:
                    if firma not in tasks_by_firm:
                        tasks_by_firm[firma] = []
                    tasks_by_firm[firma].append({
                        'orden': tarea.orden, 'cuenta': tarea.cuenta_contrato,
                        'direccion': tarea.direccion
                    })

                    # Email notification per task
                    firma_user = Usuario.query.filter_by(username=firma).first()
                    if firma_user and firma_user.email and firma_user.notify_email:
                        from app.services.email_service import send_email
                        subject = f"Nueva Imposibilidad Asignada - Orden {tarea.orden}"
                        html_content = render_template('email_base.html', content=f"""
                            <p>Hola {firma},</p>
                            <p>Se te ha asignado una nueva imposibilidad.</p>
                            <ul>
                                <li><strong>Orden:</strong> {tarea.orden}</li>
                                <li><strong>Cuenta:</strong> {tarea.cuenta_contrato}</li>
                                <li><strong>Dirección:</strong> {tarea.direccion}</li>
                                <li><strong>Tipo:</strong> {tarea.tipo_imposibilidad}</li>
                            </ul>
                        """)
                        send_email(firma_user.email, subject, html_content)

            db.session.commit()

            # WhatsApp summaries per firm
            from app.services.whatsapp_service import send_whatsapp
            ws_sent = ws_failed = 0
            for firma, tasks in tasks_by_firm.items():
                firma_user = Usuario.query.filter(
                    (Usuario.username == firma) | (Usuario.bp_firma == firma)
                ).first()
                if firma_user and firma_user.celular and firma_user.notify_whatsapp:
                    count = len(tasks)
                    preview = "\n".join([f"- {t['orden']} ({t['direccion']})" for t in tasks[:3]])
                    if count > 3:
                        preview += f"\n... y {count - 3} más."
                    msg = f"Hola {firma}, se han cargado {count} nuevas tareas.\n\n{preview}\n\nIngresa al sistema para gestionarlas."
                    if send_whatsapp(firma_user.celular, msg):
                        ws_sent += 1
                    else:
                        ws_failed += 1

            flash(f"Carga completada: {len(df_nuevos)} tareas nuevas. WhatsApps: {ws_sent} enviados, {ws_failed} fallidos.",
                  "success" if ws_failed == 0 else "warning")
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al procesar: {e}", "danger")
        return redirect(url_for('admin.dashboard'))
    return render_template('cargar_excel.html')


@admin_bp.route('/eliminar_tarea/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def eliminar_tarea(id):
    tarea = Imposibilidad.query.get_or_404(id)
    orden = tarea.orden
    db.session.delete(tarea)
    db.session.commit()
    flash(f"Tarea '{orden}' eliminada.", "success")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/descargar_excel')
@login_required
@role_required('admin')
def descargar_excel():
    data = Imposibilidad.query.all()
    df = pd.DataFrame([{
        'ID': i.id, 'Orden': i.orden, 'Cuenta_Contrato': i.cuenta_contrato,
        'Estado_Tarea': i.estado_tarea, 'Tipo_Tarea': i.tipo_tarea,
        'BP_Firma': i.bp_firma, 'Gestor_Asignado': i.gestor_asignado,
        'Ejecutivo_Asignado': i.ejecutivo_asignado,
        'Comentarios_Firma': i.comentarios, 'Comentarios_Gestor': i.comentarios_gestor,
        'Fecha_Cargue': i.fecha_cargue.strftime('%Y-%m-%d %H:%M') if i.fecha_cargue else None,
        'Fecha_Gestion_Firma': i.fecha_gestion_firma.strftime('%Y-%m-%d %H:%M') if i.fecha_gestion_firma else None,
        'Fecha_Gestion_Gestor': i.fecha_gestion_gestor.strftime('%Y-%m-%d %H:%M') if i.fecha_gestion_gestor else None,
    } for i in data])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Gestion_Imposibilidades')
    output.seek(0)
    return send_file(output, download_name='reporte_gestiones.xlsx', as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@admin_bp.route('/reset_database', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def reset_database():
    """DISABLED for production safety. Use admin/purge_imposibilidades instead if you
    truly need to clear task data. Never drop schema on a live database."""
    flash(
        'El reset destructivo fue DESHABILITADO para proteger la base de datos en produccion. '
        'Contacta al administrador del sistema si realmente necesitas este procedimiento.',
        'warning'
    )
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/purge_imposibilidades', methods=['POST'])
@login_required
@role_required('admin')
def purge_imposibilidades():
    """Safe alternative: delete only Imposibilidad rows (preserves users, catalogs, service config).
    Requires typing the total count to confirm."""
    total = Imposibilidad.query.count()
    confirm_count = request.form.get('confirm_count', '').strip()
    if confirm_count != str(total):
        flash(
            f'Para confirmar debes escribir exactamente el numero actual de tareas ({total}). '
            f'Esta accion NO toca usuarios, catalogos ni configuracion.',
            'warning'
        )
        return redirect(url_for('admin.dashboard'))
    try:
        # Delete carta first (FK), then imposibilidad
        Carta.query.delete()
        Imposibilidad.query.delete()
        db.session.commit()
        flash(f'{total} tareas eliminadas. Usuarios y catalogos intactos.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al purgar tareas: {e}', 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/adjuntos/<path:filename>')
@login_required
def descargar_adjuntos(filename):
    return send_from_directory(Config.UPLOADS_DIR, filename, as_attachment=True)
