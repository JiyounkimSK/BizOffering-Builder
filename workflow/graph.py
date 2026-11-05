import os
from langgraph.graph import StateGraph, END
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from workflow.state import OfferingBuilderState, OfferingDocument
from tools.infra_mcp import calculate_infra_tco

api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AOAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AOAI_ENDPOINT")
embed_deployment = os.getenv("AOAI_DEPLOY_EMBED_3_SMALL", "ait1-prd-text-embedding-3-small")
chat_deployment = os.getenv("AOAI_DEPLOY_GPT41_MINI", "ait1-prd-gpt-4.1-mini")

llm = AzureChatOpenAI(
    azure_deployment=chat_deployment,
    api_version="2024-02-01",
    api_key=api_key,
    azure_endpoint=azure_endpoint,
    temperature=0.2
)

sample_knowledge = [
    "[Offering Map] 스마트팩토리 > AI 제조 품질/수율 최적화: 가상 계측, 초정밀 비전 결함 검사, 이상 진단 FDC",
    "[Offering Map] 스마트팩토리 > 공정 환경/에너지 최적화: 탄소 원장 플랫폼, 전력/스팀 APC 에너지 절감",
    "[수주 레퍼런스] A사 반도체 후공정 팹 비전 검사 구축 (PoC 3개월 후 전 라인 롤아웃, 수율 1.8%p 개선)",
    "[거버넌스 기준] 신규 Offering은 마진율 18% 이상을 목표로 하며, 인프라 비용은 Pass-through로 고객 별도 청구"
]

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=embed_deployment,
    api_version="2024-02-01",
    api_key=api_key,
    azure_endpoint=azure_endpoint
)
vectorstore = FAISS.from_texts(sample_knowledge, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

def value_engineer_node(state: OfferingBuilderState):
    prompt = ChatPromptTemplate.from_template(
        "당신은 제조 IT 전략 컨설턴트입니다. 사업수행팀 기술 메모를 고객사 임원 관점의 비즈니스 가치로 변환하세요.\n\n"
        "기술 메모: {tech_note}\n고객사: {customer}\n"
        "고객 페인포인트와 정량적 수율/비용 절감 효과 중심으로 정리하세요."
    )
    res = (prompt | llm).invoke({"tech_note": state["raw_tech_note"], "customer": state["target_customer"]})
    return {"value_data": {"summary": res.content}}

def rag_retriever_node(state: OfferingBuilderState):
    query = state["raw_tech_note"]
    docs = retriever.invoke(query)
    context_text = [d.page_content for d in docs]
    return {
        "retrieved_docs": context_text,
        "category": "스마트팩토리 > AI 제조 품질/수율 최적화"
    }

def commercial_mcp_node(state: OfferingBuilderState):
    tco_res = calculate_infra_tco(gpu_type="T4", gpu_count=2, is_closed_network=True)
    return {
        "infra_cost": tco_res,
        "commercial_plan": {
            "tier1": "3개월 알고리즘 검증 유료 PoC",
            "tier2": "마더팩토리 전 라인 확산 구축형(SI)",
            "tier3": "지속적 MLOps 연간 구독 유지운영"
        }
    }

def pmo_validator_node(state: OfferingBuilderState):
    count = state.get("revision_count", 0)
    if count >= 1:
        return {"validation_status": "PASS"}
    return {"validation_status": "PASS", "revision_count": count + 1}

def document_generator_node(state: OfferingBuilderState):
    structured_llm = llm.with_structured_output(OfferingDocument)
    prompt = ChatPromptTemplate.from_template(
        "수집된 비즈니스 가치, RAG 표준 지식, 인프라 TCO를 바탕으로 완성형 Offering 1-Pager 기획서를 생성하세요.\n\n"
        "가치 데이터: {value_data}\n"
        "사내 매핑 지식: {retrieved_docs}\n"
        "인프라 원가: {infra_guide}\n"
        "딜 구조: {commercial_plan}"
    )
    final_doc = (prompt | structured_llm).invoke({
        "value_data": state["value_data"]["summary"],
        "retrieved_docs": "\n".join(state["retrieved_docs"]),
        "infra_guide": state["infra_cost"]["guide_text"],
        "commercial_plan": str(state["commercial_plan"])
    })
    return {"final_output": final_doc}

def create_offering_graph():
    builder = StateGraph(OfferingBuilderState)
    builder.add_node("value_engineer", value_engineer_node)
    builder.add_node("rag_retriever", rag_retriever_node)
    builder.add_node("commercial_mcp", commercial_mcp_node)
    builder.add_node("pmo_validator", pmo_validator_node)
    builder.add_node("doc_generator", document_generator_node)

    builder.set_entry_point("value_engineer")
    builder.add_edge("value_engineer", "rag_retriever")
    builder.add_edge("rag_retriever", "commercial_mcp")
    builder.add_edge("commercial_mcp", "pmo_validator")
    builder.add_conditional_edges(
        "pmo_validator",
        lambda state: state["validation_status"],
        {"REVISE": "commercial_mcp", "PASS": "doc_generator"}
    )
    builder.add_edge("doc_generator", END)
    return builder.compile()
