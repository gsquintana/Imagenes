from os import access
import numpy
import pickle


# ----- Coding Tables ----- #

# Low-Entropy Code Input Symbo Limit and Threshold (Table 5-16)
# Code index, i || Input Simbol Limit, Li || Threshold, Ti
INPUT_SYMBOL_LIMIT_AND_THRESHOLD_TABLE_PATH = 'CodingTables/LowEntropyCodeInputSymbolLimitAndThreshold.pickle'

# Code tables (Input to output)
# List. Element index = Code index
# Each list element is a dictionary with 'key' = 'input codeword'
INPUT_TO_OUTPUT_CODEWORDS = 'CodingTables/CodingTable.pickle'

# Flush tables (Input to output)
# List. Element index = Code index
# Each list element is a dictionary with 'key' = 'input codeword'
FLUSH_INPUT_TO_OUTPUT_CODEWORDS = 'CodingTables/FlushCodingTable.pickle'






# gamma_0
#   Initial count exponent
#   Ingeter value
#   1 <= ɣ(0) <= 8

# gamma
#   Rescaling counter size parameter
#   Ingeter value
#   max{4, ɣ(0)+1} <= ɣ^* <= 11

# Umax
#   Unary Length Limit (Umax)
#   Ingeter value
#   8 <= Umax <= 32

# Sigma_0
#   Initial High-Resolution Accumulator Value (Σz(0)) 
#   Integer value or list with Nz integer values. 
#   0 <= Σz(0) <= 2^(D+ɣ(0))

class HybridCoder():

    def __init__(self):

        # Coding Tables
        self.Table_InputSimbolLimitAndThreshold = None
        self.Table_InputToOutputCodeWords = None
        self.Table_FlushInputToOutputCodeWords = None
        self.loadCodingTables()

        # Coder variables
        #   Dynamic range in bits (D)
        self.dynamicRangeInBits = None
        #   Initial count exponent (1 <= ɣ(0) <= 8)
        self.gamma_0 = None 
        #   Counter: Γ(0) = 2^ɣ(0)
        self.Gamma = None
        #   High-Resolution accumulator: 0 <= Σ(0) <= 2^(D+ɣ(0))
        self.Sigma = None
        #   User define initial value for Sigma for each spectral band (may be a single integer or a list with Nz elements)
        self.Sigma_0 = None      
        #   Rescaling counter size parameter: max{4, ɣ(0)+1} <= ɣ^* <= 11
        self.gamma = None  
        #   Threshold: T(0) (page 5-23 - Table 5-16)
        self.T0 = self.Table_InputSimbolLimitAndThreshold[0][2]
        #   Unary Length Limit: 8 <= Umax <= 32
        self.Umax = None
        #   Active prefix for the low entropy coder
        self.ActivePrefix = None

        # Bitstream variables
        self.bitStream = None       # bytearray with the already completely coded bytes
        self.currentByte = None     # byte being coded (still uncompleted)
        self.writtenBits = None     # number of bits already written into the current byte
        self.outputWordSize = None  # Not really needed but specified in the CCSDS123 Standard

        # Input vector variables
        self.inputLength = None

        # Initialize the coding parameters to the default values
        self.setConfigurationParameters()


       
         



    # ----- Utils general functions ----- #


    # Clip function
    def clip(self, x, minVal, maxVal):
        return min(max(minVal, x), maxVal)


    # Load the coding files from the pickle files
    def loadCodingTables(self):
        # Low-Entropy Code Input Symbo Limit and Threshold
        filePath = INPUT_SYMBOL_LIMIT_AND_THRESHOLD_TABLE_PATH
        filePointer = open(filePath, 'rb')
        self.Table_InputSimbolLimitAndThreshold = pickle.load(filePointer)
        filePointer.close()
        # Code tables (Input to output)
        filePath = INPUT_TO_OUTPUT_CODEWORDS
        filePointer = open(filePath, 'rb')
        self.Table_InputToOutputCodeWords = pickle.load(filePointer)
        filePointer.close()
        # Flush tables (Input to output)
        filePath = FLUSH_INPUT_TO_OUTPUT_CODEWORDS
        filePointer = open(filePath, 'rb')
        self.Table_FlushInputToOutputCodeWords = pickle.load(filePointer)
        filePointer.close()


    # Write the binary string into the byte array bit by bit
    def writeBinaryStringToBitStream(self, binaryString):
        nBits = len(binaryString)
        for bit in binaryString:
            self.currentByte = (self.currentByte << 1) | (int(bit) & 0x1)
            self.writtenBits = self.writtenBits + 1
            if self.writtenBits == 8:
                self.bitStream.append(self.currentByte)
                self.currentByte = 0
                self.writtenBits = 0


    # Add the 'padingValue' to the last byte of the bitstream until completing it
    def padding(self, padingValue):
        # PadingValue: '0' or '1'
        binaryString = padingValue
        while self.writtenBits != 0:
            self.writeBinaryStringToBitStream(binaryString)      


    # Write the bitstream to a binary file
    def writeBitStreamToBinaryFile(self, filePath):
        # filePath: Complete path to the target output file
        filePointer = open(filePath, 'wb')
        filePointer.write(self.bitStream)
        filePointer.close()


    # Write an integer value to bitstream using specific number of bits
    def writeIntegerValueToBitstream(self, integerNumber, nBits):
        binaryString = bin(integerNumber)[2:].zfill(nBits)
        self.writeBinaryStringToBitStream(binaryString)









    # ----- Coder specific functions functions ----- #

    # Initialize varialbes
    def initializeCodingVariables(self):
        # Counter: Γ(0) = 2^ɣ(0)
        self.Gamma = 2**self.gamma_0  
        # High-Resolution accumulator 
        # 0 <= Σz(0) <= 2^(D+ɣ(0))
        Sigma_0_clipped = self.clip(self.Sigma_0, 0, 2**(self.dynamicRangeInBits+self.gamma_0)-1 )
        self.Sigma = Sigma_0_clipped  
        # Active prefix
        self.ActivePrefix = []
        for index in range(0, 16):
            self.ActivePrefix.append('')
        # Bitstream variables
        self.bitStream = bytearray()
        self.currentByte = 0
        self.writtenBits = 0


    # Generate Header
    def generateHeader(self, headerBinaryString):
        self.writeBinaryStringToBitStream(headerBinaryString)


    # CCSDS123 - GPO2 
    # Actions
    #   Codes the value 'j' using integer code index 'k' generating a binaryString
    #   Writes the corresponding binaryString to the output bitstream
    # Inputs:
    #   j: unsigned integer to be coded
    #   k: unsigned integer code index
    def GPO2_coding(self, j, k):
        # Coding
        if int(j/2**k) < self.Umax:
            # bitstream:
            #   k least significant bits of j
            #   followed by a 'one'
            #   followed by int(j/2^k) 'zeros'
            # Process
            #   Convert the decimal integer to binary format and remove the '0b' of the start
            binaryString = bin(j)[2:]
            #   Extract only the k least significant bits
            if k == 0:
                binaryString = ''
            elif len(binaryString) >= k:
                binaryString = binaryString[-k:]
            elif len(binaryString) < k:
                binaryString = binaryString.zfill(k)
            #   Add the required 'one'
            binaryString = binaryString + '1'
            #   Add the j/2^k 'zeros'
            nZeros = int(j/2**k)
            binaryString = binaryString + ''.zfill(nZeros)
        else:
            # bitstream:
            #   Binary representation of j using D-bits (D: Dynamic range in bits)
            #   followed by Umax 'zeros'
            # Process
            #   Convert the decimal integer to binary format and remove the '0b' of the start
            binaryString = bin(j)[2:]
            #   Append the number of required zeros at the start to complete the string with the specified length
            binaryString = binaryString.zfill(self.dynamicRangeInBits)
            #   Append the Umax zeros at the end
            binaryString = binaryString + ''.zfill(self.Umax)
        # Write the binary string to the bitstream
        self.writeBinaryStringToBitStream(binaryString)


    # Update the High Resolution Accumulator (Σ(t): Sigma) and the Counter (Γ(t): Gamma)
    def UpdateHighResolutionAccumulatorAndCounter(self, mappedResidual):
        # Evaluate the scaling condition
        if self.Gamma < 2**self.gamma - 1:
            #   No rescaling
            self.Sigma = self.Sigma + 4*mappedResidual
            self.Gamma = self.Gamma + 1
        else:
            # Rescaling, Add the least significant bit of Σ(t-1) to the bitstream
            # TIP: Σ(t-1) is self.Sigma before being updated
            binaryString = bin(self.Sigma)[-1:]
            self.writeBinaryStringToBitStream(binaryString)
            # Update the values (rescaling them)
            self.Sigma = int((self.Sigma + 4*mappedResidual + 1)/2)
            self.Gamma = int((self.Gamma + 1)/2)



    # Returns True: current mapped residual has to be processed as high-entropy
    # Returns False: current mapped residual has to be processed as low-entropy
    def EvaluateHighEntropyCondition(self):
        if self.Sigma * (2**14) >= self.T0 * self.Gamma:
            # Process current residual as high entropy
            return True
        else:
            # Process current residual as low entropy
            return False


    # TODO: TBD. Optimize this doing the loop in reverser order.
    # Process the mapped residual with the high-entropy processing
    def HighEntropyProcess(self, mappedResidual):
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
        self.GPO2_coding(mappedResidual, k_good)




    # TODO: TBD. Optimize this doing the loop in reverser order.
    # Process the mapped residual with the high-entropy processing
    def LowEntropyProcess(self, mappedResidual):
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
        # Get the Input Symbol 'l(t)'
        if mappedResidual <= Li:
            # TODO: TBD.
            # l: string with the hexadecimal value of the mapped residual
            l = hex(mappedResidual).split('x')[-1]
        else:
            # TODO: TBD.
            # l: Scape symbol 'X'
            l = 'X'
            # Write the residual value to the bitstream using the GPO2 function
            # Rk'(δ(t) - L(i) - 1) with k=0
            residualValue = mappedResidual - Li -1
            self.GPO2_coding(residualValue, 0)
        # Update the active prefix
        self.ActivePrefix[i] = self.ActivePrefix[i] + l.upper()
        # Get the current input-output code table (dict)
        # Check if the active prefix matches a complete codeword. If it does, add the 
        # active prefix to the output bitstream and clear the active prefix
        if self.ActivePrefix[i] in self.Table_InputToOutputCodeWords[i]:
            outputCodeWord = self.Table_InputToOutputCodeWords[i].get(self.ActivePrefix[i])
            self.writeBinaryStringToBitStream(outputCodeWord)
            self.ActivePrefix[i] = ''




    def codeImageTail(self):
        flushValues = []
        # Codify the remaining active prefix using the corresponding code index for each of them
        for i in range(0, 16):    
            flushOutputCodeWord = self.Table_FlushInputToOutputCodeWords[i].get(self.ActivePrefix[i])
            self.writeBinaryStringToBitStream(flushOutputCodeWord)  
            flushValues.append(flushOutputCodeWord)
        print(self.ActivePrefix)
        print(flushValues)
        # Codify Σ(t) as binary using 2+D+ɣ^* bits for each band in increasing order
        nBits = 2 + self.dynamicRangeInBits + self.gamma
        binaryString = bin(self.Sigma)[2:]
        binaryString = binaryString.zfill(nBits)
        self.writeBinaryStringToBitStream(binaryString)
        # Add a '1' to the bitstream
        self.writeBinaryStringToBitStream('1')
        # Padding '0' until completing the last byte
        self.padding('0')
        # Add 0 bytes until the number of bytes in the bitstream is multiple of the word size.
        # If it already is a multiple, add 'word size' bytes with 'zeros'
        # self.currentByte = 0
        # self.bitStream.append(self.currentByte)
        while len(self.bitStream) % self.outputWordSize != 0:
            self.bitStream.append(self.currentByte)





    def codeTargetMappedResidual(self, MappedResidualsMatrix, index):
        # Get the corresponding mapped residual
        mappedResidual = MappedResidualsMatrix[index]
        # Code first mapped residual a plain binary with D bits
        if index == 0:
            binaryString = bin(mappedResidual)[2:]
            binaryString = binaryString.zfill(self.dynamicRangeInBits)
            self.writeBinaryStringToBitStream(binaryString)
        else:
            # Update the high resolution accumulator and the counter
            self.UpdateHighResolutionAccumulatorAndCounter(mappedResidual)
            # Evaluate if the mapped residual should be processed as high or low entropy
            if self.EvaluateHighEntropyCondition():
                # High entropy processing
                self.HighEntropyProcess(mappedResidual)
            else:
                # Low entropy processing
                self.LowEntropyProcess(mappedResidual)





    # ----- Main processes ----- #



    def setConfigurationParameters(self, Umax=32, gamma=4, gamma_0=1, Sigma_0=32768):
        #   Unary Length Limit: 8 <= Umax <= 32
        self.Umax = self.clip(Umax, 8, 32) 
        #   Initial count exponent (1 <= ɣ(0) <= 8)
        self.gamma_0 = self.clip(gamma_0, 1, 8)  
        #   Rescaling counter size parameter: max{4, ɣ(0)+1} <= ɣ^* <= 11
        self.gamma = self.clip(gamma, max(4, gamma_0+1), 11)   
        #   User define initial value for Sigma for each spectral band (may be a single integer or a list with Nz elements)
        self.Sigma_0 = Sigma_0   
        



    def code(self, dynamicRangeInBits, headerBinaryString, outputFilePath, MappedResidualsMatrix, outputWordSize=1):

        # Set the input variables
        #   Dynamic range (D)
        self.dynamicRangeInBits = dynamicRangeInBits
        #   Output word size
        self.outputWordSize = outputWordSize

        # Get the array shape
        self.inputLength = MappedResidualsMatrix.size

        # Initialize the coding variables
        self.initializeCodingVariables()

        # Generate header
        self.generateHeader(headerBinaryString)

        # Code each mapped residual 
        for index in range(0, self.inputLength):
            # Code the mapped residual
            self.codeTargetMappedResidual(MappedResidualsMatrix, index)

        # Bits coded pre tail codification
        print('pre tail ' + str(len(self.bitStream)))

        # Code image tail
        self.codeImageTail()

        print('post tail ' + str(len(self.bitStream)))

        # Write bitstream to file
        self.writeBitStreamToBinaryFile(outputFilePath)

        # Display coding compression ratio
        outputBits = 8 * len(self.bitStream)
        inputBits = self.inputLength * self.dynamicRangeInBits
        codingCompressionRatio = inputBits / outputBits
        codingCompressionRatio = round(codingCompressionRatio, 2)
        print('Coding compression ratio: {}'.format(codingCompressionRatio))

