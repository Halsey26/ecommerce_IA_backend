import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from supabase import create_client, Client
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../chatbot_produccion")))

from modelos import rfm, churn, sentimiento, recompra
import numpy as np
from datetime import datetime, timedelta

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
    page_title="📊 Kreadores Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📷"
)

# --- Estilos CSS personalizados para Kreadores ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .kreadores-logo {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(45deg, #FFD700, #FFA500);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .tagline {
        font-size: 1.5rem;
        opacity: 0.9;
        font-weight: 350;
        display: block;
        margin-top: 0; 
    }
   .subtagline {
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 250;
        display: block;
        margin-top: 0; 
    }
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        border-left: 5px solid #667eea;
    }
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #667eea;
        margin: 15px 0;
        font-family: 'Inter', sans-serif;
    }
    .metric-label {
        font-size: 16px;
        color: #495057;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
    }
    .section-title {
        border-bottom: 3px solid #667eea;
        padding-bottom: 15px;
        margin-top: 30px;
        margin-bottom: 30px;
        color: #667eea;
        font-size: 28px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    .stRadio > div {
        flex-direction: row !important;
        gap: 20px;
    }
    .stRadio label {
        padding: 15px 30px;
        border-radius: 25px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        margin-right: 20px !important;
        transition: all 0.3s ease;
        font-weight: 500;
        border: 2px solid transparent;
        font-family: 'Inter', sans-serif;
    }
    .stRadio label:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
        border-color: #667eea;
    }
    .stRadio [data-baseweb="radio"]:checked + div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: #667eea !important;
    }
    .stPlotlyChart {
        border-radius: 15px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        padding: 20px;
        background: white;
        border: 1px solid #e9ecef;
    }
    .recommendation-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        margin: 20px 0;
        box-shadow: 0 8px 30px rgba(0,0,0,0.2);
    }
    .priority-high {
        border-left: 6px solid #dc3545;
        background: linear-gradient(135deg, #fff5f5 0%, #ffe6e6 100%);
        padding: 20px;
        margin: 15px 0;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(220,53,69,0.1);
    }
    .priority-medium {
        border-left: 6px solid #ffc107;
        background: linear-gradient(135deg, #fffbf0 0%, #fff3cd 100%);
        padding: 20px;
        margin: 15px 0;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(255,193,7,0.1);
    }
    .priority-low {
        border-left: 6px solid #28a745;
        background: linear-gradient(135deg, #f0fff4 0%, #d4edda 100%);
        padding: 20px;
        margin: 15px 0;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(40,167,69,0.1);
    }
    .insight-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border: 2px solid #dee2e6;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.05);
    }
    .action-item {
        background: white;
        border: 2px solid #dee2e6;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .action-item:hover {
        border-color: #667eea;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    }
    .camera-icon {
        font-size: 3rem;
        color: #667eea;
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# --- Header de Kreadores ---
# def kreadores_header():
#     st.markdown("""
#     <div class="main-header">
#         <div class="camera-icon">📷</div>
#         <div class="kreadores-logo">KREADORES PRO</div>
#         <div class="tagline">Analytics Dashboard - La Tienda #1 para Crear Contenido Creativo y Profesional</div>
#     </div>
#     """, unsafe_allow_html=True)
def kreadores_header():
    st.markdown("""
    <div class="main-header">
        <div class="camera-icon">📷</div>
        <div class="kreadores-logo">KREADORES PRO</div>
        <div class="tagline"> Analytics Dashboard – Análisis de Conversaciones y Experiencia del Cliente</div>
        <div class="subtagline">Insights de RFM, churn, sentimiento y recompra basados en interacciones con el cliente</div>
    </div>
    """, unsafe_allow_html=True)

# --- Clase para Análisis de Marketing específico para Kreadores ---
class KreadoresMarketingAnalyzer:
    def __init__(self, df_rfm=None, df_churn=None, df_sentiment=None, df_recompra=None):
        self.df_rfm = df_rfm
        self.df_churn = df_churn
        self.df_sentiment = df_sentiment
        self.df_recompra = df_recompra
        self.insights = []
        self.recommendations = []
        
    def analyze_customer_health(self):
        """Analiza la salud de clientes específicamente para equipo fotográfico/video"""
        insights = {
            'customer_distribution': {},
            'retention_risk': {},
            'satisfaction_level': {},
            'revenue_potential': {}
        }
        
        # Análisis RFM
        if self.df_rfm is not None and not self.df_rfm.empty:
            total_customers = len(self.df_rfm)
            champions = len(self.df_rfm[self.df_rfm['RFM_segment'].str.contains('Campeones', case=False)])
            at_risk = len(self.df_rfm[self.df_rfm['RFM_segment'].str.contains('riesgo|perdidos', case=False)])
            
            insights['customer_distribution'] = {
                'total': total_customers,
                'champions': champions,
                'champions_pct': (champions / total_customers) * 100 if total_customers > 0 else 0,
                'at_risk': at_risk,
                'at_risk_pct': (at_risk / total_customers) * 100 if total_customers > 0 else 0
            }
            
        # Análisis Churn
        if self.df_churn is not None and not self.df_churn.empty:
            total_churn = self.df_churn['conteo'].sum()
            high_risk = self.df_churn[self.df_churn['churn_risk'] == 'alto']['conteo'].sum()
            churn_rate = (high_risk / total_churn) * 100 if total_churn > 0 else 0
            
            insights['retention_risk'] = {
                'churn_rate': churn_rate,
                'high_risk_customers': high_risk,
                'status': 'critical' if churn_rate > 25 else 'warning' if churn_rate > 15 else 'good'
            }
            
        # Análisis Sentimiento
        if self.df_sentiment is not None and not self.df_sentiment.empty:
            total_messages = self.df_sentiment['conteo'].sum()
            positive = self.df_sentiment[self.df_sentiment['sentimiento'] == 'positivo']['conteo'].sum()
            negative = self.df_sentiment[self.df_sentiment['sentimiento'] == 'negativo']['conteo'].sum()
            
            satisfaction_score = (positive / total_messages) * 100 if total_messages > 0 else 0
            
            insights['satisfaction_level'] = {
                'satisfaction_score': satisfaction_score,
                'positive_messages': positive,
                'negative_messages': negative,
                'status': 'excellent' if satisfaction_score > 70 else 'good' if satisfaction_score > 50 else 'needs_improvement'
            }
            
        return insights
    
    def generate_kreadores_recommendations(self, insights):
        """Genera recomendaciones específicas para Kreadores"""
        recommendations = []
        
        # Recomendaciones basadas en RFM
        if 'customer_distribution' in insights:
            champions_pct = insights['customer_distribution'].get('champions_pct', 0)
            at_risk_pct = insights['customer_distribution'].get('at_risk_pct', 0)
            
            if champions_pct < 15:
                recommendations.append({
                    'category': 'Programa VIP para Creadores Profesionales',
                    'priority': 'crítica',
                    'issue': f'Solo {champions_pct:.1f}% de tus clientes son campeones en equipo fotográfico',
                    'impact': 'Los fotógrafos profesionales invierten $5,000+ anualmente en equipo',
                    'action': 'Crear programa "Kreadores Pro" con beneficios exclusivos',
                    'tactics': [
                        'Descuentos escalonados: 5% primera compra, 10% segunda, 15% tercera+',
                        'Acceso anticipado a cámaras Canon EOS R y Sony α7 nuevas',
                        'Soporte técnico especializado para configuración de equipos',
                        'Eventos exclusivos con fotógrafos profesionales reconocidos',
                        'Financiamiento preferencial para equipos premium (+$1M CLP)'
                    ],
                    'expected_outcome': 'Aumentar clientes VIP a 20% en 8 meses'
                })
                
            if at_risk_pct > 25:
                recommendations.append({
                    'category': 'Retención de Clientes con Equipos Costosos',
                    'priority': 'alta',
                    'issue': f'{at_risk_pct:.1f}% de clientes están en riesgo (equipos de $500K+ CLP)',
                    'impact': 'Pérdida de clientes que ya invirtieron en ecosistema Canon/Sony',
                    'action': 'Campaña "Actualiza tu Setup" personalizada',
                    'tactics': [
                        'Email serie con nuevos lentes compatibles con sus cámaras',
                        'Descuento 20% en accesorios (trípodes, filtros, baterías)',
                        'Llamada personal para entender necesidades de upgrade',
                        'Workshop gratuito "Maximiza tu equipo actual"',
                        'Trade-in program para cámaras antiguas'
                    ],
                    'expected_outcome': 'Recuperar 40% de clientes en riesgo'
                })
        
        # Recomendaciones basadas en Churn para equipo fotográfico
        if 'retention_risk' in insights:
            churn_rate = insights['retention_risk'].get('churn_rate', 0)
            status = insights['retention_risk'].get('status', 'good')
            
            if status in ['critical', 'warning']:
                recommendations.append({
                    'category': 'Experiencia Post-Venta para Equipos Técnicos',
                    'priority': 'alta',
                    'issue': f'Churn del {churn_rate:.1f}% indica problemas con soporte técnico',
                    'impact': 'Los clientes no vuelven porque no saben usar correctamente los equipos',
                    'action': 'Implementar onboarding técnico especializado',
                    'tactics': [
                        'Video tutorial personalizado según cámara comprada',
                        'Checklist de configuración inicial (ISO, apertura, enfoque)',
                        'WhatsApp de soporte técnico 24/7 para emergencias',
                        'Seguimiento a los 7, 30 y 90 días post-compra',
                        'Garantía extendida gratuita por buen uso'
                    ],
                    'expected_outcome': f'Reducir churn a 12% (benchmark para retailers técnicos)'
                })
        
        # Recomendaciones basadas en productos de Kreadores
        recommendations.append({
            'category': 'Estrategia de Bundling Premium',
            'priority': 'media',
            'issue': 'Oportunidad de aumentar ticket promedio con kits completos',
            'impact': 'Clientes compran por separado: cámara ($1.5M) + lente ($800K) + accesorios ($300K)',
            'action': 'Crear "Kits de Creador" por nicho',
            'tactics': [
                'Kit Fotógrafo: Cámara Sony α7 + lente 24-70 + trípode + filtros ND',
                'Kit YouTuber: Cámara Canon EOS R + micrófono Maono + iluminación LED',
                'Kit Podcaster: Micrófono dinámico Maono PD400X + brazo + interfaz',
                'Kit Viajero: Cámara compacta + lentes versátiles + estabilizador',
                'Descuento 15% vs compra individual + envío gratis'
            ],
            'expected_outcome': 'Aumentar AOV de $800K a $1.2M CLP'
        })
        
        # Recomendación específica de contenido
        recommendations.append({
            'category': 'Marketing de Contenido Técnico',
            'priority': 'media',
            'issue': 'Los clientes necesitan educación antes de comprar equipos costosos',
            'impact': 'Decisiones de compra más informadas = menos devoluciones',
            'action': 'Canal de YouTube "Kreadores Academy"',
            'tactics': [
                'Reviews técnicos de cada cámara en catálogo',
                'Comparativas: "Canon vs Sony para principiantes"',
                'Tutoriales: "Cómo elegir tu primer lente"',
                'Casos de uso: "Setup completo para wedding photography"',
                'Colaboraciones con fotógrafos chilenos reconocidos'
            ],
            'expected_outcome': 'Mejorar conversión de visita a compra en 25%'
        })
        
        return sorted(recommendations, key=lambda x: {'crítica': 4, 'alta': 3, 'media': 2, 'baja': 1}[x['priority']], reverse=True)

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

# --- Explicación del gráfico RFM Valor por Segmento ---
def explain_rfm_value_chart():
    st.markdown("""
    ### 📊 **¿Qué significa el gráfico "Valor por Segmento"?**
    
    Este gráfico tipo **TreeMap** muestra cuánto dinero genera cada tipo de cliente:
    
    **🟦 Reciente-Frecuente-Alto** = **Clientes VIP**
    - Compraron recientemente
    - Compran seguido  
    - Gastan mucho dinero
    - *Son tus mejores clientes que compran cámaras premium*
    
    **🟦 Reciente-Frecuente-Bajo** = **Clientes Leales**
    - Compran regularmente pero productos más económicos
    - *Compran accesorios, filtros, baterías constantemente*
    
    **🟦 Reciente-No frecuente-Bajo** = **Clientes Nuevos**
    - Primera compra reciente
    - *Probablemente compraron una cámara de entrada*
    
    **Mientras más grande el cuadro = más dinero genera ese segmento**
    
    📈 **Insight clave**: Si el cuadro azul oscuro (VIP) es pequeño, significa que no tienes suficientes clientes que compran equipos caros regularmente.
    """)

# --- Nueva página de Marketing Intelligence para Kreadores ---
def kreadores_marketing_intelligence():
    kreadores_header()
    
    st.markdown("### 🎯 Marketing Intelligence - Análisis Automatizado")
    st.markdown("*Insights accionables específicos para tu tienda de equipos fotográficos y de video*")
    
    try:
        # Cargar datos de todos los modelos
        df_rfm, rfm_summary = rfm.run(supabase)
        df_churn = churn.run(supabase)
        df_sentiment = sentimiento.run(supabase)
        result_recompra, compras_count, recompra_count = recompra.run(supabase)
        
        # Inicializar analizador específico para Kreadores
        analyzer = KreadoresMarketingAnalyzer(df_rfm, df_churn, df_sentiment, result_recompra)
        
        # Generar insights
        insights = analyzer.analyze_customer_health()
        
        # Métricas clave de marketing para Kreadores
        champions_pct = insights.get('customer_distribution', {}).get('champions_pct', 0)
        churn_rate = insights.get('retention_risk', {}).get('churn_rate', 0)
        satisfaction_score = insights.get('satisfaction_level', {}).get('satisfaction_score', 0)
        
        # Calcular AOV estimado basado en precios reales de Kreadores
        total_customers = insights.get('customer_distribution', {}).get('total', 1)
        estimated_aov = 850000  # Promedio basado en precios vistos en la web (850K CLP)
        
        metrics = [
            ("Salud del Negocio", f"{100-churn_rate:.0f}/100", "#28a745" if churn_rate < 15 else "#ffc107" if churn_rate < 25 else "#dc3545"),
            ("Clientes VIP Fotógrafos", f"{champions_pct:.1f}%", "#28a745" if champions_pct > 15 else "#ffc107" if champions_pct > 8 else "#dc3545"),
            ("Satisfacción Equipos", f"{satisfaction_score:.0f}%", "#28a745" if satisfaction_score > 70 else "#ffc107" if satisfaction_score > 50 else "#dc3545"),
            ("AOV Estimado", f"${estimated_aov:,.0f} CLP", "#667eea"),
        ]
        display_metrics(metrics)
        
        # Sección de diagnóstico específico para Kreadores
        st.markdown('<h2 class="section-title">📊 Diagnóstico Kreadores</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔍 Estado de tu Tienda de Equipos")
            
            # Diagnóstico RFM
            if champions_pct < 15:
                st.markdown(f"""
                <div class="priority-high">
                    <strong>📷 ALERTA CRÍTICA: Pocos Clientes Pro</strong><br>
                    Solo tienes {champions_pct:.1f}% de clientes que compran equipos caros regularmente. 
                    Para una tienda de cámaras profesionales, necesitas 15-20% de clientes VIP que actualicen 
                    sus equipos constantemente (nuevas cámaras, lentes, accesorios).
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="priority-low">
                    <strong>✅ BIEN: Base de Fotógrafos Profesionales</strong><br>
                    Tienes {champions_pct:.1f}% de clientes VIP, lo cual está bien para equipos especializados.
                </div>
                """, unsafe_allow_html=True)
            
            # Diagnóstico Churn específico para equipos técnicos
            if churn_rate > 25:
                st.markdown(f"""
                <div class="priority-high">
                    <strong>🚨 CRÍTICO: Los clientes no vuelven</strong><br>
                    {churn_rate:.1f}% de churn es muy alto para equipos fotográficos. Esto indica que los clientes 
                    no están satisfechos con el soporte técnico o no entienden cómo usar correctamente sus equipos.
                </div>
                """, unsafe_allow_html=True)
            elif churn_rate > 15:
                st.markdown(f"""
                <div class="priority-medium">
                    <strong>⚡ ATENCIÓN: Retención Mejorable</strong><br>
                    {churn_rate:.1f}% de churn está arriba del ideal para equipos especializados (12-15%).
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="priority-low">
                    <strong>✅ EXCELENTE: Buena Retención</strong><br>
                    {churn_rate:.1f}% de churn está en niveles óptimos para equipos técnicos.
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 💰 Oportunidades en Equipos Premium")
            
            # Análisis específico para Kreadores basado en sus precios reales
            total_customers = insights.get('customer_distribution', {}).get('total', 0)
            if total_customers > 0:
                # Basado en precios reales de Kreadores.pro
                potential_premium_sales = total_customers * 0.3 * 1500000  # 30% podrían comprar equipos de $1.5M+
                current_sales_estimate = total_customers * estimated_aov
                
                st.markdown(f"""
                <div class="insight-box">
                    <strong>📸 Potencial en Cámaras Premium</strong><br>
                    Tienes {total_customers} clientes. Si 30% compraran equipos premium 
                    (Canon EOS R8, Sony α7 III), generarías ${potential_premium_sales:,.0f} CLP adicionales.
                    <br><br>
                    <strong>🎥 Oportunidad en Kits Completos</strong><br>
                    Vendiendo kits (cámara + lente + accesorios) en vez de productos individuales 
                    podrías aumentar tu AOV de ${estimated_aov:,.0f} a ${int(estimated_aov * 1.5):,.0f} CLP.
                </div>
                """, unsafe_allow_html=True)
                
                # Cálculo de ingresos perdidos por falta de clientes VIP
                lost_revenue = total_customers * 0.15 * 2000000  # 15% deberían ser VIP gastando $2M+ anual
                st.markdown(f"""
                <div class="insight-box">
                    <strong>💸 Ingresos Perdidos Anuales</strong><br>
                    Al no tener suficientes clientes VIP (fotógrafos profesionales que actualizan equipos), 
                    estás perdiendo aproximadamente ${lost_revenue:,.0f} CLP anuales.
                    <br><br>
                    <strong>🎯 Meta Realista</strong><br>
                    Convirtiendo 20% de tus clientes nuevos en clientes VIP, podrías recuperar 
                    ${int(lost_revenue * 0.4):,.0f} CLP en 12 meses.
                </div>
                """, unsafe_allow_html=True)
        
        # Recomendaciones estratégicas específicas para Kreadores
        st.markdown('<h2 class="section-title">💡 Recomendaciones para Kreadores</h2>', unsafe_allow_html=True)
        
        recommendations = analyzer.generate_kreadores_recommendations(insights)
        
        for i, rec in enumerate(recommendations):
            priority_class = f"priority-{rec['priority'].replace('crítica', 'high').replace('alta', 'high').replace('media', 'medium').replace('baja', 'low')}"
            priority_emoji = "🚨" if rec['priority'] in ['crítica', 'alta'] else "⚡" if rec['priority'] == 'media' else "💡"
            
            st.markdown(f"""
            <div class="{priority_class}">
                <h4>{priority_emoji} {rec['category']} - Prioridad {rec['priority'].upper()}</h4>
                <p><strong>Situación:</strong> {rec['issue']}</p>
                <p><strong>Impacto en Kreadores:</strong> {rec['impact']}</p>
                <p><strong>Acción Principal:</strong> {rec['action']}</p>
                <p><strong>Resultado Esperado:</strong> {rec['expected_outcome']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mostrar tácticas específicas para Kreadores
            with st.expander(f"📋 Ver plan de acción: {rec['category']}"):
                st.markdown("**Acciones específicas para implementar:**")
                for j, tactic in enumerate(rec['tactics'], 1):
                    st.markdown(f"**{j}.** {tactic}")
        
        # Plan específico por tipo de cliente en Kreadores
        st.markdown('<h2 class="section-title">🎯 Estrategia por Tipo de Cliente</h2>', unsafe_allow_html=True)
        
        tabs = st.tabs(["📷 Fotógrafos Nuevos", "🎥 Creadores Leales", "⚠️ Clientes en Riesgo", "😴 Clientes Perdidos"])
        
        kreadores_strategies = [
            ("Fotógrafos Nuevos", [
                "Tutorial personalizado: 'Primeros pasos con tu nueva cámara Canon/Sony'",
                "Descuento 15% en primer lente dentro de 30 días",
                "Kit de bienvenida: correa, tarjeta SD, paño de limpieza",
                "Invitación a workshop gratuito 'Fotografía básica'"
            ]),
            ("Creadores Leales", [
                "Acceso VIP a pre-órdenes de nuevas cámaras",
                "Descuentos escalonados: 5%, 10%, 15% en compras sucesivas",
                "Financiamiento preferencial para equipos >$1M CLP",
                "Invitación exclusiva a evento con fotógrafos profesionales"
            ]),
            ("Clientes en Riesgo", [
                "Llamada personal: '¿Cómo va tu experiencia con tu equipo?'",
                "Oferta upgrade: Trade-in de cámara antigua con descuento",
                "Servicio técnico gratuito: limpieza y calibración",
                "Workshop exclusivo: 'Maximiza el potencial de tu equipo actual'"
            ]),
            ("Clientes Perdidos", [
                "Email: 'Nuevas cámaras que debes conocer' con comparativas",
                "Descuento comeback: 25% en cualquier compra",
                "Encuesta: '¿Qué te haría volver a Kreadores?'",
                "Demostración gratuita en tienda de últimos modelos"
            ])
        ]
        
        for i, (segment_title, strategies) in enumerate(kreadores_strategies):
            with tabs[i]:
                st.markdown(f"### {segment_title}")
                for j, strategy in enumerate(strategies, 1):
                    st.markdown(f"""
                    <div class="action-item">
                        <strong>Acción {j}:</strong> {strategy}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Cronograma de implementación específico para Kreadores
        st.markdown('<h2 class="section-title">📅 Plan de Implementación Kreadores (90 días)</h2>', unsafe_allow_html=True)
        
        timeline_data = [
            ("Mes 1 - Base", "🚀 Fundación", [
                "Configurar programa VIP 'Kreadores Pro'",
                "Crear tutoriales para cámaras más vendidas",
                "Implementar sistema de seguimiento post-venta",
                "Diseñar kits por especialidad (retrato, paisaje, video)"
            ]),
            ("Mes 2 - Activación", "📈 Campañas", [
                "Lanzar campaña 'Actualiza tu Setup' para clientes antiguos",
                "Implementar WhatsApp de soporte técnico 24/7",
                "Crear contenido educativo en redes sociales",
                "Establecer alianzas con fotógrafos influencers chilenos"
            ]),
            ("Mes 3 - Optimización", "🎯 Refinamiento", [
                "Analizar resultados y ajustar estrategias",
                "Expandir programa de trade-in",
                "Optimizar bundling basado en datos de ventas",
                "Planificar eventos exclusivos para clientes VIP"
            ])
        ]
        
        for period, phase, tasks in timeline_data:
            st.markdown(f"**{period} - {phase}**")
            for task in tasks:
                st.markdown(f"  📋 {task}")
            st.markdown("")
        
        # KPIs específicos para Kreadores
        st.markdown('<h2 class="section-title">📊 KPIs Clave para Kreadores</h2>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📷 Métricas de Producto**
            - AOV por categoría (Cámaras vs Accesorios)
            - Tasa de conversión Cámara → Lente
            - % de ventas en equipos premium (+$1M CLP)
            - Rotación de inventory por marca
            """)
        
        with col2:
            st.markdown("""
            **👥 Métricas de Cliente**
            - % de clientes que compran 2+ veces
            - Tiempo promedio entre compras
            - CLV por segmento (Aficionado vs Pro)
            - NPS específico por soporte técnico
            """)
        
        with col3:
            st.markdown("""
            **🚀 Métricas de Crecimiento**
            - Tasa de upgrade (de cámara básica a pro)
            - % de ventas por referidos
            - Engagement en contenido educativo
            - ROI de campañas por segmento
            """)
            
    except Exception as e:
        st.error(f"Error en el análisis de marketing: {str(e)}")
        st.info("Asegúrate de que todos los modelos estén funcionando correctamente.")

# --- Página RFM mejorada para Kreadores ---
def kreadores_rfm_page():
    kreadores_header()
    st.title("📊 Análisis RFM - Segmentación de Clientes")
    
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
            ("Clientes Fotógrafos Pro", f"{campeones}", "#28a745"),
            ("Revenue Total", f"${monetario_total:,.0f} CLP", "#667eea"),
            ("Clientes Activos", f"{clientes_activos}", "#ffc107")
        ]
        display_metrics(metrics)
        
        # Gráficos RFM
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Distribución de Segmentos RFM")
            # Mejorar los nombres de segmentos para Kreadores
            segment_map = {
                'Reciente-Frecuente-Alto': 'Fotógrafos Pro',
                'Reciente-Frecuente-Bajo': 'Creadores Leales',
                'Reciente-No frecuente-Alto': 'Clientes Premium',
                'Reciente-No frecuente-Bajo': 'Nuevos Fotógrafos',
                'No reciente-Frecuente-Alto': 'En Riesgo VIP',
                'No reciente-Frecuente-Bajo': 'Necesitan Atención',
                'No reciente-No frecuente-Alto': 'Clientes Dormidos',
                'No reciente-No frecuente-Bajo': 'Clientes Perdidos'
            }
            
            rfm_summary['Segmento'] = rfm_summary['RFM_segment'].map(segment_map)
            segment_counts = rfm_summary.groupby('Segmento')['cantidad_clientes'].sum().reset_index()
            
            fig = px.bar(
                segment_counts, 
                x='Segmento',
                y='cantidad_clientes',
                color='Segmento',
                text='cantidad_clientes',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                xaxis_title="Segmento de Cliente",
                yaxis_title="Número de Clientes",
                showlegend=False,
                height=500
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Valor por Segmento")
            
            # Explicación del gráfico
            explain_rfm_value_chart()
            
            fig = px.treemap(
                rfm_summary,
                path=['RFM_segment'],
                values='monetario',
                color='monetario',
                color_continuous_scale='Viridis',
                height=500
            )
            fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error en análisis RFM: {str(e)}")

# --- Página Churn para Kreadores ---
def kreadores_churn_page():
    kreadores_header()
    st.title("📊 Análisis de Churn - Retención de Clientes")
    
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
            ("Total Clientes", f"{total_clientes}", "#667eea"),
            ("Clientes en Riesgo", f"{alto_churn}", "#dc3545"),
            ("Tasa de Churn", f"{churn_rate:.1f}%", "#ffc107")
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
                    'alto': '#dc3545',
                    'bajo': '#28a745'
                },
                title="Riesgo de Abandono de Clientes"
            )
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                pull=[0.1 if risk == 'alto' else 0 for risk in df_churn['churn_risk']]
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Indicador de Retención")
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=churn_rate,
                number={'suffix': "%"},
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Tasa de Churn"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#dc3545"},
                    'steps': [
                        {'range': [0, 15], 'color': "#28a745"},
                        {'range': [15, 25], 'color': "#ffc107"},
                        {'range': [25, 100], 'color': "#dc3545"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 15
                    }
                }
            ))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Interpretación específica para Kreadores
            if churn_rate > 25:
                st.error("🚨 Crítico: Muy pocos clientes vuelven a comprar equipos")
            elif churn_rate > 15:
                st.warning("⚠️ Atención: Churn elevado para equipos especializados")
            else:
                st.success("✅ Excelente: Buena retención de clientes")
            
    except Exception as e:
        st.error(f"Error en análisis de Churn: {str(e)}")

# --- Página Sentimiento para Kreadores ---
def kreadores_sentiment_page():
    kreadores_header()
    st.title("📊 Análisis de Sentimiento - Satisfacción del Cliente")
    
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
            ("Total Interacciones", f"{total_mensajes}", "#667eea"),
            ("Feedback Positivo", f"{positivos}", "#28a745"),
            ("% Satisfacción", f"{positivos_pct:.1f}%", "#ffc107")
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
                    'positivo': '#28a745',
                    'neutral': '#ffc107',
                    'negativo': '#dc3545'
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
                annotations=[dict(text='Satisfacción<br>Clientes', x=0.5, y=0.5, font_size=16, showarrow=False)]
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
                    'positivo': '#28a745',
                    'neutral': '#ffc107',
                    'negativo': '#dc3545'
                },
                text='conteo'
            )
            fig.update_layout(
                xaxis_title="Tipo de Sentimiento",
                yaxis_title="Número de Mensajes",
                showlegend=False,
                height=400
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights específicos para Kreadores
            st.markdown("### 🎯 Insights para Kreadores")
            if positivos_pct > 70:
                st.success("✅ Excelente satisfacción con productos fotográficos")
            elif positivos_pct > 50:
                st.warning("⚠️ Satisfacción mejorable - revisar soporte técnico")
            else:
                st.error("🚨 Baja satisfacción - problemas con equipos o servicio")
            
    except Exception as e:
        st.error(f"Error en análisis de Sentimiento: {str(e)}")

# --- Página Recompra simplificada para Kreadores ---
def kreadores_recompra_page():
    kreadores_header()
    st.title("📊 Propensión de Recompra - Clientes Recurrentes")
    
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
            ("Prob. Recompra", f"{prob_recompra:.1f}%", "#667eea"),
            ("Clientes Recurrentes", f"{clientes_recompra}", "#28a745"),
            ("% Lealtad", f"{(clientes_recompra/total_clientes)*100:.1f}%", "#ffc107")
        ]
        display_metrics(metrics)
        
        # Gráfico principal simplificado
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Historial de Compras")
            compras_count['hizo_compra'] = compras_count['hizo_compra'].apply(
                lambda x: f"{x} compras" if x > 0 else "Sin compras"
            )
            
            fig = px.bar(
                compras_count, 
                x='hizo_compra', 
                y='cantidad_clientes',
                color='hizo_compra',
                color_discrete_sequence=['#667eea', '#42a5f5', '#90caf9', '#bbdefb'],
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
            st.subheader("Probabilidad de Recompra")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob_recompra,
                number={'suffix': "%"},
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Probabilidad de Comprar Nuevamente"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#667eea"},
                    'steps': [
                        {'range': [0, 30], 'color': "#dc3545"},
                        {'range': [30, 70], 'color': "#ffc107"},
                        {'range': [70, 100], 'color': "#28a745"}
                    ]
                }
            ))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error en análisis de Recompra: {str(e)}")

# --- Dashboard Global para Kreadores ---
def kreadores_global_dashboard():
    kreadores_header()
    
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
        
        # Métricas clave específicas para Kreadores
        metrics = [
            ("Clientes Activos", f"{rfm_clientes}", "#667eea"),
            ("Fotógrafos Pro", f"{rfm_campeones}", "#28a745"),
            ("Retención", f"{100-churn_rate:.1f}%", "#ffc107"),
            ("Satisfacción", f"{sent_positivo_pct:.1f}%", "#17a2b8"),
            ("Prob. Recompra", f"{prob_recompra:.1f}%", "#6f42c1")
        ]
        display_metrics(metrics)
        
        # Gráficos principales
        st.subheader("📊 Resumen Ejecutivo Kreadores")
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico RFM sin el treemap problemático
            if not rfm_summary.empty:
                fig = px.scatter(
                    rfm_summary, 
                    x='recencia', 
                    y='monetario',
                    size='frecuencia',
                    color='RFM_segment',
                    hover_name='RFM_segment',
                    hover_data=['recencia', 'frecuencia', 'monetario'],
                    title="Segmentación de Clientes por Comportamiento"
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
                        'positivo': '#28a745',
                        'neutral': '#ffc107',
                        'negativo': '#dc3545'
                    },
                    title="Satisfacción de Clientes"
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
                        'alto': '#dc3545',
                        'bajo': '#28a745'
                    },
                    title="Riesgo de Pérdida de Clientes",
                    hole=0.4
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Métrica de recompra
            if not result.empty:
                fig = go.Figure(go.Indicator(
                    mode="number",
                    value=prob_recompra,
                    number={'suffix': "%"},
                    title={'text': "Probabilidad de Recompra"},
                    domain={'x': [0, 1], 'y': [0, 1]}
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
    except Exception as e:
        st.error(f"Error al cargar datos globales: {str(e)}")

# --- Navegación principal ---
st.sidebar.markdown("""
<div style="text-align: center; padding: 20px;">
    <div style="font-size: 3rem;">📷</div>
    <div style="font-size: 1.5rem; font-weight: bold; color: #667eea;">KREADORES</div>
    <div style="font-size: 0.9rem; color: #6c757d;">Analytics Dashboard</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "🎯 Seleccionar vista:",
    ("Dashboard Global", "Marketing Intelligence", "RFM", "Churn", "Sentimiento", "Recompra"),
    index=0
)

# --- Mostrar página seleccionada ---
if page == "Dashboard Global":
    kreadores_global_dashboard()
elif page == "Marketing Intelligence":
    kreadores_marketing_intelligence()
elif page == "RFM":
    kreadores_rfm_page()
elif page == "Churn":
    kreadores_churn_page()
elif page == "Sentimiento":
    kreadores_sentiment_page()
elif page == "Recompra":
    kreadores_recompra_page()

# --- Pie de página ---
st.sidebar.markdown("---")
st.sidebar.info("""
**Kreadores Analytics Dashboard**  
v2.1 · Actualizado: {date}  
Inspírate, crea y lleva tus ideas al siguiente nivel.
Powered by Supabase
""".format(date=pd.Timestamp.now().strftime("%Y-%m-%d")))

st.sidebar.markdown("""
<div style="text-align: center; margin-top: 20px;">
    <a href="https://www.kreadores.pro" target="_blank" style="color: #667eea; text-decoration: none;">
        🌐 www.kreadores.pro
    </a>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="text-align: center; margin-top: 20px;">
    <a href="https://streamlit-kreadores-dashboard.onrender.com/" target="_blank" style="color: #667eea; text-decoration: none;">
        📊 Analytics Dashboard - Kreadores
    </a>
</div>
""", unsafe_allow_html=True)
