# Azerbaijan — legislation as Markdown (LawCodex)

Legislation of the Republic of Azerbaijan (Azərbaycan Respublikası) as Markdown, one file per
act, in the current consolidated text published by the official legal-acts database of the
Ministry of Justice, **e-qanun.az**. Part of [LawCodex](https://github.com/LawCodex).

Retrieved: **2026-10-12**. Language: Azerbaijani (the only official language).

## Coverage

| Directory | Contents | Files |
|---|---|---:|
| `konstitusiya/` | Constitution of 12 Nov 1995, with the 2002, 2009 and 2016 referendum amendments | 1 |
| `konstitusiya-qanunlari/` | constitutional laws (*Konstitusiya qanunları*) in force | 55 |
| `mecelleler/` | codes (*Məcəllələr*) in force: civil, criminal, civil/criminal procedure, tax, labour, family, land, customs, administrative offences, election, … | 20 |
| `qanunlar/<year>/` | laws (*Qanunlar*) in force, by year of adoption (1991–2026) | 2,564 |
| **Total** | | **2,640** |

- Selection: everything e-qanun.az lists with status *Qüvvədədir* (in force) in the categories
  Constitution, Constitutional laws, Codes and Laws — **except amending laws** (citation suffix
  `…QD`, "… dəyişiklik edilməsi barədə"; 3,951 of the 6,519 laws in force), whose content is
  already merged into the consolidated texts. About 1,730 of the 2,564 laws are ratification /
  approval laws for international agreements (*… təsdiq edilməsi haqqında*); the agreements
  themselves are usually not part of the law text.
- File names: `<e-qanun id>-<ASCII-folded title>.md`. Front matter: `identifier` (citation /
  number, e.g. `779-IQ`), `eqanun_id`, `date` (adoption), `entry_into_force`, `register_code`,
  `status_text`, `publication` (Qanunvericilik Toplusu references), `source` (e-qanun page) and
  `source_html` (the consolidated HTML file that was converted). e-qanun.az gives no
  consolidation date, so `last_amended` is omitted; the amendment history is in the endnotes.
- Structure: parts (*hissə*), sections (*bölmə*), chapters (*fəsil*) become `##`… headings in order
  of appearance, articles (*Maddə*) the deepest heading. The texts are Word-generated HTML; the
  numbered endnotes ([1], [2] …) that record every amending act are kept at the end after a
  `---` rule. Tables are kept as HTML.

## Not covered

- Decrees and orders of the President (~9,500), decisions of the Cabinet of Ministers (~9,700),
  normative acts of ministries and other bodies, Constitutional Court decisions, municipal acts —
  secondary legislation, not collected.
- Referendum acts amending the Constitution (3), amending laws, repealed acts.
- English: e-qanun.az has no English versions.

## Source and access notes

- **e-qanun.az** — "Azərbaycan Respublikasının Hüquqi Aktlarının Vahid Elektron Bazası", Ministry
  of Justice of the Republic of Azerbaijan.
- Access through the JSON API used by the web app (`https://api.e-qanun.az/getDetailSearch`,
  `/framework/<id>`) and the consolidated HTML files at `https://e-qanun.az/frameworks/…`.
  Neither host has a robots.txt. The HTML file server answers 403 to requests without a
  `Referer`; the fetcher sends the same Referer the web app sends
  (`https://e-qanun.az/framework/<id>`) while identifying itself honestly as
  `LawCodex/1.0 (+https://github.com/LawCodex)`. Requests were sequential, ≥ 1 s apart. (The same
  texts are also downloadable without a Referer as PDF from `frameworks.e-qanun.az`.)
- Copyright: under the Law of the Republic of Azerbaijan on Copyright and Related Rights,
  official documents (laws, decrees, decisions and other normative acts) are not objects of
  copyright.

## Regenerate

```
python3 -m pip install -r scripts/requirements.txt
python3 scripts/az_fetch.py     # downloads to ../_raw/az/ (cached)
python3 scripts/az_convert.py
```
