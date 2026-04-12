# AI·DATA LAB

AI 및 데이터 사이언스 연구 블로그 | Prof. Shin (phyzik)

## 구조

```
my-blog/
├── index.html          # 루트 (언어 자동 감지 → ko/ 또는 en/ 리다이렉트)
├── custom.scss         # 공통 스타일
├── ko/                 # 한글 사이트
│   ├── _quarto.yml
│   ├── index.qmd
│   └── posts/
└── en/                 # 영문 사이트
    ├── _quarto.yml
    ├── index.qmd
    └── posts/
```

## 로컬 실행

```bash
# 한글 사이트 미리보기
cd ko && quarto preview

# 영문 사이트 미리보기
cd en && quarto preview
```

## 글 작성

```bash
# 한글 글
ko/posts/YYYY-MM-DD-제목/index.qmd

# 영문 글 (동일 주제)
en/posts/YYYY-MM-DD-title/index.qmd
```

## 배포

```bash
git add .
git commit -m "새 글: 제목"
git push origin main
# → GitHub Actions가 자동으로 빌드 및 배포
```

## GitHub Pages 최초 설정

1. GitHub에서 레포 생성
2. Settings → Pages → Source: `gh-pages` 브랜치 선택
3. `main` 브랜치에 push하면 자동 배포
