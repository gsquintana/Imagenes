function [Pixels, Projections, averagePixel] = Inverse_HyperLCA_Prediction_Mapper(Pixels, Projections, averagePixel, DR_pixels, DR_Projections)

    %% Get the number of output mapped residuals to be obtained
    
    [nb, pmax] = size(Pixels);
    np = size(Projections,1);
    
      
    %% Carry out the prediction mapping process
        
    % Centroid 
    xMin = 0;
	xMax = 2^DR_pixels -1;
    for i = 2:nb
        averagePixel(i) = imapPredictedValue(xMin, xMax, averagePixel(i),  averagePixel(i-1));
    end
    
    
    % Pixels 
    xMin = 0;
	xMax = 2^DR_pixels -1;
    for p = 1:pmax
        for i = 2:nb
            Pixels(i,p) = imapPredictedValue(xMin, xMax, Pixels(i,p),  Pixels(i-1,p));
        end
    end
    
    % Projections 
    xMin = 0;
	xMax = 2^DR_Projections -1;
    for p = 1:pmax
        for j = 2:np
            Projections(p, j) = imapPredictedValue(xMin, xMax, Projections(p, j),  Projections(p, j-1));
        end
    end
       
return


function [MR] = imapPredictedValue(xMin, xMax, v, pv)

    % v: value to be mapped
    % pv: predicted value
    
    prediction 	= pv;
    tita = min(prediction - xMin, xMax - prediction);
    absIncrement = abs(v - tita);
       
    if prediction + absIncrement <= xMax &&  prediction - absIncrement >= xMin % Small number
        % Division mod (check Odd / Couple)
        divisionMod = rem(v, 2);
        if divisionMod == 0 % Odd
            MR = prediction + v / 2;
        else % Couple
            MR = prediction - (v + 1) / 2;
        end
    else % Large number
        if prediction + absIncrement <= xMax
            MR = prediction + absIncrement;
        else
            MR = prediction - absIncrement;
        end
    end
        
return

