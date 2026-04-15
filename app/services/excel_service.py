import io
import pandas as pd


# --- Column definitions ---
IMPOSIBILIDADES_COLUMNS = [
    'Sociedad', 'Cuenta_Contrato', 'Orden', 'Estatus_de_ Usuario',
    'BP_Firma', 'Malla', 'Direccion_Punto_Suministro', 'Nombre_del_solicitante',
    'Descripcion_Mercado', 'N_Municipio', 'N_BP_Firma', 'Estado',
    'Imposibilidad_1', 'latitud', 'longitud', 'Gestor', 'Ejecutivo', 'Tarea'
]

IMPOSIBILIDADES_REQUIRED = ['Orden', 'BP_Firma', 'Gestor', 'Ejecutivo', 'Tarea']

USUARIOS_COLUMNS = ['username', 'email', 'rol', 'bp_firma', 'celular', 'full_name']

USUARIOS_REQUIRED = ['username', 'rol']


def generate_imposibilidades_template(with_examples=False):
    """Generate XLSX template for imposibilidades upload."""
    if with_examples:
        data = [
            {
                'Sociedad': '1000', 'Cuenta_Contrato': '300012345',
                'Orden': 'ORD-001', 'Estatus_de_ Usuario': 'Activo',
                'BP_Firma': 'FIRMA_ABC', 'Malla': 'M-01',
                'Direccion_Punto_Suministro': 'Calle 100 #15-30, Bogotá',
                'Nombre_del_solicitante': 'Juan Pérez',
                'Descripcion_Mercado': 'Residencial', 'N_Municipio': 'Bogotá',
                'N_BP_Firma': '900123456', 'Estado': 'Conectado',
                'Imposibilidad_1': 'Distancia de acometida',
                'latitud': '4.6789', 'longitud': '-74.0456',
                'Gestor': 'gestor1', 'Ejecutivo': 'ejecutivo1', 'Tarea': 'carta'
            },
            {
                'Sociedad': '1000', 'Cuenta_Contrato': '300067890',
                'Orden': 'ORD-002', 'Estatus_de_ Usuario': 'Activo',
                'BP_Firma': 'FIRMA_XYZ', 'Malla': 'M-02',
                'Direccion_Punto_Suministro': 'Carrera 7 #45-12, Bogotá',
                'Nombre_del_solicitante': 'María López',
                'Descripcion_Mercado': 'Comercial', 'N_Municipio': 'Bogotá',
                'N_BP_Firma': '900654321', 'Estado': 'Suspendido',
                'Imposibilidad_1': 'Servidumbre',
                'latitud': '4.7012', 'longitud': '-74.0678',
                'Gestor': 'gestor1', 'Ejecutivo': 'ejecutivo1', 'Tarea': 'estandar'
            },
            {
                'Sociedad': '2000', 'Cuenta_Contrato': '300011111',
                'Orden': 'ORD-003', 'Estatus_de_ Usuario': 'Activo',
                'BP_Firma': 'FIRMA_ABC', 'Malla': 'M-03',
                'Direccion_Punto_Suministro': 'Av. Boyacá #80-15, Bogotá',
                'Nombre_del_solicitante': 'Carlos Rodríguez',
                'Descripcion_Mercado': 'Industrial', 'N_Municipio': 'Soacha',
                'N_BP_Firma': '900123456', 'Estado': 'Conectado',
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

        for col_num, col_name in enumerate(IMPOSIBILIDADES_COLUMNS):
            fmt = required_fmt if col_name in IMPOSIBILIDADES_REQUIRED else header_fmt
            worksheet.write(0, col_num, col_name, fmt)
            worksheet.set_column(col_num, col_num, 20)

        # Add instructions sheet
        instructions_ws = workbook.add_worksheet('Instrucciones')
        bold = workbook.add_format({'bold': True, 'font_size': 14})
        instructions_ws.write(0, 0, 'Instrucciones para Carga de Imposibilidades', bold)
        instructions = [
            '', 'Columnas OBLIGATORIAS (en rojo): Orden, BP_Firma, Gestor, Ejecutivo, Tarea',
            '', 'Descripción de columnas:',
            '- Orden: Identificador único de la orden (no puede repetirse)',
            '- BP_Firma: Username del contratista asignado',
            '- Gestor: Username del gestor asignado',
            '- Ejecutivo: Username del ejecutivo (solo para tareas tipo "carta")',
            '- Tarea: Tipo de tarea ("carta" o "estandar")',
            '- latitud/longitud: Coordenadas del punto (ej: 4.6789 / -74.0456)',
            '', 'Notas:',
            '- Si el contratista o ejecutivo no existe, se creará automáticamente',
            '- Los duplicados por Orden se omitirán',
            '- Para tipo "carta", se creará una carta vacía automáticamente',
        ]
        for i, line in enumerate(instructions):
            instructions_ws.write(i + 1, 0, line)
        instructions_ws.set_column(0, 0, 70)

    output.seek(0)
    return output


def generate_usuarios_template(with_examples=False):
    """Generate XLSX template for bulk user upload."""
    if with_examples:
        data = [
            {'username': 'contratista1', 'email': 'contratista1@empresa.com',
             'rol': 'contratista', 'bp_firma': 'FIRMA_ABC',
             'celular': '573001234567', 'full_name': 'Pedro Gómez'},
            {'username': 'gestor2', 'email': 'gestor2@vanti.com',
             'rol': 'gestor', 'bp_firma': '', 'celular': '573009876543',
             'full_name': 'Ana García'},
            {'username': 'ejecutivo2', 'email': 'ejecutivo2@vanti.com',
             'rol': 'ejecutivo', 'bp_firma': '', 'celular': '',
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

        for col_num, col_name in enumerate(USUARIOS_COLUMNS):
            fmt = required_fmt if col_name in USUARIOS_REQUIRED else header_fmt
            worksheet.write(0, col_num, col_name, fmt)
            worksheet.set_column(col_num, col_num, 20)

        # Instructions
        inst_ws = workbook.add_worksheet('Instrucciones')
        bold = workbook.add_format({'bold': True, 'font_size': 14})
        inst_ws.write(0, 0, 'Instrucciones para Carga Masiva de Usuarios', bold)
        instructions = [
            '', 'Columnas OBLIGATORIAS (en rojo): username, rol',
            '', 'Roles válidos: admin, gestor, contratista, ejecutivo',
            '', '- username: Identificador único del usuario',
            '- email: Correo electrónico (para notificaciones)',
            '- rol: Rol del usuario en el sistema',
            '- bp_firma: ID de firma (solo para contratistas)',
            '- celular: Número con código país (ej: 573001234567) para WhatsApp',
            '- full_name: Nombre completo del usuario',
            '', 'Notas:',
            '- La contraseña por defecto es "Vanti2026*"',
            '- Los usuarios deberán cambiarla en su primer inicio de sesión',
            '- Usuarios duplicados (mismo username) se omitirán',
        ]
        for i, line in enumerate(instructions):
            inst_ws.write(i + 1, 0, line)
        inst_ws.set_column(0, 0, 60)

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
