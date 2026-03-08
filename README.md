# 🌿 레저조경부 나라장터 모니터

나라장터 기술용역 **사전규격** + **발주계획** 자동 수집 → 레저조경부 필터링 → 웹페이지 누적 조회

---

## 📁 구조

```
nara-monitor/
├── .github/workflows/nara_fetch.yml   # 매일 KST 06:00 자동 실행
├── scripts/
│   ├── fetch_narajangteo.py           # 사전규격 수집
│   ├── fetch_orderplan.py             # 발주계획 수집
│   └── save_to_repo.py                # JSON 변환 + 저장
├── data/                              # 수집 데이터 누적 (자동 생성)
│   ├── index.json
│   ├── YYYYMMDD-사전규격.json
│   ├── YYYYMMDD-사전규격-filtered.json
│   └── ...
└── docs/                              # GitHub Pages 웹페이지
    └── index.html
```

---

## ⚙️ 설정 방법

### 1. Repo 생성
```
GitHub → New repository → 이름: nara-monitor → Public → Create
```

### 2. 파일 업로드
이 폴더의 모든 파일을 그대로 업로드

### 3. GitHub Secrets 등록
`Settings → Secrets and variables → Actions → New repository secret`

| 이름 | 값 |
|------|-----|
| `NARA_API_KEY` | 공공데이터포털 API 키 |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 텔레그램 채널/채팅 ID |

### 4. GitHub Pages 활성화
`Settings → Pages → Source: Deploy from a branch → Branch: main, /docs → Save`

### 5. 비밀번호 변경 (선택)
`docs/index.html` 상단의 `PASSWORD_HASH` 라인에서 문자열 수정:
```javascript
const PASSWORD_HASH = hashStr("원하는비밀번호");
```

---

## 🌐 웹페이지 주소

```
https://[GitHub계정명].github.io/nara-monitor
```

---

## 🔄 수동 실행 (테스트)

`Actions → 나라장터 기술용역 수집 → Run workflow`
- 특정 날짜: `target_date` 에 `YYYYMMDD` 형식 입력
- 전일 자동: 빈칸으로 실행

---

## 🔑 기본 비밀번호

```
leisure2026!
```
> ⚠️ 배포 전 반드시 변경하세요
