# -*- coding: utf-8 -*-
import  numpy     as np
import  time
from tkinter import messagebox
from    lifstat_CV_escreverSaida import lifstar_escreve_ler as PCVWR

class ACQUISITION_BACKEND():
    ###############################################################################
    #   Initialize some variables in the class "ACQUISITION_BACKEND()"
    ###############################################################################
    running        = False
    Read_Finished  = False
    StopMeasure    = False
    Looper_ON      = False
    DEVICE         = None
    CV_Inputs      = None
    Storage_Array  = np.zeros((1,5))
    gui            = None  # Reference to Medir_CV_GUI instance

    ###############################################################################
    #   Reset variables, if they have been modified
    ###############################################################################
    def CLEAR_STORAGE():
        ACQUISITION_BACKEND.Storage_Array  = np.zeros((1,5))   # clear memory
        ACQUISITION_BACKEND.Looper_ON      = False             # reset variable
        ACQUISITION_BACKEND.StopMeasure    = False             # reset variable
        ACQUISITION_BACKEND.running        = False             # reset variable
        ACQUISITION_BACKEND.Read_Finished  = False             # reset variable

    ###############################################################################
    #    The following will read the line of a serial output, provided by
    #    the device in action (given that there is a device connected).
    ###############################################################################
    def LINE_READER_FOR_THREAD():
        while True :
            if ACQUISITION_BACKEND.running == False:
                time.sleep(0.05)
            if ACQUISITION_BACKEND.running == True and ACQUISITION_BACKEND.Read_Finished == False:
                try:
                    data = ACQUISITION_BACKEND.DEVICE.readline()[:-2]
                    print(data)
                    if data:
                        if data != b'999999':   # As soon as the Arduino sends 999999, the measurement is done
                            # Decodifica os dados e remove caracteres indesejados
                            DECODED = [item.strip() for item in data.decode("utf-8").split('\t')]

                            try:
                                DECODED = np.array([float(item) for item in DECODED]).astype(float)
                                if DECODED.shape[0] == 5:  # Garante que há 5 elementos
                                    ACQUISITION_BACKEND.Storage_Array = np.vstack([ACQUISITION_BACKEND.Storage_Array, DECODED])
                                    print("Storage array atualizado:", ACQUISITION_BACKEND.Storage_Array)  # Confirmar atualização
                                    if ACQUISITION_BACKEND.gui is not None:
                                        ACQUISITION_BACKEND.gui.textbox.insert("end", f" {ACQUISITION_BACKEND.Storage_Array}\n")
                                        ACQUISITION_BACKEND.gui.textbox.yview_moveto(1.0)  # Scroll to the bottom
                            except ValueError:
                                print("Dados inválidos recebidos:", DECODED)  # Exibe a linha problemática

                        elif data == b'999999':
                            print("recebi o valor",  data)

                            ACQUISITION_BACKEND.running = False
                            ACQUISITION_BACKEND.Looper_ON = False
                            ACQUISITION_BACKEND.Read_Finished = True
                            PCVWR.SAVE_DATA_AFTER_STOP(STOP_STATE="Success", EXP_PARAMS=ACQUISITION_BACKEND.CV_Inputs,
                                                       DATA=ACQUISITION_BACKEND.Storage_Array)
                            #ACQUISITION_BACKEND.DEVICE.close()

                            ACQUISITION_BACKEND.DEVICE.write(b'\x78\x00\x00\x00\x00\x00')
                            time.sleep(1)
                            sistema_automatico_2 = ACQUISITION_BACKEND.DEVICE.readline().decode('utf-8').strip()
                            while sistema_automatico_2 != "ok_2":
                                time.sleep(0.1)
                                sistema_automatico_2 = ACQUISITION_BACKEND.DEVICE.readline()[:-2]

                            print("fechando a serial se receber 9999999 e ok_2")


                except Exception as e:
                    messagebox.showerror("Erro", f"Erro na comunicação serial. Verifique a conexão. {str(e)}")
                    ACQUISITION_BACKEND.running = False
                    ACQUISITION_BACKEND.Looper_ON = False
                    ACQUISITION_BACKEND.StopMeasure = True
                    PCVWR.SAVE_DATA_AFTER_STOP(STOP_STATE="Interrupt_or_fail", EXP_PARAMS=ACQUISITION_BACKEND.CV_Inputs,
                                               DATA=ACQUISITION_BACKEND.Storage_Array)
                    #ACQUISITION_BACKEND.DEVICE.close()
                    print("fechando a serial se deu exception")

    ###############################################################################
    #    The following function takes an array and reduces it by its first comuln
    #    indices by averaging equal ones. This is what BioLogic does when it says
    #    average over n-percent of the step. Here, we just have (around 4 points).
    ###############################################################################
    def ARRAYCONDENSER(ARRAY):
        NLB   = 0
        Out   = np.zeros(len(ARRAY[0,1::]))
        for i in range(len(ARRAY[::,0])-1):
            if ARRAY[i+1,0] != ARRAY[i,0]:
                B   = np.mean(ARRAY[NLB:i+1,1::], axis = 0)
                B[0] = ARRAY[i,1]
                Out = np.vstack([Out,B])
                NLB = i+1
        return Out[1::,::]
        print(f"ARRAYCONDENSER: Output shape = {result.shape}")  # Depuração
        return result
