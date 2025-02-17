# Projeto GeoAnsata GDQM
  Plataforma para análises de dados e criação de imagens para dados de mineração.
  O sistema é capaz de receber arquivos excel e csv podendo realizar modificações neles, gerar gráficos, tabelas analíticas e pdfs com o histórico de processos realizados.
  Os gráficos, tabelas e arquivos modificados podem ser baixados pelo sistema.
  Outra forma de execução é pela Seção Gráficos recomendados, em que é possível realizar análises pré-definidas sobre os dados e gerar relatórios próprios por etapa

## Como executar localmente
  - Crie um environment a partir de environment.yml (utilizei conda mas outros também devem funcionar)
  - Execute "python app.py"
## Como executar no HostGator
  - Acessando o Terminal no servidor hostgator ele está localizado na pasta /root/GDQM/GeoAnsata-GDQM
  - Pode ser executado a partir de um processo já criado com o comando: sudo systemctl restart meuapp
  - Para checar o status do programa é possível usar o comando: sudo systemctl status meuapp
  - Para atualizar o código no Hostgator simplemente acesse a pasta e utilize os comandos do git e em seguida reinicie o processo
  Pode ser acessado em http://162.240.111.242:8080/ ou https://geoansata.com.br/gdqm
## TODO
  - Atualização dos Visuais
  - Adição de um mapa de fundo no envio de imagens com arquivo kml em Gráficos Recomendados/Collar
  - Corrigir o download de tabelas geradas que não está funcionando
  - Atualizar a seção de geração de gráficos em Análise Exploratória (adicionar mais opções de gráfico por exemplo)
  - Remover ícone da barra lateral na tela de login
## Bugs Conhecidos
  - Erro ao trocar o arquivo selecionado a partir de gráficos gerados na seção Gráficos Recomendados
  - Em Limpeza, é necesário uma rechecagem na limpeza utilizando filtros
