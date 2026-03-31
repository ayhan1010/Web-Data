#!/usr/bin/env python
# coding: utf-8

# # TD1

# # Phase1

# In[1]:


import spacy
import trafilatura
import pandas as pd
import httpx

print("Tout fonctionne !")


# # URL

# In[2]:


# Librairies nécessaires

import json

# URLs des 8 plus grandes villes françaises
urls = [
    "https://fr.wikipedia.org/wiki/Toulouse",
    "https://fr.wikipedia.org/wiki/Paris",
    "https://fr.wikipedia.org/wiki/Lyon",
    "https://fr.wikipedia.org/wiki/Marseille",
    "https://fr.wikipedia.org/wiki/Nice",
    "https://fr.wikipedia.org/wiki/Nantes",
    "https://fr.wikipedia.org/wiki/Lille",
    "https://fr.wikipedia.org/wiki/Montpellier"
]

print("Cellule 1 OK : Imports et URLs prêts")


# In[3]:


# Vérifie si le texte contient plus de 500 mots
def is_useful(text, min_words=500):
    if text is None:
        return False
    return len(text.split()) >= min_words

print("Cellule 2 OK : Fonction is_useful prête")


# In[4]:


# Récupère le texte principal d'une page avec Trafilatura
def extract_text(url):
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        text = trafilatura.extract(downloaded)
        return text
    return None

print("Cellule 3 OK : Fonction extract_text prête")


# # Crawler + cleaning + NER

# In[298]:


# Sauvegarde la liste de dictionnaires dans un fichier JSONL
def save_jsonl(data, filename="crawler_output.jsonl"):
    with open(filename, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

print("Cellule 4 OK : Fonction save_jsonl prête")


# In[6]:


# Liste pour stocker les résultats
data = []

for url in urls:
    text = extract_text(url)
    if is_useful(text):
        data.append({"url": url, "text": text})
        print(f"Page utile sauvegardée : {url}")
    else:
        print(f"Page ignorée (moins de 500 mots) : {url}")

# Sauvegarde dans JSONL
save_jsonl(data)
print(f"Phase 1 terminée : {len(data)} pages sauvegardées dans crawler_output.jsonl")


# # Phase2

# In[7]:


import spacy
import pandas as pd
import json

# Charge le modèle léger CPU-only
nlp = spacy.load("en_core_web_sm")

print("Phase 2 OK : spaCy prêt")


# In[8]:


# Lire le fichier crawler_output.jsonl
data = []
with open("crawler_output.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

print(f"{len(data)} pages chargées pour extraction NER")


# In[9]:


# On ne garde que PERSON, ORG, GPE, DATE
def extract_entities(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "ORG", "GPE", "DATE"]:
            entities.append({"text": ent.text, "label": ent.label_})
    return entities

print("Fonction extract_entities prête")


# In[10]:


results = []

for page in data:
    url = page["url"]
    text = page["text"]
    entities = extract_entities(text)
    for ent in entities:
        results.append({
            "entity": ent["text"],
            "type": ent["label"],
            "source_url": url
        })

print(f"{len(results)} entités extraites")


# In[11]:


df = pd.DataFrame(results)
df.to_csv("extracted_knowledge.csv", index=False, encoding="utf-8")
print("extracted_knowledge.csv créé ✅")


# In[12]:


relations = []

for page in data:
    text = page["text"]
    doc = nlp(text)
    for sent in doc.sents:
        sent_ents = [ent for ent in sent.ents if ent.label_ in ["PERSON","ORG","GPE","DATE"]]
        if len(sent_ents) >= 2:
            # Exemple simple : relier la première entité à la deuxième
            relations.append({
                "source": sent_ents[0].text,
                "relation": "connected_to",  # placeholder, on peut essayer d'utiliser le verbe
                "target": sent_ents[1].text,
                "sentence": sent.text
            })

print(f"{len(relations)} relations candidates trouvées")


# In[13]:


import os
os.listdir()


# # TD4

# # Phase1

# In[15]:


get_ipython().system('pip install rdflib')


# In[16]:


import pandas as pd
import json
from rdflib import Graph, URIRef, Literal, Namespace, RDF


# In[17]:


# Charger le CSV des entités
entities_df = pd.read_csv("extracted_knowledge.csv")
entities_df.head()

# Charger le JSONL du texte (optionnel si tu veux exploiter les textes pour relations)
jsonl_file = "crawler_output.jsonl"
pages = []
with open(jsonl_file, "r", encoding="utf-8") as f:
    for line in f:
        pages.append(json.loads(line))

# Vérifions le contenu du JSONL
pages[0]  # affiche la première page pour voir la structure


# In[25]:


get_ipython().system('pip install unidecode')


# In[26]:


import re
import unidecode


# In[27]:


def clean_entity_for_uri(entity):
    # remplacer les espaces par "_"
    uri = entity.replace(" ", "_")
    # supprimer tous les caractères non alphanumériques sauf "_"
    uri = re.sub(r'[^a-zA-Z0-9_]', '', uri)
    # transformer les accents en lettres simples
    uri = unidecode.unidecode(uri)
    return uri


# In[28]:


# Créer le graphe RDF
g = Graph()
EX = Namespace("http://example.org/")
g.bind("ex", EX)

# Ajouter les entités
for index, row in entities_df.iterrows():
    clean_name = clean_entity_for_uri(row['entity'])
    entity_uri = EX[clean_name]

    # Ajouter le type si PERSON, ORG ou GPE
    if row['type'] in ['PERSON', 'ORG', 'GPE']:
        g.add((entity_uri, RDF.type, EX[row['type']]))

    # Exemple de relation simple : toutes les GPE sont en France
    if row['type'] == "GPE":
        g.add((entity_uri, EX.locatedIn, EX.France))


# In[29]:


# Nombre total de triplets
print(f"Nombre de triplets dans le graphe : {len(g)}\n")

# Afficher les 20 premiers triplets pour vérifier
for i, triple in enumerate(g):
    if i >= 20:
        break
    print(triple)


# # Ontology

# In[30]:


# Sauvegarder le graphe RDF au format Turtle
g.serialize("initial_KB.ttl", format="turtle")
print("Graphe RDF sauvegardé sous 'initial_KB.ttl'")


# # Phase2

# In[34]:


from rdflib import Graph, Namespace, RDF, OWL, URIRef

# Charger le graphe RDF créé à Step 1
g = Graph()
g.parse("initial_KB.ttl", format="turtle")

EX = Namespace("http://example.org/")
g.bind("ex", EX)


# In[35]:


# Lister toutes les entités uniques
entities = set(g.subjects(RDF.type, None))
print(f"Nombre d'entités privées : {len(entities)}")
list(entities)[:10]  # Affiche les 10 premières pour vérifier


# In[39]:


get_ipython().system('pip install SPARQLWrapper')


# In[40]:


from SPARQLWrapper import SPARQLWrapper, JSON

# Endpoint Wikidata
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setReturnFormat(JSON)

print("ok")


# In[41]:


def wikidata_search(entity_label):
    """
    Cherche une entité dans Wikidata par son label en français.
    Retourne l'URI si trouvée, sinon None.
    """
    query = f"""
    SELECT ?item ?itemLabel WHERE {{
      ?item rdfs:label "{entity_label}"@fr .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr". }}
    }}
    LIMIT 1
    """
    sparql.setQuery(query)
    results = sparql.query().convert()
    bindings = results["results"]["bindings"]
    if bindings:
        # Retourne URI + confiance fictive (ici 0.99 si trouvé)
        return bindings[0]["item"]["value"], 0.99
    else:
        return None, 0.0


print("ok")


# In[48]:


print(len(entities))
print(len(triple))


# In[46]:


import pandas as pd
from rdflib import URIRef, RDF, OWL

# Convertir le set en liste et limiter aux 200 premières entités
entities_list = list(entities)
entities_subset = entities_list[:200]

mapping = []

for entity in entities_subset:
    label = entity.split('/')[-1]  # Nom simple de l'URI, ex: 'MarieCurie'

    try:
        wd_uri, confidence = wikidata_search(label)
    except Exception as e:
        print(f"Erreur pour {label}: {e}")
        wd_uri, confidence = None, 0.0  # En cas d'erreur HTTP ou timeout

    if wd_uri:
        # Ajouter le lien owl:sameAs dans le graphe
        g.add((entity, OWL.sameAs, URIRef(wd_uri)))
    else:
        # Nouvelle entité → ajouter une définition RDF minimale
        g.add((entity, RDF.type, EX["NewEntity"]))

    # Ajouter la ligne dans la table de mapping
    mapping.append([entity, wd_uri if wd_uri else "N/A", confidence])

# Convertir en DataFrame et sauvegarder
mapping_df = pd.DataFrame(mapping, columns=["Private Entity", "External URI", "Confidence"])
mapping_df.to_csv("entity_mapping_200.csv", index=False)
mapping_df.head(10)


# In[53]:


import pandas as pd
from rdflib import URIRef, RDF, OWL
import time
from SPARQLWrapper import SPARQLWrapper, JSON

# Préparer la liste des entités (convertir le set en liste si nécessaire)
entities_list = list(entities)

# Définir le sous-ensemble à traiter (par exemple 2000)
start_index = 0    # tu peux changer si tu reprends plus tard
end_index = 2000
entities_subset = entities_list[start_index:end_index]

# Initialiser le mapping et le SPARQL endpoint
mapping = []
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setReturnFormat(JSON)

# Fonction pour rechercher sur Wikidata
def wikidata_search(label):
    try:
        query = f"""
        SELECT ?item WHERE {{
          ?item rdfs:label "{label}"@en .
        }}
        LIMIT 1
        """
        sparql.setQuery(query)
        results = sparql.query().convert()
        bindings = results["results"]["bindings"]
        if bindings:
            return bindings[0]["item"]["value"], 0.99  # confiance fictive
        else:
            return None, 0.0
    except Exception as e:
        print(f"Erreur pour {label}: {e}")
        return None, 0.0

# Boucle principale
for idx, entity in enumerate(entities_subset, start=start_index+1):
    label = entity.split('/')[-1]
    wd_uri, confidence = wikidata_search(label)

    if wd_uri:
        g.add((entity, OWL.sameAs, URIRef(wd_uri)))
    else:
        g.add((entity, RDF.type, EX["NewEntity"]))

    mapping.append([entity, wd_uri if wd_uri else "N/A", confidence])

    # Affichage de progression toutes les 10 entités
    if idx % 30 == 0:
        print(f"Traitée entité {idx}/{end_index}")

    # Pause pour éviter 429 Too Many Requests
    time.sleep(0.5)

# Sauvegarder le CSV partiel
mapping_df = pd.DataFrame(mapping, columns=["Private Entity", "External URI", "Confidence"])
mapping_df.to_csv(f"entity_mapping_{start_index+1}_{end_index}.csv", index=False)
print("CSV partiel sauvegardé.")


# In[54]:


g.serialize("linked_KB.ttl", format="turtle")
print("Graphe RDF mis à jour sauvegardé sous 'linked_KB.ttl'")


# In[55]:


from rdflib import Graph

# Charger le graphe RDF existant
g = Graph()
g.parse("linked_KB.ttl", format="turtle")

print("Graphe chargé avec succès")
print("Nombre de triplets :", len(g))


# In[56]:


from SPARQLWrapper import SPARQLWrapper, JSON

# Initialiser le endpoint Wikidata
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setReturnFormat(JSON)

print("SPARQL prêt à être utilisé")


# # Phase3

# In[57]:


predicates = set(g.predicates())

print("Nombre de predicates :", len(predicates))

for p in list(predicates)[:10]:
    print(p)


# In[59]:


query = """
SELECT ?property ?propertyLabel WHERE {
  ?property a wikibase:Property .
  ?property rdfs:label ?propertyLabel .

  FILTER(CONTAINS(LCASE(?propertyLabel), "location"))
  FILTER(LANG(?propertyLabel) = "en")
}
LIMIT 10
"""

sparql.setQuery(query)
results = sparql.query().convert()

for result in results["results"]["bindings"]:
    print(result["property"]["value"], "-", result["propertyLabel"]["value"])


# # Alignment scripts and file

# In[60]:


from rdflib import URIRef, OWL

EX = Namespace("http://example.org/")

# Ton predicate
my_predicate = EX.locatedIn

# Predicate Wikidata choisi (ex: P131)
wikidata_predicate = URIRef("http://www.wikidata.org/prop/direct/P131")

# Ajouter l’alignement
g.add((my_predicate, OWL.equivalentProperty, wikidata_predicate))

print("Alignment ajouté !")


# In[61]:


g.serialize("aligned_KB.ttl", format="turtle")
print("Graphe sauvegardé sous 'aligned_KB.ttl'")


# # Phase4

# In[67]:


from rdflib import OWL

aligned_entities = []

for s in g.subjects():
    for o in g.objects(s, OWL.sameAs):
        aligned_entities.append((s, str(o)))

print("Nombre d'entités alignées :", len(aligned_entities))


# # Expansion

# In[68]:


import time
from rdflib import URIRef

max_entities = 100   #  commence avec 50
triples_added = 0

for i, (entity, wiki_uri) in enumerate(aligned_entities[:max_entities]):

    query = f"""
    SELECT ?p ?o WHERE {{
      <{wiki_uri}> ?p ?o .
    }}
    LIMIT 50
    """

    try:
        sparql.setQuery(query)
        results = sparql.query().convert()

        for result in results["results"]["bindings"]:
            p = URIRef(result["p"]["value"])
            o = URIRef(result["o"]["value"])

            g.add((URIRef(wiki_uri), p, o))
            triples_added += 1

        print(f"Entité {i+1}/{max_entities} → OK ({triples_added} triples)")
        time.sleep(1)

    except Exception as e:
        print("Erreur :", e)
        time.sleep(5)


# In[71]:


query = """
SELECT ?s ?p ?o WHERE {
  ?s wdt:P31 ?o .
}
LIMIT 10000
"""

sparql.setQuery(query)
results = sparql.query().convert()

from rdflib import URIRef

count = 0
p = URIRef("http://www.wikidata.org/prop/direct/P31")

for result in results["results"]["bindings"]:
    s = URIRef(result["s"]["value"])
    o = URIRef(result["o"]["value"])

    g.add((s, p, o))
    count += 1

print("Triplets ajoutés :", count)


# In[132]:


print(len(entities))
print("Nombre total de triplets uniques :", len(set(g)))


# In[76]:


from rdflib import URIRef

valid_triples = []

for s, p, o in g:
    if isinstance(s, URIRef) and isinstance(p, URIRef) and isinstance(o, URIRef):
        valid_triples.append((s, p, o))

g_clean = Graph()
for triple in valid_triples:
    g_clean.add(triple)

print("Triplets après nettoyage des URI :", len(g_clean))


# In[299]:


from urllib.parse import quote
from rdflib import Graph, URIRef, RDF, OWL

def safe_uri(uri):
    # Si c'est déjà un URIRef, on prend sa valeur
    if isinstance(uri, URIRef):
        uri = str(uri)
    # Encode les caractères spéciaux
    return URIRef(quote(uri, safe=":/#"))  # : / # restent intacts

# Créer un nouveau graphe propre
g_safe = Graph()

for s, p, o in g_clean:
    try:
        g_safe.add((safe_uri(s), safe_uri(p), safe_uri(o)))
    except Exception as e:
        print(f"Erreur sur le triplet ({s}, {p}, {o}) → {e}")


# # RDF graph

# In[81]:


g_safe.serialize("expanded_KB_clean.ttl", format="turtle")
print("Graphe RDF final nettoyé et URI encodées sauvegardé sous 'expanded_KB_clean.ttl'")


# # TD5

# # Part1

# In[101]:


get_ipython().system('pip install owlready2')


# In[102]:


from owlready2 import *

# Charger l'ontologie depuis le fichier
onto = get_ontology("file://family.owl").load()
print("Ontologie chargée :", onto)


# In[103]:


# Lister toutes les classes
print("Classes dans l'ontologie :")
for cls in onto.classes():
    print("-", cls.name)

# Lister toutes les propriétés de données (DataProperty)
print("\nPropriétés de données :")
for prop in onto.data_properties():
    print("-", prop.name)


# In[105]:


# Récupérer la classe Person depuis l'ontologie
Person = onto.Person

with onto:
    # Créer oldPerson comme sous-classe de Person
    class oldPerson(Person):
        pass

# Vérifier que la classe a bien été créée
print("Classes mises à jour :")
for cls in onto.classes():
    print("-", cls.name)


# In[106]:


# Récupérer la propriété de données hasAge
hasAge = onto.hasAge

print("Propriété récupérée :", hasAge)


# In[113]:


# Parcourir tous les individus de Person
for p in onto.Person.instances():
    # Vérifier que l'individu a un âge
    if hasattr(p, "hasAge") and len(p.hasAge) > 0:
        age = p.hasAge[0]  # OWLReady2 stocke les DataProperty comme liste
        if age > 60:
            p.is_a.append(onto.oldPerson)  # Ajouter oldPerson comme classe

# Vérifier le résultat
print("Individus inférés comme oldPerson :")
for p in onto.oldPerson.instances():
    print("-", p.name, "âge :", p.hasAge[0])


# # Part2

# In[145]:


from rdflib import Graph

g = Graph()
g.parse("expanded_KB_clean.ttl", format="turtle")  # lire Turtle
g.serialize(destination="expanded_KB_clean.owl", format="xml")  # sauvegarder en RDF/XML
print("Conversion terminée : expanded_KB_clean.owl")


# In[146]:


from owlready2 import *

onto = get_ontology("file://expanded_KB_clean.owl").load()
print("Ontologie chargée :", onto)
print("Nombre d'individus :", len(list(onto.individuals())))


# In[147]:


from owlready2 import *

# Charger ontologie vide (après conversion)
onto = get_ontology("file://expanded_KB_clean.owl").load()

# Exemple : créer quelques individus pour tester
with onto:
    p1 = onto.Person("Jean")
    p1.hasAge = [65]
    p2 = onto.Person("Marie")
    p2.hasAge = [45]

    # Inférence manuelle oldPerson
    for p in onto.Person.instances():
        if hasattr(p, "hasAge") and p.hasAge[0] > 60:
            p.is_a.append(onto.oldPerson)

print("Individus après injection :", list(onto.individuals()))


# In[176]:


with onto:
    # Créer la classe Person et oldPerson
    class Person(Thing):
        pass

    class oldPerson(Thing):
        pass

    # Créer une propriété de données pour l'âge
    class hasAge(DataProperty):
        domain = [Person]
        range = [int]

# Vérifier ce qu'on a créé
print("Classes après création :", list(onto.classes()))
print("Propriétés de données après création :", list(onto.data_properties()))


# In[148]:


from rdflib import Graph

# Charger le graphe
g = Graph()
g.parse("expanded_KB_clean.ttl", format="turtle")
print(f"Nombre de triplets dans le graphe : {len(g)}")


# In[149]:


triplets = set()
for s, p, o in g:
    triplets.add((str(s), str(p), str(o)))

triplets = list(triplets)
print(f"Nombre total de triplets uniques : {len(triplets)}")


# # KGE prep

# In[163]:


import random
random.shuffle(triplets)

n = len(triplets)
train_end = int(0.8 * n)
valid_end = int(0.9 * n)

train_triplets = triplets[:train_end]
valid_triplets = triplets[train_end:valid_end]
test_triplets = triplets[valid_end:]

print("ok")


# In[165]:


def save_triplets(triplets, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for s, p, o in triplets:
            f.write(f"{s}\t{p}\t{o}\n")

save_triplets(train_triplets, "train.txt")
save_triplets(valid_triplets, "valid.txt")
save_triplets(test_triplets, "test.txt")

print("Fichiers train.txt, valid.txt et test.txt créés !")


# In[187]:


get_ipython().system('pip install pykeen torch')


# In[188]:


import torch
from pykeen.models import TransE, DistMult
from pykeen.training import SLCWATrainingLoop
from pykeen.triples import TriplesFactory
from pykeen.evaluation import RankBasedEvaluator
import pandas as pd

print("✅ Tous les imports OK!")


# In[189]:


train_factory = TriplesFactory.from_path('train.txt')

test_factory = TriplesFactory.from_path('test.txt', 
                entity_to_id=train_factory.entity_to_id, 
                relation_to_id=train_factory.relation_to_id)

valid_factory = TriplesFactory.from_path('valid.txt', 
                entity_to_id=train_factory.entity_to_id,
                relation_to_id=train_factory.relation_to_id)

print(f"✅ Train:  {train_factory.num_triples} triplets")
print(f"✅ Test:   {test_factory.num_triples} triplets")
print(f"✅ Valid:  {valid_factory.num_triples} triplets")
print(f"\nNombre d'entités:  {train_factory.num_entities}")
print(f"Nombre de relations: {train_factory.num_relations}")


# # KGE train - models

# In[193]:


transe_model = TransE(
    triples_factory=train_factory,
    embedding_dim=50,   # Réduit de 100 à 50
    scoring_fct_norm=2
)

transe_trainer = SLCWATrainingLoop(
    model=transe_model,
    triples_factory=train_factory,
    optimizer='Adam',
    optimizer_kwargs={'lr': 0.001},
)

print("Entraînement TransE en cours...")
transe_losses = transe_trainer.train(
    triples_factory=train_factory,
    num_epochs=30,    # Réduit de 100 à 30
    batch_size=512,   # Augmenté de 256 à 512
)
print("✅ TransE entraîné!")


# In[194]:


distmult_model = DistMult(
    triples_factory=train_factory,
    embedding_dim=50,
)

distmult_trainer = SLCWATrainingLoop(
    model=distmult_model,
    triples_factory=train_factory,
    optimizer='Adam',
    optimizer_kwargs={'lr': 0.001},
)

print("Entraînement DistMult en cours...")
distmult_losses = distmult_trainer.train(
    triples_factory=train_factory,
    num_epochs=30,
    batch_size=512,
)
print("✅ DistMult entraîné!")


# In[195]:


print("Évaluation en cours...")

# Évaluer TransE
transe_evaluator = RankBasedEvaluator()
transe_results = transe_evaluator.evaluate(
    model=transe_model,
    mapped_triples=test_factory.mapped_triples,
    additional_filter_triples=train_factory.mapped_triples,
    batch_size=256,
)

# Évaluer DistMult
distmult_evaluator = RankBasedEvaluator()
distmult_results = distmult_evaluator.evaluate(
    model=distmult_model,
    mapped_triples=test_factory.mapped_triples,
    additional_filter_triples=train_factory.mapped_triples,
    batch_size=256,
)

print("✅ Évaluation terminée!")


# # KGE evaluation - Comparison of results

# In[196]:


print("=" * 50)
print("RÉSULTATS FINAUX SUR LE TEST SET")
print("=" * 50)

print("\n--- TransE ---")
print(f"MRR:     {transe_results.get_metric('mean_reciprocal_rank'):.4f}")
print(f"Hits@1:  {transe_results.get_metric('hits_at_1'):.4f}")
print(f"Hits@3:  {transe_results.get_metric('hits_at_3'):.4f}")
print(f"Hits@10: {transe_results.get_metric('hits_at_10'):.4f}")

print("\n--- DistMult ---")
print(f"MRR:     {distmult_results.get_metric('mean_reciprocal_rank'):.4f}")
print(f"Hits@1:  {distmult_results.get_metric('hits_at_1'):.4f}")
print(f"Hits@3:  {distmult_results.get_metric('hits_at_3'):.4f}")
print(f"Hits@10: {distmult_results.get_metric('hits_at_10'):.4f}")


# In[198]:


from pykeen.evaluation import RankBasedEvaluator

# Évaluation séparée head et tail pour TransE
transe_evaluator = RankBasedEvaluator()
transe_results = transe_evaluator.evaluate(
    model=transe_model,
    mapped_triples=test_factory.mapped_triples,
    additional_filter_triples=train_factory.mapped_triples,
    batch_size=256,
)

# Affichage TransE
print("=" * 55)
print("TRANSE — FILTERED METRICS")
print("=" * 55)

print("\n[HEAD PREDICTION]")
print(f"  MRR:     {transe_results.get_metric('head.realistic.inverse_harmonic_mean_rank'):.4f}")
print(f"  Hits@1:  {transe_results.get_metric('head.realistic.hits_at_1'):.4f}")
print(f"  Hits@3:  {transe_results.get_metric('head.realistic.hits_at_3'):.4f}")
print(f"  Hits@10: {transe_results.get_metric('head.realistic.hits_at_10'):.4f}")

print("\n[TAIL PREDICTION]")
print(f"  MRR:     {transe_results.get_metric('tail.realistic.inverse_harmonic_mean_rank'):.4f}")
print(f"  Hits@1:  {transe_results.get_metric('tail.realistic.hits_at_1'):.4f}")
print(f"  Hits@3:  {transe_results.get_metric('tail.realistic.hits_at_3'):.4f}")
print(f"  Hits@10: {transe_results.get_metric('tail.realistic.hits_at_10'):.4f}")

print("\n[BOTH (averaged)]")
print(f"  MRR:     {transe_results.get_metric('both.realistic.inverse_harmonic_mean_rank'):.4f}")
print(f"  Hits@1:  {transe_results.get_metric('both.realistic.hits_at_1'):.4f}")
print(f"  Hits@3:  {transe_results.get_metric('both.realistic.hits_at_3'):.4f}")
print(f"  Hits@10: {transe_results.get_metric('both.realistic.hits_at_10'):.4f}")

# Évaluation séparée head et tail pour DistMult
distmult_evaluator = RankBasedEvaluator()
distmult_results = distmult_evaluator.evaluate(
    model=distmult_model,
    mapped_triples=test_factory.mapped_triples,
    additional_filter_triples=train_factory.mapped_triples,
    batch_size=256,
)

print("\n" + "=" * 55)
print("DISTMULT — FILTERED METRICS")
print("=" * 55)

print("\n[HEAD PREDICTION]")
print(f"  MRR:     {distmult_results.get_metric('head.realistic.inverse_harmonic_mean_rank'):.4f}")
print(f"  Hits@1:  {distmult_results.get_metric('head.realistic.hits_at_1'):.4f}")
print(f"  Hits@3:  {distmult_results.get_metric('head.realistic.hits_at_3'):.4f}")
print(f"  Hits@10: {distmult_results.get_metric('head.realistic.hits_at_10'):.4f}")

print("\n[TAIL PREDICTION]")
print(f"  MRR:     {distmult_results.get_metric('tail.realistic.inverse_harmonic_mean_rank'):.4f}")
print(f"  Hits@1:  {distmult_results.get_metric('tail.realistic.hits_at_1'):.4f}")
print(f"  Hits@3:  {distmult_results.get_metric('tail.realistic.hits_at_3'):.4f}")
print(f"  Hits@10: {distmult_results.get_metric('tail.realistic.hits_at_10'):.4f}")

print("\n[BOTH (averaged)]")
print(f"  MRR:     {distmult_results.get_metric('both.realistic.inverse_harmonic_mean_rank'):.4f}")
print(f"  Hits@1:  {distmult_results.get_metric('both.realistic.hits_at_1'):.4f}")
print(f"  Hits@3:  {distmult_results.get_metric('both.realistic.hits_at_3'):.4f}")
print(f"  Hits@10: {distmult_results.get_metric('both.realistic.hits_at_10'):.4f}")


# # KGE evaluation - Best models

# In[200]:


print("=" * 60)
print("5.1 — MODEL COMPARISON")
print("=" * 60)

print("""
CONFIGURATION (identical for both models)
------------------------------------------
Embedding dim : 50
Learning rate : 0.001
Batch size    : 512
Epochs        : 30
Optimizer     : Adam
Neg. sampling : SLCWA
""")

print("RESULTS — FILTERED METRICS ON TEST SET")
print("-" * 60)
print(f"{'Metric':<15} {'TransE':>10} {'DistMult':>10} {'Best':>10}")
print("-" * 60)

metrics = [
    ("MRR",
     transe_results.get_metric("both.realistic.inverse_harmonic_mean_rank"),
     distmult_results.get_metric("both.realistic.inverse_harmonic_mean_rank")),
    ("Hits@1",
     transe_results.get_metric("both.realistic.hits_at_1"),
     distmult_results.get_metric("both.realistic.hits_at_1")),
    ("Hits@3",
     transe_results.get_metric("both.realistic.hits_at_3"),
     distmult_results.get_metric("both.realistic.hits_at_3")),
    ("Hits@10",
     transe_results.get_metric("both.realistic.hits_at_10"),
     distmult_results.get_metric("both.realistic.hits_at_10")),
]

for name, t, d in metrics:
    best = "TransE" if t > d else "DistMult"
    print(f"{name:<15} {t:>10.4f} {d:>10.4f} {best:>10}")

print("-" * 60)

print("""
HEAD vs TAIL PREDICTION
-----------------------
TransE   — Head MRR: 0.0954  |  Tail MRR: 0.6122  (strong on tail)
DistMult — Head MRR: 0.1119  |  Tail MRR: 0.0585  (more balanced)

CONCLUSION
----------
TransE outperforms DistMult on all global metrics.
- TransE (MRR=0.35) is ~4x better than DistMult (MRR=0.085).
- TransE excels at tail prediction (MRR=0.61), suggesting that
  relations in this graph are mostly asymmetric.
- DistMult performs slightly better on head prediction (0.11 vs 0.095),
  consistent with its symmetric scoring architecture.
- With more epochs and a larger embedding_dim, DistMult could
  potentially close the gap.
""")


# In[201]:


total = train_factory.num_triples + test_factory.num_triples + valid_factory.num_triples
print(f"Train:  {train_factory.num_triples}")
print(f"Test:   {test_factory.num_triples}")
print(f"Valid:  {valid_factory.num_triples}")
print(f"TOTAL:  {total}")


# import numpy as np
# from pykeen.triples import TriplesFactory
# from pykeen.models import TransE
# from pykeen.training import SLCWATrainingLoop
# from pykeen.evaluation import RankBasedEvaluator
# 
# train_triplets = train_factory.triples
# subsets = [20000, len(train_triplets)]
# labels = ["20k", "Full (25920)"]
# 
# results_sensitivity = {}
# 
# for size, label in zip(subsets, labels):
#     print(f"\n=== Training on {label} triples ===")
#     
#     # Subsample
#     idx = np.random.choice(len(train_triplets), size=size, replace=False)
#     subset_triples = train_triplets[idx]
#     
#     # Utiliser les MEMES mappings que le train original
#     subset_factory = TriplesFactory.from_labeled_triples(
#         subset_triples,
#         entity_to_id=train_factory.entity_to_id,
#         relation_to_id=train_factory.relation_to_id,
#     )
#     
#     # TransE
#     model = TransE(triples_factory=subset_factory, embedding_dim=50)
#     trainer = SLCWATrainingLoop(
#         model=model,
#         triples_factory=subset_factory,
#         optimizer='Adam',
#         optimizer_kwargs={'lr': 0.001},
#     )
#     trainer.train(triples_factory=subset_factory, num_epochs=30, batch_size=512)
#     
#     # Évaluation
#     evaluator = RankBasedEvaluator()
#     res = evaluator.evaluate(
#         model=model,
#         mapped_triples=test_factory.mapped_triples,
#         additional_filter_triples=subset_factory.mapped_triples,
#         batch_size=256,
#     )
#     
#     mrr = res.get_metric("both.realistic.inverse_harmonic_mean_rank")
#     h10 = res.get_metric("both.realistic.hits_at_10")
#     results_sensitivity[label] = {"MRR": mrr, "Hits@10": h10}
#     print(f"  MRR: {mrr:.4f} | Hits@10: {h10:.4f}")
# 
# print("\n=== SUMMARY KB SIZE SENSITIVITY (TransE) ===")
# for label, metrics in results_sensitivity.items():
#     print(f"{label:<15} MRR: {metrics['MRR']:.4f}  Hits@10: {metrics['Hits@10']:.4f}")

# In[211]:


#Performance scales positively with KB size — more training data consistently improves both MRR (+25%) and Hits@10 (+44%). This confirms that larger knowledge bases provide richer context for learning entity and relation embeddings.
#Note that 50k triples was not achievable since the full dataset only contains 25 920 training triples. This should be mentioned in the report.


# In[227]:


import numpy as np

# Supposons que transe_model soit ton modèle TransE entraîné
# et train_factory soit le TriplesFactory utilisé pour l'entraînement

# Récupérer les embeddings des entités
entity_embeddings = transe_model.entity_representations[0](indices=None).detach().cpu().numpy()

# Obtenir le mapping id -> entity
id_to_entity = {idx: ent for ent, idx in train_factory.entity_to_id.items()}

# Fonction pour trouver les k voisins les plus proches
def nearest_neighbors(entity_name, k=5):
    if entity_name not in train_factory.entity_to_id:
        print(f" L'entité {entity_name} n'existe pas dans le vocabulaire.")
        return []

    entity_idx = train_factory.entity_to_id[entity_name]
    vec = entity_embeddings[entity_idx]

    # Calcul de la distance cosinus
    norms = np.linalg.norm(entity_embeddings, axis=1) * np.linalg.norm(vec)
    cosines = entity_embeddings.dot(vec) / norms

    # Trier par proximité
    nearest_idx = np.argsort(-cosines)  # du plus proche au plus éloigné
    neighbors = [id_to_entity[i] for i in nearest_idx if i != entity_idx][:k]
    return neighbors

# Exemple : voisins de "MarieCurie" (ou ton URI dans le dataset)
example_entity = "http://example.org/MarieCurie"  # adapter selon ton dataset
neighbors = nearest_neighbors(example_entity, k=5)
print(f"Nearest neighbors of {example_entity}:")
for n in neighbors:
    print(f" - {n}")


# In[223]:


import torch

# Embeddings des entités
entity_embeddings = transe_model.entity_representations[0]().detach().cpu().numpy()
entity_ids = train_factory.entity_to_id  # dictionnaire URI → id
entities = list(entity_ids.keys())


# In[220]:


get_ipython().system('pip install matplotlib')


# In[224]:


import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt


# # t-SNE Visualization of Entity Embeddings (sampled 1000 entities)

# In[229]:


# Sous-échantillon de 1000 entités
subset_size = 1000
subset_indices = np.random.choice(len(entities), size=subset_size, replace=False)
subset_embeddings = entity_embeddings[subset_indices]
subset_entities = [entities[i] for i in subset_indices]

# Couleurs aléatoires (temporaire)
subset_colors = np.random.rand(subset_size)

# t-SNE
from sklearn.manifold import TSNE
tsne = TSNE(n_components=2, random_state=42, perplexity=30, max_iter=500)
entity_2d = tsne.fit_transform(subset_embeddings)

# Plot
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 8))
plt.scatter(entity_2d[:,0], entity_2d[:,1], c=subset_colors, cmap='Spectral', s=10)
plt.title("t-SNE Visualization of Entity Embeddings (sampled 1000 entities)")
plt.show()


# # t-SNE Visualization of Entity Embeddings (all entities)

# In[230]:


# ─────────────────────────────────────────────
# 6.2 Clustering Analysis – t-SNE + coloring by ontology class
# ─────────────────────────────────────────────
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.manifold import TSNE
from collections import defaultdict

# ── 1. Extraire les embeddings (déjà fait en 6.1, on réutilise) ──
entity_embeddings = transe_model.entity_representations[0](indices=None).detach().cpu().numpy()
id_to_entity = {idx: ent for ent, idx in train_factory.entity_to_id.items()}

# ── 2. Récupérer la classe ontologique de chaque entité ──
# On cherche les triplets de type (entité, rdf:type, Classe)
type_relation = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"  # adapter si besoin

entity_to_class = {}  # URI entité → nom de classe

for h, r, t in train_factory.mapped_triples.tolist():
    h_name = id_to_entity[h]
    r_name = {idx: rel for rel, idx in train_factory.relation_to_id.items()}[r]
    t_name = id_to_entity[t]
    if r_name == type_relation:
        entity_to_class[h_name] = t_name.split("/")[-1].split("#")[-1]  # nom court

# Entités sans classe connue → "Unknown"
all_entities = [id_to_entity[i] for i in range(len(id_to_entity))]
classes = [entity_to_class.get(e, "Unknown") for e in all_entities]

# ── 3. t-SNE réduction 2D ──
print("Running t-SNE... (peut prendre quelques secondes)")
tsne = TSNE(n_components=2, perplexity=30, random_state=42, max_iter=1000)
embeddings_2d = tsne.fit_transform(entity_embeddings)

# ── 4. Mapping classe → couleur ──
unique_classes = sorted(set(classes))
cmap = plt.cm.get_cmap("tab20", len(unique_classes))
class_to_color = {cls: cmap(i) for i, cls in enumerate(unique_classes)}
colors = [class_to_color[c] for c in classes]

# ── 5. Plot ──
plt.figure(figsize=(12, 8))
for i, (x, y) in enumerate(embeddings_2d):
    plt.scatter(x, y, color=colors[i], alpha=0.7, s=30, edgecolors="none")

# Légende
patches = [mpatches.Patch(color=class_to_color[cls], label=cls) for cls in unique_classes]
plt.legend(handles=patches, bbox_to_anchor=(1.01, 1), loc="upper left",
           fontsize=8, title="Ontology Class")

plt.title("t-SNE Visualization of Entity Embeddings\n(colored by ontology class)", fontsize=13)
plt.xlabel("t-SNE Dim 1")
plt.ylabel("t-SNE Dim 2")
plt.tight_layout()
plt.savefig("tsne_clustering.png", dpi=150, bbox_inches="tight")
plt.show()

# ── 6. Discussion ──
print("""
=== Discussion – 6.2 Clustering Analysis ===

1. Do entities of the same class cluster together?
   → Si les entités d'une même classe forment des groupes visuels distincts sur le plot,
     cela indique que TransE a capturé la structure sémantique du graphe.
   → Des clusters bien séparés (ex: toutes les Persons ensemble, toutes les Places ensemble)
     suggèrent que le modèle a appris des représentations cohérentes.

2. Does the embedding capture semantic structure?
   → TransE encode les relations sous forme de translations (h + r ≈ t).
     Si des entités partagent beaucoup de relations similaires, elles tendent à être proches.
   → Cependant, TransE a des limites connues : il gère mal les relations N-N
     et les hiérarchies complexes, ce qui peut produire des clusters bruités.

3. Résultats inexplicables (à mentionner si observés) :
   → Certaines entités peuvent apparaître loin de leur classe attendue.
     Cela peut s'expliquer par :
       - Un manque de triplets rdf:type dans le dataset
       - Des entités très connectées à plusieurs classes à la fois
       - La nature même de t-SNE qui distord les distances globales
       - Un underfitting du modèle (epochs insuffisantes, dimension trop faible)
""")


# In[232]:


import numpy as np

# Récupérer embeddings
entity_embeddings = transe_model.entity_representations[0](indices=None).detach().cpu().numpy()
relation_embeddings = transe_model.relation_representations[0](indices=None).detach().cpu().numpy()

entity_to_id = train_factory.entity_to_id
relation_to_id = train_factory.relation_to_id

# Exemple de relations
r1 = relation_to_id.get("http://example.org/locatedIn")
r2 = relation_to_id.get("http://example.org/livesInCountry")

if r1 is not None and r2 is not None:
    vec_sum = relation_embeddings[r1]

    # Trouver relation la plus proche
    similarities = np.dot(relation_embeddings, vec_sum)
    closest_rel = np.argmax(similarities)

    for rel, idx in relation_to_id.items():
        if idx == closest_rel:
            print("Relation la plus proche :", rel)


# In[234]:


 # ─────────────────────────────────────────────
# 8.2 Embedding verification of the SWRL rule
# vector(bornIn) + vector(locatedIn) ≈ vector(isFrom) ?
# ─────────────────────────────────────────────
import numpy as np

relation_embeddings = transe_model.relation_representations[0](indices=None).detach().cpu().numpy()
id_to_relation = {idx: rel for rel, idx in train_factory.relation_to_id.items()}
relation_to_id = train_factory.relation_to_id

def get_relation_vector(name_fragment):
    """Trouve une relation par fragment de nom."""
    for rel, idx in relation_to_id.items():
        if name_fragment.lower() in rel.lower():
            return relation_embeddings[idx], rel
    return None, None

# Récupérer les vecteurs des relations de la règle
r1_vec, r1_name = get_relation_vector("bornIn")
r2_vec, r2_name = get_relation_vector("locatedIn")
r3_vec, r3_name = get_relation_vector("isFrom")

if r1_vec is not None and r2_vec is not None:
    composed = r1_vec + r2_vec

    # Trouver la relation la plus proche de la composition
    dists = np.linalg.norm(relation_embeddings - composed, axis=1)
    sorted_idx = np.argsort(dists)

    print("=== Rule verification ===")
    print(f"vector({r1_name.split('/')[-1]}) + vector({r2_name.split('/')[-1]})")
    print(f"→ closest relations in embedding space:\n")
    for i in sorted_idx[:5]:
        rel_name = id_to_relation[i].split('/')[-1]
        print(f"   {rel_name:<35} (dist = {dists[i]:.4f})")

    # Vérifier si isFrom est bien en tête
    if r3_vec is not None:
        target_dist = np.linalg.norm(composed - r3_vec)
        rank = np.sum(dists < target_dist) + 1
        print(f"\n→ Rank of '{r3_name.split('/')[-1]}' : {rank} / {len(dists)}")
        if rank <= 3:
            print("✅ The embedding confirms the SWRL rule!")
        else:
            print("⚠️  The embedding does not perfectly confirm the rule.")
            print("   This may be due to insufficient training data or")
            print("   TransE's limitations with compositional patterns.")
else:
    print("Relations not found — adapt name fragments to your dataset.")
    print("Available relations :")
    for rel in list(relation_to_id.keys())[:10]:
        print(f"  {rel}")


# # TD6

# In[235]:


get_ipython().system('pip install rdflib owlready2 requests')


# In[238]:


# Vérification de la version de Python
import sys
print("Python version:", sys.version)

# Vérification de rdflib
try:
    import rdflib
    print("rdflib version:", rdflib.__version__)
except ImportError:
    print("rdflib n'est pas installé. Installez-le avec : pip install rdflib")


# In[246]:


import subprocess

# Chemin complet vers ollama.exe (si PATH non détecté)
ollama_path = r"C:\Users\ayhan\AppData\Local\Programs\Ollama\ollama.exe"

# Vérifier la version depuis Jupyter
try:
    result = subprocess.run([ollama_path, "--version"], capture_output=True, text=True)
    print("Ollama est accessible :", result.stdout.strip())
except FileNotFoundError:
    print("Chemin incorrect. Vérifie le chemin vers ollama.exe")


# In[260]:


import subprocess

ollama_path = r"C:\Users\ayhan\AppData\Local\Programs\Ollama\ollama.exe"

result = subprocess.run([ollama_path, "list"], capture_output=True, text=True)
print(result.stdout)


# In[264]:


import subprocess

ollama_path = r"C:\Users\ayhan\AppData\Local\Programs\Ollama\ollama.exe"

result = subprocess.run(
    [ollama_path, "pull", "gemma:2b"],
    capture_output=True,
    encoding="utf-8",
    errors="ignore"
)
print(result.stdout)
print(result.stderr)


# In[266]:


import subprocess

ollama_path = r"C:\Users\ayhan\AppData\Local\Programs\Ollama\ollama.exe"

# Télécharger Gemma 2B
print("Téléchargement de Gemma 2B… cela peut prendre quelques minutes.")
subprocess.run([ollama_path, "pull", "gemma2b"])
print("Gemma 2B est maintenant disponible.")


# In[265]:


import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma:2b",
        "prompt": "Who are you?",
        "stream": False
    }
)

print(response.json()["response"])


# In[268]:


from rdflib import Graph

g = Graph()
g.parse("expanded_KB_clean.ttl", format="turtle")

print(f"Graphe chargé : {len(g)} triplets")


# In[269]:


from rdflib.namespace import RDF, RDFS, OWL

# 1. Préfixes
prefixes = dict(g.namespaces())
print("=== PRÉFIXES ===")
for prefix, uri in prefixes.items():
    print(f"  {prefix}: <{uri}>")

# 2. Classes
print("\n=== CLASSES ===")
classes = set(g.objects(None, RDF.type))
for c in sorted(classes, key=str)[:20]:  # on limite à 20 pour lisibilité
    print(f"  {c}")

# 3. Prédicats
print("\n=== PRÉDICATS ===")
predicates = set(g.predicates())
for p in sorted(predicates, key=str)[:30]:  # on limite à 30
    print(f"  {p}")


# In[270]:


# Construction du schema summary pour le prompt
schema_summary = """
## RDF Knowledge Graph Schema

### Prefixes
- ns3: <http://example.org/>
- ns1: <http://www.wikidata.org/prop/direct/>
- rdfs: <http://www.w3.org/2000/01/rdf-schema#>
- skos: <http://www.w3.org/2004/02/skos/core#>
- owl: <http://www.w3.org/2002/07/owl#>
- rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

### Classes (rdf:type)
- ns3:PERSON  → a person entity
- ns3:ORG     → an organization entity
- ns3:GPE     → a geopolitical entity (country, city...)

### Key Predicates
- rdfs:label              → name/label of the entity
- skos:altLabel           → alternative name
- ns3:locatedIn           → geographic location
- owl:sameAs              → link to Wikidata entity
- ns1:P106                → occupation (Wikidata)
- ns1:P131                → located in administrative territory
- ns1:P127                → owned by
- ns1:P140                → religion
- ns1:P154                → logo image

### Example entity URI pattern
- http://example.org/SomeName
"""

print(schema_summary)


# In[273]:


# Chercher une entité PERSON avec plus de propriétés
print("=== Exemple PERSON ===")
query = """
SELECT ?entity ?p ?o WHERE {
    ?entity rdf:type <http://example.org/PERSON> .
} LIMIT 1
"""
results = list(g.query(query))
if results:
    entity = results[0].entity
    print(f"Entité : {entity}")
    print("\nTous ses triplets :")
    for p, o in g.predicate_objects(entity):
        print(f"  {p} --> {o}")


# In[274]:


query = """
SELECT ?entity WHERE {
    ?entity rdf:type <http://example.org/PERSON> .
    FILTER(STRLEN(STR(?entity)) > 25)
} LIMIT 10
"""
for row in g.query(query):
    print(row.entity)


# # RAG Pipeline

# In[276]:


import requests

question = "What organizations are located in Toulouse according to your knowledge?"

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma:2b",
        "prompt": question,
        "stream": False
    }
)

print("=== BASELINE (sans RAG) ===")
print(f"Question : {question}")
print(f"Réponse  : {response.json()['response']}")


# In[277]:


import requests
import re

# Le prompt qui demande au LLM de générer du SPARQL
sparql_prompt = f"""
You are a SPARQL expert. Using the following RDF schema, write a SPARQL query to answer the question.

{schema_summary}

Important rules:
- Use PREFIX declarations at the top
- Only use predicates and classes from the schema above
- Return ONLY the SPARQL query, no explanation

Question: What organizations are located in Toulouse?

SPARQL query:
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma:2b",
        "prompt": sparql_prompt,
        "stream": False
    }
)

generated_sparql = response.json()["response"]
print("=== SPARQL GÉNÉRÉ ===")
print(generated_sparql)


# In[279]:


# Étape 5 : Exécuter le SPARQL et capturer l'erreur
def execute_sparql(graph, sparql_query):
    try:
        results = list(graph.query(sparql_query))
        return results, None
    except Exception as e:
        return None, str(e)

results, error = execute_sparql(g, generated_sparql)

if error:
    print(f"Erreur SPARQL : {error}")
else:
    print(f"✅ {len(results)} résultats trouvés")
    for row in results[:10]:
        print(f"  {row}")


# In[282]:


# SPARQL correct basé sur la vraie structure du graphe
corrected_sparql = """
PREFIX ns3: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?organization WHERE {
    ?organization rdf:type ns3:ORG .
    ?organization ns3:locatedIn ns3:Toulouse .
}
"""

results, error = execute_sparql(g, corrected_sparql)

if error:
    print(f" Erreur : {error}")
else:
    print(f" {len(results)} résultats trouvés")
    for row in results[:10]:
        name = str(row.organization).replace("http://example.org/", "").replace("_", " ")
        print(f"  {name}")


# In[284]:


# Chercher toutes les GPE et voir leurs connexions
print("=== Exemples de GPE ===")
query = """
PREFIX ns3: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?entity WHERE {
    ?entity rdf:type ns3:GPE .
} LIMIT 20
"""
for row in g.query(query):
    name = str(row.entity).replace("http://example.org/", "")
    print(f"  {name}")


# In[285]:


# Voir quelques exemples de locatedIn
print("=== Exemples de locatedIn ===")
query = """
PREFIX ns3: <http://example.org/>

SELECT ?subject ?object WHERE {
    ?subject ns3:locatedIn ?object .
} LIMIT 20
"""
for row in g.query(query):
    s = str(row.subject).replace("http://example.org/", "")
    o = str(row.object).replace("http://example.org/", "")
    print(f"  {s} --locatedIn--> {o}")


# In[286]:


# SPARQL correct adapté à la vraie structure
corrected_sparql = """
PREFIX ns3: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?entity ?type WHERE {
    ?entity ns3:locatedIn ns3:France .
    ?entity rdf:type ?type .
} LIMIT 10
"""

results, error = execute_sparql(g, corrected_sparql)

if error:
    print(f" Erreur : {error}")
else:
    print(f" {len(results)} résultats trouvés")
    for row in results:
        name = str(row.entity).replace("http://example.org/", "").replace("_", " ")
        type_ = str(row.type).replace("http://example.org/", "")
        print(f"  {name} ({type_})")


# In[289]:


# Nettoyer les résultats et améliorer le prompt RAG
sparql_query = """
PREFIX ns3: <http://example.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?entity ?type WHERE {
    ?entity ns3:locatedIn ns3:France .
    ?entity rdf:type ?type .
    FILTER(STRLEN(STR(?entity)) > 25)
} LIMIT 15
"""

results, error = execute_sparql(g, sparql_query)

# Contexte nettoyé
context_lines = []
for row in results:
    name = str(row.entity).replace("http://example.org/", "").replace("_", " ").strip()
    type_ = str(row.type).replace("http://example.org/", "")
    if name:
        context_lines.append(f"- {name} is a {type_} located in France")

context = "\n".join(context_lines)

rag_prompt = f"""
You are a helpful assistant. Here is data extracted from a knowledge graph.
Use ONLY this data to answer the question. Do not say the data is missing.

### Knowledge Graph Data:
{context}

### Question:
{question}

### Answer (based only on the data above):
"""

rag_response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma:2b",
        "prompt": rag_prompt,
        "stream": False
    }
)
rag_answer = rag_response.json()["response"]

print("=" * 60)
print(f"Question : {question}")
print("=" * 60)
print("\n BASELINE (sans RAG) :")
print(baseline_answer)
print("\n RAG (avec SPARQL) :")
print(f"\nContexte injecté :\n{context}")
print(f"\nRéponse LLM : {rag_answer}")
print("=" * 60)


# In[297]:


import requests

question = "Tell me about the Emmanuel Macron"

# --- BASELINE : LLM seul sans contexte ---
baseline_response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma:2b",
        "prompt": question,
        "stream": False
    }
)
baseline_answer = baseline_response.json()["response"]

# --- RAG : avec contexte du graphe ---
rag_answer, context = ask_rag(question, g)

# --- AFFICHAGE COMPARAISON ---
print("=" * 60)
print(f" Question : {question}")
print("=" * 60)

print("\n BASELINE (sans RAG) :")
print(baseline_answer)

print("\n RAG (avec SPARQL + KB) :")
print(f"Contexte injecté :\n{context}")
print(f"\nRéponse : {rag_answer}")
print("=" * 60)


# # CLI

# In[292]:


from rdflib import URIRef

def ask_rag(question, graph, model="gemma:2b"):

    # Détecter l'entité dans la question (gère les espaces -> underscore)
    words = question.strip().split()

    # Essayer des combinaisons de mots (1 mot, 2 mots, 3 mots)
    candidates = []
    for i in range(len(words)):
        for j in range(i+1, len(words)+1):
            phrase = "_".join(words[i:j]).capitalize()
            candidates.append(phrase)
            # Aussi avec chaque mot capitalisé
            phrase2 = "_".join(w.capitalize() for w in words[i:j])
            candidates.append(phrase2)

    context = ""

    # Chercher chaque candidat dans le graphe
    for candidate in candidates:
        uri = URIRef(f"http://example.org/{candidate}")
        triples = list(graph.predicate_objects(uri))
        if triples:
            context_lines = [f"Entity: {candidate.replace('_', ' ')}"]
            for p, o in triples:
                pred = str(p).split("/")[-1].split("#")[-1]
                obj = str(o).replace("http://example.org/", "").replace("_", " ")
                context_lines.append(f"- {pred}: {obj}")
            context = "\n".join(context_lines)
            break

    # Fallback si rien trouvé
    if not context:
        context = "No specific data found for this entity in the knowledge graph."

    # Réponse finale
    final_prompt = f"""
You are a helpful assistant. Use ONLY the data below to answer.

### Data:
{context}

### Question:
{question}

### Answer:
"""
    final_response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": final_prompt, "stream": False}
    )
    return final_response.json()["response"], context


# Relancer le CLI
print(" RAG Chatbot (tape 'quit' pour quitter)\n")
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Au revoir !")
        break
    if not user_input:
        continue
    answer, ctx = ask_rag(user_input, g)
    print(f"\n Contexte KB :\n{ctx}")
    print(f"\n Bot : {answer}\n")
    print("-" * 50)


# In[ ]:




