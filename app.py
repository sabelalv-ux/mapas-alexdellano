import streamlit as st
import re
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch

# Configuración de la página web
st.set_page_config(page_title="Analizador de Partidos", layout="wide")
st.title("⚽ Generador de Mapas de Rendimiento (WhoScored)")
st.write("Sube el archivo HTML de WhoScored y escribe el nombre del jugador para generar su mapa.")

# Funciones de procesamiento
def extraer_json_de_whoscored(html_content):
    match = re.search(r'matchCentreData:\s*(\{.*\}),\s*\n', html_content)
    if not match:
        return None
    return json.loads(match.group(1))

def procesar_datos(data, nombre_jugador):
    jugadores_dict = {}
    for team in ['home', 'away']:
        for p in data[team]['players']:
            jugadores_dict[p['playerId']] = p['name']
            
    events = data['events']
    df = pd.DataFrame(events)
    df['playerName'] = df['playerId'].map(jugadores_dict)
    
    df_player = df[df['playerName'].str.lower() == nombre_jugador.lower()].copy()
    if df_player.empty:
        return None
        
    df_player['type_name'] = df_player['type'].apply(lambda x: x.get('displayName', ''))
    df_player['outcome_name'] = df_player['outcomeType'].apply(lambda x: x.get('displayName', ''))
    return df_player

# --- INTERFAZ DE USUARIO (STREAMLIT) ---
col1, col2 = st.columns([1, 3])

with col1:
    archivo_subido = st.file_uploader("1. Sube tu archivo 'partido.html'", type=["html"])
    nombre_jugador = st.text_input("2. Nombre del jugador", placeholder="Ej: Rodri")
    boton_generar = st.button("Generar Gráfico 🚀")

if boton_generar and archivo_subido and nombre_jugador:
    html_content = archivo_subido.read().decode("utf-8")
    raw_data = extraer_json_de_whoscored(html_content)
    
    if raw_data is None:
        st.error("No se encontraron datos en el HTML. Asegúrate de estar en la pestaña 'Match Centre'.")
    else:
        df_player = procesar_datos(raw_data, nombre_jugador)
        
        if df_player is None:
            st.error(f"No se encontraron eventos para el jugador '{nombre_jugador}'. Revisa las mayúsculas o acentos.")
        else:
            # --- DISEÑO DEL GRÁFICO ---
            BACKGROUND_COLOR = '#0d1b2a'
            LINE_COLOR = '#415a77'

            fig, axs = plt.subplots(1, 3, figsize=(18, 10), facecolor=BACKGROUND_COLOR)
            plt.subplots_adjust(wspace=0.1)

            pitch = VerticalPitch(pitch_type='opta', pitch_color=BACKGROUND_COLOR, 
                                  line_color=LINE_COLOR, goal_type='box', line_zorder=2)

            for ax in axs:
                pitch.draw(ax=ax)
                ax.set_facecolor(BACKGROUND_COLOR)

            axs[0].set_title("Pass Zones", color='white', fontsize=16, pad=10, weight='bold')
            axs[1].set_title("Defensive and Offensive Actions", color='white', fontsize=16, pad=10, weight='bold')
            axs[2].set_title("Shot Actions", color='white', fontsize=16, pad=10, weight='bold')

            # PANEL 1: PASES
            pases = df_player[df_player['type_name'] == 'Pass']
            total_pases = len(pases)
            pases_completados = len(pases[pases['outcome_name'] == 'Successful'])
            porcentaje = (pases_completados / total_pases * 100) if total_pases > 0 else 0
            
            pases_exito = pases[pases['outcome_name'] == 'Successful']
            pases_fallo = pases[pases['outcome_name'] == 'Unsuccessful']
            
            if len(pases_exito) > 5:
                pitch.kdeplot(pases_exito['x'], pases_exito['y'], ax=axs[0], cmap='Blues', fill=True, alpha=0.3, levels=100, zorder=1)
                
            pitch.arrows(pases_exito['x'], pases_exito['y'], pases_exito['endX'], pases_exito['endY'], color='#00f5d4', width=1.5, ax=axs[0], zorder=3)
            pitch.arrows(pases_fallo['x'], pases_fallo['y'], pases_fallo['endX'], pases_fallo['endY'], color='#ff007f', width=1.5, ax=axs[0], zorder=3)
            pitch.scatter(pases['x'], pases['y'], color='#ff007f', edgecolors='white', s=30, ax=axs[0], zorder=4)

            # PANEL 2: ACCIONES DEFENSIVAS Y OFENSIVAS
            defensivas = df_player[df_player['type_name'].isin(['Tackle', 'Interception', 'Clearance', 'BallRecovery'])]
            ofensivas = df_player[(df_player['type_name'].isin(['TakeOn', 'FoulGiven'])) | ((df_player['type_name'] == 'Pass') & (df_player['x'] > 50))]

            if len(defensivas) >= 3:
                try:
                    pitch.convex_hull(defensivas['x'], defensivas['y'], ax=axs[1], facecolor='#0077b6', alpha=0.4, edgecolor='#00b4d8', linewidth=2)
                except Exception:
                    pass
            if len(defensivas) > 0:
                pitch.scatter(defensivas['x'], defensivas['y'], color='#00b4d8', s=40, ax=axs[1], zorder=3)
            
            if len(ofensivas) >= 3:
                try:
                    pitch.convex_hull(ofensivas['x'], ofensivas['y'], ax=axs[1], facecolor='#38b000', alpha=0.4, edgecolor='#70e000', linewidth=2)
                except Exception:
                    pass
            if len(ofensivas) > 0:
                pitch.scatter(ofensivas['x'], ofensivas['y'], color='#70e000', s=40, ax=axs[1], zorder=3)

            axs[1].text(50, 30, "DF", color='white', weight='bold', bbox=dict(facecolor='#0077b6', edgecolor='none', boxstyle='round,pad=0.4'))
            axs[1].text(50, 70, "OF", color='white', weight='bold', bbox=dict(facecolor='#38b000', edgecolor='none', boxstyle='round,pad=0.4'))

            # PANEL 3: TIROS
            tiros = df_player[df_player['type_name'] == 'Shot']
            goles = len(df_player[df_player['type_name'] == 'Goal'])
            
            if len(tiros) > 0:
                pitch.scatter(tiros['x'], tiros['y'], color='#ff4d6d', edgecolors='white', s=150, ax=axs[2], zorder=3)
            axs[2].text(50, 52, f"{goles}\nGoals", color='white', fontsize=20, ha='center', va='center', weight='bold')
            axs[2].text(50, 42, f"{len(tiros)}\nShots", color='grey', fontsize=16, ha='center', va='center')

            # Textos inferiores y estadísticas
            plt.suptitle(f"{nombre_jugador} - Match Performance", color='white', fontsize=22, weight='bold', y=0.98)
            stats_left = f"Total Passes: {pases_completados}/{total_pases} ({porcentaje:.1f}%)\n"
            stats_center = f"Tackles: {len(df_player[df_player['type_name'] == 'Tackle'])}   Ball Recovery: {len(df_player[df_player['type_name'] == 'BallRecovery'])}"
            
            # --- MARCA DE AGUA (AQUÍ SE INCLUYE TU NOMBRE) ---
            stats_
