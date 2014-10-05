#!/usr/bin/env python

# Copyright (c) 2014 Jeff Kramer

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import pyaudio
import audioop
import math
from nupic.encoders import ScalarEncoder
from nupic.research.TP import TP
from termcolor import colored

# Create our NuPIC entities

enc = ScalarEncoder(n=50, w=3, minval=0, maxval=100,
						clipInput=True, forced=True)

tp = TP(numberOfCols=50, cellsPerColumn=4, initialPerm=0.5,
		connectedPerm=0.5, minThreshold=5, newSynapseCount=5,
		permanenceInc=0.1, permanenceDec=0.1,
        activationThreshold=3, globalDecay=0.1, burnIn=1,
        checkSynapseConsistency=False, pamLength=3)

# Setup our PyAudio Stream

p = pyaudio.PyAudio()
stream = p.open(format = pyaudio.paInt16, channels = 1,
	rate = int(p.get_device_info_by_index(0)['defaultSampleRate']),
	input = True, frames_per_buffer = 1024*5)

print "%-48s %48s" % (colored("DECIBELS","green"),
						colored("PREDICTION","red"))

b = 0
while 1:
	b += 1

	# Grab a sample from our audio input.

	stream.start_stream()
	data = stream.read(1024*5)
	stream.stop_stream()

	# Turn our sample into a decibel measurement.

	rms = audioop.rms(data,2)
	decibel = int(20 * math.log10(rms))

	# Turn our decibel number into a sparse distributed representation.

	encoded = enc.encode(decibel)

	# Add our encoded representation to the temporal pooler.

	tp.compute(encoded, enableLearn = True, computeInfOutput = True)

	# For the curious:
	#tp.printCells()
	#tp.printStates(printPrevious=False, printLearnState=False)

	predictedCells = tp.getPredictedState()

	decval = 0
	if predictedCells.any():
		decval = predictedCells.max(axis=1).nonzero()[0][-1]

		# This is more correct, but seems wonky...
		#decval =  int(enc.decode(predictedCells.max(axis=1).
		#nonzero()[0])[0]["[0:100]"][0][0][1])

	print "%-48s %48s" % (colored(("*"*(decibel/2))[:38],"green"),
							colored(("#"*(decval))[:38],"red"))

	if b >= 20:
		b = 0

		# If we have enough samples, reset the encoder to help it learn.
		tp.reset()

		print " "*35, "RESET!"
