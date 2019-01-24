# -*- coding: utf-8 -*-

import tempfile

import sounddevice as sd
import soundfile as sf
import numpy as np # Make sure NumPy is loaded before it is used in the callback
assert np  # avoid "imported but unused" message (W0611)

import queue
import sys
import threading

import webrtcvad


import autost.audio.cv
from autost.audio.vad import SimpleVad
from autost.audio.audiomatch import AudioMatch
import airtest.core.helper
from airtest.core.helper import G,log_in_func,log
from airtest.core.settings import Settings as ST

import librosa
import scipy
import time
import os
import json

from enum import Enum

DEFAULT_FS = 16000 
DEFAULT_CHANNELS = 1
DEFAULT_DTYPE= 'int16'
DEFAULT_BLOCK_SIZE = 160 * 2 # webrtc-vad just support 10ms,20ms,30ms; but it look just support 20ms when samplerate is 16000

DEFAUTLT_BUFFER_SIZE = 10


CONFIG_FILE_PATH = "atide/ui/vr/vr_config.json"


class AudioConfig():
    def __init__(self):
        pass

    def get_audio_config(self):
        audio_config = self.read_config()
        return self.init_sound_device(audio_config)

    def get_root_dir(self):
        dirpath = os.getcwd()
        parent_path,fold = os.path.split(dirpath)
        while fold != "iautost" :
            dirpath = parent_path
            parent_path,fold = os.path.split(dirpath)
        if dirpath:
            return dirpath

    def read_config(self):
        root_path = self.get_root_dir()        
        if root_path:
            config_file = os.path.join(root_path,CONFIG_FILE_PATH)
            if os.path.isfile(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                config_dir = os.path.split(config_file)[0]
                data["config_dir"] = config_dir
                return data

        return {}

    def set_device_index(self,audio_config,device_name,devices_list):

        if device_name in audio_config["audio_device"]:
            device = audio_config["audio_device"][device_name]
            audio_config["audio_device"][device_name]["device_id"] = -1

            i = -1
            for item in devices_list:
                i = i + 1
                if item["name"] == device["name"] and item["hostapi"] == device["hostapi"]:
                    audio_config["audio_device"][device_name]["device_id"] = i
        


    def init_sound_device(self,audio_config):
        if "audio_device" in audio_config :
           devices_list = sd.query_devices()
           self.set_device_index(audio_config,"microphone_conn_machine",devices_list)
           self.set_device_index(audio_config,"microphone",devices_list)
           self.set_device_index(audio_config,"speaker_conn_machine",devices_list)
           self.set_device_index(audio_config,"speaker",devices_list)
        else :
            input_device,output_device = sd.default.device
            audio_device = {"microphone_conn_machine":{"device_id": input_device},
                        "speaker_conn_machine": {"device_id": output_device}}
            audio_config["audio_device"] = audio_device      

        return audio_config  

class AudioProcess():    
    def __init__(self):         
        self.reset()

    def reset(self):
        self.case_dir = ""
        self.siri = None
        self.play_siri = None
        self.run_test = None 

    def start_audio_test(self,case_dir):        
        G.LOGGING.info("Try finding:\n%s", "audio")   
        self.case_dir = case_dir     
        audio_config = AudioConfig().get_audio_config()   
        self.run_test = RunTestMode(audio_config)
        self.run_test.start_record()
        
    
    def stop_audio_test(self):
        self.run_test.stop()
        self.reset()

    def auto_test_play_file(self,filename): 
        if self.run_test:            
            filepath = self.case_dir  + '/' + filename 
            self.run_test.play_file(filepath)        
        

    def auto_test_match_record(self,filename):         
        if self.run_test:
            filepath = self.case_dir + '/' + filename
            self.run_test.match_record(filepath)        
    

    def start_siri(self,case_dir) :
        if self.play_siri or self.siri:
            return ["can not start record,when other record is running"]
        
        audio_config = AudioConfig().get_audio_config()
        self.siri = DialogMode(audio_config)
        self.siri.start_human_machine_mode(case_dir)
        
    def stop_siri(self):
        if self.siri:
            case_list =  self.siri.stop_dialog()        
            self.reset()      
            return case_list 
        


    def start_record(self, case_dir, filename, case_list_callback):
        if self.play_siri :
            self.stop_record()
            self.play_siri = None
        if self.siri:
            self.stop_siri()
            self.siri = None

        play_file_list = []
        if filename :
            if not os.path.isfile(filename):
                return ["can not open the file:%s"%filename]

            play_file_list = [line.rstrip('\n') for line in open(filename)]

            if len(play_file_list) < 0 :
                return ["the %s is empty!"%filename]
            
        audio_config = AudioConfig().get_audio_config()
        self.play_siri =  DialogMode(audio_config)        

        return self.play_siri.start_play_record_mode(case_dir,play_file_list,case_list_callback)
        

    def stop_record(self) :
        if not self.play_siri :
            return ["recording has not been started"]
        
        case_list = self.play_siri.stop_dialog()       
        self.reset()
        return case_list
        

    def play_wave_file(self,filename):
        if not self.play_siri:     
            return ["please start record before play file..."]
                    
        case_list = self.play_siri.play_file(filename)

        return case_list


class RunModeBase():

    class AudioThreadState():
        def __init__(self):
            self.input_device = -1
            self.output_device = -1
            self.audio_thread = None
            self.record_audio = [] 
            self.record_audio_files = queue.Queue() 

        def start_record_thread(self):
            if self.input_device > -1 :
                self.audio_thread = RecordThread(self.input_device,self.output_device)
                self.audio_thread.start()
            return self.audio_thread
            
        
        def start_play_thread(self):
            if self.output_device > -1:
                self.audio_thread = PlayThread(self.output_device)
                self.audio_thread.start()
            return self.audio_thread
            
        

    def __init__(self,audio_config):
        self.audio_config= audio_config
        self.beep_peaks = {}
        self.microphone_for_machine = RunModeBase.AudioThreadState()
        self.speaker_for_machine = RunModeBase.AudioThreadState()
        self.init_device(audio_config["audio_device"])
        self.init_beeps(audio_config["config_dir"],audio_config["beep_files"])
        
    def init_device(self,audio_devices):
        if "microphone_conn_machine" in audio_devices:
            self.microphone_for_machine.input_device = audio_devices["microphone_conn_machine"]["device_id"]
        if "speaker" in audio_devices:
            self.microphone_for_machine.output_device = audio_devices["speaker"]["device_id"]

        if "microphone" in audio_devices:
            self.speaker_for_machine.input_device = audio_devices["microphone"]["device_id"]
        if "speaker_conn_machine" in audio_devices:
            self.speaker_for_machine.output_device = audio_devices["speaker_conn_machine"]["device_id"]


    def init_beeps(self,config_dir,beep_files):        
        audio_match = AudioMatch()

        for tag in beep_files:
            file = beep_files[tag]
            path = os.path.join(config_dir,file)
            if os.path.isfile(path):
                data, sr = sf.read(path, dtype='int16')                 
                #valid_data = simple_vad.remove_fade_in(data)
                valid_data = audio_match.preproccess_data(data,sr)
                self.beep_peaks[tag] = audio_match.get_features(valid_data,sr)

    def exist_beep(self):
        return len(self.beep_peaks) > 0

    def exist_beep_tag(self,tag):
        return tag in self.beep_peaks

    def check_beep(self, data):
        if len(data) > DEFAULT_FS or len(self.beep_peaks) <= 0:
            return ""
        audio_match = AudioMatch()
        simple_vad = SimpleVad()
        valid_data = simple_vad.get_valid_voice(data)
        valid_data = audio_match.preproccess_data(valid_data,DEFAULT_FS)
        data_peaks = audio_match.get_features(valid_data)
        for tag in self.beep_peaks :
            peaks = self.beep_peaks[tag]            
            if audio_match.match_features(peaks,data_peaks):
                return tag        
        return ""


    def save_audio(self,case_dir, prefix, data_list):                        
           
        filename = tempfile.mktemp(prefix=prefix,
                                            suffix='.wav', dir="")                    
        filepath = case_dir + "/" + filename            

        with sf.SoundFile(filepath, mode='x', samplerate=DEFAULT_FS,                            
                            channels=DEFAULT_CHANNELS) as file:
            for data in data_list:
                file.write(data)
            file.close()
            return filename            
        return ""

    

class RunTestMode(RunModeBase):
    def __init__(self, audio_config):
        super().__init__(audio_config)

        self.record_thread = self.microphone_for_machine.start_record_thread()
        
        self.current_audio_time = 0                
        self.runtest_condition = threading.Condition()         
        self.new_audio = False  
            
    def stop(self):
        self.record_thread.stop_record()
        self.record_thread.stop()

    def start_record(self):
        def callback_for_record(data):                     
            self.runtest_condition.acquire() 

            audio_state = self.check_audio_state(data)
            if audio_state:
                self.runtest_condition.notify()           
            self.runtest_condition.release()
            return audio_state
        
        self.record_thread.start_record(callback_for_record)

    
    def check_audio_state(self,data):
        if self.exist_beep() :            
            tag = self.check_beep(data)             
            if tag:
                record_data = self.microphone_for_machine.record_audio
                if len(record_data) > 0 :
                    self.microphone_for_machine.record_audio_files.put(("voice",record_data))
                self.microphone_for_machine.record_audio = []
                self.microphone_for_machine.record_audio_files.put((tag,data)) 
                return True               
            
        self.microphone_for_machine.record_audio += data
        record_data = self.microphone_for_machine.record_audio
        if self.current_audio_time <= 0 :            
            self.microphone_for_machine.record_audio_files.put(("voice",record_data))
            self.microphone_for_machine.record_audio = []
            return True
        else:
            record_audio_time = float(len(record_data) * DEFAULT_BLOCK_SIZE) / DEFAULT_FS                                     
            if ( record_audio_time >= self.current_audio_time ) or (self.current_audio_time - record_audio_time < 1): 
                self.microphone_for_machine.record_audio_files.put(("voice",record_data))
                self.microphone_for_machine.record_audio = [] 
                return True

        return False


    def match_record(self,filename):
        try :
            self.runtest_condition.acquire()

            audio_features = {}
            if filename:
                print("begin to match the file : ", filename)
                data,fs = sf.read(filename,dtype='int16')            
                if len(data) <= 0:
                    return
                
                audio_match = AudioMatch() 
                simple_vad = SimpleVad()            
                data = audio_match.preproccess_data(data,fs)    
                audio_features = audio_match.get_features(data,fs)                        
                self.current_audio_time = float(len(data)) / fs            
           
            #audio_files = self.microphone_for_machine.record_audio_files
            
            
            while True :
                tag = ""
                if self.microphone_for_machine.record_audio_files.empty():                   
                    self.runtest_condition.wait(30)                
                if not self.microphone_for_machine.record_audio_files.empty():    
                    tag,audio_file =  self.microphone_for_machine.record_audio_files.get_nowait()                     

                    if tag == "vr_start_beep" or tag == "vr_end_beep" or tag == "vr_return_beep":                        
                        break

                    if filename:                                  
                        simple_vad = SimpleVad()
                        output = simple_vad.get_valid_voice(audio_file)
                        output = audio_match.preproccess_data(output,DEFAULT_FS)   
                        output_features = audio_match.get_features(output,DEFAULT_FS)                    
                        match_result = audio_match.match_features(audio_features,output_features)
                   
                        recordname = self.save_audio(ST.LOG_DIR,"record_from_machine_", audio_file)
                                                    
                        log_in_func({"audio_file": filename})                                    
                        log_in_func({"record_audio_file": recordname})
                        log_in_func({"audio_match_result": match_result})                           
                        break                                                                                                       
            
            self.current_audio_time = 0
            self.runtest_condition.release()  
            return tag
        except:
            log_in_func({"audio_file": filename})                                                
            log_in_func({"audio_match_result": False})
            log_in_func({"audio_match_info": "error to open %s"%filename})

    def match_beep(self,match_tag):
        if not self.exist_beep_tag(match_tag) :
            return True
        tag = ""
        try_num = 0
        while tag != match_tag and try_num < 10:
            try_num = try_num + 1
            tag = self.match_record("")
        
        return tag == match_tag               
       
    def play_file(self, filename):
        print("begint to play file : ", filename)  
        if self.match_beep("vr_start_beep") :
            #self.record_thread.stop_record()
            output_device = self.speaker_for_machine.output_device        
            time.sleep(0.5)                
            data, fs = sf.read(filename, dtype='float32')        
            sd.play(data, fs, device=output_device)        
            #sd.wait()             
            #self.start_record() 
            self.match_beep("vr_end_beep")


class DialogMode(RunModeBase):

    class RunMode(Enum):
        Stop = 0
        Auto = 1
        File = 2
        FileList = 3
        
    def __init__(self,audio_config):
        super().__init__(audio_config)
        self.microphone_record_thread = None
        self.speaker_record_thread = None
        self.speaker_play_thread = None
        self.case_list = []
        self.play_file_list = [] 
        self.dialog_mode = DialogMode.RunMode.Stop       
        self.case_list_callback = None        

    def start_human_machine_mode(self,case_dir):
        self.dialog_mode = DialogMode.RunMode.Auto  
        self.microphone_record_thread = self.microphone_for_machine.start_record_thread()
        self.speaker_record_thread = self.speaker_for_machine.start_record_thread()            
        self.case_dir = case_dir               
        self.add_case("start_audio_test",self.case_dir)
        self.start_record_from_machine()


    def start_play_record_mode(self,case_dir,filelist,case_list_callback):
        if len(filelist) > 0:
            self.dialog_mode = DialogMode.RunMode.FileList
        else:
            self.dialog_mode = DialogMode.RunMode.File
        self.microphone_record_thread = self.microphone_for_machine.start_record_thread()
        self.speaker_play_thread = self.speaker_for_machine.start_play_thread()  

        self.case_list_callback = case_list_callback
        self.case_dir = case_dir
        self.play_file_list = filelist[::-1]
        self.start_record_from_machine()

        self.add_case("start_audio_test",self.case_dir)    
        case_list = self.case_list
        self.case_list = []    
        return case_list

    
    def stop_dialog(self):
        
        self.stop_record()

        if self.microphone_record_thread :
            self.microphone_record_thread.stop()
        if self.speaker_record_thread :
            self.speaker_record_thread.stop()
        if self.speaker_play_thread :
            self.speaker_play_thread.stop()

        case_list = self.case_list
        self.case_list = []
        return case_list

    def stop_record(self):
        self.stop_record_from_machine()
        self.stop_play_to_machine()        
        self.add_case("stop_audio_test","")    
        self.dialog_mode = DialogMode.RunMode.Stop    
        
    def save_audio_with_case(self,prefix,case_key,vdata):        
        filename = self.save_audio(self.case_dir,prefix, vdata) 
        if filename:
            self.add_case(case_key,filename)        
    
    def add_case(self,case_key,filename):
        if filename:
            case = case_key + "('" + filename + "')\n"
        else:
            case = case_key + "()\n"

        if self.case_list_callback:
            self.case_list_callback(case)
        else:            
            self.case_list.append(case)          

    def start_record_from_machine(self):
    
        def record_callback(vdata):                            
            if not self.exist_beep():
                self.save_audio_with_case("record_from_machine_","match_record",vdata)
                self.stop_record_from_machine()
                self.start_play_to_machine()  
                return True

            tag = self.check_beep(vdata)            
            if tag :
                record_audio = self.microphone_for_machine.record_audio
                if len(record_audio) > 0 :
                    self.save_audio_with_case("record_from_machine_","match_record",record_audio)
                    self.microphone_for_machine.record_audio = []
                self.save_audio_with_case("record_from_machine_","match_record",vdata)

                if tag == "vr_start_beep" :
                    self.stop_record_from_machine()
                    self.start_play_to_machine()                    
                
                if tag == "vr_return_beep" :
                    self.stop_record_from_machine()
                    self.stop_play_to_machine()
                    self.dialog_mode = DialogMode.RunMode.Stop
                return True
            else :
                self.microphone_for_machine.record_audio += vdata
                return False            
                           
        self.microphone_for_machine.audio_thread.start_record(record_callback)

    def stop_record_from_machine(self):
        if self.microphone_record_thread :
            record_audio = self.microphone_for_machine.record_audio
            if len(record_audio) > 0 :
                self.save_audio_with_case("record_from_machine_","match_record",record_audio)
                self.microphone_for_machine.record_audio = []        
            self.microphone_record_thread.stop_record()


    def start_play_to_machine(self):        
        if self.dialog_mode is DialogMode.RunMode.Auto :
            self.start_record_from_microphone()
        elif self.dialog_mode is DialogMode.RunMode.FileList :
            self.play_file_in_list()

    def stop_play_to_machine(self):
        if self.speaker_record_thread :
            self.stop_record_from_microphone()
        elif self.speaker_play_thread:
            self.speaker_play_thread.stop_play()

    
    def start_record_from_microphone(self):    
        if not self.speaker_record_thread:
            return

        def record_callback(data):
            self.save_audio_with_case("record_from_human_",'play_file',data) 
            self.stop_record_from_microphone()
            self.start_record_from_machine()            
            return True                 
        self.speaker_record_thread.start_record(record_callback)

    def stop_record_from_microphone(self):
        if self.microphone_record_thread :
            self.microphone_record_thread.stop_record()
     

    def play_file(self,filename):
        def playend_callback():
            self.start_record_from_machine()

        self.stop_record_from_machine()   
        
        filepath = self.case_dir + '/' + filename        

        if os.path.isfile(filepath):
            time.sleep(0.1)
            self.speaker_play_thread.play_file(filepath,playend_callback)

        return self.add_case("play_file",filename)
        

    def play_file_in_list(self):        
        if len(self.play_file_list) <= 0:
            self.stop_record()
            return False
        filename = self.play_file_list.pop()
        self.play_file(filename)

        return True
                        

class RecordThread(threading.Thread):
    def __init__(self, input_device,output_device):
        threading.Thread.__init__(self)
        self.threadID = 10001
        self.name = "record_thread"
        self.recording = False
        self.running = True    
        self.input_device = input_device
        self.output_device = output_device        
        self.recording_condition = threading.Condition()
            
    def run(self):
        while self.running :           
            self.recording_condition.acquire()
            if not self.recording :
                self.recording_condition.wait()
            if not self.recording:
                break
            self.recording_condition.release()           
            self.record()
             

    def stop_record(self) :
        self.recording = False       


    def stop(self) :
        self.recording_condition.acquire()
        self.running = False
        self.recording = False
        self.recording_condition.notify()
        self.recording_condition.release()        
        self.join()        

    def start_record(self,fun_call_back) : 

        self.recording_condition.acquire()
        if self.recording :
            self.recording_condition.release()
            return        
        self.recording = True
        self.client_callback = fun_call_back
        self.recording_condition.notify()
        self.recording_condition.release()


    def get_device_stream(self,qdata): 

        def stream_callback(indata, outdata, frames, time, status):             
            outdata[:] = indata
            qdata.put(indata.copy())              

        def inputstream_callback(indata, frames, time, status):             
            qdata.put(indata.copy())                                  
                
        if self.output_device > -1 :
            stream = sd.Stream(device=(self.input_device, self.output_device),
                        samplerate=DEFAULT_FS, blocksize= DEFAULT_BLOCK_SIZE,
                        dtype=DEFAULT_DTYPE, channels=DEFAULT_CHANNELS, callback=stream_callback)
        else :
            stream = sd.InputStream(device=self.input_device,
                        samplerate=DEFAULT_FS, blocksize= DEFAULT_BLOCK_SIZE,
                        dtype=DEFAULT_DTYPE, channels=DEFAULT_CHANNELS,callback=inputstream_callback)
                
        return stream
    

    def record(self):                    
        q = queue.Queue()            
        q_speech = []
              
        silent_count = 0        
        speeching = False
        vad = webrtcvad.Vad(3)
        #vad = SimpleVad()
        
        with self.get_device_stream(q):                      
            while True:       
                #print("begin to get data")     
                data = q.get()                                              
                is_speech = vad.is_speech(data,DEFAULT_FS)                
                #is_speech = vad.is_voice(data)#,DEFAULT_FS)                                
                if is_speech :   
                    speeching = True                                        
                else :
                    if speeching:                        
                        silent_count = silent_count + 1

                if speeching:                    
                    q_speech.append(data)
                                            
                               
                if silent_count >= 6 :                                     
                    if  len(q_speech) >  10 :                        
                        if self.client_callback(q_speech) :                       
                            speeching = False

                    q_speech = []

                    silent_count = 0     
                    

                if not self.recording:                    
                    sd.stop()
                    break 
                

class PlayThread(threading.Thread):
    def __init__(self, output_device):
        threading.Thread.__init__(self)
        self.threadID = 10002
        self.name = "play_thread"
        self.output_device = output_device
        self.playing = False
        self.running = True
        self.kwargs = None
        self.playing_condition = threading.Condition()
        self.stop_event = threading.Event()
        self.stop_condition = threading.Condition()
        self.stop_event.set()
  

    def run(self):
        while self.running :            
            self.playing_condition.acquire()
            if not self.playing : 
                self.playing_condition.wait()   
            if self.playing:                 
                self.play()            
            self.playing_condition.release()
              

    def play_file(self,filename,playend_callback): 
        self.playing = False          
        self.playing_condition.acquire()        
        self.stop_event.wait()                 
        self.playing = True
        self.filename = filename        
        self.playend_callback = playend_callback
        self.playing_condition.notify()
        self.playing_condition.release()

    def stop(self):        
        self.playing = False
        self.running = False
        self.playing_condition.acquire()                
        self.playing_condition.notify()      
        self.playing_condition.release()
        

    def stop_play(self):
        self.playing = False
        self.playing_condition.acquire()                
        self.stop_event.wait()        
        self.playing_condition.release()                
                


    def play(self):        
        self.stop_event.clear()        
        event = threading.Event()
        q = queue.Queue(maxsize=DEFAUTLT_BUFFER_SIZE)

        blocksize = 4096
        def callback(outdata, frames, time, status):            
            assert frames == blocksize
            
            if status.output_underflow:                
                raise sd.CallbackAbort
            assert not status
            try:
                data = q.get_nowait()
            except queue.Empty:                
                raise sd.CallbackAbort
            if len(data) < len(outdata):
                outdata[:len(data)] = data
                outdata[len(data):] = b'\x00' * (len(outdata) - len(data))
                raise sd.CallbackStop
            else:
                outdata[:] = data

        
        
        
        with sf.SoundFile(self.filename) as f:
            for _ in range(DEFAUTLT_BUFFER_SIZE):
                data = f.buffer_read(blocksize, dtype='int16')
                if not data:
                    break
                q.put_nowait(data)  # Pre-fill queue       
                                
            stream = sd.RawOutputStream(
                samplerate=f.samplerate, blocksize=blocksize,
                device=self.output_device, channels=f.channels, dtype='int16',
                callback=callback, finished_callback=event.set)                        

            with stream:   
                timeout = blocksize * DEFAUTLT_BUFFER_SIZE / f.samplerate
                while data :
                    if not self.playing :
                        stream.close()
                        break
                    data = f.buffer_read(blocksize, dtype='int16')
                    q.put(data, timeout=timeout)                       

                event.wait()  # Wait until playback is finished

        self.playing = False
        self.stop_event.set() 
        self.playend_callback()
                        

        



if __name__ == '__main__':  

    #audio_process = AudioProcess()


    #l = sd.query_devices()

    #for item in l :
    #    print(item)

    def fun_call_back(data):
        print("fun_cal_back")

    r = RecordThread(1,4)
    r.start()
    r.start_record(fun_call_back)

    time.sleep(1)

    data, fs = sf.read("test.wav", dtype='float32')        
    sd.play(data, fs, device=4)        
    sd.wait()        

    r.stop()

    time.sleep(10)
    '''
    data, sr1 = sf.read('vr_3.wav', dtype='int16') 

    vad = SimpleVad()

    num = int(sr1 / 50)
    data = data.reshape( -1, num)
    
    list = []
    for item in data:        
        list.append(item)
    
    data_1 = vad.remove_fade_in(data)

    audio_match = AudioMatch()
  
    
    features = audio_match.get_features(data)
    features_1 = audio_match.get_features(data_1)

    result = audio_match.match_features(features,features_1)

    print(result)

    print("len(data):", len(data))
    print("len(data_1):", len(data_1))


    with sf.SoundFile("vr_3_new_new.wav", mode='x', samplerate=sr1,                            
                                            channels=DEFAULT_CHANNELS) as file:

        file.write(data_1)
        file.close()'''