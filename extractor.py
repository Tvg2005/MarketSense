from seleniumbase import SB
import time
from bs4 import BeautifulSoup
import os
import json
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

def extrair_dados_nfe(url):
    print("Iniciando o navegador anti-detecção...")
    
    # uc=True é o modo Undetected Chromedriver, que burla o Cloudflare
    # Voltamos para headless=False temporariamente no Windows para não sermos bloqueados
    with SB(uc=True, headless=True) as sb:
        print(f"Acessando a URL: {url}")
        
        # uc_open_with_reconnect é uma função especial do SeleniumBase para lidar com Cloudflare Turnstile
        sb.uc_open_with_reconnect(url, reconnect_time=4)
        
        try:
            # Em alguns casos o Turnstile exige um clique no checkbox, isso tenta clicar
            sb.uc_gui_click_captcha()
        except:
            pass
            
        print("Aguardando o botão de continuar aparecer e liberar...")
        sb.sleep(4)
        
        # O botão na página tem essa classe CSS
        botao_continuar = 'input.btn.btn-primary[type="submit"]'
        
        if sb.is_element_visible(botao_continuar):
            print("Botão 'Continuar consulta' encontrado! Clicando nele...")
            sb.click(botao_continuar)
            print("Aguardando a página da nota fiscal carregar...")
            sb.sleep(6)
        else:
            print("Botão não visível, talvez o Cloudflare ainda esteja validando...")
        
        html = sb.get_page_source()
        
        # Salvamos o HTML apenas se o modo debug estiver ativado
        if os.getenv("LOG_LEVEL", "").lower() == "debug":
            with open("nfe_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Página salva em nfe_page.html com sucesso (Modo Debug)!")

        # Parseando o HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # A SEFAZ-DF não usa uma tabela clássica, eles usam uma lista (ul) com a classe 'list-group'
        lista_produtos = soup.find('ul', class_='list-group')
        
        if lista_produtos:
            print("\nSUCESSO! Acessamos a nota fiscal perfeitamente.")
            
            # Vamos extrair TODOS os produtos e salvar num JSON
            itens = lista_produtos.find_all('li', class_='list-group-item')
            print(f"Encontrados {len(itens)} produtos na nota. Extraindo dados...")
            
            produtos_extraidos = []
            
            for item in itens:
                # O nome do produto está no <p class="h6">
                nome_tag = item.find('p', class_='h6')
                if not nome_tag:
                    continue
                    
                nome = nome_tag.contents[0].strip()
                
                # Pega o código do produto
                codigo = ""
                small_tag = item.find('small')
                if small_tag:
                    codigo = small_tag.text.replace('(Cód:', '').replace(')', '').strip()
                
                # O preço total fica no último span
                spans = item.find_all('span')
                if len(spans) > 0:
                    preco_texto = spans[-1].text.strip()
                    try:
                        preco_float = float(preco_texto.replace('.', '').replace(',', '.'))
                    except:
                        preco_float = 0.0
                else:
                    preco_texto = "0,00"
                    preco_float = 0.0
                    
                produtos_extraidos.append({
                    "nome": nome,
                    "codigo": codigo,
                    "preco_formatado": f"R$ {preco_texto}",
                    "preco_float": preco_float
                })
                
            # Garante que a pasta json_storage existe
            os.makedirs('json_storage', exist_ok=True)
            
            # Salvar os dados de produtos analisados em um arquivo JSON na pasta
            with open('json_storage/produtos_extraidos.json', 'w', encoding='utf-8') as f:
                json.dump(produtos_extraidos, f, ensure_ascii=False, indent=4)
                
            print("[SALVO] Todos os produtos foram salvos em 'json_storage/produtos_extraidos.json'.")
            
            # --- PARTE 2: Acessar a página detalhada ---
            print("Procurando o botão de 'Visualizar NFC-e Detalhada'...")
            
            # O link usa a classe btn-success e contém o texto "Visualizar"
            botao_detalhada = "a.btn-success"
            
            if sb.is_element_present(botao_detalhada):
                # Extrair o link real e navegar, costuma ser mais seguro que clicar
                link_detalhada = sb.get_attribute(botao_detalhada, "href")
                if link_detalhada:
                    print(f"Navegando para a URL detalhada...")
                    sb.uc_open_with_reconnect(link_detalhada, reconnect_time=4)
                    sb.sleep(5)
                    
                    html_detalhada = sb.get_page_source()
                    if os.getenv("LOG_LEVEL", "").lower() == "debug":
                        with open("nfe_detalhada.html", "w", encoding="utf-8") as f:
                            f.write(html_detalhada)
                        print("[SUCESSO] HTML da página detalhada salvo (Modo Debug)!")
                    
                    # --- PARTE 3: Extrair Metadados (Mercado, Data, Valor Total) ---
                    print("Extraindo os metadados da página detalhada...")
                    soup_det = BeautifulSoup(html_detalhada, 'html.parser')
                    dados_completos = {}
                    
                    abas = [
                        ('NFC-e', 'abaNFe'),
                        ('Emitente', 'abaEmitente'),
                        ('Destinatário', 'abaDestinatario'),
                        ('Produtos e Serviços', 'abaProdutosServicos'),
                        ('Totais', 'abaTotais'),
                        ('Transporte', 'abaTransportes'),
                        ('Cobrança', 'abaCobranca'),
                        ('Inf Adic', 'abaInfoAdicionais')
                    ]
                    
                    # Chave de Acesso e Versão (fora das abas)
                    dados_gerais = {}
                    cols_md = soup_det.find_all('div', class_='col-md-10')
                    for col in cols_md:
                        sub = col.find('div', class_='sub-titulo')
                        camp = col.find('div', class_='campo-xml')
                        if sub and camp:
                            chave = sub.text.strip().replace('\n', ' ').replace('  ', '')
                            valor = camp.text.replace('\n', '').replace('-', '').replace('.', '').replace(' ', '').strip()
                            dados_gerais[chave] = valor
                            
                    cols_md2 = soup_det.find_all('div', class_='col-md-2')
                    for col in cols_md2:
                        sub = col.find('div', class_='sub-titulo')
                        camp = col.find('div', class_='campo-xml')
                        if sub and camp:
                            dados_gerais[sub.text.strip().replace('\n', ' ').replace('  ', '')] = camp.text.strip()
                            
                    if dados_gerais:
                        dados_completos['Dados Gerais'] = dados_gerais

                    for nome_aba, id_aba in abas:
                        pane = soup_det.find('div', id=id_aba)
                        if not pane:
                            continue
                            
                        if id_aba == 'abaProdutosServicos':
                            lista_produtos = {}
                            itens = pane.find_all('div', class_='item-accordion')
                            for index, item in enumerate(itens):
                                prod_dados = {}
                                cols = item.find_all('div', class_='col')
                                for col in cols:
                                    sub = col.find('div', class_='sub-titulo')
                                    camp = col.find('div', class_='campo-xml')
                                    if sub and camp:
                                        chave = sub.text.strip().replace('\n', ' ').replace('  ', '')
                                        valor = camp.text.replace('\n', '').replace('  ', '').strip()
                                        if chave:
                                            prod_dados[chave] = valor
                                if prod_dados:
                                    ean_base = prod_dados.get('Código EAN Comercial', '')
                                    if not ean_base or ean_base == 'SEM GTIN' or ean_base.strip() == '':
                                        ean_base = prod_dados.get('Código do produto', f'Item-{index+1}')
                                    
                                    if ean_base in lista_produtos:
                                        # Em vez de criar um novo id (EAN_2), apenas incrementamos a quantidade
                                        lista_produtos[ean_base]['quantidade_registros'] += 1
                                        
                                        # Somar o valor da chave "Quantidade" e "valor_total"
                                        try:
                                            q_atual = float(lista_produtos[ean_base].get('Quantidade', '0').replace(',', '.'))
                                            q_nova = float(prod_dados.get('Quantidade', '0').replace(',', '.'))
                                            lista_produtos[ean_base]['Quantidade'] = f"{(q_atual + q_nova):.4f}".replace('.', ',')
                                            
                                            v_total_atual = float(lista_produtos[ean_base].get('valor_total', lista_produtos[ean_base].get('Valor(R$)', '0')).replace('.', '').replace(',', '.'))
                                            v_novo = float(prod_dados.get('Valor(R$)', '0').replace('.', '').replace(',', '.'))
                                            lista_produtos[ean_base]['valor_total'] = f"{(v_total_atual + v_novo):.2f}".replace('.', ',')
                                        except:
                                            pass
                                    else:
                                        prod_dados['quantidade_registros'] = 1
                                        prod_dados['valor_total'] = prod_dados.get('Valor(R$)', '0')
                                        lista_produtos[ean_base] = prod_dados
                            dados_completos[nome_aba] = lista_produtos
                        else:
                            aba_dados = {}
                            cols = pane.find_all('div', class_='col')
                            for col in cols:
                                sub = col.find('div', class_='sub-titulo')
                                camp = col.find('div', class_='campo-xml')
                                if sub and camp:
                                    chave = sub.text.strip().replace('\n', ' ').replace('  ', '')
                                    valor = camp.text.replace('\n', '').replace('  ', '').strip()
                                    if chave:
                                        aba_dados[chave] = valor
                            dados_completos[nome_aba] = aba_dados
                    
                    # Salva o JSON completo
                    with open('json_storage/nfe_metadados.json', 'w', encoding='utf-8') as f:
                        json.dump(dados_completos, f, ensure_ascii=False, indent=4)
                        
                    print("[SALVO] Metadados da nota salvos em 'json_storage/nfe_metadados.json'!")
                    
            else:
                print("[ERRO] Botão 'Visualizar NFC-e Detalhada' não encontrado na página.")
            
        else:
            print("[ERRO] Produtos não encontrados. A estrutura do HTML não bateu com a esperada.")

if __name__ == "__main__":
    url_teste = os.getenv("NFE_URL")
    if not url_teste:
        print("[ERRO] Variável 'NFE_URL' não encontrada no arquivo .env")
    else:
        extrair_dados_nfe(url_teste)
