import libnit_listener
import network_call_processor

simple_processor = network_call_processor.NetworkCallProcessor()

new_listener = libnit_listener.LibnitListener(simple_processor)

new_listener.serve_forever()
