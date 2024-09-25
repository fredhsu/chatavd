import os
import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# from langchain_chroma import Chroma
from langchain_qdrant import QdrantVectorStore
from langchain import hub
from langchain_core.output_parsers import (
    StrOutputParser,
    JsonOutputParser,
    PydanticOutputParser,
)
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from qdrant_client import QdrantClient
from pydantic import BaseModel, Field


class ChatAVDResponse(BaseModel):
    answer: str = Field(description="The answer to the query")
    # question: str = Field(description="The query")
    # context: dict = Field(description="The context of the answer")


def format_docs(docs):
    json_docs = ",\n".join(doc.page_content for doc in docs)
    json_list = f"[{json_docs}]"
    return json_list


def get_response(query: str):
    load_dotenv()
    model = "gpt-4o-mini"
    llm = ChatOpenAI(model=model, temperature=0)
    # llm = llm.bind(request_format={"type": "json_object"})
    embeddings = OpenAIEmbeddings()

    url = "d66c427c-49d7-4a20-a09c-eff49a047f43.europe-west3-0.gcp.cloud.qdrant.io"
    api_key = os.environ["QDRANT_API_KEY"]

    collection_name = "dc1"
    client = QdrantClient(url=url, api_key=api_key)
    vectorstore = QdrantVectorStore(
        client=client, collection_name=collection_name, embedding=embeddings
    )

    prompt = hub.pull("rlm/rag-prompt")
    # chat prompt template human
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "human",
                "You are an assistant for question-answering tasks and a computer networking expert of CCIE level. \
                Use the following pieces of retrieved context to answer the question. If you don't know the answer, \
                just say that you don't know. Keep the answer concise. \
    Question: {question} \
    Context: {context} \
    Answer:",
            )
        ]
    )

    # answer = prompt | llm | JsonOutputParser()
    answer = prompt | llm | StrOutputParser()
    # answer = prompt | llm | PydanticOutputParser()

    chain = (
        RunnableParallel(
            {
                "context": vectorstore.as_retriever() | format_docs,
                "question": RunnablePassthrough(),
            }
        )
        # .assign(context=format)
        .assign(answer=answer)
        .pick(["answer"])
        # .pick(["answer", "context"])
    )
    return chain.stream(query)

    # previous for non streaming
    # response = chain.invoke(query)
    # context_json = json.loads(response["context"])
    # for config in context_json:
    #     print(config["hostname"])
    #
    # return response["answer"]
