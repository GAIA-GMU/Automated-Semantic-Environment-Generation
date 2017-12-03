###############################################################################
##Hueisics.py
##Author:J. Timothy Balint
##Last Modified: 12-1-2017
##
##Contains a list of heuristics used in word sense disambiguation for a sparse
##number of surrounding words
###############################################################################
from nltk.corpus import stopwords

##Uses the Jaccard index to compare one vector to another. It is assumed that the passed in vectors are sorted for faster processing and an error in processing will occur if they are not.
#@param vec1 The iterable full of values to compare
#@param vec2 The other iterable full of values to compare
#@returns a float of the jacard comparision
def JaccardCompare(vec1,vec2):
    union_count=len(vec1)+len(vec2)
    intersection_count=0
    i=0
    j=0
    while i<len(vec1) and j<len(vec2):
        if vec1[i] == vec2[j]:
            intersection_count+=1
            i+=1
            j+=1
        elif vec1[i] < vec2[j]:
            i+=1
        else:
            j+=1
    union_count-=intersection_count
    return float(intersection_count)/float(union_count)


##Creates a unique sorted list from a given list
#@param li the iterable with duplicate values
#@returns a list with no duplicate values
def unique(li):
    return sorted(list(set(li)))

##Uses only a direct string comparision to determine a percentage total count
#@param words The set of words being compared
#@param keywords The set of keywords being compared
#@returns a percentage of found keywords to total keywords
def directHueristic(words,keywords):
    if len(keywords) == 0:
        return 0
    return float(len(words.intersection(keywords)))/len(words.union(keywords))

##Performs cosine simlarity between sets
#@param words The first set of tokenized words
#@param keywords The second set of tokenized words
#@returns cosine similarity score between 0 and 1
def cosineSimilary(words,keywords):
    if len(words) == 0 or len(keywords) == 0:
        return 0 #No score here
    return float(len(words.intersection(keywords)))/(len(words)*len(keywords))

##Uses the lemma of a synset to determine a percentage count total
#@param synset The synset being tested
#@param keywords The list of keywords to be compared against
#@returns a percentage of found keywords to total keywords
def lemmaHueristic(synset,keywords):
    '''Uses the lemma of the synset to determine if any of the keywords are used
    by the synset'''
    if len(keywords) == 0:
        return 0
    total_count=0
    try:
        lemmas=synset.getSynSet().lemma_names()
    except: #FIX THIS TO BE BETTER
        lemmas=synset.lemma_names()
    lemmas=set(lemmas)#Must be a set so we have no duplicates
    return directHueristic(lemmas,keywords)


##Examines all child words for a given synset. This is a BFS on all the child synsets
#@param synset The synset being tested
#@param keywords The list of keywords to be compared against
#@returns a percentage of found keywords to total keywords, cooresponding to the highest found parameter
def childSynsetHueristic(synset,keywords):
    '''Examines the lemmas of each child to determine if any
    match can be made. We do a BFS of three levels'''
    search_items=[synset.getSynSet()]
    first_next_level=synset
    score=0.0
    seen = []
    while len(search_items) > 0:
        syn=search_items.pop(0)
        seen.append(syn)
        #print synset,len(search_items)#[str(i) for i in syn.hyponyms()]
        if(score > lemmaHueristic(syn,keywords)):
            score=lemmaSynHueristic(syn,keywords)
        new_sets=syn.hyponyms()
        search_items.extend([i for i in new_sets if i not in seen])         
    return score

##property Heuristic considers the properties attached to a candidate node, and determines a score based on the jaccard index
#@param node A wordnet node with attached properties
#@param keywords The keywords connected with known_synset (if any)
#@returns a score for the synset
def propertyHueristic(node,keywords):
    if len(keywords) == 0:
        return 0
    total_count=0
    properties=set(node.getProperties())
    return directHueristic(properties,keywords)

##Does a single wu-palmer similarity metric between all possible synsets one time
#@param candidate The candidate to test agains the others
#@param all_synsets The list of synsets to perform the test agains
#@returns The maximum score between the candidate and all synsets
def ClusterResolve(candidate,all_synsets):
    max_score=candidate.getSynSet().wup_similarity(all_synsets[0].getSynSet())
    for syn in all_synsets:
        score=candidate.getSynSet().wup_similarity(syn.getSynSet())
        if score > max_score:
            max_score=score
    return max_score

##Definition resolve considers all information based on the words in the definition
#and therefore, is a general methods that can build up a vague understanding
#@param word the word to be resolved
#@param keywords the list of keywords provided by the system
#@synsets The list of candidate synsets to test
def definitionResolve(word,keywords,synsets,replace = False):
    methods=[directHueristic]
    stop_words=stopwords.words("english")
    for syn in synsets:
        diction=syn.getSynSet().definition().split()
        diction=[word.strip() for word in diction if word not in stop_words]
        #Removed self.stemmer.stem
        diction=set([word.lower() for word in diction])
        for method in methods:
            score=method(diction,keywords)
            if not replace:
                syn.setScore(score)
            else:
                if syn.getScore(0) < score:
                    syn.setScore(score,replace)
    return None

##Synonym resolve considers all information based on only the word
#@param word the word to be resolved
#@param keywords the list of keywords provided by the system
#@synsets The list of candidate synsets to test
def synsetResolve(word,keywords,synsets,replace = False):
    methods=[lemmaHueristic,childSynsetHueristic]
    for syn in synsets:
        for method in methods:
            score=method(syn,keywords)
            if not replace:
                syn.setScore(score)
            else:
                if syn.getScore(0) < score:
                    syn.setScore(score,replace)
    return  None

##Property resolve considers all information based on the additional properties of the word
#@param word the word to be resolved
#@param keywords the list of keywords provided by the system
#@synsets The list of candidate synsets to test
#@returns None
def propertyResolve(word,keywords,synsets):
    methods=[propertyHueristic]
    for syn in synsets:
        for method in methods:
            score=method(syn,keywords)
            syn.setScore(score)
    return None

##Path clustering considers all the found synsets so far, and connects them to unresolved synsets
#@param known_synset A resolved synset in the list
#@param keywords The keywords connected with known_synset (if any)
#@param candidates The list of possible synsets for an unresolved word
#@param candidate_keywords The list of possible keywords for an unresolved word
#@returns a tuple of (highest_synset,score)
def pathClustering(known_synset,keywords,candidates,candidate_keywords):
    score=0.0 #TODO: Is this using the old way of doing things?
    highest=None
    for can in candidates:
        if known_synset.getSynSet().wup_similarity(can.getSynSet()) > score:
            score=known_synset.getSynSet().wup_similarity(can.getSynSet())
            highest=can
    return (highest,score)

##Path clustering between a synset and another group of synsets
#@param candidate The candidate score to be tested
#@param all_synsets The set of sysnsets to compare to
#@param keywords not used
#@param all_synset_keywords not used
#@param replace Determines if the highest score is replaced or added to the wordNetNode
def pathResolve(candidates,all_synsets,keywords,all_synset_keywords,replace = False):
    methods=[ClusterResolve]
    if len(all_synsets) == 0:
        return None
    for can in candidates:
        for method in methods:
            score=method(can,all_synsets)
            if not replace:
                can.setScore(score)
            else:
                if can.getScore(0) < score:
                    can.setScore(score,replace)                
    return None

def clusterMaxResolve(candidates,all_synsets,keywords,all_synset_keywords,replace = False):
    methods=[ClusterResolve]
    scores=[]
    for can in candidates:
        for method in methods:
            score=method(can,all_synsets)
            scores.append(score)
            #can.setScore(can.getScore()+score)
    if len(scores) > 0:
        avg=float(sum(scores))
        if abs(avg) > 0.001:
            scores=[i/avg for i in scores]
            for i in range(len(candidates)):
                if not replace:
                    candidates[i].setScore(scores[i])
                else:
                    if candidates[i].getScore(0) < scores[i]:
                        candidates[i].setScore(scores[i],replace)                
    return None


