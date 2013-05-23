#
# A demo for the Easy Computer Vision library.
#

# before interpreting this file, make sure this is set:
# export PYTHONPATH="/opt/Ice-3.4.2/python:./src/easy"
import cvac
import easy


#
# First, a teaser for detection:
#
# TODO: doesn't work yet because the image file argument doesn't get turned into a RunSet yet.
detector = easy.getDetector( "bowTest:default -p 10004" )
results = easy.detect( detector, "detectors/bowUSKOCA.zip", "testImg/TestCaFlag.jpg" )
easy.printResults( results )

#
# Second, a quick way to train a detector.  The resulting model
# can be used in place of the detector above.
#
# TODO: doesn't work yet because a) getDataSet assumes a CorpusServer and Corpus,
#       and b) createRunSet expects entire categories, not LabelLists
categories = easy.getDataSet( "Caltech101.properties" )
runset = easy.createRunSet( categories["car_side"] )
trainer = easy.getTrainer( "bowTrain:default -p 10003" )
carSideModel = easy.train( trainer, runset )

#
# Third, a slower walk-through of functionality that digs a bit deeper.  All
# following steps are part of that.
# Obtain a set of labeled data from a Corpus,
# print dataset information about this corpus
#
cs = easy.getCorpusServer("CorpusServer:default -p 10011")
#corpus = easy.openCorpus( cs, "corpus/CvacCorpusTest.properties" )
#corpus = easy.openCorpus( cs, "corporate_logos" );
corpus = easy.openCorpus( cs, "trainImg" );
categories, lablist = easy.getDataSet( cs, corpus )
print 'Obtained {0} labeled artifact{1} from corpus "{2}":'.format(
    len(lablist), ("s","")[len(lablist)==1], corpus.name );
easy.printCategoryInfo( categories )

#
# add all samples from corpus to a RunSet,
# also obtain a mapping from class ID to label name
#
res = easy.createRunSet( categories )
runset = res['runset']
classmap = res['classmap']

#
# Make sure all files in the RunSet are available on the remote site;
# it is the client's responsibility to upload them if not.
#
fileserver = easy.getFileServer( "FileService:default -p 10110" )
easy.putAllFiles( fileserver, runset )

#
# Connect to a trainer service, train on the RunSet
#
trainer = easy.getTrainer( "bowTrain:default -p 10003" )
trainedModel = easy.train( trainer, runset )
print "Training model stored in file: " + easy.getFSPath( trainedModel.file )

#
# Connect to a detector service,
# test on the training RunSet for validation purposes;
# The detect call takes the detector, the trained model, the
# runset, and a mapping from purpose to label name
#
detector = easy.getDetector( "bowTest:default -p 10004" )
results = easy.detect( detector, trainedModel, runset, classmap )
easy.printResults( results )

quit()
