from math import log

import sqlite3

from app import app
from flask import render_template, request, jsonify
import wikipedia
import pickle
import spacy





# Define document






# Sprachmodel laden
nlp = spacy.load('en_core_web_md')

from spacy.lang.en.stop_words import STOP_WORDS

article_name = ''

# Jaccard index berechnen
def jci(en_sentence, simple_text):
    highest_ratio = 0
    sentence_index = 0
    for i in range(len(simple_text)):
        if simple_text[i]:
            if(simple_text[i][0] == '='):
                continue
        ratio = len(set(en_sentence).intersection(simple_text[i])) / float(len(set(en_sentence).union(simple_text[i])))
        if ratio > highest_ratio:
            highest_ratio = ratio
            sentence_index = i
    return highest_ratio, sentence_index

# Jaccard index 2 sentences berechnen
def jci2(en_sentence, simple_text):
    highest_ratio = 0
    sentence_index = 0
    for i in range(len(simple_text)-1):
        if simple_text[i]:
            if (simple_text[i][0] == '='):
                continue
        simple_two_sentences = simple_text[i] + simple_text[i+1]
        ratio = len(set(en_sentence).intersection(simple_two_sentences)) / float(len(set(en_sentence).union(simple_two_sentences)))
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
            sentence_no_stopwords.append(str(word.lemma_).lower())
    return sentence_no_stopwords


# Stopwords entfernen aus Text
def remove_stopwords(text):
    text_no_stopwords = []
    for sentence in range (len(text)):
        my_sentence = nlp(text[sentence])
        new_sentence = []
        for word in my_sentence:
            if word.is_stop == False and word.is_punct == False:
                new_sentence.append(str(word.lemma_).lower())
        text_no_stopwords.append(new_sentence)

    return text_no_stopwords


# Text nach Zeilenumbruechen zerlegen um Titel unterscheiden zu koennen
def process(text):
    text = text.splitlines()
    processed = []
    for i in text:
        if(i):
            if i[0] == '=':
                if i == '== Related pages ==':
                    break
                if i == '== See also ==':
                    break
                if i == '== References ==':
                    break
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
    article_name = selected_query
    algorithms = ['Cosine Vector', 'Jaccard Index', 'Local TF-IDF']
    try:
        wikipedia.set_lang('simple')
        content_simple = wikipedia.WikipediaPage(title=selected_query).content
        simple_page_id = wikipedia.WikipediaPage(title=selected_query).pageid
        content_simple_processed = process(content_simple)

        wikipedia.set_lang('en')
        content_en = wikipedia.WikipediaPage(title=selected_query).content
        content_en_processed = process(content_en)

        page_info = {'id': simple_page_id, 'name': selected_query}
        pickle_page_id = open('page_info.pickle', 'wb')
        pickle.dump(page_info, pickle_page_id)
        pickle_page_id.close()

        simple_no_stopwords = remove_stopwords(content_simple_processed)
        pickle_content_simple_processed = open('content_simple_processed.pickle', 'wb')
        pickle.dump(simple_no_stopwords, pickle_content_simple_processed)
        pickle_content_simple_processed.close()

        return render_template('results.html', algorithms = algorithms, text_simple=content_simple_processed, simple_len=len(content_simple_processed), en_len=len(content_en_processed), text_en=content_en_processed, title=selected_query)

    except wikipedia.exceptions.DisambiguationError as e:
        wikipedia.set_lang("simple")
        content_simple = wikipedia.WikipediaPage(title=e.options[0]).content

        wikipedia.set_lang("en")
        content_en = wikipedia.WikipediaPage(title=e.options[0]).content

        return render_template('index.html', text_simple=content_simple, text_en=content_en, title=e.options[0])


def word_count_f(sent):
    freq = {}
    for word in sent:
        if word in freq:
            freq[word] += 1
        else:
            freq[word] = 1
    return freq


#TF-IDF matching methode
def tfidf(sentence, text):
    wordfreqsent = {}
    sentence_count = 0
    word_count = 0
    for i in range(len(text)):
        sentence_count += 1
        double_sentence = []
        for j in range(len(text[i])):
            if text[i][j][0] == '=':
                sentence_count -= 1
                break
            if text[i][j] not in wordfreqsent:
                wordfreqsent[text[i][j]] = 0
            if(text[i][j] not in double_sentence):
                wordfreqsent[text[i][j]] += 1
            double_sentence.append(text[i][j])
            word_count += 1
        sentence_count += 1


    score = 0
    highest_score = 0;
    sent_index_highest_score = 0

    for i in range(len(text)):
        wc = word_count_f(text[i])
        if text[i][0] == '=':
            continue
        sent_len = len(text[i])
        for word in sentence:
            sent_score = 0
            if word in wc.keys():
                c = wc[word]
            else:
                c = 0
            if word in wordfreqsent:
                score = (c/sent_len)*log(sentence_count/wordfreqsent[word])
                #print(score, c, sent_len, sentence_count, wordfreqsent[word])
            else:
                score = 0

            sent_score += score

        if sent_score > highest_score:
            highest_score = sent_score;
            sent_index_highest_score = i

    return highest_score, sent_index_highest_score

def remove_dublicate_list(mylist):
    mylist = list(dict.fromkeys(mylist))
    return mylist

def sim(sentence, text):
    sentence = remove_dublicate_list(sentence)
    sentence = " ".join(sentence)
    sentence = nlp(sentence)

    highest_score = 0
    c = 0
    for sent in text:
        sent = remove_dublicate_list(sent)
        sent = " ".join(sent)
        if sent:
            if sent[0] == '=':
                c += 1
                continue
        sent = nlp(sent)
        score = sentence.similarity(sent)
        if score > highest_score:
            highest_score = score
            best_sent = sent
            pos = c
        c += 1

    if highest_score < 0.9:
        match = 0
    elif highest_score >= 0.9:
        match = 1

    return pos, highest_score

def sim2(sentence, text):
    sentence = remove_dublicate_list(sentence)
    sentence = " ".join(sentence)
    sentence = nlp(sentence)

    c = 0
    highest_score = 0
    for index, sent in enumerate(text):
        sent = remove_dublicate_list(sent)
        sent2 = remove_dublicate_list(text[index+1])
        sent = " ".join(sent)
        sent2 = " ".join(sent2)
        two_sent = sent + " " + sent2
        if sent[0][0] == '=':
            c += 1
            continue
        two_sent = nlp(two_sent)

        score = sentence.similarity(two_sent)
        if score > highest_score:
            highest_score = score
            best_sent = sent
            pos = c
        c += 1

        if highest_score < 0.9:
            match = 0
        elif highest_score >= 0.9:
            match = 1

        return pos, highest_score



# Ausgewaehlten Satz bekommen und verarbeiten
@app.route('/result/compare', methods=['POST'])
def compare_fetch():
    req = request.get_json()
    sentence = req.get('selected_sentence')
    selected_alg = req.get('selected_alg')
    sentence_no_stopwords = remove_stopwords_sentence(sentence)
    pickle_in = open('content_simple_processed.pickle', 'rb')
    simple_no_stopwords = pickle.load(pickle_in)
    print(selected_alg)
    if(selected_alg == 'Cosine Vector'):
        pos, score = sim(sentence_no_stopwords,simple_no_stopwords)
        pos2, score2 = sim2(sentence_no_stopwords, simple_no_stopwords)

        if score > score2:
            return jsonify(score, pos, 1, 'cosinevector')
        else:
            return jsonify(score2, pos2, 2, 'cosinevector')
    elif(selected_alg == 'Local TF-IDF'):
        tfidf_index, sentence_index = tfidf(sentence_no_stopwords, simple_no_stopwords)
        return jsonify(tfidf_index, sentence_index, 1, 'ltfidf')
    else:
        # JCI berechnen
        jci_index, sentence_index = jci(sentence_no_stopwords, simple_no_stopwords)
        jci_index2, sentence_index2 = jci2(sentence_no_stopwords, simple_no_stopwords)

        if jci_index > jci_index2:
            return jsonify(jci_index, sentence_index, 1, 'jci')
        else:
            return jsonify(jci_index2, sentence_index2, 2, 'jci')

def run_all_algs(sentence_no_stopwords, simple_no_stopwords):

    # Cosine Vector
    match, pos, score = sim(sentence_no_stopwords, simple_no_stopwords)
    match2, pos2, score2 = sim2(sentence_no_stopwords, simple_no_stopwords)

    if score > score2:
        cosine_vector_score = score
    else:
        cosine_vector_score = score2

    # Local TF-IDF
    tfidf_index, sentence_index = tfidf(sentence_no_stopwords, simple_no_stopwords)
    local_tfidf_score = tfidf_index

    # JCI berechnen
    jci_index, sentence_index = jci(sentence_no_stopwords, simple_no_stopwords)
    jci_index2, sentence_index2 = jci2(sentence_no_stopwords, simple_no_stopwords)

    if jci_index > jci_index2:
        jci_score = jci_index
    else:
        jci_score = jci_index

    return jci_score, cosine_vector_score, local_tfidf_score


# Rating und Daten fuer DB vorbereiten
@app.route('/result/prepwritedb', methods=['POST'])
def prepwritedb():
    # DB connection
    conn = sqlite3.connect('align.db')
    c = conn.cursor()

    req = request.get_json()
    en_sentence = req.get('en_sentence')
    simple_sentence = req.get('simple_sentence')
    alg = req.get('alg')
    userrating = req.get('rating')

    pickle_in = open('page_info.pickle', 'rb')
    page_info = pickle.load(pickle_in)
    # page_name = page_info['name']
    # page_id = page_info['id']

    print("ALG: " + str(alg))
    if(alg == 'Jaccard Index'):
        alg_col_name = 'jci_score'
        score = req.get('jci')
        print("JCI")
    elif(alg == 'Cosine Vector'):
        alg_col_name = 'cosine_vector_score'
        score = req.get('cosinevecindex')
        print("COSINE")
    elif(alg == 'Local TF-IDF'):
        alg_col_name = 'local_tfidf_score'
        score = req.get('ltfidf')
        print("LTFIDF")



    c.execute("SELECT match_id FROM matches WHERE first_string = ? AND second_string = ?", [en_sentence, simple_sentence])
    conn.commit()
    res = c.fetchone()
    if res:
        matchid = res[0]

    if res:
        c.execute("INSERT INTO user_ratings (match_id,rating) VALUES(?,?)", (matchid, userrating))
        c.execute("UPDATE scores SET match_id = ?, {} = ?".format(alg_col_name), (matchid, score))
        conn.commit()
    else:
        sentence_no_stopwords = remove_stopwords_sentence(en_sentence)
        simple_no_stopwords = remove_stopwords_sentence(simple_sentence)
        print(simple_no_stopwords)
        #jci_score, cosine_score, local_tfidf_score = run_all_algs(sentence_no_stopwords, [simple_no_stopwords])

        c.execute("INSERT INTO matches (first_string, second_string) VALUES (?,?)", (en_sentence, simple_sentence))
        conn.commit()
        rowid = c.lastrowid
        c.execute("INSERT INTO user_ratings (match_id, rating) VALUES (?,?)", (rowid, userrating))
        c.execute("INSERT INTO scores (match_id, {}) VALUES (?,?)".format(alg_col_name), (rowid, score))
        conn.commit()

    print("Done")

    return '', 204

