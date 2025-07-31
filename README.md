# SquareBot

![Banner da Square Cloud](src/assets/squarecloudbanner.png)

SquareBot é um bot de Discord focado na gestão de aplicações hospedadas na [Square Cloud](https://squarecloud.app/). Além de comandos de deploy e monitoramento, ele integra cobrança via Mercado Pago para automatizar o gerenciamento de suas aplicações.

## Recursos Principais

- **Dashboard Interativo** (`/dashboard`)
  - Lista todas as suas aplicações da Square Cloud.
  - Possibilita iniciar, reiniciar, parar ou excluir cada aplicação com botões.
  - Permite realizar deploy enviando o link de um arquivo ZIP.
- **Configuração Rápida** (`/configurar`)
  - Modal para inserir o token da Square Cloud e, opcionalmente, dados do Mercado Pago e ID do administrador.
  - Salva todas as informações em `config.json` para uso posterior.
- **Pagamentos Integrados** (`/pagar`)
  - Gera um link de pagamento via Mercado Pago.
  - Ao ser aprovado, o bot faz o deploy automático do ZIP configurado e envia confirmação ao usuário.
- **Notificações de Erro**
  - Monitora periodicamente o status das aplicações.
  - Caso alguma pare de responder, envia mensagem direta ao administrador definido.

## Pré-requisitos

- Python 3.10 ou superior;
- Conta no Discord e um bot criado;
- Conta na [Square Cloud](https://squarecloud.app/).

## Execução Local

1. Clone este repositório e crie um ambiente virtual (opcional, mas recomendado):
   ```bash
   git clone https://github.com/seu-usuario/SquareDash.git
   cd SquareDash
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Crie um arquivo `.env` contendo:
   ```env
   BOT_TOKEN=<seu-token-do-discord>
   ```
3. Inicie o bot:
   ```bash
   python src/SquareBot.py
   ```

## Configuração Inicial pelo Discord

Dentro do seu servidor, utilize `/configurar` para registrar:

- **Token da Square Cloud** (obrigatório);
- **Token do Mercado Pago** e **link do ZIP** (opcionais);
- **Preço** e **ID do administrador** (opcionais).

Todas as informações ficam salvas em `config.json`, que está no `.gitignore` para evitar vazamento de dados sensíveis.

## Hospedagem na Square Cloud

1. Acesse o painel da [Square Cloud](https://squarecloud.app/) e crie uma nova aplicação do tipo **Bot**.
2. Certifique-se de que o arquivo `squarecloud.config` esteja na raiz do projeto. Ele define o ponto de entrada (`MAIN`), memória e outras opções.
3. Compacte o repositório em um ZIP contendo todos os arquivos (inclusive `requirements.txt` e `squarecloud.config`).
4. Envie esse ZIP na aba de deploy da sua aplicação e aguarde o processamento.
5. No painel de variáveis da Square Cloud, defina `BOT_TOKEN` com o token do seu bot do Discord e quaisquer outras variáveis que desejar.
6. Clique em **Iniciar** para que o SquareBot fique online. Os logs podem ser acompanhados diretamente no painel.

Após o deploy inicial, você pode usar o próprio SquareBot para realizar novos deploys e controlar suas aplicações via Discord.

## Estrutura do Projeto

- `src/SquareBot.py` &mdash; ponto de entrada do bot.
- `src/cogs/` &mdash; conjunto de *cogs* que implementam os comandos:
  - `gestao.py` &mdash; dashboard de aplicações e controles de deploy.
  - `config.py` &mdash; comandos para definição de tokens e opções.
  - `pagamento.py` &mdash; integração com Mercado Pago.
  - `notificacao.py` &mdash; envio de avisos para o administrador.
- `squarecloud.config` &mdash; arquivo de configuração utilizado pela Square Cloud para hospedar o bot.

## Contribuições

Sinta-se à vontade para abrir issues ou pull requests com sugestões e melhorias. Este projeto demonstra como integrar a Square Cloud a bots de Discord utilizando Python.
