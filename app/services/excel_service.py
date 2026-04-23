import io
import pandas as pd


# --- Column definitions ---
IMPOSIBILIDADES_COLUMNS = [
    'Sociedad', 'Cuenta_Contrato', 'Orden', 'Estatus_de_ Usuario',
    'BP_Firma', 'Tipo_Asignacion', 'Filial', 'Malla',
    'Direccion_Punto_Suministro', 'Nombre_del_solicitante',
    'Descripcion_Mercado', 'N_Municipio', 'N_BP_Firma', 'Estado',
    'Tipo_Negacion', 'Motivo_Rechazo',
    'Codigo_Imposibilidad', 'Imposibilidad_1',
    'latitud', 'longitud', 'Gestor', 'Ejecutivo', 'Tarea'
]

IMPOSIBILIDADES_REQUIRED = ['Orden', 'BP_Firma', 'Gestor', 'Ejecutivo', 'Tarea']

USUARIOS_COLUMNS = ['username', 'email', 'rol', 'tipo_firma', 'bp_firma', 'celular', 'full_name']

USUARIOS_REQUIRED = ['username', 'rol']


def generate_imposibilidades_template(with_examples=False):
    """Generate XLSX template for imposibilidades upload."""
    if with_examples:
        data = [
            {
                'Sociedad': '1000', 'Cuenta_Contrato': '300012345',
                'Orden': 'ORD-001', 'Estatus_de_ Usuario': 'Activo',
                'BP_Firma': 'FIRMA_ABC', 'Tipo_Asignacion': 'firma',
                'Filial': 'VANTI BOGOTA', 'Malla': 'M-01',
                'Direccion_Punto_Suministro': 'Calle 100 #15-30, Bogotá',
                'Nombre_del_solicitante': 'Juan Pérez',
                'Descripcion_Mercado': 'Residencial', 'N_Municipio': 'Bogotá',
                'N_BP_Firma': '900123456', 'Estado': 'Conectado',
                'Tipo_Negacion': 'imposibilidad', 'Motivo_Rechazo': '',
                'Codigo_Imposibilidad': 161,
                'Imposibilidad_1': 'Distancia de acometida',
                'latitud': '4.6789', 'longitud': '-74.0456',
                'Gestor': 'gestor1', 'Ejecutivo': 'ejecutivo1', 'Tarea': 'carta'
            },
            {
                'Sociedad': '1000', 'Cuenta_Contrato': '300067890',
                'Orden': 'ORD-002', 'Estatus_de_ Usuario': 'Activo',
                'BP_Firma': 'FIRMA_XYZ', 'Tipo_Asignacion': 'contratista',
                'Filial': 'VANTI CUNDINAMARCA', 'Malla': 'M-02',
                'Direccion_Punto_Suministro': 'Carrera 7 #45-12, Bogotá',
                'Nombre_del_solicitante': 'María López',
                'Descripcion_Mercado': 'Comercial', 'N_Municipio': 'Bogotá',
                'N_BP_Firma': '900654321', 'Estado': 'Suspendido',
                'Tipo_Negacion': 'rechazo', 'Motivo_Rechazo': 'Cliente no autorizo acceso al predio',
                'Codigo_Imposibilidad': 32,
                'Imposibilidad_1': 'Servidumbre',
                'latitud': '4.7012', 'longitud': '-74.0678',
                'Gestor': 'gestor1', 'Ejecutivo': 'ejecutivo1', 'Tarea': 'estandar'
            },
            {
                'Sociedad': '2000', 'Cuenta_Contrato': '300011111',
                'Orden': 'ORD-003', 'Estatus_de_ Usuario': 'Activo',
                'BP_Firma': 'FIRMA_ABC', 'Tipo_Asignacion': 'firma',
                'Filial': 'VANTI BOYACA', 'Malla': 'M-03',
                'Direccion_Punto_Suministro': 'Av. Boyacá #80-15, Bogotá',
                'Nombre_del_solicitante': 'Carlos Rodríguez',
                'Descripcion_Mercado': 'Industrial', 'N_Municipio': 'Soacha',
                'N_BP_Firma': '900123456', 'Estado': 'Conectado',
                'Tipo_Negacion': 'imposibilidad', 'Motivo_Rechazo': '',
                'Codigo_Imposibilidad': 102,
                'Imposibilidad_1': 'Vía vehicular',
                'latitud': '4.5678', 'longitud': '-74.1234',
                'Gestor': 'gestor1', 'Ejecutivo': '', 'Tarea': 'estandar'
            },
        ]
        df = pd.DataFrame(data, columns=IMPOSIBILIDADES_COLUMNS)
    else:
        df = pd.DataFrame(columns=IMPOSIBILIDADES_COLUMNS)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Imposibilidades')

        workbook = writer.book
        worksheet = writer.sheets['Imposibilidades']

        # Format headers
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#6c5ce7', 'font_color': 'white',
            'border': 1, 'text_wrap': True
        })
        required_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#e74c3c', 'font_color': 'white',
            'border': 1, 'text_wrap': True
        })
        key_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#f59e0b', 'font_color': 'white',
            'border': 1, 'text_wrap': True
        })

        KEY_COLS = {'Tipo_Asignacion', 'Filial', 'Codigo_Imposibilidad', 'Tipo_Negacion', 'Motivo_Rechazo'}
        for col_num, col_name in enumerate(IMPOSIBILIDADES_COLUMNS):
            if col_name in IMPOSIBILIDADES_REQUIRED:
                fmt = required_fmt
            elif col_name in KEY_COLS:
                fmt = key_fmt
            else:
                fmt = header_fmt
            worksheet.write(0, col_num, col_name, fmt)
            worksheet.set_column(col_num, col_num, 20)

        # Add instructions sheet
        instructions_ws = workbook.add_worksheet('Instrucciones')
        bold = workbook.add_format({'bold': True, 'font_size': 14})
        sub_bold = workbook.add_format({'bold': True, 'font_size': 11, 'font_color': '#6c5ce7'})
        instructions_ws.write(0, 0, 'Instrucciones para Carga de Imposibilidades', bold)
        instructions = [
            '',
            'Columnas OBLIGATORIAS (en rojo): Orden, BP_Firma, Gestor, Ejecutivo, Tarea',
            'Columnas CLAVE (en naranja): Tipo_Asignacion, Filial, Codigo_Imposibilidad',
            '',
            'Descripción de columnas:',
            '- Orden: Identificador único de la orden (no puede repetirse)',
            '- BP_Firma: Username/ID del contratista o firma asignada (filtra la cartera que cada usuario ve)',
            '- Tipo_Asignacion: "firma" o "contratista" — aclara si BP_Firma pertenece a una firma o contratista',
            '- Filial: Filial/Sociedad dueña del negocio (visible al contratista)',
            '- Tipo_Negacion: "imposibilidad" (tecnica, estandar) o "rechazo" (la firma rechaza el negocio)',
            '- Motivo_Rechazo: si Tipo_Negacion=rechazo, describir el motivo del rechazo',
            '- Codigo_Imposibilidad: Código numérico de PowerBI (1-172). Se usa para trazabilidad',
            '- Imposibilidad_1: Descripción del tipo de imposibilidad',
            '- Gestor: Username del gestor asignado',
            '- Ejecutivo: Username del ejecutivo (solo para tareas tipo "carta")',
            '- Tarea: Tipo de tarea ("carta" o "estandar")',
            '- latitud/longitud: Coordenadas del punto (ej: 4.6789 / -74.0456)',
            '',
            'Notas:',
            '- Si el contratista o ejecutivo no existe, se creará automáticamente',
            '- Los duplicados por Orden se omitirán (NO se sobrescriben)',
            '- Para tipo "carta", se creará una carta vacía automáticamente',
            '- Tipo_Asignacion por defecto es "contratista" si no se especifica',
        ]
        for i, line in enumerate(instructions):
            instructions_ws.write(i + 1, 0, line)
        instructions_ws.set_column(0, 0, 80)

    output.seek(0)
    return output


def generate_usuarios_template(with_examples=False):
    """Generate XLSX template for bulk user upload."""
    if with_examples:
        data = [
            {'username': 'FIRMA_ABC', 'email': 'firma_abc@empresa.com',
             'rol': 'firma', 'tipo_firma': 'firma', 'bp_firma': '1000008472',
             'celular': '573001234567', 'full_name': 'Ingenieria de Gas Natural'},
            {'username': 'contratista1', 'email': 'contratista1@empresa.com',
             'rol': 'contratista', 'tipo_firma': 'contratista', 'bp_firma': '1000008472',
             'celular': '573001112233', 'full_name': 'Pedro Gómez'},
            {'username': 'gestor2', 'email': 'gestor2@vanti.com',
             'rol': 'gestor', 'tipo_firma': '', 'bp_firma': '', 'celular': '573009876543',
             'full_name': 'Ana García'},
            {'username': 'ejecutivo2', 'email': 'ejecutivo2@vanti.com',
             'rol': 'ejecutivo', 'tipo_firma': '', 'bp_firma': '', 'celular': '',
             'full_name': 'Luis Martínez'},
        ]
        df = pd.DataFrame(data, columns=USUARIOS_COLUMNS)
    else:
        df = pd.DataFrame(columns=USUARIOS_COLUMNS)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Usuarios')

        workbook = writer.book
        worksheet = writer.sheets['Usuarios']

        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#6c5ce7', 'font_color': 'white', 'border': 1
        })
        required_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#e74c3c', 'font_color': 'white', 'border': 1
        })
        key_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#f59e0b', 'font_color': 'white', 'border': 1
        })

        KEY_COLS = {'tipo_firma', 'bp_firma'}
        for col_num, col_name in enumerate(USUARIOS_COLUMNS):
            if col_name in USUARIOS_REQUIRED:
                fmt = required_fmt
            elif col_name in KEY_COLS:
                fmt = key_fmt
            else:
                fmt = header_fmt
            worksheet.write(0, col_num, col_name, fmt)
            worksheet.set_column(col_num, col_num, 20)

        # Instructions
        inst_ws = workbook.add_worksheet('Instrucciones')
        bold = workbook.add_format({'bold': True, 'font_size': 14})
        inst_ws.write(0, 0, 'Instrucciones para Carga Masiva de Usuarios', bold)
        instructions = [
            '',
            'Columnas OBLIGATORIAS (en rojo): username, rol',
            'Columnas CLAVE (en naranja): tipo_firma, bp_firma',
            '',
            'Roles válidos: admin, firma, contratista, gestor, ejecutivo',
            '  - firma: dueno del BP (la firma principal)',
            '  - contratista: subcontratado por la firma (ejecuta trabajo)',
            '  - gestor: valida gestiones',
            '  - ejecutivo: emite cartas al cliente',
            '  - admin: administrador total',
            'Valores tipo_firma (solo para rol contratista): firma, contratista',
            '',
            'Descripción de columnas:',
            '- username: Identificador único del usuario (puede ser el nombre de la firma)',
            '- email: Correo electrónico (para notificaciones)',
            '- rol: Rol del usuario (admin, gestor, contratista, ejecutivo)',
            '- tipo_firma: "firma" (dueña del BP) o "contratista" (subcontratado por una firma)',
            '  Importante: el rol "contratista" es el ACCESO a la plataforma; tipo_firma distingue',
            '  si ese usuario es DUEÑO del BP (firma) o SOLO EJECUTA trabajos (contratista)',
            '- bp_firma: ID del BP — filtra la cartera de tareas que el usuario ve',
            '- celular: Número con código país (ej: 573001234567) para WhatsApp',
            '- full_name: Nombre completo del usuario o razón social',
            '',
            'Notas:',
            '- La contraseña por defecto es "Vanti2026*"',
            '- El usuario recibe notificación por WhatsApp/email de creación con la contraseña temporal',
            '- Deberá cambiar la contraseña en su primer inicio de sesión',
            '- Usuarios duplicados (mismo username) se omitirán (no se sobrescriben)',
        ]
        for i, line in enumerate(instructions):
            inst_ws.write(i + 1, 0, line)
        inst_ws.set_column(0, 0, 80)

    output.seek(0)
    return output


def validate_imposibilidades_upload(df):
    """Validate DataFrame columns for imposibilidades upload."""
    missing = [col for col in IMPOSIBILIDADES_REQUIRED if col not in df.columns]
    if missing:
        return False, f"Columnas faltantes: {', '.join(missing)}"
    return True, ""


def validate_usuarios_upload(df):
    """Validate DataFrame columns for users upload."""
    missing = [col for col in USUARIOS_REQUIRED if col not in df.columns]
    if missing:
        return False, f"Columnas faltantes: {', '.join(missing)}"
    return True, ""
