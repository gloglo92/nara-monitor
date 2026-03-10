"""
수집된 데이터를 JSON으로 변환하여 data/ 폴더에 저장
- 원본 전체 데이터 저장
- 레저조경부 키워드 필터링 결과도 함께 저장
- data/index.json 날짜 목록 갱신
"""

import json
import os
from datetime import datetime
from pathlib import Path
import pandas as pd

# ── 레저조경부 확정 키워드 (INCLUDE) ─────────────────────────
INCLUDE_KEYWORDS = [
    # ── 기존 키워드 ───────────────────────────────────────────
    "공원", "경관", "관광", "관광지", "관광자원", "관광단지",
    "지역개발", "지역활성화", "농어촌", "농촌", "어촌",
    "생태", "녹지", "산림", "숲", "수변", "자연경관",
    "에코파크", "생태공원", "정원", "치유의숲", "산림치유", "도시숲",
    "조경", "경관설계", "아름다운거리", "가로경관", "경관개선", "가로수",
    "테마파크", "테마", "레저", "힐링", "리조트", "휴양",
    "스카이브릿지", "전망대", "출렁다리", "짚라인", "어드벤처",
    "유원지", "캠핑", "글램핑",
    "둘레길", "탐방로", "산책로", "트레킹", "자전거길", "그린웨이",
    "해양관광", "해안", "갯벌", "섬관광", "강변", "해변",
    "문화관광", "문화재", "역사문화", "유산", "근대역사", "역사공원",
    "도시재생", "마을만들기", "마을조성", "마을재생",
    "권역개발", "거점개발", "지역특화",
    "체육", "스포츠", "레포츠", "수상레저",

    # ── 직접 추가 요청 키워드 ─────────────────────────────────
    "친수공간", "물순환", "친수", "은퇴자마을", "골목재생", "명소화", "명소",
    "트레일", "여가", "레져", "워터파크", "녹화", "박람회",
    "식재", "파크", "골프", "바람길", "해안길", "수변길", "테마로드",
    "복원", "복지", "콘텐츠", "문화", "복합문화", "신활력", "거점",
    "복합", "놀이터", "철도복개", "쉼터", "자연", "에코",
    "호국원", "야생", "동물", "관찰원", "치유원",
    "트리탑로드", "스카이로드", "로드",

    # ── 기후대응/생태 ─────────────────────────────────────────
    "기후대응도시숲", "스마트도시숲", "도시바람길숲", "미세먼지차단숲", "미세먼지", "차단숲",
    "탄소저장숲", "탄소중립", "산림생태복원", "자생식물",
    "훼손지복구", "대체산림조성", "사방댐", "산림경관", "산림복지",

    # ── 정원/해양/어촌 ───────────────────────────────────────
    "국가정원", "지방정원", "정원도시", "정원비엔날레",
    "어촌뉴딜", "어촌신활력", "K-관광섬",
    "해양레저", "갯벌생태",

    # ── 마이크로 레저/복합공간 ───────────────────────────────
    "맨발걷기", "파크골프", "복합스포츠", "무장애탐방",
    "산림치유원", "유아숲체험", "반려견",
    "매립장", "복개",

    # ── 제도/기획/컨설팅 ─────────────────────────────────────
    "민간공원", "장기미집행", "일몰제", "기부채납",
    "기본구상", "타당성조사", "마스터플랜",
    "조성계획", "경관계획", "공원녹지기본계획",
    "활용방안",
]

# ── 완전제외 키워드 (확정·검토 어디에도 안 보임) ─────────────
HARD_EXCLUDE_KEYWORDS = [
    "건설사업관리",
]

# ── 확정→검토 강등 키워드 (INCLUDE에 걸려도 검토로 이동) ──────
SOFT_EXCLUDE_KEYWORDS = [
    "재해위험",   # 자연재해위험개선지구 정비사업
    "급경사지",   # 급경사지 붕괴위험지구 정비
    "소하천",     # 소하천 정비사업
    "하수관",     # 하수관로 정비
    "도로",       # 단순 도로 설계
    "교량",       # 교량 설계
    "상수도",     # 상수도 정비
    "하천정비",   # 하천정비 기본계획
    "치수",       # 치수사업
]


def get_name_field(data_type: str) -> str:
    """데이터 타입에 따른 사업명 필드 반환"""
    if data_type == "사전규격":
        return "사업명(품명)"
    return "사업명"


def leisure_filter(items: list[dict], name_field: str) -> list[dict]:
    """
    레저조경부 필터링
    - HARD_EXCLUDE 포함 항목: 확정/검토 어디에도 포함 안 함
    - SOFT_EXCLUDE 포함 항목: INCLUDE에 걸려도 검토로 이동
    - confirmed: INCLUDE 매칭 + SOFT_EXCLUDE 미해당
    - review: 나머지 전체 (SOFT_EXCLUDE 강등 포함)
    반환: {"confirmed": [...], "review": [...]}
    """
    confirmed = []
    review = []

    for item in items:
        name = str(item.get(name_field, ""))

        # 완전 제외 (확정·검토 둘 다 제외)
        if any(ex in name for ex in HARD_EXCLUDE_KEYWORDS):
            continue

        # 확정→검토 강등 (SOFT_EXCLUDE 단어 포함 시 검토로)
        if any(ex in name for ex in SOFT_EXCLUDE_KEYWORDS):
            review.append(item)
            continue

        matched = [kw for kw in INCLUDE_KEYWORDS if kw in name]
        if matched:
            confirmed.append({**item, "_matched": ", ".join(matched)})
        else:
            review.append(item)

    return {"confirmed": confirmed, "review": review}


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame → JSON 직렬화 가능한 dict 리스트"""
    records = []
    for _, row in df.iterrows():
        rec = {}
        for k, v in row.items():
            if pd.isna(v) if not isinstance(v, str) else False:
                rec[k] = ""
            else:
                rec[k] = str(v) if not isinstance(v, (int, float, str, bool)) else v
        records.append(rec)
    return records


def save_json_data(df: pd.DataFrame, date_str: str, data_type: str) -> None:
    """
    수집된 DataFrame을 JSON으로 저장
    - data/YYYYMMDD-타입.json : 원본 전체
    - data/YYYYMMDD-타입-filtered.json : 레저조경부 필터 결과
    - data/index.json : 날짜 목록 갱신
    """
    # scripts/ 에서 실행되므로 두 단계 위 → repo 루트 / docs / data
    data_dir = Path(__file__).parent.parent / "docs" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    name_field = get_name_field(data_type)
    all_items  = df_to_records(df)

    # ── 1. 원본 전체 저장 ──────────────────────────────────────
    raw_path = data_dir / f"{date_str}-{data_type}.json"
    raw_payload = {
        "date":         date_str,
        "type":         data_type,
        "total":        len(all_items),
        "generated_at": datetime.now().isoformat(),
        "items":        all_items,
    }
    raw_path.write_text(
        json.dumps(raw_payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 저장: {raw_path} ({len(all_items)}건)")

    # ── 2. 레저조경부 필터링 결과 저장 ────────────────────────
    filtered = leisure_filter(all_items, name_field)
    confirmed_items = filtered["confirmed"]
    review_items    = filtered["review"]

    filtered_path = data_dir / f"{date_str}-{data_type}-filtered.json"
    filtered_payload = {
        "date":             date_str,
        "type":             data_type,
        "total":            len(all_items),
        "confirmed_count":  len(confirmed_items),
        "review_count":     len(review_items),
        "generated_at":     datetime.now().isoformat(),
        "confirmed":        confirmed_items,
        "review":           review_items,
    }
    filtered_path.write_text(
        json.dumps(filtered_payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 저장: {filtered_path} (확정 {len(confirmed_items)}건 / 검토 {len(review_items)}건)")

    # ── 3. index.json 갱신 ────────────────────────────────────
    index_path = data_dir / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {"dates": [], "types": ["사전규격", "발주계획"]}

    # 날짜 추가 (중복 제거, 내림차순 정렬)
    dates = set(index.get("dates", []))
    dates.add(date_str)
    index["dates"]  = sorted(dates, reverse=True)
    index["latest"] = index["dates"][0]

    # 해당 날짜 요약 정보 갱신
    summary = index.get("summary", {})
    if date_str not in summary:
        summary[date_str] = {}
    summary[date_str][data_type] = {
        "total":     len(all_items),
        "confirmed": len(confirmed_items),
        "review":    len(review_items),
    }
    index["summary"] = summary

    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ index.json 갱신: {date_str} / {data_type}")
