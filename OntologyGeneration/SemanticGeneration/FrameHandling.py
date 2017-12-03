from nltk.corpus import framenet as fn
from nltk.tokenize import RegexpTokenizer    
import re,sys,inspect  #Tells you the information for a module inspect.getmembers(module)
import parse
from ..CommonFunctions import *

    



def fillApplicable(obj_list):
    '''Creates the required arguments for applicability conditions (since we
    can get them, we might as well'''
    app_string=""
    counter=0
    for obj in obj_list:
        split_list=obj.split("=")
        if len(split_list)== 1:
            #In this case,we have required arguments, so we should make sure
            #they are appropriate and the objects exist
            #checkObjectCap is agent,action,position
            app_string+="\tif not isSet("+obj+") or not checkObjectCapability("+obj+",self.id,"+str(counter)+"):\n\t\treturn FAILURE\n"
        counter+=1
    app_string+="\treturn SUCCESS\n"
    return app_string

class FrameOntology:
    '''Finds frames from an action ontology, and attempts to connect 
    them to objects in the object ontology'''
    def __init__(self,database,parse_text="FnWnVerbMap.1.0.txt"):
        self.tokenizer=tokenizer=RegexpTokenizer(r'\w+')
        (verbnet,framenet)=parse.parse(parse_text)
        self.frame_dict=verbnet
        self.database=database

    ##Gets a frame from a synset
    def getFrameSynset(self,synset):
        try:
            if synset in self.frame_dict:
                #print synset,self.frame_dict[synset]
                frame=fn.frame(self.frame_dict[synset].capitalize())
                return frame
        except:
            pass
        return None

    ##Gets a frame from a wordnet node
    def getFrame(self,node):
        return self.getFrameSynset(node.getSynSet())

    ##Does a recursive parse on the synsets until the synset has no parent
    def getFrameRecursive(self,synset):
        frame=self.getFrameSynset(synset)
        if frame is None:
            hyper=synset.hypernyms()
            count=0
            if len(hyper) > 0:
                while frame is None and count < len(hyper):
                    frame=self.getFrameRecursive(hyper[count])
                    count+=1
        return frame

    ##returns the first frame by a verb lemma (i.e str+'v')
    def getFrameLemma(self,lemma):
        frame = fn.frames_by_lemma(lemma+'.v')
        if len(frame) > 0:
            return frame[0]
        return None
    ##Gets the participants (Functional Elements) of a frame
    def getParticipants(self,frame):
        fus=frame.FE
        core_elements=[]
        non_core_elements=[]
        for obj in fus.keys():
            if fus[obj].coreType == "Core":
                core_elements.append(fus[obj])
            else:
                non_core_elements.append(fus[obj])
        return (core_elements,non_core_elements)


    ##Gets the participants (Functional Elements) of a frame
    def getParticipantsMatch(self,frame,keywords):
        fus=frame.FE
        core_elements=[]
        non_core_elements=[]
        for obj in fus.keys():
            semType=fus[obj].semType
            #print obj.lower(),
            #print type(obj.lower())
            
            if obj.lower() in keywords or len(set(obj.lower().split("_")).intersection(keywords)) > 0  or self.__searchSemType(semType,keywords):
                #print "found",obj.lower()
                if fus[obj].coreType == "Core":
                    core_elements.append(fus[obj])
                else:
                    non_core_elements.append(fus[obj])
            #print obj.lower()
        return (core_elements,non_core_elements)
    ##Finds all the keywords that match a given FE
    def getKeywordMatch(self,FE,keywords):
        matched = []
        semType = FE.semType
        if FE.name.lower() in keywords:
            matched.append(FE.name.lower())
        else:
            spliter = FE.name.lower().split("_")
            found = False
            if len(spliter) > 1:
               for s in spliter:
                   if not found and s in keywords:
                        found=True
                        matched.append(s)
            for word in keywords:
                if not found and self.__searchSemType(semType,[word]):
                    matched.append(word)
        return matched

    def __searchSemType(self,sem,keywords):
        found=False
        if sem is not None:
            obj=[sem.name.lower()]
            for o in obj:
                if o in keywords:
                    return True
            sub_types=[i for i in sem.subTypes]
            while len(sub_types) > 0 and not found:
                sem=sub_types.pop(0)
                found=self.__searchSemType(sem,keywords)
        return found

    
    def chooseParticipationConstraints(self,frame,act_name):
        '''From a given grame, this allows a use to choose participation constrains
        by looking at the FE name and definition'''
        fus=frame.FE
        if len(fus) == 0:
            return [] #If the frame doesn't have functional entites, then why bother
        
        found_objs=[]
        functions=[self.getObject,self.getPartialObject]
        for obj in fus.keys():
            is_core=False
            if (fus[obj].coreType == "Core"):
                is_core=True
            obj_name=obj
            if not is_core:
                obj_name+="=-1"
            obj_id=-1
            counter=0
            obj_def=fus[obj].definition
            while obj_id < 0 and counter < len(functions):
                obj_id=functions[counter](obj)
                counter+=1
            if obj_id == -1:
                #Here we search along semTypes and their children
                semType=fus[obj].semType
                if semType is not None:
                    subtypes=[semType]
                    #BFS Queue
                    while len(subtypes) > 0 and obj_id < 0:
                        semType=subtypes.pop(0)
                        obj=semType.name
                        counter=0
                        while obj_id < 0 and counter < len(functions):
                            obj_id=functions[counter](obj)
                            counter+=1
                        subtypes.extend(semType.subTypes)
            
            found_objs.append((obj_name,obj_id,obj_def))
        
        print act_name
        print "Choose multiple participants with a comma (i.e. 2,5,6)"
        print "Input -1 to not use any participants"
        for i in range(len(found_objs)):
            print str(i)+")",found_objs[i][0],"-",found_objs[i][1],":",found_objs[i][2],'\n'
        selected_objs=raw_input("Selection:")
        selected_objs=selected_objs.split(",")
        selected_objs=[int(i.strip()) for i in selected_objs]
        return_objs=[]
        if selected_objs[0] != -1:
            for i in selected_objs:
                return_objs.append((found_objs[i][0],found_objs[i][1]))
        return return_objs
        
    def findParticipationConstraints(self,frame,functions):
        '''
        From a given frame, this determines participant constraints by
        examining functional entities. It also examines a functional entities
        using the semantic types
        @param frame The framenet frame to test
        @param functions The equality functions that are used to test functional entities
        @returns A tuple with two lists, a core list and non-core list. The core list is nessicary participants, and non-core list is optional participants
        '''
        fus=frame.FE
        if len(fus) == 0:
            return [] #If the frame doesn't have functional entites, then why bother
        found_objs=[]   
        for obj in fus.keys():
            is_core=False
            if (fus[obj].coreType == "Core"):
                is_core=True
            obj_name=obj
            if not is_core:
                obj_name+="=-1"
            obj_id=-1
            counter=0
            while obj_id < 0 and counter < len(functions):
                obj_id=functions[counter](obj)
                counter+=1
            if obj_id == -1:
                #Here we search along semTypes and their children
                semType=fus[obj].semType
                if semType is not None:
                    subtypes=[semType]
                    #BFS Queue
                    while len(subtypes) > 0 and obj_id < 0:
                        semType=subtypes.pop(0)
                        obj=semType.name
                        counter=0
                        #while obj_id < 0: and counter < len(functions):
                        obj_id=functions[counter](obj)
                            #counter+=1
                        subtypes.extend(semType.subTypes)
            if obj_id > 0:
                found_objs.append((obj_name,obj_id))
        #Finally, create two list, Core and non-core
        core_list=[i for i in found_objs if i[0].find("=") == -1]
        non_core =[i for i in found_objs if i[0].find("=") != -1]
        return (core_list,non_core)

def writeOutParFiles(file_dir,pars):
    '''Creates a par file for every found action, and places it inside the 
    directory'''
    par_types=("applicability_condition","preparatory_spec","execution_steps","culmination_condition")
    required_arguments=["self","agent"]#list for join
    other_args=""
    for par in pars:
        f=open(file_dir+"/"+par[2].capitalize()+".py","w")
        #First, we give some documentation on it
        if len(par) >3:
            f.write('#'.join(['']+par[3]));
        for func in par_types:
            if len(par[1]) > 0:
                func_string="def "+func+"("+",".join(required_arguments+[i[0] for i in par[1] if i[0].lower() not in required_arguments])+"):\n"
            else:
                func_string="def "+func+"("+",".join(required_arguments)+"):\n"
            if(func =="applicability_condition" and len(par[1]) >0):
                func_string+=fillApplicable([i[0] for i in par[1] if i[0].lower() not in required_arguments])#We can fill in the applicability condition
            elif(func == "culmination_condition"):
                func_string+="\tif finishedAction(self.id):\n\t\treturn SUCCESS\n\treturn INCOMPLETE\n\n"
            elif(func == "execution_steps"):
                exec_string="\treturn {'PRIMITIVE':('"+par[2]+"',{'agents':agent,'objects':"
                if len(par[1]) == 0:
                    exec_string+="None})}\n"
                else:
                    exec_string+="("+",".join([i[0].split("=")[0] for i in par[1]])+")})}\n"
                func_string+=exec_string+"\n"
            else:
                func_string+="\treturn SUCCESS\n\n"
            f.write(func_string)
        f.close()
