"""Genera el PDF del Manual de Operacion de SGI Vanti.

Estilo inspirado en el Manual del Gestor Cartografico: portada, tabla de
contenido, secciones numeradas, tablas, casos de uso paso a paso y
credenciales. Las capturas son opcionales (docs/screenshots/*.png); si no
existen se reemplazan por un marcador.

Uso:
    python docs/generate_manual.py
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image,
)
import os

# --- Paleta (consistente con la marca SGI Vanti / brand morado) ---
DARK = HexColor('#1e1b4b')
ACCENT = HexColor('#6366f1')
PURPLE = HexColor('#7c3aed')
GREEN = HexColor('#10b981')
RED = HexColor('#ef4444')
AMBER = HexColor('#f59e0b')
GRAY = HexColor('#64748b')
LIGHT_BG = HexColor('#f1f5f9')
WHITE = HexColor('#ffffff')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS_DIR = os.path.join(BASE_DIR, 'docs', 'screenshots')
OUTPUT = os.path.join(BASE_DIR, 'app', 'static', 'manual', 'Manual_SGI_Vanti.pdf')
URL = 'https://sgi-vanti.onrender.com'

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

doc = SimpleDocTemplate(
    OUTPUT, pagesize=letter,
    topMargin=0.8 * inch, bottomMargin=0.7 * inch,
    leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    title='Manual de Operacion - SGI Vanti',
    author='Brayan G. y Equipo de Herramientas',
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle('CoverTitle', fontSize=28, textColor=DARK, spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('CoverSub', fontSize=14, textColor=ACCENT, spaceAfter=10, alignment=TA_CENTER))
styles.add(ParagraphStyle('Section', fontSize=18, textColor=DARK, spaceBefore=16, spaceAfter=8, fontName='Helvetica-Bold', borderColor=ACCENT, borderWidth=2, borderPadding=4))
styles.add(ParagraphStyle('Sub', fontSize=13, textColor=ACCENT, spaceBefore=12, spaceAfter=5, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('Body', fontSize=10, textColor=DARK, spaceAfter=5, leading=14, alignment=TA_JUSTIFY))
styles.add(ParagraphStyle('BulletCustom', fontSize=10, textColor=DARK, spaceAfter=3, leading=13, leftIndent=20, bulletIndent=10))
styles.add(ParagraphStyle('Caption', fontSize=8, textColor=GRAY, alignment=TA_CENTER, spaceAfter=8, spaceBefore=2, fontName='Helvetica-Oblique'))
styles.add(ParagraphStyle('SmallGray', fontSize=8, textColor=GRAY, alignment=TA_CENTER))
styles.add(ParagraphStyle('TH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER))
styles.add(ParagraphStyle('TD', fontSize=9, textColor=DARK, leading=11))
styles.add(ParagraphStyle('TDC', fontSize=9, textColor=DARK, alignment=TA_CENTER, leading=11))
styles.add(ParagraphStyle('CaseTitle', fontSize=11, textColor=PURPLE, spaceBefore=10, spaceAfter=4, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('CaseStep', fontSize=10, textColor=DARK, spaceAfter=3, leftIndent=15, leading=13))
styles.add(ParagraphStyle('Note', fontSize=9, textColor=GRAY, spaceAfter=5, leading=12, leftIndent=10, alignment=TA_JUSTIFY))

story = []


def add_screenshot(filename, caption, width=5.5 * inch):
    path = os.path.join(SS_DIR, filename)
    if os.path.exists(path):
        img = Image(path, width=width, height=width * 0.6)
        img.hAlign = 'CENTER'
        story.append(img)
    story.append(Paragraph(caption, styles['Caption']))


def bullets(items, style='BulletCustom'):
    for b in items:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {b}', styles[style]))


def table(data, col_widths, header_color=DARK):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def th(txt):
    return Paragraph(txt, styles['TH'])


def td(txt):
    return Paragraph(txt, styles['TD'])


def tdc(txt):
    return Paragraph(txt, styles['TDC'])


# ============================================================
# PORTADA
# ============================================================
story.append(Spacer(1, 1.4 * inch))
story.append(Paragraph('Manual de Operacion', styles['CoverTitle']))
story.append(Paragraph('SGI Vanti', styles['CoverTitle']))
story.append(Spacer(1, 0.2 * inch))
story.append(HRFlowable(width='60%', thickness=3, color=ACCENT, spaceAfter=12))
story.append(Paragraph('Sistema de Gestion de Imposibilidades y Rechazos', styles['CoverSub']))
story.append(Paragraph('Vanti S.A. ESP', styles['CoverSub']))
story.append(Spacer(1, 0.8 * inch))
story.append(Paragraph('Elaborado por:', styles['SmallGray']))
story.append(Paragraph('<b>Brayan G. y Equipo de Herramientas</b>', styles['CoverSub']))
story.append(Spacer(1, 0.5 * inch))
story.append(Paragraph('Mayo 2026 - Version 1.0', styles['SmallGray']))
story.append(Paragraph(URL, styles['SmallGray']))
story.append(Paragraph('Documento Confidencial', styles['SmallGray']))
story.append(PageBreak())

# ============================================================
# CONTENIDO
# ============================================================
story.append(Paragraph('Contenido', styles['Section']))
toc = [
    '1. Introduccion al Sistema',
    '2. Acceso y Login',
    '3. Roles y Permisos',
    '4. Conceptos Clave (BP, Firma, Clasificacion)',
    '5. Estados de la Tarea',
    '6. Flujo Administrador - Carga de Cartera (Caso de Uso)',
    '7. Flujo Firma / Contratista - Gestion (Caso de Uso)',
    '8. Flujo Gestor - Validacion (Caso de Uso)',
    '9. Flujo Ejecutivo - Visibilidad y Cartas (Caso de Uso)',
    '10. Panel de Subsanacion del Administrador',
    '11. Clasificacion de Cartera ZACO / INSO',
    '12. Notificaciones (WhatsApp + Email)',
    '13. Mesa de Ayuda (Tickets de Soporte)',
    '14. Diagrama de Proceso (BPMN) y Documentacion',
    '15. Credenciales y Buenas Practicas',
]
for t in toc:
    story.append(Paragraph(t, styles['Body']))
story.append(PageBreak())

# ============================================================
# 1. INTRODUCCION
# ============================================================
story.append(Paragraph('1. Introduccion al Sistema', styles['Section']))
story.append(Paragraph(
    'SGI Vanti es una plataforma web para la gestion del ciclo completo de las imposibilidades '
    'y rechazos de conexion de servicio de gas natural. Centraliza la asignacion de la cartera a '
    'las firmas instaladoras y contratistas, la carga de soportes, la validacion por parte del '
    'gestor y el ejecutivo, y el cierre del caso, con notificaciones automaticas por WhatsApp y '
    'correo electronico en cada paso.', styles['Body']))
story.append(Paragraph('Capacidades principales:', styles['Sub']))
bullets([
    'Carga masiva de la cartera desde Excel con plantilla guiada',
    'Asignacion automatica por BP_Firma a firmas y contratistas',
    'Diferenciacion entre Imposibilidades (ZACO) y Rechazos (INSO)',
    'Estados de tarea simplificados y unificados para todos los roles',
    'Notificaciones agrupadas por BP via WhatsApp (UltraMsg) y Email (SendGrid)',
    'Panel de subsanacion del administrador (reactivar, devolver, finalizar)',
    'Mesa de Ayuda integrada para reporte y escalamiento de incidentes',
    'Generacion de cartas de imposibilidad para el cliente final',
    'Diagrama de proceso BPMN y documentacion publica en el login',
])
story.append(PageBreak())

# ============================================================
# 2. ACCESO Y LOGIN
# ============================================================
story.append(Paragraph('2. Acceso y Login', styles['Section']))
story.append(Paragraph('Acceda al sistema desde cualquier navegador (PC o movil):', styles['Body']))
story.append(Paragraph(f'<b>URL:</b> {URL}', styles['Body']))
add_screenshot('01_login.png', 'Figura 1: Pantalla de inicio de sesion de SGI Vanti')
story.append(Paragraph(
    'Ingrese su usuario y contrasena. El sistema lo redirige automaticamente al panel que '
    'corresponde a su rol. En el primer ingreso el sistema solicitara cambiar la contrasena '
    'temporal por una personal.', styles['Body']))
story.append(Paragraph(
    'Desde el login tambien puede consultar, sin necesidad de iniciar sesion, la documentacion '
    'del proceso y el diagrama de flujo BPMN de la herramienta.', styles['Note']))
story.append(PageBreak())

# ============================================================
# 3. ROLES Y PERMISOS
# ============================================================
story.append(Paragraph('3. Roles y Permisos', styles['Section']))
story.append(Paragraph(
    'Cada usuario tiene un rol que determina que puede ver y hacer. La visibilidad de la cartera '
    'se filtra automaticamente por el BP_Firma asociado al usuario.', styles['Body']))
roles = [
    [th('Rol'), th('Funcion principal'), th('Que ve')],
    [td('Administrador'), td('Carga la cartera, gestiona usuarios, subsana casos y configura catalogos.'), tdc('Todo')],
    [td('Firma'), td('Titular del BP. Gestiona las imposibilidades de su cartera y carga soportes.'), tdc('Su cartera (BP)')],
    [td('Contratista'), td('Subcontratado por una firma. Carga soportes de los casos asignados.'), tdc('Su cartera (BP)')],
    [td('Gestor'), td('Valida los soportes de la firma: finaliza o devuelve el caso.'), tdc('Casos asignados')],
    [td('Ejecutivo'), td('Gestion de cartera. Visibilidad de todos los BP que administra, cartas y solicitud de correccion.'), tdc('BP que administra')],
]
story.append(table(roles, [1.3 * inch, 3.5 * inch, 1.3 * inch]))
story.append(Paragraph(
    '<b>Firma vs Contratista:</b> ambos comparten el mismo panel de trabajo, pero la firma es la '
    'titular del BP y el contratista es subcontratado. El campo tipo_firma los distingue.', styles['Note']))
story.append(PageBreak())

# ============================================================
# 4. CONCEPTOS CLAVE
# ============================================================
story.append(Paragraph('4. Conceptos Clave', styles['Section']))
concept = [
    [th('Concepto'), th('Descripcion')],
    [td('<b>BP_Firma</b>'), td('Codigo que identifica a la firma o contratista. Es la llave que vincula cada negocio de la cartera con el usuario que debe gestionarlo.')],
    [td('<b>tipo_firma</b>'), td('Indica si el usuario es "firma" (titular del BP) o "contratista" (subcontratado).')],
    [td('<b>tipo_negacion</b>'), td('Distingue entre "imposibilidad" (causa tecnica) y "rechazo" (la firma o el cliente rechaza el negocio).')],
    [td('<b>Clasificacion</b>'), td('Cartera a la que pertenece el caso: ZACO (imposibilidades / construccion) o INSO (rechazos / interventorias).')],
    [td('<b>Codigo de imposibilidad</b>'), td('Codigo numerico del tipo de anomalia proveniente de Power BI.')],
    [td('<b>Filial</b>'), td('Sucursal o regional propietaria del negocio (visible para la firma).')],
    [td('<b>Tipo de tarea</b>'), td('Estandar (gestion de soportes) o Carta (requiere elaborar carta al cliente).')],
]
story.append(table(concept, [1.6 * inch, 4.5 * inch]))
story.append(PageBreak())

# ============================================================
# 5. ESTADOS
# ============================================================
story.append(Paragraph('5. Estados de la Tarea', styles['Section']))
story.append(Paragraph(
    'Para mantener la operacion clara y uniforme entre el area interna y las firmas instaladoras, '
    'los estados se simplificaron a un conjunto unico y comun a todos los perfiles.', styles['Body']))
estados = [
    [th('Estado'), th('Significado'), th('Quien lo activa')],
    [tdc('<font color="#64748b"><b>Pendiente</b></font>'), td('Caso recien cargado o devuelto; requiere accion de la firma.'), tdc('Admin / sistema')],
    [tdc('<font color="#3b82f6"><b>Soportes cargados</b></font>'), td('La firma cargo los soportes y comentarios del caso.'), tdc('Firma / Contratista')],
    [tdc('<font color="#f59e0b"><b>Caso escalado</b></font>'), td('Se abrio un ticket de Mesa de Ayuda sobre el caso.'), tdc('Sistema (soporte)')],
    [tdc('<font color="#ef4444"><b>Rechazado</b></font>'), td('El caso fue marcado como no valido / rechazo.'), tdc('Admin / Gestor')],
    [tdc('<font color="#22c55e"><b>Finalizado</b></font>'), td('Caso cerrado y gestionado completamente.'), tdc('Admin / Gestor')],
]
story.append(table(estados, [1.5 * inch, 3.3 * inch, 1.3 * inch]))
story.append(Paragraph(
    'Para el flujo de cartas existen ademas dos estados internos: "Carta pendiente revision" y '
    '"Carta enviada", usados por el ejecutivo. Los estados antiguos de versiones previas se '
    'conservan solo para visualizacion historica.', styles['Note']))
story.append(PageBreak())

# ============================================================
# 6. FLUJO ADMIN
# ============================================================
story.append(Paragraph('6. Flujo Administrador - Carga de Cartera', styles['Section']))
story.append(Paragraph(
    '<b>Escenario:</b> El administrador recibe el reporte mensual de imposibilidades y rechazos y '
    'lo carga a la plataforma para distribuirlo entre las firmas.', styles['Body']))
story.append(Paragraph('Caso de Uso: Carga y distribucion de la cartera mensual', styles['CaseTitle']))
admin_steps = [
    '<b>Paso 1:</b> El admin descarga la plantilla Excel desde "Cargar Excel". La plantilla incluye una hoja de instrucciones y resalta en naranja las columnas clave.',
    '<b>Paso 2:</b> Llena la plantilla. Las columnas obligatorias son Orden, BP_Firma, Gestor, Ejecutivo y Tarea. Define Tipo_Negacion (imposibilidad/rechazo) y Clasificacion (ZACO/INSO); si se deja vacia, se deriva automaticamente.',
    '<b>Paso 3:</b> Sube el archivo. El sistema omite las ordenes duplicadas y crea solo los registros nuevos.',
    '<b>Paso 4:</b> Si una firma o ejecutivo no existe como usuario, el sistema lo crea automaticamente con su BP y una contrasena temporal.',
    '<b>Paso 5:</b> El sistema envia un resumen por WhatsApp y Email a cada BP, agrupando la cantidad de negocios cargados (no satura con el detalle completo).',
    '<b>Paso 6:</b> El admin revisa el resultado: cuantas notificaciones se enviaron y que BP quedaron sin destinatario configurado.',
]
for s in admin_steps:
    story.append(Paragraph(s, styles['CaseStep']))
add_screenshot('02_admin_dashboard.png', 'Figura 2: Vista maestra de tareas del administrador')
story.append(PageBreak())

# ============================================================
# 7. FLUJO FIRMA / CONTRATISTA
# ============================================================
story.append(Paragraph('7. Flujo Firma / Contratista - Gestion', styles['Section']))
story.append(Paragraph(
    '<b>Escenario:</b> La firma "Alvigas" recibe la notificacion de nuevos negocios y debe gestionar '
    'sus imposibilidades cargando los soportes correspondientes.', styles['Body']))
story.append(Paragraph('Caso de Uso: Cargue de soportes de una imposibilidad', styles['CaseTitle']))
firma_steps = [
    '<b>Paso 1:</b> La firma ingresa y ve "Mi Cartera" filtrada por su BP, con tarjetas de conteo por estado y los filtros de busqueda (estado, cartera ZACO/INSO, cuenta contrato, orden).',
    '<b>Paso 2:</b> Identifica un caso en estado Pendiente. Lee la direccion, el tipo de imposibilidad y el codigo.',
    '<b>Paso 3:</b> Escribe un comentario explicando la gestion y adjunta la evidencia (foto o documento).',
    '<b>Paso 4:</b> Presiona "Marcar como Gestionado". El caso pasa a estado "Soportes cargados" y se notifica al gestor.',
    '<b>Paso 5:</b> Para casos tipo Carta, presiona "Gestionar Carta" y diligencia los datos del cliente para que el ejecutivo genere el documento.',
    '<b>Paso 6:</b> Puede descargar toda su cartera en Excel desde "Descargar Cartera" y actualizar sus datos de contacto en "Mi Perfil".',
]
for s in firma_steps:
    story.append(Paragraph(s, styles['CaseStep']))
add_screenshot('03_contratista.png', 'Figura 3: Panel "Mi Cartera" de la firma / contratista')
story.append(PageBreak())

# ============================================================
# 8. FLUJO GESTOR
# ============================================================
story.append(Paragraph('8. Flujo Gestor - Validacion', styles['Section']))
story.append(Paragraph(
    '<b>Escenario:</b> El gestor revisa los soportes que cargo la firma y decide si el caso se '
    'finaliza o se devuelve para correccion.', styles['Body']))
story.append(Paragraph('Caso de Uso: Validacion de soportes', styles['CaseTitle']))
gestor_steps = [
    '<b>Paso 1:</b> El gestor ve los casos asignados a su nombre con el soporte adjunto de la firma.',
    '<b>Paso 2:</b> Abre el adjunto y verifica que la evidencia sea clara y suficiente.',
    '<b>Paso 3a:</b> Si todo esta correcto, agrega un comentario y presiona "Finalizar Caso". El estado pasa a Finalizado y se notifica a la firma.',
    '<b>Paso 3b:</b> Si los soportes son insuficientes, presiona "Devolver a Contratista". El caso vuelve a Pendiente con la observacion y la firma es notificada.',
]
for s in gestor_steps:
    story.append(Paragraph(s, styles['CaseStep']))
add_screenshot('04_gestor.png', 'Figura 4: Bandeja de validacion del gestor')
story.append(PageBreak())

# ============================================================
# 9. FLUJO EJECUTIVO
# ============================================================
story.append(Paragraph('9. Flujo Ejecutivo - Visibilidad y Cartas', styles['Section']))
story.append(Paragraph(
    '<b>Escenario:</b> El ejecutivo de Gestion de Cartera supervisa el estado de los negocios de las '
    'firmas que administra, gestiona las cartas y solicita correcciones cuando los soportes no son claros.',
    styles['Body']))
story.append(Paragraph('Caso de Uso: Supervision y solicitud de correccion', styles['CaseTitle']))
exec_steps = [
    '<b>Paso 1:</b> El ejecutivo ve el "Panel Ejecutivo" con la visibilidad completa de todos los BP que administra y un resumen por firma.',
    '<b>Paso 2:</b> El listado muestra Orden, Cuenta Contrato, BP, Cartera (ZACO/INSO), Filial, Tipo, Estado y Gestion.',
    '<b>Paso 3:</b> Si un soporte no es claro, usa la accion "Solicitar correccion": escribe la inconsistencia, adjunta un archivo de referencia y envia.',
    '<b>Paso 4:</b> El caso regresa a la firma en estado Pendiente y se le notifica por WhatsApp y Email el detalle de lo que debe corregir.',
    '<b>Paso 5:</b> Para casos tipo Carta, edita los datos, genera el documento Word y lo marca como "Enviada". Tambien puede descargar todas las cartas pendientes en un ZIP.',
]
for s in exec_steps:
    story.append(Paragraph(s, styles['CaseStep']))
add_screenshot('05_ejecutivo.png', 'Figura 5: Panel Ejecutivo con resumen por BP y acciones')
story.append(PageBreak())

# ============================================================
# 10. PANEL DE SUBSANACION
# ============================================================
story.append(Paragraph('10. Panel de Subsanacion del Administrador', styles['Section']))
story.append(Paragraph(
    'Desde la vista maestra, el admin abre cualquier caso (icono de herramientas) y accede a un panel '
    'unico de gestion que permite corregir y reencausar un negocio. Cada accion notifica a la firma por '
    'WhatsApp y Email.', styles['Body']))
acc = [
    [th('Accion'), th('Efecto sobre el caso')],
    [td('<b>Solo guardar</b>'), td('Guarda cambios en comentarios sin cambiar el estado.')],
    [td('<b>Reactivar</b>'), td('Vuelve el caso a Pendiente para que la firma suba nuevos soportes.')],
    [td('<b>Devolver para ajustes</b>'), td('Regresa el caso a Pendiente con el motivo indicado.')],
    [td('<b>Marcar NO VALIDA</b>'), td('Marca como Rechazado, fija tipo_negacion=rechazo y clasificacion INSO.')],
    [td('<b>Finalizar</b>'), td('Cierra el caso (estado Finalizado).')],
    [td('<b>Cambiar estado</b>'), td('Asigna manualmente cualquier estado activo.')],
    [td('<b>Cambiar tipo negacion</b>'), td('Alterna entre imposibilidad y rechazo.')],
]
story.append(table(acc, [1.9 * inch, 4.2 * inch]))
add_screenshot('06_subsanacion.png', 'Figura 6: Panel de gestion y subsanacion del administrador')
story.append(PageBreak())

# ============================================================
# 11. CLASIFICACION ZACO / INSO
# ============================================================
story.append(Paragraph('11. Clasificacion de Cartera ZACO / INSO', styles['Section']))
story.append(Paragraph(
    'La herramienta diferencia dos carteras para una gestion adecuada de cada tipo de negocio:',
    styles['Body']))
clasif = [
    [th('Clasificacion'), th('Cartera'), th('Asociada a')],
    [tdc('<font color="#6366f1"><b>ZACO</b></font>'), td('Imposibilidades'), td('Procesos de construccion')],
    [tdc('<font color="#ef4444"><b>INSO</b></font>'), td('Rechazos'), td('Interventorias')],
]
story.append(table(clasif, [1.4 * inch, 2.2 * inch, 2.5 * inch]))
story.append(Paragraph(
    'La clasificacion puede venir explicita en el Excel de carga (columna Clasificacion) o derivarse '
    'automaticamente del tipo de negacion: rechazo se asigna a INSO y cualquier otro caso a ZACO. '
    'Existe un filtro "Cartera" en todos los paneles y una etiqueta de color en cada fila.', styles['Body']))
story.append(PageBreak())

# ============================================================
# 12. NOTIFICACIONES
# ============================================================
story.append(Paragraph('12. Notificaciones (WhatsApp + Email)', styles['Section']))
story.append(Paragraph(
    'El sistema notifica los eventos relevantes por dos canales, respetando las preferencias de cada '
    'usuario (puede activar o desactivar cada canal en su perfil).', styles['Body']))
notif = [
    [th('Evento'), th('Destinatario'), th('Canal')],
    [td('Carga de nuevos negocios'), td('Firma / Contratista (por BP)'), tdc('WhatsApp + Email')],
    [td('Soportes cargados'), td('Gestor asignado'), tdc('WhatsApp + Email')],
    [td('Caso devuelto / reactivado'), td('Firma'), tdc('WhatsApp + Email')],
    [td('Solicitud de correccion'), td('Firma'), tdc('WhatsApp + Email')],
    [td('Carta enviada'), td('Firma'), tdc('WhatsApp + Email')],
    [td('Ticket de soporte creado'), td('Administradores'), tdc('WhatsApp + Email')],
    [td('Respuesta a ticket'), td('Quien reporto'), tdc('WhatsApp + Email')],
]
story.append(table(notif, [2.4 * inch, 2.2 * inch, 1.5 * inch]))
story.append(Paragraph(
    '<b>Recordatorio masivo:</b> el administrador puede enviar a todas las firmas un recordatorio de sus '
    'negocios pendientes agrupados por BP. Antes de enviar, el sistema muestra una vista previa y pide '
    'confirmacion explicita para evitar envios accidentales.', styles['Note']))
story.append(Paragraph(
    'Los mensajes de WhatsApp se envian mediante UltraMsg y los correos mediante SendGrid. Cada envio '
    'queda registrado para auditoria.', styles['Note']))
story.append(PageBreak())

# ============================================================
# 13. MESA DE AYUDA
# ============================================================
story.append(Paragraph('13. Mesa de Ayuda (Tickets de Soporte)', styles['Section']))
story.append(Paragraph(
    'Cualquier usuario puede reportar un error o escalar un incidente desde el boton "Reportar Error". '
    'Esto crea un ticket que notifica a los administradores y, si esta asociado a una orden, marca el '
    'caso como "Escalado".', styles['Body']))
story.append(Paragraph('Categorias disponibles:', styles['Sub']))
bullets([
    'No puedo cambiar el estado del negocio',
    'No puedo cargar soportes / evidencia',
    'Error de visualizacion en la plataforma',
    'No recibo notificaciones (WhatsApp / Email)',
    'Problemas de acceso / credenciales',
    'Datos incorrectos en la cartera',
    'Otro (describir en el mensaje)',
])
story.append(Paragraph(
    'El administrador gestiona los tickets desde su bandeja, cambia el estado (abierto, en proceso, '
    'resuelto, cerrado) y responde; la respuesta se notifica automaticamente a quien reporto.', styles['Body']))
add_screenshot('07_soporte.png', 'Figura 7: Formulario de reporte a la Mesa de Ayuda')
story.append(PageBreak())

# ============================================================
# 14. BPMN Y DOCUMENTACION
# ============================================================
story.append(Paragraph('14. Diagrama de Proceso (BPMN) y Documentacion', styles['Section']))
story.append(Paragraph(
    'Desde la pantalla de login, sin necesidad de iniciar sesion, estan disponibles dos recursos de '
    'consulta:', styles['Body']))
bullets([
    '<b>Documentacion:</b> describe que hace la herramienta, los roles y el ciclo de vida del caso.',
    '<b>Diagrama BPMN:</b> mapa visual del proceso con carriles por rol (Admin, Firma/Contratista, '
    'Gestor, Ejecutivo, Sistema), actividades y estados.',
])
story.append(Paragraph(
    'Este diagrama sirve como referencia para mapear lo que hace la app y se debe actualizar cada vez '
    'que el proceso cambie.', styles['Note']))
add_screenshot('08_bpmn.png', 'Figura 8: Diagrama BPMN del proceso de imposibilidades')
story.append(PageBreak())

# ============================================================
# 15. CREDENCIALES Y BUENAS PRACTICAS
# ============================================================
story.append(Paragraph('15. Credenciales y Buenas Practicas', styles['Section']))
story.append(Paragraph(f'<b>URL:</b> {URL}', styles['Body']))
cred = [
    [th('Usuario'), th('Contrasena inicial'), th('Rol')],
    [td('admin'), td('Vanti2026*'), tdc('Administrador')],
    [td('(BP de la firma)'), td('igual al usuario'), tdc('Firma / Contratista')],
    [td('(nombre del gestor)'), td('igual al usuario'), tdc('Gestor')],
    [td('(nombre del ejecutivo)'), td('igual al usuario'), tdc('Ejecutivo')],
]
story.append(table(cred, [2.0 * inch, 2.0 * inch, 1.6 * inch]))
story.append(Paragraph(
    'Los usuarios de firma, gestor y ejecutivo se crean automaticamente al cargar la cartera con una '
    'contrasena temporal igual al nombre de usuario; el sistema obliga a cambiarla en el primer ingreso.',
    styles['Note']))
story.append(Paragraph('Buenas practicas:', styles['Sub']))
bullets([
    'Cada firma debe mantener su celular y correo actualizados en "Mi Perfil" para recibir notificaciones.',
    'Adjuntar siempre evidencia clara y legible al gestionar un caso.',
    'Usar la Mesa de Ayuda para reportar errores en lugar de gestionar datos incorrectos.',
    'El administrador nunca debe borrar la base de datos; usar las acciones seguras de subsanacion.',
])
story.append(Spacer(1, 0.6 * inch))
story.append(HRFlowable(width='100%', thickness=1, color=GRAY))
story.append(Spacer(1, 0.15 * inch))
story.append(Paragraph('<b>Elaborado por: Brayan G. y Equipo de Herramientas</b>', styles['SmallGray']))
story.append(Paragraph('Vanti S.A. ESP - Mayo 2026 - Version 1.0', styles['SmallGray']))
story.append(Paragraph('Generado automaticamente para SGI Vanti', styles['SmallGray']))

doc.build(story)
print(f'PDF generado: {OUTPUT}')
