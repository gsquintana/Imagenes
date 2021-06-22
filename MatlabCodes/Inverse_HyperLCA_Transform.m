function [ decImgBlock ] = Inverse_HyperLCA_Transform( Pixels, Projections, averagePixel, DR_Projections)



%% Subtract the average pixel to the Pixels

Pixels = Pixels - averagePixel*ones(1,size(Pixels,2));


%% Get the Q and U vectors from the Pixel vectors (Gram-Schmidt orthogonalization)

Q(:,1) = Pixels(:,1);
U(:,1) = Pixels(:,1) / ( Pixels(:,1)' * Pixels(:,1) ); 

for j=2:1:size(Pixels,2)
    Pixels = Pixels - U(:,j-1) * ( Q(:,j-1)' * Pixels );
    Q = [Q, Pixels(:,j)];
    U = [U, Pixels(:,j) / ( Pixels(:,j)' * Pixels(:,j) )];
end



%% Creating the decompressed image as the average pixel

np = size(Projections,2);
ImgAverage = averagePixel * ones(1,np);
decImgBlock = ImgAverage;


% Scaling projection vectors
scalingFactor = (2^(DR_Projections-1)-1);
Projections = (Projections / scalingFactor) - 1;



%% Loop for decompressing the image

for j = 1:1:size(U,2)         
        decImgBlock = decImgBlock + Q(:,j) * Projections(j,:);
end









