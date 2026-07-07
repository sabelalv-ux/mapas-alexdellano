import streamlit as st
import re
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request
from mplsoccer import VerticalPitch

# Configuración de la página web
st.set_page_config(page_title="Analizador Pro - @alexdellano", layout="wide")
st.title("⚽ Generador Avanzado de Mapas de Rendimiento")
st.write("Sube el archivo HTML de WhoScored para generar el mapa estilo Premium.")

# Funciones de procesamiento
def extraer_json_de_whoscored(html_content):
    match = re.search(r'matchCentreData:\s*(\{.*\}),\s*\n', html_content)
    if not match:
        return None
    return json.loads(match.group(1))

def procesar_datos(data, nombre_jugador):
    jugadores_dict = {}
    id_a_equipo = {}
    
    # Identificar equipos y jugadores
    for team in ['home', 'away']:
        team_name = data[team]['name']
        team_id = data[team]['teamId']
        for p in data[team]['players']:
            jugadores_dict[p['playerId']] = p['name']
            id_a_equipo[p['playerId']] = team_name
            
    events = data['events']
    df = pd.DataFrame(events)
    df['playerName'] = df['playerId'].map(jugadores_dict)
    df['teamName'] = df['playerId'].map(id_a_equipo)
    
    df_player = df[df['playerName'].str.lower() == nombre_jugador.lower()].copy()
    if df_player.empty:
        return None, None
        
    df_player['type_name'] = df_player['type'].apply(lambda x: x.get('displayName', ''))
    df_player['outcome_name'] = df_player['outcomeType'].apply(lambda x: x.get('displayName', ''))
    
    # Extraer los calificadores/tags para estadísticas avanzadas
    df_player['tags'] = df_player['qualifiers'].apply(lambda x: [q.get('type', {}).get('displayName', '') for q in x] if isinstance(x, list) else [])
    
    equipo_jugador = df_player['teamName'].iloc[0]
    return df_player, equipo_jugador

def obtener_escudo_pais(nombre_pais):
    """Intenta descargar la bandera/escudo del país desde un repositorio público"""
    try:
        # Formatear el nombre para la URL (ej: "United Kingdom" -> "gb")
        codigo_pais = "es" # Por defecto España si falla
        if "portugal" in nombre_pais.lower(): codigo_pais = "pt"
        elif "argentina" in nombre_pais.lower(): codigo_pais = "ar"
        elif "france" in nombre_pais.lower() or "francia" in nombre_pais.lower(): codigo_pais = "fr"
        elif "brazil" in nombre_pais.lower() or "brasil" in nombre_pais.lower(): codigo_pais = "br"
        elif "germany" in nombre_pais.lower() or "alemania" in nombre_pais.lower(): codigo_pais = "de"
        elif "england" in nombre_pais.lower() or "inglaterra" in nombre_pais.lower(): codigo_pais = "gb"
        
        url = f"https://flagcdn.com/w160/{codigo_pais}.png"
        img = plt.imread(urllib.request.urlopen(url), format='png')
        return img
    except Exception:
        return None

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
col1, col2 = st.columns([1, 3])

with col1:
    archivo_subido = st.file_uploader("1. Sube tu archivo 'partido.html'", type=["html"])
    nombre_jugador = st.text_input("2. Nombre del jugador", placeholder="Ej: Rodri")
    rival_name = st.text_input("3. Rival (para el título)", placeholder="Ej: Portugal")
    boton_generar = st.button("Generar Gráfico Estilo Premium 🚀")

if boton_generar and archivo_subido and nombre_jugador:
    html_content = archivo_subido.read().decode("utf-8")
    raw_data = extraer_json_de_whoscored(html_content)
    
    if raw_data is None:
        st.error("No se encontraron datos en el HTML. Asegúrate de estar en 'Match Centre'.")
    else:
        df_player, pais_jugador = procesar_datos(raw_data, nombre_jugador)
        
        if df_player is None:
            st.error(f"No se encontraron eventos para '{nombre_jugador}'.")
        else:
            # --- CÁLCULO DE ESTADÍSTICAS AVANZADAS ---
            pases = df_player[df_player['type_name'] == 'Pass']
            total_pases = len(pases)
            pases_exito = pases[pases['outcome_name'] == 'Successful']
            pases_fallo = pases[pases['outcome_name'] == 'Unsuccessful']
            porcentaje = (len(pases_exito) / total_pases * 100) if total_pases > 0 else 0
            
            # Avanzadas utilizando los tags e información posicional
            asistencias = sum(pases_exito['tags'].apply(lambda x: 'IntentionalGoalAssist' in x))
            key_passes = sum(pases_exito['tags'].apply(lambda x: 'KeyPass' in x))
            
            # Pases al área (endX > 83 y endY entre 21.1 y 78.9)
            pases_al_area = pases_exito[(pases_exito['endX'] >= 83) & (pases_exito['endY'] >= 21.1) & (pases_exito['endY'] <= 78.9)]
            
            # Pases progresivos (aproximación: pases hacia adelante que avanzan más de 10 metros en campo contrario)
            pases_progresivos = pases_exito[(pases_exito['endX'] - pases_exito['x'] > 10) & (pases_exito['x'] > 40)]

            # Defensivas
            tackles = len(df_player[df_player['type_name'] == 'Tackle'])
            recoveries = len(df_player[df_player['type_name'] == 'BallRecovery'])
            clearances = len(df_player[df_player['type_name'] == 'Clearance'])
            fouls = len(df_player[df_player['type_name'] == 'FoulCommitted'])

            # --- DISEÑO DEL GRÁFICO (FONDO ULTRA OSCURO) ---
            BACKGROUND_COLOR = '#0b131f'
            LINE_COLOR = '#22334b'

            fig, axs = plt.subplots(1, 3, figsize=(18, 10), facecolor=BACKGROUND_COLOR)
            plt.subplots_adjust(wspace=0.1, bottom=0.15, top=0.85)

            pitch = VerticalPitch(pitch_type='opta', pitch_color=BACKGROUND_COLOR, 
                                  line_color=LINE_COLOR, goal_type='box', line_zorder=2, linewidth=1.2)

            for ax in axs:
                pitch.draw(ax=ax)
                ax.set_facecolor(BACKGROUND_COLOR)

            axs[0].set_title("Pass Zones", color='white', fontsize=15, pad=12, weight='bold')
            axs[1].set_title("Defensive and Offensive Actions", color='white', fontsize=15, pad=12, weight='bold')
            axs[2].set_title("Shot Actions", color='white', fontsize=15, pad=12, weight='bold')

            # --- PANEL 1: PASES (KDE + FLECHAS ESTILO IMAGEN) ---
            if len(pases_exito) > 5:
                pitch.kdeplot(pases_exito['x'], pases_exito['y'], ax=axs[0], cmap='bone', fill=True, alpha=0.25, levels=50, zorder=1)
                
            pitch.arrows(pases_exito['x'], pases_exito['y'], pases_exito['endX'], pases_exito['endY'], color='#00f5d4', width=1.2, headwidth=3, ax=axs[0], zorder=3, alpha=0.8)
            pitch.arrows(pases_fallo['x'], pases_fallo['y'], pases_fallo['endX'], pases_fallo['endY'], color='#ff007f', width=1.2, headwidth=3, ax=axs[0], zorder=3, alpha=0.7)
            pitch.scatter(pases['x'], pases['y'], color='#ff007f', edgecolors='white', s=20, ax=axs[0], zorder=4)

            # --- PANEL 2: ACCIONES DEFENSIVAS Y OFENSIVAS ---
            defensivas = df_player[df_player['type_name'].isin(
