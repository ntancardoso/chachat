# Sample Basic Chatbot with Haystack and SQLite

This project demonstrates a **Retrieval-Augmented Generation (RAG)** chatbot built using:
- **Haystack**: For document retrieval and question-answering.
- **SQLite**: For storing product information (e.g., prices, stock). This can be replaced with actual database server
- **Lightweight Language Models**: For generating human-like responses.

The chat bot can answer questions about products (e.g., prices, stock) and general information (e.g., return policy, shipping) by retrieving data from a SQLite database and documents.

---

## Features
- **Document Retrieval**: Retrieve relevant information from documents (e.g., `txt`, `pdf`, `doc`).
- **Database Querying**: Fetch product details (e.g., price, stock) from an SQL database.
- **Human-Like Responses**: Generate concise and natural responses using a lightweight language model (e.g., TinyLLaMA).
- **Lightweight**: Designed to run on low-resource hardware (e.g., CPUs or low-end GPUs).

---

## Prerequisites
- Python 3.8+
- Install the required libraries:
  ```bash
  pip install -r requirements.txt
  ```

## Setup
- Add or update sample data on products table on data\data.db
- Add or update documents on documents folder

## Run the Application
This is for local testing purpose only. Must run this with gunicorn on servers
```
python app.py
```

## Usage
###  Ask a Question
```
curl -X POST http://localhost:5000/ask -H "Content-Type: application/json" -d '{"question": "How much is an apple?"}'
```
### Response
```
{
    "answers": [
        "The price of Apple is $2.00, and we currently have 100 units in stock."
    ]
}
```

## Example Questions

### Product Information:

```
"How much is Product A?"

"What is the stock of Product B?"
```
### General Information:
```
"What is your return policy?"

"How long does standard shipping take?"
```