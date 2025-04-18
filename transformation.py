import pandas as pd
import re
import numpy as np


def neteja_resumen(df):
    patterns = [
        r"Incidència a UNeix AM09_23 ",
        r"Suport funcional a UNeix AM09_23 ",
        r"UNeix AM09 "
    ]
    
    combined_pattern = "|".join(patterns)
    df['Resumen'] = df['Resumen'].str.replace(combined_pattern, "", regex=True)
    df['Resumen'] = df['Resumen'].str.replace(r"^[-.]\s*", "", regex=True)
    return df


def neteja_descripcio(df):
    regex_pattern = r">>Descripció detallada:(.*?)>>Adreces de correu addicionals"
    regex_pattern2 = r"destinat al lot AM09_23 T-Systems.(.*?)_______________________________________________________________"
    regex_pattern3 = r"> Resum de la incidència o de l’error que es mostra a la pantalla: (.*?)> La incidència afecta"
    regex_pattern4 = r"destinat al lot AM09_23 T-Systems.(.*?)>>Adreces de correu"

    patterns = [
        regex_pattern4,
        regex_pattern,
        regex_pattern2,
        regex_pattern3,
    ]

    def extract_description(text):
        if pd.isna(text):
            return None
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.DOTALL)
            if match:
                return match.group(1)
        return None  # fallback if nothing matches

    df["Descripción"] = df["Descripción"].apply(extract_description)

    patterns_to_remove = [
        "UNeix AM09"
    ]
    for remove_pattern in patterns_to_remove:
        df["Descripción"] = df["Descripción"].str.replace(remove_pattern, "", regex=True)
    return df


def transform(df) -> pd.DataFrame:
    df['Componente(s)'] = df['Componente(s)'].str.replace(r'^\w+-\d+-', '', regex=True)
    # Extreu WO/INC
    df['Ticket'] = df['Resumen'].str.extract(r'\b(WO\d+|INC\d+)\b(?= - )', expand=False)
    df['Resumen'] = df['Resumen'].str.replace(r'\s*(WO\d+|INC\d+)\s*-\s*', '', regex=True)

    # Elimina frases sense informació
    df = neteja_resumen(df)

    # Extreu missatge
    df = neteja_descripcio(df)

    # Arregla columnes
    df = df.rename(columns={
        "Campo personalizado (Remedy Tiquet Status)": "Remedy Status",
        "Campo personalizado (Due Date Resolució ANS)": "ANS",
        "Campo personalizado (Linked Customer Code 5)": "Remedy ID",
        "Campo personalizado (Customer Reporter)": "Customer Reporter"
        })
    df = df[['Componente(s)', 'Ticket', 'Resumen', 'Descripción', 'Estado', 'Remedy Status', 'Creada',
        'Resuelta', 'ANS', 'Remedy ID',
       'Customer Reporter']]
    df = df.sort_values('Estado').reset_index(drop=True)

    return df