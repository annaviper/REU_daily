import pandas as pd
from datetime import datetime, timedelta
import glob
import os
import pandas as pd
import streamlit as st
from os import listdir
from os.path import isfile, join
import regex as re
from transformation import transform


# CONSTANTS
PRIORITARI = ["INC000009899529", "INC000009868868"]

UNEIX = "UNeix"
PD = "Plataforma de Dades"

ESTATS_OBERTS = ["Paralizada"]
ESTATS_TANCATS = ["Pendiente de Validación"]

TODAY_DATETIME = datetime.today()
TODAY_DATETIME_STR = TODAY_DATETIME.strftime(format='%d-%m-%Y %H:%M')
TODAY_STR = TODAY_DATETIME.strftime(format='%Y-%m-%d')
TODAY_DATE = TODAY_DATETIME.date()
YESTERDAY = (TODAY_DATETIME - timedelta(days=1)).date().strftime('%d/%m/%Y')

LEGEND = """
<div style="font-size: 14px; display: flex; justify-content: space-between; align-items: center;">
    <p style="margin-right: 20px;font-size: 18px;"></p>
    <div style="display: flex; align-items: center;">
        <p style="margin-right: 20px;">Llegenda: </p>
        <p style="margin-right: 20px;">
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #FFFF99;"></span> Prioritari
        </p>
        <p style="margin-right: 20px;">
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #FFCCCC;"></span> ANS caducat
        </p>
                <p style="margin-right: 20px;">
            <span style="display: inline-block; width: 20px; height: 20px; background-color: rgba(0, 204, 102, 0.35);"></span> Tancat ahir
        </p>
    </div>
</div>
"""

def data_actualitzacio() -> str:
    csv_path = "data/"
    csv_file_list = [f for f in listdir(csv_path) if isfile(join(csv_path, f))]
    csv_file_string = ", ".join(csv_file_list)
    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}_\d{2})', csv_file_string)
    datetime_str = match.group(1)
    datetime_str = datetime_str.replace("T", " ").replace("_", ":")
    datetime_str = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M").strftime('%d-%m-%Y %H:%M')
    return datetime_str


# @st.cache_data
def load_data(): 
    search_pattern = os.path.join('data', f"*{TODAY_STR}*.csv")
    matching_files = glob.glob(search_pattern)
    if matching_files:
        file_path = matching_files[0]
    else:
        file_path = glob.glob(os.path.join('data', '*.csv'))[0]

    COLUMNES_DATETIME = ["Creada", "Actualizada", "Resuelta", "Campo personalizado (Due Date Resolució ANS)"]
    df = pd.read_csv(file_path, parse_dates=COLUMNES_DATETIME)
    df = df.rename(columns={"Resumen": "Títol", "Clave de incidencia": "JIRA"})

    df['Componente(s)'] = df['Componente(s)'].replace(to_replace={
        "REU-3891-Eina de QdC AUTOSERVEI": PD,
        "REU-2898-UNeix-(UNX)": UNEIX
    })
    df['JIRA'] = df['JIRA'].replace(to_replace="ESMAGREL09-", value="", regex=True)
    return df#.sort_values(["Estado", "Creada"], ascending=[True, True])


def data_tiquets(df):
    return df[df['Ticket'].str.startswith(('WO', 'INC'), na=False)].reset_index(drop=True)


def data_projectes(df):
    df = df[~df['Ticket'].str.startswith(('WO', 'INC'), na=False)]
    cols_to_drop = ['Ticket', 'Remedy Status', 'Resuelta', 'ANS', 'Remedy ID', 'Customer Reporter']
    df = df.drop(cols_to_drop, axis=1)
    df = df.sort_values('Estado', ascending=False)
    return df.reset_index(drop=True)


def tancat_ahir(df) -> list:
    """Si és cap de setmana o dilluns, mostra com a "Tancat ahir" els tancats el divendres"""
    today = datetime.now()
    
    if today.weekday() in [5, 6, 0]:  # Divendres, dissabte, diumenge
        days_since_friday = (today.weekday() - 4) % 7  # Calculate how many days back to Friday
        last_friday = today - timedelta(days=days_since_friday)

        df = df.dropna(subset=['Resuelta'])
        closed_on_friday = df[(df['Estado'].isin(ESTATS_TANCATS)) & 
                                   (df['Resuelta'].dt.date == last_friday.date())]
        
        return closed_on_friday['Ticket'].tolist()
    else:
        return df[df.Resuelta == YESTERDAY]['Ticket'].tolist()
    

st.set_page_config(layout="wide")

st.image("https://www.iec.cat/wp-content/uploads/generalitat-de-catalunya-departament-de-jrecerques-i-universitat.png")
ultima_actualitzacio = data_actualitzacio()
st.text(f"Última actualització: {ultima_actualitzacio}")
st.markdown("")

data = load_data()
data = transform(data)

# FILTERS
st.markdown("#### 🔎 Filtres")
components = data['Componente(s)'].unique()
components = sorted(components, reverse=True)  # UNeix primer
selected_component = st.radio('Tria un component:', components)
data = data[data['Componente(s)']==selected_component].drop("Componente(s)", axis=1)
st.markdown("")

tiquets = data_tiquets(data)

# METRIQUES
st.markdown("#### Mètriques setmanals")

total, oberts, tancats, ans_caducat = st.columns(4)
total.metric("Total", len(tiquets), border=True)
oberts.metric("Oberts", len(tiquets[tiquets['Estado'].isin(ESTATS_OBERTS)]), border=True)
tancats.metric("Tancats", len(tiquets[tiquets['Estado'].isin(ESTATS_TANCATS)]), border=True)

# Convertir a data per poder comparar
tiquets['ANS'] = pd.to_datetime(tiquets['ANS'], errors='coerce', dayfirst=True).dt.date
caducat_i_paralitzat = tiquets[(tiquets['ANS'] <= TODAY_DATE) & (tiquets['Estado'] == "Paralizada")]
ans_caducat.metric("ANS caducat", len(caducat_i_paralitzat), border=True)
st.divider()

# TIQUETS
st.subheader("🎫 Tiquets")

st.markdown("""
    <style>
        .stTextInput>div>div>input {
            border: 1px solid #999999;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)

if "search_query_ticket" not in st.session_state:
    st.session_state.search_query_ticket = ""
if "search_query_jira" not in st.session_state:
    st.session_state.search_query_jira = ""

search_ticket, search_jira, reset = st.columns([1.2, 1.2, 4])

with search_ticket:
    search_query_ticket = st.text_input(
        "Busca per número d'INC/WO:",
        value=st.session_state.search_query_ticket, 
        key="search_query_ticket", 
        placeholder="INC000009906850"
    )
    if search_query_ticket:
        tiquets = tiquets[tiquets.Ticket == search_query_ticket]

with search_jira:
    search_query_jira = st.text_input(
        "Busca per número de Jira:",
        value=st.session_state.search_query_jira, 
        placeholder="7895", 
        key="search_query_jira"
    )
    if search_query_jira:
        tiquets = tiquets[tiquets.JIRA == search_query_jira]

def reset_filters():
    st.session_state.search_query_ticket = ""
    st.session_state.search_query_jira = ""
    st.rerun()

with reset:
    st.markdown("<div style='padding-top: 28px;'>", unsafe_allow_html=True)
    st.button("🧹 Reset filtres", on_click=reset_filters)
    st.markdown("</div>", unsafe_allow_html=True)



st.markdown(LEGEND, unsafe_allow_html=True)

if selected_component == UNEIX:
    st.warning('"INC000009892007 Validació ERR-F1382 no està desactivada" : està tancada per error. Pendent de fer', icon='🚨')


# Afegir colors a les files segons condició
tiquets['ANS'] = pd.to_datetime(tiquets['ANS'], format='%d/%m/%Y').dt.date
tiquets['Resuelta'] = pd.to_datetime(tiquets['Resuelta']).dt.strftime('%d/%m/%Y')

tancats_ahir = tancat_ahir(data)

def style_row(row):
    styles = []
    if row.ANS <= datetime.today().date() and row.Estado == 'Paralizada':
        styles = ['background-color: #ffcccc'] * len(row)  # vermell
    elif row.Ticket in PRIORITARI:
        styles = ['background-color: #ffff99'] * len(row)  # groc
    elif row.Ticket in tancats_ahir:
        styles = ['background-color: rgba(0, 204, 102, 0.35)'] * len(row)  # verd
    else:
        styles = [''] * len(row)
    return styles

st.dataframe(data=tiquets.style.apply(style_row, axis=1))

st.divider()

# PROJECTES
st.subheader("🚀 Projectes")

projectes = data_projectes(data)
st.dataframe(projectes)