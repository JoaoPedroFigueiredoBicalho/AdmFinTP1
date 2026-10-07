# InvestCompare

Aplicação desktop em Python para comparar investimentos financeiros de forma visual e prática. O projeto calcula indicadores como VPL, ganho nominal, retorno percentual e payback, além de gerar gráfico comparativo e relatório em PDF.

## Objetivo

O sistema foi desenvolvido para auxiliar na análise de alternativas de investimento, permitindo que o usuário:

- cadastre múltiplos investimentos;
- informe investimento inicial, taxa de desconto e fluxo de caixa;
- compare as opções pelo critério do VPL;
- visualize os resultados em uma tabela e em gráfico;
- gere um relatório em PDF para documentação ou apresentação.

## Funcionalidades

- Cadastro de investimentos com nome, valor inicial, taxa e períodos;
- Cálculo de:
  - Valor Presente Líquido (VPL);
  - ganho nominal;
  - retorno percentual;
  - payback simples;
- Comparação automática da melhor alternativa;
- Exibição dos dados em tabela dentro da interface;
- Gráfico comparativo do VPL dos investimentos;
- Exportação do resultado em arquivo PDF.

## Tecnologias

- Python 3
- Tkinter para interface gráfica
- Matplotlib para gráficos
- ReportLab para geração de PDF

## Requisitos

- Python 3.9 ou superior
- pip

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/JoaoPedroFigueiredoBicalho/AdmFinTP1.git
cd AdmFinTP1
```

2. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv .venv
```

3. Ative o ambiente virtual:

No Windows:

```bash
.venv\Scripts\activate
```

No macOS/Linux:

```bash
source .venv/bin/activate
```

4. Instale as dependências usando o arquivo de requisitos:

```bash
pip install -r requirements.txt
```

## Execução

Para iniciar a aplicação:

```bash
python TP1.py
```

## Como usar

1. Preencha o nome do investimento;
2. Informe o investimento inicial em reais;
3. Informe a taxa de desconto em porcentagem;
4. Defina a quantidade de períodos;
5. Insira os fluxos de caixa de cada período;
6. Clique em "Adicionar investimento";
7. Repita para outros investimentos;
8. Use "Comparar investimentos" para ver a melhor alternativa;
9. Use "Gerar relatório PDF" para exportar a análise.

## Estrutura do projeto

- `TP1.py` — aplicação principal com a interface gráfica e os cálculos financeiros;
- `README.md` — documentação do projeto.

## Observações

- O projeto foi desenvolvido para fins acadêmicos e de análise financeira básica.
- Os cálculos seguem uma abordagem simples de comparação de investimentos com foco em VPL e indicadores financeiros clássicos.
- A entrada de valores aceita formatos comuns, como `10000`, `10000,50` e `10.000,50`.

## Licença

Este projeto não especifica uma licença pública e foi desenvolvido como material de estudo/atividade acadêmica.
