#
# high-level functionality to evaluate trainers and detectors
# Matz, July 2013
# last edit: November 2013
#
import random
random.seed()
import numpy
import easy
import util.misc as misc 
import cvac
import math
from operator import attrgetter, itemgetter

'''
The default callback used to count the positive and/or negative hits when building 
the confusion table.
'''
def defaultHitStrategy(origpur, foundLabels, foundMap, tres):
    numfound = len(foundLabels)
    if numfound==0:
        if origpur.ptype==cvac.PurposeType.POSITIVE:
            tres.fn += 1
        else:
            tres.tn += 1
        return tres
    foundPurposes = []
    '''
    Get one count each of each purpose found.  We use this to make sure that we
    only return a result for each purpose and no more.  If more than one result for each
    purpose is in the foundLabels, then only the first one is counted.
    '''
    for lbl in foundLabels:
        labelText = easy.getLabelText( lbl.lab, guess=False )
        if labelText in foundMap:
            foundPurpose = foundMap[labelText]
            if foundPurpose not in foundPurposes:
                foundPurposes.append(foundPurpose)
        else:
            print("warning: Label " + labelText + " not in foundMap can't compute evaluation.")
    for lbl in foundLabels:
        labelText = easy.getLabelText( lbl.lab, guess=False )
        if labelText in foundMap:
            foundPurpose = foundMap[labelText]
            '''We only want to count a purpose once
               so remove it from the foundPurposes list '''
            if foundPurpose in foundPurposes:
                foundPurposes.remove(foundPurpose)
                if origpur.ptype == cvac.PurposeType.POSITIVE:
                    if foundPurpose.ptype == cvac.PurposeType.POSITIVE:
                        tres.tp += 1
                    else:
                        tres.fn += 1
                else:
                    if foundPurpose.ptype == cvac.PurposeType.POSITIVE:
                        # This defaultHitStrategy counts every false positive
                        tres.fp += 1
                    else:
                        tres.tn += 1
    return tres
                            
                            
                   
    
class TestResult:
    def __init__(self, tp=0, fp=0, tn=0, fn=0):
        self.tp = tp;
        self.fp = fp;
        self.tn = tn;
        self.fn = fn;
        
    def __str__(self):
        desc = "{0} tp, {1} fp, {2} tn, {3} fn"\
           .format(self.tp, self.fp, self.tn, self.fn)
        return desc
   

def getRelativePath( label ):
    fspath = misc.getLabelableFilePath(label)
    return fspath.directory.relativePath + "/" + fspath.filename

def verifyFoundMap(foundMap):
    ''' Verify that the all the purposes in the found map are pos or neg '''
    for purpose in foundMap.itervalues():
        if purpose.ptype != cvac.PurposeType.POSITIVE \
           and purpose.ptype != cvac.PurposeType.NEGATIVE:
            print ("Not a negative or positive purpose found")
            return False
    return True

def getConfusionTable( results, foundMap, origMap=None, origSet=None, 
                       HitStrategy=defaultHitStrategy):
    '''Determine true and false positives and negatives based on
    the purpose of original and found labels.
    origMap maps the relative file path of every label to the assigned purpose.
    The origMap can be constructed from the original RunSet if it
    contained purposes.
    Returns TestResult, nores'''

    if not origMap and not origSet:
        raise RuntimeError("need either origMap or origSet")
    if not foundMap:
        raise RuntimeError("need a foundMap")
    if not verifyFoundMap(foundMap):
        raise RuntimeError("Invalid found map")
    if not origMap:
        origMap = {}
        for plist in origSet.purposedLists:
            assert( isinstance(plist, cvac.PurposedLabelableSeq) )
            for sample in plist.labeledArtifacts:
                if plist.pur.ptype != cvac.PurposeType.POSITIVE \
                     and plist.pur.ptype != cvac.PurposeType.NEGATIVE:
                    raise RuntimeError("Non pos or neg purpose in runset")
                origMap[ getRelativePath(sample) ] = plist.pur
    # compute the number of samples in the origSet that was not evaluated
    nores = 0
    if origSet:
        origSize = len( asList( origSet ) )
        nores = origSize - len(results)
    else:
        print("warning: Not able to determine samples not evaluated")
    tres = TestResult()
    for res in results:
        origpur = origMap[ getRelativePath(res.original) ]
        '''
        We can define our strategy on how to count hits.  The default
        strategy provided is to count all the false positives and a true positive
        only for each purpose found.  So if the same object is found 3 times it is only
        counted once, but if 2 different objects are found, they both are counted.
        '''
        tres = HitStrategy(origpur, res.foundLabels, foundMap, tres)
            
    print('{0}, nores: {1}'.format(tres, nores))
       
    return tres, nores

def splitRunSet( runset_pos, runset_neg, fold, chunksize, evalsize, rndidx ):
    '''Take parts of runset_pos and runset_neg and re-combine into
    a training set and an evaluation set.  For use by crossValidate().
    '''
    num_items = ( len(runset_pos), len(runset_neg) )
    evalidx_pos  = range( fold*chunksize[0], fold*chunksize[0]+evalsize[0] )
    evalidx_neg  = range( fold*chunksize[1], fold*chunksize[1]+evalsize[1] )
    trainidx_pos = range( 0, fold*chunksize[0] ) + range( fold*chunksize[0]+evalsize[0], num_items[0] )
    trainidx_neg = range( 0, fold*chunksize[1] ) + range( fold*chunksize[1]+evalsize[1], num_items[1] )
    # The following line selects those elements from runset_pos
    # that correspond to the randomized indices for the current
    # evaluation chunk.  Think of this, conceptually:
    # evalset_pos  = runset_pos[ rndidx[0][evalidx_pos] ]
    # Subsequent lines: equivalently, for runset_neg, and trainset pos/neg
    evalset_pos  = list( runset_pos[i] for i in list( rndidx[0][j] for j in evalidx_pos) )
    evalset_neg  = list( runset_neg[i] for i in list( rndidx[1][j] for j in evalidx_neg) )
    trainset_pos = list( runset_pos[i] for i in list( rndidx[0][j] for j in trainidx_pos) )
    trainset_neg = list( runset_neg[i] for i in list( rndidx[1][j] for j in trainidx_neg) )

    # create a RunSet with proper purposes
    trainset = cvac.RunSet()
    trainset.purposedLists = (cvac.PurposedLabelableSeq(easy.getPurpose("pos"), trainset_pos),
                              cvac.PurposedLabelableSeq(easy.getPurpose("neg"), trainset_neg))
    evalset  = cvac.RunSet()
    evalset.purposedLists = (cvac.PurposedLabelableSeq(easy.getPurpose("pos"), evalset_pos),
                             cvac.PurposedLabelableSeq(easy.getPurpose("neg"), evalset_neg))
    return trainset, evalset

def asList( runset, purpose=None ):
    '''You can pass in an actual cvac.RunSet or a dictionary with
    the runset and a classmap, as returned by createRunSet.'''
    if type(runset) is dict and not runset['runset'] is None\
        and isinstance(runset['runset'], cvac.RunSet):
        runset = runset['runset']
    if not runset or not isinstance(runset, cvac.RunSet) or not runset.purposedLists:
        raise RuntimeError("no proper runset")
    if isinstance(purpose, str):
        purpose = easy.getPurpose( purpose )

    rsList = []
    for plist in runset.purposedLists:
        if purpose and not plist.pur==purpose:
            # not interested in this purpose
            continue
        if isinstance(plist, cvac.PurposedDirectory):
            print("warning: runset contains directory; will treat as one for folds")
        elif isinstance(plist, cvac.PurposedLabelableSeq):
            rsList = rsList + plist.labeledArtifacts
        else:
            raise RuntimeError("unexpected plist type "+type(plist))
    return rsList

class EvaluationResult:
    def __init__( self, folds, testResult, nores, detail=None, name=None ):
        self.folds = folds
        self.res = testResult
        self.nores = nores
        self.detail = detail
        self.name = name
        '''
        recall is sensitivity or True positive rate (TP/(TP + FN).    
        trueNegRate is specificity or True negative rate (TN/FP + TN).  
        '''
        numpos = self.res.tp + self.res.fn
        numneg = self.res.fp + self.res.tn
    
        if numpos != 0:
            self.recall = self.res.tp/float(numpos)
        else:
            self.recall = 0
        if numneg != 0:
            self.trueNegRate = self.res.tn/float(numneg)
        else:
            self.trueNegRate = 0
        if self.res.tp > 0 and self.res.tn > 0:
            # calculate combined recall/trueNegRate score:
            self.score = (self.recall + self.trueNegRate)/2.0
        elif self.res.tp > 0:
            self.score = self.recall
        else:
            self.score = self.trueNegRate
        # add in to the score no result counts
        allSam = self.res.tp + self.res.tn + \
                  self.res.fp + self.res.fn + self.nores;
        resfactor = (allSam - nores) / float(allSam)
        self.score = self.score * resfactor;

    def __str__(self):
        
        if self.res.tp != 0  and self.res.tn != 0:
            desc = "{0:5.2f}  score, {1:5.2f}% recall, {2:5.2f}% 1-FPR " \
                "({3} tp, {4} fp, {5} tn, {6} fn, {7} nores)" \
                .format( self.score*100.0, self.recall*100.0, self.trueNegRate*100.0,
                         self.res.tp, self.res.fp, 
                         self.res.tn, self.res.fn, self.nores )
        elif self.res.tp == 0:
            # Don't show recall since its not valid with no tp
            desc = "{0:5.2f}  score,   -   recall, {2:5.2f}% 1-FPR " \
                "({3} tp, {4} fp, {5} tn, {6} fn, {7} nores)" \
                .format( self.score*100.0, self.trueNegRate*100.0,
                         self.res.tp, self.res.fp, 
                         self.res.tn, self.res.fn, self.nores )
        else:
            # Don't show specificity since its not valid with no tn
            desc = "{0:5.2f}  score, {1:5.2f}% recall,   -   1 - FPR  " \
                "({3} tp, {4} fp, {5} tn, {6} fn, {7} nores)" \
                .format( self.score*100.0, self.recall*100.0, 
                         self.res.tp, self.res.fp, 
                         self.res.tn, self.res.fn, self.nores )
        if self.name:
            return self.name + ": " + desc
        return desc

        
def crossValidate( contender, runset, folds=10, printVerbose=False ):
    '''Returns summary statistics tp, fp, tn, fn, recall, trueNegRate,
    and a detailed matrix of results with one row for
    each fold, and one column each for true positive, false
    positive, true negative, and false negative counts'''

    # sanity checks:
    # only positive and negative purposes,
    # count number of entries for each purpose
    runset_pos = asList( runset, purpose="pos" )
    runset_neg = asList( runset, purpose="neg" )
    num_items = ( len(runset_pos), len(runset_neg) )
    # check that there are no other purposes
    all_items = len( asList( runset ) )
    if sum(num_items)!=all_items:
        raise RuntimeError("crossValidate can only handle Positive and Negative purposes")
    if min(num_items)<2:
        raise RuntimeError("need more than 1 labeled item per purpose to cross validate")

    # make sure there are enough items for xval to make sense
    if folds>min(num_items):
        print("warning: cannot do "+folds+"-fold validation with only "+str(num_items)+" labeled items")
        folds = min(num_items)

    # calculate the size of the training and evaluation sets.
    # if the number of labeled items in the runset divided
    # by the number of folds isn't an even
    # division, use more items for the evaluation
    chunksize = (int(math.floor( num_items[0]/folds )), int(math.floor( num_items[1]/folds )))
    trainsize = (chunksize[0] * (folds-1), chunksize[1] * (folds-1))
    evalsize  = (num_items[0]-trainsize[0], num_items[1]-trainsize[1])
    print( "Will perform a {0}-fold cross-validation with {1} training samples and "
           "{2} evaluation samples".format( folds, trainsize, evalsize ) )

    # randomize the order of the elements in the runset, once and for all folds
    rndidx = ( range( num_items[0] ), range( num_items[1] ) )
    random.shuffle( rndidx[0] ) # shuffles items in place
    random.shuffle( rndidx[1] ) # shuffles items in place

    #confusionTables = numpy.empty( [folds, 5], dtype=int )
    confusionTables = []
    
    for fold in range( folds ):
        # split the runset
        trainset, evalset = splitRunSet( runset_pos, runset_neg, fold, chunksize, evalsize, rndidx )
        print( "-------- fold number {0} --------".format(fold) )

        # training
        print( "---- training:" )
        easy.printRunSetInfo( trainset, printArtifacts=printVerbose )
        trainer = contender.getTrainer()
        
        model = easy.train( trainer, trainset,
                            trainerProperties=contender.trainerProps)

        # detection
        print( "---- evaluation:" )
        easy.printRunSetInfo( evalset, printArtifacts=printVerbose )
        detector = contender.getDetector()
        detections = easy.detect( detector, model, evalset,
                                  detectorProperties=contender.detectorProps )
        confusionTables.append( \
            getConfusionTable( detections, origSet=evalset, foundMap=contender.foundMap ))

    # calculate statistics of our tuple TestResult,nores
    
    sumTestResult = TestResult()
    sumNoRes = 0;
    for entry in confusionTables:
        sumTestResult.tp += entry[0].tp
        sumTestResult.tn += entry[0].tn
        sumTestResult.fp += entry[0].fp
        sumTestResult.fn += entry[0].fn
        sumNoRes += entry[1]
    r = EvaluationResult(folds, sumTestResult, sumNoRes, detail=None, name=contender.name)
    return r

def evaluate( contender, runset, printVerbose=False ):
    if type(runset) is dict and not runset['runset'] is None\
        and isinstance(runset['runset'], cvac.RunSet):
        runset = runset['runset']
    if not runset or not isinstance(runset, cvac.RunSet) or not runset.purposedLists:
        raise RuntimeError("no proper runset")
    evalset = runset

    print( "---- evaluation:" )
    easy.printRunSetInfo( evalset, printArtifacts=printVerbose )
    detector = contender.getDetector()
    detections = easy.detect( detector, contender.detectorData, evalset,
                              detectorProperties=contender.detectorProps )
    ct = getConfusionTable( detections, origSet=evalset, foundMap=contender.foundMap )

    # create result structure
    r = EvaluationResult( 0, ct[0], nores=ct[1],
                          detail=None, name=contender.name )
    return r


class Contender:
    '''Ultimately a detector, this product can be built from
    a trainer or be a pre-defined detector.  Any combination that
    that can be trained into a detector is valid.
    Once a trainer is specified, it is assumed that this contender
    needs to be trained, irrespective of whether detectorData are
    present or not.
    '''
    def __init__( self, name ):
        self.name = name
        self.trainer = None
        self.trainerString = None
        self.trainerProps = None
        self.detector = None
        self.detectorString = None
        self.detectorData = None
        self.detectorProps = None
        self.foundMap = None

    def hasTrainer( self ):
        if self.trainer or self.trainerString:
            return True
        return False

    def hasDetector( self ):
        if self.detector or self.detectorString:
            return True
        return False

    def isSufficientlyConfigured( self ):
        if not self.foundMap:
            # need to correlate the labels that the detector will report
            # to purposes such as "positive" or "negative"
            return False
        if not self.hasDetector():
            return False
        if self.hasTrainer():
            # we can produce a trainedModel (detectorData)
            return True
        # warn if no trainer and no detectorData because this might
        # cause a failure after training only, but return true
        if not self.detectorData:
            print( "Warning: contender has no trainer and no detectorData" )
        return True

    def getTrainer( self ):
        if not self.trainer:
            self.trainer = easy.getTrainer( self.trainerString )
        return self.trainer

    def getDetector( self ):
        if not self.detector:
            self.detector = easy.getDetector( self.detectorString )
        return self.detector

    def getDetectorProps( self ):
        if not self.detectorProps:
            self.detectorProps = easy.getDetectorProperties( self.getDetector() )
        return self.detectorProps

def joust( contenders, runset, method='crossvalidate', folds=10, verbose=True ):
    '''evaluate the contenders on the runset, possibly training
    and evaluating with n-fold cross-validation or another method.
    The contenders parameter is a list of detectors (or
    trainer-detector tuples) that are to be evaluated.'''

    # check arguments
    if not method=='crossvalidate':
        raise RuntimeError( 'method ' + method + ' unknown.' )
    for c in contenders:
        if not c.isSufficientlyConfigured():
            raise RuntimeError('This contender needs more configuration: ' + c.name)

    results = []
    for c in contenders:
        if verbose:
            print("======== evaluating contender '{0}' ========".format( c.name ) )
        #try:
            if c.hasTrainer():
                evalres = crossValidate( c, runset, folds )
            else:
                evalres = evaluate( c, runset )
            results.append( evalres )

            if verbose:
                print evalres
                print evalres.detail
       # except Exception as exc:
           # print("error encountered, evaluation aborted: " + str(exc))

    if verbose:
        print("======== done! ========")
    # sort the results by "score"
    originalResults =  results
    sortedResults = sorted( results, key=lambda result: result.score, reverse=True )
    return sortedResults,originalResults

def printEvaluationResults(results):
    print('name        ||  score |  recall | 1 - FPR ||  tp  |  fp  |  tn  |  fn  | nores')
    print('-------------------------------------------------------------------')
    for result in results:
        # need 6.2 instead of 5.2 to allow for 100.0%
        if result.res.tp != 0 and result.res.tn != 0:
            desc = "{0:6.2f}  | {1:6.2f}% | {2:6.2f}% || " \
                "{3:4d} | {4:4d} | {5:4d} | {6:4d} | {7:4d}" \
                .format( result.score*100.0, result.recall*100.0, result.trueNegRate*100.0,
                         result.res.tp, result.res.fp, result.res.tn, result.res.fn, result.nores )
        elif result.res.tp == 0:
            desc = "{0:6.2f}  |    -    | {1:6.2f}% || " \
                "{2:4d} | {3:4d} | {4:4d} | {5:4d} | {6:4d}" \
                .format( result.score*100.0,  result.trueNegRate*100.0,
                         result.res.tp, result.res.fp, result.res.tn, result.res.fn, result.nores )
        else:
            desc = "{0:6.2f}  | {1:6.2f}% |    -    || " \
                "{2:4d} | {3:4d} | {4:4d} | {5:4d} | {6:4d}" \
                .format( result.score*100.0, result.recall*100.0, 
                         result.res.tp, result.res.fp, result.res.tn, result.res.fn, result.nores )
        if result.name:
            if len(result.name) > 12:
                print (result.name[0:11] + '.' + '||'+ desc)  
            else: 
                print (result.name.ljust(12) + "||" + desc)
                
