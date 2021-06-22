function [ Pixels, Projections, averagePixel ] = HyperLCA_Transform( ImgBlock, pmax, DR_Projections )


    %% Inputs

    % ImgBlock -> Hyperspectral image pixels placed in columns (nb x np)
    % pmax -> Number of pixels and projection vectors to be calculated
    

    %% Initialization 
    
    Pixels = [];
    Projections = [];
    
    % Auxiliary copy of the image
        
    AuxImgBlock = ImgBlock;
       
    % Sum the average pixel to the entire image

    [~, np] = size(ImgBlock);

    averagePixel = double(int16(mean(ImgBlock, 2)));
    ImgAverage = averagePixel * ones(1,np);
    ImgBlock = ImgBlock - ImgAverage;

    % Select the first endmember as the brighest pixel of the image

    ImgError = sum(ImgBlock.^2,1);
    [~, maxIndex] = max(ImgError);

    q = ImgBlock(:,maxIndex);
    u = q / (q'*q);

    % Compressed data to be send: maxIndex

    Pixels = [Pixels, AuxImgBlock(:,maxIndex)];
      
    projection = u' * ImgBlock;   
    Projections = [Projections; projection];

    
    %% Loop (Compressing process)

    for j=2:1:pmax   
                       
        % Select the next vector 
        
        ImgBlock = ImgBlock - q * projection;
        ImgError = sum(ImgBlock.^2,1);
        [~, maxIndex] = max(ImgError);
        
        q = ImgBlock(:,maxIndex);
        u = q / (q'*q);
 
        % Compressed staff to be send: maxIndex

        Pixels = [Pixels, AuxImgBlock(:,maxIndex)];
        
        projection = u' * ImgBlock;
        Projections = [Projections; projection];
        
        
    end   

    
    % Scaling projection vectors
    scalingFactor = (2^(DR_Projections-1)-1);
    Projections = floor((Projections + 1) * scalingFactor);

end

