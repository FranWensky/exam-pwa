"use strict";

const app = document.getElementById("app");
const themeButton = document.getElementById("theme");
const darkMedia = matchMedia("(prefers-color-scheme: dark)");
const customKey = "sessia.cards.v1";
const symbols = { 1: "∫", 2: "λ", 3: "{ }" };
const formatting = document.createElement("template");
let subjects = [];
let topicIndex = new Map();
let custom = {};
let training = null;
let offlineMessage = "Офлайн-копия загружается…";

function element(tag, className = "", text) {
  const result = document.createElement(tag);
  if (className) result.className = className;
  if (text !== undefined) result.textContent = text;
  return result;
}

function button(text, className, action) {
  const result = element("button", className, text);
  result.type = "button";
  result.addEventListener("click", action);
  return result;
}

function link(text, className, path) {
  const result = element("a", className, text);
  result.href = "#" + path;
  return result;
}

function setTheme(value, persist = false) {
  document.documentElement.dataset.theme = value;
  document.querySelector('meta[name="theme-color"]').content = value === "dark" ? "#141322" : "#f4f4fa";
  themeButton.textContent = value === "dark" ? "☀" : "☾";
  themeButton.setAttribute("aria-label", value === "dark" ? "Включить светлую тему" : "Включить тёмную тему");
  if (persist) {
    try { localStorage.setItem("sessia.theme", value); } catch {}
  }
}

function toggleTheme() {
  setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark", true);
}

setTheme(document.documentElement.dataset.theme || (darkMedia.matches ? "dark" : "light"));
themeButton.addEventListener("click", toggleTheme);

function tile(title, detail, path, subject) {
  const anchor = link("", subject ? "tile subject-tile" : "tile", path);
  if (subject) {
    const symbol = element("span", `symbol subject-${subject}`, symbols[subject]);
    symbol.setAttribute("aria-hidden", "true");
    anchor.append(symbol);
  }
  const label = element("span");
  label.append(element("span", "tile-title", title));
  if (detail) label.append(element("span", "tile-meta", detail));
  const arrow = element("span", "chevron", "›");
  arrow.setAttribute("aria-hidden", "true");
  anchor.append(label, arrow);
  return anchor;
}

function heading(title, backPath, backTitle, subtitle) {
  if (backPath) app.append(link(`‹ ${backTitle}`, "back", backPath));
  const header = element("header", "page-header");
  header.append(element("h1", "", title));
  if (subtitle) header.append(element("p", "", subtitle));
  app.append(header);
}

function plural(count, forms) {
  const form = new Intl.PluralRules("ru").select(count);
  return `${count} ${forms[{ one: 0, few: 1, many: 2 }[form] ?? 2]}`;
}

function cardCount(count) {
  return plural(count, ["карточка", "карточки", "карточек"]);
}

function topicCount(subject, count) {
  return plural(count, subject.id === "3" ? ["билет", "билета", "билетов"] : ["тема", "темы", "тем"]);
}

function topicPath(subject, topic) {
  return topic.section ? `/subject/${subject.id}/${topic.section}` : `/subject/${subject.id}`;
}

function cardTotal(topics) {
  return topics.reduce((total, topic) => total + topic.cards.length + (custom[topic.id]?.length || 0), 0);
}

function trainingLink(label, scope, id) {
  const anchor = link(label, "primary", `/train/${scope}/${id}`);
  anchor.addEventListener("click", () => { training = null; });
  return anchor;
}

function home() {
  const hero = element("section", "hero");
  const mark = element("span", "hero-mark", "∫");
  mark.setAttribute("aria-hidden", "true");
  const topics = subjects.flatMap(subject => subject.topics);
  hero.append(element("h1", "", "Подготовка к экзаменам"),
    element("p", "", `${plural(topics.length, ["материал", "материала", "материалов"])} · ${cardCount(cardTotal(topics))}`), mark);
  const list = element("div", "list");
  for (const subject of subjects) {
    list.append(tile(subject.title,
      `${topicCount(subject, subject.topics.length)} · ${cardCount(cardTotal(subject.topics))}`,
      `/subject/${subject.id}`, subject.id));
  }
  app.append(hero, element("h2", "section-heading", "Предметы"), list);
}

function browse(subject, section) {
  const path = `/subject/${subject.id}`;
  const topics = section ? subject.topics.filter(topic => topic.section === section.id) : subject.topics;
  const sections = !section && subject.sections.length;
  heading(section?.title || subject.title, section ? path : "/", section ? "К разделам" : "Предметы",
    `${topicCount(subject, topics.length)} · ${cardCount(cardTotal(topics))}`);
  const actions = element("div", "actions");
  if (cardTotal(topics)) {
    actions.append(trainingLink(section ? "Учить весь раздел" : "Учить весь предмет",
      section ? "section" : "subject", section?.id || subject.id));
  }
  const list = element("div", "list");
  if (sections) {
    for (const item of subject.sections) {
      const sectionTopics = subject.topics.filter(topic => topic.section === item.id);
      list.append(tile(item.title, topicCount(subject, sectionTopics.length), `${path}/${item.id}`));
    }
  } else {
    for (const topic of topics) {
      list.append(tile(topic.title, cardCount(cardTotal([topic])), `/theory/${topic.id}`));
    }
  }
  app.append(actions, element("h2", "", sections ? "Разделы" : subject.id === "3" ? "Билеты" : "Темы"), list);
}

function markup(html, className = "", tag = "div") {
  const result = element(tag, className);
  result.innerHTML = html;
  return result;
}

function codeBlock(text) {
  const pre = element("pre", "code-block");
  const code = element("code");
  const tokens = /\/\*[\s\S]*?\*\/|\/\/[^\n]*|#[ \t]*[a-z]+|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:auto|bool|break|case|char|class|const|continue|default|delete|do|double|else|enum|float|for|if|int|long|namespace|new|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|while)\b|\b(?:0x[\da-f]+|\d+(?:\.\d+)?)\b/gi;
  let cursor = 0;
  for (const match of text.matchAll(tokens)) {
    const token = match[0];
    code.append(text.slice(cursor, match.index));
    const kind = token.startsWith("/") ? "comment" : /^["']/.test(token) ? "string"
      : /^\d/.test(token) ? "number" : "keyword";
    code.append(element("span", `tok-${kind}`, token));
    cursor = match.index + token.length;
  }
  code.append(text.slice(cursor));
  pre.append(code);
  return pre;
}

function theoryArticle(topic) {
  const article = element("article", "theory");
  for (const block of topic.blocks) {
    if (block.kind === "heading") article.append(element("h2", "", block.text));
    else if (block.kind === "code") article.append(codeBlock(block.text));
    else if (block.text !== undefined) article.append(element("pre", "", block.text));
    else article.append(markup(block.html, block.kind === "paragraph" ? "" : `callout ${block.kind}`, "p"));
  }
  return article;
}

function searchPanel(article) {
  const panel = element("div", "search-panel");
  const label = element("label", "", "Поиск по теории");
  label.htmlFor = "theory-search";
  const input = element("input", "search");
  input.type = "search";
  input.id = "theory-search";
  input.placeholder = "Слово или формула";
  const searchRow = element("div", "search-controls");
  const top = button("↑", "icon-button", () => window.scrollTo(0, 0));
  top.setAttribute("aria-label", "Наверх");
  searchRow.append(input, top);
  const controls = element("div", "search-controls");
  const counter = element("output", "muted");
  counter.setAttribute("aria-live", "polite");
  const previous = button("↑", "icon-button", () => selectMatch(current - 1));
  const next = button("↓", "icon-button", () => selectMatch(current + 1));
  previous.setAttribute("aria-label", "Предыдущее совпадение");
  next.setAttribute("aria-label", "Следующее совпадение");
  controls.append(counter, previous, next);
  controls.hidden = true;
  panel.append(label, searchRow, controls);
  let matches = [];
  let current = 0;
  const normalize = text => text.toLocaleLowerCase("ru").replaceAll("ё", "е");
  function selectMatch(index) {
    if (!matches.length) return;
    for (const mark of matches[current] || []) mark.classList.remove("current");
    current = (index + matches.length) % matches.length;
    for (const mark of matches[current]) mark.classList.add("current");
    matches[current][0].scrollIntoView({ block: "center" });
    counter.textContent = `${current + 1} из ${matches.length}`;
  }
  input.addEventListener("input", () => {
    for (const mark of matches.flat()) {
      const parent = mark.parentNode;
      mark.replaceWith(document.createTextNode(mark.textContent));
      parent.normalize();
    }
    matches = [];
    current = 0;
    const query = normalize(input.value.trim());
    controls.hidden = !query;
    if (!query) return;
    for (const block of article.children) {
      const haystack = normalize(block.textContent);
      const ranges = [];
      for (let position = haystack.indexOf(query); position >= 0; position = haystack.indexOf(query, position + query.length)) {
        const marks = [];
        ranges.push({ start: position, end: position + query.length, marks });
        matches.push(marks);
      }
      if (!ranges.length) continue;
      const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      let offset = 0;
      for (const node of nodes) {
        const text = node.textContent;
        const limit = offset + text.length;
        const fragment = document.createDocumentFragment();
        let cursor = 0;
        for (const range of ranges) {
          if (range.end <= offset) continue;
          if (range.start >= limit) break;
          const start = Math.max(0, range.start - offset);
          const end = Math.min(text.length, range.end - offset);
          const mark = element("mark", "", text.slice(start, end));
          fragment.append(text.slice(cursor, start), mark);
          range.marks.push(mark);
          cursor = end;
        }
        if (cursor) {
          fragment.append(text.slice(cursor));
          node.replaceWith(fragment);
        }
        offset = limit;
      }
    }
    counter.textContent = matches.length ? `Найдено: ${matches.length}` : "Совпадений нет";
    previous.disabled = next.disabled = !matches.length;
    current = matches.length - 1;
  });
  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && matches.length) {
      event.preventDefault();
      selectMatch(current + 1);
    }
  });
  return panel;
}

function theory(subject, topic) {
  heading(topic.title, topicPath(subject, topic), subject.id === "3" ? "К билетам" : "К темам");
  const actions = element("div", "actions");
  if (cardTotal([topic])) actions.append(trainingLink("Начать тренировку", "topic", topic.id));
  const article = theoryArticle(topic);
  const footer = element("div", "actions end-actions");
  footer.append(button("↑ Наверх", "secondary", () => window.scrollTo(0, 0)));
  if (cardTotal([topic])) footer.append(trainingLink("Начать тренировку", "topic", topic.id));
  app.append(actions, searchPanel(article), article, footer);
}

function plain(html) {
  formatting.innerHTML = html;
  return formatting.content.textContent;
}

function cardKey(question, answer) {
  return JSON.stringify([question.trim(), answer.trim()]);
}

function topicCards(topic) {
  return topic.cards.map(card => ({ ...card, plainQuestion: plain(card.question), plainAnswer: plain(card.answer) }))
    .concat((custom[topic.id] || []).map(card => ({
      ...card, plainQuestion: card.question, plainAnswer: card.answer, custom: true,
    })));
}

function deckFor(topics) {
  const cards = new Map();
  for (const topic of topics) {
    for (const card of topicCards(topic)) {
      const key = cardKey(card.plainQuestion, card.plainAnswer);
      if (!cards.has(key)) cards.set(key, card);
    }
  }
  const deck = [...cards.values()];
  for (let index = deck.length - 1; index > 0; index -= 1) {
    const other = Math.floor(Math.random() * (index + 1));
    [deck[index], deck[other]] = [deck[other], deck[index]];
  }
  return deck;
}

function scopeData(scope, id) {
  if (scope === "topic" && topicIndex.has(id)) {
    const { topic } = topicIndex.get(id);
    return { title: topic.title, topics: [topic], back: `/theory/${id}` };
  }
  for (const subject of subjects) {
    if (scope === "subject" && subject.id === id) {
      return { title: subject.title, topics: subject.topics, back: `/subject/${id}` };
    }
    const section = subject.sections.find(item => item.id === id);
    if (scope === "section" && section) {
      return { title: section.title, topics: subject.topics.filter(topic => topic.section === id),
        back: `/subject/${subject.id}/${id}` };
    }
  }
  return null;
}

function review(scope, id) {
  const info = scopeData(scope, id);
  if (!info) return unavailable();
  const path = `/train/${scope}/${id}`;
  if (!training || training.path !== path || training.complete) {
    const queue = deckFor(info.topics);
    training = { ...info, path, queue, total: queue.length, known: 0, flipped: false, complete: false };
  }
  if (!training.total) {
    heading("Тренировка", info.back, "К материалам", info.title);
    app.append(element("p", "empty", "В этой теме пока нет карточек."));
    return;
  }
  renderCard();
}

function renderCard() {
  const session = training;
  app.replaceChildren();
  heading("Тренировка", session.back, "К материалам", session.title);
  const progress = element("div", "progress-line muted");
  progress.append(element("span", "", "Выучено"), element("strong", "", `${session.known} из ${session.total}`));
  const meter = element("progress");
  meter.max = session.total;
  meter.value = session.known;
  meter.setAttribute("aria-label", "Выученные карточки");
  const item = session.queue[0];
  const card = element("div", "flip-card");
  card.tabIndex = 0;
  card.setAttribute("role", "button");
  const inner = element("div", "flip-inner");
  const front = element("div", "flip-face");
  const back = element("div", "flip-face flip-back");
  const face = (parent, title, value) => {
    parent.append(element("h2", "", title), item.custom ? element("div", "formatted", value) : markup(value, "formatted"));
  };
  face(front, "Вопрос", item.question);
  face(back, "Ответ", item.answer);
  inner.append(front, back);
  card.append(inner);
  const actions = element("div", "actions");
  const flipButton = button("🔄 Перевернуть карточку", "primary", flip);
  const ratings = element("div", "list");
  for (const [grade, label] of [
    ["green", "🟢 Я хорошо знаю"], ["yellow", "🟡 Я практически знаю"], ["red", "🔴 Я этого не знаю"],
  ]) ratings.append(button(label, `rating ${grade}`, () => rate(grade)));
  const stop = button("🛑 Завершить тренировку", "secondary danger", finish);
  function updateFace() {
    card.classList.toggle("flipped", session.flipped);
    card.setAttribute("aria-pressed", String(session.flipped));
    card.setAttribute("aria-label", session.flipped ? `Ответ: ${item.plainAnswer}` : `Вопрос: ${item.plainQuestion}`);
    front.setAttribute("aria-hidden", String(session.flipped));
    back.setAttribute("aria-hidden", String(!session.flipped));
    flipButton.hidden = session.flipped;
    ratings.hidden = !session.flipped;
  }
  function flip() {
    const wasFlipButton = document.activeElement === flipButton;
    session.flipped = !session.flipped;
    updateFace();
    if (wasFlipButton) card.focus({ preventScroll: true });
  }
  card.addEventListener("click", flip);
  card.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      flip();
    }
  });
  actions.append(flipButton, ratings, stop);
  app.append(progress, meter, card, actions);
  updateFace();
}

function rate(grade) {
  const session = training;
  const card = session.queue.shift();
  if (grade === "green") session.known += 1;
  else {
    const distance = grade === "red" ? 5 : 15 + Math.floor(Math.random() * 6);
    session.queue.splice(Math.min(distance, session.queue.length), 0, card);
  }
  session.flipped = false;
  if (session.queue.length) {
    renderCard();
    window.scrollTo(0, 0);
  } else finish();
}

function finish() {
  training.complete = true;
  location.hash = "/result";
}

function result() {
  if (!training?.complete) return unavailable();
  const { known, total, title, path, back } = training;
  const percent = Math.floor(100 * known / total);
  const color = percent >= 75 ? "green" : percent >= 50 ? "yellow" : "red";
  const feedback = {
    green: "Отлично", yellow: "Ещё немного практики", red: "Стоит повторить теорию",
  };
  heading("Результат", back, "К материалам", title);
  const panel = element("section", "panel result");
  const ring = element("div", `ring ${color}`);
  ring.style.setProperty("--score", `${percent}%`);
  ring.append(element("strong", "", `${percent}%`));
  panel.append(ring, element("h2", "", feedback[color]),
    element("p", "", `Выучено ${known} из ${total}`),
    element("p", "muted", `Осталось закрепить: ${total - known}`));
  const actions = element("div", "actions");
  const repeat = link("Повторить тренировку", "primary", path);
  repeat.addEventListener("click", () => { training = null; });
  actions.append(repeat, link("К материалам", "secondary", back));
  app.append(panel, actions);
}

function validCard(item) {
  return item && typeof item.question === "string" && typeof item.answer === "string" &&
    item.question.trim() && item.answer.trim();
}

function saveCards(value) {
  localStorage.setItem(customKey, JSON.stringify(value));
  custom = value;
}

function addCards(existing, topic, incoming) {
  const cards = existing[topic.id] || [];
  const keys = new Set(topic.cards.map(card => cardKey(plain(card.question), plain(card.answer))));
  for (const card of cards) keys.add(cardKey(card.question, card.answer));
  const added = [];
  for (const card of incoming) {
    const question = card.question.trim();
    const answer = card.answer.trim();
    const key = cardKey(question, answer);
    if (keys.has(key)) continue;
    keys.add(key);
    added.push({ question, answer });
  }
  if (added.length) existing[topic.id] = [...cards, ...added];
  return added.length;
}

function parseCards(text) {
  return text.split(/\r?\n/).flatMap((line, index) => {
    if (!line.trim()) return [];
    const separator = line.includes(" | ") ? " | " : "|";
    const split = line.indexOf(separator);
    const card = { question: line.slice(0, split).trim(), answer: line.slice(split + separator.length).trim() };
    if (split < 0 || !validCard(card)) throw new Error(`Строка ${index + 1}: нужен формат «Вопрос | Ответ».`);
    return [card];
  });
}

function downloadBackup() {
  const data = JSON.stringify({ version: 1, subjects, customCards: custom }, null, 2);
  const url = URL.createObjectURL(new Blob([data], { type: "application/json" }));
  const anchor = element("a");
  anchor.href = url;
  anchor.download = "sessia-backup.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

function settings() {
  heading("Настройки", "/", "Предметы");
  const stack = element("div", "stack");
  const preferences = element("section", "panel");
  const themeRow = element("div", "setting-row");
  themeRow.append(element("strong", "", "Тема"), button("Переключить", "secondary", toggleTheme));
  const offline = element("p", "muted", offlineMessage);
  offline.id = "offline-status";
  preferences.append(themeRow, offline);
  const panel = element("section", "panel");
  panel.append(element("h2", "settings-title", "Управление базой"),
    element("p", "muted", "Ваши карточки сохраняются на этом устройстве. Резервная копия включает и исходные материалы."));
  const form = element("form", "form");
  const topicLabel = element("label", "", "Тема или билет");
  topicLabel.htmlFor = "edit-topic";
  const select = element("select");
  select.id = "edit-topic";
  for (const subject of subjects) {
    const group = element("optgroup");
    group.label = subject.title;
    for (const topic of subject.topics) {
      const option = element("option", "", topic.title);
      option.value = topic.id;
      group.append(option);
    }
    select.append(group);
  }
  const cardLabel = element("label", "", "Новые карточки");
  cardLabel.htmlFor = "edit-cards";
  const text = element("textarea");
  text.id = "edit-cards";
  text.placeholder = "Вопрос | Ответ\nОдна карточка на строку";
  text.required = true;
  const add = element("button", "primary", "Добавить карточки");
  add.type = "submit";
  const notice = element("p", "notice muted");
  notice.setAttribute("role", "status");
  const show = (message, error = false) => {
    notice.textContent = message;
    notice.classList.toggle("error", error);
  };
  form.addEventListener("submit", event => {
    event.preventDefault();
    try {
      const incoming = parseCards(text.value);
      if (!incoming.length) throw new Error("Введите хотя бы одну карточку.");
      const updated = { ...custom };
      const count = addCards(updated, topicIndex.get(select.value).topic, incoming);
      if (count) saveCards(updated);
      text.value = "";
      show(count ? `Добавлено: ${cardCount(count)}.` : "Эти карточки уже есть в теме.");
    } catch (error) {
      show(error instanceof DOMException ? "Не удалось сохранить карточки на устройстве." : error.message, true);
    }
  });
  const restore = element("input");
  restore.type = "file";
  restore.accept = ".json,application/json";
  restore.hidden = true;
  restore.addEventListener("change", async () => {
    if (!restore.files[0]) return;
    try {
      const backup = JSON.parse(await restore.files[0].text());
      if (backup?.version !== 1 || !backup.customCards || Array.isArray(backup.customCards) ||
          typeof backup.customCards !== "object") throw new Error();
      const updated = { ...custom };
      let count = 0;
      let missing = 0;
      for (const [id, cards] of Object.entries(backup.customCards)) {
        if (!Array.isArray(cards) || !cards.every(validCard)) throw new Error();
        if (topicIndex.has(id)) count += addCards(updated, topicIndex.get(id).topic, cards);
        else missing += cards.length;
      }
      if (count) saveCards(updated);
      show(`Восстановлено: ${cardCount(count)}.${missing ? ` Без темы: ${missing}.` : ""}`);
    } catch {
      show("Не удалось прочитать или сохранить резервную копию Сессии.", true);
    } finally {
      restore.value = "";
    }
  });
  form.append(topicLabel, select, cardLabel, text, add,
    button("Скачать резервную копию", "secondary", downloadBackup),
    button("Восстановить свои карточки", "secondary", () => restore.click()), restore, notice);
  panel.append(form);
  stack.append(preferences, panel);
  app.append(stack);
}

function unavailable() {
  heading("Материалы не найдены", "/", "Предметы");
}

function render() {
  const [view, id, sectionId] = (location.hash.slice(2) || "").split("/");
  app.replaceChildren();
  app.setAttribute("aria-busy", "false");
  for (const [elementId, active] of [["nav-home", view !== "settings"], ["nav-settings", view === "settings"]]) {
    const item = document.getElementById(elementId);
    if (active) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  }
  if (!view) home();
  else if (view === "subject") {
    const subject = subjects.find(item => item.id === id);
    const section = subject?.sections.find(item => item.id === sectionId);
    if (!subject || (sectionId && !section)) unavailable();
    else browse(subject, section);
  } else if (view === "theory" && topicIndex.has(id)) {
    const { subject, topic } = topicIndex.get(id);
    theory(subject, topic);
  } else if (view === "train") review(id, sectionId);
  else if (view === "result") result();
  else if (view === "settings") settings();
  else unavailable();
  window.scrollTo(0, 0);
}

async function prepareOffline() {
  try {
    await navigator.serviceWorker.register("./sw.js");
    await navigator.serviceWorker.ready;
    offlineMessage = "Материалы готовы к работе без интернета.";
  } catch {
    offlineMessage = "Офлайн-копия пока недоступна.";
  }
  const status = document.getElementById("offline-status");
  if (status) status.textContent = offlineMessage;
}

async function start() {
  try {
    const response = await fetch("./data.json");
    if (!response.ok) throw new Error();
    const data = await response.json();
    subjects = data.subjects;
    for (const subject of subjects) {
      for (const topic of subject.topics) topicIndex.set(topic.id, { subject, topic });
    }
    try {
      const stored = JSON.parse(localStorage.getItem(customKey) || "{}");
      for (const [id, cards] of Object.entries(stored)) {
        if (topicIndex.has(id) && Array.isArray(cards)) custom[id] = cards.filter(validCard);
      }
    } catch {}
    window.addEventListener("hashchange", render);
    render();
    prepareOffline();
  } catch {
    app.setAttribute("aria-busy", "false");
    app.replaceChildren(element("p", "empty", "Материалы не загрузились. Подключитесь к интернету и попробуйте ещё раз."),
      button("Повторить", "primary", () => location.reload()));
  }
}

start();
