import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from seleniumbase import SB
from bs4 import BeautifulSoup
import os
import json
import re
import threading
import numpy as np
from datetime import timedelta
from dotenv import load_dotenv

# Carrega .env do root do projeto
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_root_dir, '.env'), override=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nfe-analyser-secret')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', os.getenv('SECRET_KEY', 'jwt-dev-secret'))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

jwt = JWTManager(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Rastreia sessões ativas para cancelamento em caso de disconnect
_active_extractions = {}  # sid -> {"cancelled": bool}

# Register blueprints
from auth_routes import auth_bp
from me_routes import me_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(me_bp, url_prefix='/me')

BASE_URL_SEFAZ = "https://ww1.receita.fazenda.df.gov.br/DecVisualizador/Nfce/Captcha?Chave="


def montar_url_nfe(entrada):
    """
    Recebe a entrada do usuário (chave numérica, URL completa, ou conteúdo do QR)
    e retorna a URL de consulta padronizada.
    """
    entrada = entrada.strip()

    # Se já é uma URL completa da SEFAZ
    if 'receita.fazenda' in entrada and 'Chave=' in entrada:
        return entrada

    # Se contém parâmetro Chave com 44 dígitos
    chave_match = re.search(r'[Cc]have=(\d{44})', entrada)
    if chave_match:
        return BASE_URL_SEFAZ + chave_match.group(1)

    # Tenta extrair apenas dígitos (chave de acesso = 44 dígitos)
    apenas_digitos = re.sub(r'\D', '', entrada)
    if len(apenas_digitos) == 44:
        return BASE_URL_SEFAZ + apenas_digitos

    return None


def decodificar_qr_com_opencv(image_bytes):
    """
    Usa OpenCV + pyzbar com múltiplas técnicas de pré-processamento
    para maximizar a chance de leitura do QR Code.
    """
    import cv2
    from pyzbar.pyzbar import decode as pyzbar_decode

    # Converter bytes para numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return None

    resultados = []

    # Estratégia 1: Imagem original
    resultados = pyzbar_decode(img)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 2: Converter para grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resultados = pyzbar_decode(gray)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 3: Threshold adaptativo (Gaussian)
    thresh_gauss = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 10
    )
    resultados = pyzbar_decode(thresh_gauss)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 4: Threshold Otsu
    _, thresh_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    resultados = pyzbar_decode(thresh_otsu)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 5: Aumentar contraste (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    resultados = pyzbar_decode(enhanced)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 6: Blur + threshold (remove ruído)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh_blur = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    resultados = pyzbar_decode(thresh_blur)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 7: Resize (upscale 2x) + threshold
    h, w = gray.shape
    upscaled = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    _, thresh_up = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    resultados = pyzbar_decode(thresh_up)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 8: Sharpen + threshold
    kernel_sharpen = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
    _, thresh_sharp = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    resultados = pyzbar_decode(thresh_sharp)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 9: Morphological close (preenche gaps)
    kernel = np.ones((3, 3), np.uint8)
    morph = cv2.morphologyEx(thresh_otsu, cv2.MORPH_CLOSE, kernel)
    resultados = pyzbar_decode(morph)
    if resultados:
        return resultados[0].data.decode('utf-8')

    # Estratégia 10: Inversão (QR branco em fundo escuro)
    inverted = cv2.bitwise_not(thresh_otsu)
    resultados = pyzbar_decode(inverted)
    if resultados:
        return resultados[0].data.decode('utf-8')

    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/decodificar-qr', methods=['POST'])
def decodificar_qr():
    """Decodifica QR code usando OpenCV + pyzbar com múltiplas estratégias."""
    if 'imagem' not in request.files:
        return jsonify({'sucesso': False, 'erro': 'Nenhuma imagem enviada.'}), 400

    arquivo = request.files['imagem']
    image_bytes = arquivo.read()

    try:
        qr_data = decodificar_qr_com_opencv(image_bytes)

        if not qr_data:
            return jsonify({'sucesso': False, 'erro': 'Nenhum QR code encontrado na imagem.'})

        url = montar_url_nfe(qr_data)
        if url:
            # Extrair a chave de 44 dígitos
            chave = re.sub(r'\D', '', qr_data)
            if len(chave) > 44:
                chave = chave[-44:]
            return jsonify({'sucesso': True, 'chave': chave, 'url': url})
        else:
            return jsonify({'sucesso': False, 'erro': f'QR lido mas não contém chave válida: {qr_data[:100]}'})

    except Exception as e:
        return jsonify({'sucesso': False, 'erro': f'Erro ao processar imagem: {str(e)}'}), 500


def emitir_status(sid, mensagem, tipo='info', debug_only=False):
    """Emite uma atualização de status para o cliente via WebSocket."""
    if debug_only and os.getenv("LOG_LEVEL", "").lower() != "debug":
        return
    socketio.emit('status_update', {'mensagem': mensagem, 'tipo': tipo}, to=sid)


def extrair_dados_nfe_async(url, sid, user_id=None):
    """Executa a extração em uma thread separada, emitindo status via socket."""
    def is_cancelled():
        return _active_extractions.get(sid, {}).get("cancelled", False)

    try:
        emitir_status(sid, 'Iniciando navegador...', 'info', debug_only=True)
        emitir_status(sid, 'Conectando ao portal da SEFAZ...', 'info')

        with SB(uc=True, headless=True) as sb:
            emitir_status(sid, 'Acessando nota fiscal...', 'info', debug_only=True)
            sb.uc_open_with_reconnect(url, reconnect_time=4)

            try:
                sb.uc_gui_click_captcha()
            except:
                pass

            emitir_status(sid, 'Validando acesso ao portal...', 'info', debug_only=True)
            sb.sleep(4)

            if is_cancelled():
                return

            botao_continuar = 'input.btn.btn-primary[type="submit"]'

            if sb.is_element_visible(botao_continuar):
                emitir_status(sid, 'Validação concluída', 'success', debug_only=True)
                sb.click(botao_continuar)
                sb.sleep(6)

                if is_cancelled():
                    return
            else:
                emitir_status(sid, 'Aguardando liberação do portal...', 'info', debug_only=True)

            html = sb.get_page_source()

            if os.getenv("LOG_LEVEL", "").lower() == "debug":
                with open("nfe_page.html", "w", encoding="utf-8") as f:
                    f.write(html)

            soup = BeautifulSoup(html, 'html.parser')
            lista_produtos = soup.find('ul', class_='list-group')

            if not lista_produtos:
                emitir_status(sid, 'Não foi possível acessar os dados da nota fiscal. Tente novamente.', 'error')
                socketio.emit('extracao_finalizada', {'sucesso': False}, to=sid)
                return

            emitir_status(sid, 'Nota fiscal localizada. Extraindo produtos...', 'info')

            itens = lista_produtos.find_all('li', class_='list-group-item')
            emitir_status(sid, f'{len(itens)} produtos identificados', 'info', debug_only=True)

            produtos_extraidos = []
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

            if os.getenv("LOG_LEVEL", "").lower() == "debug":
                os.makedirs('json_storage', exist_ok=True)
                with open('json_storage/produtos_extraidos.json', 'w', encoding='utf-8') as f:
                    json.dump(produtos_extraidos, f, ensure_ascii=False, indent=4)

            emitir_status(sid, 'Buscando dados detalhados da nota...', 'info')

            botao_detalhada = "a.btn-success"
            if sb.is_element_present(botao_detalhada):
                link_detalhada = sb.get_attribute(botao_detalhada, "href")
                if link_detalhada:
                    emitir_status(sid, 'Acessando detalhamento completo...', 'info', debug_only=True)
                    sb.uc_open_with_reconnect(link_detalhada, reconnect_time=4)
                    sb.sleep(5)

                    if is_cancelled():
                        return

                    html_detalhada = sb.get_page_source()
                    if os.getenv("LOG_LEVEL", "").lower() == "debug":
                        with open("nfe_detalhada.html", "w", encoding="utf-8") as f:
                            f.write(html_detalhada)

                    emitir_status(sid, 'Processando metadados...', 'info', debug_only=True)
                    soup_det = BeautifulSoup(html_detalhada, 'html.parser')
                    dados_completos = extrair_metadados_detalhados(soup_det)

                    if os.getenv("LOG_LEVEL", "").lower() == "debug":
                        os.makedirs('json_storage', exist_ok=True)
                        with open('json_storage/nfe_metadados.json', 'w', encoding='utf-8') as f:
                            json.dump(dados_completos, f, ensure_ascii=False, indent=4)

                    # Salvar no banco de dados
                    emitir_status(sid, 'Salvando dados...', 'info')
                    try:
                        from db_service import salvar_nota_completa
                        chave = salvar_nota_completa(dados_completos, user_id=user_id)
                        emitir_status(sid, f'Nota {chave[:8]}... persistida', 'success', debug_only=True)
                    except Exception as db_err:
                        emitir_status(sid, f'Falha ao persistir: {str(db_err)}', 'warning', debug_only=True)

                    emitir_status(sid, 'Extração concluída com sucesso', 'success')
                    socketio.emit('extracao_finalizada', {
                        'sucesso': True,
                        'produtos': produtos_extraidos,
                        'metadados': dados_completos
                    }, to=sid)
                else:
                    emitir_status(sid, 'Dados parciais extraídos. Detalhamento indisponível.', 'warning')
                    socketio.emit('extracao_finalizada', {
                        'sucesso': True,
                        'produtos': produtos_extraidos,
                        'metadados': {}
                    }, to=sid)
            else:
                emitir_status(sid, 'Dados parciais extraídos. Detalhamento indisponível.', 'warning')
                socketio.emit('extracao_finalizada', {
                    'sucesso': True,
                    'produtos': produtos_extraidos,
                    'metadados': {}
                }, to=sid)

    except Exception as e:
        emitir_status(sid, f'Erro na extração. Tente novamente.', 'error')
        emitir_status(sid, f'Detalhe: {str(e)}', 'error', debug_only=True)
        socketio.emit('extracao_finalizada', {'sucesso': False}, to=sid)
    finally:
        _active_extractions.pop(sid, None)


def extrair_metadados_detalhados(soup_det):
    """Extrai todos os metadados da página detalhada da NFC-e."""
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
                        lista_produtos[ean_base]['quantidade_registros'] += 1
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

    return dados_completos


@socketio.on('iniciar_extracao')
def handle_extracao(data):
    entrada = data.get('chave', '').strip()
    token = data.get('token', '')

    if not entrada:
        emit('status_update', {'mensagem': 'Chave de acesso não fornecida.', 'tipo': 'error'})
        return

    url = montar_url_nfe(entrada)
    if not url:
        emit('status_update', {'mensagem': 'Chave inválida. Informe os 44 dígitos da nota fiscal.', 'tipo': 'error'})
        return

    # Extrair user_id do JWT se fornecido
    user_id = None
    if token:
        try:
            import jwt as pyjwt
            clean_token = token.replace('Bearer ', '') if token.startswith('Bearer ') else token
            secret = app.config.get('JWT_SECRET_KEY', 'jwt-dev-secret')
            decoded = pyjwt.decode(clean_token, secret, algorithms=["HS256"])
            user_id = decoded.get('sub')
        except Exception as e:
            if os.getenv("LOG_LEVEL", "").lower() == "debug":
                print(f"[WARN] Falha ao decodificar token: {e}")
    else:
        if os.getenv("LOG_LEVEL", "").lower() == "debug":
            print("[WARN] Nenhum token recebido no socket emit")

    sid = request.sid
    _active_extractions[sid] = {"cancelled": False}
    emit('status_update', {'mensagem': 'Extração iniciada...', 'tipo': 'info'})

    thread = threading.Thread(target=extrair_dados_nfe_async, args=(url, sid, user_id))
    thread.daemon = True
    thread.start()


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in _active_extractions:
        _active_extractions[sid]["cancelled"] = True


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
