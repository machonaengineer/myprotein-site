#!/usr/bin/env python3
"""全HTMLの<head>に検証タグを一括挿入する。

使い方:
  # AdSense publisher ID を全HTMLに反映
  python3 inject_head.py --adsense ca-pub-1234567890

  # 複数のIDをまとめて
  python3 inject_head.py \
    --adsense ca-pub-1234567890 \
    --ga4 G-XXXXXXX \
    --search-console abcdef0123456789

引数を省略すると、現在の挿入状態のスキャンのみ行います。
冪等性あり：既に同じタグが入っている場合は重複挿入しません。
"""
import argparse, glob, re, sys

MARK_START = "<!-- INJECTED-HEAD-START -->"
MARK_END = "<!-- INJECTED-HEAD-END -->"


def build_snippets(adsense=None, ga4=None, search_console=None):
    parts = []
    if search_console:
        parts.append(f'<meta name="google-site-verification" content="{search_console}">')
    if adsense:
        parts.append(
            f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={adsense}" '
            f'crossorigin="anonymous"></script>'
        )
    if ga4:
        parts.append(
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga4}"></script>\n'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
            f"gtag('js',new Date());gtag('config','{ga4}');</script>"
        )
    return "\n".join(parts)


def inject(file, snippet):
    with open(file, encoding="utf-8") as f:
        s = f.read()
    block = f"\n{MARK_START}\n{snippet}\n{MARK_END}\n"
    # 既存ブロックがあれば置き換え、なければ </head> 直前に挿入
    pattern = re.compile(re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\s*", re.S)
    if pattern.search(s):
        new = pattern.sub(block.strip() + "\n", s)
    else:
        if "</head>" not in s:
            return False, "no </head>"
        new = s.replace("</head>", f"{block}</head>", 1)
    if new == s:
        return False, "unchanged"
    with open(file, "w", encoding="utf-8") as f:
        f.write(new)
    return True, "ok"


def scan(file):
    with open(file, encoding="utf-8") as f:
        s = f.read()
    m = re.search(re.escape(MARK_START) + r"(.*?)" + re.escape(MARK_END), s, re.S)
    return m.group(1).strip() if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adsense", help="AdSense publisher ID (e.g. ca-pub-XXXX)")
    ap.add_argument("--ga4", help="Google Analytics 4 ID (e.g. G-XXXX)")
    ap.add_argument("--search-console", help="Search Console verification token")
    ap.add_argument("--clear", action="store_true", help="挿入済みブロックを全削除")
    args = ap.parse_args()

    files = sorted(
        glob.glob("*.html") + glob.glob("blog/*.html") + glob.glob("blog/category/*.html")
    )
    print(f"対象HTMLファイル: {len(files)}")

    if args.clear:
        for f in files:
            with open(f, encoding="utf-8") as fp:
                s = fp.read()
            new = re.sub(
                re.escape(MARK_START) + r".*?" + re.escape(MARK_END) + r"\s*",
                "",
                s,
                flags=re.S,
            )
            if new != s:
                with open(f, "w", encoding="utf-8") as fp:
                    fp.write(new)
        print("既存の挿入ブロックを削除しました")
        return

    if not any([args.adsense, args.ga4, args.search_console]):
        # スキャンモード
        seen = set()
        for f in files:
            content = scan(f)
            if content:
                seen.add(content)
        print(f"現在挿入されているブロック種別: {len(seen)}")
        for c in seen:
            print("---")
            print(c)
        return

    snippet = build_snippets(args.adsense, args.ga4, args.search_console)
    print("挿入する内容:")
    print(snippet)
    print("---")

    ok = ng = 0
    for f in files:
        success, msg = inject(f, snippet)
        if success:
            ok += 1
        else:
            ng += 1
            if msg != "unchanged":
                print(f"WARN {f}: {msg}")
    print(f"完了: 更新 {ok} / 変更なし {ng}")


if __name__ == "__main__":
    main()
