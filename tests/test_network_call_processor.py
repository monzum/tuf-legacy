"""
<Purpose>
  Test the network_call_processor library to make
  sure it works.
 
<Author>
  Monzur Muhammad
  mmuham01@students.poly.edu

<Date Started>
  October 27th, 2012
"""

from network_call_processor import NetworkCallProcessor
from network_call_processor import ProcessCallNotDefined

class SampleProcessor(NetworkCallProcessor):   
  def __init__(self):
    NetworkCallProcessor.__init__(self)



def main():
  """
  Launch the main test for NetworkCallProcessor.
  """

  sample_processor = SampleProcessor()

  try:
    sample_processor.call_socket()
  except ProcessCallNotDefined:
    pass



if __name__ == '__main__':
  main()
