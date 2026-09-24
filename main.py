import flet as ft
from datetime import datetime
import json
import os

ARQUIVO_DADOS = "historico_recargas.json"

# Dicionário para tradução dos meses em português
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def salvar_dados(dados):
    try:
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar dados: {e}")

def filtrar_ultimo_ano(dados):
    """Mantém apenas registros de no máximo 1 ano atrás (sobrescrevendo os mais antigos)."""
    agora = datetime.now()
    dados_filtrados = []
    for item in dados:
        try:
            data_item = datetime.strptime(item['data'], "%d/%m/%Y %H:%M")
            if (agora - data_item).days <= 365:
                dados_filtrados.append(item)
        except Exception:
            continue
    return dados_filtrados

def main(page: ft.Page):
    page.title = "Gestão de Recarga - BYD Dolphin"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 410
    page.window_height = 800

    TARIFA_BASE_KWH = 0.881
    
    historico_recargas = filtrar_ultimo_ano(carregar_dados())
    salvar_dados(historico_recargas)

    txt_kwh = ft.TextField(
        label="kWh Consumidos na Recarga",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=8
    )

    dropdown_bandeira = ft.Dropdown(
        label="Bandeira Tarifária Vigente (Obrigatório)",
        border_radius=8,
        options=[
            ft.dropdown.Option("Verde (R$ 0,00 por 100 kWh)"),
            ft.dropdown.Option("Amarela (R$ 1,885 a cada 100 kWh)"),
            ft.dropdown.Option("Vermelha P1 (R$ 4,463 a cada 100 kWh)"),
            ft.dropdown.Option("Vermelha P2 (R$ 7,877 a cada 100 kWh)"),
        ],
        value="Amarela (R$ 1,885 a cada 100 kWh)"
    )

    # Componentes para os 3 últimos meses na tela principal
    txt_mes_atual_titulo = ft.Text("Mês Atual", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700)
    txt_mes_atual_valor = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD)
    
    txt_mes_anterior_1_titulo = ft.Text("Mês -1", size=13, weight=ft.FontWeight.BOLD)
    txt_mes_anterior_1_valor = ft.Text("R$ 0,00", size=15)
    
    txt_mes_anterior_2_titulo = ft.Text("Mês -2", size=13, weight=ft.FontWeight.BOLD)
    txt_mes_anterior_2_valor = ft.Text("R$ 0,00", size=15)

    lista_historico = ft.ListView(expand=1, spacing=5, padding=10, auto_scroll=False)

    def calcular_custo(kwh, bandeira):
        adicional = 0.0
        if "Amarela" in bandeira:
            adicional = 1.885 / 100
        elif "Vermelha P1" in bandeira:
            adicional = 4.463 / 100
        elif "Vermelha P2" in bandeira:
            adicional = 7.877 / 100
        return kwh * (TARIFA_BASE_KWH + adicional)

    def obter_meses_alvo():
        """Retorna os 3 meses atuais/anteriores baseados na data de hoje."""
        agora = datetime.now()
        meses = []
        for i in range(3):
            m = agora.month - i
            a = agora.year
            while m <= 0:
                m += 12
                a -= 1
            meses.append((m, a))
        return meses # [(mes_atual, ano), (mes_passado, ano), (mes_passado_2, ano)]

    def atualizar_paineis_e_totais():
        meses_alvo = obter_meses_alvo()
        
        totais = {0: 0.0, 1: 0.0, 2: 0.0}
        
        for item in historico_recargas:
            try:
                data_item = datetime.strptime(item['data'], "%d/%m/%Y %H:%M")
                for idx, (m_alvo, a_alvo) in enumerate(meses_alvo):
                    if data_item.month == m_alvo and data_item.year == a_alvo:
                        totais[idx] += item['valor']
            except Exception:
                continue

        # Textos com nomes dos meses em Português
        m0, a0 = meses_alvo[0]
        m1, a1 = meses_alvo[1]
        m2, a2 = meses_alvo[2]

        txt_mes_atual_titulo.value = f"{MESES_PT[m0]} / {a0} (Atual)"
        txt_mes_atual_valor.value = f"R$ {totais[0]:.2f}"

        txt_mes_anterior_1_titulo.value = f"{MESES_PT[m1]} / {a1}"
        txt_mes_anterior_1_valor.value = f"R$ {totais[1]:.2f}"

        txt_mes_anterior_2_titulo.value = f"{MESES_PT[m2]} / {a2}"
        txt_mes_anterior_2_valor.value = f"R$ {totais[2]:.2f}"

        page.update()

    def carregar_historico_na_tela():
        lista_historico.controls.clear()
        for item in historico_recargas:
            lista_historico.controls.append(ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"{item['kwh']} kWh - R$ {item['valor']:.2f}", weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(f"Data: {item['data']} | Bandeira: {item['bandeira']}", size=11, color=ft.Colors.GREY_700),
                    ], spacing=2),
                    padding=10
                )
            ))

    def registrar_clique(e):
        nonlocal historico_recargas
        if not txt_kwh.value:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, informe a quantidade de kWh!"))
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            kwh = float(txt_kwh.value.replace(',', '.'))
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Digite um número válido para os kWh!"))
            page.snack_bar.open = True
            page.update()
            return

        bandeira = dropdown_bandeira.value
        if not bandeira:
            page.snack_bar = ft.SnackBar(ft.Text("A bandeira tarifária é obrigatória!"))
            page.snack_bar.open = True
            page.update()
            return

        valor_total = calcular_custo(kwh, bandeira)
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M")

        novo_registro = {'kwh': kwh, 'valor': valor_total, 'bandeira': bandeira, 'data': data_hora}
        
        historico_recargas.insert(0, novo_registro)
        historico_recargas = filtrar_ultimo_ano(historico_recargas)
        
        salvar_dados(historico_recargas)

        carregar_historico_na_tela()
        txt_kwh.value = ""
        atualizar_paineis_e_totais()
        page.update()

        def fechar_dialog(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Recarga Registrada!"),
            content=ft.Text(f"Custo calculado: R$ {valor_total:.2f}\nSalvo com sucesso!"),
            actions=[ft.TextButton("OK", on_click=fechar_dialog)]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    btn_registrar = ft.Button(
        content=ft.Text("Registrar Recarga e Calcular"),
        on_click=registrar_clique,
        width=400
    )

    carregar_historico_na_tela()
    atualizar_paineis_e_totais()

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Gestão de Recarga - BYD Dolphin", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                # Card com os 3 últimos meses destacados
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            txt_mes_atual_titulo,
                            txt_mes_atual_valor,
                            ft.Divider(height=10),
                            ft.Row([
                                ft.Column([txt_mes_anterior_1_titulo, txt_mes_anterior_1_valor], expand=1),
                                ft.VerticalDivider(width=1),
                                ft.Column([txt_mes_anterior_2_titulo, txt_mes_anterior_2_valor], expand=1),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ], spacing=6),
                        padding=12
                    ),
                    elevation=2
                ),
                
                ft.Container(height=2),
                txt_kwh,
                dropdown_bandeira,
                ft.Container(height=2),
                btn_registrar,
                ft.Divider(),
                
                ft.Text("Histórico Geral (Até 1 Ano):", weight=ft.FontWeight.BOLD, size=15),
                ft.Container(
                    content=lista_historico, 
                    height=200, 
                    border_radius=8,
                    bgcolor=ft.Colors.GREY_50
                )
            ], spacing=10),
            padding=15,
            width=420
        )
    )

ft.app(target=main)