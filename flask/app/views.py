from app import app
from flask import render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import wikipedia
import pickle
import spacy

# DB connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ratings.db'
db = SQLAlchemy(app)


class Ratings(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    simple_sentence = db.Column(db.String, nullable = False)
    en_sentence = db.Column(db.String, nullable = False)
    rating = db.Column(db.Integer, nullable = False)
    jci = db.Column(db.Float, nullable=False)

# Sprachmodel laden
nlp = spacy.load('en_core_web_sm')

from spacy.lang.en.stop_words import STOP_WORDS

# Jaccard index berechnen
def jci(en_sentence, simple_text):
    highest_ratio = 0
    sentence_index = 0
    for i in range(len(simple_text)):
        ratio = len(set(en_sentence).intersection(simple_text[i])) / float(len(set(en_sentence).union(simple_text[i])))
        if ratio > highest_ratio:
            highest_ratio = ratio
            sentence_index = i
    return highest_ratio, sentence_index

# Stopwords entfernen aus Satz
def remove_stopwords_sentence(sentence):
    sentence_no_stopwords = []
    my_sentence = nlp(sentence)
    for word in my_sentence:
        if word.is_stop == False and word.is_punct == False:
            sentence_no_stopwords.append(str(word).lower())
    return sentence_no_stopwords


# Stopwords entfernen aus Text
def remove_stopwords(text):
    text_no_stopwords = []
    for sentence in range (len(text)):
        my_sentence = nlp(text[sentence])
        new_sentence = []
        for word in my_sentence:
            if word.is_stop == False and word.is_punct == False:
                new_sentence.append(str(word).lower())
        text_no_stopwords.append(new_sentence)

    return text_no_stopwords


# Text nach Zeilenumbruechen zerlegen um Titel unterscheiden zu koennen
def process(text):
    text = text.splitlines()
    processed = []
    for i in text:
        if(i):
            if i[0] == '=':
                processed.append(str(i))
                continue
            elif i[0] == '':
                continue
            else:
                doc = nlp(i)
                for sent in doc.sents:
                    processed.append(str(sent))

    return (processed)


@app.route('/')
def index():
    return render_template('index.html')

# Wiki Suche
@app.route('/', methods=['POST'])
@app.route('/result', methods=['POST'])
def search_form():

    search_text = request.form['search_text']

    try:
        wikipedia.set_lang("simple")
        result_list = wikipedia.search(search_text)
        return render_template('index.html', len = len(result_list), result_list=result_list)

    except wikipedia.exceptions.DisambiguationError as e:
        wikipedia.set_lang("simple")
        content_simple = wikipedia.WikipediaPage(title=e.options[0]).content

        wikipedia.set_lang("en")
        content_en = wikipedia.WikipediaPage(title=e.options[0]).content

        return render_template('index.html', text_simple=content_simple, text_en=content_en, title=e.options[0])

# Wiki Suchergebnisse
@app.route('/result', methods=['GET', 'POST'])
def result():
    selected_query = request.args.get('query')
    try:
        wikipedia.set_lang('simple')
        content_simple = wikipedia.WikipediaPage(title=selected_query).content
        content_simple_processed = process(content_simple)

        wikipedia.set_lang('en')
        content_en = wikipedia.WikipediaPage(title=selected_query).content
        content_en_processed = process(content_en)

        simple_no_stopwords = remove_stopwords(content_simple_processed)
        pickle_content_simple_processed = open('content_simple_processed.pickle', 'wb')
        pickle.dump(simple_no_stopwords, pickle_content_simple_processed)
        pickle_content_simple_processed.close()

        return render_template('results.html', text_simple=content_simple_processed, simple_len=len(content_simple_processed), en_len=len(content_en_processed), text_en=content_en_processed, title=selected_query)

    except wikipedia.exceptions.DisambiguationError as e:
        wikipedia.set_lang("simple")
        content_simple = wikipedia.WikipediaPage(title=e.options[0]).content

        wikipedia.set_lang("en")
        content_en = wikipedia.WikipediaPage(title=e.options[0]).content

        return render_template('index.html', text_simple=content_simple, text_en=content_en, title=e.options[0])

# Ausgewaehlten Satz bekommen und verarbeiten
@app.route('/result/compare', methods=['POST'])
def compare_fetch():
    req = request.get_json()
    sentence = req.get('selected_sentence')
    sentence_no_stopwords = remove_stopwords_sentence(sentence)
    pickle_in = open('content_simple_processed.pickle', 'rb')
    simple_no_stopwords = pickle.load(pickle_in)

    # JCI berechnen
    jci_index, sentence_index = jci(sentence_no_stopwords, simple_no_stopwords)
    print(jci_index, sentence_index)

    return jsonify(jci_index, sentence_index)

# Rating und Daten fuer DB vorbereiten
@app.route('/result/prepwritedb', methods=['POST'])
def prepwritedb():
    req = request.get_json()
    en_sentence = req.get('en_sentence')
    simple_sentence = req.get('simple_sentence')
    jci = req.get('jci')
    rating = req.get('rating')
    write_database(simple_sentence, en_sentence, jci, rating)

    return '', 204

# Daten in die DB schreiben
def write_database(simple_s, en_s, jcindex, user_rating):
    sri = Ratings(simple_sentence=str(simple_s), en_sentence=str(en_s), jci=float(jcindex), rating=int(user_rating))

    db.session.add(sri)
    db.session.commit()
    db.session.flush()
    a = Ratings.query.all()
    for b in a:
        print(b.en_sentence)
    return '', 204