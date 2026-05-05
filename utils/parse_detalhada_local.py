import json
import os
from bs4 import BeautifulSoup

def gerar_json_metadados_local():
    with open('nfe_detalhada.html', 'r', encoding='utf-8') as f:
        html = f.read()

    soup_det = BeautifulSoup(html, 'html.parser')
    dados_completos = {}
    
    # Mapeamento dos IDs das abas no HTML para o nome amigável
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
    
    # A Chave de Acesso e a Versão ficam fora das abas (no topo)
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

    # Agora iteramos por cada aba principal
    for nome_aba, id_aba in abas:
        pane = soup_det.find('div', id=id_aba)
        if not pane:
            continue
            
        # Se for a aba de produtos, tem que ser uma lista porque há vários itens (produtos)
        if id_aba == 'abaProdutosServicos':
            lista_produtos = {}
            # Cada produto fica dentro de um accordion próprio
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
                    # Usa o EAN como chave. Se estiver vazio ou "SEM GTIN", usa o código interno
                    ean_base = prod_dados.get('Código EAN Comercial', '')
                    if not ean_base or ean_base == 'SEM GTIN' or ean_base.strip() == '':
                        ean_base = prod_dados.get('Código do produto', f'Item-{index+1}')
                    
                    if ean_base in lista_produtos:
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
            # Para as outras abas (como Emitente), é apenas um objeto único com os campos
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

    os.makedirs('json_storage', exist_ok=True)
    with open('json_storage/nfe_metadados.json', 'w', encoding='utf-8') as f:
        json.dump(dados_completos, f, ensure_ascii=False, indent=4)
        
    print("Sucesso! JSON estruturado por abas e com todos os produtos salvo.")
    print(f"Total de produtos capturados na aba detalhada: {len(dados_completos.get('Produtos e Serviços', []))}")

if __name__ == "__main__":
    gerar_json_metadados_local()
