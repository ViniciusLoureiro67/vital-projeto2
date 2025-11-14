from datetime import date

from modelo.moto import Moto
from modelo.checklist_item import ChecklistItem, StatusItem
from modelo.checklist import Checklist
from controle.oficina_controller import OficinaController
from analytics.oficina_analytics import OficinaAnalytics


def popular_dados_exemplo(controller: OficinaController) -> None:
    """
    Cria alguns checklists de exemplo para podermos testar o sistema.
    Em produção, isso poderia ser substituído por dados reais.
    """
    moto = Moto("QLE-5084", "Yamaha", "MT-07", 2022, 689)
    controller.cadastrar_moto(moto)

    # Revisão 1
    checklist1 = Checklist(moto=moto, km_atual=15000, data_revisao=date(2025, 1, 10))
    checklist1.adicionar_item(
        ChecklistItem(
            nome="Óleo do motor",
            categoria="Motor",
            status=StatusItem.NECESSITA_TROCA,
            custo_estimado=250.0,
        )
    )
    checklist1.adicionar_item(
        ChecklistItem(
            nome="Pastilhas de freio dianteiras",
            categoria="Freios",
            status=StatusItem.NECESSITA_TROCA,
            custo_estimado=350.0,
        )
    )
    controller.registrar_checklist(checklist1)

    # Revisão 2
    checklist2 = Checklist(moto=moto, km_atual=22000, data_revisao=date(2025, 6, 5))
    checklist2.adicionar_item(
        ChecklistItem(
            nome="Pneu traseiro",
            categoria="Pneus",
            status=StatusItem.NECESSITA_TROCA,
            custo_estimado=800.0,
        )
    )
    checklist2.adicionar_item(
        ChecklistItem(
            nome="Filtro de ar",
            categoria="Motor",
            status=StatusItem.NECESSITA_TROCA,
            custo_estimado=180.0,
        )
    )
    controller.registrar_checklist(checklist2)

    # Revisão 3
    checklist3 = Checklist(moto=moto, km_atual=30000, data_revisao=date(2026, 1, 20))
    checklist3.adicionar_item(
        ChecklistItem(
            nome="Óleo + filtro + fluido de freio",
            categoria="Motor/Freios",
            status=StatusItem.NECESSITA_TROCA,
            custo_estimado=450.0,
        )
    )
    controller.registrar_checklist(checklist3)


def mostrar_menu() -> None:
    print("\n=== MENU OFICINA VITAL ===")
    print("1 - Listar motos cadastradas")
    print("2 - Buscar moto por PLACA")
    print("3 - Buscar motos por MODELO")
    print("4 - Ver histórico de revisões de uma moto (por placa)")
    print("5 - Ver resumo de custos (Analytics)")
    print("0 - Sair")


def listar_motos(controller: OficinaController) -> None:
    motos = controller.listar_motos()
    if not motos:
        print("Nenhuma moto cadastrada.")
        return

    print("\n=== Motos cadastradas ===")
    for m in motos:
        print(f"- {m.modelo} ({m.placa}) - Ano {m.ano}")


def buscar_por_placa(controller: OficinaController) -> None:
    placa = input("Digite a placa da moto: ").strip()
    moto = controller.get_moto_por_placa(placa)

    if moto is None:
        print(f"Nenhuma moto encontrada com a placa: {placa}")
        return

    print(f"\nMoto encontrada: {moto.modelo} ({moto.placa}) - Ano {moto.ano}")


def buscar_por_modelo(controller: OficinaController) -> None:
    termo = input("Digite parte ou o nome completo do modelo: ").strip()
    motos = controller.buscar_motos_por_modelo(termo)

    if not motos:
        print(f"Nenhuma moto encontrada para o modelo que contém: '{termo}'")
        return

    print(f"\nMotos encontradas para modelo contendo '{termo}':")
    for m in motos:
        print(f"- {m.modelo} ({m.placa}) - Ano {m.ano}")


def ver_historico_revisoes(controller: OficinaController) -> None:
    placa = input("Digite a placa da moto para ver o histórico: ").strip()
    historico = controller.get_checklists_por_moto(placa)

    if not historico:
        print(f"Nenhum checklist encontrado para a moto com placa: {placa}")
        return

    print(f"\n=== Histórico de revisões da moto {placa.upper()} ===")
    for ch in historico:
        print(ch)
        print(f"- Custo total estimado das trocas: R$ {ch.custo_total_estimado():.2f}")
        print("-" * 50)


def ver_resumo_analytics(analytics: OficinaAnalytics) -> None:
    print("\n=== Resumo de custos (NumPy) ===")
    resumo = analytics.resumo_custos()
    print(f"Soma total: R$ {resumo['soma']:.2f}")
    print(f"Média por revisão: R$ {resumo['media']:.2f}")
    print(f"Maior custo: R$ {resumo['max']:.2f}")
    print(f"Menor custo: R$ {resumo['min']:.2f}")

    print("\n=== Distribuição de status dos itens (TODAS as revisões) ===")
    dist = analytics.distribuicao_status_itens()
    print(f"Itens concluídos: {dist['concluido']}")
    print(f"Itens pendentes: {dist['pendente']}")
    print(f"Itens com necessidade de troca: {dist['necessita_troca']}")

    print("\n=== Estimativa de custo em função da quilometragem (polyfit) ===")
    modelo = analytics.estimar_custo_por_km()
    if modelo is not None:
        print(f"Coeficiente angular (a): {modelo['coef_angular']:.6f}")
        print(f"Coeficiente linear (b): {modelo['coef_linear']:.2f}")

        km_futuro = 35000
        custo_prev = analytics.prever_custo_para_km(km_futuro)
        print(f"Custo previsto para {km_futuro} km: R$ {custo_prev:.2f}")
    else:
        print("Dados insuficientes para estimar um modelo.")


def main():
    print("Oficina Vital – Projeto 2UP em Python iniciado! 🚀\n")

    controller = OficinaController()
    popular_dados_exemplo(controller)
    analytics = OficinaAnalytics(controller)

    while True:
        mostrar_menu()
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            listar_motos(controller)
        elif opcao == "2":
            buscar_por_placa(controller)
        elif opcao == "3":
            buscar_por_modelo(controller)
        elif opcao == "4":
            ver_historico_revisoes(controller)
        elif opcao == "5":
            ver_resumo_analytics(analytics)
        elif opcao == "0":
            print("Encerrando sistema. Até mais! 👋")
            break
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
