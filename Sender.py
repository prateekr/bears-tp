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
        self.seqno = 0
        self.msg_table = {}
        self.window_size = 4
    
    # Main sending loop.
    def start(self):
        self.segment_file()
        
        msg_type = None
        while not msg_type == 'end':
        
            for i in range(self.seqno, self.seqno + self.window_size):
                msg_type = 'data'
                if i == 0: 
                    msg_type = 'start'
                else:
                    if self.msg_table[i+1] == "": msg_type = 'end'
                    
    
                packet = self.make_packet(msg_type,i,self.msg_table[i])
                self.send(packet)
                print "sent: %s" % packet

            
            response = self.receive(0.5)
            self.handle_response(response)
            
    def segment_file(self):
        msg = None
        seqno = 0
        while msg != "":
            msg = self.infile.read(1372)
            self.msg_table[seqno] = msg
            seqno += 1

        
    def handle_response(self,response_packet):
        if response_packet == None:
            self.handle_timeout()
        else:
            if Checksum.validate_checksum(response_packet):
                self.seqno += 1
                print "recv: %s" % response_packet
            else:
                return

    def handle_timeout(self):
        print "didn't receive anything"

    def handle_new_ack(self, ack):
        pass

    def handle_dup_ack(self, ack):
        pass

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
