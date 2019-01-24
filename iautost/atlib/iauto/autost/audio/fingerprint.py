import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import (generate_binary_structure,
                                      iterate_structure, binary_erosion)
import hashlib
from operator import itemgetter
import math

from collections import defaultdict

IDX_FREQ_I = 0
IDX_TIME_J = 1

######################################################################
# Sampling rate, related to the Nyquist conditions, which affects
# the range frequencies we can detect.
DEFAULT_FS = 16000

######################################################################
# Size of the FFT window, affects frequency granularity
DEFAULT_WINDOW_SIZE = 128

######################################################################
# Ratio by which each sequential window overlaps the last and the
# next window. Higher overlap will allow a higher granularity of offset
# matching, but potentially more fingerprints.
DEFAULT_OVERLAP_RATIO = 0.5

######################################################################
# Degree to which a fingerprint can be paired with its neighbors --
# higher will cause more fingerprints, but potentially better accuracy.
DEFAULT_FAN_VALUE = 15

######################################################################
# Minimum amplitude in spectrogram in order to be considered a peak.
# This can be raised to reduce number of fingerprints, but can negatively
# affect accuracy.
DEFAULT_AMP_MIN = 10

######################################################################
# Number of cells around an amplitude peak in the spectrogram in order
# for Dejavu to consider it a spectral peak. Higher values mean less
# fingerprints and faster matching, but can potentially affect accuracy.
PEAK_NEIGHBORHOOD_SIZE = 20

######################################################################
# Thresholds on how close or far fingerprints can be in time in order
# to be paired as a fingerprint. If your max is too low, higher values of
# DEFAULT_FAN_VALUE may not perform as expected.
MIN_HASH_TIME_DELTA = 0
MAX_HASH_TIME_DELTA = 200

######################################################################
# If True, will sort peaks temporally for fingerprinting;
# not sorting will cut down number of fingerprints, but potentially
# affect performance.
PEAK_SORT = True

######################################################################
# Number of bits to throw away from the front of the SHA1 hash in the
# fingerprint calculation. The more you throw away, the less storage, but
# potentially higher collisions and misclassifications when identifying songs.
FINGERPRINT_REDUCTION = 20


BUCKET_SIZE = 10
BUCKETS = 4
BITS_PER_NUMBER = int(math.ceil(math.log(BUCKET_SIZE, 2)))
assert((BITS_PER_NUMBER * BUCKETS) <= 32)


class FingerPrint() :
    def __init__(self):
        pass
    
    def specgram(self, channel_samples, Fs=DEFAULT_FS,
                wsize=DEFAULT_WINDOW_SIZE,
                wratio=DEFAULT_OVERLAP_RATIO) :        
        arr2D = mlab.specgram(
            channel_samples,
            NFFT=wsize,
            Fs=Fs,
            window=mlab.window_hanning,
            noverlap=int(wsize * wratio))[0]

        arr2D = 10 * np.log10(arr2D)

        return arr2D

    def get_fingerprints(self, channel_samples, Fs=DEFAULT_FS,
                wsize=DEFAULT_WINDOW_SIZE,
                wratio=DEFAULT_OVERLAP_RATIO) :

        specgram = self.specgram(channel_samples,Fs,wsize,wratio)
        specgram = specgram.T

        chunks = len(specgram)

        print(chunks)
    
        #fingerprints = np.zeros(chunks, dtype=np.uint32)
        fingerprints = defaultdict(list)

        # Examine each chunk independently
        for chunk in range(chunks):
            fingerprint = 0
            for bucket in range(BUCKETS):
                start_index = bucket * BUCKET_SIZE
                end_index = (bucket + 1) * BUCKET_SIZE               
                bucket_vals = specgram[chunk][start_index:end_index]
                max_index = bucket_vals.argmax()
                fingerprint += (max_index << (bucket * BITS_PER_NUMBER))
            #fingerprints[chunk] = fingerprint
            fingerprints[fingerprint].append(chunk)

        print("fingerprints:",fingerprints)

        # return the indexes of the loudest frequencies
        return chunks,fingerprints

    def match(self, left_fingerprints, right_fingerprints):
        
        left_chunks, left_fingerprints = left_fingerprints
        right_chunks, right_fingerprints = right_fingerprints
        offsets = defaultdict(lambda: 0)

        for key in left_fingerprints:            
            if key in right_fingerprints:
                for left_chunk in left_fingerprints[key] :
                    for right_chunk in right_fingerprints[key]:
                        offset = left_chunk - right_chunk
                        offsets[offset] += 1
        
        min_len = min(left_chunks, right_chunks)

        
        print(offsets.values())
        max_offset = 0
        if len(offsets) != 0:
            max_offset = max(offsets.values())
            print("max_offset:",max_offset)
        else:
            max_offset = 0

        score = 0
        if min_len > 0:
            score = max_offset / min_len
        else:
            score = 0

        return score


def fingerprint(channel_samples, Fs=DEFAULT_FS,
                wsize=DEFAULT_WINDOW_SIZE,
                wratio=DEFAULT_OVERLAP_RATIO,
                fan_value=DEFAULT_FAN_VALUE,
                amp_min=DEFAULT_AMP_MIN):
    """
    FFT the channel, log transform output, find local maxima, then return
    locally sensitive hashes.
    """
    # FFT the signal and extract frequency components
    arr2D = mlab.specgram(
        channel_samples,
        NFFT=wsize,
        Fs=Fs,
        window=mlab.window_hanning,
        noverlap=int(wsize * wratio))[0]

    # apply log transform since specgram() returns linear array
    arr2D = 10 * np.log10(arr2D)
    #arr2D[arr2D == -np.inf] = 0  # replace infs with zeros

    # find local maxima    
    local_maxima = get_2D_peaks(arr2D, plot=False, amp_min=amp_min)

    # return hashes
    return generate_hashes(local_maxima, fan_value=fan_value)


def get_2D_peaks(arr2D, plot=False, amp_min=DEFAULT_AMP_MIN):
    # http://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.morphology.iterate_structure.html#scipy.ndimage.morphology.iterate_structure
    struct = generate_binary_structure(2, 1)
    neighborhood = iterate_structure(struct, PEAK_NEIGHBORHOOD_SIZE)

    # find local maxima using our fliter shape
    local_max = maximum_filter(arr2D, footprint=neighborhood) == arr2D
    background = (arr2D == 0)
    eroded_background = binary_erosion(background, structure=neighborhood,
                                       border_value=1)

    # Boolean mask of arr2D with True at peaks
    detected_peaks = local_max ^ eroded_background

    # extract peaks
    amps = arr2D[detected_peaks]
    j, i = np.where(detected_peaks)

    # filter peaks
    amps = amps.flatten()
    peaks = zip(i, j, amps)
    peaks_filtered = [x for x in peaks if x[2] > amp_min]  # freq, time, amp

    # get indices for frequency and time
    frequency_idx = [x[1] for x in peaks_filtered]
    time_idx = [x[0] for x in peaks_filtered]

    if plot:
        # scatter of the peaks
        fig, ax = plt.subplots()
        ax.imshow(arr2D)
        ax.scatter(time_idx, frequency_idx)
        ax.set_xlabel('Time')
        ax.set_ylabel('Frequency')
        ax.set_title("Spectrogram")
        plt.gca().invert_yaxis()
        plt.show()

    return zip(frequency_idx, time_idx)


def generate_hashes(peaks, fan_value=DEFAULT_FAN_VALUE):
    """
    Hash list structure:
       sha1_hash[0:20]    time_offset
    [(e05b341a9b77a51fd26, 32), ... ]
    """
    if PEAK_SORT:
        peaks = sorted(peaks, key=itemgetter(1))

    for i in range(len(peaks)):
        for j in range(1, fan_value):
            if (i + j) < len(peaks):                
                freq1 = peaks[i][IDX_FREQ_I]
                freq2 = peaks[i + j][IDX_FREQ_I]
                t1 = peaks[i][IDX_TIME_J]
                t2 = peaks[i + j][IDX_TIME_J]
                t_delta = t2 - t1

                if MIN_HASH_TIME_DELTA <= t_delta <= MAX_HASH_TIME_DELTA:
                    h = hashlib.sha1(
                        ("%s|%s|%s" % (str(freq1), str(freq2), str(t_delta))).encode('utf-8'))
                    yield (h.hexdigest().encode()[0:FINGERPRINT_REDUCTION], t1)


def finger_matches(hashes,origin_hashes):
    """
    Return the (song_id, offset_diff) tuples associated with
    a list of (sha1, sample_offset) values.
    """
    # Create a dictionary of hash => offset pairs for later lookups
    mapper = {}
    for hash, offset in hashes:              
        mapper[hash] = offset

    mapper_matches = {}
    for hash , offset in origin_hashes:          
        mapper_matches[hash] = offset

    matches = {}
    
    print("len(mapper):",len(mapper))
    print("len(mapper_matches):",len(mapper_matches))
    
    for key in mapper.keys():        
        for key_match in mapper_matches.keys():              
            if key == key_match: 
                print("key:",key)                           
                matches[ key ] = mapper[key]  - mapper_matches[key]    
    return len(matches) > 0

if __name__ == '__main__':
    '''
    import soundfile as sf
    data, fs = sf.read("vr_3_t.wav", dtype='int16')  

    data1, fs1 = sf.read("vr_3.wav", dtype='int16')  

    #print(data)

    finger_print = FingerPrint()
   
    finger_1 = finger_print.get_fingerprints(data,fs)
    finger_2 = finger_print.get_fingerprints(data1,fs1)

    print(finger_print.match(finger_1,finger_2))
    '''

    import librosa
    import librosa.display

    y1, sr1 = librosa.load('vr_3_new_new.wav')
    y2, sr2 = librosa.load('vr_3_new.wav')

    import matplotlib.pyplot as plt
    
    plt.subplot(1, 2, 1)
    mfcc1 = librosa.feature.mfcc(y1, sr1)
    librosa.display.specshow(mfcc1)

    plt.subplot(1, 2, 2)
    mfcc2 = librosa.feature.mfcc(y2, sr2)
    librosa.display.specshow(mfcc2)

    
    from dtw import dtw

    from numpy.linalg import norm
    dist, cost, acc_cost, path = dtw(mfcc1.T, mfcc2.T, dist=lambda x, y: norm(x - y, ord=1))
    print('Normalized distance between the two sounds:', dist)

    plt.imshow(cost.T, origin='lower', cmap=plt.cm.gray, interpolation='nearest')
    plt.plot(path[0], path[1], 'w')
    plt.xlim((-0.5, cost.shape[0]-0.5))
    plt.ylim((-0.5, cost.shape[1]-0.5))

    plt.show()