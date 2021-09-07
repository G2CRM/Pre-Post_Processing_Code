# -*- coding: utf-8 -*-
"""
Created on Wed Aug 18 13:07:07 2021

@author: Trenton Saunders

------ G2CRM: Stage Frequency Curve Calculation ----------

**** USER NOTE: This code will only work if the correct columns are extraced from the "ModeledAreaStormDetail" .csv file .
 Please check that the correct columns are being retrived when the variable 'data' is defined (Column Data:  Iteration #, Days from Start of Iteration, Storm Surge, and Tide Data). ****

Description: This Python script was created to enable G2CRM Stage-Freq Post Processing across USACE. 
This code utilizes an empirical approach to calculate the mean & median Stage-Freq Curve, given "n" G2CRM simulations. The recurrence interval
on the x-axis is limited to the number of years run during each iteration. If larger reccurence interval  (e.g. 500 or 1000 years) estimates are needed 
the user should run G2CRM iteration over longer time scales.
A seperate solution could employ a Parametric approaches (Example: Gumbel Method) to extrapolate for more extreme recurrence intervals.

## Graphical Outputs include
1) plot of each G2CRM iteration stage freq curve (Surge + Tide & Surge Alone)
2) plot of the median & mean surge + tide
3) plot of the median & mean surge 
4) plot of 'Mean Surge + Tide','Mean Surge','Mean Tide'
5) plot of 'Median Surge + Tide','Median Surge','Median Tide'


"""



import numpy as np
import matplotlib.pyplot as plt


#### Import Initial File (USER Needs to adjust) ####

# This file should be found as output from G2CRM:  "ModeledAreaStormDetail" .csv file

file1 = r"C:\Users\Becca.LAPTOP-SSI4KM18\Desktop\ERDC\G2CRM\Studies\Fox Point\Trenton_Fox_Point_Storm_Mod_08052021\Outputs\Trenton_Fox_Point_Storm_Mod_08052021_-_default\Without Project Plan\fox_Stg_freq_08182021\ModeledAreaStormDetail_NoSLC_fox_Stg_freq_08182021.csv"

# Pull Iteration, Days from Start, Storm Surge, and Tide Data. 
# ****User needs to verify that the columns being used in python are correct***
data = np.genfromtxt(file1, skip_header = 1, usecols = (0,3,16,17), delimiter = ',')


#### Rest of the code should run without any user modifications ####

# Days to Years (Round up)
data[:,1] = np.ceil(data[:,1]/365)

# Create a Storm + Tide Surge Array
Surge_Tide = np.transpose(np.array( [data[:,2] + data[:,3]])) 

# Append Storm + Tide array to the "data" matrix
data = np.append(data, Surge_Tide, axis=1)

# Total Number of Iteration  
num_iterations = int(np.amax(data[:,0]))

# Number of years covered in the G2CRM iterations (this value can be wrong if a low number of iterations are run)
num_year = int(np.amax(data[:,1]) - 1)


## Calculate the Stage Curve in Each Iteration (Storm + Tide)

fig, axs = plt.subplots(2)
fig.suptitle('All G2CRM Iterations')
axs[0].title.set_text('Surge + Tide')
axs[0].set_ylabel('Stage (ft)')
axs[1].title.set_text('Surge')

# loop for all iterations
for j in range(1,num_iterations+1):
    
    #temp matrix with all data from the current iteration
    iter_temp = data[data[:,0]==j,:]
    
    
    # temp matrix that will store the max Surge + Tide value for each year in the iteration
    temp_year = np.transpose(np.matrix(np.arange(1,num_year+2)))
    temp_year = np.append(temp_year, np.matrix(np.zeros([np.size(temp_year),1])), axis=1)
   
    # temp matrix that will store the max Surge value for each year in the iteration   
    surge_year = np.transpose(np.matrix(np.arange(1,num_year+2)))
    surge_year = np.append(surge_year, np.matrix(np.zeros([np.size(surge_year),1])), axis=1)
    
    # loop for all years within iteration
    for i in temp_year[:,0].astype(int):
        
        
        # check if any storms occured in the "current" year. If so, pull the maximum surge + tide/surge value
        if np.any((iter_temp[:,1] == float(i)) == True):
           
            temp_year[i - 1,1] = max(iter_temp[iter_temp[:,1] == float(i),4])
            surge_year[i -1 ,1] = max(iter_temp[iter_temp[:,1] == float(i),2])
            
        # if no storms occured in the given year. Surge + Tide will be taken as 90 percentile tide event and surge = 0
        elif np.any((iter_temp[:,1] == float(i)) == False):
            
            temp_year[i - 1,1] = np.percentile(data[:,3],90)
            surge_year[i- 1,1] = 0
            
            
        
    # Sort the Surge + Tide events in descending order        
    temp_year   =    temp_year[np.lexsort(temp_year.T[::1])]
    temp_year = np.flip(temp_year, 1)
    temp_year = temp_year.reshape(temp_year.shape[0]* temp_year.shape[1],temp_year.shape[2])

    # Sort the Surge events in descending order 
    surge_year   =    surge_year[np.lexsort(surge_year.T[::1])]
    surge_year = np.flip(surge_year, 1)
    surge_year = surge_year.reshape(surge_year.shape[0]* surge_year.shape[1],surge_year.shape[2])
    
    # append an array from 1 to n_years + 1. This is the rank of storm events
    temp_year= np.append(temp_year, np.transpose(np.matrix(np.arange(1,num_year+2))), axis=1)
    surge_year= np.append(surge_year, np.transpose(np.matrix(np.arange(1,num_year+2))), axis=1)
    
    # Calculate the Recurrence Interval
    temp_year[:,2] = (num_year+1)/temp_year[:,2]
    surge_year[:,2] = (num_year+1)/surge_year[:,2]
    
    #subplot of each iterations calculated recurrence interval 
    axs[0].plot(temp_year[:,2], temp_year[:,1])
    axs[1].plot(surge_year[:,2], surge_year[:,1])
    
    # store the temporary recurrence intervals into a permanent matrix. This will be used to calculate the mean & median stage freq curve
    if j == 1:
        Final_Stage = temp_year[:,1]
        Final_Surge_Stage= surge_year[:,1]
    else:
        Final_Stage = np.append(Final_Stage, temp_year[:,1], axis=1)
        Final_Surge_Stage = np.append(Final_Surge_Stage, surge_year[:,1], axis=1)
     
        
# Mean stage freq curve
Mean_Stage_Curve = np.mean(Final_Stage,1)
Mean_Stage_Surge_Curve = np.mean(Final_Surge_Stage,1)

# Median stage freq curve
Median_Stage_Curve = np.median(Final_Stage,1)
Median_Stage_Surge_Curve = np.median(Final_Surge_Stage,1)

plt.ylabel('Stage (ft)')
plt.xlabel('Recurrence Interval (years)')

plt.show()
plt.close


fig
plt.plot(temp_year[:,2],Mean_Stage_Curve)
plt.plot(temp_year[:,2],Median_Stage_Curve)
plt.ylabel('Stage (ft)')
plt.xlabel('Recurrence Interval (years)')
plt.legend(['Mean','Median'])
plt.title('Stage Frequency Curve (Tide + Surge)')
plt.show()
plt.close


fig
plt.plot(temp_year[:,2],Mean_Stage_Surge_Curve)
plt.plot(temp_year[:,2],Median_Stage_Surge_Curve)
plt.ylabel('Stage (ft)')
plt.xlabel('Recurrence Interval (years)')
plt.legend(['Mean','Median'])
plt.title('Stage Frequency Curve (Surge Only)')
plt.show()
plt.close



fig
plt.plot(temp_year[:,2],Mean_Stage_Curve)
plt.plot(temp_year[:,2],Mean_Stage_Surge_Curve)
plt.plot(temp_year[:,2],Mean_Stage_Curve - Mean_Stage_Surge_Curve)
plt.ylabel('Stage (ft)')
plt.xlabel('Recurrence Interval (years)')
plt.legend(['Mean Surge + Tide','Mean Surge','Mean Tide'])
plt.title('Stage Frequency Curve (Mean Values)')
plt.show()
plt.close

fig
plt.plot(temp_year[:,2],Median_Stage_Curve)
plt.plot(temp_year[:,2],Median_Stage_Surge_Curve)
plt.plot(temp_year[:,2],Median_Stage_Curve - Median_Stage_Surge_Curve)
plt.ylabel('Stage (ft)')
plt.xlabel('Recurrence Interval (years)')
plt.legend(['Median Surge + Tide','Median Surge','Median Tide'])
plt.title('Stage Frequency Curve (Median Values)')
plt.show()
plt.close
