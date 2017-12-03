##############################################################
##Action_gen.py
##Author:J. Timothy Balint
##LastModified:12-01-2017
##
##This file performs Word Sense Disambiguation on a word 
##given a sparse set of keywords. We also generate a smaller
##tree forest based on the corpus
##############################################################
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from ..CommonFunctions import printStats,transformToSpaceFormat,transformToPARFormat
from ..DataStructures import WordNetNode
import numpy as np
from random import shuffle
#import matplotlib.pyplot as plt

##Creates a WordNetNode out of a list of words as strings
#@param list_of_strings A list of strings to be turned into WNN
#@returns a list of WNN based off the strings
def createWNNs(list_of_strings):
    return [WordNetNode(i) for i in list_of_strings]
        
            
##Disambiguates synsets based on the word and a set of keywords. This is a general class that will disambiguate and create a wordnet
#forest for any type of word class cluster 
class SynsetResolver:
    ##The initalize function loads all the nessicary stemmers and dictionaries. It also keeps words in a list for comparision
    #@param words A dictionary of the form "word"=>"list of keywords"
    #@param correct_answers (Defaults to None) When using the system for testing, this holds a dictionary of the form "word"=>synset, where "word" should match up to the a word in @param word
    #@param alpha (Defaults to 0.3) The threshold for deciding if a synset is viable
    def __init__(self,words=None,correct_answers=None,method = "choice", hand_cluster = True, multi_parent = None, alpha=0.3,scores=None,no_prune = False):
        ##The list of words and keywords
        self.unresolved=words

        ##The correct answers for statistical comparisions (if any)
        self.correct_answers=correct_answers

        ##The resolved solutions
        self.answers={}
        if words is not None:
            ##This allows us to keep an ordering of words for comparisions
            self.word_list=self.unresolved.keys()

        ##A stemmer used to get the root of a word
        self.stemmer=SnowballStemmer("english")

        ##A list of stopwords nessicary to clean up certain functions
        self.stops=stopwords.words("english")

        ##The threshold needed for a synset to be resolved
        self.alpha=alpha

        ##The type of method we are using (I have three for my dissertation)
        self.method = method

        ##Determines if we are using hand-clustering at the end or not
        self.hand_cluster = hand_cluster

        ##Allows for multiple candidates to represent a synset based on criteria.
        self.multi_parent = multi_parent
        
        ##Formats the scores into a 3 dimensional matrix of word x candidate x heuristic (for debugging puroses)
        if scores is not None:
            self.__counts=[[] for i in self.word_list]
            self.__scores=scores
        else:
            self.__scores=None

        ##If set to true, does not prune the candidates, but leaves them in tact
        self.__no_prune = no_prune
    ##If a word cannot be resolved into a synset, then a simulation author must resolve the synset by hand
    #@param word The synset word that needs to be resolved
    #@param synsets All the candidate synsets
    #@return the synset that the user chooses, or None if they do not choose any
    def chooseSynSet(self,word,synsets):
        '''Allows a choice of Synsets based on the 
        definition'''
        choice=-1
        shuffle(synsets)
        while choice < 0 or choice > len(synsets)+1:
            print "Choose a synset for",word,":"
            counter=0
            for syn in synsets:
                lemma_names=[str(lemma.name()) for lemma in syn.getSynSet().lemmas()]
                lemma_names=",".join(lemma_names)
                print counter,syn.getSynSet().name(),"(",lemma_names,"):",syn.getSynSet().definition()
                counter+=1
            print counter,"None" #The last choice is always none
            try:
                choice=int(raw_input(""))
                if choice < 0 or choice > len(synsets)+1:
                    print "Invalid choice"
            except:
                print "Invalid choice"
                choice=-1 #Make sure we are properly reset
        if choice == len(synsets) or choice < 0:
            return None
        return synsets[choice]

    ##This is our hand resolving metric, which allows an author to choose a synset based on the avalable synsets
    #@param synsets A list of the avalable synsets for a given word
    #@returns The chosen synset, or False otherwise
    def __handResolve(self,word,synsets):
        if len(synsets)==1:
            return synsets[0]
        elif len(synsets) > 1:
            choice=self.chooseSynSet(word,synsets)
            if choice is not None:
                return choice
        return False #If there isn't a way to resolve the synset, it is set to False
    
    ##Using the list of wordss and their associated keywords, this method generates and resolves synsets to all words. If a word cannot be
    #resolved, then the system returns None
    #@param generator A pointer to the generator function that uses the list of words as input
    #@param methods A list of methods that are used to resolve synsets. These methods are written as (method,type) where type is either independent or dependent. Independent methods take a single word, their keywords, and their associated synsets, and (dependent, dependent_repeat) methods take the dictionary of words,keywords, and their associated synsets
    def resolveSynsets(self,generator,methods):
        self.answers={}#Clean out the generated answers
        all_synsets={}
        for word in self.word_list:
            self.answers[word]=None#If the word is unresolved, then it is set to none
            if generator is not None: #Generate the synsets if we have a method
                all_synsets[word]=generator(word)
        if self.method == "multi-sieve":
            self.__multiSeiveResolve(all_synsets,methods)
        elif self.method == "cluster-prob":
            self.__probabilityCluster(all_synsets,methods)
        else:
            for word in all_synsets: #This doesn't resolve polysem words, but assumes we already have it
                if self.multi_parent: #If we have multiple parents, then we can have all of them
                    self.answers[word] = all_synsets[word]
                elif len(all_synsets[word]) == 1: #Just take the first
                    self.answers[word] = all_synsets[word][0]

        #Default for now is Hand resolve
        if self.hand_cluster:
            for word in [word for word in self.answers if self.answers[word] is None]:
                self.answers[word]=self.__handResolve(word,all_synsets[word])
        if self.__scores is not None:
            self.saveScore(all_synsets)

    ##Performs a multi-sieve technique to resolve synsets. Multi-sieve methods are hierarchical in nature, in that once a synset passes the threshold, it is considered a good candidate
    #@param all_synsets A dictionary that holds all candidate synsets
    #@param methods The methods to apply to the synset candidates
    #@returns Nothing, because the final result is stored in self
    def __multiSeiveResolve(self,all_synsets,methods):
        for method in methods:
            #print method[1]
            if method[1] == "independent":
                for word in self.word_list:
                    if self.answers[word] is None:
                        #ret_val returns a tuple of (highest synset, alpha value)
                        ret_val=method[0](word,self.unresolved[word],all_synsets[word],True)
            elif method[1] == "dependent":
                #Dependent one off
                all_syns=sorted({x for v in all_synsets.itervalues() for x in v})
                all_keys=sorted({x for v in self.unresolved.itervalues() for x in v})
                for word in self.word_list:
                    if self.answers[word] is None:
                        method[0](all_synsets[word],[i for i in all_syns if i not in all_synsets[word]],self.unresolved[word],[i for i in all_keys if i not in self.unresolved[word]],True)
            elif method[1] == "dependent-repeat":
                #Dependent repeat until changed
                changed = True
                while changed:
                    all_syns=sorted({x for v in all_synsets.itervalues() for x in v})
                    all_keys=sorted({x for v in self.unresolved.itervalues() for x in v})
                    if not self.multi_parent:
                        found_candidates = [self.answers[i] for i in self.answers if self.answers[i] is not None and self.answers[i] is not False]
                    else:
                        found_candidates = []
                        for i in self.answers:
                            if isinstance(self.answers[i],list):
                                found_candidates.extend(self.answers[i])
                            elif isinstance(self.answers[i],WordNetNode):
                                found_candidates.append(self.answers[i])
                    found_keywords = [i for i in all_keys if i not in self.unresolved[word]]
                    for word in self.word_list:
                        if self.answers[word] is None:
                            method[0](all_synsets[word],found_candidates,self.unresolved[word],found_keywords,True)
                    changed = self.__pruneMultiSieve(all_synsets)
                    #print changed
            self.__pruneMultiSieve(all_synsets) #We do this at each iteration. For dependent-repeat, the iteration after change should have no effect, so it is fine to run once
        if self.__no_prune:
            self.answers = all_synsets

            
    ##Examines the candidates and sets a synset if the synset is higher than alpha
    #@param all_synsets The set of candidate synsets. Each candidate is a WordNetNode
    #@returns Nothing because the work is done to self.answers
    def __pruneMultiSieve(self,all_synsets):
        cans = [word for word in self.answers if self.answers[word] is None] #Gets the candidates who have not been resolved
        changed = False
        for word in cans:
            if len(all_synsets[word]) == 0:
                self.answers[word] = False #We do not have anything for this one, so we return that
            else:
                best = None
                for c in all_synsets[word]:
                    if c.getScore(0) > self.alpha:
                        if self.answers[word] is None: #We add in the later condition for SPH
                            #print word,"is now ",str(c.getSynSet()),"with score",c.getScore(0)
                            self.answers[word] = c
                            changed = True
                        else:
                            if self.multi_parent is not None:
                                #print word,"is now ",str(c.getSynSet()),"with score",c.getScore(0)
                                if isinstance(self.answers[word],list):
                                    if c.getScore(0) == self.answers[word][0].getScore(0):
                                        self.answers[word].append(c)
                                        changed = True
                                    elif c.getScore(0) > self.answers[word][0].getScore(0):
                                        self.answers[word] = c
                                        changed = True
                                else:
                                    if c.getScore(0) == self.answers[word].getScore(0):
                                        self.answers[word] = [self.answers[word],c]
                                        changed = True
                                    elif c.getScore(0) > self.answers[word].getScore(0):
                                        self.answers[word] = c
                                        changed = True 
                            else:
                                if c.getScore(0) > self.answers[word].getScore(0): #If we have a higher one, we replace
                                    #print word,"is now ",str(c.getSynSet()),"with score",c.getScore(0),"from",self.answers[word].getScore(0)
                                    self.answers[word] = c
                                    changed = True
        return changed
                           
    ##Performs an end clustering technique using the scores from all methods to provide a probability score
    #@param all_synsets A dictionary that holds all candidate synsets
    #@param methods The methods to apply to the synset candidates
    #@returns Nothing, because the final result is stored in self
    def __probabilityCluster(self,all_synsets,methods):
        for method in methods:
            if method[1] == "independent":
                for word in self.word_list:
                    if self.answers[word] is None:
                        #ret_val returns a tuple of (highest synset, alpha value)
                        ret_val=method[0](word,self.unresolved[word],all_synsets[word])
            elif method[1] == "dependent":
                #Dependent one off
                all_syns=sorted({x for v in all_synsets.itervalues() for x in v})
                all_keys=sorted({x for v in self.unresolved.itervalues() for x in v})
                for word in self.word_list:
                    if self.answers[word] is None:
                        method[0](all_synsets[word],[i for i in all_syns if i not in all_synsets[word]],self.unresolved[word],[i for i in all_keys if i not in self.unresolved[word]])
        if not self.__no_prune:
            for word in [word for word in self.answers if self.answers[word] is None]:#For probability, we cluster after all methods are finished
                self.answers[word]=self.pruneCandidates(all_synsets[word])
        else:
            self.answers = all_synsets
    ##Takes a bunch of candidates and forces them down into either having one or None. Note, this is the pruning method for our cluster-prob, multi-sieve has it's own method
    def pruneCandidates(self,candidates):
        if len(candidates) == 0:
            return False
        else:
            if not isinstance(self.alpha,int):
                try:
                    max_can=candidates[0]
                    hl=len(max_can.getScore())

                    max_score=self.alpha.predict(max_can.getScore())
                except:
                    return False
                if max_score > 10000: #TODO:This shouldn't happen, but does from time to time with regession. Will fix some day
                    max_score=-1.0
                for i in range(1,len(candidates)):
                    score=self.alpha.predict(candidates[i].getScore())
                    if score > 10000:
                        score=-1.0
                    if score > max_score:
                        max_can=candidates[i]
                        max_score=score
                max_can.setScore([max_score],True)
                return max_can

            else:
                max_cans=candidates[0]
                for i in range(1,len(candidates)):
                    if max_cans.getScore() < candidates[i].getScore():
                        max_cans=candidates[i]
                if max_cans.getScore() < self.alpha:
                    return False
                else:
                    return max_cans
                    
        return candidates
    ##Writes out the scores to a file
    #@param all_synsets
    def saveScore(self,all_synsets):
        if self.__scores is not None:
            fi=open(self.__scores,'w')
            for word in self.word_list:
                if len(all_synsets[word]) > 0:
                    fi.write(word+'\n')
                    for candidate in all_synsets[word]:
                        fi.write(str(candidate.getSynSet())+','.join([str(i) for i in candidate.getScore()])+'\n')
                    
            fi.close()
            
    ##Creates a string represenation of the answer, where each answer is a line of word:answers
    def __str__(self):
        end_string=""
        if len(self.answers) > 0:
            for s in self.word_list:
                if self.answers[s] is not None and self.answers[s] is not False:
                    end_string+=transformToSpaceFormat(s)+":"+str(self.answers[s].name())+"\n"
                else:
                    end_string+=transformToSpaceFormat(s)+":"+"None\n"
        return end_string

    ##Creates a forest of size |clusters| based on the word vector representation of model
    #@param model The word-vector model used to create higher clusters
    #@param clusters a list of clustering methods. If |clusters| = 1, performs the same method until there is a single word left to cluster
    #@returns a list of all WordNetNodes, with their parents attached
    def buildForestWordVectors(self,model,clusters,decomposition = None,print_clusters=False):
        #These are the initial words to cluster
        if not self.multi_parent:
            words_to_cluster = [self.answers[w] for w in self.answers if self.answers[w] is not None and self.answers[w] is not False]
        else:
            words_to_cluster = []
            for w in self.answers:
                if self.answers[w] is not None and self.answers[w] is not False:
                    if len(self.answers[w]) > 1:
                        wnn = WordNetNode(w)
                        for i in self.answers[w]:
                            i.attachChild(wnn,True,self.multi_parent)
                    words_to_cluster.extend(self.answers[w])
        words_to_cluster = list(set(words_to_cluster)) #Make sure they are unique
        #print [str(i) for i in words_to_cluster]
        #First, we remove all words that are not in vocabulary. They are children of no-one
        not_in_vocab = filter(lambda x:str(x) not in model.wv.vocab,words_to_cluster)
        words_to_cluster = filter(lambda x:x not in not_in_vocab,words_to_cluster)
        for cluster in clusters:
            if len(words_to_cluster) > 1:
                for word in words_to_cluster:
                    word.setScore(model[str(word)])
                vectors = [word.getScore()[0] for word in words_to_cluster] #We remove all words not in the vocabulary because we cannot really handle them
                #print vectors
                if decomposition is not None:
                    vectors = decomposition(vectors)
                prediction = cluster.fit_predict(vectors)
                if print_clusters:
                    if len(np.unique(prediction)) == 1:
                        print "Single Cluster",np.unique(prediction)
                    else:
                        print len(np.unique(prediction)),"Clusters"
                    #Reomoved this dependency but easy enough to add back in
                    #plt.scatter(vectors[:,0],vectors[:,1],c=prediction)
                    #plt.show()
                #Now, we have to connect the words that were used in the clusters to the ones that were not (so easy in pandas, need minion)
                for i in range(len(prediction)):
                    words_to_cluster[i].attachToParent(int(prediction[i]))
                new_words = map(lambda x:model.most_similar(positive =map(lambda y: str(y),filter(lambda z:z.getParent() == int(x),words_to_cluster)),topn=1)[0][0],np.unique(prediction)) #[word.getScore()[0] for word in words_to_cluster if word.getParent() == x]
                new_words = [WordNetNode(i) for i in new_words]
                #TODO:When this is converted to pandas, it will be alot cleaner
                for i in np.unique(prediction):
                    for word in words_to_cluster:
                        if isinstance(word.getParent(),int) and word.getParent() == i:
                            #word.attachToParent(new_words[i])
                            new_words[i].attachChild(word)
                words_to_cluster = new_words
                #for new in words_to_cluster:
                #    print new.getChildren()
        return words_to_cluster + not_in_vocab +createWNNs([syn for syn in self.answers if self.answers[syn] is None or self.answers[syn] is False])#This should return the forest, regardless of everything
    
    ##We build a forest from a set of synsets using the WordNet hierarchy.
    #@return This returns a forest, as the roots of the forest
    def buildWordNetForest(self,ans= None):
        #TODO: Clean this up. This gave me trouble during my diss, and there are definetly better ways of doing this
        if ans is not None:
            self.answers = ans
        if not self.multi_parent: #Single parent answers, we get the answers themselves
            all_synsets = [self.answers[syn] for syn in self.answers if self.answers[syn] is not None and self.answers[syn] is not False] #this  makes it go through our answers first
        else:
            all_synsets = []
            for syn in self.answers:#Here, we are getting all the answers for multiparent
                if self.answers[syn] is not None and self.answers[syn] is not False:
                    if isinstance(self.answers[syn],list):
                        all_synsets.extend(self.answers[syn])
                    else:
                        all_synsets.append(self.answers[syn])

        #We get a smattering of the nodes themselves
        syn_dict = {}
        for syn in all_synsets:
            syn_dict[str(syn.getSynSet())] = syn
        all_synsets = syn_dict.values() #throws out WNN that we no longer need
        #for syn in syn_dict:
        #    print syn
        finished_forest = []
        #Build a bunch of trees
        counter = 0 
        for s in self.answers:
            if self.answers[s] is not None and self.answers[s] is not False:
                wnn = WordNetNode(s)
                if isinstance(self.answers[s],list):
                    for ans in self.answers[s]:
                        hyp = syn_dict[str(ans.getSynSet())]
                        if hyp.getParent() is None: #We haven't built the tree yet
                            counter += 1
                            hypes = hyp.getSynSet().hypernym_paths()[0] #This provides us with the full path in the tree
                            prev = hyp
                            prev.attachChild(wnn,True,self.multi_parent)
                            for h in hypes[::-1][1:]: #So many slices
                                h = WordNetNode(h)
                                h.attachChild(prev) #won't be multi at this step
                                prev = h
                                all_synsets.append(h)
                        else:
                            hyp.attachChild(wnn,True,self.multi_parent)
                else: #Single parent hierarhcy
                    hyp = syn_dict[str(self.answers[s].getSynSet())]
                    hyp.attachChild(wnn,True,self.multi_parent)
                    if hyp.getParent() is None: #Here, we are checking to see if we need to add to the parents
                        hypes = hyp.getSynSet().hypernym_paths()[0] #This provides us with the full path in the tree
                        prev = hyp
                        for h in hypes[::-1][1:]: #So many slices
                            h = WordNetNode(h)
                            h.attachChild(prev,True,self.multi_parent)
                            prev = h
                            all_synsets.append(h)
        syn_dict = {}
        for syn in all_synsets:
            swapped = False
            if str(syn.getSynSet()) not in syn_dict:
                syn_dict[str(syn.getSynSet())] = syn #if we haven't found it, we put it in
            else:
                #If it's already in the dictionary, then we swap out
                swapped = True
                fixer = syn_dict[str(syn.getSynSet())] #This is our new node
                if syn.getChildren() is not None: #If our old node has any children
                    for child in syn.getChildren():
                    #    print "Attaching",str(child.getSynSet()),"to",str(syn.getSynSet())
                        fixer.attachChild(child,True,self.multi_parent)
                        child.removeParent(syn)
                #As a final step, I need to remove the synset from it's parent
                if syn.getParent() is not None:
                    syn.getParent().removeChild(syn)
                    #child.attachToParent(syn_dict[str(syn.getSynSet())])
            if syn.getParent() is None and not swapped: #We have a root and did not change the connection
                finished_forest.append(syn)
        return finished_forest + createWNNs([syn for syn in self.answers if self.answers[syn] is None or self.answers[syn] is False])

    ##Removes long strains of the tree (i.e, when |children| is one, it is an un-necessary generation)
    #@param tree The initial tree to run through
    #@a new tree that removes long chains of single parent-children
    def pruneTree(self,tree):
        queue = [t for t in tree] #Copy because we are pushing and popping the tree
        new_forest = []
        while(len(queue) > 0):
            item = queue.pop(0)
            if len(item.getChildren()) == 1:
                node = item.getChildren()[0]
                node.attachToParent(item.getParent())
            else:
                if item.getParent() is None: #We are at a root node
                    new_forest.append(item)
            if len(item.getChildren()) > 0:
                map(lambda x:queue.append(x),node.getChildren())
        return new_forest

    ##Returns the answers as a dictionary (instead of a string like str does)   
    #@returns A Dictionary containing the key value pair of word-synset or word-False
    def getAnswers(self):
        return self.answers

    ##Allows us to set the dictionary key answers to the system if we have saved them out somewhere
    def setAnswers(self,answers):
        self.answers=answers
        return True
            

    
