# run.py - PUNTO DE ENTRADA MEJORADO
import sys
import logging
from services import google_sheets
from core import enricher

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("enrichment.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def print_banner():
    """Muestra banner de bienvenida."""
    banner = """
╔═══════════════════════════════════════════════════╗
║        🚀 ENRIQUECEDOR DE DATOS EMPRESARIALES       ║
║                    VERSIÓN 2.0                      ║
║                                                     ║
║  ✨ Multi-motor de búsqueda                         ║
║  🎯 Búsquedas contextuales inteligentes             ║
║  🛡️  Anti-detection avanzado                        ║
║  📊 Análisis de completitud                         ║
║  🇦🇷 Optimizado para empresas argentinas            ║
╚═══════════════════════════════════════════════════╝
    """
    print(banner)


def show_enrichment_analysis(analysis):
    """Muestra análisis detallado del potencial de enriquecimiento."""
    if "error" in analysis:
        print(f"❌ Error en análisis: {analysis['error']}")
        return

    print("\n📊 ANÁLISIS DE POTENCIAL DE ENRIQUECIMIENTO:")
    print(f"   📋 Total empresas pendientes: {analysis['total_pending']}")
    print(
        f"   🏢 Con nombre: {analysis['with_name']} ({(analysis['with_name']/analysis['total_pending']*100):.1f}%)"
    )
    print(
        f"   🔢 Con CUIT: {analysis['with_cuit']} ({(analysis['with_cuit']/analysis['total_pending']*100):.1f}%)"
    )
    print(
        f"   📍 Con ubicación: {analysis['with_location']} ({(analysis['with_location']/analysis['total_pending']*100):.1f}%)"
    )
    print(
        f"   🌐 Con sitio web: {analysis['with_web']} ({(analysis['with_web']/analysis['total_pending']*100):.1f}%)"
    )

    if analysis["completely_empty"] > 0:
        print(f"   ⚠️  Completamente vacías: {analysis['completely_empty']}")

    # Indicador visual del potencial
    potential = analysis["enrichment_potential"]
    potential_icons = {"alto": "🟢", "medio": "🟡", "bajo": "🔴"}
    potential_desc = {
        "alto": "Excelente - La mayoría tiene datos buscables",
        "medio": "Bueno - Cerca de la mitad tiene datos buscables",
        "bajo": "Limitado - Pocos datos para buscar",
    }

    print(
        f"   {potential_icons[potential]} Potencial: {potential.upper()} - {potential_desc[potential]}"
    )


def get_user_confirmation(message):
    """Obtiene confirmación del usuario con validación."""
    while True:
        response = input(f"\n{message} (s/n): ").lower().strip()
        if response in ["s", "si", "yes", "y"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Por favor responde 's' para sí o 'n' para no.")


def select_processing_strategy(analysis):
    """Permite al usuario elegir estrategia de procesamiento basada en análisis."""
    print("\n🎯 ESTRATEGIAS RECOMENDADAS:")

    potential = analysis.get("enrichment_potential", "bajo")
    total = analysis.get("total_pending", 0)

    if potential == "alto":
        print("   ✅ Procesamiento completo - Se esperan excelentes resultados")
        recommended_limit = total
    elif potential == "medio":
        print(
            "   🎯 Procesamiento selectivo - Comenzar con empresas que tienen más datos"
        )
        recommended_limit = min(50, total)
    else:
        print("   ⚠️  Procesamiento limitado - Pocos datos disponibles para enriquecer")
        recommended_limit = min(20, total)

    print(f"\n💡 RECOMENDACIÓN: Procesar {recommended_limit} empresas")

    # Opciones para el usuario
    print("\nOpciones disponibles:")
    print(f"   1. Procesar TODAS las {total} empresas")
    print(f"   2. Procesar las primeras {recommended_limit} empresas (recomendado)")
    print("   3. Especificar cantidad personalizada")
    print("   4. Cancelar")

    while True:
        try:
            choice = input("\nElige una opción (1-4): ").strip()

            if choice == "1":
                return total
            elif choice == "2":
                return recommended_limit
            elif choice == "3":
                custom_limit = int(
                    input(f"¿Cuántas empresas quieres procesar? (máx {total}): ")
                )
                return min(custom_limit, total)
            elif choice == "4":
                return None
            else:
                print("Opción inválida. Elige 1, 2, 3 o 4.")

        except ValueError:
            print("Por favor ingresa un número válido.")


def main():
    """Punto de entrada principal mejorado."""
    print_banner()

    logger.info("Iniciando Enriquecedor de Datos Empresariales v2.0")

    # Conexión a Google Sheets
    print("🔌 Conectando con Google Sheets...")
    client = google_sheets.get_gspread_client()
    if not client:
        print("❌ Error: No se pudo conectar con Google Sheets.")
        print("   Verifica que el archivo 'credentials.json' existe y es válido.")
        sys.exit(1)

    print("✅ Conexión establecida exitosamente.")

    # Obtener hojas disponibles
    worksheets = google_sheets.get_all_worksheets(client)
    if not worksheets:
        print("❌ No se encontraron hojas en el documento.")
        print("   Verifica que el nombre del documento en config.py es correcto.")
        sys.exit(1)

    # Selección de hoja
    print(f"\n📋 HOJAS DISPONIBLES ({len(worksheets)} encontradas):")
    for i, ws in enumerate(worksheets):
        print(f"   {i + 1}. {ws.title}")

    while True:
        try:
            choice = (
                int(
                    input(f"\n📌 Selecciona la hoja a procesar (1-{len(worksheets)}): ")
                )
                - 1
            )
            if 0 <= choice < len(worksheets):
                selected_ws = worksheets[choice]
                break
            else:
                print(f"Número fuera de rango. Debe estar entre 1 y {len(worksheets)}.")
        except ValueError:
            print("Por favor ingresa un número válido.")

    print(f"✅ Hoja seleccionada: '{selected_ws.title}'")

    # Análisis de la hoja
    print(f"\n🔍 Analizando hoja '{selected_ws.title}'...")
    stats = google_sheets.analyze_worksheet(selected_ws)

    if not stats:
        print("❌ Error al analizar la hoja.")
        sys.exit(1)

    if stats["pending"] == 0:
        print("ℹ️  No hay empresas pendientes de búsqueda en esta hoja.")
        print("   Todas las empresas ya han sido procesadas.")
        sys.exit(0)

    # Mostrar estadísticas básicas
    print("\n📊 ESTADÍSTICAS DE LA HOJA:")
    print(f"   📈 Total de empresas: {stats['total']}")
    print(f"   ✅ Empresas completadas: {stats['completed']}")
    print(f"   ⏳ Empresas pendientes: {stats['pending']}")

    # Análisis detallado del potencial
    print("\n🔬 Realizando análisis detallado...")
    analysis = enricher.analyze_enrichment_potential(selected_ws)
    show_enrichment_analysis(analysis)

    # Seleccionar estrategia de procesamiento
    limit = select_processing_strategy(analysis)
    if limit is None:
        print("\n👋 Proceso cancelado por el usuario.")
        sys.exit(0)

    # Confirmación final
    print("\n📋 RESUMEN DEL PROCESAMIENTO:")
    print(f"   🎯 Hoja: '{selected_ws.title}'")
    print(f"   📊 Empresas a procesar: {limit}")
    print(
        f"   🔍 Potencial: {analysis.get('enrichment_potential', 'desconocido').upper()}"
    )

    if not get_user_confirmation("¿Deseas continuar con el procesamiento?"):
        print("\n👋 Proceso cancelado por el usuario.")
        sys.exit(0)

    # Ejecutar enriquecimiento
    print("\n🚀 INICIANDO PROCESAMIENTO...")
    print(
        "⏰ Esto puede tomar varios minutos dependiendo de la cantidad de empresas..."
    )
    print("💡 Puedes interrumpir en cualquier momento con Ctrl+C")

    try:
        enricher.run_enrichment_process(selected_ws, limit)

        print("\n🎉 ¡PROCESAMIENTO COMPLETADO EXITOSAMENTE!")
        print("📝 Revisa los logs en 'enrichment.log' para más detalles.")
        print("📊 Los resultados han sido actualizados en Google Sheets.")

    except KeyboardInterrupt:
        print("\n⏹️  Procesamiento interrumpido por el usuario.")
        print("💾 Los datos procesados hasta ahora han sido guardados.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error durante el procesamiento: {e}")
        print(f"\n❌ Error durante el procesamiento: {e}")
        print("📝 Revisa los logs en 'enrichment.log' para más detalles.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Programa interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        print(f"\n💥 Error fatal: {e}")
        print("📞 Si el problema persiste, contacta al desarrollador.")
        sys.exit(1)
