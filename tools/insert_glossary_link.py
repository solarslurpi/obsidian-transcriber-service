import re
import os

# Path to your glossary file
GLOSSARY_PATH = r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\docs\README_glossary.md"
# Folder with your markdown files
MARKDOWN_FOLDER = r"C:\Users\happy\Documents\Projects\obsidian-transcriber-service\docs\test"

def load_glossary(path):
    with open(path, 'r') as f:
        content = f.read()
    terms = re.findall(r'## (.+)\n', content)
    return {term: f'[{term}](#{term})' for term in terms}

def link_terms_in_file(filepath, glossary):
    with open(filepath, 'r') as f:
        content = f.read()

    for term, link in glossary.items():
        # Use word boundaries to match the term exactly
        content = re.sub(rf'\b{re.escape(term)}\b', link, content)

    with open(filepath, 'w') as f:
        f.write(content)

glossary = load_glossary(GLOSSARY_PATH)

for filename in os.listdir(MARKDOWN_FOLDER):
    if filename.endswith(".md"):
        link_terms_in_file(os.path.join(MARKDOWN_FOLDER, filename), glossary)