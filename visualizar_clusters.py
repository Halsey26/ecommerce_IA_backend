import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from math import pi
import squarify
from sklearn.decomposition import PCA

def cargar_y_preparar_datos():
    # Cargar los datos clusterizados
    df = pd.read_csv("chat_sesiones_clusterizadas.csv")
    
    # Asegurarse de que 'cluster' es categórico
    df['cluster'] = df['cluster'].astype('category')
    
    return df

def generar_pdf_reporte():
    df = cargar_y_preparar_datos()
    
    # Crear el PDF
    with PdfPages('reporte_clustering.pdf') as pdf:
        # Configuración general
        plt.rcParams.update({'font.size': 12})
        
        # 1. Distribución de clusters
        plt.figure(figsize=(12, 8))
        sns.countplot(data=df, x='cluster', hue='cluster', palette='viridis', legend=False)
        plt.title('Distribución de Chats por Cluster', fontsize=16)
        plt.xlabel('Cluster', fontsize=14)
        plt.ylabel('Número de Chats', fontsize=14)
        
        for p in plt.gca().patches:
            plt.gca().annotate(f'{int(p.get_height())}', 
                             (p.get_x() + p.get_width() / 2., p.get_height()), 
                             ha='center', va='center', 
                             xytext=(0, 10), 
                             textcoords='offset points')
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # 2. Mensajes por cluster
        plt.figure(figsize=(12, 8))
        sns.boxplot(data=df, x='cluster', y='mensajes_totales', hue='cluster', 
                   palette='viridis', legend=False)
        plt.title('Distribución de Mensajes por Cluster', fontsize=16)
        plt.xlabel('Cluster', fontsize=14)
        plt.ylabel('Número de Mensajes', fontsize=14)
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # 3. Duración por cluster
        plt.figure(figsize=(12, 8))
        sns.boxplot(data=df, x='cluster', y='duracion_sesion', hue='cluster', 
                   palette='viridis', legend=False)
        plt.title('Duración de Sesión por Cluster', fontsize=16)
        plt.xlabel('Cluster', fontsize=14)
        plt.ylabel('Duración (segundos)', fontsize=14)
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # 4. Relación mensajes-duración
        plt.figure(figsize=(12, 8))
        sns.scatterplot(data=df, x='mensajes_totales', y='duracion_sesion', 
                       hue='cluster', palette='viridis', alpha=0.7, s=100)
        plt.title('Relación entre Mensajes y Duración por Cluster', fontsize=16)
        plt.xlabel('Número de Mensajes', fontsize=14)
        plt.ylabel('Duración (segundos)', fontsize=14)
        plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # 5. Heatmap de características
        cluster_stats = df.groupby('cluster')[['mensajes_totales', 'duracion_sesion']].mean()
        plt.figure(figsize=(12, 8))
        sns.heatmap(cluster_stats.T, annot=True, cmap='YlGnBu', fmt='.1f', 
                   cbar_kws={'label': 'Valor Promedio'})
        plt.title('Promedio de Características por Cluster', fontsize=16)
        plt.xlabel('Cluster', fontsize=14)
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # 6. Treemap de clusters
        cluster_counts = df['cluster'].value_counts()
        plt.figure(figsize=(12, 8))
        squarify.plot(sizes=cluster_counts.values,
                     label=[f'Cluster {k}\n({v} chats)' for k, v in cluster_counts.items()],
                     color=sns.color_palette('viridis', len(cluster_counts)),
                     alpha=0.7,
                     text_kwargs={'fontsize':12})
        plt.title('Distribución de Chats por Cluster (Treemap)', fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # 7. Tabla de estadísticas
        stats = df.groupby('cluster').agg({
            'mensajes_totales': ['mean', 'median', 'std', 'count'],
            'duracion_sesion': ['mean', 'median', 'std'],
            'chatId': 'count'
        })
        
        stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
        stats.rename(columns={'chatId_count': 'n_chats'}, inplace=True)
        
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.axis('off')
        table = ax.table(cellText=stats.round(2).values,
                        rowLabels=stats.index,
                        colLabels=[col.replace('_', ' ').title() for col in stats.columns],
                        loc='center',
                        cellLoc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.5)
        plt.title('Estadísticas por Cluster', fontsize=16, y=1.1)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    
    print("✅ Reporte PDF generado: 'reporte_clustering.pdf'")

if __name__ == "__main__":
    generar_pdf_reporte()