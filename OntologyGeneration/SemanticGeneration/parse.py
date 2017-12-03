from nltk.corpus import wordnet

def parse(file):
    framedict = {}
    verbdict = {}
    f = open(file, 'r+')
    for line in f:
        x = line.strip().split(" ")
        for key in range(2,len(x)):
            try:
                synset = wordnet.lemma_from_key(x[key]).synset()
            except:
                #print x,key
                pass
            #print synset
            framedict[synset] = x[0]
            verbdict[synset] = x[1]
    #print framedict
    #print verbdict
    return (framedict,verbdict)

if __name__ =="__main__":
    parse('FnWnVerbMap.1.0.txt')
