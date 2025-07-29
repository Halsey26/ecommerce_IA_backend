import pandas as pd
import panel as pn
import datetime as dt

pn.extension('tabulator')

# Cargar datos
df = pd.read_csv('chatbot.csv', parse_dates=['fecha_inicio', 'fecha_fin'])

# Crear columnas adicionales para análisis temporal
df['hora_inicio'] = df['fecha_inicio'].dt.hour
df['dia_semana'] = df['fecha_inicio'].dt.day_name()
df['semana'] = df['fecha_inicio'].dt.isocalendar().week
df['mes'] = df['fecha_inicio'].dt.month_name()
df['fecha'] = df['fecha_inicio'].dt.date

# Selector de agrupación
agrupamiento = pn.widgets.RadioButtonGroup(
    name='Agrupar por',
    options=['Día', 'Semana', 'Mes'],
    button_type='success'
)

@pn.depends(agrupamiento)
def tabla_agrupada(grupo):
    if grupo == 'Día':
        group = df.groupby('fecha')
    elif grupo == 'Semana':
        group = df.groupby('semana')
    else:  # Mes
        group = df.groupby('mes')

    resumen = group.agg({
        'chatId': 'count',
        'mensajes_totales': 'sum',
        'duracion_sesion': 'mean',
        'porcentaje_user': 'mean'
    }).rename(columns={'chatId': 'cantidad_sesiones'})

    resumen['duracion_sesion'] = resumen['duracion_sesion'].round(2)
    resumen['porcentaje_user'] = resumen['porcentaje_user'].round(2)

    return pn.widgets.Tabulator(resumen.reset_index(), height=300)

# Visualización de tabla original
tabla = pn.widgets.Tabulator(df, pagination='remote', page_size=10, height=300)

# Dashboard completo
dashboard = pn.Column(
    "# 📊 Dashboard de sesiones Chatbot",
    pn.pane.Markdown("**Agrupar sesiones por:**"),
    agrupamiento,
    tabla_agrupada,
    pn.pane.Markdown("**Tabla completa de sesiones**"),
    tabla
)

dashboard.servable()
