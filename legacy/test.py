from db_models import *
from chat_lemmatizer import RuLemma


lemma = RuLemma()

# print('Вопрос ответ')
# try:
#     while True:
#         q = lemma.lemma(input('Вопрос: '))
#         a = input('Ответ: ')
#         QA.insert({
#             QA.question: lemma.lemma(q),
#             QA.answer: a
#         }).execute()
# except KeyboardInterrupt:
#     print('\n')

print('Ответы на вопросы:')
try:
    while True:
        inp = ' OR '.join(lemma.lemma(input('>>')).split())
        print(inp)
        ans = QA.select(QA, QA.bm25().alias('score')).where(QA.match(inp)).order_by(SQL('score')).dicts()
    # .where(QA.match(inp))
    #.order_by(SQL('score').desc()).dicts()
        [print(a) for a in ans]
except KeyboardInterrupt:
    print('bb')