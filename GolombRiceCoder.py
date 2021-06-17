
import numpy
import struct
import math



class GolombRiceCoder:

    def __init__(self):
        self.verbose = False
        self.logFile = None
        self.fileOut = None
        self.writtenBytes = None


    # ---- Compressor functions ---- #

    def increaseWrittenBytes(self): 
        self.writtenBytes += 1

    def writeIntToUnary(self, currentByte, writtenBits, integerNumber):
        # Write a set of bits with value 1 equal to the integer number -1
        for i in range(integerNumber-1, -1, -1):
            #currentByte = currentByte | (int(1) << (7 - writtenBits))
            currentByte = currentByte | (0x1 << (7 - writtenBits))
            writtenBits = writtenBits + 1
            if writtenBits >= 8:
                self.fileOut.write(struct.pack('B', currentByte))
                currentByte = 0
                writtenBits = 0
                self.increaseWrittenBytes()
        # Add one extra bit with value 0
        #currentByte = currentByte | (int(0) << (7 - writtenBits))
        currentByte = currentByte | (0x0 << (7 - writtenBits))
        writtenBits = writtenBits + 1
        if writtenBits >= 8:
            self.fileOut.write(struct.pack('B', currentByte))
            currentByte = 0
            writtenBits = 0
            self.increaseWrittenBytes()
        # Return the updated values
        return currentByte, writtenBits



    def writeIntToBinary(self, currentByte, writtenBits, integerNumber, numberOfBitsToBeUsed):
        # Write the specified integer n umber in binary using the specified number of bits
        for i in range(numberOfBitsToBeUsed-1, -1, -1):
            bitToWrite = ((integerNumber >> i) & 0x01)
            position = (7 - writtenBits)
            currentByte = currentByte | (bitToWrite << position)
            writtenBits = writtenBits + 1
            if writtenBits >= 8:
                self.fileOut.write(struct.pack('B', currentByte))
                currentByte = 0
                writtenBits = 0
                self.increaseWrittenBytes()
        # Return the updated values
        return currentByte, writtenBits


    def paddingByte(self, currentByte, writtenBits):
        integerNumber = 0
        numberOfBitsToBeUsed = 8 - writtenBits
        (currentByte, writtenBits) = self.writeIntToBinary(currentByte, writtenBits, integerNumber, numberOfBitsToBeUsed)
        remainder = self.writtenBytes % 2
        if remainder != 0:
            integerNumber = 0
            numberOfBitsToBeUsed = 8
            (currentByte, writtenBits) = self.writeIntToBinary(currentByte, writtenBits, integerNumber, numberOfBitsToBeUsed)
        return currentByte, writtenBits


    def code(self, vector, dynamicRange, outputFilePath, logFilePath=None):

        self.fileOut = open(outputFilePath, 'wb')
        
        self.verbose = False
        if logFilePath != None:
            self.logFile = open(logFilePath, 'w')
            self.verbose = True

        # Get the MTac size
        nElements = vector.shape[0]
        # Coding parameters
        self.writtenBytes = 0
        currentByte = 0
        writtenBits = 0
        # Calculate the coding parameter M (Mean value of the mapped tac)
        M = int(numpy.mean(vector))
        M = max(M, 1) # Protection in case M == 0
        # Write the M value in the bitstream as binary code
        integerNumber = M
        numberOfBitsToBeUsed = dynamicRange 
        (currentByte, writtenBits) = self.writeIntToBinary(currentByte, writtenBits, integerNumber, numberOfBitsToBeUsed)
        # Get the first power of two (b) bigger than M (b = floor(log2(M))+1)
        b = int(math.floor(math.log2(M))+1)
        difference =  2**b - M

        # TODO: Checking
        if self.verbose:
            print('M = {}'.format(M), file=self.logFile)
            print('b = {}'.format(b), file=self.logFile)
            print('difference = {}'.format(difference), file=self.logFile)
            print('writtenBytes, writtenBits = {}, {}'.format(self.writtenBytes, writtenBits), file=self.logFile)


        # Code each pixel in vector one by one
        for index in range(0, nElements):
            # Get the data to be written in the bitsream
            q = int(vector[index]) // M # Division Quotient
            r = int(vector[index]) % M  # Division Reminder
            if r < difference:
                rBits = b - 1
                rCode = r
            else:
                rBits = b
                rCode = r + difference
            # Write the data in the bitstream
            #   Write q in unary code
            integerNumber = q
            (currentByte, writtenBits) = self.writeIntToUnary(currentByte, writtenBits, integerNumber)
            #   Write r in binary code
            integerNumber = rCode
            numberOfBitsToBeUsed = rBits
            (currentByte, writtenBits) = self.writeIntToBinary(currentByte, writtenBits, integerNumber, numberOfBitsToBeUsed)

            # TODO: Checking
            if self.verbose:
                print('(index) = ({}) | value = {} | (q, r) = ({}, {}) | (rCode, rBits) = ({}, {}) | (writtenBytes, writtenBits) = ({}, {})| currentByte = {}'.format(index, int(vector[index]), q, r, rCode, rBits, self.writtenBytes, writtenBits, currentByte), file=self.logFile)


        # Add 0 to complete the last byte (Padding)
        (currentByte, writtenBits) = self.paddingByte(currentByte, writtenBits)

        self.fileOut.close()

        if self.verbose:
            self.logFile.close()






# ---- Decoder functions ---- #

    def getSizeOfFile(self, filePath):
        filePointer = open(filePath, 'rb')
        filePointer.seek(0,2) # move the cursor to the end of the file
        size = filePointer.tell()
        filePointer.close()     
        return size

    # Function for checking if the current bit is 1 or 0.
    def checkCurrentBit(self, byteList, readBytes, readBits):
        currentBitValue = (byteList[readBytes] >> (7-readBits)) & 0x1
        return currentBitValue;


    def readIntFromUnary(self, byteList, readBytes, readBits):
        # Read and increase the value while the bits in the bitstream are 1 
        # (also remove them from the bitstream)
        readValue = 0
        while (self.checkCurrentBit(byteList, readBytes, readBits) == 1):
            readValue = readValue + 1
            readBits = readBits + 1
            if readBits >= 8:
                readBytes = readBytes + 1
                readBits = 0
        # When the checked bit is 0, also increment the read bits
        readBits = readBits + 1
        if readBits >= 8:
            readBytes = readBytes + 1
            readBits = 0
        # return the updated values
        return readBytes, readBits, readValue


    # Method for getting an integer value from a part of a bitsream coded as binary and return it
    # This method does not increment the readBits and do not increase the values of the read bits and bytes
    def checkIntFromBinary(self, byteList, readBytes, readBits, numberOfBitsToBeUsed):
        checkedBits = readBits
        checkedBytes = readBytes
        readValue = 0
        for i in range(0, numberOfBitsToBeUsed):
            bitToRead = ( byteList[checkedBytes] >> (7-checkedBits) ) & 0x1
            position = (numberOfBitsToBeUsed-1-i)
            readValue = readValue + (bitToRead << position)
            checkedBits = checkedBits + 1
            if checkedBits >= 8:
                checkedBits = 0
                checkedBytes = checkedBytes + 1
        # Return the read value
        return readValue


    # Method for getting an integer value from a part of a bitsream coded as binary and return it
    def readIntFromBinary(self, byteList, readBytes, readBits, numberOfBitsToBeUsed):
        readValue = 0
        for i in range(0, numberOfBitsToBeUsed):
            bitToRead = ( byteList[readBytes] >> (7-readBits) ) & 0x1
            position = (numberOfBitsToBeUsed-1-i)
            readValue = readValue + (bitToRead << position)
            readBits = readBits + 1
            if readBits >= 8:
                readBits = 0
                readBytes = readBytes + 1
        # return the updated values
        return readBytes, readBits, readValue 


    # Method for for incrementing the number of readBytes and readBits
    def incrementReadBits(self, readBytes, readBits, numberOfBitsToBeIncremented):
        for i in range(0, numberOfBitsToBeIncremented):
            readBits = readBits + 1
            if readBits >= 8:
                readBits = 0
                readBytes = readBytes + 1
        # return the updated values
        return readBytes, readBits 


    # Decoder
    def decodeBitstream(self, byteList, nElements, dynamicRange):
        # Decoder parameters
        decodedIntegerValue = 0
        readBytes = 0
        readBits = 0
        vector = numpy.zeros((nElements))
        # First read the M value (binary code)
        numberOfBitsToBeUsed = dynamicRange
        (readBytes, readBits, readValue) = self.readIntFromBinary(byteList, readBytes, readBits, numberOfBitsToBeUsed)
        M = readValue
        # Get the first power of two (b) bigger than M (b = floor(log2(M))+1)
        b = int(math.floor(math.log2(M))+1)
        difference =  2**b - M


        # TODO: Checking
        if self.verbose:
            print('M = {}'.format(M), file=self.logFile)
            print('b = {}'.format(b), file=self.logFile)
            print('difference = {}'.format(difference), file=self.logFile)
            print('readBytes, readBits = {}, {}'.format(readBytes, readBits), file=self.logFile)
        

        # Decode each pixel in MTac one by one
        for index in range(0, nElements):
            # Get the q value (unary code)
            (readBytes, readBits, readValue) = self.readIntFromUnary(byteList, readBytes, readBits)
            q = readValue
            # read the 2 possible rCode and accordingly obtain the r value(binary code)
            #   Check coded as b-1 bits. The obtained integer value should be smaller than "difference"
            numberOfBitsToBeUsed = b-1
            readValue = self.checkIntFromBinary(byteList, readBytes, readBits, numberOfBitsToBeUsed)
            rCode = readValue
            if rCode < difference:
                r = rCode
                numberOfBitsToBeIncremented = b-1
                (readBytes, readBits) = self.incrementReadBits(readBytes, readBits, numberOfBitsToBeIncremented)
            else:
                numberOfBitsToBeUsed = b
                (readBytes, readBits, readValue) = self.readIntFromBinary(byteList, readBytes, readBits, numberOfBitsToBeUsed)
                rCode = readValue
                r = rCode - difference
            # Obtain the corresponding integer value using q, r and M
            vector[index] = q * M + r;

            # TODO: Checking
            #print('(row, col) = ({}, {}) | value = {} | (q, r) = ({}, {}) | (rCode, rBits) = ({}, {}) | (readBytes, readBits) = ({}, {})| currentByte = {}'.format(row, col, int(DMTac[row, col]), q, r, rCode, numberOfBitsToBeUsed, readBytes, readBits, byteList[readBytes+1]), file=logFile)

            # TODO: Checking
            #print('row, col = {}, {}  --- read bytes = {}'.format(row, col, readBytes))

        # return the decoded mapped tac
        return vector


    def decode(self, filePath, dynamicRange, nElements, logFilePath=None):

        self.verbose = False
        if logFilePath != None:
            self.logFile = open(logFilePath, 'w')
            self.verbose = True

        # Get the number of bytes in the file
        nBytesInBitstream = self.getSizeOfFile(filePath)
        # Read the bytes to a python list one by one
        byteList = []
        filePointer = open(filePath, 'rb')
        for byteIndex in range(0, nBytesInBitstream):
            currentByte = struct.unpack('B', filePointer.read(1))[0] 
            byteList.append(currentByte)
        filePointer.close()
        # Decode the bistream
        decodedVector = self.decodeBitstream(byteList, nElements, dynamicRange)
        # Cast data to integer
        decodedVector = decodedVector.astype('uint16')
        return decodedVector