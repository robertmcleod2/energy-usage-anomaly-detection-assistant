from dotenv import load_dotenv
from langchain.globals import set_debug
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
import json
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnablePassthrough

set_debug(True)

load_dotenv()


def setup_chain():

    model = ChatOpenAI(model="gpt-4o-mini")


    # local document retrieval
    with open('src/example_customer_documents.json') as f:
        docs = json.load(f)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    vectorstore = InMemoryVectorStore.from_documents(
        documents=splits, embedding=OpenAIEmbeddings()
    )
    retriever = vectorstore.as_retriever()


    chat_history = ChatMessageHistory()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an an energy usage anomaly detection assistant.\n
                You are helping a user to detect anomalies in their energy usage.\n
                The user will describe their energy usage and you will help them to detect anomalies.\n
                You will also help the user to identify the causes of the anomalies \n
                and suggest ways to fix them.\n\n

                You can use the following documents to help you with your responses:\n\n
                {context}
                """,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

    

    chain = prompt | model

    chain_with_message_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: chat_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    return chain_with_message_history