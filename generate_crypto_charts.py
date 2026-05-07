#!/usr/bin/env python3
"""
Скрипт для генерации графиков к исследованию криптографии в блокчейне
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle, Polygon
import os

# Создаем директорию для графиков
os.makedirs('crypto_charts', exist_ok=True)

# Настройка стиля
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16

# ============================================================================
# График 1: Сравнение производительности алгоритмов цифровой подписи
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 8))

algorithms = ['ECDSA P-256', 'ECDSA P-384', 'Ed25519', 'RSA-2048', 'RSA-3072']
sign_speed = [100, 65, 120, 25, 12]  # операций в секунду (нормализовано)
verify_speed = [95, 60, 115, 30, 15]  # операций в секунду (нормализовано)

x = np.arange(len(algorithms))
width = 0.35

bars1 = ax.bar(x - width/2, sign_speed, width, label='Подписание', color='#2E86AB', alpha=0.8)
bars2 = ax.bar(x + width/2, verify_speed, width, label='Верификация', color='#A23B72', alpha=0.8)

ax.set_ylabel('Производительность (операций/сек, нормализовано)')
ax.set_title('Сравнение производительности алгоритмов цифровой подписи\n(для транзакций блокчейна)', fontsize=16, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(algorithms, rotation=15)
ax.legend(loc='upper right')
ax.set_ylim(0, 130)

# Добавляем значения на столбцы
for bar in bars1 + bars2:
    height = bar.get_height()
    ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('crypto_charts/signature_performance.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ График 1: signature_performance.png")

# ============================================================================
# График 2: Стойкость криптографических алгоритмов
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 8))

algos = ['ECDSA P-256', 'ECDSA P-384', 'AES-128', 'AES-256', 'SHA-256', 'RSA-2048', 'RSA-3072']
security_bits = [128, 192, 128, 256, 128, 112, 128]
colors = ['#28A745' if bits >= 128 else '#FFC107' for bits in security_bits]

bars = ax.bar(algos, security_bits, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

ax.axhline(y=128, color='red', linestyle='--', linewidth=2, label='Минимальный рекомендуемый уровень (128 бит)')
ax.axhline(y=192, color='orange', linestyle=':', linewidth=2, label='Повышенный уровень безопасности (192 бит)')
ax.axhline(y=256, color='green', linestyle='-.', linewidth=2, label='Максимальный уровень (256 бит)')

ax.set_ylabel('Биты стойкости')
ax.set_title('Стойкость криптографических алгоритмов\n(эквивалент симметричного шифрования)', fontsize=16, pad=20)
ax.set_ylim(0, 280)
ax.legend(loc='upper right')
ax.set_xticklabels(algos, rotation=25)

# Добавляем значения
for bar, bits in zip(bars, security_bits):
    height = bar.get_height()
    ax.annotate(f'{bits} бит',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('crypto_charts/security_levels.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ График 2: security_levels.png")

# ============================================================================
# График 3: Распределение методов защиты в системе
# ============================================================================

fig, ax = plt.subplots(figsize=(12, 10))

categories = ['TLS/mTLS', 'ECDSA Подписи', 'SHA-256 Хеши', 'RBAC Контроль', 'X.509 Сертификаты', 'Шифрование IPFS']
implementation = [100, 100, 100, 100, 100, 0]  # Проценты реализации
importance = [95, 98, 95, 85, 90, 92]  # Важность для безопасности

x = np.arange(len(categories))
width = 0.35

bars1 = ax.bar(x - width/2, implementation, width, label='Текущая реализация (%)', 
               color=['#28A745' if i < 5 else '#DC3545' for i in range(len(categories))], alpha=0.8)
bars2 = ax.bar(x + width/2, importance, width, label='Важность для безопасности (%)', color='#17A2B8', alpha=0.6)

ax.set_ylabel('Проценты')
ax.set_title('Анализ реализации методов криптографической защиты\nв блокчейн-системе Hyperledger Fabric', fontsize=16, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(categories, rotation=30, ha='right')
ax.legend(loc='lower right')
ax.set_ylim(0, 110)

# Линия целевого уровня
ax.axhline(y=100, color='gold', linestyle='--', linewidth=2, label='Целевой уровень (100%)', alpha=0.7)

for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height}%',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('crypto_charts/protection_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ График 3: protection_analysis.png")

# ============================================================================
# График 4: Эволюция размеров ключей (исторический тренд)
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 8))

years = [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030]
rsa_key_sizes = [512, 768, 1024, 1536, 2048, 2048, 3072, 3072, 4096]
ecdsa_key_sizes = [160, 192, 224, 256, 256, 384, 384, 512, 512]

ax.plot(years, rsa_key_sizes, marker='o', linewidth=2.5, markersize=10, 
        label='RSA (бит)', color='#DC3545', markerfacecolor='white', markeredgewidth=2)
ax.plot(years, ecdsa_key_sizes, marker='s', linewidth=2.5, markersize=10,
        label='ECDSA (бит)', color='#007BFF', markerfacecolor='white', markeredgewidth=2)

ax.fill_between(years, rsa_key_sizes, alpha=0.2, color='#DC3545')
ax.fill_between(years, ecdsa_key_sizes, alpha=0.2, color='#007BFF')

ax.set_xlabel('Год')
ax.set_ylabel('Размер ключа (бит)')
ax.set_title('Эволюция размеров криптографических ключей\n(рекомендации NIST и индустрии)', fontsize=16, pad=20)
ax.legend(loc='upper left')
ax.set_xticks(years)
ax.grid(True, alpha=0.3)

# Аннотации
ax.annotate('Переход на\nECDSA', xy=(2010, 2048), xytext=(2003, 2200),
            arrowprops=dict(arrowstyle='->', color='black'), fontsize=10)
ax.annotate('Постквантовая\nкриптография', xy=(2025, 3500), xytext=(2027, 3800),
            arrowprops=dict(arrowstyle='->', color='black'), fontsize=10)

plt.tight_layout()
plt.savefig('crypto_charts/key_evolution.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ График 4: key_evolution.png")

# ============================================================================
# График 5: Сравнение времени выполнения операций
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 8))

operations = ['SHA-256\n(хеш 1KB)', 'ECDSA\n(подпись)', 'ECDSA\n(верификация)', 
              'AES-256\n(шифрование 1KB)', 'RSA-2048\n(подпись)', 'RSA-2048\n(верификация)']
time_microseconds = [2.5, 45, 52, 1.8, 380, 12]  # микросекунды (примерные значения)

colors = ['#28A745', '#DC3545', '#DC3545', '#007BFF', '#FFC107', '#FFC107']

bars = ax.bar(operations, time_microseconds, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

ax.set_ylabel('Время выполнения (микросекунды, логарифмическая шкала)')
ax.set_title('Сравнение времени выполнения криптографических операций', fontsize=16, pad=20)
ax.set_yscale('log')
ax.set_ylim(0.5, 1000)

# Добавляем значения
for bar, time in zip(bars, time_microseconds):
    height = bar.get_height()
    ax.annotate(f'{time} μs',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('crypto_charts/operation_time.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ График 5: operation_time.png")

# ============================================================================
# График 6: Угрозы безопасности и меры защиты
# ============================================================================

fig, ax = plt.subplots(figsize=(16, 10))

threats = ['Перехват данных', 'Подделка транзакций', 'Несанкционированный доступ', 
           'Утечка из IPFS', 'Потеря ключей', 'DDoS-атаки']
risk_level = [85, 90, 75, 70, 65, 60]  # Уровень риска (0-100)
protection_level = [95, 98, 90, 0, 50, 70]  # Уровень защиты (0-100)

x = np.arange(len(threats))
width = 0.35

bars1 = ax.bar(x - width/2, risk_level, width, label='Уровень риска', color='#DC3545', alpha=0.7)
bars2 = ax.bar(x + width/2, protection_level, width, label='Уровень защиты', color='#28A745', alpha=0.7)

ax.set_ylabel('Уровень (0-100)')
ax.set_title('Матрица угроз безопасности и эффективности мер защиты\nв блокчейн-системе', fontsize=16, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(threats, rotation=25, ha='right')
ax.legend(loc='upper right')
ax.set_ylim(0, 110)

# Добавляем значения
for bar in bars1:
    height = bar.get_height()
    ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

for bar in bars2:
    height = bar.get_height()
    ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10, fontweight='bold')

# Зона внимания
ax.axhspan(70, 100, alpha=0.1, color='red', label='Высокий приоритет')

plt.tight_layout()
plt.savefig('crypto_charts/threat_matrix.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ График 6: threat_matrix.png")

# ============================================================================
# График 7: Постквантовая криптография - сравнение размеров
# ============================================================================

fig, ax = plt.subplots(figsize=(14, 8))

categories_pqc = ['Классический\nECDSA P-256', 'ML-DSA-65\n(Dilithium)', 'SLH-DSA\n(SHA2-128s)', 
                  'Классический\nRSA-3072', 'ML-KEM-768\n(Kyber)']
key_sizes = [32, 2592, 32, 384, 1088]  # байты
signature_sizes = [64, 3309, 7856, 384, 0]  # байты

x = np.arange(len(categories_pqc))
width = 0.4

bars1 = ax.bar(x - width/2, key_sizes, width, label='Размер ключа (байты)', color='#6F42C1', alpha=0.8)
bars2 = ax.bar(x + width/2, signature_sizes, width, label='Размер подписи (байты)', color='#FD7E14', alpha=0.8)

ax.set_ylabel('Размер (байты)')
ax.set_title('Сравнение размеров ключей и подписей:\nклассические vs постквантовые алгоритмы', fontsize=16, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(categories_pqc, rotation=15)
ax.legend(loc='upper left')
ax.set_yscale('log')

# Добавляем значения
for bar, size in zip(bars1, key_sizes):
    height = bar.get_height()
    if size > 0:
        ax.annotate(f'{size}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

for bar, size in zip(bars2, signature_sizes):
    height = bar.get_height()
    if size > 0:
        ax.annotate(f'{size}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('crypto_charts/pqc_comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ График 7: pqc_comparison.png")

# ============================================================================
# График 8: Архитектура системы шифрования
# ============================================================================

fig, ax = plt.subplots(figsize=(16, 12))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')
ax.set_title('Архитектура многоуровневой системы криптографической защиты\nблокчейн-системы Hyperledger Fabric', fontsize=16, pad=30)

# Уровни защиты
levels = [
    {'y': 85, 'name': 'Уровень 4: Прикладной', 'color': '#28A745', 'elements': ['RBAC', 'Шифрование документов', 'Управление сессиями']},
    {'y': 65, 'name': 'Уровень 3: Транспортный (TLS 1.3)', 'color': '#007BFF', 'elements': ['mTLS', 'AES-256-GCM', 'Сертификаты X.509']},
    {'y': 45, 'name': 'Уровень 2: Блокчейн (Fabric)', 'color': '#FFC107', 'elements': ['ECDSA P-256', 'SHA-256', 'MSP', 'Smart Contract']},
    {'y': 25, 'name': 'Уровень 1: Хранение данных', 'color': '#DC3545', 'elements': ['CouchDB Encryption', 'IPFS + Шифрование', 'Файловая система']}
]

for level in levels:
    # Рисуем прямоугольник уровня
    rect = Rectangle((5, level['y']-10), 90, 20, 
                     facecolor=level['color'], alpha=0.2, 
                     edgecolor=level['color'], linewidth=2, label=level['name'])
    ax.add_patch(rect)
    
    # Название уровня
    ax.text(50, level['y']+5, level['name'], ha='center', va='center', 
            fontsize=13, fontweight='bold', color=level['color'])
    
    # Элементы уровня
    for i, elem in enumerate(level['elements']):
        x_pos = 20 + i * 25
        circle = Circle((x_pos, level['y']-5), 8, facecolor=level['color'], alpha=0.6, edgecolor='black')
        ax.add_patch(circle)
        ax.text(x_pos, level['y']-5, elem, ha='center', va='center', 
                fontsize=10, color='black', fontweight='bold')

# Стрелки между уровнями
for i in range(len(levels)-1):
    y_start = levels[i]['y'] - 10
    y_end = levels[i+1]['y'] + 10
    ax.annotate('', xy=(50, y_end), xytext=(50, y_start),
                arrowprops=dict(arrowstyle='->', color='gray', linewidth=2))

# Легенда
ax.text(50, 5, 'Данные защищены на всех уровнях стека', ha='center', va='center', 
        fontsize=14, fontstyle='italic', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('crypto_charts/architecture_diagram.png', dpi=300, bbox_inches='tight')
plt.close()

print("✓ График 8: architecture_diagram.png")

print("\n✅ Все графики успешно созданы в директории 'crypto_charts/'")
print("\nСписок файлов:")
for f in sorted(os.listdir('crypto_charts')):
    print(f"  - {f}")
