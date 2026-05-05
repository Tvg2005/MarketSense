import json
from bs4 import BeautifulSoup

def gerar_json_do_html_local():
    with open('nfe_page.html', 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    lista_produtos = soup.find('ul', class_='list-group')
    produtos_extraidos = []

    if lista_produtos:
        itens = lista_produtos.find_all('li', class_='list-group-item')
        for item in itens:
            nome_tag = item.find('p', class_='h6')
            if not nome_tag:
                continue
                
            nome = nome_tag.contents[0].strip()
            
            codigo = ""
            small_tag = item.find('small')
            if small_tag:
                codigo = small_tag.text.replace('(Cód:', '').replace(')', '').strip()
            
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
            
        with open('produtos_extraidos.json', 'w', encoding='utf-8') as f:
            json.dump(produtos_extraidos, f, ensure_ascii=False, indent=4)
            
        print(f"Salvos {len(produtos_extraidos)} produtos em produtos_extraidos.json")

if __name__ == "__main__":
    gerar_json_do_html_local()
