from bs4 import BeautifulSoup
from pathlib import Path

import sys

VER_1 = 'div.article-header h1, div.article-header h2, h3[data-type="hed"], p[data-type="paragraph"]'
VER_2 = 'h1[data-testid="headline"], h2[data-testid="dek-block"], h3[data-type="hed"], p[data-type="paragraph"]'


def parse_html(file_path: Path | str) -> str:
    # Read file according to path
    path = Path(file_path)
    html_content = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "html.parser")

    # Classifiy a html version, find new version assert error
    tags = soup.select(VER_1)
    if tags[0].name != "h1" or tags[1].name != "h2":
        tags = soup.select(VER_2)
        if tags[0].name != "h1" or tags[1].name != "h2":
            sys.exit("Require new version")

    full_text = []
    # parsing html and make a new md file
    for tag in tags:
        text = " ".join(tag.get_text().split())

        if tag.name == "h1":
            full_text.append(f"# {text}")
        elif tag.name == "h2":
            full_text.append(f"## {text}")
        elif tag.name == "h3":
            full_text.append(f"### {text}")
        else:
            full_text.append(f"{text}")

    # return md file path
    project_path = path.parent.parent
    output_dir = project_path / "output/markdown"
    filename = path.stem.replace("main", "article")
    output_file = output_dir / f"{filename}.md"  #

    output_dir.mkdir(parents=True, exist_ok=True)

    output_file.write_text("\n".join(full_text), encoding="utf-8")
    print(f"Create new md file!")

    return output_file
