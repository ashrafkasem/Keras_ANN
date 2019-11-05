#!/usr/bin/env python
'''
DESCRIPTION:
Keras is a modular, powerful and intuitive open-source Deep Learning library built on Theano and TensorFlow. Thanks to its minimalist, user-friendly interface, it has become one of the most popular packages to build, train and test neural networks. This script provides an interface for conducting deep learning studies in python with Keras. The step included are:
1. Load Data.
2. Define Keras Model.
3. Compile Keras Model.
4. Fit Keras Model.
5. Evaluate Keras Model.
6. Tie It All Together.
7. Make Predictions


USAGE:
./sequential.py [opts]


EXAMPLES:
./sequential.py --test --activation relu -s png,pdf,root,C
./sequential.py --test --activation relu,relu,sigmoid --neurons 36,19,1 -s pdf
./sequential.py --activation relu,relu,relu,relu,sigmoid --neurons 36,35,19,19,1 --epochs 10000 --batchSize 50000 -s pdf


LAST USED:
./sequential.py --activation relu,relu,sigmoid --neurons 36,19,1 --epochs 10000 --batchSize 50000 -s pdf --log


GITHUB:
https://github.com/skonstantinou/Keras_ANN/
https://github.com/attikis/Keras_ANN


URL:
https://machinelearningmastery.com/tutorial-first-neural-network-python-keras/
https://keras.io/activations/
https://keras.io/getting-started/
https://keras.io/getting-started/faq/#what-does-sample-batch-epoch-mean
https://indico.cern.ch/event/749214/attachments/1754601/2844298/CERN_TH_Seminar_Nov2018.pdf#search=keras%20AND%20StartDate%3E%3D2018%2D10%2D01
https://www.indico.shef.ac.uk/event/11/contributions/338/attachments/281/319/rootTutorialWeek5_markhod_2018.pdf
https://indico.cern.ch/event/683620/timetable/#20190512.detailed
https://cds.cern.ch/record/2157570

'''
#================================================================================================ 
# Imports
#================================================================================================ 
print "=== Importing KERAS"
import keras
import uproot
import numpy
import pandas
import ROOT
import array
import os
import math
import json
import random as rn
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.externals import joblib

import plot
import func
import tdrstyle

import sys
import time
from datetime import datetime 
from optparse import OptionParser
import getpass
import socket

#================================================================================================
# Variable definition
#================================================================================================
# https://en.wikipedia.org/wiki/ANSI_escape_code#Colors  
ss = "\033[92m"
ns = "\033[0;0m"
ts = "\033[0;35m"   
hs = "\033[1;34m"
ls = "\033[0;33m"
es = "\033[1;31m"
cs = "\033[0;44m\033[1;37m"

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' #Disable AVX/FMA Warning

#================================================================================================ 
# Function Definition
#================================================================================================ 
def Print(msg, printHeader=False):
    fName = __file__.split("/")[-1]
    if printHeader==True:
        print "=== ", fName
        print "\t", msg
    else:
        print "\t", msg
    return

def Verbose(msg, printHeader=True, verbose=False):
    if not opts.verbose:
        return
    Print(msg, printHeader)
    return


def main(opts): 

    # Save start time (epoch seconds)
    tStart = time.time()
    Verbose("Started @ " + str(tStart), True)

    # Do not display canvases
    ROOT.gROOT.SetBatch(ROOT.kTRUE)

    # Disable screen output info
    ROOT.gROOT.ProcessLine( "gErrorIgnoreLevel = 1001;")

    style = tdrstyle.TDRStyle() 
    style.setOptStat(False) 
    style.setGridX(opts.gridX)
    style.setGridY(opts.gridY)

    # Open the ROOT file
    ROOT.TFile.Open(opts.rootFileName)

    if opts.test:
        opts.epochs    = 10
        opts.batchSize = 5000

    # Setting the seed for numpy-generated random numbers
    numpy.random.seed(opts.rndSeed)

    # Setting the seed for python random numbers
    rn.seed(opts.rndSeed)

    # Setting the graph-level random seed.
    tf.set_random_seed(opts.rndSeed)

    # Open the signal and background TTrees with uproot (uproot allows one to read ROOT data, in python, without using ROOT)
    Print("Opening the signal and background TTrees with uproot using ROOT file %s" % (ts + opts.rootFileName + ns), True)
    signal     = uproot.open(opts.rootFileName)["treeS"]
    background = uproot.open(opts.rootFileName)["treeB"]

    # Input list of discriminatin variables (TBranches)
    inputList = []
    inputList.append("TrijetPtDR")
    inputList.append("TrijetDijetPtDR")
    inputList.append("TrijetBjetMass")
    inputList.append("TrijetLdgJetBDisc")
    inputList.append("TrijetSubldgJetBDisc")
    inputList.append("TrijetBJetLdgJetMass")
    inputList.append("TrijetBJetSubldgJetMass")
    inputList.append("TrijetMass")
    inputList.append("TrijetDijetMass")
    inputList.append("TrijetBJetBDisc")
    inputList.append("TrijetSoftDrop_n2")
    inputList.append("TrijetLdgJetCvsL")
    inputList.append("TrijetSubldgJetCvsL")
    inputList.append("TrijetLdgJetPtD")
    inputList.append("TrijetSubldgJetPtD")
    inputList.append("TrijetLdgJetAxis2")
    inputList.append("TrijetSubldgJetAxis2")
    inputList.append("TrijetLdgJetMult")
    inputList.append("TrijetSubldgJetMult")
    nInputs = len(inputList)

    # Construct signal and background dataframes using a list of TBranches (a Dataframe is a two dimensional structure representing data in python)
    Print("Constucting dataframes for signal and background with %d input variables:\n\t%s%s%s" % (nInputs, ss, "\n\t".join(inputList), ns), True)
    df_signal     = signal.pandas.df(inputList) # call an array-fetching method to fill a Pandas DataFrame.
    df_background = background.pandas.df(inputList)

    # Get the index (row labels) of the DataFrame.
    nsignal = len(df_signal.index)
    nbkg    = len(df_background.index)
    Print("Signal has %s%d%s row labels. Background has %s%d%s row labels" % (ss, nsignal, ns, es, nbkg, ns), True)
    
    # Sanity check?
    columns = list(df_signal.columns.values)
    Verbose("The signal columns are :\n\t%s%s%s" % (ss, "\n\t".join(columns), ns), True)    

    # Get a Numpy representation of the DataFrames for signal and background datasets
    dset_signal     = df_signal.values
    dset_background = df_background.values
    Verbose("Printing 1 instance of the Numpy representation of the signal DataFrame:%s" % (ss), True)
    # For-loop: All TBranch entries
    for vList in dset_signal:
        # For-loop: All input variable values for given entry
        for v in vList:
            Verbose(v, False)
        break
    Verbose("%sPrinting 1 instance of the Numpy representation of the background DataFrame%s:" % (ns, es), True)
    # For-loop: All TBranch entries
    for vList in dset_background:
        # For-loop: All input variable values for given entry
        for v in vList:
            Verbose(v, False)
        break

    # Construct the pandas DataFrames (2D size-mutable tabular data structure with labeled axes i.e. rows and columns)
    Print("Constructing pandas DataFrames for signal and background", True)
    ds_signal     = pandas.DataFrame(data=dset_signal,columns=inputList)
    ds_background = pandas.DataFrame(data=dset_background,columns=inputList)

    # Construct pandas DataFrames (2D size-mutable tabular data structure with labeled axes i.e. rows and columns)
    df_signal     = df_signal.assign(signal=1)
    df_background = df_background.assign(signal=0)
    Verbose("Printing tabular data for signal:\n%s%s%s" % (ss, ds_signal,ns), True)
    Verbose("Printing tabular data for background:\n%s%s%s" % (ss, ds_background,ns), True)
    
    # Create dataframe lists
    df_list = [df_signal, df_background]
    df_all  = pandas.concat(df_list)

    # Get a Numpy representation of the DataFrames for signal and background datasets (again, and AFTER assigning signal and background)
    dset_signal     = df_signal.values
    dset_background = df_background.values
    dset_all        = df_all.values

    # Define keras model as a linear stack of layers. Add layers one at a time until we are happy with our network architecture.
    Print("Creating the sequential model", True)
    model = Sequential()

    # The best network structure is found through a process of trial and error experimentation. Generally, you need a network large enough to capture the structure of the problem.
    layer1_neurons  = 36
    layer2_neurons  = nInputs
    layerN_neurons  = 1
    layer1_activate = opts.activation
    layer2_activate = opts.activation
    layerN_activate = "sigmoid"

    # The Dense function defines each layer - how many neurons and mathematical function to use. (First hidden layer with "36" neurons, "nInputs" inputs, and "relu" as acivation function)
    for iLayer, n in enumerate(opts.neurons, 0):
        Print("Adding %slayer# %d%s, with %s%d neurons%s and activation function %s" % (ts, iLayer+1, ns, ls, n, ns, ls + opts.activation[iLayer] + ns), i==0)
        model.add( Dense(opts.neurons[iLayer], input_dim = nInputs, activation = opts.activation[iLayer]) ) # only first layer demands input_dim. For the rest it is implied.

    # Print a summary representation of your model. 
    Print("Printing model summary:", True)
    model.summary()

    # Get a dictionary containing the configuration of the model. The model can be reinstantiated from its config via: model = Model.from_config(config)
    if 0:
        config = model.get_config()
    
    # Split data into input (X) and output (Y). (Note: dataset includes both signal and background sequentially)
    X = dset_all[:2*nsignal,0:nInputs] # rows: 0 -> 2*signal, columns: 0 -> 19
    Y = dset_all[:2*nsignal,nInputs:]  # rows: 0 -> 2*signal, columns: 19 (isSignal = 0 or 1)
    #
    X_signal     = dset_signal[:nsignal, 0:nInputs]
    X_background = dset_background[:nsignal, 0:nInputs]

    # Split the datasets (X= 19 inputs, Y=output variable). Test size 0.5 means half for training half for testing
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.5, random_state=opts.rndSeed, shuffle=True)

    # Early stop? Show patience of "50" epochs with a change in the loss function smaller than "min_delta" before stopping procedure
    earlystop      = keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0.0001, patience=50)
    callbacks_list = [earlystop]

    # Compile the model with the chosen loss function. #acc = accuracy. Optimize loss function, optimizer
    # [Loss function is used to understand how well the network is working (compare predicted label with actual label via some function)]
    # Optimizer function is related to a function used to optimise the weights
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['acc']) 
    
    # Fit the model with our data
    # (An "epoch" is an arbitrary cutoff, generally defined as "one iteration of training on the whole dataset", 
    # used to separate training into distinct phases, which is useful for logging and periodic evaluation.)
    hist = model.fit(X_train,
                     Y_train,
                     validation_data=(X_test, Y_test),
                     epochs     = opts.epochs,    # one pass over the entire dataset
                     batch_size = opts.batchSize, # a set of N samples (https://stats.stackexchange.com/questions/153531/what-is-batch-size-in-neural-network)
                     shuffle    = False,
                     verbose    = int(opts.log), # 0=silent, 1=progress, 2=mention the number of epoch
                     callbacks  = callbacks_list
                 )

    if not opts.test:
        modelName = "Model_%s_trained.h5" % (opts.rootFileName.replace(".root",""))
        model.save(modelName)
        
        # serialize model to JSON (contains arcitecture of model)
        model_json = model.to_json()
        with open("model_architecture.json", "w") as json_file:
            json_file.write(model_json)

        # serialize weights to HDF5
        model.save_weights('model_weights.h5', overwrite=True)
        model.save(modelName)

    # Produce method score (i.e. predict output value for given input dataset). Computation is done in batches.
    Print("Generating output predictions for the input samples", True) # (e.g. Numpy array)
    pred_train      = model.predict(X_train     , batch_size=None, verbose=1, steps=None)
    pred_test       = model.predict(X_test      , batch_size=None, verbose=1, steps=None)
    pred_signal     = model.predict(X_signal    , batch_size=None, verbose=1, steps=None)
    pred_background = model.predict(X_background, batch_size=None, verbose=1, steps=None)
    # Keras version 2.2.5 or later (https://keras.io/models/model/)
    # pred_train      = model.predict(x, batch_size=None, verbose=0, steps=None, callbacks=None, max_queue_size=10, workers=1, use_multiprocessing=False)

    # Join a sequence of arrays (X and Y) along an existing axis (1). In other words, add the ouput variable (Y) to the input variables (X)
    XY_train = numpy.concatenate((X_train, Y_train), axis=1)
    XY_test  = numpy.concatenate((X_test , Y_test ), axis=1)

    # Pick events with output = 1
    Print("Select events/samples which have an output variable Y (last column) equal to 1 (i.e. prediction is combatible with signal)", True)
    x_train_S = XY_train[XY_train[:,nInputs] == 1]; x_train_S = x_train_S[:,0:nInputs] #iro - fixme - understand
    x_test_S  = XY_test[XY_test[:,nInputs] == 1];   x_test_S  = x_test_S[:,0:nInputs]

    Print("Select events/samples which have an output variable Y (last column) equal to 0 (i.e. prediction is NOT combatible with signal)", False)
    x_train_B = XY_train[XY_train[:,nInputs] == 0]; x_train_B = x_train_B[:,0:nInputs]
    x_test_B  = XY_test[XY_test[:,nInputs] == 0];   x_test_B  = x_test_B[:,0:nInputs]
    
    # Produce method score for signal (training and test) and background (training and test)
    pred_train_S =  model.predict(x_train_S, batch_size=None, verbose=1, steps=None)
    pred_train_B =  model.predict(x_train_B, batch_size=None, verbose=1, steps=None)
    pred_test_S  =  model.predict(x_test_S , batch_size=None, verbose=1, steps=None)
    pred_test_B  =  model.predict(x_test_B , batch_size=None, verbose=1, steps=None)

    # Plot some output
    func.PlotOutput(pred_signal , pred_background, opts.saveDir, "Output_SB"      , 1, opts.saveFormats) #dump to json
    func.PlotOutput(pred_train  , pred_test      , opts.saveDir, "Output_pred"    , 0, opts.saveFormats)
    func.PlotOutput(pred_train_S, pred_train_B   , opts.saveDir, "Output_SB_train", 1, opts.saveFormats)
    func.PlotOutput(pred_test_S , pred_test_B    , opts.saveDir, "Output_SB_test" , 1, opts.saveFormats)
    
    # Calculate efficiency (Entries Vs Output)
    htrain_s, htest_s, htrain_b, htest_b = func.PlotOvertrainingTest(pred_train_S, pred_test_S, pred_train_B, pred_test_B, opts.saveDir, "OvertrainingTest", opts.saveFormats)
    func.PlotEfficiency(htest_s, htest_b, opts.saveDir, "Efficiency", opts.saveFormats)
    
    # Print total time elapsed
    tFinish = time.time()
    dt      = int(tFinish) - int(tStart)
    days    = divmod(dt,86400)      # days
    hours   = divmod(days[1],3600)  # hours
    mins    = divmod(hours[1],60)   # minutes
    secs    = mins[1]               # seconds
    Print("Total elapsed time is %s days, %s hours, %s mins, %s secs" % (days[0], hours[0], mins[0], secs), True)
    
    # Copy logfile to results directory
    if opts.log:
        logPath = os.path.join(opts.saveDir, opts.logFile)
        os.system("mv %s %s" % (opts.logFile, logPath))
        Print("Log file %s moved to %s" % (ls + opts.logFile + ns, ts + logPath + ns), True)
    return 

#================================================================================================ 
# Main
#================================================================================================ 
if __name__ == "__main__":
    '''
    https://docs.python.org/3/library/argparse.html
 
    name or flags...: Either a name or a list of option strings, e.g. foo or -f, --foo.
    action..........: The basic type of action to be taken when this argument is encountered at the command line.
    nargs...........: The number of command-line arguments that should be consumed.
    const...........: A constant value required by some action and nargs selections.
    default.........: The value produced if the argument is absent from the command line.
    type............: The type to which the command-line argument should be converted.
    choices.........: A container of the allowable values for the argument.
    required........: Whether or not the command-line option may be omitted (optionals only).
    help............: A brief description of what the argument does.
    metavar.........: A name for the argument in usage messages.
    dest............: The name of the attribute to be added to the object returned by parse_args().
    '''
    
    # Default Settings
    ROOTFILENAME = "histograms-TT_19var.root"
    NOTBATCHMODE = False
    SAVEDIR      = None
    SAVEFORMATS  = "png"
    URL          = False
    VERBOSE      = False
    TEST         = False
    RNDSEED      = 1234
    EPOCHS       = 5000
    BATCHSIZE    = 500  # See: http://stats.stackexchange.com/questions/153531/ddg#153535
    ACTIVATION   = "relu" # "relu" or PReLU" or "LeakyReLU"
    NEURONS      = "36,19,1"
    LOG          = False
    GRIDX        = False
    GRIDY        = False

    # Define the available script options
    parser = OptionParser(usage="Usage: %prog [options]")

    parser.add_option("--notBatchMode", dest="notBatchMode", action="store_true", default=NOTBATCHMODE, 
                      help="Disable batch mode (opening of X window) [default: %s]" % NOTBATCHMODE)

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=VERBOSE, 
                      help="Enable verbose mode (for debugging purposes mostly) [default: %s]" % VERBOSE)

    parser.add_option("--test", dest="test", action="store_true", default=TEST, 
                      help="Enable test mode [default: %s]" % TEST)

    parser.add_option("--rootFileName", dest="rootFileName", type="string", default=ROOTFILENAME, 
                      help="Input ROOT file containing the signal and backbground TTrees with the various TBrances *variables) [default: %s]" % ROOTFILENAME)

    parser.add_option("--saveDir", dest="saveDir", type="string", default=SAVEDIR,
                      help="Directory where all pltos will be saved [default: %s]" % SAVEDIR)

    parser.add_option("--url", dest="url", action="store_true", default=URL, 
                      help="Don't print the actual save path the histogram is saved, but print the URL instead [default: %s]" % URL)

    parser.add_option("-s", "--saveFormats", dest="saveFormats", default = SAVEFORMATS,
                      help="Save formats for all plots [default: %s]" % SAVEFORMATS)
    
    parser.add_option("--rndSeed", dest="rndSeed", type=int, default=RNDSEED, 
                      help="Value of random seed (integer) [default: %s]" % RNDSEED)
    
    parser.add_option("--epochs", dest="epochs", type=int, default=EPOCHS, 
                      help="Number of \"epochs\" to be used (how many times you go through your training set) [default: %s]" % EPOCHS)

    parser.add_option("--batchSize", dest="batchSize", type=int, default=BATCHSIZE,
                      help="The \"batch size\" to be used (= a number of samples processed before the model is updated). Batch size impacts learning significantly; typically networks trains faster with mini-batches. However, the batch size has a direct impact on the variance of gradients (the larger the batch the better the appoximation and the largef the memory usage). [default: %s]" % BATCHSIZE)

    parser.add_option("--activation", dest="activation", type="string", default=ACTIVATION,
                      help="Type of transfer function that will be used to map the output of one layer to another [default: %s]" % ACTIVATION)

    parser.add_option("--neurons", dest="neurons", type="string", default=NEURONS,
                      help="List of neurons to use for each sequential layer (comma-separated integers)  [default: %s]" % NEURONS)

    parser.add_option("--log", dest="log", action="store_true", default=LOG,
                      help="Boolean for redirect sys.stdout to a log file [default: %s]" % LOG)

    parser.add_option("--gridX", dest="gridX", action="store_true", default=GRIDX,
                      help="Enable x-axis grid [default: %s]" % GRIDX)

    parser.add_option("--gridY", dest="gridY", action="store_true", default=GRIDY,
                      help="Enable y-axis grid [default: %s]" % GRIDY)

    (opts, parseArgs) = parser.parse_args()
    
    # Require at least two arguments (script-name, ...)
    if len(sys.argv) < 1:
        parser.print_help()
        sys.exit(1)
    else:
        pass
        
    # Create save formats
    if "," in opts.saveFormats:
        opts.saveFormats = opts.saveFormats.split(",")
    else:
        opts.saveFormats = [opts.saveFormats]
    #opts.saveFormats = ["." + s for s in opts.saveFormats]
    opts.saveFormats = [s for s in opts.saveFormats]
    Verbose("Will save all output in %d format(s): %s" % (len(opts.saveFormats), ss + ", ".join(opts.saveFormats) + ns), True)

    # Create specification lists
    if "," in opts.activation:
        opts.activation = opts.activation.split(",")
    else:
        opts.activation = [opts.activation]
    Verbose("Activation = %s" % (opts.activation), True)
    if "," in opts.neurons:
        opts.neurons = list(map(int, opts.neurons.split(",")) )
    else:
        opts.neurons = list(map(int, [opts.neurons]))
    Verbose("Neurons = %s" % (opts.neurons), True)
        
    # Sanity checks (One activation function for each layer)
    if len(opts.neurons) != len(opts.activation):
        msg = "The list of neurons (size=%d) is not the same size as the list of activation functions (=%d)" % (len(opts.neurons), len(opts.activation))
        raise Exception(es + msg + ns)  
    # Sanity check (Last layer)
    if opts.neurons[-1] != 1:
        msg = "The number of neurons for the last layer should be equal to 1 (=%d instead)" % (opts.neurons[-1])
        raise Exception(es + msg + ns)  
    if opts.neurons[-1] != 1:
        msg = "The activation function for the last layer should be set to \"sigmoid\"  (=%s instead)" % (opts.activation[-1])
        raise Exception(es + msg + ns)  

    # Define dir/logfile names
    specs = "%dLayers" % (len(opts.neurons))
    for i,n in enumerate(opts.neurons, 0):
        specs+= "_%s%s" % (opts.neurons[i], opts.activation[i])
    specs+= "_%dEpochs_%dBatchSize" % (opts.epochs, opts.batchSize)

    # Get the current date and time
    now    = datetime.now()
    nDay   = now.strftime("%d")
    nMonth = now.strftime("%h")
    nYear  = now.strftime("%Y")
    nTime  = now.strftime("%Hh%Mm") #now.strftime("%Hh%Mm%Ss")
    #nDate  = "%s_%s_%s" % (nDay, nMonth, nTime)
    nDate  = "%s-%s-%s-%s" % (nDay, nMonth, nYear, nTime)
    sName  = "Keras_%s_%s" % (specs, nDate)

    # Determine logFile name
    opts.logFile = sName + ".log"

    # Determine path for saving plots
    if opts.saveDir == None:
        usrName = getpass.getuser()
        usrInit = usrName[0]
        myDir   = "tmp"
        if "lxplus" in socket.gethostname():
            myDir = "/afs/cern.ch/user/%s/%s/public/html/" % (usrInit, usrName)
        else:
            myDir = os.path.join(os.getcwd())
        opts.saveDir = os.path.join(myDir, sName)
    else:
        pass

    # Create logfile
    bak_stdout = sys.stdout
    log_file = open(opts.logFile, 'w')
    if opts.log:
        # Keep a copy of the original "stdout"
        sys.stdout = log_file
        Print("Log file %s created" % (ls + opts.logFile + ns), True)

    # Inform user
    table    = []
    msgAlign = "{:^10} {:^10} {:>12}"
    title    =  msgAlign.format("Layer #", "Neurons", "Activation")
    hLine    = "="*len(title)
    table.append(hLine)
    table.append(title)
    table.append(hLine)
    for i, n in enumerate(opts.neurons, 0): 
        table.append( msgAlign.format(i+1, opts.neurons[i], opts.activation[i]) )
    table.append("")
    for r in table:
        Print(r, False)

    # See https://keras.io/activations/
    actList = ["elu", "softmax", "selu", "softplus", "softsign", "PReLU", "LeakyReLU",
               "relu", "tanh", "sigmoid", "hard_sigmoid", "exponential", "linear"] # Loukas used "relu"
    # Sanity checks
    for a in opts.activation:
        if a not in actList:
            msg = "Unsupported activation function %s. Please select on of the following:%s\n\t%s" % (opts.activation, ss, "\n\t".join(actList))
            raise Exception(es + msg + ns)    
    
    # Call the main function
    Print("Using Keras %s (hostname = %s)" % (ss + keras.__version__ + ns, ls + socket.gethostname() + ns), True)
    main(opts)

    # Restore "stdout" to its original state and close the log file
    sys.stdout =  bak_stdout
    log_file.close()

    Print("All output saved under directory %s" % (ls + opts.saveDir + ns), True)

    if opts.notBatchMode:
        raw_input("=== sequential.py: Press any key to quit ROOT ...")
