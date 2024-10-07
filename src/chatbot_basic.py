import streamlit as st
from dotenv import load_dotenv
from langchain.globals import set_debug
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

set_debug(True)

load_dotenv()


class ChatbotBasic:

    def __init__(self):
        model = ChatOpenAI(model="gpt-4o-mini")

        chat_history = ChatMessageHistory()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an an energy usage anomaly detection assistant.\n
                    You are helping a user to detect anomalies in their energy usage.\n
                    The user will describe their energy usage and you will help them to detect anomalies.\n
                    You will also help the user to identify the causes of the anomalies \n
                    and suggest ways to fix them.\n
                    """,
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        chain = prompt | model

        self.chain = RunnableWithMessageHistory(
            chain,
            lambda session_id: chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def stream(self, input):
        stream = self.chain.stream({"input": input}, {"configurable": {"session_id": "unused"}})
        response = st.write_stream(stream)
        return response
