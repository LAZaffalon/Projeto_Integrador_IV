#Importar as bibliotecas para a aplicação
import streamlit as st
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt

#Carregar os datasets tratados para executar a análise descritiva
def carregar_dataset(caminho):
    df = pd.read_csv(caminho)
    return df

df_2ano = carregar_dataset("dataset_clear/turma_2ano.csv")

#Preparar as visualizações

#Criar a interface no Streamlit

st.title("Meu Primeiro Aplicativo no Ar!")
st.write("Esta é uma alteração feita diretamente no VSCode")
st.markdown("## Análise de dados da Plataforma Educacional")
nivel_numerico = df_2ano["nivel_numerico"].value_counts().sort_index()
st.bar_chart(nivel_numerico)

if st.button("Clique aqui para testar"):
    st.success("Parabéns! O seu código funcionou de primeira!")