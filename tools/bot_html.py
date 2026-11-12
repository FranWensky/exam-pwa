import re
from html import escape, unescape


TELEGRAM_LIMIT = 4096
TOKEN = re.compile(r"</?(?:b|i|u|s|code|pre)>|&(?:#[0-9]+|#x[0-9a-f]+|[a-z][a-z0-9]+);", re.I)


def parse_html(source: str) -> tuple[str, list[tuple[int, tuple[str, ...]]]]:
    """Keep Telegram's basic tags and treat other angle brackets as literal text."""
    stack: list[str] = []
    pieces: list[str] = []
    runs: list[tuple[int, tuple[str, ...]]] = []
    length = 0

    def add(value: str) -> None:
        nonlocal length
        if value:
            length += len(value)
            pieces.append(value)
            style = tuple(stack)
            if runs and runs[-1][1] == style:
                runs[-1] = (length, style)
            else:
                runs.append((length, style))

    cursor = 0
    for match in TOKEN.finditer(source):
        add(source[cursor:match.start()])
        token = match.group()
        cursor = match.end()
        if token.startswith("&"):
            add(unescape(token))
            continue
        tag = token.strip("</>").lower()
        if token.startswith("</"):
            if tag in stack:
                while stack.pop() != tag:
                    pass
            continue
        if not stack or (
            tag not in stack and not {"code", "pre"}.intersection((*stack, tag))
        ):
            stack.append(tag)
    add(source[cursor:])
    return "".join(pieces), runs


def split_html(source: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    """Split on paragraphs, lines, or spaces and reopen formatting in each chunk."""
    if limit < 2:
        raise ValueError("Лимит должен вмещать как минимум два символа UTF-16.")
    visible, runs = parse_html(source)
    result: list[str] = []
    start = run_index = 0
    while start < len(visible):
        end, units = start, 0
        while end < len(visible):
            units += 1 + (ord(visible[end]) > 0xFFFF)
            if units > limit:
                break
            end += 1

        if end < len(visible):
            for separator in ("\n\n", "\n", " ", "\t"):
                boundary = visible.rfind(separator, start, end)
                if boundary > start:
                    end = boundary + len(separator)
                    break

        offset = start
        chunk: list[str] = []
        while offset < end:
            run_end, tags = runs[run_index]
            until = min(run_end, end)
            chunk.extend(f"<{tag}>" for tag in tags)
            chunk.append(escape(visible[offset:until], quote=False))
            chunk.extend(f"</{tag}>" for tag in reversed(tags))
            offset = until
            if offset == run_end:
                run_index += 1
        if visible[start:end].strip():
            result.append("".join(chunk))
        start = end
    return result


def parse_cards(text: str) -> list[tuple[str, str]]:
    cards = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        question, sep, answer = line.partition(" | ")
        if not sep:
            question, sep, answer = line.partition("|")
        question, answer = question.strip(), answer.strip()
        if not sep or not all(parse_html(part)[0].strip() for part in (question, answer)):
            raise ValueError(f"Строка {number}: ожидается «Вопрос | Ответ».")
        cards.append((question, answer))
    return cards
