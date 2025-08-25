import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from supabase import create_client, Client
from modelos import rfm, churn, sentimiento, recompra

# --- Cargar .env ---
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ No se encontraron SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el .env")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Configuración de la página ---
st.set_page_config(
    page_title="📊 Dashboard de Clientes Ecommerce",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilos CSS personalizados ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #1e88e5;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 16px;
        color: #6c757d;
        font-weight: 500;
    }
    .section-title {
        border-bottom: 3px solid #1e88e5;
        padding-bottom: 12px;
        margin-top: 25px;
        margin-bottom: 25px;
        color: #1e88e5;
        font-size: 24px;
    }
    .stRadio > div {
        flex-direction: row !important;
        gap: 15px;
    }
    .stRadio label {
        padding: 12px 24px;
        border-radius: 30px;
        background: #f0f2f6;
        margin-right: 15px !important;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    .stRadio label:hover {
        background: #e0e5ec;
    }
    .stRadio [data-baseweb="radio"]:checked + div {
        background-color: #1e88e5 !important;
        color: white !important;
    }
    .stPlotlyChart {
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        padding: 15px;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# --- Función para mostrar métricas ---
def display_metrics(metrics):
    cols = st.columns(len(metrics))
    for i, (label, value, color) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color: {color};">{value}</div>
            </div>
            """, unsafe_allow_html=True)

# --- Página RFM ---
def rfm_page():
    st.title("📊 Análisis RFM")
    try:
        df_rfm, rfm_summary = rfm.run(supabase)
        
        if df_rfm.empty or rfm_summary.empty:
            st.warning("No hay datos disponibles para el análisis RFM")
            return
        
        # Métricas RFM
        campeones = df_rfm[df_rfm['RFM_segment'].str.contains('Campeones', case=False)].shape[0]
        monetario_total = df_rfm['monetario'].sum()
        clientes_activos = df_rfm[df_rfm['recencia'] <= 30].shape[0]
        
        metrics = [
            ("Clientes Campeones", f"{campeones}", "#4CAF50"),
            ("Valor Monetario Total", f"${monetario_total:,.0f}", "#1e88e5"),
            ("Clientes Activos", f"{clientes_activos}", "#FF9800")
        ]
        display_metrics(metrics)
        
        # Gráficos RFM
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribución de Segmentos RFM")
            # Mejorar los nombres de segmentos
            segment_map = {
                'Reciente-Frecuente-Alto': 'Campeones',
                'Reciente-Frecuente-Bajo': 'Leales',
                'Reciente-No frecuente-Alto': 'Prometedores',
                'Reciente-No frecuente-Bajo': 'Nuevos',
                'No reciente-Frecuente-Alto': 'En riesgo',
                'No reciente-Frecuente-Bajo': 'Necesitan atención',
                'No reciente-No frecuente-Alto': 'Dormidos',
                'No reciente-No frecuente-Bajo': 'Perdidos'
            }
            
            rfm_summary['Segmento'] = rfm_summary['RFM_segment'].map(segment_map)
            segment_counts = rfm_summary.groupby('Segmento')['cantidad_clientes'].sum().reset_index()
            
            fig = px.bar(
                segment_counts, 
                x='Segmento',
                y='cantidad_clientes',
                color='Segmento',
                text='cantidad_clientes',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(
                xaxis_title="Segmento RFM",
                yaxis_title="Número de Clientes",
                showlegend=False,
                height=500
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Valor por Segmento")
            fig = px.treemap(
                rfm_summary,
                path=['RFM_segment'],
                values='monetario',
                color='monetario',
                color_continuous_scale='Blues',
                height=500
            )
            fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
        # Mapa de calor RFM
        st.subheader("Mapa de Calor RFM")
        rfm_heatmap = df_rfm.pivot_table(
            index='R_segment',
            columns='F_segment',
            values='monetario',
            aggfunc='mean'
        ).fillna(0)
        
        fig = px.imshow(
            rfm_heatmap,
            labels=dict(x="Frecuencia", y="Recencia", color="Valor Monetario"),
            aspect="auto",
            color_continuous_scale='Viridis',
            text_auto=".0f"
        )
        fig.update_xaxes(side="top")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error en análisis RFM: {str(e)}")

# --- Página Churn ---
def churn_page():
    st.title("📊 Análisis de Churn")
    try:
        df_churn = churn.run(supabase)
        
        if df_churn.empty:
            st.warning("No hay datos disponibles para el análisis de Churn")
            return
        
        # Métricas Churn
        alto_churn = df_churn[df_churn['churn_risk'] == 'alto']['conteo'].sum()
        total_clientes = df_churn['conteo'].sum()
        churn_rate = alto_churn / total_clientes * 100
        
        metrics = [
            ("Total Clientes", f"{total_clientes}", "#1e88e5"),
            ("Clientes Alto Riesgo", f"{alto_churn}", "#F44336"),
            ("Tasa de Churn", f"{churn_rate:.1f}%", "#FF9800")
        ]
        display_metrics(metrics)
        
        # Gráficos Churn
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribución de Riesgo de Churn")
            fig = px.pie(
                df_churn, 
                names='churn_risk', 
                values='conteo',
                color='churn_risk',
                color_discrete_map={
                    'alto': '#F44336',
                    'bajo': '#4CAF50'
                }
            )
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                pull=[0.1 if risk == 'alto' else 0 for risk in df_churn['churn_risk']]
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Clientes por Nivel de Riesgo")
            # Mejorar nombres para visualización
            df_churn['churn_risk'] = df_churn['churn_risk'].str.capitalize()
            
            fig = px.bar(
                df_churn, 
                x='churn_risk', 
                y='conteo',
                color='churn_risk',
                color_discrete_map={
                    'Alto': '#F44336',
                    'Bajo': '#4CAF50'
                },
                text='conteo'
            )
            fig.update_layout(
                xaxis_title="Nivel de Riesgo",
                yaxis_title="Número de Clientes",
                showlegend=False,
                height=400
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
            # Indicador de tasa de churn
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=churn_rate,
                number={'suffix': "%"},
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Tasa de Churn"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#F44336"},
                    'steps': [
                        {'range': [0, 20], 'color': "#4CAF50"},
                        {'range': [20, 50], 'color': "#FFC107"},
                        {'range': [50, 100], 'color': "#F44336"}
                    ]
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error en análisis de Churn: {str(e)}")

# --- Página Sentimiento ---
def sentiment_page():
    st.title("📊 Análisis de Sentimiento")
    try:
        df_sent = sentimiento.run(supabase)
        
        if df_sent.empty:
            st.warning("No hay datos disponibles para el análisis de Sentimiento")
            return
        
        # Métricas Sentimiento
        total_mensajes = df_sent['conteo'].sum()
        positivos = df_sent[df_sent['sentimiento'] == 'positivo']['conteo'].sum()
        positivos_pct = positivos / total_mensajes * 100
        
        metrics = [
            ("Total Mensajes", f"{total_mensajes}", "#1e88e5"),
            ("Mensajes Positivos", f"{positivos}", "#4CAF50"),
            ("% Positivos", f"{positivos_pct:.1f}%", "#FF9800")
        ]
        display_metrics(metrics)
        
        # Gráficos Sentimiento
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribución de Sentimientos")
            fig = px.pie(
                df_sent, 
                names='sentimiento', 
                values='conteo',
                color='sentimiento',
                color_discrete_map={
                    'positivo': '#4CAF50',
                    'neutral': '#FFC107',
                    'negativo': '#F44336'
                },
                hole=0.4
            )
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                pull=[0.1 if sent == 'positivo' else 0 for sent in df_sent['sentimiento']]
            )
            fig.update_layout(
                showlegend=False,
                height=500,
                annotations=[dict(text='Sentimiento', x=0.5, y=0.5, font_size=16, showarrow=False)]
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Comparación de Sentimientos")
            fig = px.bar(
                df_sent, 
                x='sentimiento', 
                y='conteo',
                color='sentimiento',
                color_discrete_map={
                    'positivo': '#4CAF50',
                    'neutral': '#FFC107',
                    'negativo': '#F44336'
                },
                text='conteo'
            )
            fig.update_layout(
                xaxis_title="Sentimiento",
                yaxis_title="Número de Mensajes",
                showlegend=False,
                height=400
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
            # Evolución temporal (simulada)
            st.subheader("Evolución del Sentimiento (simulada)")
            time_data = pd.DataFrame({
                'Fecha': pd.date_range(start='2023-01-01', periods=12, freq='M'),
                'Positivo': [60, 65, 70, 68, 72, 75, 78, 76, 80, 82, 85, 83],
                'Negativo': [15, 14, 12, 10, 9, 8, 7, 6, 5, 6, 5, 4]
            })
            
            fig = px.line(
                time_data, 
                x='Fecha', 
                y=['Positivo', 'Negativo'],
                markers=True,
                color_discrete_map={
                    'Positivo': '#4CAF50',
                    'Negativo': '#F44336'
                }
            )
            fig.update_layout(
                yaxis_title="Porcentaje",
                legend_title="Sentimiento",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error en análisis de Sentimiento: {str(e)}")

# --- Página Recompra ---
def recompra_page():
    st.title("📊 Propensión de Recompra")
    try:
        result, compras_count, recompra_count = recompra.run(supabase)
        
        if result.empty or compras_count.empty or recompra_count.empty:
            st.warning("No hay datos suficientes para el análisis de recompra")
            return
        
        # Métricas Recompra
        prob_recompra = result.iloc[0]['probabilidad_recompra'] * 100
        clientes_recompra = recompra_count[recompra_count['recompra'] == 1]['clientes'].sum()
        total_clientes = recompra_count['clientes'].sum()
        
        metrics = [
            ("Prob. Recompra", f"{prob_recompra:.1f}%", "#1e88e5"),
            ("Clientes que Recompran", f"{clientes_recompra}", "#4CAF50"),
            ("% Recompran", f"{(clientes_recompra/total_clientes)*100:.1f}%", "#FF9800")
        ]
        display_metrics(metrics)
        
        # Gráficos Recompra
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Historial de Compras")
            # Mejorar nombres para visualización
            compras_count['hizo_compra'] = compras_count['hizo_compra'].apply(
                lambda x: f"{x} compras" if x > 0 else "Sin compras"
            )
            
            fig = px.bar(
                compras_count, 
                x='hizo_compra', 
                y='cantidad_clientes',
                color='hizo_compra',
                color_discrete_sequence=['#1e88e5', '#42a5f5', '#90caf9', '#bbdefb'],
                text='cantidad_clientes'
            )
            fig.update_layout(
                xaxis_title="Número de Compras",
                yaxis_title="Número de Clientes",
                showlegend=False,
                height=400
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Tendencia de Recompra")
            # Mejorar nombres para visualización
            recompra_count['recompra'] = recompra_count['recompra'].map({
                0: "No recompró",
                1: "Recompró"
            })
            
            fig = px.bar(
                recompra_count, 
                x='recompra', 
                y='clientes',
                color='recompra',
                color_discrete_map={
                    "Recompró": "#4CAF50",
                    "No recompró": "#F44336"
                },
                text='clientes'
            )
            fig.update_layout(
                xaxis_title="Recompra",
                yaxis_title="Número de Clientes",
                showlegend=False,
                height=400
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
            # Indicador de probabilidad
            st.subheader("Probabilidad de Recompra")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob_recompra,
                number={'suffix': "%"},
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Probabilidad Media de Recompra"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#1e88e5"},
                    'steps': [
                        {'range': [0, 30], 'color': "#F44336"},
                        {'range': [30, 70], 'color': "#FFC107"},
                        {'range': [70, 100], 'color': "#4CAF50"}
                    ]
                }
            ))
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error en análisis de Recompra: {str(e)}")

# --- Dashboard Global ---
def global_dashboard():
    st.title("🌐 Dashboard Global de Clientes")
    
    # Obtener datos de todos los modelos
    try:
        # RFM
        df_rfm, rfm_summary = rfm.run(supabase)
        rfm_clientes = df_rfm['cliente_id'].nunique() if not df_rfm.empty else 0
        rfm_campeones = df_rfm[df_rfm['RFM_segment'].str.contains('Campeones', case=False)].shape[0] if not df_rfm.empty else 0
        
        # Churn
        df_churn = churn.run(supabase)
        churn_total = df_churn['conteo'].sum() if not df_churn.empty else 0
        churn_alto = df_churn[df_churn['churn_risk'] == 'alto']['conteo'].sum() if not df_churn.empty else 0
        churn_rate = (churn_alto / churn_total * 100) if churn_total > 0 else 0
        
        # Sentimiento
        df_sent = sentimiento.run(supabase)
        sent_total = df_sent['conteo'].sum() if not df_sent.empty else 0
        sent_positivo = df_sent[df_sent['sentimiento'] == 'positivo']['conteo'].sum() if not df_sent.empty else 0
        sent_positivo_pct = (sent_positivo / sent_total * 100) if sent_total > 0 else 0
        
        # Recompra
        result, compras_count, recompra_count = recompra.run(supabase)
        prob_recompra = result.iloc[0]['probabilidad_recompra'] * 100 if not result.empty else 0
        recompra_clientes = recompra_count[recompra_count['recompra'] == 1]['clientes'].sum() if not recompra_count.empty else 0
        
        # Métricas clave
        metrics = [
            ("Clientes Activos (RFM)", f"{rfm_clientes}", "#1e88e5"),
            ("Clientes Campeones", f"{rfm_campeones}", "#4CAF50"),
            ("Tasa de Churn", f"{churn_rate:.1f}%", "#F44336"),
            ("Sentimiento Positivo", f"{sent_positivo_pct:.1f}%", "#FF9800"),
            ("Prob. Recompra", f"{prob_recompra:.1f}%", "#9C27B0")
        ]
        display_metrics(metrics)
        
        # Gráficos principales
        st.subheader("Resumen de Modelos")
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico RFM
            if not rfm_summary.empty:
                fig = px.scatter(
                    rfm_summary, 
                    x='recencia', 
                    y='monetario',
                    size='frecuencia',
                    color='RFM_segment',
                    hover_name='RFM_segment',
                    hover_data=['recencia', 'frecuencia', 'monetario'],
                    title="Segmentos RFM"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Gráfico Sentimiento
            if not df_sent.empty:
                fig = px.bar(
                    df_sent, 
                    x='sentimiento', 
                    y='conteo',
                    color='sentimiento',
                    color_discrete_map={
                        'positivo': '#4CAF50',
                        'neutral': '#FFC107',
                        'negativo': '#F44336'
                    },
                    title="Distribución de Sentimientos"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gráfico Churn
            if not df_churn.empty:
                fig = px.pie(
                    df_churn, 
                    names='churn_risk', 
                    values='conteo',
                    color='churn_risk',
                    color_discrete_map={
                        'alto': '#F44336',
                        'bajo': '#4CAF50'
                    },
                    title="Distribución de Riesgo de Churn",
                    hole=0.4
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Gráfico Recompra
            if not result.empty:
                fig = go.Figure(go.Indicator(
                    mode="number",
                    value=prob_recompra,
                    number={'suffix': "%"},
                    title={'text': "Probabilidad Media de Recompra"},
                    domain={'x': [0, 1], 'y': [0, 1]}
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error al cargar datos globales: {str(e)}")

# --- Navegación principal ---
st.sidebar.title("Navegación")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2554/2554897.png", width=80)
page = st.sidebar.radio(
    "Seleccionar vista:",
    ("Dashboard Global", "RFM", "Churn", "Sentimiento", "Recompra")
)

# --- Mostrar página seleccionada ---
if page == "Dashboard Global":
    global_dashboard()
elif page == "RFM":
    rfm_page()
elif page == "Churn":
    churn_page()
elif page == "Sentimiento":
    sentiment_page()
elif page == "Recompra":
    recompra_page()

# --- Pie de página ---
st.sidebar.markdown("---")
st.sidebar.info("""
**Customer Intelligence Dashboard**  
v1.0 · Actualizado: {date}  
Datos: Supabase  
""".format(date=pd.Timestamp.now().strftime("%Y-%m-%d")))