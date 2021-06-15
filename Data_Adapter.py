import numpy as np

class Adapter():

    def __init__(self, CentroidPath, PixelsPath, ProjectionsPath):

        # Data paths
        self.Centroid_Path = CentroidPath
        self.Pixels_Path = PixelsPath
        self.Projections_Path = ProjectionsPath

        # Input vectors
        self.PM_Centroid = None
        self.PM_Pixels = None
        self.PM_Projections = None

        # Number of bands
        self.nBands = None
        # Number of endmembers
        self.endMembers = None
        # Blocksize
        self.blockSize = None

        # Load the data specified
        self.LoadData()

        # Get input characteristics
        self.GetInputCharacteristics()




    # Load the data from the vectors specified in the diferent data paths
    def LoadData(self):
        self.PM_Centroid = np.load(self.Centroid_Path)
        self.PM_Pixels = np.load(self.Pixels_Path)
        self.PM_Projections = np.load(self.Projections_Path)


    # Get the number of bands captured by the hyperspectral camera,
    # the  number of endmembers obtained by the hyperLCA transform
    # and the block size utilized 
    def GetInputCharacteristics(self):
        self.nBands = self.PM_Centroid.size
        self.endMembers = self.PM_Pixels.shape[1]
        self.blockSize = self.PM_Projections.shape[1]

    
    # Concatenate PM_Centroid, PM_Pixels and PM_Projections into a single 1D array
    # PM_Centroid     -> (nBands, 1)
    # PM_Pixels       -> (nBands, endMembers)
    # PM_Projections  -> (endMembers, blockSize)
    # outVector       -> [PM_Centroid + PM_Pixels(nBands,endMember1) + PM_Projections(endMember1, blockSize) + ....
    #                       + PM_Pixels(nBands,endMemberN) + PM_Projections(endMemberN, blockSize)]
    def AdaptInputTo1DVector(self):
        accumulatedData = self.PM_Centroid.flatten()
        for i in range(0, self.endMembers):
            subPixels = self.PM_Pixels[:, i].flatten()
            subProjections = self.PM_Projections[i, :]
            outVector = np.concatenate((accumulatedData, subPixels, subProjections), axis = 0)
            accumulatedData = outVector
        return outVector.astype(int)


    # Compare the 1D vector used as input for the hybrid coder with the 1D vector obtained from the hybrid decoder
    def CompareVectors(self, inputVector, outputVector):
        equal = False
        sum = 0
        for i in range(0, inputVector.size):
            sum += inputVector[i] - outputVector[i]

        if sum == 0:
            equal = True

        return equal
            
