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
    original_date = date_match.group(1) if date_match else ""
    
    # Auto-enrich categories based on title and body content
    categories = []
    categories_match = re.search(r'^categories:\s*\n((?:\s*-\s*.*?\n)+)', frontmatter_raw, re.MULTILINE)
    inline_match = re.search(r'^categories:\s*\[(.*?)\]', frontmatter_raw, re.MULTILINE)
    
    if categories_match:
        existing_block = categories_match.group(1)
        categories = [line.strip().lstrip('-').strip() for line in existing_block.splitlines() if line.strip()]
    elif inline_match:
        categories = [c.strip().strip('"').strip("'") for c in inline_match.group(1).split(',') if c.strip()]
        
    keyword_rules = {
        "autograd": (["autograd", "backward", "역전파"], ["Autograd", "역전파", "텐서"], ["Autograd", "Backpropagation", "Tensor"]),
        "quantile": (["quantile", "probabilistic", "분위수", "확률적"], ["분위수 회귀", "확률적 예측"], ["Quantile Regression", "Probabilistic Forecasting"]),
        "informer": (["informer", "patchtst"], ["Informer", "PatchTST", "어텐션 병목"], ["Informer", "PatchTST", "Attention Bottleneck"]),
        "revin": (["revin", "non-stationary", "stationarity", "비정상", "정상성"], ["RevIN", "가역 정규화", "비정상 시계열"], ["RevIN", "Reversible Instance Normalization", "Non-stationary Time Series"]),
        "multi-step": (["multi-step", "forecasting strategies", "멀티 스텝", "예측 전략"], ["멀티 스텝 예측", "예측 전략"], ["Multi-step Forecasting", "Forecasting Strategies"]),
        "physics": (["physics-informed", "pinn", "물리 제약", "물리 정보"], ["물리 제약 신경망", "PINN", "물리 정보"], ["Physics-informed Neural Networks", "PINN", "Physics-informed"]),
        "tokenization": (["tokenization", "bpe", "wordpiece", "토큰화"], ["토큰화", "BPE", "WordPiece"], ["Tokenization", "BPE", "WordPiece"]),
    }
    
    body_lower = body.lower()
    title_lower = title.lower()
    new_tags = []
    
    # Add DataLoader rule dynamically
    keyword_rules["dataloader"] = (
        ["dataloader", "sliding window", "슬라이딩 윈도우", "데이터로더"],
        ["데이터로더", "슬라이딩 윈도우", "PyTorch"],
        ["DataLoader", "Sliding Window", "PyTorch"]
    )
    
    for key, (keywords, ko_tags, en_tags) in keyword_rules.items():
        # Heuristic: keyword must be in the title, OR appear at least 3 times in the body text
        match = False
        for kw in keywords:
            kw_l = kw.lower()
            if kw_l in title_lower or body_lower.count(kw_l) >= 3:
                match = True
                break
        if match:
            tags_to_add = ko_tags if language == "ko" else en_tags
            for tag in tags_to_add:
                if tag not in categories and tag not in new_tags:
                    new_tags.append(tag)
                    
    if new_tags:
        print(f"[{language.upper()}] Automatically enriching categories: {new_tags}")
        categories.extend(new_tags)
        categories_yaml = "categories:\n" + "\n".join(f"  - {c}" for c in categories)
        if categories_match:
            frontmatter_raw = frontmatter_raw.replace(categories_match.group(0), categories_yaml + "\n")
        elif inline_match:
            frontmatter_raw = frontmatter_raw.replace(inline_match.group(0), categories_yaml)
        else:
            frontmatter_raw += "\n" + categories_yaml
    
    # Automatically force date to today's date (deployment date)
    import datetime
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    if original_date != today_str:
        print(f"[{language.upper()}] Updating post date from '{original_date}' to today's date '{today_str}' for deployment.")
        if original_date:
            frontmatter_raw = re.sub(r'^date:.*$', f'date: "{today_str}"', frontmatter_raw, flags=re.MULTILINE)
        else:
            frontmatter_raw += f'\ndate: "{today_str}"'
            
    date = today_str
    
    # Replace author
    frontmatter_raw = re.sub(r'^author:.*$', 'author: "Prof. Shin"', frontmatter_raw, flags=re.MULTILINE)
    # Replace bibliography to use the global shared bib file
    frontmatter_raw = re.sub(r'^bibliography:.*$', 'bibliography: ../../references.bib', frontmatter_raw, flags=re.MULTILINE)
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
    
    # Insert hero image at the top of the body for SEO
    hero_markdown = (
        '\n\n![[개념 시각화] 본 포스트의 핵심 개념을 요약한 다이어그램입니다.](thumbnail.jpg){fig-align="center" width="90%"}\n\n'
        if language == "ko" else
        '\n\n![[Concept Visualization] A diagram summarizing the key concepts of this post.](thumbnail.jpg){fig-align="center" width="90%"}\n\n'
    )
    
    # Avoid duplicate injection if already present
    if "thumbnail.jpg" not in body:
        new_content = f"---{frontmatter_raw}---{hero_markdown}{body}"
    else:
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
