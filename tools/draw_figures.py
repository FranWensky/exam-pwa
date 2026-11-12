"""Draw the original, editable SVG study diagrams for the LAiAG paragraphs."""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "figures"
INK, BLUE, TEAL, RUST, GRAY = "#182639", "#2056a3", "#00796f", "#a74412", "#50637d"
LINE, BG = "#d2deeb", "#f0f4f8"


def label(x, y, value, color=INK, size=25, bold=False, anchor="start"):
    weight = 700 if bold else 400
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{escape(value)}</text>')


def line(x, y, u, v, color=GRAY, width=3, dash=False):
    dashes = ' stroke-dasharray="7 6"' if dash else ""
    return f'<path d="M{x},{y} L{u},{v}" fill="none" stroke="{color}" stroke-width="{width}"{dashes}/>'


def arrow(x, y, u, v, color=BLUE):
    return (f'<path d="M{x},{y} L{u},{v}" fill="none" stroke="{color}" stroke-width="4" '
            f'marker-end="url(#tip-{color[1:]})"/>')


def dot(x, y, color=INK):
    return f'<circle cx="{x}" cy="{y}" r="5" fill="{color}"/>'


def rect(x, y, w, h, fill, border="none", radius=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{border}"/>'


def arc(x, y, r, large, sweep, u, v, color=RUST):
    return f'<path d="M{x},{y} A{r},{r} 0 {large},{sweep} {u},{v}" fill="none" stroke="{color}" stroke-width="3" marker-end="url(#tip-{color[1:]})"/>'


def matrix(x, y, rows, marks=None, step=53):
    marks = marks or {}
    w, h = len(rows[0]) * step + 12, len(rows) * 43 + 8
    out = [f'<path d="M{x+10},{y} h-10 v{h} h10 M{x+w-10},{y} h10 v{h} h-10" fill="none" stroke="{INK}" stroke-width="2"/>']
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            u, v = x + 6 + step * j, y + 4 + 43 * i
            color = marks.get((i, j))
            if color:
                out.append(rect(u + 2, v, step - 4, 40, {BLUE: "#e5eefb", TEAL: "#dff4ef", RUST: "#f9eadf"}[color], radius=5))
            out.append(label(u + step / 2, v + 28, str(val), color or INK, 24, bool(color), "middle"))
    return "".join(out)


def panel(x, y, w, h, title, body):
    return (f'<g transform="translate({x} {y})">{rect(0, 0, w, h, "#fff", LINE)}'
            f'{label(24, 42, title, size=27, bold=True)}{body}</g>')


def figure(number, title, panels, height=510):
    inner = "".join(panel(*p) for p in panels)
    tips = "".join(f'<marker id="tip-{color[1:]}" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="4" markerHeight="4" '
                   f'orient="auto"><path d="M0 0L10 4L0 8z" fill="{color}"/></marker>'
                   for color in (BLUE, TEAL, RUST, GRAY))
    content = (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" '
               'font-family="Segoe UI, DejaVu Sans, sans-serif">\n'
               f'<defs>{tips}</defs>\n'
               f'{rect(0,0,1200,height,BG)}{label(46, 64, title, size=38, bold=True)}\n{inner}\n</svg>\n')
    (OUT / f"algebra-{number}.svg").write_text(content, encoding="utf-8", newline="\n")


def pair(number, title, left, right):
    figure(number, title, [(40, 99, 550, 371, *left), (610, 99, 550, 371, *right)])


def matrices():
    row = {(1, j): BLUE for j in range(3)}
    col = {(i, 1): TEAL for i in range(2)}
    pair(1, "Матрицы и действия над ними",
         ("Строка, столбец и элемент",
          matrix(173, 109, (("a₁₁", "a₁₂", "a₁₃"), ("a₂₁", "a₂₂", "a₂₃")), row | col | {(1, 1): RUST}, 64)
          + label(24, 182, "строка 2", BLUE) + arrow(131, 173, 171, 173)
          + label(227, 82, "столбец 2", TEAL) + arrow(275, 89, 275, 109, TEAL)
          + label(24, 260, "a₂₂ — на пересечении строки и столбца.")
          + label(24, 307, "Размер A: 2 × 3. Размер Aᵀ: 3 × 2.", GRAY)),
         ("Умножение: строка на столбец",
          label(80, 91, "A", BLUE, bold=True) + label(323, 91, "B", TEAL, bold=True)
          + matrix(57, 111, ((1, 2), (3, 4)), {(0, 0): BLUE, (0, 1): BLUE})
          + label(211, 179, "×", size=36)
          + matrix(286, 111, ((2, 0), (1, 3)), {(0, 1): TEAL, (1, 1): TEAL})
          + label(24, 257, "Элемент (AB)₁₂:", RUST, bold=True)
          + label(24, 301, "1·0 + 2·3 = 6.", size=31)))


def determinants():
    grid = matrix(72, 93, ((1, 2, 3, 1, 2), (0, 4, 5, 0, 4), (1, 0, 6, 1, 0)), step=63)
    lines = "".join(line(109.5+63*j, 121, 235.5+63*j, 207, BLUE, 2) for j in range(3))
    reverse = "".join(line(235.5+63*j, 121, 109.5+63*j, 207, RUST, 2, True) for j in range(3))
    diagonals = f'<g opacity=".32">{lines}{reverse}</g>' + line(267, 95, 267, 225, GRAY, 1, True)
    pair(2, "Определители: диагонали и миноры",
         ("Правило Саррюса для 3 × 3", grid + diagonals
          + label(24, 255, "↘  1·4·6 + 2·5·1 + 3·0·0 = 34", BLUE)
          + label(24, 295, "↙  3·4·1 + 1·5·0 + 2·0·6 = 12", RUST)
          + label(24, 338, "det A = 34 − 12 = 22.", bold=True)),
         ("Минор и алгебраическое дополнение",
          matrix(35, 99, ((1, 2, 3), (0, 4, 5), (1, 0, 6)), {(0, 1): RUST})
          + line(38, 123, 203, 123, RUST, 2, True) + line(120, 101, 120, 234, RUST, 2, True)
          + arrow(232, 170, 299, 170)
          + matrix(321, 123, ((0, 5), (1, 6)))
          + label(24, 263, "Для M₁₂ вычёркиваем строку 1 и столбец 2.", size=23)
          + label(24, 302, "M₁₂ = 0·6 − 5·1 = −5.")
          + label(24, 340, "A₁₂ = (−1)¹⁺²·M₁₂ = 5.", BLUE, bold=True)))


def inverse():
    pair(3, "Два способа найти обратную матрицу",
         ("Через присоединённую матрицу",
          label(36, 150, "A =", size=30) + matrix(103, 94, ((2, 1), (1, 1)))
          + label(261, 151, "det A = 1 ≠ 0", TEAL, bold=True)
          + label(36, 235, "A⁻¹ = adj A / det A")
          + label(36, 307, "A⁻¹ =", size=30) + matrix(124, 255, ((1, "−1"), ("−1", 2)))),
         ("Метод Гаусса: [A | I] → [I | A⁻¹]",
          matrix(32, 105, ((2, 1, 1, 0), (1, 1, 0, 1)), {(i, j): TEAL for i in range(2) for j in (2, 3)}, 46)
          + line(130, 109, 130, 195, TEAL, 2) + arrow(233, 154, 292, 154)
          + matrix(310, 105, ((1, 0, 1, "−1"), (0, 1, "−1", 2)), {(i, j): BLUE for i in range(2) for j in (2, 3)}, 47)
          + line(410, 109, 410, 195, BLUE, 2)
          + label(24, 243, "Исключаем лишние коэффициенты.")
          + label(24, 289, "Применяем операции к обеим половинам.", GRAY, size=23)
          + label(24, 333, "Справа получается та же A⁻¹.", BLUE, bold=True)))


def rank():
    pair(4, "Ранг матрицы: минор и ведущие элементы",
         ("Ненулевой минор второго порядка",
          matrix(47, 89, ((1, 2, 3), (2, 4, 6), (0, 1, 1)), {(i, j): TEAL for i in (0, 2) for j in (0, 1)})
          + arrow(232, 158, 289, 158, TEAL) + matrix(314, 109, ((1, 2), (0, 1)))
          + label(24, 265, "Выбираем строки 1 и 3, столбцы 1 и 2.")
          + label(24, 307, "Минор = 1, значит ранг не меньше 2.", TEAL)
          + label(24, 345, "det A = 0: строка 2 равна 2 · строка 1.", GRAY, 22)),
         ("Ступенчатая форма",
          matrix(60, 101, ((1, 2, 3), (0, 1, 1), (0, 0, 0)), {(0, 0): BLUE, (1, 1): BLUE})
          + arrow(261, 131, 220, 131) + arrow(261, 175, 220, 175)
          + label(275, 160, "две ненулевые", BLUE) + label(275, 191, "строки", BLUE)
          + label(24, 273, "Из строки 2 вычитаем удвоенную строку 1.")
          + label(24, 310, "Затем переносим нулевую строку вниз.", GRAY, 23)
          + label(24, 346, "Два ведущих элемента → rank A = 2.", bold=True)))


def axes(x=70, y=260, u=450, v=87):
    return arrow(x, y, u, y, GRAY) + arrow(x, y, x, v, GRAY)


def systems():
    panels = []
    for i, (title, strokes, text) in enumerate((
        ("Одно решение", line(55, 228, 300, 94, BLUE, 4) + line(55, 94, 300, 228, TEAL, 4) + dot(177.5, 161), "Прямые пересекаются."),
        ("Нет решений", line(50, 194, 278, 88, BLUE, 4) + line(76, 227, 304, 121, TEAL, 4), "Прямые параллельны."),
        ("Бесконечно много", line(50, 228, 300, 88, BLUE, 6) + line(50, 228, 300, 88, TEAL, 3, True), "Прямые совпадают."),
    )):
        panels.append((40+i*380, 99, 360, 286, title, strokes + label(24, 261, text, GRAY, 22)))
    panels.append((40, 405, 1120, 204, "Метод Гаусса: убираем x из второго уравнения",
                   label(24, 104, "x + y = 3", BLUE, 27) + label(24, 154, "2x + 3y = 8", TEAL, 27)
                   + arrow(225, 125, 382, 125) + label(232, 99, "R₂ − 2R₁", BLUE, 24)
                   + label(421, 104, "x + y = 3", BLUE, 27) + label(421, 154, "y = 2", TEAL, 27)
                   + arrow(623, 125, 780, 125) + label(637, 99, "Подстановка", BLUE, 24)
                   + label(819, 136, "x = 1, y = 2", RUST, 32, True)))
    figure(5, "Системы линейных уравнений на плоскости", panels, 649)


def homogeneous():
    pair(6, "Однородная система и сдвиг решений",
         ("Однородное уравнение x + y = 0",
          axes(267, 170, 470, 72) + line(108, 170, 267, 170) + line(267, 170, 267, 263)
          + line(172, 75, 362, 265, BLUE, 4) + dot(267, 170)
          + arrow(267, 170, 328, 231, BLUE) + label(334, 229, "v = (1, −1)", BLUE, 23)
          + label(470, 194, "x") + label(243, 84, "y") + label(240, 191, "0", size=20)
          + label(24, 313, "Все решения: t·(1, −1), t ∈ ℝ.")
          + label(24, 345, "ФСР состоит из одного вектора v.", BLUE, 23)),
         ("Неоднородное уравнение x + y = 2",
          axes(246, 184, 470, 72) + line(102, 184, 246, 184) + line(246, 184, 246, 259)
          + line(161, 99, 327, 265, BLUE, 3, True)
          + line(255, 81, 439, 265, TEAL, 4)
          + dot(246, 184) + dot(302, 128, TEAL) + arrow(247, 183, 297, 133, RUST)
          + label(311, 121, "p = (1, 1)", TEAL, 22)
          + label(471, 208, "x") + label(224, 84, "y") + label(222, 205, "0", size=20)
          + label(24, 313, "Все решения: p + t·(1, −1), t ∈ ℝ.")
          + label(24, 345, "Сдвиг на частное решение p.", TEAL, 23)))


def polar():
    pair(8, "Полярная система координат",
         ("Радиус, угол и проекции",
          axes(85, 253, 481, 78) + arrow(85, 253, 341, 118)
          + line(341, 118, 341, 253, TEAL, 3, True) + line(85, 253, 341, 253, TEAL, 3)
          + arc(152, 253, 67, 0, 0, 144, 222) + dot(85, 253) + dot(341, 118)
          + label(355, 114, "M(r, φ)", BLUE) + label(208, 172, "r", BLUE)
          + label(161, 244, "φ", RUST) + label(80, 282, "O") + label(335, 282, "N")
          + label(455, 283, "u, x", GRAY, 22) + label(350, 194, "y", TEAL)
          + label(24, 335, "x = r cos φ,   y = r sin φ.", bold=True)),
         ("Пример: точка в III четверти",
          axes(257, 147, 468, 65) + line(87, 147, 257, 147) + line(257, 147, 257, 288)
          + arrow(257, 147, 190, 263, BLUE) + line(190, 147, 190, 263, TEAL, 2, True)
          + line(190, 263, 257, 263, TEAL, 2, True) + arc(311, 147, 54, 1, 0, 230, 194)
          + dot(190, 263) + label(60, 279, "M(−1, −√3)", BLUE, 24)
          + label(182, 134, "−1", TEAL, 20) + label(272, 275, "−√3", TEAL, 20)
          + label(471, 174, "x") + label(272, 79, "y") + label(324, 168, "φ", RUST)
          + label(24, 335, "r = 2,   φ = 4π/3.", bold=True)))


def dot_product():
    pair(9, "Скалярное произведение и проекция",
         ("Угол и проекция на направление a",
          arrow(73, 249, 476, 249, BLUE) + arrow(73, 249, 345, 104, TEAL)
          + line(345, 104, 345, 249, GRAY, 2, True) + line(73, 249, 345, 249, RUST, 4)
          + line(330, 249, 330, 235, GRAY, 2) + line(330, 235, 345, 235, GRAY, 2)
          + arc(138, 249, 65, 0, 0, 130, 219) + dot(73, 249)
          + label(150, 239, "α", RUST) + label(473, 278, "a", BLUE, 28, True)
          + label(346, 96, "b", TEAL, 28, True)
          + label(128, 283, "|b| cos α", RUST) + label(24, 335, "a · b = |a| · (|b| cos α).", bold=True)),
         ("Перпендикулярные векторы",
          arrow(122, 248, 456, 248, BLUE) + arrow(122, 248, 122, 92, TEAL)
          + line(122, 223, 147, 223, RUST, 2) + line(147, 223, 147, 248, RUST, 2)
          + dot(122, 248) + label(166, 215, "90°", RUST)
          + label(457, 276, "a", BLUE, 28, True) + label(91, 95, "b", TEAL, 28, True)
          + label(24, 313, "cos 90° = 0, поэтому a · b = 0.")
          + label(24, 345, "Для ненулевых векторов верно и обратное.", GRAY, 22)))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for draw in (matrices, determinants, inverse, rank, systems, homogeneous, polar, dot_product):
        draw()
