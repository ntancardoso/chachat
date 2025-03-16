from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import EmbeddingRetriever
from flask import Flask, request, jsonify
import sqlite3
import os
import re
from transformers import pipeline

app = Flask(__name__)
generator_model="TinyLlama/TinyLlama-1.1B-Chat-v1.0"

document_store = InMemoryDocumentStore(embedding_dim=384)
retriever = EmbeddingRetriever(
    document_store=document_store,
    embedding_model="multi-qa-MiniLM-L6-cos-v1",
    model_format="sentence_transformers"
)

generator = pipeline("text-generation", model=generator_model)

def load_documents():
    from haystack.utils import convert_files_to_docs
    if not os.path.exists("data/documents"):
        os.makedirs("data/documents")
        return
    
    docs = convert_files_to_docs(dir_path="data/documents", split_paragraphs=True)
    if not docs:
        print("No documents found in 'data/documents'. Please add some (txt, pdf, doc) documents.")
        return
    
    document_store.write_documents(docs)
    document_store.update_embeddings(retriever)
    print(f"Loaded {len(docs)} documents into the document store.")

def get_product_names(query):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM products")
    product_names = [row[0] for row in cursor.fetchall()]
    conn.close()

    words_in_query = query.split()
    found_product_names = []
    for query_word in words_in_query:
        for product in product_names:
            if query_word.lower().startswith(product.lower()):
                found_product_names.append(product)
                if abs(len(product) - len(query_word)) <= 2:
                    break

    return found_product_names


def query_database(query):
    product_names = get_product_names(query)
    if not product_names:
        print("Error: Could not extract product name from query.")
        return []

    product_names_string = ", ".join(product_names)
    print(f"Extracted product name: '{product_names_string}'")

    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    if not cursor.fetchone():
        print("Error: 'products' table not found in the database.")
        return []
    cursor.execute(f"SELECT name, price, stock FROM products WHERE name IN ({', '.join(['?'] * len(product_names))})", product_names)

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"No results found in the database for product: {product_name}")
    else:
        print(f"Found results: {results}")
    return results


def fetch_relevant_paragraphs(query):
    candidate_docs = retriever.retrieve(query, top_k=3)
    paragraphs = [doc.content for doc in candidate_docs]
    return paragraphs


def generate_response(question, db_results=None, doc_results=None):
    if db_results:
        responses = []
        for name, price, stock in db_results:
            response = f"The price of {name} is ${price:.2f}, and we currently have {stock} units in stock."
            responses.append(response)
        return " ".join(responses)
    
    if doc_results:
        context = " ".join(doc_results)
        prompt = f"Answer the following question based on the context below. Provide only the answer and nothing else.\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer:"
        response = generator(prompt, max_new_tokens=100, num_return_sequences=1)[0]["generated_text"]
        answer = response.split("Answer:")[1].strip()
        answer = re.split(r'(?<=[.!?])\s+', answer)[0]
        return answer
    
    return "I'm sorry, I couldn't find any information about that. Please try asking another question."

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question')

    db_results = None
    # adjust word_list to your needs. this is the criteria used to check info from the database like price and stock
    word_list = ["cost", "much", "price", "charge", "fee", "rate", "value", "tariff", "expenditure", "spend", "msrp", "quotation", "retail", "wholesale", "stock", "available", "inventory"]
    if any(word.lower() in question.lower().split() for word in word_list):
        db_results = query_database(question)

    doc_results = None
    if not db_results or "return policy" in question.lower() or "shipping" in question.lower():
        doc_results = fetch_relevant_paragraphs(question)
    
    response = generate_response(question, db_results, doc_results)
    return jsonify({"answers": [response]})

if __name__ == "__main__":
    load_documents()
    app.run(host="0.0.0.0", port=5000)