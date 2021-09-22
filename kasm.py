#!/usr/bin/python3
#
#   Simple 6502 assembler
#   Writen by Landon Dyer
#   ABRMS license
#

# Coding conventions:
#
# - gSomething is a global variable

import sys

import tok
import eval
import fileinput
from addressingModes import *
import input6502
import inputTpo
import outputKim1
import outputPythonArray
import symbols
import traceback
import re


gListingFile = None
gInput = None
gPriorFile = None

gOps = {} # will be set later

gLoc = 0


#   ----------------------------------------------------------------
#   Pseudo ops
#   ----------------------------------------------------------------

def fn_org( tokenizer, phaseNumber ):
    global gLoc
    org = eval.Expression( tokenizer ).eval()
    if org == None:
        raise Exception( "Undefined expression" )
    gLoc = org


def fn_db( tokenizer, phaseNumber ):
    while not tokenizer.atEnd():

        if tokenizer.curTok() == tok.STRING:

            s = tokenizer.curValue()
            for c in s:
                depositByte( ord( c ) )

            tokenizer.advance()

        else:

            expr = eval.Expression( tokenizer )

            value = expr.eval()
            if phaseNumber > 0:
                if value > 0xff or value < -128:
                    raise Exception( "value too large for a byte" )
                depositByte( value )

            else:
                depositByte( 0 )

        if tokenizer.curTok() != ',':
            break
        else:
            tokenizer.advance()


def fn_dw( tokenizer, phaseNumber ):

    while not tokenizer.atEnd():

        if tokenizer.curTok() == tok.STRING:

            s = tokenizer.curValue()
            for c in s:
                depositWord( ord( c ) )

            tokenizer.advance()

        else:

            expr = eval.Expression( tokenizer )

            value = expr.eval()
            if phaseNumber > 0:
                depositWord( value )

            else:
                depositWord( 0 )

        if tokenizer.curTok() != ',':
            break
        else:
            tokenizer.advance()


def fn_ds( tokenizer, phaseNumber ):
    global gLoc
    
    value = eval.Expression( tokenizer ).eval()
    if value == None:
        raise Exception( "Undefined expression" )
    gLoc += value


def fn_include( tokenizer, phaseNumber ):

    if tokenizer.curTok() == tok.STRING or tokenizer.curTok() == tok.SYMBOL:
        gInput.push( tokenizer.curValue() )
        tokenizer.advance()
    else:
        raise Exception( "Expected filename" )


gPsuedoOps = {
    'org':      fn_org,
    'db':       fn_db,
    'dw':       fn_dw,
    'ds':       fn_ds,
    'include':  fn_include
}



#
#   parseAddressingMode ==> addrMode, expressionObject
#

def parseAddressingMode( tokenizer ):

    if tokenizer.atEnd():
        return IMPLIED, None

    if tokenizer.curTok() == '#':
        tokenizer.advance()
        expr = eval.Expression( tokenizer )
        return IMMED, expr

    #
    #   (n)
    #   (nn)
    #   (n,x)
    #   (n),y
    #
    if tokenizer.curTok() == '(':
        tokenizer.advance()
        expr = eval.Expression( tokenizer )

        #   (expr,x)
        if tokenizer.curTok() == ',':
            if  tokenizer.peek( 1 ) == tok.SYMBOL and tokenizer.peekValue(1).lower() == 'x' and tokenizer.peek( 2 ) == ')':
                tokenizer.advance( 3 )
                return INDX, expr
            else:
                raise Exception( "bad addressing mode (started out looking like indirect-x)" )

        elif tokenizer.curTok() == ')':

            tokenizer.advance()

            #
            #   (expr),y
            #   (expr)
            #
            if tokenizer.curTok() == ',' and tokenizer.peek( 1 ) == tok.SYMBOL and tokenizer.peekValue( 1 ).lower() == 'y':
                tokenizer.advance( 2 )
                return INDY, expr
            else:
                return IND, expr

        else:
            raise Exception( "bad addressing mode (started out looking indirect, but fizzled)" )

    #
    #   nn
    #   n
    #   rel
    #
    #   n,x
    #   n,y
    #

    expr = eval.Expression( tokenizer )

    if tokenizer.curTok() == ',':
        tokenizer.advance()

        if tokenizer.curTok() == tok.SYMBOL:
            if tokenizer.curValue().lower() == 'x':
                return UNDECIDED_X, expr
            elif tokenizer.curValue().lower() == 'y':
                return UNDECIDED_Y, expr
            else:
                raise Exception( str.format( "Unxpected symbol {0} following expression", tokenizer.curValue() ) )
        else:
            raise Exception( "Unxpected gunk following expression" )

    return UNDECIDED, expr


#   ----------------------------------------------------------------
#   Image construction
#   ----------------------------------------------------------------


gMemory = [None] * 65536
gThisLine = []


def clearLineBytes():
    global gThisLine
    gThisLine = []


def depositByte( byte ):
    global gLoc, gThisLine

    if byte == None:
        byte = 0

    #xxx print("DEP ", gLoc, byte)
    gMemory[gLoc] = byte & 0xff
    gThisLine.append( byte & 0xff )
    gLoc += 1
    if gLoc >= 0x10000:
        gLoc = 0


def depositWord( word ):

    if word == None:
        word = 0

    depositByte( word )
    depositByte( word >> 8 )


#   ----------------------------------------------------------------
#   Assembly
#   ----------------------------------------------------------------

def depositImpliedArg( expr, value ):
    pass

def depositByteArg( expr, value ):
    depositByte( value )

def depositAbsArg( expr, value ):
    global gAddressWidth

    if   gAddressWidth == 1: # Byte
      depositByte( value )
    elif gAddressWidth == 2: # Byte
      depositWord( value )
    else:
      raise Exception( str.format( "Unknown gAddressWidth {0}", gAddressWidth) )

def depositRelArg( expr, value ):
    global gLoc

    if value != None:
        fromLoc = gLoc + 1
        delta = value - fromLoc

        if delta < -128 or delta > 127:
            raise Exception( str.format( "relative reference out of range ({0} bytes)", delta ) )
        depositByte( delta )

    else:

        depositByte( 0 )
    

gDepositDispatch = {
    IMPLIED: depositImpliedArg,
    IMMED: depositByteArg,
    ABS: depositAbsArg,
    ZP: depositByteArg,
    ABSX: depositAbsArg,
    ABSY: depositAbsArg,
    IND: depositAbsArg,
    REL: depositRelArg,
    ZPX: depositByteArg,
    ZPY: depositByteArg,
    INDX: depositByteArg,
    INDY: depositByteArg
    }


def assembleInstruction( op, tokenizer, phaseNumber ):
    addrMode, expr = parseAddressingMode( tokenizer )

    value = None
    if expr != None:
        value = expr.eval()
        
    if phaseNumber > 0 and value == None and addrMode != IMPLIED:
        raise Exception( "Undefined expression" )

    #
    #   Translate UNDECIDED into various forms of REL / ZP / ABS
    #
    if not addrMode in gOps[op]:

        if addrMode == UNDECIDED:

            if REL in gOps[op]:
                addrMode = REL
            elif ZP in gOps[op] and value != None and value < 0x100:
                addrMode = ZP
            else:
                addrMode = ABS

        elif addrMode == UNDECIDED_X:

            if ZPX in gOps[op] and value != None and value < 0x100:
                addrMode = ZPX
            else:
                addrMode = ABSX

        elif addrMode == UNDECIDED_Y:

            if ZPY in gOps[op] and value != None and value < 0x100:
                addrMode = ZPY
            else:
                addrMode = ABSY

    if addrMode in gOps[op]:

        depositByte( gOps[op][addrMode] )
        gDepositDispatch[addrMode]( expr, value )

    else:

        raise Exception( str.format("Bad addressing mode {0} for instruction {1}", addrMode, op) )


def generateListingLine( line ):
    global gListingFile, gPriorFile

    if gInput.file() != gPriorFile:
        gListingFile.write( str.format( "File {0}\n", gInput.file() ) )
        gPriorFile = gInput.file()

    prefix = str.format( "{0:5}: ", gInput.line() )
    baseAddr = gLoc - len( gThisLine )

    if len( gThisLine ) > 0:
        i = 0
        while i < len( gThisLine ):
            n = len( gThisLine ) - i
            if n > 8:
                n = 8

            s, ascii = dump( gThisLine, i, i + n )

            if i == 0:
                gListingFile.write( str.format( "{0} {1:04X}  {2:30} {3}", prefix, baseAddr + i, s, line ) )
            else:
                gListingFile.write( str.format( "{0} {1:04X}  {2:10}\n", prefix, baseAddr + i, s ) )

            i += n

    else:

        gListingFile.write( str.format( "{0} {1:30} {2}", prefix, "", line ) )


#
#   Handle a line of assembly input
#
#   Phase 0:    just intern stuff
#   Phase 1:    emit stuff (expressions required to be defined)
#
def assembleLine( line, phaseNumber=0 ):
    global gLoc
    
    clearLineBytes()
    tokenizer = tok.Tokenizer( line )

    #
    #   Set '*' psuedo-symbol at the start of each line
    #
    symbols.set( '*', gLoc )

    #
    #   SYMBOL = VALUE
    #
    if tokenizer.curTok() == tok.SYMBOL and tokenizer.peek(1) == '=':
        sym = tokenizer.curValue()
        tokenizer.advance( 2 )
        expr = eval.Expression( tokenizer )
        if not tokenizer.atEnd():
            raise Exception( "Bad expression (extra gunk)" )

        value = expr.eval()

        if phaseNumber > 0 and value == None:
            raise Exception( str.format( "Undefined expression" ) )
        
        symbols.set( sym, expr.eval() )

        if gListingFile != None and phaseNumber > 0:
            generateListingLine( line )

        return
        
    #
    #   handle SYMBOL: at start of line
    #   NOTE: could enforce leadingWhitespace, but we have a ':'
    #   instead of that.
    #
    if tokenizer.curTok() == tok.SYMBOL and tokenizer.peek(1) == ':':
        sym = tokenizer.curValue()
        tokenizer.advance( 2 )

        if phaseNumber == 0:
            symbols.set( sym, gLoc )
            
        else:
            #
            #   check that the symbol has the same value in
            #   subsequent phases
            #
            symbols.setScope( sym )
            if symbols.get( sym ) != gLoc:
                raise Exception( str.format( "Symbol phase error (expected {0}, have {1})", symbols.get(sym), gLoc ) )

    #
    #   handle ops
    #
    if tokenizer.curTok() == tok.SYMBOL:

        op = tokenizer.curValue().lower()
        tokenizer.advance()
        
        if op in gPsuedoOps:
            gPsuedoOps[op]( tokenizer, phaseNumber )
        elif op in gOps:
            assembleInstruction( op, tokenizer, phaseNumber )
        else:
            raise Exception( str.format( 'Unknown op: {0}', op ) )

    if gListingFile != None and phaseNumber > 0:
        generateListingLine( line )


def assembleFile( filename ):
    global gInput, gPriorFile, gLoc
    
    symbols.clear()
    gPriorFile = None
    gotError = False
    
    for phase in range(0,2):

        if gotError:
            break
            
        try:
            gInput = fileinput.FileInput( filename )
        except:
            print("Error: {0}", sys.exc_info()[1])
            return

        gLoc = 0

        try:
            while True:
                line = gInput.nextLine()
                if not line:
                    break
                assembleLine( line, phase )
        except:
            err = str.format("Error: {0}({1}): {2}",
                gInput.file(),
                gInput.line(),
                sys.exc_info()[1] )
            print(err)
            gotError = True
            # traceback.print_exc()

    return not gotError


def dump(ar, start, end ):
    s = ''
    ascii = ''
    j = 0

    for i in range( start, end ):
        v = 0
        if ar[i] != None:
            v = ar[i]

        if j > 0:
            s += ' '

        if j == 8:
            s += ' '

        s += str.format('{0:02X}', v)

        if v >= ord(' ') and v <= 0x7f:
            ascii += chr( v )
        else:
            ascii += '.'

        j = j + 1

    return s, ascii

def dumpMem():
    global gMemory

    def probe( start, end ):
        for i in range(start, end):
            if gMemory[i] != None:
                return True
        return False

    i = 0
    while i < 0x10000:
        if probe(i, i + 16):
            s, ascii = dump(gMemory, i, i+16)
            print(str.format('{0:04X}  {1}  {2}', i, s, ascii ))
        i += 0x10


gCommands = {
    # 'foo': { 'handler': function, 'count': numberOfArguments }
    }


def main( argv ):
    global gOps
    global gCommands
    global gListingFile
    global gAddressWidth
    
    # defaults
    outFormat = "Kim1"
    gOps = input6502.gOps

    argno = 1
    while argno < len( argv ):

        arg = argv[argno]

        if arg in gCommands:
            count = 0
            if 'count' in gCommands[arg]:
                count = gCommands[arg]['count']
                if argno + count >= len( argv ):
                    raise Exception( str.format( "Not enough arguments for {0}", arg ) )

                args = argv[argno + 1 : argno + count + 1]
                argno += count + 1
                gCommands[arg]['handler'](*args)
            else:
                argno += 1
                gCommands[arg]['handler']()
                
        elif arg.startswith( '-' ):
            if arg == "--outFormat=PythonArray":
                outFormat = "PythonArray"
            elif arg == "--outFormat=Kim1":
                outFormat = "Kim1"
            elif arg == "--inFormat=tpo":
                gOps          = inputTpo.gOps
                gAddressWidth = inputTpo.gAddressWidth
            elif arg == "--inFormat=6502":
                gOps = input6502.gOps
            else:
                raise Exception( str.format( "Unknown option {0}", arg ) )

            argno += 1

        else:
            
            argno += 1

            match = re.match( ".*\.(.*)", arg )
            if not match:
                arg += ".asm"

            match = re.match( "(.*\.).*", arg )
            if not match:
                raise Exception( "internal error flogging filenames" )

            baseFile = match.group(1)
            listingFile = baseFile + "lst"
            outputFile = baseFile + "dat"

            gListingFile = open( listingFile, "w" )

            if assembleFile( arg ):
                if outFormat == "Kim1":
                    outputKim1.dumpRecords( outputFile, gMemory )
                elif outFormat == "PythonArray":
                    outputPythonArray.dumpRecords( outputFile, gMemory )
                else:
                    raise Exception( str.format( "Unknown outFormat {0}", outFormat ) )


if __name__ == '__main__':
    try:
        main( sys.argv )
    except:
        err = str.format( "Error: {0}", sys.exc_info()[1] )
        print(err)
