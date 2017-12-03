from __future__ import unicode_literals
import re,sys,inspect,pickle  #Tells you the information for a module inspect.getmembers(module)
#from spacy.en import English

##Finds text representing semantics using regular expressions
class PatternSemantics:
    ##Initalizes the regular expressions used in the system
    #@param pattern the search pattern to find semantics
    #@param tagger An optional tagger to transform the text
    #@param splitter Used to split up text into a list of sentences
    def __init__(self,pattern="adj",tagger=None,splitter=r"\? |! |\. |\n"):
        self.pattern=re.compile(pattern)
        self.tagger=tagger
        self.splitter=re.compile(splitter)

    ##The function that gets the properties from a piece of text
    #@param text a string or list of strings containing the text to mine for properties
    #@returns A list of unique properties
    def getProperties(self,text):
        #Here, we want to make sure that we are dealing with a list of strings. Even if it is just a single list,
        #it's important to keep it as the same type
        data=text
        results=None
        if not isinstance(data,list):
            data=self.splitter.split(data)
        #print data
        if self.tagger is not None:
            parsed_data=[] #Later, this will link to the transformed data
            for dat in data:
                parse_str=" ".join([i[1] for i in self.tagger.tag(dat.split(" "))])
                parsed_data.append(parse_str)
            results=[]
            for i in range(len(data)):
                for res in self.pattern.finditer(parsed_data[i]):
                    num_spaces=parsed_data[i].count(" ",0,res.start()) #Start give us how many spaces to start ahead of, end how many we have to get
                    dat=data[i].split(" ")
                    #jump ahead num_spaces spaces
                    dat=dat[num_spaces:]
                    num_spaces=parsed_data[i].count(" ",res.start(),res.end())
                    dat=dat[:num_spaces+1]
                    if(len(dat)) > 0:
                        results.append(' '.join(dat))
                    
        else:
            #HERE we assume that we have a list that is already in the format that we require
            results=[]
            for item in data:
                for res in self.pattern.finditer(item):
                    results.append(res.group(0))
        return list(set(results))

class DependencySemantics:
    def __init__(self,parser,dep_types =['nmod']):
        self.pattern= dep_types
        self.parser = parser
        #self.parser=English()

    def getSentences(self,text=None):
        if text is not None:
            self.parsedData = self.parser(text)
        sents = []
        for span in self.parsedData.sents:
            # go from the start to the end of each span, returning each token in the sentence
            # combine each token using join()
            sent = ''.join(self.parsedData[i].string for i in range(span.start, span.end)).strip()
            sents.append(sent)
        return sents
        
    def getProperties(self,text=None):
        if text is not None:
            self.parsedData = self.parser(text)
        tokens = []
        counter = 0
        for token in self.parsedData:
            if token.dep_ in self.pattern:
                tokens.append((self.getPosition(counter),token))
            counter += 1

        return tokens

    def getPosition(self,tok_num):
        counter = 0
        for span in self.parsedData.sents:
            if tok_num >= span.start and tok_num <= span.end:
                #print token.orth_,self.parsedData[os:len(token)]
                return counter
            counter+=1

        return -1
