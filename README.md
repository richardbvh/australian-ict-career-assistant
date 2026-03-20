# Australian ICT Career Assistant

This project is an **AI-powered career assistant** designed to answer questions about **ICT roles in Australia** using **retrieval-augmented generation (RAG)** and **tool calling**.

The system combines document-grounded question answering with salary lookup functionality to provide more useful and context-aware responses. It uses the **OSCA ICT occupation document** as its knowledge source and integrates a salary lookup tool to answer compensation-related queries. A **Gradio interface** is used to deliver an interactive user experience.

---

## Project Overview

Choosing an ICT career path can be difficult for students, graduates, and career changers, especially when information is spread across documents, websites, and job platforms.

This project was developed to support that problem by building a career assistant that can:

- answer questions about ICT occupations in Australia
- retrieve role information from an official occupation document
- provide salary-related information using an external tool
- decide whether a query should be answered using document retrieval, tool calling, or both
- return grounded responses with citations where appropriate

---

## Project Objective

The objective of this project is to build a question-answering assistant that helps users explore Australian ICT roles through a combination of:

- **RAG** for document-based answers
- **tool calling** for external salary information
- **routing logic** to determine the most suitable response strategy

The project aims to answer questions such as:

- What does an ICT Business Analyst do?
- What tasks are involved in a Systems Analyst role?
- What is the skill level of a Database Administrator role in Australia?
- What is the median salary for a specific ICT role?
- Which occupation information should come from the document, and which should come from a salary tool?

---

## Key Features

- **Document-grounded question answering** using RAG
- **Salary lookup tool integration**
- **Routing logic** to choose between:
  - document retrieval only
  - tool only
  - document retrieval + tool
- **Citations** for retrieved document answers
- **Interactive Gradio interface**
- **Evaluation and ground truth testing**
- **Fallback handling** for ambiguous or unsupported queries

---

## System Design

The application is built around three main components:

### 1. Retrieval-Augmented Generation (RAG)
The system retrieves relevant passages from the **OSCA ICT document** and uses them to answer questions about:

- occupation descriptions
- main tasks
- skill levels
- alternative titles
- role-specific information

### 2. Tool Calling
A salary lookup tool is used to retrieve salary information for ICT occupations. This supports questions related to:

- salary expectations
- median pay
- role-specific compensation queries

### 3. Query Routing
The system includes routing logic to determine how each user query should be handled:

- **RAG only** for document-based questions
- **Tool only** for salary-related questions
- **Both** for questions requiring role information and salary information together

---

## Knowledge Source

The main knowledge source used for retrieval is:

- **OSCA_27_ICT.pdf**

This document provides structured information about ICT occupations in Australia, including:

- occupation names
- skill levels
- alternative titles
- main tasks and responsibilities

---

## Tools and Technologies

- Python
- Gradio
- ChromaDB
- Sentence Transformers
- PyPDF
- YAML configuration
- External salary lookup API
- Retrieval-Augmented Generation (RAG)

---

## Core Files

### Application Files
- `main.py` – main application entry point and routing logic
- `rag_pipeline.py` – document ingestion, chunking, embedding, and retrieval pipeline
- `tools.py` – salary lookup tool integration
- `prompts.py` – prompt templates and system prompting logic
- `config.yml` – project configuration settings
- `requirements.txt` – Python dependencies

### Supporting Files
- `GroundTruth.md` – evaluation questions and expected behaviour
- `Architecture.pdf` – system architecture overview
- `OSCA_27_ICT.pdf` – source knowledge document for retrieval

---

## Repository Structure

```text
australian-ict-career-assistant/
├── README.md
├── main.py
├── rag_pipeline.py
├── tools.py
├── prompts.py
├── config.yml
├── requirements.txt
├── GroundTruth.md
├── docs/
│   └── Architecture.pdf
└── data/
    └── OSCA_27_ICT.pdf
