import requests
import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain.tools import tool
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch


load_dotenv()

# 모델 만들기
model = init_chat_model("gpt-5.4-mini")

# # 클래스 만들기
# class ExchangeRateAns(BaseModel):
#     """실시간 환율을 분석한 답변의 구조"""
#     base : str = Field(description = "기준 통화를 나타내는 필드")
#     quote : str = Field(description = "대상 통화를 나타내는 필드")
#     base : str = Field(description = "기준 통화를 나타내는 필드")
#     base : str = Field(description = "기준 통화를 나타내는 필드")
#     base : str = Field(description = "기준 통화를 나타내는 필드")

# tool 만들기
@tool
def get_exchange_rate(base: str = "USD", quote: str = "KRW", amount: float = 1.0) -> str:
    """
    특정 통화의 환율을 조회합니다.
    예: base='USD', quote='KRW'이면 1달러가 몇 원인지 조회합니다.
    amount를 넣으면 해당 금액을 환산합니다.
    """

    base = base.upper()
    quote = quote.upper()

    url = f"https://api.frankfurter.dev/v2/rate/{base}/{quote}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    rate = data["rate"]
    date = data.get("date", "알 수 없음")

    converted = amount * rate

    return (
        f"기준 통화: {base}\n"
        f"대상 통화: {quote}\n"
        f"{int(amount)} {quote} 환율: {converted:,.2f} {quote}\n"
        f"환산 금액: {amount:,.2f} {base} = {converted:,.2f} {quote}\n"
        f"환율 기준일: {date}\n"
    )
    

# agent 생성
my_agent = create_agent(
    model,
    tools = [get_exchange_rate],
    system_prompt = """
    너는 환율 정보를 알려주는 친절한 금융 정보 assistant다.

    사용자가 원-달러 환율, 달러 환율, USD/KRW 환율을 물어보면
    반드시 get_exchange_rate Tool을 사용해 최신 환율을 조회해라.

    한국에서 말하는 '원-달러 환율'은 보통
    '1달러가 몇 원인지', 즉 USD -> KRW 환율을 의미한다.

    답변은 마크다운 언어를 기반으로 작성된 아래의 예시 형식을 준수하라.
    100달러(USD)는 **133,717원(KRW)**입니다.
    
    - **기준 통화:** USD
    - **대상 통화:** KRW
    - **1 USD 환율:** 133,717 KRW
    - **환산 금액:** 100 USD = 133,717 KRW
    - **환율 기준일:** 2026-10-13

    투자 조언처럼 말하지 말고, 조회된 환율 정보만 간단히 설명해라.
    """
)

# 웹앱 구현
st.title("실시간 환율 챗봇")
st.caption("질문할 때마다 FrankFurter의 최신 일별 기준 환율을 조회합니다. 실시간 금융시장 체결가는 아닙니다.")

if "messages" not in st.session_state :
    st.session_state.messages = []

prompt = st.chat_input("환율이나 환산할 금액을 자연어로 질문해보세요.")

if prompt:
    # response = model.invoke(prompt)
    response = my_agent.invoke(
        {"messages" : [{"role" : "user", "content" : prompt}]}
    )
    st.session_state.messages.append({"role" : "user", "content" : prompt})
    st.session_state.messages.append({"role" : "ai", "content" : response['messages'][-1].content})

for message in st.session_state.messages : 
    with st.chat_message(message["role"]) : 
        st.write(message["content"])