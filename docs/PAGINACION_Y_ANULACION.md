# Paginación y Anulación Masiva — Vista Maestra del Admin

Guía de uso y de implementación de la paginación (50 por página) y la anulación
masiva de negocios desde el dashboard del administrador (`/admin/`).

---

## 1. Para el usuario (cómo se hace)

### Anular uno o varios
1. Entra como **admin** → dashboard (`/admin/`).
2. En la columna izquierda de la tabla marca la **casilla** de cada negocio.
3. Pulsa **"Anular seleccionados"**.
4. Escribe el **motivo** y confirma. Los negocios quedan en estado **Anulado**
   (no se borran; es reversible y auditable).

### Seleccionar toda la página
- Usa la **casilla del encabezado** o el botón **"Esta página (N)"**: marca los
  hasta 50 registros visibles en la página actual.

### Seleccionar TODOS los que coinciden con el filtro (cruza páginas)
1. Aplica los filtros que quieras (estado, orden, cuenta, clasificación, BP).
2. Marca **"Esta página"**. Aparece un **banner amarillo**.
3. En el banner pulsa **"Seleccionar los X que coinciden con el filtro"**.
4. Pulsa **"Anular seleccionados"** → se anulan **todos** los que cumplen el
   filtro, aunque estén en otras páginas.

> Ejemplo para limpiar negocios de prueba: filtra por `Orden = PRUEBA` (o el
> patrón que uses), selecciona todos los del filtro y anula.

### Avisar a las firmas
- Marca **"Avisar firmas"** antes de anular para enviar la comunicación de
  anulación por **email + WhatsApp** a los usuarios de cada BP afectado.

### Paginación
- 50 registros por página por defecto. Navega con los controles inferiores.
- Puedes cambiar el tamaño con `?per_page=100` (entre 10 y 500).
- Los filtros se conservan al cambiar de página.

---

## 2. Para el desarrollador (cómo está hecho)

### Archivos involucrados
| Archivo | Rol |
|---|---|
| `app/blueprints/admin/routes.py` | Ruta `dashboard()` con paginación + `anulaciones_ejecutar()` |
| `app/templates/dashboard_admin.html` | Tabla, casillas, banner, paginación y JS |
| `app/helpers.py` | `aplicar_filtros_comunes()` — filtros compartidos |

### a) Query y paginación (`dashboard`)
```python
def _query_tareas_admin():
    query = Imposibilidad.query
    query, filtros = aplicar_filtros_comunes(query)   # estado, cuenta, orden, clasificacion
    bp_firma = request.args.get('bp_firma')
    if bp_firma:
        query = query.filter(Imposibilidad.bp_firma.ilike(f'%{bp_firma}%'))
        filtros['bp_firma'] = bp_firma
    return query, filtros

# dashboard():
query, filtros = _query_tareas_admin()
query = query.order_by(Imposibilidad.id.desc())
page = request.args.get('page', 1, type=int)
per_page = max(10, min(request.args.get('per_page', 50, type=int), 500))
pagination = query.paginate(page=page, per_page=per_page, error_out=False)
# filter_qs = querystring de filtros SIN 'page' (para links y para el form de anulacion)
```
El template recibe `pagination`, `tareas=pagination.items`, `total_filtrado=pagination.total`
y `filter_qs`.

### b) Las dos modalidades de selección
El form de anulación es **independiente** (`id="anular-form"`); las casillas se
asocian con el atributo HTML `form="anular-form"` (así no se anidan formularios
con el botón de eliminar de cada fila).

- **Modo página** (`seleccionar_todos_filtro = ""`): se envían los `ids` de las
  casillas marcadas en la página visible.
- **Modo filtro** (`seleccionar_todos_filtro = "1"`): el servidor **ignora** los
  `ids` de la página y reconstruye el query con los filtros vigentes.

> Clave: el `action` del formulario incluye el **querystring de filtros**:
> ```html
> action="{{ url_for('admin.anulaciones_ejecutar') }}{% if filter_qs %}?{{ filter_qs }}{% endif %}"
> ```
> Como los filtros viajan en el querystring (no en el body), `aplicar_filtros_comunes()`
> —que lee de `request.args`— funciona igual en este POST.

### c) Ejecución (`anulaciones_ejecutar`)
```python
if request.form.get('seleccionar_todos_filtro') == '1':
    q, _ = _query_tareas_admin()                       # mismos filtros del dashboard
    q = q.filter(Imposibilidad.estado_tarea != 'anulado')
    ids = [str(r.id) for r in q.with_entities(Imposibilidad.id).all()]
# ... valida ids, confirm, motivo; marca estado='anulado'; opcional comunicacion masiva
```
La anulación **nunca borra**: cambia `estado_tarea` a `'anulado'`, fija
`fecha_gestion_gestor` y deja traza en `comentarios_gestor`.

### d) JavaScript (resumen)
- `modoSeleccion` = `'pagina'` | `'filtro'`.
- `seleccionarPagina(bool)` — marca/limpia las casillas visibles (modo página).
- `seleccionarTodosFiltro()` — activa el flag `seleccionar_todos_filtro=1` (modo filtro);
  **no** marca casillas, solo cambia el contador y el mensaje.
- `confirmarAnulacion()` — pide motivo y confirma; usa `TOTAL_FILTRADO` cuando el
  modo es filtro.

---

## 3. Cómo extenderlo

- **Cambiar el tamaño por defecto:** edita `per_page` en `dashboard()`.
- **Aplicar el patrón a otra acción masiva** (ej. reasignar gestor, exportar
  selección): reutiliza el form independiente + `form="anular-form"` y agrega una
  rama por `request.form.get('accion')` en una nueva ruta, replicando el bloque
  `seleccionar_todos_filtro`.
- **Nuevos filtros:** añádelos en `aplicar_filtros_comunes()` (o en
  `_query_tareas_admin()`) y se respetarán automáticamente en la paginación y en
  la anulación por filtro, porque ambas usan el mismo helper.
