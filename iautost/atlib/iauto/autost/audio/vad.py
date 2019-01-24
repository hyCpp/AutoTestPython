#!/usr/bin/env python3
#
# Released under the HOT-BEVERAGE-OF-MY-CHOICE LICENSE: Bastian Rieck wrote
# this script. As long you retain this notice, you can do whatever you want
# with it. If we meet some day, and you feel like it, you can buy me a hot
# beverage of my choice in return.

import numpy as np
import scipy.io.wavfile
import scipy.stats
import sys


class SimpleVad():
    def __init__(self):
        # this value is got from windows 10 platform
        # the nosie has been cancelled by system microphoe
        self.max_value_threshold = 200
        pass
    
    def is_voice(self,signs):
        #print("simplevad::is_voice")
        #print(len(signs))        
        signs[abs(signs) < self.max_value_threshold] = 0
        return max(abs(signs)) > self.max_value_threshold

    def remove_fade(self, input_data):
        data = input_data.copy(order='C')
        if len(data) > 0:
            data[np.where(abs(data) < self.max_value_threshold)] = 0
            i = (data > 0).argmax()
            if i > 0 :
                input_data = np.delete(input_data,range(i))                            
            
            data = input_data[::-1].copy(order='C')
            if len(data) > 0:
              data[np.where(abs(data) < self.max_value_threshold)] = 0
              i = (data > 0).argmax()
              if i > 0 :    
                input_data = np.delete(input_data,range(len(input_data) - i,len(input_data)))            
    
        return input_data

    def get_valid_voice(self,list_data):

        valid_data = []        
        vad_data = []        
        for data in list_data:
            if self.is_voice(data):
              valid_data += vad_data
              valid_data.append(data)
              vad_data = []
            else:
              if (len(valid_data) > 0) : vad_data.append(data) 

        output_data = None

        for data in valid_data:
            if output_data is None:
                output_data = data 
            else :
                output_data = np.append(output_data,data)

        #if output_data is not None:
        #    return self.remove_fade_in(output_data)

        return output_data
      


if __name__ == '__main__':  
    
    import soundfile as sf
    outdata = np.ndarray([],dtype=np.int16)


    data,fs = sf.read("4.wav",dtype='int16')      
    print(len(data))    

    data[abs(data) < 100] = 0

    sf.write('4_new.wav', data, fs)
    
    #data = data.reshape( -1, 10)

    #for item in data:
    print(max(abs(data)))
    print(min(abs(data)))

    

    simple_vad = SimpleVad()
    list = []
    for item in data:        
        list.append(item)

    
    vdata = simple_vad.get_valid_voice(list)
    print(len(data) * 160)
    print(vdata)
    print(len(vdata))

