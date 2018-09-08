from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status, mixins
import json, string
from elasticSearch.serializers import DummySerializer

def stem(sentence) :
    sentence_arr = str(sentence).translate(None, string.punctuation).lower().split()
    for word in sentence_arr :
        yield word


class IndexViewSet(viewsets.ModelViewSet) :

    def create(self, request) :
        data = request.data.get('data', '')
        title = request.data.get('title', '')
        doc_id = request.data.get('id', '')
        if not data or not title or not doc_id :
            return Response("data, title, id are mandatory", status=status.HTTP_400_BAD_REQUEST)

        inverted_index = get_inverted_index()
        idf = get_word_df_dict()
        tf = {}
        for sw in stem(data) :
            if not sw in inverted_index :
                inverted_index[sw] = []
            inverted_index[sw].append(doc_id)
            if not sw in tf :
                tf[sw] = 0
            tf[sw] += 1
            
            #wont work in edit case
            if not sw in idf :
                idf[sw] = 1
            else :
                if tf[sw] == 1 : #check if same word is not appearing twice in this document
                    idf[sw] += 1

        with open('inverted_index.json', 'w') as f :
            json.dump(inverted_index, f)

        with open('idf', 'w') as f :
            json.dump(idf, f)


        with open('db.json', 'a') as f :
            update_seek_pos(f.tell(), doc_id)
            to_write = request.data
            to_write['id'] = doc_id
            to_write['tf'] = tf
            f.write(json.dumps(to_write)+"\n")

        return Response("Successfully added",  status=status.HTTP_200_OK)

def update_seek_pos(pos, pk) :
    id_pos_dict = get_id_pos_dict()
    id_pos_dict[str(pk)] = pos
    with open('id_pos', 'w') as f :
        json.dump(id_pos_dict, f)

def get_id_pos_dict() :
    try :
        with open('id_pos') as f :
            return json.loads(f.read())
    except IOError :
        return {}

def get_word_df_dict() :
    try :
        with open('idf') as f:
            return json.loads(f.read())
    except IOError :
        return {}


def get_inverted_index() :
    try :
        with open('inverted_index.json') as f :
            return json.loads(f.read())
    except IOError :
        return {}

def get_index_of(sentence_arr, word) :
    try :
        index = sentence_arr.index(word)
    except ValueError :
        return -1

    return index

def get_line_from_db() :
    with open('db.json') as f :
        for line in f :
            yield line

def get_score(data, words, word_df_dict) :
    score = 0
    tf = data.get('tf', None)
    if not tf :
        return count
    for word in words :
        score += tf.get(word, 0)
        # if word_df_dict :
            # word_df = word_df_dict.get(word, 1)
            # score = float(score)/word_df

    return score

class SearchViewSet(viewsets.ModelViewSet) :
    serializer_class = DummySerializer

    def list(self, request) :
        query = request.GET.get('q', '')
        match_phrase = request.GET.get('match_phrase', False)
        resp = []
        if not query :
            return Response("Please specify a query", status=status.HTTP_400_BAD_REQUEST)

        words = list(stem(query))
        inverted_index = get_inverted_index()
        found = set()
        for word in words :
            curr_set = set(inverted_index.get(word, []))
            found = found.union(curr_set)
        id_pos_dict = get_id_pos_dict()
        idf_dict = get_word_df_dict()
        try :
            with open('db.json') as f :
                for doc_id in found :
                    seek_pos = id_pos_dict.get(str(doc_id), -1)
                    if seek_pos == -1 :
                        continue
                    f.seek(seek_pos)
                    to_append = json.loads(f.readline())
                    if match_phrase :
                        if ' '.join(words) in to_append['data'] :
                            resp.append(to_append)
                            to_append['score'] = get_score(to_append, words, idf_dict)
                    else :
                        resp.append(to_append)
                        to_append['score'] = get_score(to_append, words, idf_dict)
                        


            resp = sorted(resp, key=lambda r : r['score'], reverse=True)
            d = self.get_serializer(resp, many=True)
            return Response(d.data, status=status.HTTP_200_OK)

        except IOError :
            return Response("Nothing is indexed till now", status=status.HTTP_400_BAD_REQUEST)

