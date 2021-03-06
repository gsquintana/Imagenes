close all
clear all
clc


% Input parameters

imageFileName = 'AVIRIS_LunarLake_BIP_LE';
nr = 512; 
nc = 512;
nb = 224; 

desiredCR = 16;
blockSize = 1024;
DR_Pixels = 16;
DR_Projections = 12;
num_blocks = 1;


% Loading image

Img = multibandread(imageFileName, [nr, nc, nb], 'uint16', 0, 'bip', 'ieee-le');

gray = mean(Img, 3);
gray = (gray - min(gray(:))) / (max(gray(:)) - min(gray(:)));
figure
imshow(gray)



% Store the image as a single matrix (nb x np) for better processing it

np = nr*nc;
ImgVect = reshape(Img, np, nb)';




% Calculate pmax according to the input parameters

num = blockSize * nb * DR_Pixels / desiredCR - nb * DR_Pixels;
den = blockSize * DR_Projections + nb * DR_Pixels;
pmax = floor(num/den);


% Execute the HyperLCA compressor (just one image block for tests)
ImgBlock = ImgVect(:, 1:num_blocks * blockSize);
%   HyperLCA Transform
[Pixels, Projections, averagePixel] = HyperLCA_Transform( ImgBlock, pmax, DR_Projections );
%   HyperLCA Prediction Mapper
[Pixels, Projections, averagePixel] = HyperLCA_Prediction_Mapper(Pixels, Projections, averagePixel, DR_Pixels, DR_Projections);

% Store the predicted mapped data
PM_Pixels = Pixels;
PM_Projections = Projections;
PM_Centroid = averagePixel;
writeNPY(PM_Pixels, 'Data/PM_Pixels.npy');
writeNPY(PM_Projections, 'Data/PM_Projections.npy');
writeNPY(PM_Centroid, 'Data/PM_Centroid.npy');

% Execute the HyperLCA decompressor for verification (just one image block for tests)
%   Inverse HyperLCA Prediction Mapper
[Pixels, Projections, averagePixel] = Inverse_HyperLCA_Prediction_Mapper(Pixels, Projections, averagePixel, DR_Pixels, DR_Projections);
%   HyperLCA Inverse Transform
decImgBlock = Inverse_HyperLCA_Transform( Pixels, Projections, averagePixel, DR_Projections);
% Verification comparing one single pixel
pixelTestIndex = 512;
plot([ImgBlock(:,pixelTestIndex), decImgBlock(:,pixelTestIndex)])




