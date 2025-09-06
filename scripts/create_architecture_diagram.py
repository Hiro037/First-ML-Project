import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import matplotlib.lines as lines


def create_architecture_diagram():
    # Настраиваем размер и стиль графика
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Цветовая схема
    colors = {
        'external': '#FF6B6B',
        'container': '#4ECDC4',
        'main_components': '#45B7D1',
        'support_components': '#F9A602',
        'database': '#9B59B6',
        'output': '#2ECC71',
        'arrows': '#34495E'
    }

    # Рисуем Docker контейнер
    container = patches.Rectangle((1, 1), 12, 8, linewidth=3, linestyle='-',
                                  edgecolor=colors['container'], facecolor='none', alpha=0.8)
    ax.add_patch(container)
    ax.text(7, 9.2, 'Docker Container', fontsize=16, fontweight='bold',
            color=colors['container'], ha='center')

    # Основные компоненты системы
    components = [
        # Основные компоненты
        ('Binance\nWebSocket\nClient', 3.5, 7, colors['main_components'], 2.5, 1.2),
        ('Real-time\nMonitor', 7, 7, colors['main_components'], 2.5, 1.2),
        ('Database\nPostgreSQL', 10.5, 7, colors['database'], 2.5, 1.2),

        # Вспомогательные компоненты
        ('Binance REST\nAPI Client', 3.5, 4.5, colors['support_components'], 2.5, 1.2),
        ('Beta Calculator\n(Model)', 7, 4.5, colors['support_components'], 2.5, 1.2),
        ('Alert\nGenerator', 10.5, 4.5, colors['output'], 2.5, 1.2),

        # Внешние сервисы
        ('Binance Exchange\n(External)', 7, 2, colors['external'], 3, 1.2)
    ]

    # Рисуем компоненты
    for name, x, y, color, width, height in components:
        # Красивые скругленные прямоугольники
        box = FancyBboxPatch((x - width / 2, y - height / 2), width, height,
                             boxstyle="round,pad=0.3", linewidth=2,
                             edgecolor='black', facecolor=color, alpha=0.9)
        ax.add_patch(box)
        ax.text(x, y, name, ha='center', va='center',
                fontweight='bold', fontsize=9, color='white')

    # Стрелки и соединения
    connections = [
        # Внешние подключения
        (7, 2.6, 7, 3.8, 'REST API\n(исторические данные)', 'dashed'),
        (7, 2.6, 3.5, 3.8, 'WebSocket\n(реальное время)', 'dashed'),

        # Внутренние данные
        (3.5, 5.8, 7, 5.8, 'Цены в\nреальном времени', 'solid'),
        (7, 5.8, 10.5, 5.8, 'Сохранение\nданных', 'solid'),
        (10.5, 5.8, 10.5, 5.2, 'Чтение/запись', 'solid'),

        # Обработка данных
        (3.5, 5.2, 7, 5.2, 'Исторические\nданные', 'solid'),
        (7, 5.2, 7, 5.8, 'Расчет β', 'solid'),

        # Оповещения
        (10.5, 3.8, 10.5, 4.5, 'Данные для\nанализа', 'solid'),
        (10.5, 4.5, 7, 2.6, 'Оповещения', 'solid'),

        # Фоновые процессы
        (10.5, 6.8, 3.5, 6.2, 'Рекалибрация β\n(каждые 24ч)', 'dotted')
    ]

    for x1, y1, x2, y2, label, style in connections:
        # Рисуем стрелку
        if style == 'dashed':
            linestyle = '--'
            arrowstyle = '->'
        elif style == 'dotted':
            linestyle = ':'
            arrowstyle = '->'
        else:
            linestyle = '-'
            arrowstyle = '->'

        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=arrowstyle, lw=2,
                                    color=colors['arrows'], linestyle=linestyle,
                                    connectionstyle="arc3,rad=0.1"))

        # Добавляем подписи
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, label, ha='center', va='center',
                    fontsize=8, bbox=dict(boxstyle="round,pad=0.2",
                                          facecolor="white", alpha=0.9))

    # Добавляем легенду
    legend_elements = [
        patches.Patch(facecolor=colors['main_components'], label='Основные компоненты'),
        patches.Patch(facecolor=colors['support_components'], label='Вспомогательные компоненты'),
        patches.Patch(facecolor=colors['database'], label='База данных'),
        patches.Patch(facecolor=colors['external'], label='Внешние сервисы'),
        patches.Patch(facecolor=colors['output'], label='Выходные данные'),
        lines.Line2D([0], [0], color=colors['arrows'], lw=2, label='Поток данных'),
        lines.Line2D([0], [0], color=colors['arrows'], lw=2, linestyle='--', label='Внешние подключения'),
        lines.Line2D([0], [0], color=colors['arrows'], lw=2, linestyle=':', label='Фоновые процессы')
    ]

    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 0.02),
              ncol=4, fontsize=8, framealpha=0.9)

    plt.title('Архитектура системы мониторинга независимых движений ETH/USDT\n',
              fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('architecture_detailed.png', dpi=300, bbox_inches='tight')
    plt.show()

    print("Диаграмма архитектуры сохранена как 'architecture_detailed.png'")
    print("\nКомпоненты системы:")
    print("1. Binance WebSocket Client - получение данных в реальном времени")
    print("2. Real-time Monitor - обработка потоковых данных")
    print("3. Database PostgreSQL - хранение данных и коэффициентов")
    print("4. Binance REST API Client - загрузка исторических данных")
    print("5. Beta Calculator - расчет регрессионной модели")
    print("6. Alert Generator - генерация оповещений")


if __name__ == "__main__":
    create_architecture_diagram()