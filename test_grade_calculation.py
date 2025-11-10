"""
Script de prueba para verificar el cálculo de notas según norma chilena
"""

from src.core.grade_calculator import GradeCalculator
from decimal import Decimal, ROUND_HALF_UP

# Crear calculador con parámetros estándar chilenos
calc = GradeCalculator(
    max_score=100,
    passing_percentage=60.0,
    min_grade=1.0,
    max_grade=7.0,
    passing_grade=4.0
)

print("=" * 80)
print("ANÁLISIS DE DISCREPANCIA EN CÁLCULO DE NOTAS")
print("=" * 80)
print("\nCaso reportado: 21 puntos de 100")
print("-" * 80)

# Caso específico: 21 puntos
score = 21
grade = calc.calculate_grade(score)

# Calcular manualmente
manual_calc = 1.0 + ((21 / 60.0) * (4.0 - 1.0))
print(f"Calculo manual: 1.0 + ((21 / 60.0) x 3.0) = {manual_calc}")
print(f"Resultado sin redondear: {manual_calc}")
print(f"Resultado con round() de Python: {round(manual_calc, 1)}")

# Redondeo "half up" (usado en el generador web)
decimal_value = Decimal(str(manual_calc))
rounded_half_up = float(decimal_value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
print(f"Resultado con redondeo 'half up': {rounded_half_up}")

print(f"\nPrograma actual devuelve: {grade}")
print(f"Tabla escaladenotas.cl dice: 2.1")
print(f"Diferencia: {abs(grade - 2.1):.1f}")

print("\n" + "=" * 80)
print("DIAGNÓSTICO DEL PROBLEMA")
print("=" * 80)
print("\nEl problema es el TIPO DE REDONDEO:")
print("- Python round(): usa 'round half to even' (IEEE 754)")
print("  -> 2.05 redondea a 2.0 (porque 2.0 es par)")
print("- Generador web: usa 'round half up' (redondeo escolar)")
print("  -> 2.05 redondea a 2.1 (siempre hacia arriba en .5)")

print("\n" + "=" * 80)
print("CASOS DE PRUEBA - Comparación de redondeos")
print("=" * 80)

# Casos problemáticos con .05, .15, .25, etc.
test_values = [20, 21, 22, 23, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 100]

print("\nPuntaje | Sin redondear | Python round() | Round Half Up | Tabla Web")
print("-" * 80)

for score in test_values:
    grade_current = calc.calculate_grade(score)

    # Calcular sin redondear
    if score < 60:
        raw = 1.0 + ((score / 60.0) * 3.0)
    else:
        raw = 4.0 + (((score - 60.0) / 40.0) * 3.0)

    # Redondeo half up
    decimal_value = Decimal(str(raw))
    half_up = float(decimal_value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))

    # Nota esperada según la tabla (extraída de la imagen)
    expected = {
        0: 1.0, 20: 2.0, 21: 2.1, 22: 2.1, 23: 2.2, 30: 2.5,
        35: 2.8, 40: 3.0, 45: 3.3, 50: 3.5, 55: 3.8, 60: 4.0,
        70: 4.8, 80: 5.5, 90: 6.3, 100: 7.0
    }

    match = "OK" if score not in expected or abs(half_up - expected[score]) < 0.01 else "X"
    web_value = expected.get(score, "?")

    print(f"  {score:3d}   |    {raw:.4f}     |     {grade_current:.1f}      |     {half_up:.1f}      |    {web_value}    {match}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
El programa usa round() de Python que implementa 'round half to even' (IEEE 754).
El generador web usa 'round half up' (redondeo matematico tradicional).

RECOMENDACION:
Cambiar el redondeo en grade_calculator.py para usar 'round half up'
y ser consistente con el estandar educacional chileno.
""")
print("=" * 80)
