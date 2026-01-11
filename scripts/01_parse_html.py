from bs4 import BeautifulSoup

import sys

html_content = sys.stdin.read()

if not html_content:
  print('No data has been entered', file=sys.stderr)
  sys.exit(1)

soup = BeautifulSoup(html_content, 'html.parser')

tags = soup.select('p[data-type="paragraph"], h1[data-testid="headline"], h2[data-testid="dek-block"], h3[data-type="hed"]')

for tag in tags:
  if tag.name == 'h1':
    print(f"# {tag.get_text()}")
  elif tag.name == 'h2':
    print(f"## {tag.get_text()}")
  elif tag.name == 'h3':
    print(f'### {tag.get_text()}')
  else:
    print(tag.get_text())