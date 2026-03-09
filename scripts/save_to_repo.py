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

# ── 레저조경부 2차 필터 키워드 ────────────────────────────────
INCLUDE_KEYWORDS = [
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
]

EXCLUDE_KEYWORDS = [
    # ── 건설사업관리본부 ───────────────────────────────────────
    # 별도 본부(건설사업관리1·2부, 기술지원1·2부) 업무 영역
    "건설사업관리",

    # ── 수도사업본부 (상하수도1·2·3부, O&M사업부) ──────────────
    "상수도", "하수도", "상수관", "하수관", "배수관",
    "정수장", "수도관망", "급수", "오수", "펌프장",
    "노후상수", "노후하수", "수도정비",
    "수리시설", "양수장",

    # ── 도로공항부 ─────────────────────────────────────────────
    "도로건설", "도로포장", "포장공사", "도로확포장", "도로개설",
    "공항", "활주로",
    "군도", "도시계획시설",

    # ── 수자원부 ───────────────────────────────────────────────
    "댐", "저수지", "하천정비", "홍수", "치수", "수자원",
    "계통확장", "계통사업", "계통공사",

    # ── 철도·구조사업부 ────────────────────────────────────────
    "철도건설", "도시철도", "교량", "터널구조", "지하철",

    # ── 항만부 ─────────────────────────────────────────────────
    "항만", "부두", "선착장", "방파제", "어항",

    # ── 지반터널부 ─────────────────────────────────────────────
    "터널", "지반조사", "연약지반", "굴착",

    # ── 교통계획부 ─────────────────────────────────────────────
    "교통영향평가", "교통계획", "신호체계", "주차",

    # ── 기전시스템부 ───────────────────────────────────────────
    "전기설비", "기계설비", "소방설비", "관망감시",

    # ── 환경평가부 ─────────────────────────────────────────────
    "환경영향평가", "소음진동", "대기오염",

    # ── 에너지·환경사업부 ──────────────────────────────────────
    "에너지사업", "산업단지", "공업단지", "산단", "온산",
    "발전사업", "전력사업", "신재생에너지",
    "기계엔지니어링", "플랜트", "전기공사", "전력설비",
    "배전", "송전", "변전", "발전소", "열병합",
    "DX", "디지털트윈", "스마트팩토리", "가상융합",
    "ICT", "IoT", "AI시스템", "빅데이터", "클라우드",
    "정보시스템", "소프트웨어", "데이터센터",

    # ── 교육·연구 ──────────────────────────────────────────────
    "교육운영", "교육연구", "검사문항", "학습연구", "교육종합",

    # ── 경찰·행정 시설 ─────────────────────────────────────────
    "지구대", "파출소", "경찰서",

    # ── 주거·임대 (단지설계부 업무) ───────────────────────────
    "노후임대", "임대주택", "공공임대",

    # ── 기타 편의·안전 시설 (레저조경 무관) ───────────────────
    "이동편의시설", "승강편의시설", "내진보강",
    "소방서", "노면표시", "자연재해",

    # ── 기타 명확히 무관 ───────────────────────────────────────
    "리튬배터리", "화재안전보관", "반부조", "밀폐용",
]


def get_name_field(data_type: str) -> str:
    """데이터 타입에 따른 사업명 필드 반환"""
    if data_type == "사전규격":
        return "사업명(품명)"
    return "사업명"


def leisure_filter(items: list[dict], name_field: str) -> list[dict]:
    """레저조경부 2차 키워드 필터링"""
    result = []
    for item in items:
        name = str(item.get(name_field, ""))
        if any(ex in name for ex in EXCLUDE_KEYWORDS):
            continue
        matched = [kw for kw in INCLUDE_KEYWORDS if kw in name]
        if matched:
            result.append({**item, "_matched": ", ".join(matched)})
    return result


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
    filtered_items = leisure_filter(all_items, name_field)
    filtered_path  = data_dir / f"{date_str}-{data_type}-filtered.json"
    filtered_payload = {
        "date":              date_str,
        "type":              data_type,
        "total":             len(all_items),
        "filtered_count":    len(filtered_items),
        "generated_at":      datetime.now().isoformat(),
        "items":             filtered_items,
    }
    filtered_path.write_text(
        json.dumps(filtered_payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 저장: {filtered_path} ({len(filtered_items)}건 필터링)")

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
        "total":    len(all_items),
        "filtered": len(filtered_items),
    }
    index["summary"] = summary

    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ index.json 갱신: {date_str} / {data_type}")
