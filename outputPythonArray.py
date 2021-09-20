def writeRecord( ar, start, end, outputFile ):
    for i in range( start, end ):
        if ar[i] != None:
             outputFile.write( str.format( "  {0},\n", ar[i] ) )

def dumpRecords( filename, gMemory ):

    def probe( start, end ):
        if end > 0x10000:
            end = 0x10000
            
        for i in range(start, end):
            if gMemory[i] != None:
                return True
        return False


    outputFile = open( filename, 'w' )

    outputFile.write( "executable = [\n" );
    
    memLen = len( gMemory )

    i = 0
    while i < 0x10000:
        if probe( i, i + 16 ):
            writeRecord( gMemory, i, i + 16, outputFile )
        i += 16

    outputFile.write( ']\n' );

    outputFile.close()
