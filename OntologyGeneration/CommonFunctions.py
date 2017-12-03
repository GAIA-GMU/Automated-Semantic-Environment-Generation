###############################################################################
##CommonFunctions.py
##Author: J. Timothy Balint
##Last Modified: 8-4-2017
##
##Holds commonly used functions. Mainly used to transform words into WordNet format and into PAR format
##############################################################################
import re

##This function transforms a word into something that is parseable by wordnet
#@param obj A string containing the word to be broken up
#@returns a string of form this_is_an_example
def transformToWordNetFormat(obj):
    #We first see if the string is space delimeted
    obj = obj.strip()
    new_obj=obj.split(" ")
    if len(new_obj) == 1:
        new_obj=re.findall("[A-Z][^A-Z]*",obj)
        if len(new_obj) == 0:
            new_obj = obj.split(" ")
    return '_'.join([i.lower() for i in new_obj])

##Removes numbers from the word, so "Pilliar1" just becomes pillar
#@param word A string containing the word to be tranformed
#@returns A cleaned up word
def removeAllEndNumbers(word):
    m=re.search("\d+",word)
    if m is not None:
        return word[:m.start()]
    return word


##Transforms from "  Physical  object " to "physical_object". Useful for combining multiple words into one
#@param obj A string containing the word to be tranformed
#@returns A string in Capitalized And Spaces Format
def cleanToWordNetFormat(obj):
    new_obj=obj.strip().split(" ")
    return '_'.join([i.lower() for i in new_obj])
    

##Takes a wordnet formated word and transforms it into a PAR compatable word (CamelCase)
#@param obj A string containing the word to be tranformed
#@returns A string in CamelCase Format
def transformToPARFormat(obj):
        return "".join([i.capitalize() for i in obj.split("_")])

##Takes a wordnet formated word and transforms it (Capitalized And Spaces)
#@param obj A string containing the word to be tranformed
#@returns A string in Capitalized And Spaces Format
def transformToSpaceFormat(obj):
        return " ".join([i.capitalize() for i in obj.split("_")])

##We take a WordNet format word and turn it into a compound object word
#@param obj A string containing the word to be tranformed
#@returns A string in Capitalized And Spaces Format
def compoundWord(word):
    return ''.join([i.lower() for i in word.split('_')])

##This prints out the statistics of the generated list. We define the total as the number of correct answers because we shouldn't be generating any final answers not in the list
#@param provided_answers A dictionary of the answers, that relates input=>output
#@param correct_answers A dictionary of the correct answers that relates input=>output
#@return A dictionary that provides Correct, Missed, and False Hit percentages
def printStats(provided_answers,correct_answers):
    correct=[]
    missed=[]
    false_hits=[]
    incorrect=[]
    for ans in provided_answers:
        if ans in correct_answers:
            if correct_answers[ans] is None:
                if provided_answers[ans] is None:
                    correct.append(ans)
                else:
                    false_hits.append(ans)
            elif provided_answers[ans] is None:
                if correct_answers[ans] is None:
                    correct.append(ans)
                else:
                    missed.append(ans)
            else:
                if isinstance(correct_answers[ans],tuple):
                    if provided_answers[ans] in correct_answers[ans]:
                        correct.append(ans)
                    else:
                        incorrect.append(ans)
                else:
                    if provided_answers[ans] == correct_answers[ans]:
                        correct.append(ans)
                    else:
                        incorrect.append(ans)
            
    correct=len(correct)
    print "Found",correct,"out of",len(correct_answers)
    #missed=len([ans for ans in correct_answers if ans not in provided_answers or provided_answers[ans] is None and correct_answers[ans] is not None])
    #false_hits=len([ans for ans in correct_answers if correct_answers[ans] is None and provided_answers[ans] is not None])
    for ans in incorrect:
        if ans in correct_answers:
            print ans,":",provided_answers[ans],"=/=",correct_answers[ans]
    #    else:
    #        print ans,"not in correct answers"
    return {"Correct":float(correct)/float(len(correct_answers)),"Missed":float(len(missed))/float(len(correct_answers)),"False Hits":float(len(false_hits))/float(len(correct_answers))}


        
