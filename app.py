import streamlit as st
from dotenv import load_dotenv

from basic_chatbot import chain_with_message_history

load_dotenv()

st.title("Energy Usage Anomaly Detection Assistant")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        stream = chain_with_message_history.stream(
            {"input": prompt}, {"configurable": {"session_id": "unused"}}
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
