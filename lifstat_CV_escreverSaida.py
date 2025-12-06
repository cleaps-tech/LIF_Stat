# -*- coding: utf-8 -*-
from    tkinter import *
import  numpy as np
import customtkinter as ctk
import cyclic_voltammetry_filterCondenser as CVFC
import lifstat_finalizer_V4 as LSFV4
import CTkMessagebox

class lifstar_escreve_ler():
    Zero_IDX_E  = 1
    Zero_IDX_I  = 1
    ReadResist  = 120
    Exper_Notes = "No notes found"
    Output_File = None
    onoff = False
    ###############################################################################
    # Define a function for writing the final CV-outputs into a .txt file, which
    # has been specified before the measurement was initialized.
    ###############################################################################
    def SAVE_DATA_AFTER_STOP(STOP_STATE, EXP_PARAMS, DATA):
        EXP_PAR_LABEL = np.array(["E_in_vs_RE_in_V","E_v1_vs_RE_in_V","E_v2_vs_RE_in_V","E_fi_vs_RE_in_V","n_cycles","Scanr_in_mV/s","Cond_t_in_s","Rread_in_Ohm"])
        #==================================================================
        #   Write output in the output-txt file
        #==================================================================
        lifstar_escreve_ler.Output_File.write("Stop_State\t")
        lifstar_escreve_ler.Output_File.write(STOP_STATE)
        lifstar_escreve_ler.Output_File.write("\n")
        for i in range(len(EXP_PAR_LABEL)):
            lifstar_escreve_ler.Output_File.write(EXP_PAR_LABEL[i])
            lifstar_escreve_ler.Output_File.write("\t")
            lifstar_escreve_ler.Output_File.write(str(EXP_PARAMS[i]))
            lifstar_escreve_ler.Output_File.write("\n")
        lifstar_escreve_ler.Output_File.write("Notes:\t")
        lifstar_escreve_ler.Output_File.write(lifstar_escreve_ler.Exper_Notes)
        lifstar_escreve_ler.Output_File.write("\n")
        lifstar_escreve_ler.Output_File.write("======================================================\n\n")
        lifstar_escreve_ler.Output_File.write("Ramp-Index\ttime in ms\tE_WE_vs_RE in V\tI in mA\tCyc.No.\n\n")
        for i in range(len(DATA[::,0])-1):
            lifstar_escreve_ler.Output_File.write(str(DATA[i + 1,0]))
            lifstar_escreve_ler.Output_File.write("\t")
            lifstar_escreve_ler.Output_File.write(str(0.001 * DATA[i + 1,1]))
            lifstar_escreve_ler.Output_File.write("\t")
            lifstar_escreve_ler.Output_File.write(str(-0.000249 * (DATA[i + 1,2] - lifstar_escreve_ler.Zero_IDX_E)))
            lifstar_escreve_ler.Output_File.write("\t")
            lifstar_escreve_ler.Output_File.write(str(-0.12452 * (DATA[i + 1,3] - lifstar_escreve_ler.Zero_IDX_I) / lifstar_escreve_ler.ReadResist))
            lifstar_escreve_ler.Output_File.write("\t")
            lifstar_escreve_ler.Output_File.write(str(DATA[i + 1,4]))
            lifstar_escreve_ler.Output_File.write("\n")
        lifstar_escreve_ler.Output_File.close()
        #motores.frame_esquerdo.conexao_serial.write(b'\x78')

        # Verifica se o sinal externo ativou a flag
        if lifstar_escreve_ler.onoff:
            print("LSFV4.load_file() chamado")  # Substitua com a função real
            LSFV4.load_file()

        #LSFV4.load_file()
        #CVFC.Get_CV_Data()


    ###############################################################################
    # Define a function for writing a text output to a certain text-field
    # the INSERT is specified by the "from   tkinter import *" (see above)
    ###############################################################################
    def WRITE_TEXT_OUTPUT(WHERE_TO_WRITE, TEXT_TO_WRITE):
        WHERE_TO_WRITE.insert(INSERT, "%s \n" %TEXT_TO_WRITE)

    ###############################################################################
    # Define a function for writing a data output to a certain text-field
    # the INSERT is specified by the "from   t kinter import *" (see above)
    ###############################################################################
    def WRITE_DATA_OUTPUT(WHERE_TO_WRITE, DATA_TO_WRITE):
        for i in range(len(DATA_TO_WRITE[::,0])):
            WHERE_TO_WRITE.insert(INSERT, "%.3f \t"  %((1e-6)*DATA_TO_WRITE[i,0])   )
            WHERE_TO_WRITE.insert(INSERT, "%.4f \t" % (-0.000249 * (DATA_TO_WRITE[i,1] - lifstar_escreve_ler.Zero_IDX_E)))
            WHERE_TO_WRITE.insert(INSERT, "%.4f \t" % (-0.12452 * (DATA_TO_WRITE[i,2] - lifstar_escreve_ler.Zero_IDX_I) / lifstar_escreve_ler.ReadResist))
            WHERE_TO_WRITE.insert(INSERT, "%.f \n"  %DATA_TO_WRITE[i,3]   )


        
        
        
