import sys
import getopt

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.buffer = {}
        self.windowSize = 5
        self.packets_in_transit = 0
        self.seqno = 1
        self.segmented_all_file = False
        self.last_seqno = float('inf')

    # Main sending loop.
    def start(self):
        #Initiate communication
        self.initiate_conversation()
        while len(self.buffer.keys()) != 0 or self.segmented_all_file == False:
            response = self.receive(0.5)
            self.handle_response(response)

        
    """
    Sends first window of packets, ensures first ack is received (TODO: Deal 100% packet loss)
    Note: Does not ensure full window is acked!
    """
    def initiate_conversation(self):
        for i in range(1, self.windowSize + 1):
            msg = self.infile.read(1372)
            self.buffer[i] = msg
            #End of file has been read.
            if msg == "":
                #Empty msg, need to send empty start and end packets.
                if i == 1: 
                    self.buffer[i+1] = ""
                    self.last_seqno = i+1
                else:
                    self.last_seqno = i

                self.segmented_all_file = True
                break
            
        #Will break out if we get a valid ack
        received_valid_ack = False
        while(not received_valid_ack):
            #Will keep sending all the packets in the first window, except the end packet.
            for i in range(1, len(self.buffer.keys())+1):
                if i == 1: msg_type = 'start'
                elif i == len(self.buffer.keys()): break
                else: msg_type = 'data'
                
                packet = self.make_packet(msg_type, i, self.buffer[i])
                self.send(packet)
                self.packets_in_transit += 1
            response = self.receive(0.5)
            received_valid_ack = response != None and Checksum.validate_checksum(response)
        self.handle_response(response)
    
    def handle_response(self, response):
        if response == None:
            self.handle_timeout()
        elif not Checksum.validate_checksum(response):
            self.packets_in_transit -= 1
            return
        else:
            msg_type, ack, data, checksum = self.split_packet(response)
            ack = int(ack)
            if self.seqno < ack:
                self.handle_new_ack(ack)
            else:
                self.handle_dup_ack(ack)

        
    def handle_timeout(self):
        self.packets_in_transit = 0
        self.send_max_transit_amount()


    def handle_new_ack(self, ack):
        self.packets_in_transit -= ack - self.seqno
        if self.packets_in_transit < 0: self.packets_in_transit = 0
        self.seqno = ack
        self.update_buffer()
        self.send_max_transit_amount()

    def handle_dup_ack(self, ack):
        if ack != self.seqno: return
        
        if self.segmented_all_file and self.seqno == max(self.buffer.keys()):
            msg_type = 'end'
        else:
            msg_type = 'data'
        
        packet = self.make_packet(msg_type, self.seqno, self.buffer[self.seqno])
        self.send(packet)

    def send_max_transit_amount(self):
        while self.packets_in_transit < 5 and self.seqno + self.packets_in_transit <= self.last_seqno:
            packet_seqno = self.seqno + self.packets_in_transit

            if self.segmented_all_file and packet_seqno == max(self.buffer.keys()):
                msg_type = 'end'
            else:
                msg_type = 'data'

            packet = self.make_packet(msg_type, packet_seqno, self.buffer[packet_seqno])
            self.send(packet)
            self.packets_in_transit += 1
            if msg_type == 'end': break

        
    def update_buffer(self):
        for key in self.buffer.keys():
            if key < self.seqno: del(self.buffer[key])

        if self.segmented_all_file: return

        while len(self.buffer.keys()) < 5:
            msg = self.infile.read(1372)
            buffer_seqno = len(self.buffer.keys()) + self.seqno
            self.buffer[buffer_seqno] = msg
            if msg == "":
                self.segmented_all_file = True
                self.last_seqno = buffer_seqno
                break

    def log(self, msg):
        if self.debug:
            print msg

'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:d", ["file=", "port=", "address=", "debug="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True

    s = Sender(dest,port,filename,debug)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
