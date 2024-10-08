import streamlit as st
from chatbot_rag_anomaly_detection import ChatbotRAG as Chatbot
from dotenv import load_dotenv
from utils import check_password

load_dotenv()

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

st.title("Energy Usage Anomaly Detection Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], str):
            st.markdown(message["content"])
        else:
            st.plotly_chart(message["content"])

if "chatbot" not in st.session_state:
    st.session_state.chatbot = Chatbot()

if prompt := st.chat_input("Please describe your energy usage anomaly."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = st.session_state.chatbot.stream(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
