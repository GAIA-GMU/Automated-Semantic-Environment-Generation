from FrameHandling import FrameOntology
from FrameHandling import writeOutParFiles
from ..DataStructures import WordNetNode
from SemanticPatternFind import PatternSemantics
from SemanticPatternFind import DependencySemantics

##Determines the frame recursively from the WNN
#@param node the WordNetNode
def propertyResolve(node):
        if node is False:
                return False
        frame=sem.getFrameRecursive(node.getSynSet())
        if frame is not None:
                return frame
        return False

##Determines Non-Interaction Function Information (NIFI) and roles to actions based on Balint and Allbeck 2017
#@param actions The action set as a dictionary, where each action has a list of WordNetNodes
#@param adverbs The set of adverb keywords to look for
#@param objects The set of object keywords (and adjectives if you are doing the full ALET) to match roles on
#@returns None, (NIFI,Roles) are set as properties of the Node
def ALET(actions,adverbs,objects):
        #Clear out our previous measurements
        for action in actions:
                if actions[action] is not False:
                        for act in actions[action]:
                                act.setProperties([])
        for action in actions:
                if actions[action] is not False: #Make sure we have a frame that we are working with
                        for act in actions[action]:
                                frame = propertyResolve(act) #Get the frame for the node
                                if frame is not False:
                                    #Should rename these because they are the adverbs and not the adjectives
                                    adj_matches = sem.getParticipantsMatch(frame,adverbs)
                                    adj_matches = set([m.name.lower() for m in adj_matches[0]+adj_matches[1]])
                                    matches = sem.getParticipantsMatch(frame,objects)
                                    matches = set([m.name.lower() for m in matches[0]+matches[1] if m.name.lower() not in adj_matches])
                                    act.setProperties((adj_matches,matches))



