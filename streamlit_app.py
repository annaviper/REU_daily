import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import glob
import os
import pandas as pd

from transformation import transform

st.set_page_config(layout="wide")

PRIORITARI = ["INC000009899529", "INC000009868868"]

daily_path = "daily.xlsx"
if os.path.exists(daily_path):
    os.remove(daily_path)
    print(f"{daily_path} has been deleted.")
else:
    print(f"{daily_path} not found.")

# st.title('Recerca i Universitats')
st.image("https://www.iec.cat/wp-content/uploads/generalitat-de-catalunya-departament-de-jrecerques-i-universitat.png")
st.markdown("")

@st.cache_data
def load_data():
    today = datetime.today().strftime(format='%Y-%m-%d')
    file_path = glob.glob(f"DBA T-Systems JIRA {today}*.csv")[0]
    df = pd.read_csv(file_path, parse_dates=["Creada", "Actualizada", "Resuelta", "Campo personalizado (Due Date Resolució ANS)"])
    df = df.sort_values('Creada')
    
    # Convert the columns to datetime
    df['Creada'] = pd.to_datetime(df['Creada'])
    df['Resuelta'] = pd.to_datetime(df['Resuelta'])

    # Format the date part to '%d/%m/%Y' and keep the time
    df['Creada'] = df['Creada'].dt.strftime('%d/%m/%Y ') # + df['Creada'].dt.strftime('%H:%M:%S')
    df['Resuelta'] = df['Resuelta'].dt.strftime('%d/%m/%Y ') #+ df['Resuelta'].dt.strftime('%H:%M:%S')

    return df

    
data = load_data()
data = transform(data)

# FILTERS
st.markdown("#### Filtres")

col1, col2 = st.columns(2)

with col1:
    components = data['Componente(s)'].unique()
    selected_component = st.radio('Tria un component:', components)
    data = data[data['Componente(s)']==selected_component].reset_index(drop=True)

with col2:
    pass
    # option = st.selectbox('How would you like to be contacted?', ('Email', 'Home phone', 'Mobile phone'))
    # selected_component2 = st.segmented_control(
    #     "Components", components, selection_mode="multi"
    # )
    # data = data[data['Componente(s)'].isin(selected_component2)]

data = data.drop("Componente(s)", axis=1)

st.divider()

# METRIQUES
def data_tiquets(df):
    return df[df['Ticket'].str.startswith(('WO', 'INC'), na=False)].reset_index(drop=True)

tiquets = data_tiquets(data)

st.text("Mètriques")

col0, col1, col2, col3 = st.columns(4)

col0.metric("Total", len(tiquets), border=True)
col1.metric("Oberts", len(tiquets[tiquets['Estado'].isin(["Paralizada"])]), border=True)
col2.metric("Tancats", len(tiquets[tiquets['Estado'].isin(["Pendiente de Validación"])]), border=True)

tiquets['ANS'] = tiquets['ANS'].dt.date

today = datetime.today().date()
col3.metric("ANS caducat", 
            len(tiquets[(tiquets['ANS'] <= today) & (tiquets['Estado'] == "Paralizada")]), 
            border=True)
st.divider()

# TIQUETS
st.subheader("Tiquets 🎫")
st.warning("'INC000009892007 Validació ERR-F1382 no està desactivada' : està tancada per error. Pendent de fer", icon='🚨')
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

tiquets['ANS'] = pd.to_datetime(tiquets['ANS'], format='%d/%m/%Y').dt.date
tiquets['ANS_display'] = tiquets['ANS'].apply(lambda x: x.strftime('%d/%m/%Y'))

tiquets['expired_and_paralizada'] = (
    (tiquets['ANS'] <= datetime.today().date()) & (tiquets['Estado'] == 'Paralizada')
)

yesterday = (datetime.today() - timedelta(days=1)).date().strftime('%d/%m/%Y')
tiquets['Resuelta'] = pd.to_datetime(tiquets['Resuelta']).dt.strftime('%d/%m/%Y')
tiquets = tiquets.style.apply(
    lambda row: [
        #highlight_expired(val, row['expired_and_paralizada']) for val in row
        'background-color: #ffcccc'  # Red color
        if (row['ANS'] <= datetime.today().date() and row['Estado'] == 'Paralizada') 
        else 'background-color: #ffff99'  # Yellow color for PRIORITARI tickets
        if (row["Ticket"] in PRIORITARI) 
        else 'background-color: rgba(0, 204, 102, 0.35)'
        if (row['Resuelta'] == yesterday) 
        else ''
        for _ in range(len(row))
    ],
    axis=1
)

st.dataframe(tiquets)

st.divider()

# PROJECTES
st.subheader("Projectes 🚀")

def data_projectes(df):
    df = df[~df['Ticket'].str.startswith(('WO', 'INC'), na=False)]
    cols_to_drop = ['Ticket', 'Descripción','Remedy Status', 'Resuelta', 'ANS', 'Remedy ID', 'Customer Reporter']
    df = df.drop(cols_to_drop, axis=1)
    df = df.sort_values('Estado', ascending=False)
    return df

projectes = data_projectes(data)
st.dataframe(projectes)