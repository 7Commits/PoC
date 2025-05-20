#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import re
from collections import Counter
import numpy as np

class BM25:
    """
    Implementazione dell'algoritmo BM25 per il calcolo della similarità tra testi
    
    BM25 è un algoritmo di ranking probabilistico basato sul miglioramento di TF-IDF che considera:
    1. Frequenza dei termini (TF): frequenza con cui un termine appare in un documento
    2. Frequenza inversa del documento (IDF): quanto raro è un termine in tutta la collezione di documenti
    3. Normalizzazione della lunghezza: considera l'effetto della lunghezza del documento sulla rilevanza
    """
    
    def __init__(self, docs, k1=1.5, b=0.75):
        """
        Inizializza l'oggetto BM25
        
        Args:
            docs: collezione di documenti, ogni documento è una lista di token
            k1: parametro di saturazione della frequenza dei termini (tra 1.2 e 2.0)
            b: parametro di normalizzazione lunghezza (tra 0 e 1, tipicamente 0.75)
        """
        self.k1 = k1
        self.b = b
        self.docs = docs
        
        # Calcola la lunghezza di ogni documento
        self.doc_len = [len(doc) for doc in docs]
        # Calcola la lunghezza media dei documenti
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if len(self.doc_len) > 0 else 0
        # Calcola la frequenza di ogni termine in ogni documento
        self.doc_freqs = [Counter(doc) for doc in docs]
        # Calcola in quanti documenti appare ogni termine (per IDF)
        self.idf = {}
        
        # Prepara idf per tutti i termini nei documenti
        all_terms = set()
        for doc in docs:
            all_terms.update(doc)
            
        self.calculate_idf(all_terms)
            
    def calculate_idf(self, terms):
        """
        Calcola l'IDF per ogni termine nella collezione di documenti
        
        Args:
            terms: insieme di termini per cui calcolare l'IDF
        """
        N = len(self.docs)
        
        for term in terms:
            # Conta in quanti documenti appare il termine
            n_docs_with_term = sum(1 for doc_freq in self.doc_freqs if term in doc_freq)
            
            # Calcola IDF con formula di Robertson
            self.idf[term] = math.log((N - n_docs_with_term + 0.5) / (n_docs_with_term + 0.5) + 1.0)
            
    def get_score(self, query):
        """
        Calcola il punteggio BM25 per una query rispetto ai documenti
        
        Args:
            query: lista di token che costituisce la query
            
        Returns:
            lista di punteggi per ogni documento
        """
        scores = [0.0 for _ in range(len(self.docs))]
        
        # Calcola IDF per eventuali nuovi termini nella query
        query_terms = set(query)
        new_terms = query_terms - set(self.idf.keys())
        if new_terms:
            self.calculate_idf(new_terms)
        
        # Calcola punteggio per ogni documento
        for doc_idx, doc_freq in enumerate(self.doc_freqs):
            for term in query:
                if term not in doc_freq:
                    continue
                
                # Frequenza del termine nel documento attuale
                f = doc_freq[term]
                
                # Calcola il termine di frequenza normalizzato (con saturazione k1 e normalizzazione lunghezza b)
                numerator = f * (self.k1 + 1)
                denominator = f + self.k1 * (1 - self.b + self.b * (self.doc_len[doc_idx] / self.avgdl))
                
                # Somma il contributo di questo termine al punteggio totale
                tf_term = numerator / denominator
                scores[doc_idx] += self.idf.get(term, 0.0) * tf_term
                
        return scores


def segmenta_testo(testo):
    """
    Funzione per segmentare un testo in parole (tokens)
    
    Args:
        testo: stringa di testo da segmentare
        
    Returns:
        lista di token
    """
    if not testo:
        return []
    
    # Pulisce il testo: converte in minuscolo e rimuove caratteri speciali
    testo = testo.lower()
    # Rimuove punteggiatura mantenendo l'unicità delle parole
    testo = re.sub(r'[^\w\s]', ' ', testo)
    # Rimuove spazi multipli
    testo = re.sub(r'\s+', ' ', testo).strip()
    
    # Divide il testo in token
    tokens = testo.split()
    
    return tokens


def calcola_similarita(query, documenti, k1=1.5, b=0.75):
    """
    Calcola la similarità tra una query e una lista di documenti usando BM25
    
    Args:
        query: stringa di query
        documenti: lista di stringhe di documenti
        k1: parametro di saturazione della frequenza dei termini
        b: parametro di normalizzazione lunghezza
        
    Returns:
        lista di punteggi di similarità
    """
    # Segmenta query e documenti
    query_tokens = segmenta_testo(query)
    doc_tokens = [segmenta_testo(doc) for doc in documenti]
    
    # Inizializza l'oggetto BM25
    bm25 = BM25(doc_tokens, k1, b)
    
    # Calcola i punteggi
    scores = bm25.get_score(query_tokens)
    
    return scores


def calcola_similarita_bidirezionale(testo1, testo2, k1=1.5, b=0.75):
    """
    Calcola la similarità bidirezionale tra due testi usando BM25
    
    Args:
        testo1: primo testo
        testo2: secondo testo
        k1: parametro di saturazione della frequenza dei termini
        b: parametro di normalizzazione lunghezza
        
    Returns:
        punteggio di similarità combinato (media delle due direzioni)
    """
    # Calcola la similarità in entrambe le direzioni
    score1 = calcola_similarita(testo1, [testo2], k1, b)[0]
    score2 = calcola_similarita(testo2, [testo1], k1, b)[0]
    
    # Restituisce la media dei due punteggi
    return (score1 + score2) / 2


def calcola_similarita_normalizzata(testo1, testo2, k1=1.5, b=0.75, max_score=10.0):
    """
    Calcola la similarità bidirezionale tra due testi e la normalizza in percentuale
    
    Args:
        testo1: primo testo
        testo2: secondo testo
        k1: parametro di saturazione della frequenza dei termini
        b: parametro di normalizzazione lunghezza
        max_score: punteggio massimo atteso (per normalizzazione)
        
    Returns:
        punteggio di similarità normalizzato (0-100%)
    """
    # Gestione input problematici
    if testo1 is None or testo2 is None:
        # print(f"DEBUG BM25: Testi invalidi. testo1: {type(testo1)}, testo2: {type(testo2)}")
        return 0.0
    
    if not isinstance(testo1, str) or not isinstance(testo2, str):
        # print(f"DEBUG BM25: Testi non sono stringhe. testo1: {type(testo1)}, testo2: {type(testo2)}")
        # Tenta di convertire in stringa
        try:
            testo1 = str(testo1) if testo1 is not None else ""
            testo2 = str(testo2) if testo2 is not None else ""
        except Exception as e:
            # print(f"DEBUG BM25: Errore durante la conversione: {e}")
            return 0.0
    
    if testo1.strip() == "" or testo2.strip() == "":
        # print(f"DEBUG BM25: Testi vuoti. testo1: '{testo1}', testo2: '{testo2}'")
        return 0.0
    
    try:
        score = calcola_similarita_bidirezionale(testo1, testo2, k1, b)
        
        # Normalizza il punteggio (0-100%)
        normalized_score = min(100, (score / max_score) * 100)
        
        return normalized_score
    except Exception as e:
        # print(f"DEBUG BM25: Errore durante il calcolo: {e}")
        return 0.0


def analizza_parole_chiave(risposta_standard, risposta_utente):
    """
    Analizza le parole chiave mancanti e in eccesso tra due testi
    
    Args:
        risposta_standard: risposta standard/attesa
        risposta_utente: risposta dell'utente
        
    Returns:
        tuple con (parole_mancanti, parole_eccesso)
    """
    # Segmenta i testi
    token_standard = set(segmenta_testo(risposta_standard))
    token_utente = set(segmenta_testo(risposta_utente))
    
    # Identifica le parole mancanti e in eccesso
    parole_mancanti = token_standard - token_utente
    parole_eccesso = token_utente - token_standard
    
    return list(parole_mancanti), list(parole_eccesso)


def genera_suggerimenti(parole_mancanti, livello_match):
    """
    Genera suggerimenti di miglioramento basati sulle parole mancanti
    
    Args:
        parole_mancanti: lista di parole chiave mancanti
        livello_match: livello di match (alto, medio, basso)
        
    Returns:
        stringa con suggerimenti
    """
    if livello_match == "alto":
        if not parole_mancanti:
            return "La risposta è completa e accurata."
        else:
            return f"La risposta è buona, ma potresti includere i seguenti termini: {', '.join(parole_mancanti[:3])}."
    elif livello_match == "medio":
        if parole_mancanti:
            return f"La risposta potrebbe essere migliorata includendo questi concetti chiave: {', '.join(parole_mancanti[:5])}."
        else:
            return "La risposta contiene i termini richiesti ma potrebbe essere più accurata."
    else:  # basso
        if parole_mancanti:
            return f"La risposta manca di concetti fondamentali come: {', '.join(parole_mancanti[:7])}."
        else:
            return "La risposta è lontana da quella attesa, anche se contiene termini simili."