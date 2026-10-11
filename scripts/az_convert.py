#!/usr/bin/env python3
"""Convert e-qanun.az acts (cached by az_fetch.py in ../_raw/az/) to Markdown."""
import datetime, json, os, re, sys
from bs4 import BeautifulSoup, NavigableString, Tag

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "az")
FOLD = str.maketrans({"ə": "e", "Ə": "e", "ı": "i", "İ": "i", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u", "ş": "s",
                      "Ş": "s", "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g"})
# matched against an upper-cased copy of the line in which İ/ı are folded to I
ORD = r"(BIRINCI|IKINCI|ÜÇÜNCÜ|DÖRDÜNCÜ|BEŞINCI|ALTINCI|YEDDINCI|SƏKKIZINCI|DOQQUZUNCU|ONUNCU|[IVXLC]+|\d+(-[A-ZÜ]+)?)"
KINDS = [
    ("book", rf"^({ORD}\.?\s+)?KITAB(\s+{ORD})?\.?(\s|$)"),
    ("part", rf"^({ORD}\.?\s+)?(ÜMUMI|XÜSUSI)\s+HISSƏ\b|^{ORD}\.?\s+HISSƏ\b|^HISSƏ\s+{ORD}\b"),
    ("section", rf"^{ORD}\.?\s+BÖLMƏ\b|^BÖLMƏ\s+{ORD}\b"),
    ("subsection", rf"^({ORD}\.?\s+)?YARIMBÖLMƏ\b"),
    ("chapter", rf"^{ORD}\.?\s+FƏSIL\b|^FƏSIL\s+{ORD}\b"),
    ("article", r"^MADDƏ\s*\d+(-\d+)?(\.\d+)*\.?(\s|$)"),
]
HEAD_KINDS = ("book", "part", "section", "subsection", "chapter")


def slug(title, n=70):
    s = title.translate(FOLD).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > n:
        s = s[:n].rsplit("-", 1)[0]
    return s or "untitled"


def text_of(el):
    out = []
    for d in el.descendants:
        if isinstance(d, NavigableString):
            if d.parent.name in ("script", "style") or type(d).__name__ == "Comment":
                continue
            out.append(re.sub(r"[\r\n]+", " ", str(d)))
        elif isinstance(d, Tag) and d.name == "br":
            out.append("\n")
    t = "".join(out).replace("\xa0", " ")
    t = re.sub(r"[ \t\f\v]+", " ", t)
    t = "\n".join(x.strip() for x in t.split("\n"))
    return re.sub(r"\n{2,}", "\n", t).strip()


def frac(el, tags):
    t = re.sub(r"\s", "", el.get_text())
    if not t:
        return 0
    return len("".join(re.sub(r"\s", "", i.get_text()) for i in el.find_all(tags))) / len(t)


def esc(t):
    return re.sub(r"^(#+|>|[-+*] )", lambda m: "\\" + m.group(0), t)


def table_html(tb):
    rows = []
    for tr in tb.find_all("tr"):
        if tr.find_parent("table") is not tb:
            continue
        cells = []
        for td in tr.find_all(["td", "th"], recursive=False):
            attrs = "".join(f' {a}="{td[a]}"' for a in ("colspan", "rowspan") if td.get(a) and td.get(a) != "1")
            cells.append(f"<{td.name}{attrs}>{text_of(td).replace(chr(10), '<br>')}</{td.name}>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def kind_of(t):
    u = t.replace("İ", "I").replace("ı", "I").upper()
    for k, rx in KINDS:
        if re.match(rx, u):
            return k
    return None


def blocks(root):
    for el in root.children:
        if not isinstance(el, Tag):
            continue
        if el.name == "table":
            yield el
        elif el.name in ("div", "center", "blockquote", "section", "font", "span") and el.find(
                ["p", "table", "div", "h1", "h2", "h3", "h4", "h5", "h6"]):
            yield from blocks(el)
        elif el.name in ("ol", "ul"):
            for li in el.find_all("li", recursive=False):
                yield li
        elif el.name in ("style", "script", "meta", "link", "title", "xml"):
            continue
        else:
            yield el


def convert_body(root):
    items = []
    for el in blocks(root):
        if el.name == "table":
            if el.get_text(strip=True):
                items.append(("table", table_html(el)))
            continue
        t = text_of(el)
        if not t:
            continue
        one = re.sub(r"\s+", " ", t)
        cls = " ".join(el.get("class") or [])
        if re.match(r"(MHEADNG|StyleTOC|MsoToc|Bashlig)", cls):  # table of contents lines
            items.append(("para", t))
            continue
        k = kind_of(one)
        if k and len(one) < (400 if k == "article" else 200):
            items.append((k, one))
        elif "Endnote" in cls or "Footnote" in cls:
            items.append(("note", one))
        elif el.name in ("h1", "h2", "h3", "h4", "h5", "h6") or re.match(r"(Lar\d|Madde$)", cls) or (frac(el, ["b", "strong"]) > 0.9 and len(one) < 200 and (
                one.upper() == one or "center" in (el.get("align") or "") + (el.get("style") or ""))):
            items.append(("other", one))
        else:
            items.append(("para", t))
    merged = []
    for k, t in items:
        if k == "other" and merged and merged[-1][0] in HEAD_KINDS and len(merged[-1][1].split()) <= 3 \
                and not re.search(r"[.:–—]\s*\S", merged[-1][1]):
            merged[-1] = (merged[-1][0], merged[-1][1].rstrip(".") + ". " + t)
        else:
            merged.append((k, t))
    items = merged
    for n, (k, t) in enumerate(items):
        if k == "other":
            items[n] = ("bold", t)
        elif k in HEAD_KINDS or k == "article":
            break
    order = []
    for k, _ in items:
        if k in HEAD_KINDS and k not in order:
            order.append(k)
    level = {k: 2 + n for n, k in enumerate(order)}
    art_level = min(6, 2 + len(order))
    out, notes_started = [], False
    for k, t in items:
        if k == "para":
            out.append(esc(t).replace("\n", "  \n"))
        elif k == "note":
            if not notes_started:
                out.append("---")
                notes_started = True
            out.append(esc(t))
        elif k == "table":
            out.append(t)
        elif k == "bold":
            out.append("**" + t.replace("*", "\\*") + "**")
        elif k == "other":
            out.append("#" * max(2, art_level - 1) + " " + t if art_level > 2 else "**" + t.replace("*", "\\*") + "**")
        else:
            lv = art_level if k == "article" else level[k]
            out.append("#" * min(lv, 6) + " " + t)
    return "\n\n".join(out) + "\n"


def dmy(s):
    m = re.search(r"(\d{2})[.-](\d{2})[.-](\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def yq(s):
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


TYPES = {"konstitusiya": "constitution", "konstitusiya-qanunlari": "constitutional_law", "mecelleler": "code",
         "qanunlar": "act"}


def main():
    today = datetime.date.today().isoformat()
    acts = json.load(open(os.path.join(RAW, "index.json")))
    counts = {}
    for a in acts:
        mp, hp = os.path.join(RAW, "meta", f"{a['id']}.json"), os.path.join(RAW, "html", f"{a['id']}.html")
        if not (os.path.exists(mp) and os.path.exists(hp)):
            continue
        meta = json.load(open(mp))["data"]
        req = meta.get("requisite") or {}
        raw = open(hp, "rb").read()
        m = re.search(rb'charset=["\']?([^"\' >;]+)', raw)
        enc = m.group(1).decode() if m else "utf-8"
        try:
            html = raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            html = raw.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "lxml")
        body = soup.body or soup
        cat = a["category"]
        title = re.sub(r"\s+", " ", req.get("title") or a["title"]).strip()
        date = dmy(req.get("acceptDate") or a.get("acceptDate"))
        year = (date or "0000")[:4]
        sub = os.path.join("qanunlar", year) if cat == "qanunlar" else cat
        pubs = []
        f = req.get("fields") or []
        for i in range(0, len(f), 3):
            grp = f[i:i + 3]
            pubs.append(", ".join(x["fieldValue"].strip() for x in grp if (x.get("fieldValue") or "").strip()))
        pubname = f[0]["name"] if f else ""
        fm = ["---", f"title: {yq(title)}", f"identifier: {yq(req.get('citation') or a.get('citation'))}",
              f"eqanun_id: {a['id']}", f"type: {TYPES[cat]}", f"document_type: {yq(req.get('typeName'))}",
              "jurisdiction: az", "language: az"]
        if date:
            fm.append(f"date: {date}")
        if dmy(req.get("effectDate")):
            fm.append(f"entry_into_force: {dmy(req.get('effectDate'))}")
        if req.get("registerCode"):
            fm.append(f"register_code: {yq(req['registerCode'])}")
        fm += [f"status_text: {yq(req.get('statusName'))}", "status: in_force"]
        if pubs:
            fm.append(f"publication: {yq(pubname + ': ' + '; '.join(pubs))}")
        fm += [f"source: \"https://e-qanun.az/framework/{a['id']}\"", f"source_html: {yq(meta.get('htmlUrl'))}",
               f"retrieved: {today}", "---", "", f"# {title}", "", ""]
        out = os.path.join(REPO, sub, f"{a['id']}-{slug(title)}.md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write("\n".join(fm) + convert_body(body))
        counts[cat] = counts.get(cat, 0) + 1
    print(counts)


if __name__ == "__main__":
    main()
