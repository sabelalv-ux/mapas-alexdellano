import streamlit as st
import re
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request
from mplsoccer import VerticalPitch

# --- CONFIGURACIÓN DE LA PÁGINA (ESTILO OSCURO POR DEFECTO) ---
st.set_page_config(page_title="Analizador Pro - @alexdellano", layout="wide")

# Forzar algunos estilos CSS para clonar la apariencia oscura y los botones de la barra lateral de per-90
st.markdown("""
    <style>
    /* Estilos para los botones del menú lateral */
    div.stButton > button:first-child {
        width: 100%;
        background-color: #1e1e24;
        color: #ffffff;
        border: 1px solid #3a3a42;
        border-radius: 4px;
        padding: 0.5rem;
        margin-bottom: 0.2rem;
        text-align: center;
    }
    div.stButton > button:first-child:hover {
        border-color: #ff4d6d;
        color: #ff4d6d;
    }
    </style>
""", unsafe_allow_html=True)

# --- PANEL LATERAL (MENÚ DE NAVEGACIÓN ESTILO PER-90) ---
with st.sidebar:
    st.button("Inicio")
    st.button("Gráfico de tarta (Pizza)")
    st.button("Estadísticas de Jugador")
    st.button("Comparativa de Radares")
    st.button("Gráfico de Dispersión (Scatter)")
    st.button("Tabla de Datos")
    st.button("Filtros de Estadísticas")
    st.button("Puntuación de Similitud")
    st.button("Clasificación por Rol")
    st.button("Datos de Eventos")
    st.button("Informes de Partido")

# --- FUNCIONES DE PROCESAMIENTO DE DATOS ---
def extraer_json_de_whoscored(html_content):
    match = re.search(r'matchCentreData:\s*(\{.*\}),\s*\n', html_content)
    if not match:
        return None
    return json.loads(match.group(1))

def obtener_lista_jugadores(data):
    jugadores = []
    for team in ['home', 'away']:
        for p in data[team]['players']:
            jugadores.append(p['name'])
    return sorted(jugadores)

def procesar_datos(data, nombre_jugador):
    jugadores_dict = {}
    id_a_equipo = {}
    
    for team in ['home', 'away']:
        team_name = data[team]['name']
        for p in data[team]['players']:
            jugadores_dict[p['playerId']] = p['name']
            id_a_equipo[p['playerId']] = team_name
            
    events = data['events']
    df = pd.DataFrame(events)
    df['playerName'] = df['playerId'].map(jugadores_dict)
    df['teamName'] = df['playerId'].map(id_a_equipo)
    
    df_player = df[df['playerName'] == nombre_jugador].copy()
    if df_player.empty:
        return None, None
        
    df_player['type_name'] = df_player['type'].apply(lambda x: x.get('displayName', ''))
    df_player['outcome_name'] = df_player['outcomeType'].apply(lambda x: x.get('displayName', ''))
    df_player['tags'] = df_player['qualifiers'].apply(lambda x: [q.get('type', {}).get('displayName', '') for q in x] if isinstance(x, list) else [])
    
    equipo_jugador = df_player['teamName'].iloc[0]
    return df_player, equipo_jugador

def obtener_escudo_pais(nombre_pais):
    try:
        codigo_pais = "es"
        p_low = nombre_pais.lower()
        
        # Corregidas todas las líneas eliminando cortes visuales o saltos de línea incorrectos
        if "portugal" in p_low: codigo_pais = "pt"
        elif "argentina" in p_low: codigo_pais = "ar"
        elif "france" in p_low or "francia" in p_low: codigo_pais = "fr"
        elif "brazil" in p_low or "brasil" in p_low: codigo_pais = "br"
        elif "germany" in p_low or "alemania" in p_low: codigo_pais = "de"
        elif "england" in p_low or "inglaterra" in p_low: codigo_pais = "gb"
        elif "italy" in p_low or "italia" in p_low: codigo_pais = "it"
        
        url = f"https://flagcdn.com/w160/{codigo_pais}.png"
        img = plt.imread(urllib.request.urlopen(url), format='png')
        return img
    except Exception:
        return None

# --- CUERPO PRINCIPAL ---

# 1. Seleccionar Opción (Radio Buttons superiores al estilo per-90)
opciones_principales = [
    "Cargar Datos (Requerido)", 
    "Mapa de Pases", 
    "Eventos de Jugador", 
    "Eventos de Equipo", 
    "xT vía Pases (Equipo)", 
    "Control Zonal"
]
opcion_seleccionada = st.radio("Selecciona una Opción", opciones_principales, index=2)

st.markdown("---")

col1, col2 = st.columns([1, 2.5])

with col1:
    # Contenedor para cargar el archivo
    archivo_subido = st.file_uploader("Sube tu archivo 'partido.html' exportado de WhoScored", type=["html"])

    if archivo_subido:
        html_content = archivo_subido.read().decode("utf-8")
        raw_data = extraer_json_de_whoscored(html_content)
        
        if raw_data:
            lista_jugadores = obtener_lista_jugadores(raw_data)
            
            # 2. Selector de Nombre de Jugador
            nombre_jugador = st.selectbox("Selecciona el Nombre del Jugador", lista_jugadores)
            
            # 3. Selección de Métricas (Multiselect en castellano)
            metricas_disponibles = ["Gol", "Tiro", "Asistencia de Tiro", "Pase al Tercio Final", "Acción Defensiva"]
            metricas_seleccionadas = st.multiselect(
                "Selecciona la(s) Métrica(s)", 
                metricas_disponibles, 
                default=["Gol", "Tiro", "Asistencia de Tiro", "Pase al Tercio Final", "Acción Defensiva"]
            )
            
            # Inputs para personalizar la cabecera del gráfico
            rival_name = st.text_input("Rival", placeholder="Ej: Marruecos")
            marcador_text = st.text_input("Resultado", placeholder="Ej: 2 - 0")
            minutos_jugados = st.text_input("Minutos jugados", placeholder="Ej: 90")
                
            # Botón para generar
            boton_generar = st.button("Generar")
        else:
            st.error("Error al procesar el archivo HTML.")
    else:
        st.info("Por favor, sube un archivo HTML de WhoScored en el panel superior para comenzar.")

# Lógica de renderizado del gráfico en la columna derecha
if archivo_subido and raw_data and 'boton_generar' in locals() and boton_generar and nombre_jugador:
    with col2:
        df_player, pais_jugador = procesar_datos(raw_data, nombre_jugador)
        
        if df_player is not None:
            # --- FILTRADO DE ACCIONES ---
            pases = df_player[df_player['type_name'] == 'Pass']
            pases_exito = pases[pases['outcome_name'] == 'Successful']
            
            # Clasificación según lo seleccionado en el multiselect
            pases_prog = pases_exito[(pases_exito['endX'] - pases_exito['x'] > 8)] if "Pase al Tercio Final" in metricas_seleccionadas else pd.DataFrame()
            key_passes = sum(pases_exito['tags'].apply(lambda x: 'KeyPass' in x)) if "Asistencia de Tiro" in metricas_seleccionadas else 0
            asistencias = sum(pases_exito['tags'].apply(lambda x: 'IntentionalGoalAssist' in x))
            
            tiros = df_player[df_player['type_name'] == 'Shot'] if "Tiro" in metricas_seleccionadas else pd.DataFrame()
            goles = len(df_player[df_player['type_name'] == 'Goal']) if "Gol" in metricas_seleccionadas else 0
            
            # Defensivas agrupadas
            tackles_succ = df_player[(df_player['type_name'] == 'Tackle') & (df_player['outcome_name'] == 'Successful')]
            recoveries = df_player[df_player['type_name'] == 'BallRecovery']
            interceptions = df_player[df_player['type_name'] == 'Interception']
            
            # --- CONFIGURACIÓN VISUAL DEL GRÁFICO (TEMA OSCURO) ---
            BACKGROUND_COLOR = '#192231' 
            LINE_COLOR = '#ffffff'

            fig, axs = plt.subplots(1, 2, figsize=(16, 10), facecolor=BACKGROUND_COLOR)
            plt.subplots_adjust(wspace=0.15, bottom=0.20, top=0.80)

            pitch = VerticalPitch(pitch_type='opta', pitch_color=BACKGROUND_COLOR, 
                                  line_color='#3a4a63', goal_type='box', line_zorder=2, linewidth=1.2)

            for ax in axs:
                pitch.draw(ax=ax)
                ax.set_facecolor(BACKGROUND_COLOR)

            axs[0].set_title("Acciones Ofensivas", color='white', fontsize=14, pad=15, weight='bold')
            axs[1].set_title("Acciones Defensivas", color='white', fontsize=14, pad=15, weight='bold')

            # --- DIBUJAR ACCIONES FILTRADAS ---
            if "Pase al Tercio Final" in metricas_seleccionadas and len(pases_prog) > 0:
                pitch.arrows(pases_prog['x'], pases_prog['y'], pases_prog['endX'], pases_prog['endY'], color='#00b4d8', width=1.3, headwidth=3, ax=axs[0], zorder=3)
            
            if "Tiro" in metricas_seleccionadas and len(tiros) > 0:
                pitch.scatter(tiros['x'], tiros['y'], color='#ff4d6d', edgecolors='white', s=90, marker='o', ax=axs[0], zorder=4)

            if "Acción Defensiva" in metricas_seleccionadas:
                pitch.scatter(tackles_succ['x'], tackles_succ['y'], color='#52b788', edgecolors='white', s=80, marker='X', ax=axs[1], zorder=3)
                pitch.scatter(recoveries['x'], recoveries['y'], color='#0077b6', edgecolors='white', s=80, marker='o', ax=axs[1], zorder=3)
                pitch.scatter(interceptions['x'], interceptions['y'], color='#edef5d', edgecolors='white', s=90, marker='*', ax=axs[1], zorder=3)

            # --- TEXTOS DE CABECERA ESTILO CLON ---
            res_rival = f" vs. {rival_name}" if rival_name else ""
            subtitulo = f"Datos extraídos de WhoScored | Minutos jugados: {minutos_jugados}" if minutos_jugados else "Datos de WhoScored"
            
            fig.text(0.18, 0.92, f"{nombre_jugador}{res_rival}", color='white', fontsize=28, weight='bold', ha='left')
            fig.text(0.18, 0.88, subtitulo, color='#a3b8cc', fontsize=14, ha='left')

            # --- LEYENDAS INFERIORES EN CASTELLANO ---
            leg_y = 0.08
            fig.text(0.08, leg_y, f"Goles: {goles} | Tiros: {len(tiros)}", color='white', fontsize=11)
            fig.text(0.35, leg_y, f"Pases al Tercio Final: {len(pases_prog)}", color='white', fontsize=11)
            fig.text(0.65, leg_y, f"Acciones Defensivas: {len(tackles_succ)+len(recoveries)+len(interceptions)}", color='white', fontsize=11)

            # Marca de agua
            fig.text(0.50, 0.03, "@alexdellano", color='#5c7599', fontsize=14, ha='center', weight='bold')

            # Bandera / Escudo
            escudo = obtener_escudo_pais(pais_jugador)
            if escudo is not None:
                ax_logo = fig.add_axes([0.06, 0.86, 0.09, 0.09]) 
                ax_logo.imshow(escudo)
                ax_logo.axis('off')

            st.pyplot(fig, facecolor=BACKGROUND_COLOR)
        else:
            st.error("No se encontraron eventos para este jugador.")
