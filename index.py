from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
from bs4 import BeautifulSoup
import pandas as pd
import os

start_time = time.time()

# Diretório com os arquivos CSV
diretorio = './'
# Apagar todos os arquivos CSV da pasta
print('apagando')
for arquivo in os.listdir(diretorio):
    if arquivo.endswith('.csv'):
        os.remove(os.path.join(diretorio, arquivo))

# Inicializa o driver do Chrome
driver = webdriver.Chrome()

# URL da página que será acessada
url = "https://www.fazenda.sp.gov.br/RepasseConsulta/Consulta/repasse.aspx"
driver.get(url)

# Espera até que o seletor de ano esteja disponível
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_ddlAno")))

# Seleciona o dropdown de ano
select_element_ano = Select(driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_ddlAno"))

# Pega todas as opções de ano disponíveis
options_ano = [option.text for option in select_element_ano.options]

# Itera sobre os anos, ignorando o '---'
for ano in options_ano:
    if ano != '---':
        print(f"Baixando dados para o ano {ano}")
        
        # Reencontra o seletor de ano e seleciona o ano atual
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_ddlAno")))
        select_element_ano = Select(driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_ddlAno"))
        select_element_ano.select_by_visible_text(ano)
        
        # Reencontra o seletor de município e obtém as opções
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_ddlMuni")))
        select_element_municipio = Select(driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_ddlMuni"))
        options_municipio = [option.text for option in select_element_municipio.options]
        
        # Itera sobre os municípios, ignorando o '---'
        for option_text_municipio in options_municipio:
            if option_text_municipio != '---':
                try:
                    # Reencontra o seletor de município e seleciona o município atual
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_ddlMuni")))
                    select_element_municipio = Select(driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_ddlMuni"))
                    select_element_municipio.select_by_visible_text(option_text_municipio)
                    
                    # Encontra e clica no botão de confirmar
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_btnConfirmar")))
                    button = driver.find_element(By.CSS_SELECTOR, "#ConteudoPagina_btnConfirmar")
                    button.click()
                    
                    # Espera até que a tabela esteja presente na página
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#ConteudoPagina_gdvRepasse")))
                        html = driver.page_source
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        tabela = soup.find('table', {'id': 'ConteudoPagina_gdvRepasse'})
                        
                        # Verifica se a tabela foi encontrada
                        if tabela:
                            dados_tabela = []
                            linhas = tabela.find_all('tr')
                            for linha in linhas:
                                colunas = linha.find_all(['th', 'td'])
                                colunas_texto = [coluna.get_text(strip=True) for coluna in colunas]
                                dados_tabela.append(colunas_texto)

                            # Converte os dados da tabela em um DataFrame do Pandas
                            df = pd.DataFrame(dados_tabela[1:], columns=dados_tabela[0])
                            df = df.assign(Municipio=option_text_municipio)
                            
                            # Salva o DataFrame em um arquivo CSV
                            df.to_csv(f"{ano}_{option_text_municipio}.csv", index=False)
                        else:
                            print(f"Tabela não encontrada para {ano} - {option_text_municipio}")
                            
                    except TimeoutException:
                        print(f"Timeout: Tabela não encontrada para {ano} - {option_text_municipio}")

                except StaleElementReferenceException:
                    # Continua no próximo município em caso de erro StaleElementReferenceException
                    continue

# Fecha o navegador
driver.quit()

# Lista para armazenar os DataFrames
dataframes = []

# Ler todos os arquivos CSV da pasta e adicionar à lista
print('lendo')
for arquivo in os.listdir(diretorio):
    if arquivo.endswith('.csv'):
        caminho_arquivo = os.path.join(diretorio, arquivo)
        df = pd.read_csv(caminho_arquivo)
        dataframes.append(df)

# Apagar todos os arquivos CSV da pasta
print('apagando')
for arquivo in os.listdir(diretorio):
    if arquivo.endswith('.csv'):
        os.remove(os.path.join(diretorio, arquivo))

# Unir todos os DataFrames em um só
print('Unir todos os DataFrames')
df_unido = pd.concat(dataframes, ignore_index=True)

# Salvar o DataFrame unido em um novo arquivo CSV
print('Salvar o DataFrame unido em um novo arquivo CSV')
caminho_saida = os.path.join(diretorio, 'dados.csv')
df_unido.to_csv(caminho_saida, index=False)

print('Processo concluído. Todos os CSVs foram unidos e salvos como dados.csv.')

end_time = time.time()  
elapsed_time = end_time - start_time
print(f"Tempo total de execução: {elapsed_time:.2f} segundos")
