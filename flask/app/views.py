from math import log

import sqlite3

from app import app
from flask import render_template, request, jsonify
import wikipedia
import pickle
import spacy
from spacy.pipeline import merge_entities
from collections import Counter



# Define document


# Sprachmodel laden
nlp = spacy.load('en_core_web_md')
nlp.add_pipe(merge_entities)

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


def jci_flex(sentence, simple_text, ands):
    highest_ratio = 0
    sentence_index = 0
    sentence_quan = 1
    ands = ands + 1
    for i in range(len(simple_text)-1):
        if simple_text[i]:
            if (simple_text[i][0] == '='):
                continue
        simple_sentences = []
        local_ratio = -1
        for j in range(ands):

            if i + j < len(simple_text):
                simple_sentences = simple_sentences + simple_text[i+j]

                ratio = len(set(sentence).intersection(simple_sentences)) / float(len(set(sentence).union(simple_sentences)))
                ratio = round(ratio,4)
                local_ratio = round(local_ratio,4)

                if local_ratio < ratio:
                    local_ratio = ratio
                    sentence_quan_local = j+1
        if local_ratio >= highest_ratio:
            highest_ratio = local_ratio
            sentence_index = i
            sentence_quan = sentence_quan_local

    return highest_ratio, sentence_index, sentence_quan


# Stopwords entfernen aus Satz
def remove_stopwords_sentence(sentence):
    sentence_no_stopwords = []
    my_sentence = nlp(sentence)
    commata_and_ands = 0

    for word in my_sentence:
        if word.text == ',' or word.text == 'and':
            commata_and_ands += 1
        if word.is_stop == False and word.is_punct == False:
            if word.ent_type_== '':
                sentence_no_stopwords.append(str(word.lemma_).lower())
            else:
                sentence_no_stopwords.append(str(word.text).lower())



    sentence_ent = []
    local_ent = []
    is_ent = False
    # for word in my_sentence:
    #     print(word.text, word.ent_iob)
    #     if word.ent_iob == 2:
    #         if is_ent:
    #             if len(local_ent) > 1:
    #                 ent = ' '.join(local_ent)
    #             else:
    #                 ent = local_ent[0]
    #             local_ent = []
    #             sentence_no_stopwords.append(str(ent).lower())
    #             is_ent = False
    #         if str(word) == ',' or str(word) == 'and':
    #             commata_and_ands += 1
    #         if word.is_stop == False and word.is_punct == False:
    #             sentence_no_stopwords.append(str(word.lemma_).lower())
    #     if word.ent_iob == 3:
    #         local_ent.append(word.text)
    #         is_ent = True
    #     if word.ent_iob == 1:
    #         local_ent.append(word.text)

    return sentence_no_stopwords, commata_and_ands


# Stopwords entfernen aus Text
def remove_stopwords(text):
    text_no_stopwords = []
    for sentence in range (len(text)):
        my_sentence = nlp(text[sentence])
        new_sentence = []
        if my_sentence.text[0] == '=':
            text_no_stopwords.append([])
            continue
        for word in my_sentence:
            if word.text == ' ':
                continue
            if word.is_stop == False and word.is_punct == False:
                if word.ent_type_ == '':
                    new_sentence.append(str(word.lemma_).lower())
                else:
                    new_sentence.append(str(word.text).lower())
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

        return render_template('results.html', loading = True, algorithms = algorithms, text_simple=content_simple_processed, simple_len=len(content_simple_processed), en_len=len(content_en_processed), text_en=content_en_processed, title=selected_query)

    except wikipedia.exceptions.DisambiguationError as e:
        wikipedia.set_lang("simple")
        content_simple = wikipedia.WikipediaPage(title=e.options[0]).content

        wikipedia.set_lang("en")
        content_en = wikipedia.WikipediaPage(title=e.options[0]).content

        return render_template('index.html', loading = True, text_simple=content_simple, text_en=content_en, title=e.options[0])


def word_count_f(sent):
    freq = {}
    for word in sent:
        if word in freq:
            freq[word] += 1
        else:
            freq[word] = 1
    return freq
def tfidf_flex(sentence, text, ands):
    sentence_count = len(text)
    sentence_length = len(sentence)
    ands = ands + 1
    tf_scores = {}

    #tf
    occurrences = Counter(sentence)
    for word in sentence:
        tf_scores[word] = occurrences[word]/sentence_length


    #df
    df = {}
    for key in tf_scores:
        count = 0
        for sent in text:
            if key in sent:
                count += 1
        df[key] = count

    #tfidf
    tfidf_scores = {}
    for word in sentence:
        tfidf_scores[word] = tf_scores[word]*log(sentence_count/(df[word]+1))


    #Matching
    highest_score = 0
    digit_multiplicator = 1.8
    sent_quan = 0
    for sentence_index, sent in enumerate(text):
        sentence_score = 0
        temp_sentences = []
        local_highest_score = 0
        local_sent_quan = 1
        for i in range(ands):
            if sentence_index + i < len(text):
                if sent:
                    if sent[0] == '=':
                        break

                temp_sentences += text[sentence_index + i]
                for word in sentence:
                    if word in temp_sentences:
                        if word.isdigit():
                            sentence_score += (tfidf_scores[word] * digit_multiplicator)
                        else:
                            sentence_score += tfidf_scores[word]
                #???
                sentence_score = sentence_score / (log(len(temp_sentences)+1) + 1)
                print(highest_score, sentence_score, sent_quan)
                if local_highest_score <= sentence_score:
                    local_highest_score = sentence_score
                    local_sent_quan = i + 1

        if local_highest_score >= highest_score:
            highest_score = local_highest_score
            best_sentence_index = sentence_index
            sent_quan = local_sent_quan



    return highest_score, best_sentence_index, sent_quan



def remove_dublicate_list(mylist):
    mylist = list(dict.fromkeys(mylist))
    return mylist


def sim_flex(sentence, text, ands):

    #sentence = remove_dublicate_list(sentence)
    sentence = " ".join(sentence)
    sentence = nlp(sentence)

    ands += 1
    c = 0
    highest_score = 0

    for index in range(len(text)):
        sentences = ''

        # Ein Satz, zwei Saetze, etc.
        sentences_different_quan = []

        for i in range(0,ands):
            if index+i < len(text):
                sent = remove_dublicate_list(text[index+i])
                if sent:
                    if sent[0] == '=':
                        break
                sent = " ".join(sent)
                sentences = " ".join([sentences,sent])
                sentences_different_quan.append(sentences)

        local_highest_score = 0
        for j in range(0,len(sentences_different_quan)):

            if sentences_different_quan[j][0] == '=' or sentences_different_quan[j] == ' ' or sentences_different_quan[j] == '' or sentences_different_quan == ' ':
                #c += 1
                continue
            sentences_comp = nlp(sentences_different_quan[j])
            score = sentence.similarity(sentences_comp)


            if score > local_highest_score:
                local_highest_score = score
                local_quan = j+1

        if local_highest_score >= highest_score:
            highest_score = local_highest_score

            quan = local_quan
            best_sent = sent
            pos = c
        c += 1
    return pos, highest_score, quan


# Ausgewaehlten Satz bekommen und verarbeiten
@app.route('/result/compare', methods=['POST'])
def compare_fetch():
    req = request.get_json()
    sentence = req.get('selected_sentence')
    selected_alg = req.get('selected_alg')
    sentence_no_stopwords, commata_and_ands = remove_stopwords_sentence(sentence)
    pickle_in = open('content_simple_processed.pickle', 'rb')
    simple_no_stopwords = pickle.load(pickle_in)
    print(selected_alg)
    if(selected_alg == 'Cosine Vector'):
        pos, score, quan = sim_flex(sentence_no_stopwords, simple_no_stopwords, commata_and_ands)
        return jsonify(score, pos, quan, 'cosinevector')

    elif(selected_alg == 'Local TF-IDF'):
        tfidf_index, sentence_index, sent_quan = tfidf_flex(sentence_no_stopwords, simple_no_stopwords,commata_and_ands)
        return jsonify(tfidf_index, sentence_index, sent_quan, 'ltfidf')
    else:
        # JCI berechnen
        jci_index, sentence_index, sentence_quan = jci_flex(sentence_no_stopwords, simple_no_stopwords, commata_and_ands)
        return jsonify(jci_index, sentence_index, sentence_quan, 'jci')



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

