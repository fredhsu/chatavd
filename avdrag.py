import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# from langchain_chroma import Chroma
from langchain_qdrant import QdrantVectorStore
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from qdrant_client import QdrantClient


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def get_response(query: str):
    load_dotenv()
    model = "gpt-4o-mini"
    llm = ChatOpenAI(model=model, temperature=0)
    embeddings = OpenAIEmbeddings()

    url = "d66c427c-49d7-4a20-a09c-eff49a047f43.europe-west3-0.gcp.cloud.qdrant.io"
    api_key = os.environ["QDRANT_API_KEY"]

    collection_name = "dc1"
    client = QdrantClient(url=url, api_key=api_key)
    vectorstore = QdrantVectorStore(
        client=client, collection_name=collection_name, embedding=embeddings
    )

    prompt = hub.pull("rlm/rag-prompt")

    answer = prompt | llm | StrOutputParser()

    chain = (
        RunnableParallel(
            {
                "context": vectorstore.as_retriever() | format_docs,
                "question": RunnablePassthrough(),
            }
        )
        .assign(context=format)
        .assign(answer=answer)
        .pick(["answer", "context"])
    )
    response = chain.invoke(query)
    print(response)

    return response
