import numpy
import pickle
import json


# ----- Coding Tables ----- #

# Low-Entropy Code Input Symbo Limit and Threshold (Table 5-16)
# Code index, i || Input Simbol Limit, Li || Threshold, Ti
INPUT_SYMBOL_LIMIT_AND_THRESHOLD_TABLE_PATH = 'CodingTables/LowEntropyCodeInputSymbolLimitAndThreshold.pickle'

# Code tables (Input to output)
# List. Element index = Code index
# Each list element is a dictionary with 'key' = 'input codeword'
OUTPUT_TO_INPUT_CODEWORDS = 'CodingTables/DecodingTable.pickle'

# Flush tables (Input to output)
# List. Element index = Code index
# Each list element is a dictionary with 'key' = 'input codeword'
FLUSH_OUTPUT_TO_INPUT_CODEWORDS = 'CodingTables/FlushDecodingTable.pickle'






class HybridDecoder():

    def __init__(self):

        # Coding Tables
        self.Table_InputSimbolLimitAndThreshold = None
        self.Table_OutputToInputCodeWords = None
        self.Table_FlushOutputToInputCodeWords = None
        self.loadCodingTables()

        # Coder variables
        #   Dynamic range in bits (D)
        self.dynamicRangeInBits = None
        #   User defined (1 <= ɣ(0) <= 8)
        self.gamma_0 = None
        #   Counter: Γ(0) = 2^ɣ(0)
        self.Gamma = None
        #   High-Resolution accumulator: 0 <= Σ(0) <= 2^(D+ɣ(0))
        self.Sigma = None
        #   User define initial value for Sigma
        self.Sigma_0 = None
        #   Rescaling counter size parameter: max{4, ɣ(0)+1} <= ɣ^* <= 11
        self.gamma = None
        #   Threshold: T(0) (page 5-23 - Table 5-16)
        self.T0 = self.Table_InputSimbolLimitAndThreshold[0][2]
        #   Unary Length Limit: 8 <= Umax <= 32
        self.Umax = None
        #   Active prefix list for the low entropy coder
        self.ActivePrefixList = None

        # Bitstream variables
        self.bitStream = None           # bytearray with the already completely coded bytes
        self.currentByteIndex = None    # byte being coded (still uncompleted)
        self.readBits = None            # number of bits already read from the current byte

        # Image parameters
        self.nBands = None
        self.nRows = None
        self.nCols = None

        # Variables for storing the counter values
        self.GammaList = None
        self.RescalingList = None




    # ----- Utils general functions ----- #

    def inverseMod(self, value, modDivisor):
        if value == 0:
            value = modDivisor
        return value


    # Load the coding files from the pickle files
    def loadCodingTables(self):
        # Low-Entropy Code Input Symbo Limit and Threshold
        filePath = INPUT_SYMBOL_LIMIT_AND_THRESHOLD_TABLE_PATH
        filePointer = open(filePath, 'rb')
        self.Table_InputSimbolLimitAndThreshold = pickle.load(filePointer)
        filePointer.close() 
        # Code tables (Input to output)
        filePath = OUTPUT_TO_INPUT_CODEWORDS
        filePointer = open(filePath, 'rb')
        self.Table_OutputToInputCodeWords = pickle.load(filePointer)
        filePointer.close() 
        # Flush tables (Input to output)
        filePath = FLUSH_OUTPUT_TO_INPUT_CODEWORDS
        filePointer = open(filePath, 'rb')
        self.Table_FlushOutputToInputCodeWords = pickle.load(filePointer)
        filePointer.close() 


    # Read a binary string of 'nBits' from the bitstream 
    # Inputs:
    #   nBits: number of bits to be read and returned in string format
    #   updateCounters: indicates if the returned currentByte and readBits are modified or not
    #   reverseReading: Bolean. 
    #       True: read from the back (as normaly done in the decoder)
    #       False: read from the begining (as done in the header)
    def readBinaryStringFromBitStream(self, nBits, updateCounters=True, reverseReading = True):
        currentByteIndexLocal = self.currentByteIndex
        readBitsLocal = self.readBits
        binaryString = ''
        currentByte = self.bitStream[currentByteIndexLocal]
        for counter in range(0, nBits):
            # Get a new byte to be decoded
            if readBitsLocal == 0:
                currentByte = self.bitStream[currentByteIndexLocal] 
            # Decode the specific bit
            if reverseReading:
                bitIntegerValue = ((currentByte >> readBitsLocal) & 0x1)
                binaryString = str(bitIntegerValue) + binaryString
            else:
                bitIntegerValue = ((currentByte >> (7 - readBitsLocal)) & 0x1)
                binaryString = binaryString + str(bitIntegerValue)
            # Update counters
            readBitsLocal = readBitsLocal + 1
            if readBitsLocal >= 8:
                readBitsLocal = 0
                if reverseReading:
                    currentByteIndexLocal = currentByteIndexLocal - 1
                else:
                    currentByteIndexLocal = currentByteIndexLocal + 1
        # Return the desired values
        if updateCounters:
            self.currentByteIndex = currentByteIndexLocal
            self.readBits = readBitsLocal
        return binaryString


    def readIntegerValueFromBitstreamForHeader(self, nBits):
        binaryString = self.readBinaryStringFromBitStream(nBits, updateCounters=True, reverseReading=False)
        integerValue = int(binaryString, 2)
        return integerValue
   

    # Read bits from the bitstream, one by one, until one of them matches the inversePadingValue
    #   inversePadingValue: '0', '1'
    def inversePadding(self, inversePadingValue):
        binaryString = self.readBinaryStringFromBitStream(1, updateCounters=True)
        while binaryString == '0':
            binaryString = self.readBinaryStringFromBitStream(1, updateCounters=True)


    # Read bits from the bitstream, one by one, while the read bit matches the targetValue
    #   targetValue: '0', '1'
    #   updateCounters: indicates if the returned currentByte and readBits are modified or not
    def getNumberOfBitsEqualToTargetValue(self, targetValue, maximumNumberOfBits, updateCounters=True):
        # Get number of bits matching the target value
        nMatchingBits = 0
        binaryString = self.readBinaryStringFromBitStream(maximumNumberOfBits, updateCounters=False)
        while True:
            bitFronBinaryString = binaryString[-1:]
            if bitFronBinaryString == targetValue:
                nMatchingBits = nMatchingBits + 1
                binaryString = binaryString[:-1]
            else:
                break
        # Update counters if necessary
        if updateCounters:
            binaryString = self.readBinaryStringFromBitStream(nMatchingBits, updateCounters=True)
        # Return the result
        return nMatchingBits


    # Read bitstream from binary file
    def readBitStreamFromBinaryFile(self, filePath):
        filePointer = open(filePath, 'rb')
        self.bitStream = filePointer.read()
        filePointer.close()


    def getOutputCodeWordFromBitstream(self, dictionary):
        outputCodeWord = ''
        while not outputCodeWord in dictionary:
            newBitString = self.readBinaryStringFromBitStream(1, updateCounters=True)
            outputCodeWord = newBitString + outputCodeWord
        return outputCodeWord








    # ----- Decoder specific functions functions ----- #      
    

    def initializeDecodingVariables(self):        
        # Counter: Γ(0) = 2^ɣ(0)
        # Values ordered according to 't = col + row * nCols'
        self.GammaList = []
        self.RescalingList = []
        Gamma = 2**self.gamma_0  
        for row in range(0, self.nRows):
            for col in range(0, self.nCols):
                # Update the Gamma Value
                if not (row == 0 and col == 0):
                    if Gamma < 2**self.gamma - 1:
                        Gamma = Gamma + 1
                        self.RescalingList.append(False)
                    else:
                        Gamma = int((Gamma + 1)/2) 
                        self.RescalingList.append(True)
                else:
                    self.RescalingList.append(False)
                # Store the Gamma value in the Gamma Matrix
                self.GammaList.append(Gamma)      
        # Bitstream variables 
        # TIP: it would be possible to reverser the bitstream order using self.bitStream.reverse()
        # In such a case, 'self.currentByteIndex' should be 0, and the reading function should increase
        # the 'self.currentByteIndex' value instead of decrease it
        self.currentByteIndex = len(self.bitStream) - 1
        self.readBits = 0




    def decodeImageTail(self):
        # Remove the padding values
        self.inversePadding('1')
        # Read the 'D+2+ɣ^*' bits binary integer Σ(t) value for each band in decreasing order
        nBits = self.dynamicRangeInBits + 2 + self.gamma
        self.SigmaList = []
        for b in range(0, self.nBands):
            binaryString = self.readBinaryStringFromBitStream(nBits, updateCounters=True)
            Sigma = int(binaryString, 2)
            self.SigmaList.insert(0, Sigma)
        # Get Flush codewords
        self.ActivePrefixList = []
        flushValues = []
        for i in range(15, -1, -1):
            dictionary_OutputToInputCodeWords = self.Table_FlushOutputToInputCodeWords[i]
            outputCodeWord = self.getOutputCodeWordFromBitstream(dictionary_OutputToInputCodeWords)
            inputCodeWord = dictionary_OutputToInputCodeWords.get(outputCodeWord)
            self.ActivePrefixList.insert(0, inputCodeWord)
            flushValues.insert(0, outputCodeWord)



    # CCSDS123 - GPO2 Inverse 
    # Actions
    #   Decodes the value 'j' from the bitstring using integer code index 'k' 
    # Inputs:
    #   k: k value to be used
    # Outputs:
    #   j: decoded unsigned integer 
    def GPO2_decoding(self, k):
        # Get number of 'zeros' at the end of the bitstream
        #   If nZeros < Umax:
        #       Coding-Decoding mode A
        #   IF nZeros == Umax:
        #       Coding-Decoding mode B
        nZeros = self.getNumberOfBitsEqualToTargetValue('0', self.Umax, updateCounters=True)
        # Coding-Decoding mode A
        if nZeros < self.Umax:
            # Remove one bit from the bitstream (with value 1)
            binaryString = self.readBinaryStringFromBitStream(1, updateCounters=True)
            # Read the 'k' bits as plain binary ('k' least significant bits of 'j')
            if k > 0:
                binaryString = self.readBinaryStringFromBitStream(k, updateCounters=True)
                integerValueOfTheKLeastSignificantBitsOfJ = int(binaryString, 2)
            else:
                integerValueOfTheKLeastSignificantBitsOfJ = 0
            # Generate the 'j' value
            j = int(nZeros * 2**k) + integerValueOfTheKLeastSignificantBitsOfJ
        # Coding-Decoding mode B
        elif nZeros == self.Umax:
            # Read 'j' as a plain binary number using D bits
            binaryString = self.readBinaryStringFromBitStream(self.dynamicRangeInBits, updateCounters=True)
            j = int(binaryString, 2)
        # Return the 'j' value
        return j


    # Returns True: current mapped residual has to be processed as high-entropy
    # Returns False: current mapped residual has to be processed as low-entropy
    def EvaluateHighEntropyCondition(self):
        if self.Sigma * (2**14) >= self.T0 * self.Gamma:
            # Process current residual as high entropy
            return True
        else:
            # Process current residual as low entropy
            return False


    #  Update the High Resolution Accumulator (Σ(t): Sigma) and the Counter (Γ(t): Gamma)
    #def UpdateHighResolutionAccumulatorAndCounter(self, mappedResidual):
    def UpdateHighResolutionAccumulatorAndCounter(self, mappedResidual, row, col, band):
        # TIP: Be care, in the decoder we have the values after being updated 
        # (Γ(t): Gamma) is rescaled when Γ(t-1)=2^ɣ-1
        # its value after being rescaled is Γ(t)=2^(ɣ-1)
        #if self.Gamma == 2**(self.gamma - 1):
        t = col + row * self.nCols
        self.Gamma = self.GammaList[t]
        rescaling = self.RescalingList[t]
        # If Γ(t) was rescaled
        if rescaling:
            # The least significant bit of Sigma(t-1) is stored in the bitstream before rescaling it
            # It must be read and added to the decoder rescaled value of Sigma
            binaryString = self.readBinaryStringFromBitStream(1, updateCounters=True)
            SigmaLeastSignificantBit = int(binaryString, 2)
            #self.Sigma = int(2*self.Sigma - 4*mappedResidual - 1) | SigmaLeastSignificantBit
            self.Sigma = int(2*self.Sigma - 4*mappedResidual) - SigmaLeastSignificantBit
        else:
            # If Γ(t) was not rescaled
            self.Sigma = self.Sigma - 4*mappedResidual



    def getHighResolutionAccumulatorForTargetBand(self, band):
        self.Sigma = self.SigmaList[band]

    def storeCurrentHighResolutionAccumulatorForTargetBand(self, band):
        self.SigmaList[band] = self.Sigma
        




    # Get the mapped residual carrying out the inverse of with the high-entropy processing
    def HighEntropyProcess(self):
        # Get largest 'k' satisfying:
        #   k ≤ max{D-2, 2}
        #   Γ(t) · 2^(k+2) ≤ Σ(t) + floor(49/2^5 · Γ(t))
        # TIP: 
        #   D: dynamicRangeInBits
        #   Σ(t): Sigma 
        #   Γ(t): Gamma
        k_good = 2
        k = 3
        while k <= max(self.dynamicRangeInBits-2, 2): 
            if self.Gamma * 2**(k+2) <= self.Sigma + int( (49/2**5)*self.Gamma ):
                k_good = k
                k = k + 1
            else:
                break
        # Code the mappedResidual using the appropiate value of 'k' and the 'GPO2' method 
        mappedResidual = self.GPO2_decoding(k_good)
        return mappedResidual



    # TODO: TBD
    # Get the mapped residual carrying out the inverse of with the low-entropy processing
    def LowEntropyProcess(self):
        # Get the largest code index 'i' satisfying:
        #   Σ(t) · 2^14 < Γ(t) · T(i)
        i_good = 0
        i = 1
        while i < 16: #len(self.Table_InputSimbolLimitAndThreshold):
            #  Threshold, Ti
            Ti = self.Table_InputSimbolLimitAndThreshold[i][2]
            # Condition to be satisfied
            if self.Sigma * 2**14 < self.Gamma * Ti:
                i_good = i
                i = i + 1
            else:
                break
        i = i_good
        # Get the corresponding Input Simbol Limit, Li
        Li = self.Table_InputSimbolLimitAndThreshold[i][1] 
        # Get the corresponding active prefix 
        ActivePrefix = self.ActivePrefixList[i]
        # If the Acvtive Prefix string is empty, load a new one from the bitstream
        if ActivePrefix == '':
            dictionary_OutputToInputCodeWords = self.Table_OutputToInputCodeWords[i]
            outputCodeWord = self.getOutputCodeWordFromBitstream(dictionary_OutputToInputCodeWords)
            inputCodeWord = dictionary_OutputToInputCodeWords.get(outputCodeWord)
            ActivePrefix = inputCodeWord
        # Extract the last character of the string (li) and update the acvite prefix value in the list
        li = ActivePrefix[-1:]
        self.ActivePrefixList[i] = ActivePrefix[:-1]
        # Decode the corresponding mapped residual from li according to its value
        if li == 'X':
            # the mapped residual was codded using Rk'(j), using:
            #   k = 0
            #   j = δ(t) - L(i) - 1
            k = 0
            j = self.GPO2_decoding(k)
            mappedResidual = j + Li + 1
        else:
            # li contains the mapped residual value represented in hexadecimal notation
            mappedResidual = int(li, 16)
        # return the mapped residual
        return mappedResidual





    def decodeTargetMappedResidual(self, row, col, band):
        if row == 0 and col == 0:
            # The first mapped residual of each band is decoded as a plain binary with D bits
            binaryString = self.readBinaryStringFromBitStream(self.dynamicRangeInBits, updateCounters=True)
            mappedResidual = int(binaryString, 2)
        else:
            # Get High-Resolution accumulator for the current band from the list
            self.getHighResolutionAccumulatorForTargetBand(band)
            # Get Counter for target 't' value
            t = col + row * self.nCols
            self.Gamma = self.GammaList[t]
            # Evaluate if the mapped residual should be processed as high or low entropy
            if self.EvaluateHighEntropyCondition():
                # High entropy processing
                mappedResidual = self.HighEntropyProcess()
            else:
                # Low entropy processing
                mappedResidual = self.LowEntropyProcess()
            # Update the high resolution accumulator and the counter
            self.UpdateHighResolutionAccumulatorAndCounter(mappedResidual, row, col, band)
            # Store the High-Resolution accumulator for the current band int the list
            self.storeCurrentHighResolutionAccumulatorForTargetBand(band)
        # Return the decoded mapped residual
        return mappedResidual











    # ----- Main processes ----- #

    def decode(self, inputFilePath, Umax, gamma, gamma_0, dynamicRange, nCols, nRows, nBands, decodingOrder):

        # Get the input parameters
        self.Umax = Umax
        self.gamma = gamma
        self.gamma_0 = gamma_0
        self.dynamicRangeInBits = dynamicRange
        self.nCols = nCols
        self.nRows = nRows
        self.nBands = nBands
        decodingOrder = decodingOrder

        # Read bitstream from binary file
        self.readBitStreamFromBinaryFile(inputFilePath)
        # Initialize the decoding variables
        self.initializeDecodingVariables()
        # Decode image tail
        self.decodeImageTail()
        # Generate the decoded TAC as an empty numpy
        MappedResidualsMatrix = numpy.zeros((self.nRows, self.nCols, self.nBands))
        # Decode each mapped residual one by one in the corresponding order (BSQ | BIL | BIP)
        #   BSQ
        if decodingOrder == 'bsq':
            for band in range(self.nBands-1, -1, -1):
                for row in range(self.nRows-1, -1, -1):
                    for col in range(self.nCols-1, -1, -1):
                            # Store the mapped residual value
                            mappedResidual = self.decodeTargetMappedResidual(row, col, band)
                            MappedResidualsMatrix[row, col, band] = mappedResidual
        #   BIL
        elif decodingOrder == 'bil':
            for row in range(self.nRows-1, -1, -1):
                for band in range(self.nBands-1, -1, -1):
                    for col in range(self.nCols-1, -1, -1):
                            # Store the mapped residual value
                            mappedResidual = self.decodeTargetMappedResidual(row, col, band)
                            MappedResidualsMatrix[row, col, band] = mappedResidual
        #   BIP
        elif decodingOrder == 'bip':
                for row in range(self.nRows-1, -1, -1):
                    for col in range(self.nCols-1, -1, -1):
                        for band in range(self.nBands-1, -1, -1):
                            # Store the mapped residual value
                            mappedResidual = self.decodeTargetMappedResidual(row, col, band)
                            MappedResidualsMatrix[row, col, band] = mappedResidual
        # Return the decoded TAC
        return MappedResidualsMatrix





    


    




    # Input parameters
    #   filePath: Target file path for the output quantized mapped residuals
    #   dataOrder: bsq, bip, bil
    def generateMappedResidualsLogFile(self, MappedResidualsMatrix, filePath='MappedResiduals.log', dataOrder='bsq'):
        # bsq data order
        if dataOrder == 'bsq':
            mappedResidualsFiles = filePath
            filePointer = open(mappedResidualsFiles, 'wb')
            for z in range(0, self.nBands): 
                for y in range(0, self.nRows):
                    for x in range(0, self.nCols):
                        filePointer.write(MappedResidualsMatrix[y, x, z].astype(numpy.uint16).tobytes())
            filePointer.close()
        # bip data order
        elif dataOrder == 'bip':
            mappedResidualsFiles = filePath
            filePointer = open(mappedResidualsFiles, 'wb')
            for y in range(0, self.nRows):
                for x in range(0, self.nCols):
                    for z in range(0, self.nBands): 
                        filePointer.write(MappedResidualsMatrix[y, x, z].astype(numpy.uint16).tobytes())
            filePointer.close()
        # bil data order
        elif dataOrder == 'bil':
            mappedResidualsFiles = filePath
            filePointer = open(mappedResidualsFiles, 'wb')
            for y in range(0, self.nRows):
                for z in range(0, self.nBands): 
                    for x in range(0, self.nCols):
                        filePointer.write(MappedResidualsMatrix[y, x, z].astype(numpy.uint16).tobytes())
            filePointer.close()
        # Unrecognized data order
        else:
            print('\n\n The specified data order does not match any of the available format. Use bsq, bil or bip \n\n')

    

    


