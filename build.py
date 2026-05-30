#!/usr/bin/env python3
"""Static blog generator for プロテイン攻略ナビ.

Reads Markdown sources from content/blog/*.md (front matter + a small Markdown
subset) and renders static HTML into blog/ using the site's existing design
(style.css). Also generates the blog index, category pages and sitemap.xml.

Run:  python3 build.py
"""
import os, re, html, json, datetime, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "content", "blog")
OUT_BLOG = os.path.join(ROOT, "blog")
OUT_CAT = os.path.join(OUT_BLOG, "category")
BASE = "https://machonaengineer.github.io/myprotein-site/"
SITE = "プロテイン攻略ナビ"

CATEGORIES = {
    "training-method":      "トレーニング理論",
    "nutrition-supplement": "栄養・サプリメント",
    "recovery-sleep":       "回復・睡眠",
    "diet-fatloss":         "減量・ダイエット",
    "hormone-health":       "ホルモン・健康",
    "mindset-habit":        "メンタル・習慣",
}
CAT_DESC = {
    "training-method":      "分割法・ボリューム・頻度など、筋肥大と筋力向上のトレーニング設計を論文ベースで整理した記事。",
    "nutrition-supplement": "プロテイン・EAA・クレアチンなどのサプリと、たんぱく質・糖質を中心とした栄養の考え方をまとめた記事。",
    "recovery-sleep":       "睡眠・休養・疲労回復・入浴など、トレーニングの効果を左右するリカバリーに関する記事。",
    "diet-fatloss":         "減量・体脂肪コントロール・食事管理を、リバウンドを避ける観点から解説した記事。",
    "hormone-health":       "テストステロンをはじめとするホルモンと、加齢・健康との関係を扱う記事。",
    "mindset-habit":        "継続・習慣化・生活リズムなど、トレーニングを続けるための考え方をまとめた記事。",
}

# ---------------------------------------------------------------- markdown
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)',
               lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    return t

def slugify_id(n):
    return f"s{n}"

def md_to_html(md, top=True):
    """Return (body_html, toc) where toc is list of (id, text)."""
    lines = md.split("\n")
    out, toc = [], []
    i, n = 0, len(lines)
    hcount = 0
    first_para_done = not top  # only the top-level first paragraph becomes the lede
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1; continue
        # callout block :::type ... :::
        m = re.match(r':::(\w+)\s*$', s)
        if m:
            kind = m.group(1)
            i += 1
            buf = []
            while i < n and lines[i].strip() != ":::":
                buf.append(lines[i]); i += 1
            i += 1  # skip closing :::
            inner = md_to_html("\n".join(buf), top=False)[0]
            if kind in ("point", "conclusion"):
                out.append(f'<div class="article-callout"><b>結論</b>{inner}</div>')
            elif kind == "note":
                out.append(f'<div class="notice">{inner}</div>')
            elif kind == "cta":
                out.append(f'<div class="cta-inline">{inner}</div>')
            else:
                out.append(f'<div class="article-callout">{inner}</div>')
            continue
        # headings
        if s.startswith("### "):
            out.append(f'<h3>{inline(s[4:].strip())}</h3>'); i += 1; continue
        if s.startswith("## "):
            hcount += 1
            hid = slugify_id(hcount)
            txt = s[3:].strip()
            toc.append((hid, txt))
            out.append(f'<h2 id="{hid}">{inline(txt)}</h2>'); i += 1; continue
        # blockquote
        if s.startswith("> "):
            buf = []
            while i < n and lines[i].strip().startswith("> "):
                buf.append(lines[i].strip()[2:]); i += 1
            out.append(f'<blockquote>{inline(" ".join(buf))}</blockquote>'); continue
        # unordered list
        if re.match(r'[-*]\s+', s):
            buf = []
            while i < n and re.match(r'[-*]\s+', lines[i].strip()):
                buf.append(re.sub(r'^[-*]\s+', '', lines[i].strip())); i += 1
            items = "".join(f'<li>{inline(x)}</li>' for x in buf)
            out.append(f'<ul>{items}</ul>'); continue
        # ordered list
        if re.match(r'\d+\.\s+', s):
            buf = []
            while i < n and re.match(r'\d+\.\s+', lines[i].strip()):
                buf.append(re.sub(r'^\d+\.\s+', '', lines[i].strip())); i += 1
            items = "".join(f'<li>{inline(x)}</li>' for x in buf)
            out.append(f'<ol>{items}</ol>'); continue
        # paragraph (gather until blank)
        buf = [s]
        i += 1
        while i < n and lines[i].strip() and not re.match(r'(##|###|[-*]\s|\d+\.\s|>|:::)', lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        para = inline(" ".join(buf))
        if not first_para_done:
            out.append(f'<p class="lede">{para}</p>'); first_para_done = True
        else:
            out.append(f'<p>{para}</p>')
    return "\n".join(out), toc

# ---------------------------------------------------------------- front matter
def parse(path):
    raw = open(path, encoding="utf-8").read()
    meta = {}
    body = raw
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        for ln in fm.strip().split("\n"):
            if ":" in ln:
                k, v = ln.split(":", 1)
                meta[k.strip()] = v.strip()
    slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
    meta["slug"] = slug
    meta.setdefault("category", "training-method")
    meta.setdefault("date", datetime.date.today().isoformat())
    meta.setdefault("tags", "")
    body_html, toc = md_to_html(body.strip())
    meta["_html"] = body_html
    meta["_toc"] = toc
    return meta

# ---------------------------------------------------------------- templates
def header(prefix, active_blog=True):
    return f'''<div class="topbar">本ページはプロモーション（アフィリエイト広告）を含みます</div>
<header class="header"><div class="container header-inner">
<a class="logo" href="{prefix}index.html">🏋️ {SITE}<small>実践者目線の購入ガイド</small></a>
<nav class="nav">
<a href="{prefix}myprotein-osusume.html">選び方</a>
<a href="{prefix}myprotein-review.html">レビュー</a>
<a href="{prefix}blog/index.html">コラム</a>
<a href="{prefix}myprotein-shoshinsha.html">初心者</a>
</nav>
<a class="btn btn-dark" href="{prefix}blog/index.html">コラムを読む<span>→</span></a>
</div></header>'''

def footer(prefix):
    return f'''<footer class="footer"><div class="container footer-grid">
<div><b>🏋️ {SITE}</b><p>筋トレ実践者の視点で、トレーニングと栄養・サプリメントの考え方を、論文と実際の経験をもとに解説する個人運営の情報サイトです。掲載内容はアフィリエイト広告を含みます。効果には個人差があり、サプリメントは薬ではありません。</p></div>
<div><b>コラム</b><div class="links">
<a href="{prefix}blog/index.html">コラム一覧</a>
<a href="{prefix}blog/category/training-method.html">トレーニング理論</a>
<a href="{prefix}blog/category/nutrition-supplement.html">栄養・サプリメント</a>
<a href="{prefix}blog/category/recovery-sleep.html">回復・睡眠</a>
</div></div>
<div><b>商品ガイド</b><div class="links">
<a href="{prefix}impact-whey.html">Impactホエイ</a>
<a href="{prefix}myprotein-creatine.html">クレアチン</a>
<a href="{prefix}eaa-bcaa.html">EAA・BCAA</a>
</div></div>
<div><b>運営</b><div class="links">
<a href="{prefix}profile.html">運営者情報</a>
<a href="{prefix}privacy.html">プライバシーポリシー</a>
<a href="{prefix}contact.html">お問い合わせ</a>
</div></div>
</div></footer>'''

AUTHOR_BOX = '''<div class="author-box"><div class="ava">🏋️</div><div><b>運営者について</b><p>週2〜3回の筋力トレーニングを数年継続している個人です。本記事は公開されている研究・論文と自身の経験をもとに構成しています。効果には個人差があり、サプリメントは薬ではありません。<a href="{prefix}profile.html">運営者情報の詳細 →</a></p></div></div>'''

def page_shell(title, desc, canonical, prefix, body, head_extra=""):
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="{prefix}style.css">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="ja_JP">{head_extra}
</head><body>
{header(prefix)}
<main>
{body}
</main>
{footer(prefix)}
</body></html>'''

def render_article(a, related):
    prefix = "../"
    cat = a["category"]
    cat_name = CATEGORIES.get(cat, "コラム")
    url = f'{BASE}blog/{a["slug"]}.html'
    desc = a.get("description", "")[:120]
    toc = a["_toc"]
    toc_html = ""
    if len(toc) >= 2:
        items = "".join(f'<a href="#{i}">{html.escape(t)}</a>' for i, t in toc)
        toc_html = f'<div class="toc"><b>目次</b>{items}</div>'
    rel_html = ""
    if related:
        cards = "".join(
            f'<article class="card pad"><span class="tag">{CATEGORIES.get(r["category"],"")}</span>'
            f'<h3><a href="{r["slug"]}.html">{html.escape(r["title"])}</a></h3></article>'
            for r in related)
        rel_html = f'<section class="section"><div class="container"><h2>関連記事</h2><div class="grid3">{cards}</div></div></section>'
    tags = [t.strip() for t in a.get("tags", "").split(",") if t.strip()]
    tags_html = ""
    if tags:
        tags_html = '<p class="muted" style="margin-top:24px">' + " ".join(
            f'<span class="pill">{html.escape(t)}</span>' for t in tags) + '</p>'
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": a["title"], "description": desc,
        "datePublished": a["date"], "dateModified": a.get("updated", a["date"]),
        "author": {"@type": "Person", "name": "プロテイン攻略ナビ 運営者"},
        "publisher": {"@type": "Organization", "name": SITE},
        "mainEntityOfPage": url,
        "articleSection": cat_name,
    }, ensure_ascii=False)
    head_extra = f'\n<script type="application/ld+json">{jsonld}</script>'
    body = f'''<article class="section"><div class="container">
<p class="breadcrumb"><a href="{prefix}index.html">ホーム</a> ／ <a href="index.html">コラム</a> ／ <a href="category/{cat}.html">{cat_name}</a></p>
<div class="prose">
<span class="tag">{cat_name}</span>
<h1 style="font-size:clamp(28px,4vw,42px);letter-spacing:-.03em;margin:10px 0 6px">{html.escape(a["title"])}</h1>
<p class="updated">公開日: {a["date"]}</p>
<div class="article">
{toc_html}
{a["_html"]}
</div>
{tags_html}
{AUTHOR_BOX.format(prefix=prefix)}
<div class="notice"><b>広告・免責表記</b><br>当サイトはアフィリエイト広告を利用しています。本記事は一般的な情報提供を目的としたもので、医療上の助言ではありません。体調・持病・服薬がある場合は医師等の専門家にご相談ください。効果には個人差があります。</div>
</div></div></article>
{rel_html}'''
    return page_shell(f'{a["title"]}｜{SITE}', desc, url, prefix, body, head_extra)

def card(a, prefix=""):
    return (f'<article class="card pad"><span class="tag">{CATEGORIES.get(a["category"],"")}</span>'
            f'<h3><a href="{prefix}{a["slug"]}.html">{html.escape(a["title"])}</a></h3>'
            f'<p class="muted">{html.escape(a.get("description","")[:90])}</p>'
            f'<p class="updated">{a["date"]}</p></article>')

def render_index(arts):
    prefix = "../"
    url = f"{BASE}blog/"
    catnav = " ".join(
        f'<a class="btn" href="category/{c}.html">{n}</a>' for c, n in CATEGORIES.items())
    cards = "".join(card(a) for a in arts)
    body = f'''<section class="section white"><div class="container">
<p class="breadcrumb"><a href="{prefix}index.html">ホーム</a> ／ コラム</p>
<p class="eyebrow">COLUMN</p>
<h1>筋トレ攻略コラム</h1>
<p class="desc">論文・研究をベースに、トレーニング・栄養・回復の「なんとなく信じられている常識」を整理するコラムです。全{len(arts)}記事。</p>
<div class="row" style="margin:22px 0;flex-wrap:wrap">{catnav}</div>
<div class="grid3">{cards}</div>
</div></section>'''
    return page_shell(f"筋トレ攻略コラム｜{SITE}",
                      f"トレーニング・栄養・回復を論文ベースで解説する{SITE}のコラム一覧。",
                      url, prefix, body)

def render_category(cat, arts):
    prefix = "../../"
    name = CATEGORIES[cat]
    url = f"{BASE}blog/category/{cat}.html"
    cards = "".join(card(a, prefix="../") for a in arts)
    other = " ".join(
        f'<a class="btn" href="{c}.html">{n}</a>' for c, n in CATEGORIES.items() if c != cat)
    body = f'''<section class="section white"><div class="container">
<p class="breadcrumb"><a href="{prefix}index.html">ホーム</a> ／ <a href="../index.html">コラム</a> ／ {name}</p>
<p class="eyebrow">CATEGORY</p>
<h1>{name}</h1>
<p class="desc">{CAT_DESC.get(cat,"")}（{len(arts)}記事）</p>
<div class="row" style="margin:22px 0;flex-wrap:wrap"><a class="btn btn-primary" href="../index.html">コラム一覧</a>{other}</div>
<div class="grid3">{cards}</div>
</div></section>'''
    return page_shell(f"{name}の記事一覧｜{SITE}",
                      CAT_DESC.get(cat, name), url, prefix, body)

# ---------------------------------------------------------------- sitemap
def write_sitemap(arts):
    static_pages = [
        "", "index.html", "myprotein-osusume.html", "protein-osusume.html",
        "myprotein-review.html", "myprotein-aji.html", "myprotein-shoshinsha.html",
        "impact-whey.html", "myprotein-creatine.html", "eaa-bcaa.html",
        "myprotein-clear-whey.html", "myprotein-diet.html", "myprotein-sale.html",
        "profile.html", "privacy.html", "contact.html", "protein-faq.html",
    ]
    urls = [BASE + p for p in static_pages]
    urls.append(BASE + "blog/")
    urls += [f"{BASE}blog/category/{c}.html" for c in CATEGORIES]
    urls += [f'{BASE}blog/{a["slug"]}.html' for a in arts]
    today = datetime.date.today().isoformat()
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        body += f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n"
    body += "</urlset>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(body)

# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT_BLOG, exist_ok=True)
    os.makedirs(OUT_CAT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC, "*.md")))
    arts = [parse(f) for f in files]
    arts.sort(key=lambda a: a["date"], reverse=True)

    for a in arts:
        same = [r for r in arts if r["category"] == a["category"] and r["slug"] != a["slug"]][:3]
        out = os.path.join(OUT_BLOG, a["slug"] + ".html")
        open(out, "w", encoding="utf-8").write(render_article(a, same))

    open(os.path.join(OUT_BLOG, "index.html"), "w", encoding="utf-8").write(render_index(arts))

    for cat in CATEGORIES:
        catarts = [a for a in arts if a["category"] == cat]
        open(os.path.join(OUT_CAT, cat + ".html"), "w", encoding="utf-8").write(
            render_category(cat, catarts))

    write_sitemap(arts)
    print(f"Built {len(arts)} articles, {len(CATEGORIES)} category pages, index, sitemap.")
    by = {}
    for a in arts:
        by[a["category"]] = by.get(a["category"], 0) + 1
    for c, n in sorted(by.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {CATEGORIES.get(c,c)}")

if __name__ == "__main__":
    main()
