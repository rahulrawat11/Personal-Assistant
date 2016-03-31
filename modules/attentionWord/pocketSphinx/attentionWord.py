#!/usr/bin/python3

import zmq
import sys
import datetime
import os
import pyaudio
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

class DummyModule:
  """
  Dummy module class, which just sends back what it receives.
  """

  def __init__(self, port):
    """
    Constructor of the dummy class.
    Args:
      port (int): port of the server
    Returns:
      None
    """

    self.port = port
    self.zmqctx = zmq.Context()
    self.runServer()


  def runServer(self):
    """
    Runs the ZMQ server.
    Returns:
      None
    """

    # bind the port
    self.socket = self.zmqctx.socket(zmq.REP)
    self.socket.bind('ipc://127.0.0.1:{}'.format(port))


  def listen(self):
    """
    Listens on the port.
    Returns:
      None
    """

    while True:
      # wait for request
      message = self.socket.recv_json()

      config = message['config']
      data = message['data']
      timestamp = message['timestamp']

      # save config
      if bool(config):
        configSaved = self.saveConfig(config)
      else:
        # no config send
        configSaved = True

      # do what is needed with the data
      if bool(data):
        replyData = self.application(data)
      else:
        # no data send
        replyData = {}

      # prepare data before send
      replyTimestamp = datetime.datetime.now().isoformat(' ')
      reply = {'timestamp': replyTimestamp, 'data': replyData, 'config': {}}
      if configSaved == True:
        reply['config']['state'] = 'accepted'
      else:
        reply['config']['state'] = 'failed'

      # send back reply
      self.socket.send_json(reply)


  def application(self, message):
    """
    Main application logic of the module.
    Args:
      message (dict): received data as a dictionary
    Returns:
      dict: data to send back as dictionary
    """

    # start Decoder
    decoder = Decoder(self.config)
    decoder.start_utt()

    while True:
        buf = self.stream.read(1024)
        if buf:
             decoder.process_raw(buf, False, False)
        else:
             break
        if decoder.hyp() != None:
            timeOfActivation = datetime.datetime.now().isoformat(' ')
            print ("Detected keyword, restarting search")
            decoder.end_utt()
            message = {'timeOfActivation': timeOfActivation}
            break

    # return result
    return message


  def saveConfig(self, config):
    """
    Saves config received from the kernel.
    Args:
      config (dict): received config
    Returns:
      bool: True if config successuflly saved, False is not
    """
    
    attentionWord = config['attentionWord']
    threshold = config['threshold']

    if bool(attentionWord) and bool(threshold):
        # Create a decoder with certain model
        self.config = Decoder.default_config()
        self.config.set_string('-hmm', '/vagrant/cmusphinx-en-us-5.2')
        self.config.set_string('-dict', '/vagrant/cmusphinx-en-us-5.2/cmudict_SPHINX_40.dict')
        self.config.set_string('-keyphrase', attentionWord)
        self.config.set_float('-kws_threshold', threshold)

        # prepare microphone using PyAudio
        p = pyaudio.PyAudio()
        self.stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
        self.stream.start_stream()
        return True
    else: 
        return False


if __name__ == '__main__':
  port = sys.argv[1]
  port = int(port)
  dm = DummyModule(port)
  dm.listen()