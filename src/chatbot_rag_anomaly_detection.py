import json

import streamlit as st
from dotenv import load_dotenv
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.globals import set_debug
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveJsonSplitter
from utils import (
    detect_daily_anomalies,
    detect_prolonged_anomalies,
    generate_anomaly_text,
    load_smart_meter_data,
    load_weather_data,
    plot_anomalies,
    analyse_weather_data,
    plot_weather,
)

set_debug(True)

load_dotenv()

class ChatbotRAG:

    def __init__(self):

        ### Load smart meter data and detect anomalies ###
        df = load_smart_meter_data()
        weather_df = load_weather_data()
        anomalies = detect_daily_anomalies(df)
        prolonged_anomalies = detect_prolonged_anomalies(df)
        average_temperature_str, anomaly_temperatures_str, prolonged_anomaly_temperatures_str = analyse_weather_data(weather_df, anomalies, prolonged_anomalies)
        fig = plot_anomalies(df, anomalies, prolonged_anomalies)
        st.session_state.messages.append({"role": "assistant", "content": fig})
        fig_weather = plot_weather(weather_df)
        st.session_state.messages.append({"role": "assistant", "content": fig_weather})
        self.anomaly_text = generate_anomaly_text(anomalies, prolonged_anomalies, average_temperature_str, anomaly_temperatures_str, prolonged_anomaly_temperatures_str)

        ### initialize chain ###
        self.initialize_chain()

        ### invoke chain for initial summary ###
        initial_prompt = """provide a summary of the anomalies detected in the my energy usage \
        from the smart meter data and any other relevant context."""
        response = self.stream(initial_prompt)
        st.plotly_chart(fig)
        st.plotly_chart(fig_weather)
        st.session_state.messages.append({"role": "assistant", "content": response})

    def initialize_chain(self):

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        ### Construct retriever ###
        with open("src/example_customer_documents.json") as f:
            json_data = json.load(f)

        splitter = RecursiveJsonSplitter(max_chunk_size=300)
        docs = splitter.create_documents(texts=[json_data])

        vectorstore = InMemoryVectorStore.from_documents(documents=docs, embedding=OpenAIEmbeddings())
        retriever = vectorstore.as_retriever()

        ### Contextualize question ###
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. \
        Include information relevant to energy anomaly detection in the question, if needed. \
        Do NOT answer the question, just reformulate it if needed and otherwise return it as is."""
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

        ### Answer question ###
        qa_system_prompt = (
            f"""You are an an energy usage anomaly detection assistant. \
        You are helping a user to detect anomalies in their energy usage. \
        An anomaly detection has already been performed. \
        {self.anomaly_text} \
        If there are anomalies, you can compare when they have occured against the additional context \
        provided to determine if there are any patterns. You have been provided data up to 2024-08-31, and \
        so if any anomalies continue up to the end of the data you have been provided, \
        they may still be ongoing. This must be taken into account when providing advice.
        """
            + """ The user will describe their energy usage and you will help them to resolve \
        or determine additional issues. \
        You will also help the user to identify the causes of the anomalies \
        and suggest ways to fix them. \
        Follow up on previous parts of customer service chatbot and agent conversations that are not yet resolved. \
        
        Use the following pieces of retrieved context to answer the question if needed. \

        {context}"""
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        ### Statefully manage chat history ###
        chat_history = ChatMessageHistory()

        self.chain = RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

    def stream(self, input):
        stream = self.chain.stream({"input": input}, {"configurable": {"session_id": "unused"}})

        def stream_func():
            for chunk in stream:
                for key in chunk:
                    if key == "answer":
                        yield chunk[key]

        response = st.write_stream(stream_func)

        return response
