# -*- coding: utf-8 -*-
"""Open-source RAG using LangChain, LLAMA 3 and Chroma (P).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Nwh1tLmlmkNIle4l3IFo69UVZSs-gSxy

You can read the accompanying article here:

[Jupyter Notebook - Build Your Own Open-source RAG Using LangChain, LLAMA 3 and Chroma](https://codecompass00.substack.com/p/build-open-source-rag-langchain-llm-llama-chroma)

Access case studies and technical deep dives: [The Code Compass](https://codecompass00.substack.com/)



---



Remember to switch the Runtime to GPU.

Let's install all the pre-requisites first.
"""

# Commented out IPython magic to ensure Python compatibility.
!pip install transformers langchain langchain-chroma langchainhub
!pip install langchain-community unstructured[pdf] langchain-text-splitters
!pip install sentence-transformers
!pip install colab-xterm #https://pypi.org/project/colab-xterm/
# %load_ext colabxterm

"""Let's load the script file, which is a PDF."""

from langchain.document_loaders import UnstructuredURLLoader

documents = [
    "https://thetelevisionpilot.com/wp-content/uploads/2017/09/Game-of-Thrones-pilot-script.pdf"
]

loader = UnstructuredURLLoader(documents)

loader.load()

raw_texts = loader.load()

"""Let's split the loaded file into 1000 character chunks with 100 characters overlap."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)

texts = text_splitter.create_documents([t.page_content for t in raw_texts])

"""Let's see how many chunks we got and what one of these looks like."""

len(texts)

texts[0]

"""We need to use xterm to start a terminal session and install ollama.
This will allow us to use LLAMA 3 locally and other models that you may wish.
We will use LLAMA 3 both for embeddings generation as well as for LLM generation.

Let's type in the following into the terminal, to install and start ollama:
```
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```
"""

# Commented out IPython magic to ensure Python compatibility.
# %xterm

# curl -fsSL https://ollama.com/install.sh | sh
# ollama serve

"""Let's pull LLAMA 3 weights so we can use it for inference locally."""

!ollama pull llama3

"""Let's try if we can embed using the LLAMA 3 model."""

!curl http://localhost:11434/api/embeddings -d '{"model": "llama3","prompt": "Earth is one of the planets in our solar system"}'

"""Let's create objects for the LLM and embedder.
Here, LLAMA 3 is used but you can switch to your favorite embedding model or LLM.

You can read the accompanying article here:

[Jupyter Notebook - Build Your Own Open-source RAG Using LangChain, LLAMA 3 and Chroma](https://codecompass00.substack.com/p/build-open-source-rag-langchain-llm-llama-chroma)

Access case studies and technical deep dives: [The Code Compass](https://codecompass00.substack.com/)
"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import OllamaEmbeddings

from langchain_community.llms import Ollama
llm = Ollama(
    base_url='http://127.0.0.1:11434',
    model="llama3"
)
embedder = OllamaEmbeddings(
    base_url="http://127.0.0.1:11434",
    model="llama3"
)

# If you prefer, to use embeddings from HuggingFace, simply use the following:
# embedder = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")

"""Let's now embed the documents using Chroma which is a vector database.
It takes the chunks of text and the embedding model to generate the embeddings.
"""

from langchain_chroma import Chroma

vector_store = Chroma.from_documents(texts, embedder)

"""We can now use the vector store to query similar items to what we are looking for. Here, we query `k` results."""

query = "What is Bran's age?"
relevant_docs = vector_store.similarity_search(query, k=10)

print(f"Retrieved most relevant documents with lengths: {[len(doc.page_content) for doc in relevant_docs]}")

"""Let's put all the pieces together and create the pipeline or chain using LangChain.
First, we need the vector store to act as a retriever function.
When it gets a query, it should return the most similar chunks.
"""

retriever = vector_store.as_retriever(k=10)

"""Next, we need a prompt. We use the RAG template from LangChain.
Let's see that the prompt template looks like.
"""

from langchain import hub

prompt = hub.pull("rlm/rag-prompt")

print(f"Prompt takes the following as inputs: {prompt.messages[0].input_variables}")
print("Prompt template: \n", prompt.messages[0].prompt.template)

"""Putting it all together, we pass on the context from the retriever with the query to the LLM in the form of the prompt template."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

for chunk in rag_chain.stream("What is Bran's age?"):
    print(chunk, end="", flush=True)

"""Let's create a custom prompt.
This gives it more context on what is the task and what kind of data it will be looking at.
"""

from langchain_core.prompts import PromptTemplate

template = """Use the following pieces of context to answer the question at the end.
The context are pieces of a script from a TV show. The script contains what each of the character says in the show.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use three sentences maximum and keep the answer as concise as possible.
Explain your reasoning in the last sentence.

{context}

Question: {input}

Helpful Answer:"""
custom_rag_prompt = PromptTemplate.from_template(template)

rag_chain = (
    {"context": retriever, "input": RunnablePassthrough()}
    | custom_rag_prompt
    | llm
    | StrOutputParser()
)

for chunk in rag_chain.stream("What is Bran's age?"):
    print(chunk, end="", flush=True)

"""Well, that is much better now! With the custom prompt we are able to get much better out of the same LLM, vector store and query.

We can also see what sources or "context" the retriever presented to the LLM when generating the response:
"""

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

question_answer_chain = create_stuff_documents_chain(llm, custom_rag_prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

response = rag_chain.invoke({"input": "What is Bran's age?"})
print(response["answer"])

for doc in response["context"]:
  print("---- START OF CONTEXT ----")
  print(doc.page_content)
  print("---- END OF CONTEXT ----")



"""You can read the accompanying article here:

[Jupyter Notebook - Build Your Own Open-source RAG Using LangChain, LLAMA 3 and Chroma](https://codecompass00.substack.com/p/build-open-source-rag-langchain-llm-llama-chroma)

Access case studies and technical deep dives: [The Code Compass](https://codecompass00.substack.com/)

"""

