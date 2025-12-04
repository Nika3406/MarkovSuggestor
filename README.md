# MarkovSuggestor
**An intelligent, explainable code suggestion and analysis plugin powered by hybrid — combining Hidden Markov Models (HMM), local code scanning, and minimal NLP embeddings.**

---

## Overview
**CodeSuggester** enhances Sublime Text with two core capabilities:

1. **Smart Code Suggestions**  
   Predicts and autocompletes code functions based on:
   - Your current syntax and token patterns  
   - The libraries and functions available in your local environment  
   - Probabilistic modeling (HMM) and semantic similarity search  

2. **Code Explanation Panel**  
   Opens a secondary view translating your selected code into:
   - Human-readable pseudocode  
   - A “computer science” style summary of detected algorithms or logic structures  

Unlike LLM-based assistants, CodeSuggester avoids heavy neural dependency and cloud computation.  
It performs all inference **locally**, using explainable models and pre-scanned libraries.

---

## Architecture
CodeSuggester follows a modular hybrid-AI pipeline:
User Input → Syntax & HMM Analysis → Vector Similarity Search → Ranked Suggestions → Pseudocode & Algorithm Insight

| Module | Description |
|--------|--------------|
| **code_suggester.py** | Sublime Text plugin entry; connects frontend editor events to backend logic. |
| **code_explainer.py** | Uses the library info from the function database to create pseudocode to explain your code. |
| **embedder.py** | Generates compact semantic embeddings for local library functions using `sentence-transformers`. |
| **suggester.py** | Combines HMM state prediction with vector similarity ranking for final code suggestions. |
| **explain.py** | Produces pseudocode and algorithmic insights based on code structure. |
| **functions.json** | Local dataset of available functions and short descriptions, generated from library scanning. |
