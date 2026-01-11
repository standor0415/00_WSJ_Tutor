from bs4 import BeautifulSoup

import sys

html_content = sys.stdin.read()

if not html_content:
    print("No data has been entered", file=sys.stderr)
    sys.exit(1)

soup = BeautifulSoup(html_content, "html.parser")

tags = soup.select(
    'div.article-header h1, div.article-header h2, h3[data-type="hed"], p[data-type="paragraph"]'
)

for tag in tags:
    text = tag.get_text(strip=True)

    if tag.name == "h1":
        print(f"# {text}")
    elif tag.name == "h2":
        print(f"## {text}")
    elif tag.name == "h3":
        print(f"### {text}")
    else:
        print(f"{text}")
