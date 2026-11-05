def calculate_infra_tco(gpu_type: str = "T4", gpu_count: int = 2, is_closed_network: bool = True) -> dict:
    """
    솔루션 구동에 필요한 클라우드/GPU 하드웨어 연간 운영 원가(TCO)를 산출하는 MCP 도구.
    """
    pricing_table = {
        "T4": 0.526,      # 비전 검사/경량 이상감지 추론
        "A10G": 1.212,    # 중형 비전 및 sLLM 서빙
        "A100": 4.100     # 대규모 모델 파인튜닝
    }
    
    hourly_rate = pricing_table.get(gpu_type, 0.526)
    annual_hours = 24 * 365
    exchange_rate = 1350  # 원/달러 기준
    
    annual_cost_usd = hourly_rate * gpu_count * annual_hours
    if is_closed_network:
        # 공정 폐쇄망 보안 에어갭/전용 인프라 프리미엄 20% 가산
        annual_cost_usd *= 1.2
        
    annual_cost_krw = int(annual_cost_usd * exchange_rate)
    
    return {
        "gpu_type": gpu_type,
        "gpu_count": gpu_count,
        "is_closed_network": is_closed_network,
        "annual_cost_usd": round(annual_cost_usd, 2),
        "annual_cost_krw_manwon": round(annual_cost_krw / 10000, 1),
        "guide_text": f"연간 예상 인프라 TCO 약 {round(annual_cost_krw / 10000, 1):,}만 원 (GPU {gpu_count}대, 공정 폐쇄망 보안 프리미엄 포함)"
    }
