import Data_Adapter
import Coder_Hybrid_Mod as coder
import Decoder_Hybrid_Mod as decoder
import numpy as np

if(__name__ == "__main__"):

    # Data paths
    centroid = 'InputData\PM_Centroid.npy'
    pixels = 'InputData\PM_Pixels.npy'
    projections = 'InputData\PM_Projections.npy'
    # Adapt the input data to a 1D vector format
    adaptador = Data_Adapter.Adapter(centroid, pixels, projections)
    v = adaptador.AdaptInputTo1DVector()
    # Instantiate coder object
    codificador = coder.HybridCoder()
    # Code input vector
    codificador.code(16, '', 'OutputData\CodedData.npy', v)
    print(v)
    print(codificador.Sigma)
    print(codificador.Gamma)
    # Decode coded vector
    decodificador = decoder.HybridDecoder()
    vDecoded = decodificador.decode('OutputData\CodedData.npy', 32, 4, 1, 16, len(v))
    vDecoded = np.flip(vDecoded)
    print(vDecoded)

    if(adaptador.CompareVectors(v, vDecoded)):
        print("Vectores iguales")
    else:
        print("Vectores diferentes")