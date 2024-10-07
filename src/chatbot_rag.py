import json

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

set_debug(True)

load_dotenv()


def setup_chain():
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
    qa_system_prompt = """You are an an energy usage anomaly detection assistant. \
    You are helping a user to detect anomalies in their energy usage. \
    The user will describe their energy usage and you will help them to detect anomalies. \
    You will also help the user to identify the causes of the anomalies \
    and suggest ways to fix them. \

    Use the following pieces of retrieved context to answer the question if needed. \
    Follow up on previous parts of customer service chatbot and agent conversations that are not yet resolved. \

    {context}"""

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

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        lambda session_id: chat_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return conversational_rag_chain
