from natasha import (
    Segmenter,
    MorphVocab,
    
    NewsEmbedding,
    NewsMorphTagger,

    Doc
)



print('initializing...')

segmenter = Segmenter()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
morph_vocab = MorphVocab()

print('initialized!')
print('calculating')

text = 'Привет, ну что идем домой? Меня зовут Валерий, а тебя?'
doc = Doc(text)
doc.segment(segmenter)
doc.tag_morph(morph_tagger)

for token in doc.tokens:
    token.lemmatize(morph_vocab)

# lemma_text = ''
# for token in doc.tokens:
#     lemma_text += (' ' if token.pos != 'PUNCT' else '') + token.lemma

lemma_text = ' '.join(token.lemma for token in doc.tokens if token.pos != 'PUNCT')
print(lemma_text.strip())


print('finnished!')
# print({_.text: _.lemma for _ in doc.tokens})