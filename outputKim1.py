def makeRecord( ar, start, end ):
    record = str.format( ';{0:02X}{1:02X}{2:02X}',
        end - start,
        (start >> 8) & 0xff,
        start & 0xff )
    sum = 0

    for i in range( start, end ):
        v = 0
        if ar[i] != None:
            v = ar[i]
        record += str.format( '{0:02X}', v )
        sum += v

    record += str.format( '{0:02X}{1:02X}\r\n', (sum >> 8) & 0xff, sum & 0xff )
    return record

def dumpRecords( filename, gMemory ):

    def probe( start, end ):
        if end > 0x10000:
            end = 0x10000
            
        for i in range(start, end):
            if gMemory[i] != None:
                return True
        return False

    outputFile = open( filename, 'w' )

    recordCount = 0
    i = 0
    while i < 0x10000:
        if probe( i, i + 16 ):
            outputFile.write( makeRecord( gMemory, i, i + 16 ) )
            recordCount += 1
        i += 16

    outputFile.write( str.format( ';00{0:02X}{1:02X}{0:02X}{1:02X}\r\n',
        (recordCount >> 8) & 0xff,
        recordCount & 0xff )
        )

    outputFile.close()
