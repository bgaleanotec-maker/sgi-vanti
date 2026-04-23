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
                tipo_negacion = (_safe(row.get('Tipo_Negacion')) or 'imposibilidad').lower()
                if tipo_negacion not in ('imposibilidad', 'rechazo'):
                    tipo_negacion = 'imposibilidad'
                motivo_rechazo = _safe(row.get('Motivo_Rechazo'))
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
                    tipo_negacion=tipo_negacion,
                    motivo_rechazo=motivo_rechazo,
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

            # WhatsApp + Email summaries per firm - busca TODOS los usuarios con ese BP_Firma
            from app.services.whatsapp_service import send_whatsapp
            from app.services.email_service import send_email
            ws_sent = ws_failed = 0
            em_sent = em_failed = 0
            sin_destinatario = []
            for firma, tasks in tasks_by_firm.items():
                # Buscar TODOS los usuarios relacionados con este BP (firma o contratista)
                # Pueden existir multiples (una firma + varios contratistas bajo el mismo BP)
                firma_users = Usuario.query.filter(
                    or_(
                        Usuario.username == firma,
                        Usuario.bp_firma == firma
                    ),
                    Usuario.is_active == True
                ).all()

                if not firma_users:
                    sin_destinatario.append(f"{firma} ({len(tasks)} tareas)")
                    continue

                count = len(tasks)
                # Summary compact (nunca lista todas las tareas para no saturar WhatsApp)
                preview = "\n".join([f"- {t['orden']}" for t in tasks[:3]])
                if count > 3:
                    preview += f"\n... y {count - 3} mas."

                msg = (
                    f"Hola, se acaban de cargar *{count} nuevos negocios* para el BP {firma} en SGI Vanti.\n\n"
                    f"Primeras ordenes:\n{preview}\n\n"
                    f"Ingresa a la plataforma para gestionarlos."
                )

                destinatarios_wa = 0
                destinatarios_email = 0
                for fu in firma_users:
                    # WhatsApp
                    if fu.celular and fu.notify_whatsapp:
                        try:
                            ok = send_whatsapp(fu.celular, msg)
                            if ok:
                                ws_sent += 1
                                destinatarios_wa += 1
                            else:
                                ws_failed += 1
                                print(f"[cargar_excel][WA-fail] BP={firma} user={fu.username} celular={fu.celular}")
                        except Exception as e:
                            ws_failed += 1
                            print(f"[cargar_excel][WA-error] BP={firma} user={fu.username}: {e}")
                    # Email resumen (adicional al por-tarea)
                    if fu.email and fu.notify_email:
                        try:
                            subject = f"SGI Vanti - {count} nuevas tareas cargadas para BP {firma}"
                            html = f"""
                                <p>Hola {fu.full_name or fu.username},</p>
                                <p>Se han cargado <strong>{count} nuevas tareas</strong> vinculadas al BP <strong>{firma}</strong>.</p>
                                <p>Primeras ordenes:</p>
                                <ul>{''.join(f'<li>{t["orden"]} - {t["direccion"]}</li>' for t in tasks[:5])}</ul>
                                <p>Ingresa a la plataforma SGI Vanti para gestionarlas.</p>
                            """
                            send_email(fu.email, subject, html)
                            em_sent += 1
                            destinatarios_email += 1
                        except Exception as e:
                            em_failed += 1
                            print(f"[cargar_excel][email-error] BP={firma} user={fu.username}: {e}")

                if destinatarios_wa == 0 and destinatarios_email == 0:
                    sin_destinatario.append(f"{firma} ({count} tareas, sin celular/email)")
                print(f"[cargar_excel] BP={firma}: {count} tareas, {destinatarios_wa} WA + {destinatarios_email} emails enviados")

            msg_resumen = (
                f"Carga completada: {len(df_nuevos)} tareas nuevas. "
                f"WhatsApp: {ws_sent} enviados ({ws_failed} fallidos). "
                f"Emails: {em_sent} enviados ({em_failed} fallidos)."
            )
            if sin_destinatario:
                msg_resumen += f" BPs sin destinatario configurado: {', '.join(sin_destinatario[:5])}"
                if len(sin_destinatario) > 5:
                    msg_resumen += f" (+{len(sin_destinatario)-5} mas)"
            flash(msg_resumen, "success" if (ws_failed + em_failed) == 0 else "warning")
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al procesar: {e}", "danger")
        return redirect(url_for('admin.dashboard'))
    return render_template('cargar_excel.html')


@admin_bp.route('/tarea/<int:id>', methods=['GET'])
@login_required
@role_required('admin')
def gestionar_tarea(id):
    """Admin: ver detalle de tarea con acciones de subsanacion (modificar, reactivar, devolver, marcar no valida)."""
    from app.models.catalog import EstadoTareaConfig
    tarea = Imposibilidad.query.get_or_404(id)
    estados = EstadoTareaConfig.query.filter_by(is_active=True).order_by(EstadoTareaConfig.order_index).all()
    return render_template('admin_gestionar_tarea.html', tarea=tarea, estados=estados)


@admin_bp.route('/tarea/<int:id>/accion', methods=['POST'])
@login_required
@role_required('admin')
def tarea_accion(id):
    """Admin actions over a task: modify comments, reactivate, return for adjustments, mark invalid."""
    tarea = Imposibilidad.query.get_or_404(id)
    accion = request.form.get('accion', '').strip()
    comentario_admin = (request.form.get('comentario_admin') or '').strip()
    nuevo_estado = request.form.get('nuevo_estado', '').strip()

    # Actualizar comentarios si viene editado (subsanacion)
    nuevos_comentarios_firma = request.form.get('comentarios_firma')
    if nuevos_comentarios_firma is not None:
        tarea.comentarios = nuevos_comentarios_firma.strip() or None
    nuevos_comentarios_gestor = request.form.get('comentarios_gestor')
    if nuevos_comentarios_gestor is not None:
        tarea.comentarios_gestor = nuevos_comentarios_gestor.strip() or None

    mensaje_usuario = None

    if accion == 'reactivar':
        # Volver a etapa de gestion: permite a la firma subir nuevos soportes
        tarea.estado_tarea = 'pendiente'
        tarea.motivo_rechazo = None
        mensaje_usuario = (
            f"Admin reactivo la orden {tarea.orden}. "
            f"Ingresa al sistema y sube la informacion corregida."
        )
        if comentario_admin:
            tarea.comentarios_gestor = (tarea.comentarios_gestor or '') + f"\n[ADMIN reactivo {datetime.now():%Y-%m-%d %H:%M}]: {comentario_admin}"
    elif accion == 'devolver':
        tarea.estado_tarea = 'devuelta'
        mensaje_usuario = (
            f"Admin devolvio la orden {tarea.orden} para ajustes. "
            f"Motivo: {comentario_admin or 'ver plataforma'}."
        )
        if comentario_admin:
            tarea.comentarios_gestor = (tarea.comentarios_gestor or '') + f"\n[ADMIN devolvio {datetime.now():%Y-%m-%d %H:%M}]: {comentario_admin}"
    elif accion == 'marcar_no_valida':
        tarea.estado_tarea = 'rechazada'
        tarea.tipo_negacion = 'rechazo'
        tarea.motivo_rechazo = comentario_admin or 'Informacion no valida segun admin'
        mensaje_usuario = (
            f"Admin marco la orden {tarea.orden} como NO VALIDA. "
            f"Motivo: {tarea.motivo_rechazo}"
        )
    elif accion == 'cerrar':
        tarea.estado_tarea = 'cerrada'
        mensaje_usuario = f"Admin cerro la orden {tarea.orden}."
        if comentario_admin:
            tarea.comentarios_gestor = (tarea.comentarios_gestor or '') + f"\n[ADMIN cerro {datetime.now():%Y-%m-%d %H:%M}]: {comentario_admin}"
    elif accion == 'cambiar_estado' and nuevo_estado:
        tarea.estado_tarea = nuevo_estado
        if comentario_admin:
            tarea.comentarios_gestor = (tarea.comentarios_gestor or '') + f"\n[ADMIN estado->{nuevo_estado} {datetime.now():%Y-%m-%d %H:%M}]: {comentario_admin}"
    elif accion == 'guardar':
        # solo guarda edits de comentarios sin cambiar estado
        pass
    elif accion == 'cambiar_tipo_negacion':
        nuevo_tipo_neg = request.form.get('tipo_negacion', 'imposibilidad').strip().lower()
        if nuevo_tipo_neg in ('imposibilidad', 'rechazo'):
            tarea.tipo_negacion = nuevo_tipo_neg
            if nuevo_tipo_neg == 'rechazo':
                tarea.motivo_rechazo = comentario_admin or tarea.motivo_rechazo
    else:
        flash('Accion no reconocida.', 'warning')
        return redirect(url_for('admin.gestionar_tarea', id=id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error guardando cambios: {e}', 'danger')
        return redirect(url_for('admin.gestionar_tarea', id=id))

    # Notificar a la firma si hubo accion con mensaje
    if mensaje_usuario and tarea.bp_firma:
        from sqlalchemy import or_ as _or
        recipientes = Usuario.query.filter(
            _or(Usuario.username == tarea.bp_firma, Usuario.bp_firma == tarea.bp_firma),
            Usuario.is_active == True
        ).all()
        subject = f"SGI Vanti - Actualizacion admin en orden {tarea.orden}"
        html = f"""
            <p>Hola,</p>
            <p>{mensaje_usuario}</p>
            <p>Ingresa a la plataforma para revisar el detalle y actuar.</p>
        """
        for u in recipientes:
            try:
                if u.email and u.notify_email:
                    from app.services.email_service import send_email
                    send_email(u.email, subject, html)
                if u.celular and u.notify_whatsapp:
                    from app.services.whatsapp_service import send_whatsapp
                    send_whatsapp(u.celular, mensaje_usuario)
            except Exception as e:
                print(f"[admin.tarea_accion] error notificando {u.username}: {e}")

    flash(f'Accion "{accion}" aplicada correctamente. Notificacion enviada.', 'success')
    return redirect(url_for('admin.gestionar_tarea', id=id))


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
