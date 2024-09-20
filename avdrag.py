from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def get_response(query: str):
    model = "gpt-4o-mini"
    llm = ChatOpenAI(model=model, temperature=0)
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(persist_directory="db", embedding_function=embeddings)

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
