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
st.title("⚽ Generador de Gráficos de Rendimiento (Estilo Federación)")

# Funciones de procesamiento de datos
def extraer_json_de_whoscored(html_content):
    match = re.search(r'matchCentreData:\s*(\{.*\}),\s*\n', html_content)
    if not match:
        return None
    return json.loads(match.group(1))

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
    
    df_player = df[df['playerName'].str.lower() == nombre_jugador.lower()].copy()
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

# --- INTERFAZ ---
col1, col2 = st.columns([1, 3])

with col1:
    archivo_subido = st.file_uploader("1. Sube tu archivo 'partido.html'", type=["html"])
    nombre_jugador = st.text_input("2. Nombre del jugador", placeholder="Ej: Aymeric Laporte")
    rival_name = st.text_input("3. Rival", placeholder="Ej: Austria")
    marcador_text = st.text_input("4. Resultado", placeholder="Ej: 3 - 0")
    minutos_jugados = st.text_input("5. Minutos jugados", placeholder="Ej: 86")
    boton_generar = st.button("Generar Mapa Estilo Claro 🚀")

if boton_generar and archivo_subido and nombre_jugador:
    html_content = archivo_subido.read().decode("utf-8")
    raw_data = extraer_json_de_whoscored(html_content)
    
    if raw_data is None:
        st.error("No se encontraron datos en el HTML.")
    else:
        df_player, pais_jugador = procesar_datos(raw_data, nombre_jugador)
        
        if df_player is None:
            st.error(f"No se encontraron eventos para '{nombre_jugador}'.")
        else:
            # --- FILTRADO DE ACCIONES ---
            pases = df_player[df_player['type_name'] == 'Pass']
            pases_exito = pases[pases['outcome_name'] == 'Successful']
            pases_fallo = pases[pases['outcome_name'] == 'Unsuccessful']
            
            # Progresivos (aproximación por distancia hacia adelante)
            pases_prog = pases_exito[(pases_exito['endX'] - pases_exito['x'] > 8)]
            key_passes = sum(pases_exito['tags'].apply(lambda x: 'KeyPass' in x))
            asistencias = sum(pases_exito['tags'].apply(lambda x: 'IntentionalGoalAssist' in x))
            
            # Tiros y Goles
            tiros = df_player[df_player['type_name'] == 'Shot']
            goles = len(df_player[df_player['type_name'] == 'Goal'])
            tiros_puerta = len(df_player[df_player['tags'].apply(lambda x: 'OnTarget' in x)])
            
            # Defensivas
            tackles_succ = df_player[(df_player['type_name'] == 'Tackle') & (df_player['outcome_name'] == 'Successful')]
            tackles_unsucc = df_player[(df_player['type_name'] == 'Tackle') & (df_player['outcome_name'] == 'Unsuccessful')]
            recoveries = df_player[df_player['type_name'] == 'BallRecovery']
            interceptions = df_player[df_player['type_name'] == 'Interception']
            clearances = df_player[df_player['type_name'] == 'Clearance']

            # --- CONFIGURACIÓN VISUAL (ESTILO CLARO) ---
            BACKGROUND_COLOR = '#f4f4f6'
            LINE_COLOR = '#111111'

            fig, axs = plt.subplots(1, 2, figsize=(16, 11), facecolor=BACKGROUND_COLOR)
            plt.subplots_adjust(wspace=0.15, bottom=0.22, top=0.78)

            pitch = VerticalPitch(pitch_type='opta', pitch_color=BACKGROUND_COLOR, 
                                  line_color=LINE_COLOR, goal_type='box', line_zorder=2, linewidth=1.5)

            for ax in axs:
                pitch.draw(ax=ax)
                ax.set_facecolor(BACKGROUND_COLOR)

            axs[0].set_title("Offensive Actions", color='black', fontsize=16, pad=15, weight='bold')
            axs[1].set_title("Defensive Actions", color='black', fontsize=16, pad=15, weight='bold')

            # --- DIBUJAR ACCIONES OFENSIVAS (PANEL 1) ---
            # Pases con líneas finas y cabezas de flecha sutiles
            pitch.arrows(pases_exito['x'], pases_exito['y'], pases_exito['endX'], pases_exito['endY'], color='#8e9aaf', width=1, headwidth=2.5, ax=axs[0], zorder=3)
            pitch.arrows(pases_prog['x'], pases_prog['y'], pases_prog['endX'], pases_prog['endY'], color='#00b4d8', width=1.3, headwidth=3, ax=axs[0], zorder=3)
            
            # Tiros
            if len(tiros) > 0:
                pitch.scatter(tiros['x'], tiros['y'], color='#ff4d6d', edgecolors='black', s=80, marker='o', ax=axs[0], zorder=4)

            # --- DIBUJAR ACCIONES DEFENSIVAS (PANEL 2) ---
            pitch.scatter(tackles_succ['x'], tackles_succ['y'], color='#00b4d8', edgecolors='black', s=70, marker='X', ax=axs[1], zorder=3)
            pitch.scatter(tackles_unsucc['x'], tackles_unsucc['y'], color='#ff4d6d', edgecolors='black', s=70, marker='X', ax=axs[1], zorder=3)
            pitch.scatter(recoveries['x'], recoveries['y'], color='#0077b6', edgecolors='black', s=70, marker='o', ax=axs[1], zorder=3)
            pitch.scatter(interceptions['x'], interceptions['y'], color='#52b788', edgecolors='black', s=90, marker='*', ax=axs[1], zorder=3)
            pitch.scatter(clearances['x'], clearances['y'], color='#edef5d', edgecolors='black', s=70, marker='p', ax=axs[1], zorder=3)

            # --- TEXTOS DE ENCABEZADO (IZQUIERDA) ---
            res_rival = f" in {pais_jugador} {marcador_text} {rival_name}" if rival_name else f" in {pais_jugador}"
            min_text = f"  |  Minutes played: {minutos_jugados}" if minutos_jugados else ""
            
            fig.text(0.18, 0.91, nombre_jugador, color='black', fontsize=32, weight='bold', ha='left')
            fig.text(0.18, 0.86, f"{res_rival}{min_text}", color='#4a4a4a', fontsize=16, ha='left')

            # --- LEYENDAS INFERIORES SIMPLIFICADAS ---
            leg_y1, leg_y2 = 0.12, 0.08
            
            # Leyenda Bloque 1 (Ofensivo)
            fig.text(0.08, leg_y1, f"⚽ Goals: {goles}", color='black', fontsize=11, weight='bold')
            fig.text(0.08, leg_y2, f"🎯 Shots on Target: {tiros_puerta}", color='black', fontsize=11)
            fig.text(0.24, leg_y1, f"─ Successful Pass: {len(pases_exito)}", color='black', fontsize=11)
            fig.text(0.24, leg_y2, f"─ Progressive Pass: {len(pases_prog)}", color='black', fontsize=11)
            fig.text(0.40, leg_y1, f"─ Key Passes: {key_passes}", color='black', fontsize=11)
            fig.text(0.40, leg_y2, f"─ Assists: {asistencias}", color='black', fontsize=11)

            # Leyenda Bloque 2 (Defensivo)
            fig.text(0.56, leg_y1, f"✖ Tackle (Succ.): {len(tackles_succ)}", color='black', fontsize=11)
            fig.text(0.56, leg_y2, f"✖ Tackle (Unsucc.): {len(tackles_unsucc)}", color='black', fontsize=11)
            fig.text(0.72, leg_y1, f"● Ball Recoveries: {len(recoveries)}", color='black', fontsize=11)
            fig.text(0.72, leg_y2, f"★ Interceptions: {len(interceptions)}", color='black', fontsize=11)
            fig.text(0.86, leg_y1, f"⬠ Clearances: {len(clearances)}", color='black', fontsize=11)

            # --- MARCA DE AGUA EXCLUSIVA ---
            fig.text(0.50, 0.03, "@alexdellano", color='#a3a3a3', fontsize=16, ha='center', weight='bold')

            # --- ESCUDO/BANDERA DE LA SELECCIÓN ---
            escudo = obtener_escudo_pais(pais_jugador)
            if escudo is not None:
                ax_logo = fig.add_axes([0.06, 0.84, 0.09, 0.09]) 
                ax_logo.imshow(escudo)
                ax_logo.axis('off')

            st.pyplot(fig, facecolor=BACKGROUND_COLOR)
