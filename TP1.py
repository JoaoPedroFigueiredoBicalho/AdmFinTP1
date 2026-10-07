# ============================================================
# INVESTCOMPARE - COMPARADOR DE INVESTIMENTOS
#
# Versão com:
# - Interface gráfica
# - Cálculo de VPL, ganho nominal, retorno, TIR e payback
# - Gráfico comparativo dentro da interface
# - Geração de relatório em PDF
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Bibliotecas externas usadas para gráficos e PDF.
# Instale, se necessário:
# pip install matplotlib reportlab
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)


# ============================================================
# CÁLCULOS FINANCEIROS
# ============================================================

def calcular_vpl(investimento_inicial, fluxos, taxa):
    """Calcula o Valor Presente Líquido (VPL)."""

    vpl = -investimento_inicial

    for periodo, fluxo in enumerate(fluxos, start=1):
        vpl += fluxo / ((1 + taxa) ** periodo)

    return vpl


def calcular_ganho_nominal(investimento_inicial, fluxos):
    """Calcula o ganho nominal total."""

    return sum(fluxos) - investimento_inicial


def calcular_retorno_percentual(investimento_inicial, fluxos):
    """Calcula o retorno percentual simples."""

    ganho = calcular_ganho_nominal(
        investimento_inicial,
        fluxos
    )

    return (ganho / investimento_inicial) * 100


def calcular_payback(investimento_inicial, fluxos):
    """Calcula o Payback Simples."""

    acumulado = 0

    for periodo, fluxo in enumerate(fluxos, start=1):

        acumulado_anterior = acumulado
        acumulado += fluxo

        if acumulado >= investimento_inicial:

            valor_faltante = (
                investimento_inicial - acumulado_anterior
            )

            if fluxo > 0:
                fracao = valor_faltante / fluxo
            else:
                fracao = 0

            return (periodo - 1) + fracao

    return None


def calcular_tir(investimento_inicial, fluxos):
    """Calcula a Taxa Interna de Retorno (TIR)."""

    if not fluxos:
        return None

    def npv(taxa):
        return sum(
            fluxo / ((1 + taxa) ** periodo)
            for periodo, fluxo in enumerate(fluxos, start=1)
        ) - investimento_inicial

    if npv(0) == 0:
        return 0

    limite_inferior = -0.9999
    limite_superior = 0.0
    valor_inferior = npv(limite_inferior)
    valor_superior = npv(limite_superior)

    if valor_inferior == 0:
        return limite_inferior
    if valor_superior == 0:
        return limite_superior

    if valor_inferior * valor_superior > 0:
        limite_superior = 0.5
        valor_superior = npv(limite_superior)

        if valor_inferior * valor_superior > 0:
            for tentativa in range(1, 101):
                limite_superior = 2 ** tentativa
                valor_superior = npv(limite_superior)

                if valor_inferior * valor_superior <= 0:
                    break
            else:
                return None

    for _ in range(200):
        ponto_medio = (limite_inferior + limite_superior) / 2
        valor_medio = npv(ponto_medio)

        if abs(valor_medio) < 1e-10:
            return ponto_medio

        if valor_inferior * valor_medio <= 0:
            limite_superior = ponto_medio
            valor_superior = valor_medio
        else:
            limite_inferior = ponto_medio
            valor_inferior = valor_medio

        if abs(limite_superior - limite_inferior) < 1e-12:
            return (limite_inferior + limite_superior) / 2

    return (limite_inferior + limite_superior) / 2

def gerar_grafico_linhas(investimentos):
    """
    Gera um gráfico de linhas com o fluxo de caixa acumulado
    de cada investimento e devolve a imagem em memória (PNG).
    """

    figura = Figure(figsize=(7.5, 4), dpi=150)
    FigureCanvasAgg(figura)
    ax = figura.add_subplot(111)

    max_periodos = 0

    for inv in investimentos:

        acumulado = -inv["inicial"]
        serie = [acumulado]

        for fluxo in inv["fluxos"]:
            acumulado += fluxo
            serie.append(acumulado)

        periodos = list(range(len(serie)))
        max_periodos = max(max_periodos, len(serie) - 1)

        ax.plot(
            periodos,
            serie,
            marker="o",
            linewidth=2,
            label=inv["nome"]
        )

    ax.axhline(0, color="black", linewidth=1, linestyle="--")

    ax.set_title("Fluxo de caixa acumulado por investimento")
    ax.set_xlabel("Período")
    ax.set_ylabel("Valor acumulado (R$)")
    ax.set_xticks(range(0, max_periodos + 1))
    ax.grid(True, alpha=0.3)
    ax.legend()

    figura.tight_layout()

    buffer = BytesIO()
    figura.savefig(buffer, format="png")
    buffer.seek(0)

    return buffer

# ============================================================
# FORMATAÇÃO
# ============================================================

def converter_numero(texto):
    """
    Converte números digitados pelo usuário.

    Exemplos aceitos:
    10000
    10000,50
    10.000,50
    """

    texto = (
        texto
        .strip()
        .replace("R$", "")
        .replace(" ", "")
    )

    if "," in texto:
        texto = texto.replace(".", "")
        texto = texto.replace(",", ".")
    else:
        texto = texto.replace(",", "")

    return float(texto)


def dinheiro(valor):
    """Formata valores no padrão monetário brasileiro."""

    texto = f"{valor:,.2f}"

    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")

    return f"R$ {texto}"


# ============================================================
# APLICAÇÃO
# ============================================================

class InvestCompareApp:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "InvestCompare - Administração Financeira"
        )

        self.root.geometry("1200x850")
        self.root.minsize(1000, 700)

        # Lista com todos os investimentos cadastrados.
        self.investimentos = []

        # Campos dos fluxos de caixa.
        self.fluxos_entries = []

        self.criar_estilo()
        self.criar_interface()

    # ========================================================
    # ESTILO
    # ========================================================

    def criar_estilo(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Arial", 20, "bold")
        )

        style.configure(
            "Subtitle.TLabel",
            font=("Arial", 10)
        )

        style.configure(
            "Section.TLabel",
            font=("Arial", 12, "bold")
        )

        style.configure(
            "Action.TButton",
            font=("Arial", 10, "bold"),
            padding=8
        )

        style.configure(
            "Treeview",
            rowheight=30,
            font=("Arial", 10)
        )

        style.configure(
            "Treeview.Heading",
            font=("Arial", 10, "bold")
        )

    # ========================================================
    # INTERFACE
    # ========================================================

    def criar_interface(self):

        # ----------------------------------------------------
        # CABEÇALHO
        # ----------------------------------------------------

        header = ttk.Frame(
            self.root,
            padding=20
        )

        header.pack(fill="x")

        ttk.Label(
            header,
            text="InvestCompare",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            header,
            text=(
                "Comparador de Investimentos - "
                "Administração Financeira"
            ),
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(5, 0))

        # ----------------------------------------------------
        # DADOS DO INVESTIMENTO
        # ----------------------------------------------------

        entrada = ttk.LabelFrame(
            self.root,
            text="Dados do investimento",
            padding=15
        )

        entrada.pack(
            fill="x",
            padx=20,
            pady=5
        )

        ttk.Label(
            entrada,
            text="Nome do investimento:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.nome_entry = ttk.Entry(
            entrada,
            width=30
        )

        self.nome_entry.grid(
            row=0,
            column=1,
            sticky="w",
            padx=5,
            pady=5
        )

        ttk.Label(
            entrada,
            text="Investimento inicial (R$):"
        ).grid(
            row=0,
            column=2,
            sticky="w",
            padx=5,
            pady=5
        )

        self.inicial_entry = ttk.Entry(
            entrada,
            width=20
        )

        self.inicial_entry.grid(
            row=0,
            column=3,
            sticky="w",
            padx=5,
            pady=5
        )

        ttk.Label(
            entrada,
            text="Taxa de desconto (%):"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=5,
            pady=5
        )

        self.taxa_entry = ttk.Entry(
            entrada,
            width=15
        )

        self.taxa_entry.grid(
            row=1,
            column=1,
            sticky="w",
            padx=5,
            pady=5
        )

        ttk.Label(
            entrada,
            text="Quantidade de períodos:"
        ).grid(
            row=1,
            column=2,
            sticky="w",
            padx=5,
            pady=5
        )

        self.periodos_entry = ttk.Entry(
            entrada,
            width=15
        )

        self.periodos_entry.grid(
            row=1,
            column=3,
            sticky="w",
            padx=5,
            pady=5
        )

        ttk.Button(
            entrada,
            text="Definir períodos",
            style="Action.TButton",
            command=self.criar_campos_fluxo
        ).grid(
            row=2,
            column=0,
            columnspan=4,
            pady=12
        )

        # ----------------------------------------------------
        # FLUXOS
        # ----------------------------------------------------

        self.fluxos_frame = ttk.LabelFrame(
            self.root,
            text="Fluxos de caixa",
            padding=15
        )

        self.fluxos_frame.pack(
            fill="x",
            padx=20,
            pady=5
        )

        self.fluxos_container = ttk.Frame(
            self.fluxos_frame
        )

        self.fluxos_container.pack(
            fill="x"
        )

        # ----------------------------------------------------
        # BOTÕES
        # ----------------------------------------------------

        botoes = ttk.Frame(
            self.root,
            padding=(20, 10)
        )

        botoes.pack(fill="x")

        ttk.Button(
            botoes,
            text="Adicionar investimento",
            style="Action.TButton",
            command=self.adicionar_investimento
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            botoes,
            text="Limpar campos",
            command=self.limpar_campos
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            botoes,
            text="Remover selecionado",
            command=self.remover_selecionado
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            botoes,
            text="Comparar investimentos",
            style="Action.TButton",
            command=self.comparar
        ).pack(
            side="left",
            padx=5
        )

        ttk.Button(
            botoes,
            text="Gerar relatório PDF",
            style="Action.TButton",
            command=self.gerar_pdf
        ).pack(
            side="right",
            padx=5
        )

        # ----------------------------------------------------
        # TABELA
        # ----------------------------------------------------

        tabela_frame = ttk.LabelFrame(
            self.root,
            text="Investimentos cadastrados",
            padding=10
        )

        tabela_frame.pack(
            fill="x",
            padx=20,
            pady=5
        )

        colunas = (
            "nome",
            "inicial",
            "vpl",
            "ganho",
            "retorno",
            "tir",
            "payback"
        )

        self.tabela = ttk.Treeview(
            tabela_frame,
            columns=colunas,
            show="headings",
            selectmode="browse",
            height=6
        )

        titulos = {
            "nome": "Investimento",
            "inicial": "Investimento inicial",
            "vpl": "VPL",
            "ganho": "Ganho nominal",
            "retorno": "Retorno",
            "tir": "TIR",
            "payback": "Payback"
        }

        larguras = {
            "nome": 170,
            "inicial": 150,
            "vpl": 150,
            "ganho": 150,
            "retorno": 100,
            "tir": 100,
            "payback": 110
        }

        for coluna in colunas:

            self.tabela.heading(
                coluna,
                text=titulos[coluna]
            )

            self.tabela.column(
                coluna,
                width=larguras[coluna],
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            tabela_frame,
            orient="vertical",
            command=self.tabela.yview
        )

        self.tabela.configure(
            yscrollcommand=scrollbar.set
        )

        self.tabela.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        self.resultado_label = ttk.Label(
            self.root,
            text=(
                "Cadastre os investimentos para "
                "iniciar a análise."
            ),
            font=("Arial", 11, "bold"),
            padding=10
        )

        self.resultado_label.pack(
            fill="x",
            padx=20,
            pady=5
        )

        # ----------------------------------------------------
        # ÁREA DO GRÁFICO
        # ----------------------------------------------------

        grafico_frame = ttk.LabelFrame(
            self.root,
            text="Análise gráfica",
            padding=5
        )

        grafico_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=5
        )

        self.grafico_frame = grafico_frame

        self.figure = plt.Figure(
            figsize=(8, 3.2),
            dpi=90
        )

        self.ax = self.figure.add_subplot(111)

        self.ax.set_title(
            "VPL dos investimentos"
        )

        self.ax.set_ylabel(
            "VPL (R$)"
        )

        self.ax.text(
            0.5,
            0.5,
            "Cadastre investimentos para visualizar o gráfico.",
            ha="center",
            va="center",
            transform=self.ax.transAxes
        )

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=grafico_frame
        )

        self.canvas.get_tk_widget().pack(
            fill="both",
            expand=True
        )

        self.canvas.draw()

    # ========================================================
    # CAMPOS DE FLUXO
    # ========================================================

    def criar_campos_fluxo(self):

        for widget in self.fluxos_container.winfo_children():
            widget.destroy()

        self.fluxos_entries = []

        try:

            periodos = int(
                self.periodos_entry.get()
            )

            if periodos <= 0 or periodos > 50:
                raise ValueError

        except ValueError:

            messagebox.showerror(
                "Erro",
                "Digite uma quantidade de períodos entre 1 e 50."
            )

            return

        for periodo in range(
            1,
            periodos + 1
        ):

            linha = ttk.Frame(
                self.fluxos_container
            )

            linha.pack(
                fill="x",
                pady=3
            )

            ttk.Label(
                linha,
                text=f"Período {periodo}:",
                width=12
            ).pack(
                side="left"
            )

            entry = ttk.Entry(
                linha,
                width=20
            )

            entry.pack(
                side="left",
                padx=5
            )

            self.fluxos_entries.append(entry)

        if self.fluxos_entries:
            self.fluxos_entries[0].focus()

    # ========================================================
    # ADICIONAR INVESTIMENTO
    # ========================================================

    def adicionar_investimento(self):

        try:

            nome = self.nome_entry.get().strip()

            if not nome:
                raise ValueError(
                    "Informe o nome do investimento."
                )

            investimento_inicial = converter_numero(
                self.inicial_entry.get()
            )

            if investimento_inicial <= 0:
                raise ValueError(
                    "O investimento inicial deve ser maior que zero."
                )

            taxa = converter_numero(
                self.taxa_entry.get()
            ) / 100

            if taxa < 0:
                raise ValueError(
                    "A taxa não pode ser negativa."
                )

            if not self.fluxos_entries:
                raise ValueError(
                    "Defina primeiro a quantidade de períodos."
                )

            fluxos = [
                converter_numero(entry.get())
                for entry in self.fluxos_entries
            ]

            investimento = {
                "nome": nome,
                "inicial": investimento_inicial,
                "fluxos": fluxos,
                "taxa": taxa,
                "vpl": calcular_vpl(
                    investimento_inicial,
                    fluxos,
                    taxa
                ),
                "ganho": calcular_ganho_nominal(
                    investimento_inicial,
                    fluxos
                ),
                "retorno": calcular_retorno_percentual(
                    investimento_inicial,
                    fluxos
                ),
                "tir": calcular_tir(
                    investimento_inicial,
                    fluxos
                ),
                "payback": calcular_payback(
                    investimento_inicial,
                    fluxos
                )
            }

            self.investimentos.append(
                investimento
            )

            self.atualizar_tabela()
            self.atualizar_grafico()
            self.limpar_campos()

            messagebox.showinfo(
                "Sucesso",
                f"'{nome}' foi cadastrado com sucesso."
            )

        except ValueError as erro:

            messagebox.showerror(
                "Dados inválidos",
                str(erro)
            )

    # ========================================================
    # TABELA
    # ========================================================

    def atualizar_tabela(self):

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for investimento in self.investimentos:

            if investimento["tir"] is None:
                tir = "N/A"
            else:
                tir = (
                    f"{investimento['tir'] * 100:.2f}%"
                )

            if investimento["payback"] is None:
                payback = "Não recuperado"
            else:
                payback = (
                    f"{investimento['payback']:.2f}"
                )

            self.tabela.insert(
                "",
                "end",
                values=(
                    investimento["nome"],
                    dinheiro(
                        investimento["inicial"]
                    ),
                    dinheiro(
                        investimento["vpl"]
                    ),
                    dinheiro(
                        investimento["ganho"]
                    ),
                    f"{investimento['retorno']:.2f}%",
                    tir,
                    payback
                )
            )

    # ========================================================
    # GRÁFICO
    # ========================================================

    def atualizar_grafico(self):

        self.ax.clear()

        if not self.investimentos:

            self.ax.set_title(
                "VPL dos investimentos"
            )

            self.ax.text(
                0.5,
                0.5,
                "Cadastre investimentos para visualizar o gráfico.",
                ha="center",
                va="center",
                transform=self.ax.transAxes
            )

            self.canvas.draw()

            return

        nomes = [
            investimento["nome"]
            for investimento in self.investimentos
        ]

        vpl = [
            investimento["vpl"]
            for investimento in self.investimentos
        ]

        self.ax.bar(
            nomes,
            vpl
        )

        self.ax.axhline(
            0,
            linewidth=1
        )

        self.ax.set_title(
            "Comparação do VPL"
        )

        self.ax.set_ylabel(
            "Valor Presente Líquido (R$)"
        )

        self.ax.tick_params(
            axis="x",
            rotation=25
        )

        self.figure.tight_layout()

        self.canvas.draw()

    # ========================================================
    # COMPARAÇÃO
    # ========================================================

    def comparar(self):

        if not self.investimentos:

            messagebox.showwarning(
                "Comparação",
                "Cadastre pelo menos um investimento."
            )

            return

        melhor = max(
            self.investimentos,
            key=lambda investimento:
            investimento["vpl"]
        )

        tir_texto = (
            f"TIR: {melhor['tir'] * 100:.2f}%\n"
            if melhor["tir"] is not None
            else "TIR: não identificada\n"
        )

        if melhor["vpl"] > 0:

            texto = (
                f"Melhor investimento: {melhor['nome']}\n\n"
                f"VPL: {dinheiro(melhor['vpl'])}\n"
                f"Retorno: {melhor['retorno']:.2f}%\n"
                f"{tir_texto}\n"
                "Recomendação: investimento atrativo "
                "pelo critério do VPL."
            )

        elif melhor["vpl"] == 0:

            texto = (
                f"Melhor investimento: {melhor['nome']}\n\n"
                f"VPL: {dinheiro(melhor['vpl'])}\n"
                f"{tir_texto}\n"
                "Recomendação: investimento indiferente "
                "pelo critério do VPL."
            )

        else:

            texto = (
                f"Maior VPL entre as alternativas: "
                f"{melhor['nome']}\n\n"
                f"VPL: {dinheiro(melhor['vpl'])}\n"
                f"{tir_texto}\n"
                "Atenção: o VPL é negativo."
            )

        self.resultado_label.config(
            text=texto
        )

        messagebox.showinfo(
            "Resultado da comparação",
            texto
        )

    # ========================================================
    # REMOVER INVESTIMENTO
    # ========================================================

    def remover_selecionado(self):

        selecionado = self.tabela.selection()

        if not selecionado:

            messagebox.showwarning(
                "Remover",
                "Selecione um investimento na tabela."
            )

            return

        indice = self.tabela.index(
            selecionado[0]
        )

        investimento = self.investimentos[
            indice
        ]

        confirmar = messagebox.askyesno(
            "Confirmar remoção",
            f"Deseja remover '{investimento['nome']}'?"
        )

        if confirmar:

            self.investimentos.pop(
                indice
            )

            self.atualizar_tabela()
            self.atualizar_grafico()

            self.resultado_label.config(
                text="Investimento removido."
            )

    # ========================================================
    # LIMPAR CAMPOS
    # ========================================================

    def limpar_campos(self):

        self.nome_entry.delete(
            0,
            tk.END
        )

        self.inicial_entry.delete(
            0,
            tk.END
        )

        self.periodos_entry.delete(
            0,
            tk.END
        )

        self.taxa_entry.delete(
            0,
            tk.END
        )

        for widget in self.fluxos_container.winfo_children():
            widget.destroy()

        self.fluxos_entries = []

    # ========================================================
    # GERAR PDF
    # ========================================================

    def gerar_pdf(self):

        if not self.investimentos:

            messagebox.showwarning(
                "Relatório",
                "Cadastre pelo menos um investimento "
                "antes de gerar o relatório."
            )

            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".pdf",
            filetypes=[
                ("Arquivo PDF", "*.pdf")
            ],
            initialfile="Relatorio_InvestCompare.pdf"
        )

        if not caminho:
            return

        try:

            documento = SimpleDocTemplate(
                caminho,
                pagesize=A4,
                rightMargin=35,
                leftMargin=35,
                topMargin=35,
                bottomMargin=35
            )

            estilos = getSampleStyleSheet()

            titulo = estilos["Title"]
            titulo.alignment = TA_CENTER

            subtitulo = estilos["Heading2"]
            normal = estilos["BodyText"]

            elementos = []

            # Título
            elementos.append(
                Paragraph(
                    "InvestCompare",
                    titulo
                )
            )

            elementos.append(
                Spacer(1, 8)
            )

            elementos.append(
                Paragraph(
                    "Relatório de Análise de Investimentos",
                    subtitulo
                )
            )

            elementos.append(
                Spacer(1, 15)
            )

            elementos.append(
                Paragraph(
                    "Administração Financeira - CAD 167",
                    normal
                )
            )

            elementos.append(
                Spacer(1, 15)
            )

            # ------------------------------------------------
            # TABELA PRINCIPAL
            # ------------------------------------------------

            dados = [
                [
                    "Investimento",
                    "Inicial",
                    "VPL",
                    "Ganho",
                    "Retorno",
                    "TIR",
                    "Payback"
                ]
            ]

            for investimento in self.investimentos:

                tir = (
                    f"{investimento['tir'] * 100:.2f}%"
                    if investimento["tir"] is not None
                    else "N/A"
                )

                payback = (
                    f"{investimento['payback']:.2f}"
                    if investimento["payback"] is not None
                    else "Não recuperado"
                )

                dados.append(
                    [
                        investimento["nome"],
                        dinheiro(
                            investimento["inicial"]
                        ),
                        dinheiro(
                            investimento["vpl"]
                        ),
                        dinheiro(
                            investimento["ganho"]
                        ),
                        f"{investimento['retorno']:.2f}%",
                        tir,
                        payback
                    ]
                )

            tabela = Table(
                dados,
                repeatRows=1,
                colWidths=[
                    76,
                    60,
                    60,
                    60,
                    48,
                    46,
                    52
                ]
            )

            tabela.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.black
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (-1, -1),
                        "CENTER"
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    )
                ])
            )

            elementos.append(tabela)
            elementos.append(Spacer(1, 20))

            # ------------------------------------------------
            # RECOMENDAÇÃO
            # ------------------------------------------------

            melhor = max(
                self.investimentos,
                key=lambda investimento:
                investimento["vpl"]
            )

            elementos.append(
                Paragraph(
                    "Conclusão",
                    subtitulo
                )
            )

            if melhor["vpl"] > 0:

                conclusao = (
                    f"O investimento com maior VPL foi "
                    f"<b>{melhor['nome']}</b>, com VPL de "
                    f"<b>{dinheiro(melhor['vpl'])}</b>. "
                    "Pelo critério do VPL, a alternativa apresenta "
                    "resultado positivo e é considerada atrativa."
                )

            elif melhor["vpl"] == 0:

                conclusao = (
                    f"O investimento com maior VPL foi "
                    f"<b>{melhor['nome']}</b>, com VPL igual a zero. "
                    "Pelo critério do VPL, a alternativa é indiferente."
                )

            else:

                conclusao = (
                    f"O investimento com maior VPL foi "
                    f"<b>{melhor['nome']}</b>, porém o VPL é "
                    f"<b>{dinheiro(melhor['vpl'])}</b>. "
                    "Assim, a alternativa não é atrativa pelo critério do VPL."
                )

            elementos.append(
                Paragraph(
                    conclusao,
                    normal
                )
            )

            elementos.append(
                Spacer(1, 15)
            )

            # ------------------------------------------------
            # GRÁFICO DE LINHAS
            # ------------------------------------------------

            elementos.append(
                Paragraph(
                    "Comparação gráfica dos investimentos",
                    subtitulo
                )
            )

            imagem_grafico = gerar_grafico_linhas(
                self.investimentos
            )

            elementos.append(
                Image(
                    imagem_grafico,
                    width=480,
                    height=256
                )
            )

            elementos.append(
                Spacer(1, 15)
            )

            # ------------------------------------------------
            # DETALHAMENTO DOS FLUXOS
            # ------------------------------------------------

            elementos.append(
                Paragraph(
                    "Fluxos de caixa utilizados",
                    subtitulo
                )
            )

            for investimento in self.investimentos:

                elementos.append(
                    Paragraph(
                        f"<b>{investimento['nome']}</b> "
                        f"- Taxa de desconto: "
                        f"{investimento['taxa'] * 100:.2f}%",
                        normal
                    )
                )

                fluxos_texto = " | ".join(
                    [
                        f"Período {i}: {dinheiro(fluxo)}"
                        for i, fluxo in enumerate(
                            investimento["fluxos"],
                            start=1
                        )
                    ]
                )

                elementos.append(
                    Paragraph(
                        fluxos_texto,
                        normal
                    )
                )

                elementos.append(
                    Spacer(1, 8)
                )

            # ------------------------------------------------
            # CONSTRUÇÃO DO PDF
            # ------------------------------------------------

            documento.build(
                elementos
            )

            messagebox.showinfo(
                "Relatório gerado",
                f"Relatório salvo em:\n{caminho}"
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro ao gerar PDF",
                f"Não foi possível gerar o relatório.\n\n{erro}"
            )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = InvestCompareApp(
        root
    )

    root.mainloop()
