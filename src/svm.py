# the actual classifier script for predicting a sentiment using SVM
from __future__ import division
from sklearn import svm
from sklearn import cross_validation
from sklearn import preprocessing as pr

from sklearn.feature_selection import SelectKBest, f_classif # for features selection


import numpy as np
import nltk # for pos tags 

import features
import polarity
import ngramGenerator
import preprocessing


KERNEL_FUNCTION='linear'
C_PARAMETER=0.6

print "Initializing dictionnaries"
stopWords = preprocessing.getStopWordList('../resources/stopWords.txt')
slangs = preprocessing.loadSlangs('../resources/internetSlangs.txt')
#sentiWordnet=polarity.loadSentiFull('../resources/sentiWordnetBig.csv')
sentiWordnet=polarity.loadSentiWordnet('../resources/sentiWordnetBig.csv')
emoticonDict=features.createEmoticonDictionary("../resources/emoticon.txt")

print "Bulding Bag of words ..."
positive=ngramGenerator.mostFreqList('../data/used/positive_processed.csv',3000)
negative=ngramGenerator.mostFreqList('../data/used/negative_processed.csv',3000)
neutral=ngramGenerator.mostFreqList('../data/used/neutral_processed.csv',3000)


for w in positive:
    if w in negative+neutral : 
        positive.remove(w)

for w in negative:
    if w in positive+neutral : 
        negative.remove(w)

for w in neutral:
    if w in negative+positive : 
        neutral.remove(w)



#print len(total)
 
def mapTweet(tweet,sentiWordnet,emoDict,positive,negative,neutral,slangs):
    out=[]
    line=preprocessing.processTweet(tweet,stopWords,slangs)
   
    p=polarity.posPolarity(line,sentiWordnet)
    out.extend([p[0],p[1],p[2]/2]) # aggregate polsarity pos - negative
#    out.extend(p[7:]) # frequencies of pos 
#    out.append(float(features.emoticonScore(line,emoDict))) # emo aggregate score be careful to modify weights
#    out.append(float(len(features.hashtagWords(line))/40)) # number of hashtagged words
#    out.append(float(len(line)/140)) # for the length
#    out.append(float(features.upperCase(line))) # uppercase existence : 0 or 1
#    out.append(float(features.exclamationTest(line)))
#    out.append(float(line.count("!")/140))
#    out.append(float((features.questionTest(line))))
#    out.append(float(line.count('?')/140))
#    out.append(float(features.freqCapital(line)))
    u=features.scoreUnigram(tweet,positive,negative,neutral)
    out.extend(u)
    return out

# load matrix
def loadMatrix(posfilename,neufilename,negfilename,poslabel,neulabel,neglabel):
    vectors=[]
    labels=[]
    f=open(posfilename,'r')
    kpos=0
    kneg=0
    kneu=0
    line=f.readline()
    while line:
        
        try:
            kpos+=1
            z=mapTweet(line,sentiWordnet,emoticonDict,positive,negative,neutral,slangs)
            vectors.append(z)
            labels.append(float(poslabel))
        except:
            None
        line=f.readline()
        print str(kpos)+"positive lines loaded : "+str(z)
    f.close()
    
    f=open(neufilename,'r')
    line=f.readline()
    while line:
        try:
            kneu=kneu+1
            z=mapTweet(line,sentiWordnet,emoticonDict,positive,negative,neutral,slangs)
            vectors.append(z)
            labels.append(float(neulabel))
        except:
            None
        line=f.readline()
        print str(kneu)+"neutral lines loaded : "+str(z)
    f.close()
    
    f=open(negfilename,'r')
    line=f.readline()
    while line:
        try:
            kneg=kneg+1
            z=mapTweet(line,sentiWordnet,emoticonDict,positive,negative,neutral,slangs)
            vectors.append(z)
            labels.append(float(neglabel))
        except:
            None
        line=f.readline()
        print str(kneg)+"negative lines loaded : "+str(z)
    f.close()
    return vectors,labels


# map tweet into a vector 
def trainModel(X,Y,knel,c): # relaxation parameter
    clf=svm.SVC(kernel=knel) # linear, poly, rbf, sigmoid, precomputed , see doc
    clf.fit(X,Y)
    return clf

def predict(tweet,model): # test a tweet against a built model 
    z=mapTweet(tweet,sentiWordnet,emoticonDict,positive,negative,neutral,slangs) # mapping
    return model.predict([z]).tolist() # transform nympy array to list 

def predictFile(filename,svm_model): # function to load test file in the csv format : sentiment,tweet 
    f=open(filename,'r')
    fo=open(filename+".result",'w')
    line=f.readline()
    while line:
        tweet=line[:-1]

        nl=predict(tweet,svm_model)
    
        fo.write(r'"'+str(nl)+r'","'+tweet+r'"\n')
        line=f.readline()
   
    f.close()
    fo.close()
    print "Tweets are classified . The result is in "+filename+".result"

def loadTest(filename): # function to load test file in the csv format : sentiment,tweet 
    f=open(filename,'r')
    line=f.readline()
    labels=[]
    vectors=[]
    while line:
        l=line[:-1].split(r'","')
        s=float(l[0][1:])
        tweet=l[5][:-1]

        z=mapTweet(tweet,sentiWordnet,emoticonDict,positive,negative,neutral,slangs)
        vectors.append(z)
        labels.append(s)
        line=f.readline()
#        print str(kneg)+"negative lines loaded"
    f.close()
    return vectors,labels

def batchPredict(vectors,model): # the output is a numpy array of labels
    return model.predict(vectors).tolist()

def testModel(vectors,labels,model): # for a given set of labelled vectors calculate model labels and give accuract
    a=0 # wrong classified vectors
    newLabels=model.predict(vectors).tolist()
    mispos=0
    misneg=0
    misneu=0
    for i in range(0,len(newLabels)):
        if(labels[i] == 4.0 and newLabels[i] != 4.0):
            mispos+=1
        if(labels[i] == 2.0 and newLabels[i] != 2.0):
            misneu+=1
        if(labels[i] == 0.0 and newLabels[i] != 0.0):
            misneg+=1

        if newLabels[i]!=labels[i]:
            a=a+1
    print "mispos = %f, misneu = %f, misneg = %f" % (mispos,misneu,misneg)
    if len(labels)==0:
        return 0.0
    else:
        return 1-a/len(labels) # from future import dividion



# loading training data
print "Loading training data"
X,Y=loadMatrix('../data/used/positive2.csv','../data/used/neutral2.csv','../data/used/negative2.csv','4','2','0')
#X,Y=loadMatrix('../data/small_positive_processed.csv','../data/small_neutral_processed.csv','../data/small_negative_processed.csv','4','2','0')

# 5 fold cross validation
x=np.array(X)
y=np.array(Y)
KERNEL_FUNCTIONS=['linear','poly','rbf']
C=[0.1*i for i in range(1,11)]
ACC=0.0
iter=0

for knel in KERNEL_FUNCTIONS:
    for c in C:

        clf = svm.SVC(kernel=KERNEL_FUNCTION, C=c)
        scores = cross_validation.cross_val_score(clf, x, y, cv=5)
        if (scores.mean() > ACC):
            ACC=scores.mean()
            KERNEL_FUNCTION=knel
            C_PARAMETER=c
        iter=iter+1
        print "iteration "+str(iter)+" : c parameter : "+str(c)+", kernel : "+str(knel)
        #print scores # the precision for five iterations
        print("Accuracy of the model using 5 fold cross validation : %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))# Actual testing 
print "best C : "+str(C_PARAMETER)
print "best knel : "+KERNEL_FUNCTION


print "Training model with optimized parameters"
MODEL=trainModel(X,Y,KERNEL_FUNCTION,C_PARAMETER) 
print "Training done !"
 

# uncomment to classify test dataset 
print "Loading test data..."
V,L=loadTest('../data/test_dataset.csv')
#V,L=loadTest('../data/small_test_dataset.csv')

print "Classification done : Performance over test dataset : "+str(testModel(V,L,MODEL))

user_input=raw_input("Write a tweet to test or a file path for bulk classification with svm model. press q to quit\n")
while user_input!='q':
    try:
        predictFile(user_input,MODEL)
    except:
        print "sentiment : "+str(predict(user_input,MODEL))
        user_input=raw_input("Write a tweet to test or a file path for bulk classification . press q to quit\n")

# the end !
