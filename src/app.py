import streamlit as st
from basic_chatbot import setup_chain
from dotenv import load_dotenv
from utils import check_password

load_dotenv()

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

st.title("Energy Usage Anomaly Detection Assistant")

if "chain" not in st.session_state:
    st.session_state.chain = setup_chain()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Please describe your energy usage anomaly."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = st.session_state.chain.stream({"input": prompt}, {"configurable": {"session_id": "unused"}})
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
