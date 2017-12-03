###############################################################################
##Genertors.py
##Author: J. Timothy Balint
##Last Modified: 2-20-2017
##
##Contains all the generator functions to create candidate synsets
###############################################################################
from nltk.corpus import wordnet as wn
from ..CommonFunctions import compoundWord,transformToWordNetFormat,removeAllEndNumbers
from ..DataStructures import WordNetNode
##Filters out a list of verbs that are not active verbs
#@param synsets The list of candidate synsets
#@returns a list of filtered synsets that only contain active verbs
def removeVerbSynsets(synsets):
        keyword="Somebody"
        new_sets=[]
        for syn in synsets:
            found=False
            for lemma in syn.lemmas():
                for s in lemma.frame_strings():
                    if keyword in s:
                        #We also should add a framenet connection check.
                        #It doesn't make sense to deal with senses that
                        #have no check
                        found=True
            if found:
                new_sets.append(WordNetNode(syn))
        #print "Removed",str(len(synsets)-len(new_sets)),"from search"
        return new_sets

##Filters out a list of nouns that are not physical object children
#@param synsets The list of candidate synsets
#@returns a list of filtered synsets that only contain nouns with a physical object ancestor
def removeNounSynsets(synsets):
        physical=wn.synset("physical_entity.n.01")
        return [WordNetNode(item) for item in synsets if physical.lowest_common_hypernyms(item)[0] == physical]
        

##We create an ordering precedence for finding synsets.
#1)the broken up camel case
#2)the word as a compound fragment
#3)break up the word, and search on each fragment
#@param word The word to have candidates generated from
#@returns A list of all candidate active tense verbs
def generateVerbSynsets(word):
        syn=wn.synsets(word,pos=wn.VERB)
        #if len(syn) == 0:
        words=compoundWord(word)
        syn=wn.synsets(words,pos=wn.VERB)
        #if len(syn) == 0:
        words=word.split('_')
        for w in words:
                syn.extend(wn.synsets(w,pos=wn.VERB))
        syn = list(set(syn))
        #Finally, remove all the synsets that can't be
        #agent actions
        return list(set(removeVerbSynsets(syn)))

##Generates noun synsets using the following precidence
#1)the broken up camel case
#2)the word as a compound fragment
#3)break up the word, and search on each fragment
#@param word The word to have candidates generated from
#@returns A list of all candidate active tense verbs
def generatePhysicalSynsets(word):
        syn=wn.synsets(word,pos=wn.NOUN)
        #if len(syn) == 0:
        words=compoundWord(word)
        syn=wn.synsets(words,pos=wn.NOUN)
        #if len(syn) == 0:
        words=word.split('_')
        for w in words:
                syn.extend(wn.synsets(w,pos=wn.NOUN))
        syn = list(set(syn))
        #Finally, remove all the synsets that can't be
        #agent actions
        return list(set(removeNounSynsets(syn)))

##Converts the word into a lower_case format and sets that as the only candidate. Splits the word if possible
#@param word The word to have candidates generated from
#@returns a list containing a single word candidate as a WordNetNode
def generateWordAsSysnet(word):
        #It should already be coming in WordNet Format, so
        if len(word.split("_")) > 1:
                return [WordNetNode(i) for i in word.split("_")]
        return [WordNetNode(word)]

##Converts the word into a lower_case format and sets that as the only candidate
#@param word The word to have candidates generated from
#@returns a list containing a single word candidate as a WordNetNode
def generateSingleWordAsSynset(word):
        return [WordNetNode(word)]

##Takes in a list of lines, and parsess it into a keyword understandable format
#@param lines A list of lines, where each line is word:keyword1,keyword2... or word:synset
#@returns a dictionary in the form word_in_wordnet_format =>(keyword1,keyword2)
def parseList(lines):
    end_dictionary={}
    for line in lines:
        line=line.strip()
        items=line.split(":")
        word=transformToWordNetFormat(items[0].strip())
        word=removeAllEndNumbers(word)
        if(len(items) > 1):
                keywords=items[1].split(",")
                #Clean up all the test words
                keywords=[w.strip() for w in keywords]
                if(len(keywords) > 0 and len(keywords[0].split(".")) > 1):
                        #Here we could be dealing with a synset
                        try:
                                for i in range(len(keywords)):
                                        keywords[i]=wn.synset(keywords[i])
                        except:
                                pass
                end_dictionary[word]=set(keywords)
        else:
                end_dictionary[word]=None
    return end_dictionary

##Adds to the keyword understandable format for all words
#@param end_dict The dictionary of words connected to keywords
#@param keywords The list of keywords to add to all items in the dictionary
#@returns a dictionary with a modified set of keywords
def addKeyWords(end_dict,keywords):
        keywords=set(keywords) #No point in having multiples
        for key in end_dict:
                #print key,end_dict[key]
                if end_dict[key] is not None:
                        end_dict[key] |=(keywords)
                else:
                        end_dict[key] = keywords

        return end_dict


