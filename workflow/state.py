from typing import TypedDict, List, Dict, Optional
from pydantic import BaseModel, Field

class OfferingDocument(BaseModel):
    offering_name: str = Field(description="공식 Offering 명칭 (국문/영문)")
    category_path: str = Field(description="사내 Offering Map 분류 경로 (대분류 > 중분류)")
    target_buyer: str = Field(description="고객사 타깃 의사결정자 (예: 공장장, 생산기술팀장)")
    customer_pain_points: List[str] = Field(description="고객 핵심 현장 페인포인트 3가지")
    core_value_propositions: List[str] = Field(description="정량적 비즈니스 가치 (수율, 비용 절감치)")
    deal_structure: List[str] = Field(description="3단계 상용화 딜 구조 (PoC -> 본사업 -> SLA)")
    infra_tco_guide: str = Field(description="하드웨어/클라우드 인프라 연간 원가 가이드")
    sales_talking_points: List[str] = Field(description="Account 영업 전달용 세일즈 카드")

class OfferingBuilderState(TypedDict):
    raw_tech_note: str
    target_customer: str
    value_data: Dict
    retrieved_docs: List[str]
    category: str
    infra_cost: Dict
    commercial_plan: Dict
    validation_status: str
    revision_count: int
    final_output: Optional[OfferingDocument]
