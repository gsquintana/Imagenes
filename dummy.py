import Data_Adapter
import pickle

import Coder_Hybrid_Mod as coder
import Decoder_Hybrid_rg as decoder

from GolombRiceCoder import * 


import numpy as np
import os



if(__name__ == "__main__"):


    print('\n\n Hybrid coder test \n\n ')

    # Data paths
    centroid = os.path.join('InputData','PM_Centroid.npy')
    pixels = os.path.join('InputData','PM_Pixels.npy')
    projections = os.path.join('InputData','PM_Projections.npy')
    # Adapt the input data to a 1D vector format
    adaptador = Data_Adapter.Adapter(centroid, pixels, projections)
    v = adaptador.AdaptInputTo1DVector(32)

    # Instantiate coder object
    codificador = coder.HybridCoder()
    # Code input vector
    codificador.code(16, '', os.path.join('OutputData','CodedData.npy'), v)
    print(v)
    # Decode coded vector
    decodificador = decoder.HybridDecoder()
    vDecoded = decodificador.decode(os.path.join('OutputData','CodedData.npy'), 32, 4, 1, 16, len(v))
    print(vDecoded)

    
    if(adaptador.CompareVectors(v, vDecoded)):
        print("Vectores iguales")
    else:
        print("Vectores diferentes")



    print('\n\n GolombRiceTest \n\n ')
    
    grCoderOutputFilePath = os.path.join('OutputData','grCodedData.bin') 
    grCoder = GolombRiceCoder()
    '''grCoder.code(adaptador.PM_Centroid.flatten(), 16, grCoderOutputFilePath)
    grCoder.code(adaptador.PM_Pixels.flatten(), 16, grCoderOutputFilePath)
    grCoder.code(adaptador.PM_Projections.flatten(), 16, grCoderOutputFilePath)'''
    grCoder.code(v, 16, grCoderOutputFilePath)
    compressionRatio = len(v)*2 / grCoder.getSizeOfFile(grCoderOutputFilePath)
    print('Coding compression ratio: {}'.format(round(compressionRatio, 2)))

    vDecoded = grCoder.decode(grCoderOutputFilePath, 16, len(v))

    print(v)
    print(vDecoded)
    if(adaptador.CompareVectors(v, vDecoded)):
        print("Vectores iguales")
    else:
        print("Vectores diferentes")



    