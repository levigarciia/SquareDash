# SquareBot

SquareBot é um bot de Discord focado na gestão de aplicações hospedadas na [Square Cloud](https://squarecloud.app/). Ele combina comandos simples e interfaces interativas para facilitar o deploy, o controle das aplicações e o acompanhamento de pagamentos.

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

Tudo é pensado para ser simples: basta configurar os tokens, usar os comandos de barra e acompanhar as respostas enviadas pelo próprio Discord.

## Instalação

1. Clone este repositório e instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Defina a variável de ambiente `BOT_TOKEN` com o token do seu bot no Discord.
3. Execute o bot:
   ```bash
   python src/SquareBot.py
   ```

## Configuração Inicial

Utilize o comando `/configurar` dentro do Discord para registrar:

- **Token da Square Cloud**: necessário para controlar suas aplicações.
- **Token do Mercado Pago** e **link do ZIP** (opcionais): habilitam o comando `/pagar` e o deploy automático após a confirmação do pagamento.
- **Preço** (opcional): valor cobrado no Mercado Pago.
- **ID do administrador** (opcional): usuário que receberá alertas quando algo der errado.

As informações ficam salvas em `config.json`, arquivo listado no `.gitignore` para evitar o vazamento de dados sensíveis.

## Funcionamento

Após configurado, basta utilizar:

- `/dashboard` para abrir a tela de gestão das aplicações.
- `/pagar` para gerar um link de pagamento (se configurado).

O bot também verifica periodicamente o status das aplicações e notifica o administrador caso alguma pare de funcionar. Tudo acontece de forma automática, mantendo sua experiência prática e sem complicações.

## Estrutura do Projeto

- `src/SquareBot.py` &mdash; ponto de entrada do bot.
- `src/cogs/` &mdash; conjunto de *cogs* que implementam os comandos:
  - `gestao.py` &mdash; dashboard de aplicações e controles de deploy.
  - `config.py` &mdash; comandos para definição de tokens e opções.
  - `pagamento.py` &mdash; integração com Mercado Pago.
  - `notificacao.py` &mdash; envio de avisos para o administrador.
- `squarecloud.config` &mdash; arquivo de configuração utilizado pela Square Cloud para hospedar o bot.

## Contribuições

Sinta-se à vontade para abrir issues ou pull requests com sugestões e melhorias. Este projeto tem como objetivo demonstrar como é simples integrar a Square Cloud a bots de Discord usando Python.

