from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
from bs4 import BeautifulSoup
import pandas as pd
import os

def deletar_todos_csv(diretorio):
    """Deleta todos os arquivos CSV do diretório."""
    for arquivo in os.listdir(diretorio):
        if arquivo.endswith('.csv'):
            os.remove(os.path.join(diretorio, arquivo))

def selecionar_ano(ano):
    """Seleciona o ano no dropdown."""
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_ddlAno")))
    elemento_seletor_ano = Select(driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_ddlAno"))
    elemento_seletor_ano.select_by_visible_text(ano)

def obter_municipios():
    """Obtém a lista de municípios disponíveis no dropdown."""
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_ddlMuni")))
    elemento_seletor_municipio = Select(driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_ddlMuni"))
    return [option.text for option in elemento_seletor_municipio.options]

def selecionar_municipio(municipio):
    """Seleciona um município no dropdown."""
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_ddlMuni")))
    elemento_seletor_municipio = Select(driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_ddlMuni"))
    elemento_seletor_municipio.select_by_visible_text(municipio)

def clicar_botao_confirmar():
    """Clica no botão confirmar."""
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_btnConfirmar")))
    botao = driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_btnConfirmar")
    botao.click()

def esperar_tabela():
    """Espera até que a tabela esteja disponível na página."""
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_gdvRepasse")))
        return True
    except TimeoutException:
        return False

def extrair_dados_tabela():
    """Extrai os dados da tabela e retorna um DataFrame."""
    html = driver.page_source
    sopa = BeautifulSoup(html, 'html.parser')
    tabela = sopa.find('table', {'id': 'ConteudoPagina_gdvRepasse'})
    
    if tabela:
        dados_tabela = []
        linhas = tabela.find_all('tr')
        for linha in linhas:
            colunas = linha.find_all(['th', 'td'])
            colunas_texto = [coluna.get_text(strip=True) for coluna in colunas]
            dados_tabela.append(colunas_texto)
        
        df = pd.DataFrame(dados_tabela[1:], columns=dados_tabela[0])
        return df
    else:
        return None

def salvar_para_csv(df, ano, municipio):
    """Salva o DataFrame em um arquivo CSV."""
    df = df.assign(Municipio=municipio)
    df["Ano"] = ano
    df.to_csv(f"{ano}_{municipio}.csv", index=False)

def ler_dados():
    """Função principal que controla o processo de leitura dos dados."""
    for ano in opcoes_ano:
        if ano != '---':
            print(f"Baixando dados para o ano {ano}")
            
            # Seleciona o ano
            selecionar_ano(ano)
            
            # Obtém a lista de municípios
            opcoes_municipio = obter_municipios()
            
            # Itera sobre os municípios
            for opcao_municipio in opcoes_municipio:
                if opcao_municipio != '---':
                    try:
                        # Seleciona o município e clica no botão confirmar
                        selecionar_municipio(opcao_municipio)
                        clicar_botao_confirmar()
                        
                        # Espera a tabela e extrai os dados, se disponível
                        if esperar_tabela():
                            df = extrair_dados_tabela()
                            if df is not None:
                                salvar_para_csv(df, ano, opcao_municipio)
                            else:
                                print(f"Tabela não encontrada para {ano} - {opcao_municipio}")
                        else:
                            print(f"Timeout: Tabela não encontrada para {ano} - {opcao_municipio}")
                    
                    except StaleElementReferenceException:
                        continue

def formatar_csv(dataframes, diretorio):
    """Formata e unifica todos os arquivos CSV."""
    for arquivo in os.listdir(diretorio):
        if arquivo.endswith('.csv'):
            caminho_arquivo = os.path.join(diretorio, arquivo)
            df = pd.read_csv(caminho_arquivo)
            dataframes.append(df)

    # Apaga todos os arquivos CSV do diretório
    deletar_todos_csv(diretorio)

    # Unifica todos os DataFrames em um só
    df_unido = pd.concat(dataframes, ignore_index=True)

    # Salva o DataFrame unificado em um novo arquivo CSV
    caminho_saida = os.path.join(diretorio, 'dados.csv')
    df_unido.to_csv(caminho_saida, index=False)

if __name__ == "__main__":
    start_time = time.time()
    
    # Diretório com os arquivos CSV
    diretorio = './'
    
    # Apaga todos os arquivos CSV do diretório
    deletar_todos_csv(diretorio)

    # Inicializa o driver do Chrome
    driver = webdriver.Chrome()

    # URL da página que será acessada
    url = "https://www.fazenda.sp.gov.br/RepasseConsulta/Consulta/repasse.aspx"
    driver.get(url)

    # Espera até que o seletor de ano esteja disponível
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_ddlAno")))

    # Seleciona o dropdown de ano
    seletor_ano = Select(driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_ddlAno"))

    # Obtém todas as opções de ano disponíveis
    opcoes_ano = [option.text for option in seletor_ano.options]

    # Lê os dados dos municípios
    ler_dados()

    # Fecha o navegador
    driver.quit()

    # Lista para armazenar os DataFrames
    dataframes = []

    # Lê todos os arquivos CSV da pasta e adiciona à lista
    formatar_csv(dataframes, diretorio)

    # Calcula o tempo total de execução
    end_time = time.time()  
    elapsed_time = end_time - start_time
    print(f"Tempo total de execução: {elapsed_time:.2f} segundos")
