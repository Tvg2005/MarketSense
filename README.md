# NFE Analyser

O **NFE Analyser** é um script de automação em Python projetado para extrair e estruturar dados de Notas Fiscais de Consumidor Eletrônica (NFC-e), especificamente do portal da SEFAZ-DF. Ele acessa a URL pública da nota, contorna as proteções antibot (Cloudflare Turnstile) e processa os dados da página detalhada para gerar um arquivo JSON estruturado e de fácil análise.

## 🚀 Funcionalidades

- **Bypass de Cloudflare**: Utiliza a biblioteca `seleniumbase` no modo *undetected* (`uc=True`) para contornar verificações automatizadas de robôs e captchas do Turnstile.
- **Extração Completa**: Navega até a aba detalhada da NFC-e e realiza o parse de todos os metadados (Emitente, Destinatário, Produtos e Serviços, Totais, Transporte, etc).
- **Consolidação de Produtos**: Agrupa itens duplicados ou comprados em múltiplas quantidades na mesma nota. Ele preserva o valor unitário (`Valor(R$)`), calcula o total (`valor_total`), soma as quantidades (`Quantidade`) e exibe o número de ocorrências na nota (`quantidade_registros`).
- **Headless Mode**: A automação roda em segundo plano sem a necessidade de abrir fisicamente a interface do navegador durante as execuções.
- **Log Debug**: Permite habilitar um modo de depuração via variável de ambiente para salvar o HTML da página carregada.

## 🛠️ Tecnologias Utilizadas

- [Python 3.x](https://www.python.org/)
- [SeleniumBase](https://seleniumbase.io/) (Automação e bypass de detecção)
- [BeautifulSoup 4](https://beautiful-soup-4.readthedocs.io/) (Parsing do HTML extraído)
- [python-dotenv](https://saurabh-kumar.com/python-dotenv/) (Gerenciamento de variáveis de ambiente)

## 📦 Instalação

1. Clone o repositório ou baixe o código fonte:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd NFE_Analyser
   ```

2. Crie e ative um ambiente virtual (recomendado):
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instale as dependências necessárias:
   ```bash
   pip install seleniumbase beautifulsoup4 python-dotenv
   ```

4. Crie o arquivo de configuração de ambiente `.env` na raiz do projeto contendo as seguintes variáveis:
   ```env
   NFE_URL=https://ww1.receita.fazenda.df.gov.br/DecVisualizador/Nfce/Captcha?Chave=SUA_CHAVE_AQUI
   LOG_LEVEL=debug # (Opcional) Define se vai salvar os arquivos HTML das páginas acessadas localmente
   ```

## ▶️ Uso

Para iniciar o robô de extração, basta rodar o script principal:

```bash
python extractor.py
```

### O que acontece em seguida?
1. O robô vai abrir o portal e passar pela validação da nota.
2. Vai extrair todos os itens e depois clicar em "Visualizar NFC-e Detalhada".
3. Será gerado um arquivo principal na pasta `json_storage/` contendo todas as abas agrupadas (incluindo Emitente, Produtos, etc).

## 🗂️ Estrutura do JSON Gerado
O arquivo `json_storage/nfe_metadados.json` terá uma estrutura contendo todas as guias da nota, veja um exemplo do agrupamento de produtos:

```json
"Produtos e Serviços": {
    "7891234567890": {
        "Descrição": "PRODUTO EXEMPLO",
        "Quantidade": "3.0000",
        "Unidade Comercial": "UN",
        "Valor(R$)": "10,50",
        "...": "...",
        "quantidade_registros": 3,
        "valor_total": "31,50"
    }
}
```

## ⚠️ Observações
- Devido às constantes atualizações de segurança e layout da SEFAZ, pode ser necessário ajustar os seletores ou tempos de espera (`sb.sleep()`) no futuro.
