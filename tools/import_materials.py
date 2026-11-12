import argparse
import hashlib
import json
import re
from pathlib import Path

from bot_html import parse_html, split_html
from materials import SUBJECTS, combined, lin_alg, matan, programming, read


APP = Path(__file__).resolve().parents[1]
BLOCKS = re.compile(r"(<pre>[\s\S]*?</pre>)|\n[ \t]*\n+")
HEADING = re.compile(r"<b>[^\n]+</b>")
KINDS = (
    ("definition", re.compile(r"^(?:определени[ея]|основн\w+ поняти\w+)\b", re.I)),
    ("theorem", re.compile(r"^(?:теорем[аы]|лемм[аы]|следствие)\b", re.I)),
    ("proof", re.compile(r"^доказательств[оа]\b", re.I)),
    ("example", re.compile(r"^пример\w*\b", re.I)),
    ("formula", re.compile(r"^формул[аы]\b", re.I)),
)


def identifier(*parts: str) -> str:
    return hashlib.sha256("\x00".join(parts).encode()).hexdigest()[:14]


def safe_html(source: str) -> str:
    return "".join(split_html(source, 1_000_000))


def theory_blocks(source: str, subject: int) -> list[dict[str, str]]:
    blocks = []
    for fragment in BLOCKS.split(safe_html(source)):
        html = fragment.strip() if fragment else ""
        if not html:
            continue
        plain, _ = parse_html(html)
        if html.startswith("<pre>"):
            blocks.append({"kind": "code" if subject == 3 else "formula", "text": plain.strip("\n")})
        elif HEADING.fullmatch(html):
            blocks.append({"kind": "heading", "text": plain})
        else:
            kind = next((kind for kind, prefix in KINDS if prefix.match(plain)), "paragraph")
            blocks.append({"kind": kind, "html": html})
    return blocks


def export(topics) -> dict:
    if {topic.subject for topic in topics} != SUBJECTS.keys():
        raise ValueError("Нужны материалы по всем трём предметам.")
    subjects = {
        number: {"id": str(number), "title": title, "sections": [], "topics": []}
        for number, title in SUBJECTS.items()
    }
    seen_sections = set()
    seen_topics = set()
    for topic in topics:
        subject = subjects[topic.subject]
        section = identifier(subject["id"], topic.section) if topic.section else None
        if section and section not in seen_sections:
            subject["sections"].append({"id": section, "title": topic.section})
            seen_sections.add(section)
        topic_id = identifier(subject["id"], section or "", topic.title)
        blocks = theory_blocks(topic.body, topic.subject)
        if topic_id in seen_topics or not blocks:
            raise ValueError(f"Повторяющаяся тема или пустая теория: {topic.title}")
        seen_topics.add(topic_id)
        cards = [{"question": safe_html(question), "answer": safe_html(answer)}
                 for question, answer in dict.fromkeys(topic.cards)]
        subject["topics"].append({
            "id": topic_id, "section": section, "title": topic.title, "blocks": blocks, "cards": cards,
        })
    return {"version": 1, "subjects": list(subjects.values())}


def main() -> None:
    parser = argparse.ArgumentParser(description="Преобразование конспектов и карточек в данные PWA.")
    parser.add_argument("--source-dir", type=Path, default=Path.cwd())
    parser.add_argument("--materials", type=Path)
    parser.add_argument("--matan", type=Path)
    parser.add_argument("--output", type=Path, default=APP / "data.json")
    args = parser.parse_args()
    folder = args.source_dir
    unified = args.materials or folder / "materials.txt"
    if args.materials or unified.is_file():
        topics = combined(read(unified))
    else:
        algebra_html = folder / "ЛАиАГ — конспект.html"
        topics = (
            matan(read(args.matan or folder / "matan-complete.md"))
            + lin_alg(read(folder / "ЛАиАГ — конспект.txt"), read(algebra_html) if algebra_html.is_file() else "")
            + programming(read(folder / "ОАиП — теоретические билеты для Telegram.txt"))
        )
    data = export(topics)
    args.output.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    for subject in data["subjects"]:
        count = sum(len(topic["cards"]) for topic in subject["topics"])
        print(f'{subject["title"]} — тем: {len(subject["topics"])}, карточек: {count}')


if __name__ == "__main__":
    main()
