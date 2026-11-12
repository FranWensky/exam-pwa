import re
from dataclasses import dataclass, field
from html import escape, unescape
from pathlib import Path

from bot_html import parse_cards, parse_html


SUBJECTS = {1: "Математический анализ", 2: "Линейная алгебра и аналитическая геометрия", 3: "Основы алгоритмизации и программирования"}
PARAGRAPH = re.compile(r"§\s*(\d+)\.\s*(.+)")
BLOCK2 = "БЛОК 2. КАРТОЧКИ ДЛЯ ТРЕНИРОВКИ"
MEMO = "Памятка. Способы раскрытия неопределённостей"


@dataclass
class Topic:
    subject: int
    section: str | None
    title: str
    body: str
    cards: list[tuple[str, str]] = field(default_factory=list)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def label(line: str) -> str:
    return re.sub(r"^#{1,4}\s+", "", line.strip()).removeprefix("<b>").removesuffix("</b>").strip("*")


def split_heading(source: str, marker: str) -> tuple[str, str]:
    for match in re.finditer(r"(?m)^.+$", source):
        if label(match[0]) == marker:
            return source[:match.start()].strip(), source[match.end():].strip()
    raise ValueError(f"Не найден заголовок «{marker}».")


def paragraph_parts(source: str):
    """Read whole-line headings and carry forward the current section."""
    section = None
    title = None
    body = []
    for line in source.splitlines():
        heading = label(line)
        match = PARAGRAPH.fullmatch(heading)
        if heading.startswith(("Раздел ", "Раздел:")) or match:
            if title:
                yield title, section, "\n".join(body).strip()
                title, body = None, []
            if match:
                title = f"§ {match[1]}. {match[2]}"
            else:
                section = heading
        elif title:
            body.append(line)
    if title:
        yield title, section, "\n".join(body).strip()


def assign_card_groups(source: str, groups: list[tuple[Topic, str]]) -> None:
    cards = parse_cards(source)
    offsets = []
    for topic, first_question in groups:
        start = offsets[-1] + 1 if offsets else 0
        index = next((i for i in range(start, len(cards)) if cards[i][0] == first_question), None)
        if index is None:
            raise ValueError(f"«{topic.title}»: не найден первый вопрос «{first_question}».")
        offsets.append(index)
    if offsets[0] != 0:
        raise ValueError("Перед первой группой остались карточки без темы.")
    for (topic, _), start, end in zip(groups, offsets, offsets[1:] + [len(cards)]):
        topic.cards.extend(cards[start:end])


def matan(source: str) -> list[Topic]:
    source = re.sub(r"(?m)^```(?:html|text)?\s*$", "", source).strip()
    theory, cards = split_heading(source, BLOCK2)
    theory, summary = split_heading(theory, "ПОДЫТОГ РАЗДЕЛА I — §0–§7")
    summary, memo = split_heading(summary, MEMO)
    summaries = {PARAGRAPH.fullmatch(title)[1]: body for title, _, body in paragraph_parts(summary)}
    topics = []
    for title, section, body in paragraph_parts(theory):
        number = PARAGRAPH.fullmatch(title)[1]
        if number in summaries:
            body += "\n\n<b>Краткий итог</b>\n\n" + summaries.pop(number)
        topics.append(Topic(1, section, title, body))
    if summaries or len(topics) != 9:
        raise ValueError("В конспекте по матанализу ожидались параграфы § 0–8 и подытог § 0–7.")
    topics.append(Topic(1, topics[4].section, MEMO, memo))
    # This export lists all cards in one block. Its main and recap groups follow
    # the paragraphs in order, and the first question identifies each group.
    anchors = [
        (0, "Какой пример конечного множества приведён в конспекте?"),
        (1, "Какое число называют комплексным?"),
        (2, "Что называется числовой последовательностью?"),
        (3, "Какие многочлены называют биномами (двучленами)?"),
        (4, "Что такое предел функции по Гейне?"),
        (5, "Когда функция непрерывна в точке x₀?"),
        (6, "Что можно сказать о сумме, разности и произведении двух БМФ?"),
        (7, "Что называется наибольшим значением функции на множестве X?"),
        (8, "Чему равно приращение функции в точке x₀?"),
        (0, "Что означают A ∪ B, A ∩ B и A ∖ B?"),
        (1, "Как связаны алгебраическая, тригонометрическая и показательная формы z?"),
        (2, "Как определяется предел последовательности?"),
        (3, "Каков коэффициент при x^(n−k)·aᵏ в биноме Ньютона?"),
        (4, "Как формулируется определение предела по Гейне?"),
        (5, "Как проверить непрерывность в точке?"),
        (6, "Когда α ∼ β и когда α = o(β)?"),
        (7, "Что утверждают теоремы Вейерштрасса для непрерывной функции на отрезке?"),
        (9, "Как раскрывают [∞/∞] в дроби из многочленов?"),
    ]
    assign_card_groups(cards, [(topics[index], question) for index, question in anchors])
    return topics


def lin_alg(source: str, formatted: str = "") -> list[Topic]:
    summary, rest = split_heading(source, "БЛОК 1. ПОЛНАЯ ТЕОРИЯ И ПРИМЕРЫ")
    theory, cards = split_heading(rest, BLOCK2)
    summaries = {
        PARAGRAPH.fullmatch(title)[1]: body.removesuffix("\nЛАиАГ")
        for title, _, body in paragraph_parts(summary)
    }
    topics = []
    for title, section, body in paragraph_parts(theory):
        number = PARAGRAPH.fullmatch(title)[1]
        plain = body.removesuffix("\nЛАиАГ").rstrip()
        body = escape(plain, quote=False)
        html_box = re.search(fr'id="theory{number}"[^>]*>(.*?)</textarea>', formatted, re.S)
        if html_box:
            _, marker, markup = unescape(html_box[1]).partition(f"<b>{title}</b>")
            main, _, captions = plain.partition("\n\nРисунки к § 7")
            if marker and parse_html(markup)[0].split() == main.split():
                body = markup.strip()
                if captions:
                    body += "\n\n" + escape("Рисунки к § 7" + captions, quote=False)
        if number in summaries:
            body += "\n\n<b>Краткая сводка</b>\n\n" + escape(summaries.pop(number), quote=False)
        topics.append(Topic(2, section, title, body))
    anchors = [
        "Что называется числовой матрицей размера m × n?",
        "Что называется определителем, или детерминантом, матрицы?",
        "Какая квадратная матрица называется невырожденной, или неособенной?",
        "Что называется минором k-го порядка матрицы A?",
        "Как записывается система из m линейных уравнений с n неизвестными?",
        "Какая СЛУ называется однородной?",
        "Что называется скалярной величиной?",
        "Чем задаётся полярная система координат на плоскости?",
        "Что такое скалярное произведение двух векторов?",
    ]
    if summaries or len(topics) != len(anchors):
        raise ValueError("В конспекте по ЛАиАГ ожидались параграфы § 1–9 и сводка § 1–6.")
    assign_card_groups(cards, list(zip(topics, anchors)))
    return topics


def programming(source: str) -> list[Topic]:
    pieces = re.split(r"(?m)^<b>БЛОК 1\. ОТВЕТ НА БИЛЕТ</b>\s*$", source)
    if pieces[0].strip() or len(pieces) < 2:
        raise ValueError("Ожидаются блоки ответов на билеты ОАиП.")
    topics = []
    for piece in pieces[1:]:
        theory, cards = split_heading(piece, BLOCK2)
        title, _, body = theory.partition("\n")
        if not re.fullmatch(r"Билет №\s*\d+\. .+", label(title)):
            raise ValueError(f"Не распознан заголовок билета: {title}.")
        topics.append(Topic(3, None, label(title), body.strip(), parse_cards(cards)))
    return topics


def combined(source: str) -> list[Topic]:
    """Read materials.txt with Markdown headings for subjects, sections and topics."""
    topics = []
    subject = section = None
    for match in re.finditer(r"(?ms)^([#]{1,3}) (.+?)\n(.*?)(?=^#{1,3} |\Z)", source):
        marks, title, content = match.groups()
        if marks == "#":
            subject = next((key for key, name in SUBJECTS.items() if name == title), None)
            if subject is None or content.strip():
                raise ValueError(f"Проверьте заголовок предмета «{title}».")
            section = None
        elif marks == "##" and subject in (1, 2) and not content.strip():
            section = title
        elif (marks == "###" and section) or (marks == "##" and subject == 3):
            body, *card_block = re.split(r"(?m)^#### Карточки[ \t]*$", content, maxsplit=1)
            cards = card_block[0] if card_block else ""
            topics.append(Topic(subject, section, title, body.strip(), parse_cards(cards)))
        else:
            raise ValueError(f"Проверьте уровень заголовка «{title}».")
    return topics
