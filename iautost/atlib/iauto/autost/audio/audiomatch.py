import numpy as np
import scipy.ndimage
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import hashlib
import librosa


from autost.audio.fingerprint import fingerprint, finger_matches


#from dtw import dtw
from numpy.linalg import norm
from autost.audio.vad import SimpleVad
from autost.audio.dtw import accelerated_dtw

DEFAULT_FS = 16000
DEFAULT_WINDOW_SIZE = 1024
DEFAULT_OVERLAP_RATIO = 0.5
MFCC_THRESHOLD = 100

MIN_PEAK_VALUE = 10
MAX_PEAK_VALUE = 100

class AudioMatch:

    '''
    For vad just support integer,librosa just suport float.
    So here,we need change interger to float.
    '''
    def preproccess_data(self,data,Fs=DEFAULT_FS):

        max_dtype = np.iinfo(data.dtype).max
        max_data = max(abs(data))

        if max_data < 0.9 * max_dtype :
            scale = int (0.9 * max_dtype / max_data)            
            data = scale * data

        simple_vad = SimpleVad()        
        data = data.copy(order = "C")
        data = simple_vad.remove_fade(data)         
        buf = librosa.util.buf_to_float(data)
        if Fs != DEFAULT_FS :
            buf = librosa.resample(buf,Fs,DEFAULT_FS) 
        
        return buf

    def get_features(self, data, Fs=DEFAULT_FS,
                wsize=DEFAULT_WINDOW_SIZE,
                wratio=DEFAULT_OVERLAP_RATIO) :
        
        features = {}                   
        if len(data) < int(DEFAULT_FS / 2):
            peaks = self.get_peaks(data,Fs, wsize, wratio)
            features["peaks"] = peaks
        else:
            features["mfcc"] = self.get_mfcc(data,Fs)
        return features

    def match_features(self, features, match_features):            
        if "peaks" in features and "peaks" in match_features:               
            if self.match_peaks(features["peaks"],match_features["peaks"]) :
                return True
        elif "mfcc" in features and "mfcc" in match_features:               
            return self.match_mfcc(features["mfcc"],match_features["mfcc"])
        return False

    '''        
    def match_audio(self,data,test_data,
                    data_fs=DEFAULT_FS,
                    test_data_fs=DEFAULT_FS):
        if len(data) < DEFAULT_FS:
            if self.match_short_audio(data,test_data,data_fs,test_data_fs):
                return True
        
        hashes = fingerprint(data,data_fs)
        test_hashes = fingerprint(test_data,test_data_fs)        
        return finger_matches(hashes,test_hashes)
    '''    
    
    def get_peaks(self,data,Fs=DEFAULT_FS,
                wsize=64,
                wratio=1):
        """
        window = np.hanning(wsize)
        
        stft  = librosa.core.spectrum.stft(data,
                            n_fft = wsize, 
                            hop_length = int(wsize*wratio), 
                            window=window)
        stft  = 2 * np.abs(stft) / np.sum(window)

        # get the middle data
        sign = stft[:, stft.shape[1] -1] 
        """
                
        #_,_,arr2D= scipy.signal.stft(
        #    buf,
        #    nperseg=wsize,
        #    window='hanning',
        #    fs=Fs,            
        #    noverlap=int(wsize * wratio))


        window = np.hanning(wsize)
        arr2D  = librosa.core.spectrum.stft(data,
                n_fft = wsize, 
                hop_length = int(wsize*wratio), 
                window=window)
        
        arr2D  = 2 * np.abs(arr2D) / np.sum(window)        
        arr2D = arr2D.sum(axis=1)

        #plt.plot(arr2D)
        #plt.show()
        peaks, _ = scipy.signal.find_peaks(arr2D,
                         height = max(arr2D) / 2, distance = 3)    
        filter_peaks = peaks[(peaks >= MIN_PEAK_VALUE) & (peaks <= MAX_PEAK_VALUE)]
        if len(filter_peaks) > 0 :
            peaks = filter_peaks
        #peak = np.argmax(arr2D)     
        print("peaks:",peaks)           
        return len(data),peaks

    '''
    def match_short_audio(self, data, test_data,
                data_fs = DEFAULT_FS,
                test_data_fs = DEFAULT_FS,
                wsize=DEFAULT_WINDOW_SIZE,
                wratio=DEFAULT_OVERLAP_RATIO
                ):
        
        data_peaks = self.get_peaks(data,data_fs,wsize,wratio)            
        test_data_peaks = self.get_peaks(test_data,test_data_fs,wsize,wratio)        
        
        return self.match_peaks(data_peaks,test_data_peaks)
    '''    
    def match_peaks(self, left_peaks, right_peaks) :
        
        left_len,left_peak = left_peaks
        right_len,right_peak = right_peaks

        if ( abs(left_len - right_len) > left_len or
            abs(left_len - right_len) > right_len ):
            return False
        
        if len(left_peak) <=0  or len(right_peak) <= 0:
            return False

        if abs(len(left_peak) - len(right_peak)) > 2 :
            return False

        if len(left_peak) < len(right_peak):
            short_peaks = left_peak
            long_peaks = right_peak
        else:
            short_peaks = right_peak
            long_peaks = left_peak
        
        for peak in short_peaks:
            match = False
            for match_peak in long_peaks:
                if abs(peak - match_peak) < 3:
                    match = True
            if not match:
                return False
        
        return True



    def get_mfcc(self,data,Fs = DEFAULT_FS) :
        return librosa.feature.mfcc(data,Fs).T

    def match_mfcc(self,left_mfcc,right_mfcc):
        #print("left_mfcc:",left_mfcc)
        #print("right_mfcc:",right_mfcc)
        dist, _, _, path = accelerated_dtw(left_mfcc, right_mfcc, dist=lambda x, y: norm(x - y, ord=1))        
        match = dist < MFCC_THRESHOLD
        if not match and dist < MFCC_THRESHOLD + 50 :
            match = (path[0] == path[1]).all()
        return match


if __name__ == '__main__': 

    import soundfile as sf
    
    #window_size = 1024
    #window = np.hanning(window_size)
    #hop_length = 512 
    data1, sr1 = sf.read('returnVR.wav', dtype='int16')      
    
    data2, sr2 = sf.read('t_1.wav', dtype='int16') 
    
    print("max(data2):", max(data2))
    
    #data1, sr1 = librosa.load('4.wav',sr=16000)             
    #data2, sr2 = librosa.load('4_r.wav',sr=16000)       
    
    audio_match = AudioMatch()
    
    data1 = audio_match.preproccess_data(data1,sr1)
    data2 = audio_match.preproccess_data(data2,sr2)

    print("len(data1):", len(data1))
    print("len(data2):", len(data2))
    print("max(data2):", max(data2))
    feature1 = audio_match.get_features(data1)
    feature2 = audio_match.get_features(data2)

    
    
    print(audio_match.match_features(feature1,feature2))
    
   
    #data = librosa.util.buf_to_float(data)

    #data = librosa.resample(data,22050,16000)

    #data1 = librosa.util.buf_to_float(data1)

    #print(audiomatch.match_audio(data,data1,sr1,sr2))
    