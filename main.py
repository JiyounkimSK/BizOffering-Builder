import streamlit as st
from workflow.graph import create_offering_graph

st.set_page_config(page_title="BizOffering-Builder", page_icon="🏭", layout="wide")
st.title("🏭 제조 IT 사업수행 & 오퍼링 기획 자동화 에이전트")
st.caption("Delivery 기술 메모를 사내 표준 Offering 1-Pager와 세일즈 카드로 자동 변환합니다.")

with st.sidebar:
    st.header("📌 신규 기술 사양 입력")
    target_customer = st.selectbox("타깃 고객사", ["SK온 (배터리)", "SK하이닉스 (반도체)", "SK이노베이션 (화학)"])
    default_note = "배터리 셀 조밀 용접 라인에서 비전 영상 기반 결함 탐지 딥러닝 모델 개발 완료. 기존 룰 검사 대비 미검출률 70% 감소. 공정 폐쇄망 서버 지원 필요."
    tech_note = st.text_area("사업수행팀 기술/PoC 요약 메모", value=default_note, height=180)
    build_btn = st.button("🚀 Offering 기획서 자동 생성", type="primary")

if build_btn:
    initial_state = {
        "raw_tech_note": tech_note,
        "target_customer": target_customer,
        "revision_count": 0
    }
    
    graph = create_offering_graph()
    
    with st.spinner("Multi-Agent 파이프라인 가동 중... (가치 변환 ➔ RAG 매핑 ➔ MCP 인프라 원가 산출 ➔ PMO 검증 ➔ 산출물 빌드)"):
        res = graph.invoke(initial_state)
        doc = res.get("final_output")

    if doc:
        st.success("✅ 표준 Offering 사업화 기획서가 발행되었습니다.")
        tab1, tab2, tab3 = st.tabs(["📄 Offering 1-Pager (표준 규격)", "💼 Account 세일즈 카드", "⚙️ 인프라 원가 분석 (MCP)"])
        
        with tab1:
            st.header(doc.offering_name)
            st.markdown(f"**분류 경로:** `{doc.category_path}` | **타깃 구매자:** `{doc.target_buyer}`")
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("⚠️ 고객 현장 핵심 Pain-Point")
                for p in doc.customer_pain_points:
                    st.write(f"- {p}")
            with c2:
                st.subheader("💡 정량적 비즈니스 가치")
                for v in doc.core_value_propositions:
                    st.write(f"- {v}")
                    
            st.divider()
            st.subheader("📈 3단계 상용화 딜 구조")
            for d in doc.deal_structure:
                st.write(f"- {d}")

        with tab2:
            st.subheader("🎯 Account(영업) 전달용 Sales Talking Points")
            st.info("고객 미팅 시 복잡한 알고리즘 대신 아래 비즈니스 키워드로 오프닝하세요.")
            for tip in doc.sales_talking_points:
                st.write(f"👉 {tip}")

        with tab3:
            st.subheader("⚙️ 외부 MCP 연동 GPU 인프라 TCO 산출 내역")
            st.code(doc.infra_tco_guide, language="text")
            st.caption("※ 퍼블릭 클라우드 표준 요율 및 제조 공정 폐쇄망 보안 계수를 결합하여 산출되었습니다.")
