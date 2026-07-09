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
        if "portugal" in p_low: codigo_pais = "pt"
        elif "argentina" in p_low
