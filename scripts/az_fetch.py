#!/usr/bin/env python3
"""Download the Constitution, constitutional laws, codes and laws in force from e-qanun.az,
the official legal-acts database of the Ministry of Justice of Azerbaijan.

Uses the same public JSON API the e-qanun.az web app uses (api.e-qanun.az):
  getDetailSearch?array=<category>&statusId=1   -> list of acts in force
  framework/<id>                                -> metadata + URL of the consolidated HTML
The consolidated text is the Word-exported HTML at e-qanun.az/frameworks/<n>/f_<id>.html.
That file server refuses requests without a Referer, so we send the Referer the web app
itself sends (https://e-qanun.az/framework/<id>); the User-Agent stays LawCodex.

Amending laws (citation suffix "QD", "... dəyişiklik edilməsi barədə") are skipped: their
content is already merged into the consolidated texts.
Raw files are cached in ../_raw/az/. One request at a time, >= 1 s apart."""
import json, os, re, sys, time, requests

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
API = "https://api.e-qanun.az/"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "az")
DELAY = 1.0
CATEGORIES = {26: "konstitusiya", 28: "konstitusiya-qanunlari", 107: "mecelleler", 30: "qanunlar"}
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "AZ"})
_last = [0.0]


def get(url, **kw):
    for attempt in range(6):
        wait = _last[0] + DELAY - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = S.get(url, timeout=180, **kw)
            if r.status_code == 200:
                return r
            print("HTTP", r.status_code, url, file=sys.stderr)
            if r.status_code in (403, 404):
                return None
        except requests.RequestException as e:
            print("ERR", e, url, file=sys.stderr)
        time.sleep(20 * (attempt + 1))
    return None


def is_amending(row):
    cit = row.get("citation") or ""
    return bool(re.search(r"QD$", cit))


def list_acts():
    path = os.path.join(RAW, "index.json")
    if os.path.exists(path):
        return json.load(open(path))
    acts = []
    for cat, slug in CATEGORIES.items():
        start = 0
        while True:
            r = get(f"{API}getDetailSearch?start={start}&length=1000&orderColumn=8&orderDirection=asc"
                    f"&title=true&codeType=1&dateType=1&statusId=1&secondType=2&specialDate=false&array={cat}")
            d = r.json()
            for row in d["data"]:
                row["category"] = slug
                if cat == 30 and is_amending(row):
                    continue
                acts.append(row)
            start += 1000
            print(slug, start, d["totalCount"], len(acts), flush=True)
            if start >= d["totalCount"]:
                break
    json.dump(acts, open(path, "w"), ensure_ascii=False, indent=1)
    return acts


def main():
    os.makedirs(os.path.join(RAW, "meta"), exist_ok=True)
    os.makedirs(os.path.join(RAW, "html"), exist_ok=True)
    acts = list_acts()
    for n, a in enumerate(acts):
        mp = os.path.join(RAW, "meta", f"{a['id']}.json")
        hp = os.path.join(RAW, "html", f"{a['id']}.html")
        if not os.path.exists(mp):
            r = get(f"{API}framework/{a['id']}")
            if r is None:
                continue
            open(mp, "w").write(r.text)
        meta = json.load(open(mp))["data"]
        url = meta.get("htmlUrl")
        if url and not os.path.exists(hp):
            r = get(url, headers={"Referer": f"https://e-qanun.az/framework/{a['id']}"})
            if r is not None:
                open(hp, "wb").write(r.content)
            print(n + 1, len(acts), a["id"], len(r.content) if r is not None else None, flush=True)


if __name__ == "__main__":
    main()
