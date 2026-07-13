#!/usr/bin/env python3
import os
import re
import shutil
import json

BASE_DIR = "/Users/phyzik/Desktop/forecastai"
ITEM_DIR = os.path.join(BASE_DIR, "item")
KO_POSTS_DIR = os.path.join(BASE_DIR, "ko", "posts")
EN_POSTS_DIR = os.path.join(BASE_DIR, "en", "posts")
KO_BIB = os.path.join(BASE_DIR, "ko", "references.bib")
EN_BIB = os.path.join(BASE_DIR, "en", "references.bib")

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def merge_bib(src_bib_path, dest_bib_path):
    if not os.path.exists(src_bib_path):
        return
    with open(src_bib_path, 'r', encoding='utf-8') as f:
        src_content = f.read()
    
    # Extract keys already in destination to avoid duplicates
    existing_keys = set()
    if os.path.exists(dest_bib_path):
        with open(dest_bib_path, 'r', encoding='utf-8') as f:
            dest_content = f.read()
        existing_keys = set(re.findall(r'@\w+\{([^,]+),', dest_content))
    
    # Parse source entries
    entries = re.split(r'\n(?=@)', src_content)
    new_entries = []
    for entry in entries:
        match = re.search(r'@\w+\{([^,]+),', entry)
        if match:
            key = match.group(1).strip()
            if key not in existing_keys:
                new_entries.append(entry.strip())
                
    if new_entries:
        with open(dest_bib_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + "\n\n".join(new_entries) + "\n")

def process_frontmatter(qmd_path, language):
    with open(qmd_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    frontmatter_match = re.match(r'^---(.*?)---', content, re.DOTALL)
    if not frontmatter_match:
        return None, None
        
    frontmatter_raw = frontmatter_match.group(1)
    body = content[frontmatter_match.end():]
    
    # Parse title, date, categories
    title_match = re.search(r'^title:\s*["\']?(.*?)["\']?$', frontmatter_raw, re.MULTILINE)
    date_match = re.search(r'^date:\s*["\']?(.*?)["\']?$', frontmatter_raw, re.MULTILINE)
    
    title = title_match.group(1) if title_match else "untitled"
    date = date_match.group(1) if date_match else "2026-07-05"
    
    # Replace author
    frontmatter_raw = re.sub(r'^author:.*$', 'author: "Prof. Shin"', frontmatter_raw, flags=re.MULTILINE)
    # Replace freeze
    if re.search(r'^execute:', frontmatter_raw, re.MULTILINE):
        frontmatter_raw = re.sub(r'freeze:.*$', 'freeze: true', frontmatter_raw, flags=re.MULTILINE)
    else:
        frontmatter_raw += "\nexecute:\n  freeze: true"
        
    # Replace number-sections and code-tools
    frontmatter_raw = re.sub(r'^number-sections:.*$', 'number-sections: false', frontmatter_raw, flags=re.MULTILINE)
    frontmatter_raw = re.sub(r'^code-tools:.*$', 'code-tools: false', frontmatter_raw, flags=re.MULTILINE)
    
    # Ensure thumbnail.jpg is referenced
    frontmatter_raw = re.sub(r'^image:.*$', 'image: "thumbnail.jpg"', frontmatter_raw, flags=re.MULTILINE)
    
    # Save modified qmd
    new_content = f"---{frontmatter_raw}---{body}"
    with open(qmd_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    return title, date

def main():
    zip_files = [f for f in os.listdir(ITEM_DIR) if f.endswith('.zip')]
    if zip_files:
        print(f"Found zip files: {zip_files}. Please unzip them first.")
        return json.dumps({"status": "zip_pending", "files": zip_files})
        
    ko_src = os.path.join(ITEM_DIR, "index_ko.qmd")
    en_src = os.path.join(ITEM_DIR, "index_en.qmd")
    bib_src = os.path.join(ITEM_DIR, "references.bib")
    
    if not os.path.exists(ko_src) or not os.path.exists(en_src):
        return json.dumps({"status": "no_posts"})
        
    # Read titles and dates
    ko_title, ko_date = process_frontmatter(ko_src, "ko")
    en_title, en_date = process_frontmatter(en_src, "en")
    
    # Create directory slug using English title
    slug = f"{en_date}-{slugify(en_title)}"
    
    ko_dest_dir = os.path.join(KO_POSTS_DIR, slug)
    en_dest_dir = os.path.join(EN_POSTS_DIR, slug)
    
    os.makedirs(ko_dest_dir, exist_ok=True)
    os.makedirs(en_dest_dir, exist_ok=True)
    
    # Move qmd files
    shutil.move(ko_src, os.path.join(ko_dest_dir, "index.qmd"))
    shutil.move(en_src, os.path.join(en_dest_dir, "index.qmd"))
    
    # Merge bibliography
    if os.path.exists(bib_src):
        merge_bib(bib_src, KO_BIB)
        merge_bib(bib_src, EN_BIB)
        os.remove(bib_src)
        
    report = {
        "status": "success",
        "slug": slug,
        "en_title": en_title,
        "ko_title": ko_title,
        "ko_dest": os.path.join(ko_dest_dir, "index.qmd"),
        "en_dest": os.path.join(en_dest_dir, "index.qmd")
    }
    print(json.dumps(report, indent=2))
    return json.dumps(report)

if __name__ == "__main__":
    main()
