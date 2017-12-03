import copy

##The wordnet node class is the main data structure for creating and connecting
#ontology objects found in wordnet together
class WordNetNode:
    ##Initalizes the wordnet class, which only requires the synset
    #@param verb The synset object (or string) that is the base of the wordnet object
    def __init__(self,verb):

        ##This holds the synset
        self.__synset=verb

        ##Most wordnet have parent object, and this holds that information
        self.__parent=None

        ##A wordnet node that has children connections are stored as a list here
        self.__children=None

        ##Holds the number information for the ontology
        self.__number=None

        ##For DFS, we also want a post number
        self.__post_number=None
        
        if isinstance(verb,str):
            self.__sense=-1
        else:
            self.__sense=int(verb.name().split(".")[2]) #For synset senses

        ##For scoring the wordnet node
        self.__score=[]

        ##Stores properties related to the node
        ##We can treat these properties as excess information
        #specific to a given synset
        self.__properties=[]

    ##Returns the name of the wordnet node, which is found from self.synset
    def __str__(self):
        '''Returns a print of the verb's name'''
        if isinstance(self.__synset,str):
            my_string=self.__synset
        else:
            my_string=self.__synset.name()
        my_string=my_string.split(".")[0]
        return my_string       

    ##Attaches a wordnet node as a child node
    #@param node The wordnet node to attach to this node
    #@param recip If set to True, attaches the child to the parent
    def attachChild(self,node,recip = True,multi = False):
        if node is not None:
            if self.__children is None:
                self.__children=[node]
            else:
                self.__children.append(node)
            if recip:
                node.attachToParent(self,multi=multi)
    ##Removes a child WNN from the list if it exists
    ##@param node The node that is to be removed
    def removeChild(self,node):
        if node is not None and self.__children is not None:
            if node in self.__children:
                self.__children.remove(node)


    ##Removes a parent node from the list if it exists
    ##@param node The node that is to be removed
    def removeParent(self,node):
        if node is not None and self.__parent is not None:
            if isinstance(self.__parent,list):
                if node in self.__parent:
                    self.__parent = [i for i in self.__parent if i != node]
            else:
                if node == self.__parent:
                    self.__parent = None

    ##Attaches itself to a parent
    #@param node The parent wordnet node
    def attachToParent(self,node,multi=False):
        if not multi or node is None or self.__parent is None:
            #If we aren't doing a multiple parent hierarchy or we are providing None to it
            self.__parent=node
        else:
            if not isinstance(self.__parent,list):
                self.__parent = [self.__parent,node]
            else:
                self.__parent.append(node)

    ##Returns the parent if one exists
    #@param pos The position of the parent in the list
    #@returns The parent node, or None if the node has no parent   
    def getParent(self,pos = -1):
        if pos == -1 or not isinstance(self.__parent,list):
            return self.__parent
        else:
            return self.__parent[pos]

    ##Returns the children of the tree as a list
    #@returns A list of wordnet nodes, or None if this node has no children
    def getChildren(self):
        '''returns a list of children if one exist'''
        return self.__children

    ##Returns the Synset in question
    #@returns a Synset Node using nltk's synsets, or a string if the node is not  synset
    def getSynSet(self):
        '''Returns the actual data in question'''
        return self.__synset

    ##The getter for the sense of the node
    #@returns The sense of the node. -1 indicates there is no sense of the node
    def getSense(self):
        '''Returns the sense of the verb'''
        return self.__sense

    ##The getter for the wordnet number
    #@returns The number assigned to the node, or None if a number has not been assigned
    def getNumber(self):
        return self.__number


    ##Gives the Wordnet Node a number
    #@param number The number to set the node to
    def setNumber(self,number):
        self.__number=number

    ##For synset determination, we attach a score to the node, which may be one of many scores if
    #@param pos The position to replace. Defaults to -1 which means we return the whole list
    #@returns the score or a list of scores
    def getScore(self,pos=-1):
        if pos >= len(self.__score) and pos == 0: #Check for a bug fix I should track down in the poly sem code
            return 0.0 #replacement error
        if pos < 0 or pos >= len(self.__score):
            return self.__score
        else:
            return self.__score[pos]

    ##For synset determination, this is how we set the heuristic scores
    #@param score The score, either as a set of scores (list) or as a scalar value
    #@param replace If set to true, just replaces all the scores with the scalar value
    def setScore(self,score,replace = False):
        if isinstance(score,list):
            self.__score = score
        else:
            if not replace:
                self.__score.append(score)
            else:
                if len(self.__score) == 0:
                    self.__score.append(score)
                else:
                    self.__score = [score] #Replace it all!
                #self.__score[0] = score #We may only have one to replace

    ##The getter for adding properties to a node
    ##@returns a list of the properties attached to a node
    def getProperties(self):
        return self.__properties

    ##The setter for adding properties as a list to a node
    ##@param properties a list of properties to set to the node
    def setProperties(self,properties):
        self.__properties=properties

    ##Performs a recursive search to find all sinks in the graph node
    #@returns All found sinks (nodes with no children)
    def getSinks(self):
        '''Returns all objects that are leaves, recursively'''
        if self.__children is None:
            return [self]
        leaves=[]
        for child in self.__children:
            leaves.extend(child.getSinks())
        return leaves

    ##Determines if the verb is already a synset in the tree.
    #@returns back the node if it is a child of this node or None otherwise
    def inTree(self,verb):
        if self.__synset is verb:
            return self
        if self.__children is not None:
            for child in self.__children:
                found=child.inTree(verb)
                if found is not None:
                    return found
        return None

    ##Determines which properties can be combined from the children onto this node
    def combineProperties(self):
        if self.__children is not None:
            #if str(self) == "Steal":
            #    print list(reduce(lambda x,y:x.intersection(y),[set(i.getProperties()) for i in self.__children]))
            props = list(reduce(lambda x,y:x.intersection(y),[set(i.getProperties()) for i in self.__children]))
            #if len(props) > 0:
            #    print str(self),[str(i) for i in self.__children],props
            if isinstance(self.__properties,list) and len(self.__properties) > 0:
                #print str(self),props,self.__properties
                props = list(set(props).intersection(set(self.__properties)))
                #print str(self),props,self.__properties
                if len(props) > 0:
                    #print str(self),list(set(self.__properties).union(set(props)))
                    self.__properties = list(set(self.__properties).union(props)) #At the end, we absorb them if we can
            else:
                #print str(self),props
                self.__properties = props

    ##Removes properties that are in both the parent and children from the children (so we move the properties up the hierarchy)
    def removePropertiesFromChildren(self):
        if self.__children is not None and isinstance(self.__properties,list):
            for child in self.__children:
                if isinstance(child.getProperties(),list) and len(child.getProperties()) > 0:
                    #print list(filter(lambda x: x not in self.__properties,child.getProperties()))
                    child.setProperties(list(filter(lambda x: x not in self.__properties,child.getProperties())))
                    #if len(child.getProperties()) == 0:
                    #    print str(child),"was removed, is now",str(self)
        
            

    ##Performs a recursive Depth First Search on the given tree.
    #@param start_number The starting number to count in the search
    #@returns The number calculated after running depth first search, including post number counts
    def depthFirstSearch(self,start_number):
        num=start_number
        ##If we don't have a number, then we haven' visited yet
        if self.__number is None:
            self.__number=num
            num+=1
            ##If there are children, then we want to visit them as well
            if self.__children is not None:
                for child in self.__children:
                    num=child.depthFirstSearch(num)
            if self.__post_number is None:
                self.__post_number=num
                num+=1
        return num

    ##This replaces a node with another node, which changes the nodes parent and adds all of it's children
    #@param node The wordnet node to have copied into this node
    def copy(self,node):
        #First, check and see if the node is the same, and if it is, don't do anything
        if node is self:
            return None
    
        if node in self.__children:
            for child in self.__children:
                if child is not node:
                    node.attachChild(child)
        for child in self.__children:
            node.attachChild(child)
        return None
        

##Performs a BFS on a given group of nodes, starting from the root node and
#traversing all of the children, giving each node a number
#@param root The starting node for the system
#@param start_number The number to start counting at
#@returns the end value of the counter  
def breadthFirstSearch(root,start_number):
    nodes=[root]
    if root.getNumber() == None:
        root.setNumber(start_number)
        counter=start_number+1
    else:
        counter=root.getNumber()
    seen_list=[]
    while len(nodes) > 0:
            #Get the next node in the system
            node=nodes.pop(0)
            seen_list.append(node)
            #Add all the child nodes to the system
            children=node.getChildren()
            if children is not None:
                for child in children:
                    if child not in seen_list:
                        nodes.append(child)
            if node.getNumber() == None:
                #Add the node to the list of nodes
                node.setNumber(counter)
                #Finally, increment the counter
                counter+=1
    return counter
##Performs a BFS on a forest of rooted trees
#@param roots A list (Note that this has to be a list) of roots
#@param start number the number to start on
#@returns The last number +1 that was added to the list (i.e, the size of the forest). If roots isn't a list or is empty, it will return start_number
def breadthFirstForestSearch(roots,start_number):
    if not isinstance(roots,list):
        return start_number
    nodes = roots
    seen_list=[] #Shouldn't matter because we have no cycles
    while len(nodes) > 0:
        #Get the next node in the system
            node=nodes.pop(0)
            seen_list.append(node)
            #Add all the child nodes to the system
            children=node.getChildren()
            if children is not None:
                for child in children:
                    if child not in seen_list:
                        nodes.append(child)
            if node.getNumber() == None:
                #Add the node to the list of nodes
                node.setNumber(counter)
                #Finally, increment the counter
                counter+=1
    return counter
## Combines all information of WordNetNodes stored in root to the highest level, in place
#  @param roots The roots of all WordNetNodes tree
def treePropertyCleanUp(roots):
    #TODO: This code could be streamlined to start at the leaf nodes and simply work our way up
    #BFS search to get all the nodes into a stack (bottom up BFS search)
    for root in roots:
        stack = []
        bfs = [root]
        seen_list = []
        while len(bfs) > 0:
            top = bfs.pop(0)
            if top not in seen_list:
                seen_list.append(top)
                stack.insert(0,top)
                children = top.getChildren()
                if children is not None:
                    for child in children:
                        if child not in seen_list:
                            bfs.append(child)
        seen_list = []
        #Here, we have the stack, and so we combine properties from our bottom up BFS stack
        while len(stack) > 0:
            top = stack.pop(0)
            parents = top.getParent()
            if isinstance(parents,list):
                for parent in parents:
                    if parent not in seen_list:
                        #TODO:Lets pop off the children because they have already been seen (and we should be in order because reverse)
                        parent.combineProperties()
                        seen_list.append(parent)
            else:
                if parents is not None and parents not in seen_list:
                    parents.combineProperties()
                    seen_list.append(parents)
        #Finally, we clear out any repeat properties
        pars = list(set(map(lambda x:x,root.getSinks())))
        while len(pars) > 0:
            top = pars.pop(0)
            if top is not None:
                if isinstance(top,list):
                    for t in top:
                        t.removePropertiesFromChildren()
                        if t.getParent() is not None:
                            if isinstance(t.getParent(),list):
                                pars.extend(t.getParent())
                            else:
                                pars.append(t.getParent())
                else:
                    top.removePropertiesFromChildren()
                    if top.getParent() is not None:
                        if isinstance(top.getParent(),list):
                            pars.extend(top.getParent())
                        else:
                            pars.append(top.getParent())
        
    
    

            
