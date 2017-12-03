#Remeber python path consistancy when running this example
from OntologyGeneration import HierarchyGeneration
import sys

##A function to print out the taxonomy in a BFS manner by telling us which parents the node has
#@param forest is the root nodes in our taxonomy
def printBFS(forest):
    queue = [i for i in forest]
    while len(queue) > 0:
        item = queue.pop(0)
        print str(item.getSynSet()),
        if item.getParent() is not None:
            if isinstance(item.getParent(),list): 
                print ",".join([str(i) for i in item.getParent()])
            else:
                print str(item.getParent().getSynSet())
        else:
            print ""
        if item.getChildren() is not None:
            queue.extend(item.getChildren())


##Prints the answers from Hierarchy Generation
#@param answers A dictionary of word->predicted word net nodes which may either be a single node, false, or a list of nodes
def printAnswers(answers):
    for ans in answers:
        if answers[ans] is not None and answers[ans] is not False:
            if isinstance(answers[ans],list):
                print str(ans)+":"+",".join([str(i.getSynSet()) for i in answers[ans]])
            else:
                print str(ans)+":"+str(answers[ans].getSynSet())
        else:
            print str(ans)+":False"


if __name__ == "__main__":
    #This tests out the generation methods
    if sys.argv[1] == "actions":
        generators=HierarchyGeneration.generateVerbSynsets
    else:
        generators=HierarchyGeneration.generatePhysicalSynsets
   
    lines=open(sys.argv[2],'r').readlines() #Here we expect the input to be a list of words:descriptor,descriptor
    ambigious_words=HierarchyGeneration.parseList(lines) #From this, creates a dictionary of word =>[descriptors]
    cutoff_value = float(sys.argv[3]) #Our alpha value
    #This tests out the hueristics and method
    res = HierarchyGeneration.SynsetResolver(ambigious_words,method = "multi-sieve", #Mutlisieve method of Balint and Allbeck 2015
                                             hand_cluster = False, #If we do not find a synset, do not ask the user for help
                                             alpha = cutoff_value, 
                                             multi_parent=True)    #If multiple synsets are above the value, we keep all of them (DAG instead of tree)
    methods=[(HierarchyGeneration.synsetResolve,'independent'),     #Performs resolution on the properties of the synset (synonyms and such). Single pass and don't care about the other elements
             (HierarchyGeneration.definitionResolve,'independent'), #Performs resoultion on the definition of the candidates. Single pass as well
             (HierarchyGeneration.pathResolve,'dependent-repeat')]  #Wu-palmer similarity to build up the synsets. Continues on all synsets until there is no change in the list
    
    res.resolveSynsets(generators,methods)
    answers = res.getAnswers()
    printAnswers(answers)
    forest = res.buildWordNetForest()
    printBFS(forest)
    
