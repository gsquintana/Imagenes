


class convertHexaFileToBinFile():

    # Constructor
    def __init__(self):
        self.currentByte = None
        self.writtenBits = None
        self.bitStream = None
        self.readBits = None
        self.currentByteIndex = None


    def initializeParameters(self):
        self.currentByte = 0
        self.writtenBits = 0
        self.bitStream = []
        self.readBits = 0
        self.currentByteIndex = 0


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


    # Read bitstream from binary file
    def readBitStreamFromBinaryFile(self, filePath):
        filePointer = open(filePath, 'rb')
        self.bitStream = filePointer.read()
        filePointer.close()


    # ---------- Main method --------- #
    def readBinaryFileAsString(self, filePath):
        # Read binary file
        conversionObject = convertHexaFileToBinFile()
        conversionObject.initializeParameters()
        conversionObject.readBitStreamFromBinaryFile(filePath)
        # Parse each binary value one by one and convert it to a binary string
        entireBinaryString = ''
        nBits = 8
        for hexa in range(0, len(conversionObject.bitStream)):
            binaryString = conversionObject.readBinaryStringFromBitStream(nBits, reverseReading=False)
            entireBinaryString = entireBinaryString + binaryString
        # Return the binary string
        return entireBinaryString






































