import numpy as np

import theano
from theano import tensor as T
from cnnLayers import *
from trainingoptions import *
from common import *

theanoFloat  = theano.config.floatX

class ConvolutionalNN(object):

  """
  TODO: weight decay
  """
  def __init__(self, layers, trainingOptions, nameDataset=''):
    self.layers = layers
    self.trainingOptions = trainingOptions
    self.nameDataset = nameDataset

  def _setUpLayers(self, x, inputDimensions):

    inputVar = x
    inputDimensionsPrevious = inputDimensions

    for layer in self.layers[0:-1]:
      layer._setUp(inputVar, inputDimensionsPrevious)
      inputDimensionsPrevious = layer._outputDimensions()
      inputVar = layer.output

    # the fully connected layer, the softmax layer
    # TODO: if you allow (and you should) multiple all to all layers you need to change this
    # after some point

    self.layers[-1]._setUp(inputVar.flatten(2),
                           inputDimensionsPrevious[0] * inputDimensionsPrevious[1] * inputDimensionsPrevious[2])


  def _reshapeInputData(self, data):
    if len(data[0].shape) == 2:
      inputShape = (data.shape[0], 1, data[0].shape[0], data[0].shape[1])
      data = data.reshape(inputShape)

    return data

  def train(self, data, labels, epochs=100):

    print "shuffling training data"
    data, labels = shuffle(data, labels)


    print "data.shape"
    print data.shape

    print "labels.shape"
    print labels.shape

    data = self._reshapeInputData(data)

    sharedData = theano.shared(np.asarray(data, dtype=theanoFloat))
    sharedLabels = theano.shared(np.asarray(labels, dtype=theanoFloat))

    miniBatchSize = self.trainingOptions.miniBatchSize
    nrMinibatches = len(data) / miniBatchSize

    # Symbolic variable for the data matrix
    x = T.tensor4('x', dtype=theanoFloat)
    # the labels
    y = T.matrix('y', dtype=theanoFloat)

    # Set up the input variable as a field of the conv net
    # so that we can access it easily for testing
    self.x = x

    # Set up the layers with the appropriate theano structures
    self._setUpLayers(x, data[0].shape)

    #  create the batch trainer and using it create the updates
    batchTrainer = CNNBatchTrainer(self.layers)

    # Set the batch trainer as a field in the conv net
    # then we can access it for a forward pass during testing
    self.batchTrainer = batchTrainer
    # updates = batchTrainer.buildUpdates(error, self.trainingOptions)

    # # the train function
    # trainModel = theano.function(
    #         inputs=[miniBatchIndex],
    #         outputs=error,
    #         updates=updates,
    #         givens={
    #             x: sharedData[miniBatchIndex * miniBatchSize: (miniBatchIndex + 1) * miniBatchSize],
    #             y: sharedLabels[miniBatchIndex * miniBatchSize: (miniBatchIndex + 1) * miniBatchSize]})

    trainModel = batchTrainer.makeTrainFunction(x, y, sharedData, sharedLabels, self.trainingOptions)

    #  run the loop that trains the net
    for epoch in xrange(epochs):
      for i in xrange(nrMinibatches):
        trainModel(i, self.trainingOptions.momentum)


  def test(self, data):
    miniBatchIndex = T.lscalar()

    miniBatchSize = self.trainingOptions.miniBatchSize

    data = self._reshapeInputData(data)
    sharedData = theano.shared(np.asarray(data, dtype=theanoFloat))

    # Do a forward pass trough the network
    forwardPass = theano.function(
            inputs=[miniBatchIndex],
            outputs=self.batchTrainer.output,
            givens={
                self.x: sharedData[miniBatchIndex * miniBatchSize: (miniBatchIndex + 1) * miniBatchSize]})

    nrMinibatches = data.shape[0] / miniBatchSize

    # do the loop that actually predicts the data
    lastLayer = concatenateLists([forwardPass(i) for i in xrange(nrMinibatches)])
    lastLayer = np.array(lastLayer)

    return lastLayer, np.argmax(lastLayer, axis=1)