import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import pandas as pd
import editacodigo_whats
import time

# Caminho absoluto para o arquivo CSV
csv_path = os.path.abspath('contatos_atendidos.csv')

# Função para carregar contatos atendidos
def carregar_contatos_atendidos(csv_path):
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, index_col=0)
            if 'nome_contato' not in df.columns:
                print("Coluna 'nome_contato' não encontrada no CSV. Inicializando DataFrame vazio.")
                df = pd.DataFrame(columns=['nome_contato'])
        except pd.errors.EmptyDataError:
            print("Arquivo CSV está vazio. Inicializando DataFrame vazio.")
            df = pd.DataFrame(columns=['nome_contato'])
    else:
        print("Arquivo CSV não encontrado. Inicializando DataFrame vazio.")
        df = pd.DataFrame(columns=['nome_contato'])
    return df

# Carregar contatos atendidos
contatos_atendidos = carregar_contatos_atendidos(csv_path)

# Carregar navegador
driver = editacodigo_whats.carregar_pagina_whatsapp('zap/sessao', 'https://web.whatsapp.com/')
time.sleep(8)  # Aguardar o carregamento inicial

# Função para verificar se o contato já foi atendido
def contato_atendido(nome_contato):
    return nome_contato in contatos_atendidos['nome_contato'].values

# Função para adicionar contato atendido
def adicionar_contato_atendido(nome_contato):
    global contatos_atendidos
    novo_contato = pd.DataFrame({'nome_contato': [nome_contato]})
    contatos_atendidos = pd.concat([contatos_atendidos, novo_contato], ignore_index=True)
    try:
        contatos_atendidos.to_csv(csv_path, index=False)
    except PermissionError as e:
        print(f"Erro de permissão ao salvar o arquivo: {e}")

# Saindo do filtro
def saindo_filtro():
    try:
        driver.find_element(By.XPATH, '//*[@id="side"]/div[1]/div/button/div/span').click()
    except Exception as e:
        print(f'Erro ao sair do filtro: {e}')

# Entrar no filtro não lido
def nao_lidas():
    try:
        driver.find_element(By.XPATH, '//*[@id="side"]/div[1]/div/button/div/span').click()
        driver.find_element(By.XPATH, '//*[@id="app"]/div/span[5]/div/ul/div/li[1]/div/div[2]').click()
    except Exception as e:
        print(f'Erro ao acessar mensagens não lidas: {e}')

# Função limpar chat
def clean_chat():
    try:
        driver.find_element(By.XPATH, '//*[@id="main"]/header/div[3]/div/div[2]/div/div/span').click()
        driver.find_element(By.XPATH, '//*[@id="app"]/div/span[5]/div/ul/div/div/li[6]/div').click()
        driver.find_element(By.XPATH, '//*[@id="app"]/div/span[2]/div/div/div/div/div/div/div[3]/div/button[2]/div/div').click()
    except Exception as e:
        print(f'Erro ao limpar chat: {e}')    

# Enviar Mensagem
def enviar_mensagem(message):
    attempts = 1
    while attempts > 0:
        try:
            caixa_mensagem = driver.find_element(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[1]/p')
            caixa_mensagem.send_keys(message)
            time.sleep(1)
            caixa_mensagem.send_keys(Keys.ENTER)
            time.sleep(1)  # Aguardar um breve momento após enviar a mensagem
            break
        except NoSuchElementException as e:
            print(f"Erro ao encontrar a caixa de mensagem: {e}")
            break
        except StaleElementReferenceException as e:
            print(f"Erro de referência obsoleta ao enviar mensagem: {e}")
            attempts -= 1
            time.sleep(1)

# Loop principal
while True:
    try:
        # Esperar a notificação aparecer
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pane-side"]/div/div/div/div[1]/div/div/div/div[2]/div[2]/div[2]/span[1]/div/span')))

        nao_lidas()
        time.sleep(2)
        # Obter todas as notificações
        for i in range(1, 51):
            xpath = f'//*[@id="pane-side"]/div/div/div/div[{i}]/div/div/div/div[2]/div[2]/div[2]/span[1]/div/span'
            notificacoes = driver.find_elements(By.XPATH, xpath)

            # Iterar sobre todas as notificações e responder
            for notificacao in notificacoes:
                try:
                    notificacao.click()
                    time.sleep(2)  # Aguardar um breve momento após clicar na notificação

                    # Extrair o nome do contato
                    nome_contato = driver.find_element(By.XPATH, '//*[@id="main"]/header/div[2]/div/div/div/span').text
                    print(f'{len(notificacoes)} Notificação')
                    print("Nome do contato:", nome_contato)

                    # Verificar se o contato já foi atendido
                    if contato_atendido(nome_contato):
                        print(f"O contato {nome_contato} já foi atendido. Ignorando.")
                        driver.find_element(By.XPATH, '//body').send_keys(Keys.ESCAPE)
                        continue

                    # Enviar mensagem automática com o nome do contato
                    mensagem = f"Olá aqui é da ADTECH, bem vindo {nome_contato}, esta é uma mensagem automática."
                    mensagem2 = '''Deseja conversar com algum de nossos profissionais?
                                1 - Advogado(a)\n
                                2 - Psicólogo(a)\n
                                3 - Assistente Social 
                                (envie apenas o número por favor)
'''
                    enviar_mensagem(mensagem)
                    enviar_mensagem(mensagem2)

                    # Pausa para permitir que o usuário responda
                    time.sleep(40)

                    # Variáveis de controle
                    elemento_encontrado = False
                    resposta_texto = ""

                    # Tente localizar o elemento container principal variando o índice
                    for r in range(1, 40):
                        try:
                            # Localize o contêiner principal com o índice atual
                            container = driver.find_element(By.XPATH, f'//*[@id="main"]/div[3]/div/div[2]/div[3]/div[{r}]/div/div')

                            # Tente localizar o span que contém o texto dentro do contêiner principal
                            resposta_elemento = container.find_element(By.XPATH, './/span[contains(@class, "selectable-text copyable-text")]')

                            # Extraia o texto do elemento
                            resposta_texto = resposta_elemento.text
                            
                            # Se encontramos o texto, podemos sair do loop
                            if resposta_texto in ['1', '2', '3']:
                                elemento_encontrado = True
                                break
                        except NoSuchElementException:
                            continue
                        except StaleElementReferenceException:
                            continue
                        time.sleep(0.5)  # Pausa curta para evitar loops muito rápidos

                    time.sleep(5)

                    # Se o elemento foi encontrado, processa a resposta
                    if elemento_encontrado:
                        if resposta_texto == '1':
                            resposta_1 = f'''
                            Segue o contato do nosso Advogado
                            Clique no número e fale diretamente com o Dr. XXXXXXXXXX -> 83-99620-8929
                            Volte sempre {nome_contato}.
'''    
                            enviar_mensagem(resposta_1)

                        elif resposta_texto == '2':
                            resposta_2 = f'''
                            Segue o contato da nossa Psicóloga
                            Clique no número e fale diretamente com o Dra XXXXXXXXX -> 83-99620-8929
                            Volte sempre {nome_contato}.
'''
                            enviar_mensagem(resposta_2)

                        elif resposta_texto == '3':
                            resposta_3 = f'''
                            Segue o contato do nosso Assistente Social
                            Clique no número e fale diretamente com a Sra XXXXXXXXX -> 83-99620-8929
                            Volte sempre {nome_contato}.
'''    
                            enviar_mensagem(resposta_3)

                        # Adicionar contato à lista de atendidos
                        adicionar_contato_atendido(nome_contato)

                    else:
                        mensagem_invalida = f"Aguardando uma opção válida {nome_contato}. Por favor, envie apenas o número 1, 2 ou 3."
                        enviar_mensagem(mensagem_invalida)

                    driver.find_element(By.XPATH, '//body').send_keys(Keys.ESCAPE)
                    time.sleep(1)


                except StaleElementReferenceException:
                    print("Stale element reference ao interagir com a notificação")
                    continue
                except NoSuchElementException as e:
                    print(f"Erro ao processar notificação: {e}")
                    continue

            # tempo para buscar nova notificação
            time.sleep(2)

    except TimeoutException:
        print("Timeout esperando por notificações")
        time.sleep(5)
        try:
            saindo_filtro()
            time.sleep(30)
            nao_lidas()
        except Exception as e:
            print(f'Não chegou notificações: {e}')
        continue

