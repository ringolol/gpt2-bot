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
        self.morph_tagger = NewsMorphTagger(emb)
        self.morph_vocab = MorphVocab()
        self.segmenter = Segmenter()

        with open('stop_words_russian.json', 'r', encoding='utf8') as f:
            self.stop_words = json.load(f)

    def exclude_stop_words(self, tokens):
        return [token for token in tokens if token not in self.stop_words]

    def lemma(self, text):
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)

        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)

        word_tokens = [token.lemma for token in doc.tokens if token.pos != 'PUNCT']
        cleared_word_tokens = self.exclude_stop_words(word_tokens)

        lemma_text = ' '.join(cleared_word_tokens)

        return lemma_text