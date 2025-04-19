import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import glob
import os
import pandas as pd

from transformation import transform


# CONSTANTS
PRIORITARI = ["INC000009899529", "INC000009868868"]

UNEIX = "UNeix"
PD = "Plataforma de Dades"

ESTATS_OBERTS = ["Paralizada"]
ESTATS_TANCATS = ["Pendiente de Validación"]

TODAY_DATETIME = datetime.today()
# TODAY_DATETIME_STR = TODAY_DATETIME.strftime(format='%d-%m-%Y %H:%M')
TODAY_STR = TODAY_DATETIME.strftime(format='%Y-%m-%d')
TODAY_DATE = TODAY_DATETIME.date()
YESTERDAY = yesterday = (TODAY_DATETIME - timedelta(days=1)).date().strftime('%d/%m/%Y')


st.set_page_config(layout="wide")


st.image("https://www.iec.cat/wp-content/uploads/generalitat-de-catalunya-departament-de-jrecerques-i-universitat.png")
st.text(f"Última actualització: {TODAY_STR}")
st.markdown("")

@st.cache_data
def load_data():    
    search_pattern = os.path.join('data', f"REU - SEMANAL (DBA T-Systems JIRA) {TODAY_STR}*.csv")
    file_path = glob.glob(search_pattern)[0]
    COLUMNES_DATETIME = ["Creada", "Actualizada", "Resuelta", "Campo personalizado (Due Date Resolució ANS)"]
    df = pd.read_csv(file_path, parse_dates=COLUMNES_DATETIME)
    df = df.sort_values('Creada')

    df['Componente(s)'] = df['Componente(s)'].replace(to_replace={
        "REU-3891-Eina de QdC AUTOSERVEI": PD,
        "REU-2898-UNeix-(UNX)": UNEIX
    })

    # Format the date part to '%d/%m/%Y'
    df['Creada'] = df['Creada'].dt.strftime('%d/%m/%Y') 
    df['Resuelta'] = df['Resuelta'].dt.strftime('%d/%m/%Y')

    return df

data = load_data()
data = transform(data)


# FILTERS
st.markdown("#### 🔎 Filtres")
components = data['Componente(s)'].unique()
selected_component = st.radio('Tria un component:', components)
data = data[data['Componente(s)']==selected_component].reset_index(drop=True)
data = data.drop("Componente(s)", axis=1)
st.markdown("")

# METRIQUES
st.markdown("#### Mètriques setmanals")

def data_tiquets(df):
    return df[df['Ticket'].str.startswith(('WO', 'INC'), na=False)].reset_index(drop=True)

tiquets = data_tiquets(data)

col0, col1, col2, col3 = st.columns(4)
col0.metric("Total", len(tiquets), border=True)
col1.metric("Oberts", len(tiquets[tiquets['Estado'].isin(ESTATS_OBERTS)]), border=True)
col2.metric("Tancats", len(tiquets[tiquets['Estado'].isin(ESTATS_TANCATS)]), border=True)

# Convertir a data per poder comparar
tiquets['ANS'] = tiquets['ANS'].dt.date
caducat_i_paralitzat = tiquets[(tiquets['ANS'] <= TODAY_DATE) & (tiquets['Estado'] == "Paralizada")]
col3.metric("ANS caducat", len(caducat_i_paralitzat), border=True)
st.divider()

# TIQUETS
st.subheader("🎫 Tiquets")
if selected_component == UNEIX:
    st.warning('"INC000009892007 Validació ERR-F1382 no està desactivada" : està tancada per error. Pendent de fer', icon='🚨')
legend_html = """
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
st.markdown(legend_html, unsafe_allow_html=True)

# Afegir colors a les files segons condició
tiquets['ANS'] = pd.to_datetime(tiquets['ANS'], format='%d/%m/%Y').dt.date
tiquets['Resuelta'] = pd.to_datetime(tiquets['Resuelta']).dt.strftime('%d/%m/%Y')
tiquets = tiquets.style.apply(
    lambda row: [
        'background-color: #ffcccc'  # vermell
        if (row['ANS'] <= datetime.today().date() and row['Estado'] == 'Paralizada') 
        else 'background-color: #ffff99'  # groc
        if (row["Ticket"] in PRIORITARI) 
        else 'background-color: rgba(0, 204, 102, 0.35)'  # verd
        if (row['Resuelta'] == YESTERDAY) 
        else ''
        for _ in range(len(row))
    ],
    axis=1
)

st.dataframe(tiquets)
st.divider()

# PROJECTES
st.subheader("🚀 Projectes")

def data_projectes(df):
    df = df[~df['Ticket'].str.startswith(('WO', 'INC'), na=False)]
    cols_to_drop = ['Ticket', 'Remedy Status', 'Resuelta', 'ANS', 'Remedy ID', 'Customer Reporter']
    df = df.drop(cols_to_drop, axis=1)
    df = df.sort_values('Estado', ascending=False)
    return df

projectes = data_projectes(data)
st.dataframe(projectes)