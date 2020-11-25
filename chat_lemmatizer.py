import json

from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Doc
)


class RuLemma():
    def __init__(self):
        emb = NewsEmbedding()

        # extracts token type (noun, verb, punctiation, ...)
        #   and its features like gender, case, singularity, etc.
        self.morph_tagger = NewsMorphTagger(emb) 
        # used to get normal form of a token using its features and type
        #   p.s. can also be used to get a list of possible normal forms
        self.morph_vocab = MorphVocab()
        # extracts tokens from text
        self.segmenter = Segmenter() 

        # load russian stop-words
        with open('stop_words_russian.json', 'r', encoding='utf8') as f:
            self.stop_words = json.load(f)

    def exclude_stop_words(self, tokens):
        '''remove stop-words from tokens'''
        return [token for token in tokens if token not in self.stop_words]

    def lemma(self, text):
        '''create a lemmatized version of the text ignoring punctuation and stop-words'''
        doc = Doc(text)
        # split text into tokens
        doc.segment(self.segmenter)
        # determine tokens' types and features
        doc.tag_morph(self.morph_tagger)

        # find the normal form of each token
        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)

        # remove punctuation symbols
        word_tokens = [token.lemma for token in doc.tokens if token.pos != 'PUNCT']
        # remove stop-words
        cleared_word_tokens = self.exclude_stop_words(word_tokens)

        lemma_text = ' '.join(cleared_word_tokens)
        return lemma_text