function [Pixels, Projections, averagePixel] = HyperLCA_Prediction_Mapper(Pixels, Projections, averagePixel, DR_pixels, DR_Projections)

    %% Get the number of output mapped residuals to be obtained
    
    [nb, pmax] = size(Pixels);
    np = size(Projections,1);
    
      
    %% Carry out the prediction mapping process
        
    % Centroid 
    xMin = 0;
	xMax = 2^DR_pixels -1;
    averagePixelBU = averagePixel;
    for i = 2:nb
        averagePixel(i) = mapPredictedValue(xMin, xMax, averagePixelBU(i),  averagePixelBU(i-1));
    end
    
    % Pixels 
    xMin = 0;
	xMax = 2^DR_pixels -1;
    PixelsBU = Pixels;
    for p = 1:pmax
        for i = 2:nb
            Pixels(i,p) = mapPredictedValue(xMin, xMax, PixelsBU(i,p),  PixelsBU(i-1,p));
        end
    end
    
    % Projections 
    xMin = 0;
	xMax = 2^DR_Projections -1;
    ProjectionsBU = Projections;
    for p = 1:pmax
        for j = 2:np
            Projections(p, j) = mapPredictedValue(xMin, xMax, ProjectionsBU(p, j),  ProjectionsBU(p, j-1));
        end
    end
       
return



function [MR] = mapPredictedValue(xMin, xMax, v, pv)

    % v: value to be mapped
    % pv: predicted value

    prediction 	= pv;
    increment	= v - prediction;        
    tita = min(prediction - xMin, xMax - prediction);

    if 0 <= increment && increment <= tita
        state = 1;
        MR = 2 * increment;
    else
        if -tita <= increment && increment < 0    
            state = 2;
            MR = 2 * abs(increment) - 1;
        else
            state = 3;
            MR = tita + abs(increment);
        end
    end
    
    %disp(['v(i) = ',num2str(v),'  v(i-1) = ',num2str(pv),'  state = ', num2str(state),'  MR = ', num2str(MR)])

return
