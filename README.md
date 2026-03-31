Parfait, j'ai toutes les infos ! Voici le README mis à jour avec les vraies dépendances de ton notebook :

---

# Knowledge Graph Project

A full pipeline for Knowledge Graph Construction, Alignment, Reasoning, KGE and RAG, built on Wikipedia data for 8 major French cities.

---

## Project Structure

```
project-root/
├─ src/
│  ├─ crawl/        # Web crawler and cleaning
│  ├─ ie/           # Named Entity Recognition (NER)
│  ├─ kg/           # RDF graph construction and ontology
│  ├─ reason/       # SWRL reasoning with OWLReady2
│  ├─ kge/          # Knowledge Graph Embeddings (TransE, DistMult)
│  └─ rag/          # RAG pipeline (NL→SPARQL, self-repair, CLI)
├─ data/
│  ├─ samples/
│  └─ README.md
├─ kg_artifacts/
│  ├─ ontology.ttl
│  ├─ expanded.nt
│  └─ alignment.ttl
├─ reports/
│  └─ final_report.pdf
├─ notebooks/
├─ README.md
├─ requirements.txt
├─ .gitignore
└─ LICENSE
```

---

## Hardware Requirements

- RAM: 8GB minimum (16GB recommended)
- Disk: at least 3GB free (model + graph files)
- OS: Windows 10/11, macOS, or Linux
- Python: 3.9 or higher
- Ollama: 0.19.0 or higher

---

## Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

**2. Create and activate the environment**
```bash
conda create -n lab_env python=3.11
conda activate lab_env
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Download the spaCy model**
```bash
python -m spacy download en_core_web_sm
```

---

## requirements.txt

```
spacy
trafilatura
pandas
httpx
rdflib
unidecode
SPARQLWrapper
requests
owlready2
pykeen
torch
jupyter
```

---

## How to Run Ollama

**1. Download and install Ollama** from https://ollama.com

**2. Pull the model**
```bash
ollama pull gemma:2b
```

**3. Start the server** (keep this running in a separate terminal)
```bash
ollama serve
```

Visit http://localhost:11434 to confirm it is running. You should see "Ollama is running".

On Windows, the Ollama executable is located at:
```
C:\Users\<your-username>\AppData\Local\Programs\Ollama\ollama.exe
```

---

## How to Run Each Module

**Crawler**
```bash
cd src/crawl
python crawler.py
```

**NER / Information Extraction**
```bash
cd src/ie
python ner_pipeline.py
```

**Knowledge Graph Construction**
```bash
cd src/kg
python build_kg.py
```

**Alignment with Wikidata (via SPARQLWrapper)**
```bash
cd src/kg
python alignment.py
```

**Reasoning (SWRL)**
```bash
cd src/reason
python reasoning.py
```

**KGE Training (TransE, DistMult)**
```bash
cd src/kge
python train_kge.py
```

---

## How to Run the RAG Demo

Make sure Ollama is running, then:

```bash
cd src/rag
python lab_rag_sparql_gen.py
```

Or open the notebook:
```bash
jupyter notebook notebooks/rag_demo.ipynb
```

The CLI chatbot will start:
```
🤖 RAG Chatbot (type 'quit' to exit)

You: Tell me about Alenka Doulain
📊 KB Context: Entity: Alenka Doulain | type: GPE | locatedIn: France
🤖 Bot: Alenka Doulain is a geopolitical entity located in France.
```

---

## Data

The knowledge graph was built from Wikipedia pages for 8 French cities: Toulouse, Paris, Lyon, Marseille, Nice, Nantes, Lille, and Montpellier. The full graph contains 32,401 RDF triples.

A sample is available in `data/samples/`. If the full graph file is too large, download it here: [add your link here]