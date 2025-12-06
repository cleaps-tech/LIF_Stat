# -*- coding: utf-8 -*-
import pathlib
import os
import lifstat_finalizer_V4 as LF
from lifstat_CV_escreverSaida import  lifstar_escreve_ler as LCVES
from pathlib import Path
import struct
import tkinter as tk
import customtkinter as ctk
import matplotlib.pyplot as plt
import numpy as np
from tkinter.scrolledtext import ScrolledText
from   tkinter import *                             # Python 3
from   tkinter import messagebox                    # Python 3
from   tkinter import filedialog                    # Python 3
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import  time
from datetime import datetime        # import datetome for checking recent cal file
import threading
from    threading                                import Thread
from    lifstat_CV_Acquisition          import ACQUISITION_BACKEND     as CVAQB
from    lifstat_CV_escreverSaida        import lifstar_escreve_ler as PCVWR
import time
from tkinter import END
####################################################################################################
# Classe para o Frame direito com LabelFrame de valores de medição e gráficos
estado = None
class Medir_CV_GUI(ctk.CTkFrame):
    def __init__(self, master, frame_esquerdo = None, is_connected_callback = None):
        super().__init__(master)
        self.onoff = False
        ####################################################################################################
        #    Define plotting options to make the plot look cool :)
        ####################################################################################################
        font = {'family': 'Times New Roman', 'color': 'black', 'weight': 'normal', 'size': 15, }
        plt.rcParams['mathtext.fontset'] = 'dejavuserif'
        plt.rcParams['font.sans-serif'] = ['Times new Roman']

        ####################################################################################################
        # Initialize some global variables
        ####################################################################################################
        global PlotType;          PlotType = 1
        global arduino;           arduino = None  # initialize the device as None until it is defined
        global UpCounter;         UpCounter = 0  # used for counting in the output window
        global CalData;           CalData = 0
        global Zero_IDX_E;        Zero_IDX_E = 13250
        global Zero_IDX_I;        Zero_IDX_I = 13250
        global Initiate_Plot;     Initiate_Plot = True  # For first setup of a plot
        global thread_1;
        global selection;         selection = True
        ####################################################################################################
        # Check, if there is a recent calibration file. If so, load it and use it. If not,
        # show a respective waring and start the interface
        ####################################################################################################
        try:
            CalFile = datetime.today().strftime('CALIBRATION/%Y_%m_%d_Cal.txt')
            CalData = np.genfromtxt(CalFile, skip_header=0, skip_footer=1)
            Neg_IDX_E = np.average(CalData[CalData[::, 1] == 1, 3])
            Pos_IDX_E = np.average(CalData[CalData[::, 1] == 2, 3])
            Neg_IDX_I = np.average(CalData[CalData[::, 1] == 1, 4])
            Pos_IDX_I = np.average(CalData[CalData[::, 1] == 2, 4])
            Zero_IDX_E = int(0.5 * (Neg_IDX_E + Pos_IDX_E))
            Zero_IDX_I = int(0.5 * (Neg_IDX_I + Pos_IDX_I))
        except:
            messagebox.showwarning(title="Nenhuma calibração recente nesta data!",
                                   message="Você não gerou nenhum arquivo de dados de calibração!\n Seus resultados podem ficar incorretos, calibre a Your data might be incorrect.")
            txt_filename = ""
        ####################################################################################################
        # Change the variables in the class of the PolArStat_CV_Script_Write_Outputs script
        # according to the classical values or the values from the calibration file
        ####################################################################################################
        PCVWR.Zero_IDX_E = Zero_IDX_E
        PCVWR.Zero_IDX_I = Zero_IDX_I

        self.frame_esquerdo = frame_esquerdo
        self.is_connected_callback = is_connected_callback

        # Configuração para que o LabelFrame se expanda para preencher o grid
        self.grid_rowconfigure(0, weight=1)  # Permite expansão vertical
        self.grid_columnconfigure(0, weight=1)  # Permite expansão horizontal

        # Criação do LabelFrame para "Valores de Medição"
        self.labelframe = tk.LabelFrame(self, text="Valores de Medição", padx=5, pady=5)
        self.labelframe.grid(row=0, rowspan = 10 ,column=0, padx=10, pady=10, sticky="nsew")

        # Configuração das colunas e linhas internas do LabelFrame para expansão
        self.labelframe.grid_columnconfigure(0, weight=1)
        self.labelframe.grid_columnconfigure(1, weight=1)
        self.labelframe.grid_rowconfigure(13, weight=1)  # Última linha expansível para área de texto

        # Lista de Labels e Entries
        labels = ["E_in vs. Ref[V]*", "E_vertex1 vs. Ref[V]*", "E_vertex2 vs. Ref[V]*",
                  "E_final vs. Ref[V]*", "Scanrate[mV/s]", "Num. de ciclos",
                  "Cond. Times[s]*", "R read [Ohm]*"]
        self.entries = []
        for i, label_text in enumerate(labels):
            label = ctk.CTkLabel(self.labelframe, text=label_text)
            label.grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entrada = ctk.CTkEntry(self.labelframe)
            entrada.grid(row=i, column=1, padx=5, pady=5, sticky="w")

            # Definir o valor inicial para "R read [Ohm]*"
            if label_text == "R read [Ohm]*":
                entrada.insert(0, "120")
            if label_text == "Cond. Times[s]*":
                entrada.insert(0, "5")
            if label_text == "E_in vs. Ref[V]*":
                entrada.insert(0, "-0.6")
            if label_text == "E_vertex1 vs. Ref[V]*":
                entrada.insert(0, "-1.5")
            if label_text == "E_vertex2 vs. Ref[V]*":
                entrada.insert(0, "-0.6")
            if label_text == "E_final vs. Ref[V]*":
                entrada.insert(0, "-0.6")
            if label_text == "Scanrate[mV/s]":
                entrada.insert(0, "30")
            if label_text == "Num. de ciclos":
                entrada.insert(0, "1")
            self.entries.append(entrada)

        # Botões - todos do mesmo tamanho e centralizados
        # self.botao_nitrato = ctk.CTkButton(self.labelframe, text="Nitrato", command=self.nitrato)
        # self.botao_fosfato = ctk.CTkButton(self.labelframe, text="Fosfato", command=self.fosfato)

        self.botao_configurar = ctk.CTkButton(self.labelframe, text="Enviar parâmetros", command=self.Set_CV_Params)
        self.botao_iniciar_cv = ctk.CTkButton(self.labelframe, text="Iniciar CV", command=self.AskSaveFile_AndStart)
        self.botao_verificar = ctk.CTkButton(self.labelframe, text="Verificar", command=self.Get_CV_Params)
        self.botao_parar_cv = ctk.CTkButton(self.labelframe, text="Parar CV", command=self.Stop_CV)
        self.botao_sendEmail = ctk.CTkButton(self.labelframe, text = "Enviar/bloquear E-mail", command= self.sendEmail)
        self.botao_inibemotor = ctk.CTkButton(self.labelframe, text = "Inibe motores",command= self.inibemotores )
        #self.botao_parar_automatico = ctk.CTkButton(self.labelframe, text= "Finalizar sistema de motores", command = self.enviar_pulso_2) #receber_pulso)
        #self.botao_parar_motores = ctk.CTkButton(self.labelframe, text = "Parar todos os motores", command = self.parar_todos)

        # Posicionamento dos botões em uma linha

        self.botao_configurar.grid(row=8, column=0, padx=5, pady=10, sticky="ew")
        self.botao_iniciar_cv.grid(row=8, column=1, padx=5, pady=10, sticky="ew")
        self.botao_verificar.grid(row=9, column=0, padx=5, pady=10, sticky="ew")
        self.botao_parar_cv.grid(row=9, column=1, padx=5, pady=10, sticky="ew")
        self.botao_sendEmail.grid(row=10, column=0, padx=5, pady=10, sticky="ew")
        self.botao_inibemotor.grid(row = 10, column = 1, padx = 5, pady = 10, sticky = "ew")

        #self.botao_parar_automatico.grid(row=10, column=1, padx=5, pady=10, sticky="ew")
        #self.botao_parar_motores.grid(row=11, column = 1, padx = 5, pady = 10, sticky = "ew")

        # self.botao_nitrato.grid(row=10, column=0, padx=5, pady=10, sticky="ew")
        # self.botao_fosfato.grid(row=10, column=1, padx=5, pady=10, sticky="ew")

        # Label adicional
        label3 = ctk.CTkLabel(self.labelframe, text="Valores de configuração", font=("Times New Roman", 18))
        label3.grid(row=12, column=0, columnspan=2, padx=5, pady=10, sticky="ew")

        # Área de texto para exibir dados da serial
        self.Output_text = ScrolledText(self.labelframe, wrap=tk.WORD, font=("Times New Roman", 12, "bold"), width=65, height=20)
        self.Output_text.grid(row=13, column=0, columnspan=2, padx=5, pady=10, sticky="nsew")
        self.Output_text.focus()

        # Configuração para que os widgets internos se expandam com o LabelFrame
        #self.labelframe.grid_rowconfigure(11, weight=3)  # Permite expansão da área de texto na última linha

        if Initiate_Plot == True:
            global ax1, ax2
            global canvas
            fig, (ax1, ax2) = plt.subplots(2, 1)  # Sem compartilhar eixos

            # Dados de exemplo para os eixos X e Y
            x = 0
            y = 0
            # Gráfico 1: E vs I com linhas pontilhadas e grade
            ax1.plot(x, y, linestyle="--")
            ax1.set_title("E em Volts x I em mA")
            ax1.set_xlabel("$E$ vs. RE em (Volts)", fontsize=13)
            ax1.set_ylabel("$I$ em (mA)")
            ax1.grid(True)

            # Gráfico 2: E vs Tempo com linhas pontilhadas e grade
            ax2.plot(x, y, linestyle="--")
            ax2.set_title("E em Volts x Tempo em Segundos")
            ax2.set_xlabel("Tempo em $(s)$")
            ax2.set_ylabel("$E$ vs. RE em (Volts)")
            ax2.grid(True)

            # Ajuste de espaçamento e estilo do gráfico
            plt.subplots_adjust(hspace=0.5)
            ax1.tick_params(direction='in', length=4, width=0.5, colors='k', labelsize=13)
            ax2.tick_params(direction='in', length=4, width=0.5, colors='b', labelsize=13)
            ax1.grid(which='both', linestyle='--')
            ax2.grid(which='both', linestyle='--')

            # Criando o canvas para o gráfico e adicionando-o à interface
            canvas = FigureCanvasTkAgg(fig, self)
            canvas.get_tk_widget().grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")
            Initiate_Plot = False

        # Label acima da caixa de texto
        label2 = ctk.CTkLabel(self, text="Valores medidos em tempo real", font=("Times New Roman", 18))
        label2.grid(row=1, column=1, columnspan=1, padx=5, pady=(20, 5), sticky="n")

        # Caixa de texto para exibir valores medidos
        self.textbox = ctk.CTkTextbox(self, width=300, height=200)
        self.textbox.grid(row=2, column=1, columnspan=1, padx=10, pady=10, sticky="nsew")

        # Configuração para que a interface principal permita expansão vertical e horizontal
        self.grid_rowconfigure(0, weight=3)  # Peso para o gráfico
        self.grid_rowconfigure(2, weight=1)  # Peso para o textbox
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
    def inibemotores(self):

        return
    def sendEmail(self):
        self.onoff = not self.onoff
        if self.onoff:
            LCVES.onoff = self.onoff
            mensagem = "Email habilitado para receber dados de medição, análise, geração de gráficos e envio de arquivos txt, png e pdf."
            self.Output_text.delete("1.0", END)
            self.Output_text.insert(END, mensagem)
            self.botao_sendEmail.configure(fg_color="green")
            print("✅", mensagem)
            messagebox.showinfo("Estado do E-mail", mensagem)
        else:
            LCVES.onoff = self.onoff
            mensagem = "Dados de envio por E-mail bloqueados para envio."
            self.Output_text.delete("1.0", END)
            self.Output_text.insert(END,mensagem)
            self.botao_sendEmail.configure(fg_color="red")
            print("⛔", mensagem)
            messagebox.showwarning("Estado do E-mail", mensagem)

    ####################################################################################################

    def AskSaveFile_AndStart(self):

        if self.is_connected_callback and self.is_connected_callback():
            self.frame_esquerdo.conexao_serial.write(b'\x77\x00\x00\x00\x00\x00')
            time.sleep(3)
            #=========================================================================================
            while True:
                sistema_automatico = self.frame_esquerdo.conexao_serial.readline().decode('utf-8').strip()
                if sistema_automatico == "ok":
                    break
                print(sistema_automatico)
                time.sleep(1)  # Aguarda 1 segundo antes de tentar novamente
                print("veio o segundo", sistema_automatico)

            #==========================================================================================

        """
            sistema_automatico = self.frame_esquerdo.conexao_serial.readline().decode('utf-8').strip()
            while sistema_automatico != "ok":
                print(sistema_automatico)
                time.sleep()
                sistema_automatico = self.frame_esquerdo.conexao_serial.readline()[:-2]
                print("veio o segundo", sistema_automatico)
        else:
            messagebox.showwarning(title="Sem comunicação serial",
                                   message="Sem comunicação serial, verifique a conexão USB !")
            return
        """
        try:
            # Get absolute path for MEASURE directory
            base_dir = pathlib.Path.cwd()
            measure_dir = base_dir / "MEASURE"
            os.makedirs(measure_dir, exist_ok=True)

            # Set filename with current date
            txt_filename = measure_dir / datetime.today().strftime('%Y_%m_%d_measure.txt')

            # Show info message about default folder
            messagebox.showinfo(title="Pasta Padrão",
                                message=f"O arquivo será salvo na pasta padrão 'MEASURE': {txt_filename}\nNão é possível salvar em outra pasta.")

            # Open file in write mode
            outfile_CV_Data = open(txt_filename, 'w')
            PCVWR.Output_File = outfile_CV_Data
            print("parei por aqui, Pode começar a medir ! ")
            self.START_CV()
        except Exception as e:
            messagebox.showwarning(title="Erro ao salvar arquivo!",
                                   message=f"Não foi possível criar o arquivo: {str(e)}")
            txt_filename = ""


    def start_measure_thread(self):
        # Criar um thread separado para a calibração
        measure_thread = threading.Thread(target=self.START_CV)
        measure_thread.start()

        ######################################################################################################
        # The following function will set the inputs for a CV-measurement
        ######################################################################################################
    def Set_CV_Params(self):
        global ReadResist
        try:
            # Verifica se todos os campos foram preenchidos antes de tentar convertê-los
            if not all([self.entries[0].get(), self.entries[1].get(), self.entries[2].get(),
                        self.entries[3].get(), self.entries[4].get(), self.entries[5].get(),
                        self.entries[6].get(), self.entries[7].get()]):
                messagebox.showerror(title="Parametros incompletos!",
                                     message="Todas as entradas devem ser preenchidas para que a Voltametria Cíclica (CV) ocorra")
                return

            # Converte os valores para float
            E_initial = float(self.entries[0].get())
            E_vert1 = float(self.entries[1].get())
            E_vert2 = float(self.entries[2].get())
            E_fin = float(self.entries[3].get())
            Scanrate = float(self.entries[4].get())
            Cycles = float(self.entries[5].get())
            Conditime = float(self.entries[6].get())
            #ReadResist = float(self.entries[7].get())

            # Notas experimentais
            try:
                Exper_Notes = str(Exper_Notes_Eingabe.get())
                PCVWR.Exper_Notes = Exper_Notes if Exper_Notes != "" else "Nenhuma anotação especificada"
            except:
                PCVWR.Exper_Notes = "Nenhuma anotação especificada"

            # Atualiza o valor de ReadResist
            ReadResist = float(self.entries[7].get())
            PCVWR.ReadResist = ReadResist

            # Preparação para enviar os dados para o Arduino
            SEND_E_in = b'\x11' + b'\x10' + struct.pack('f', E_initial)
            SEND_E_v1 = b'\x11' + b'\x11' + struct.pack('f', E_vert1)
            SEND_E_v2 = b'\x11' + b'\x12' + struct.pack('f', E_vert2)
            SEND_E_fi = b'\x11' + b'\x13' + struct.pack('f', E_fin)
            SEND_Cycl = b'\x11' + b'\x14' + struct.pack('f', Cycles)
            SEND_ScaR = b'\x11' + b'\x15' + struct.pack('f', Scanrate)
            SEND_Cond = b'\x11' + b'\x16' + struct.pack('f', Conditime)

            # Verifica a conexão e envia os dados
            if self.is_connected_callback and self.is_connected_callback():
                self.frame_esquerdo.conexao_serial.write(SEND_E_in)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(SEND_E_v1)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(SEND_E_v2)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(SEND_E_fi)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(SEND_Cycl)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(SEND_ScaR)
                time.sleep(2)
                self.frame_esquerdo.conexao_serial.write(SEND_Cond)
                time.sleep(2)

                # Configuração da tag para formatação
                self.Output_text.tag_configure("bold_arial", font=("Arial", 12, "bold"))
                # Inserção de texto formatado
                self.Output_text.insert(END, "\n Transmissão de dados completa com sucesso :)\n", "bold_arial")
                self.Output_text.insert(END, "----------------------------------------------------------\n",
                                        "bold_arial")
            else:
                messagebox.showwarning("Erro de Conexão", "Nenhuma conexão serial estabelecida.")

        except Exception as e:
            messagebox.showerror(title="Erro", message=f"Ocorreu um erro: {e}")
    def Get_CV_Params(self):
        '''
        # A função recupera os parâmetros do Arduino através da comunicação serial.
        # O readline lê a entrada já convertida, o [: -2] remove o \r\n no final da linha enviada pelo Arduino,
        # e a conversão para float transforma a string recebida em um número de ponto flutuante.
        '''
        # Verificar se a conexão está ativa
        if self.is_connected_callback and self.is_connected_callback():

                # ==============================================================================================
                # Initialize an Array for data storage
                # ==============================================================================================
                Readback_Array = np.zeros(8)  # Ein, Ev1, Ev2, Ef, ncy, nu, Cond_t, Rread
                # ==============================================================================================
                # Send command to Arduino for retreiving the inputs which specify the CV
                # ==============================================================================================
                GETTING_COMMAND_BYTES = b'\x22\x00\x00\x00\x00\x00'
                self.frame_esquerdo.conexao_serial.write(GETTING_COMMAND_BYTES)
                # ==============================================================================================
                # Wait two seconds to get back the data
                # ==============================================================================================
                time.sleep(2)
                # ==============================================================================================
                # Fill the "Readback_Array" with the data obtained from the device
                # ==============================================================================================
                Readback_Array[0] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])
                Readback_Array[1] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])
                Readback_Array[2] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])
                Readback_Array[3] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])
                Readback_Array[4] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])
                Readback_Array[5] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])
                Readback_Array[6] = float(self.frame_esquerdo.conexao_serial.readline()[:-2])
                Readback_Array[7] = 120   # ReadResist
                # ==============================================================================================
                # Write retreived data in the variable CV_Inputs of the PolArStat_CV_Script_Acquisition
                # ==============================================================================================
                CVAQB.CV_Inputs = Readback_Array
                # ==============================================================================================
                # Write retreived data to the output window
                # ==============================================================================================
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "Os seguintes parâmetros foram configurados! \n")
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "E_init. \t= \t %s V vs. Re" % Readback_Array[0])
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "E_vertex 1.\t = \t %s V vs. Re" % Readback_Array[1])
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "E_vertex 2.\t = \t %s V vs. Re" % Readback_Array[2])
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "E_final.\t = \t %s V vs. Re" % Readback_Array[3])
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "n-Cycles \t = \t %s " % Readback_Array[4])
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "Scanrate \t= \t %s mV/s" % Readback_Array[5])
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "Cond. time \t = \t %s s" % Readback_Array[6])
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "R Read \t = \t %s Ohm" % Readback_Array[7])
        else:
            # Se a conexão não estiver estabelecida, exibe um erro
            messagebox.showerror("Erro de Conexão", "Nenhuma conexão serial estabelecida.")
            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    ####################################################################################################
    def START_CV(self):
        #===============================================================================================
        # reset the global variable up counter, which is required for writing output-data
        #===============================================================================================
        global UpCounter    ;   UpCounter= 0
        #===============================================================================================
        # retreive CV-inputs from the device with the Get_CV_Params() function and
        # write them to the output-text field called "Output_text"
        #===============================================================================================
        self.Get_CV_Params()
        #===============================================================================================
        # write a header in the field "Output_text" for monitoring data
        #===============================================================================================
        PCVWR.WRITE_TEXT_OUTPUT(self.Output_text,"\n Preparing CV completed.\n\n")
        PCVWR.WRITE_TEXT_OUTPUT(self.Output_text,"t/s\t E/V\t I/mA\t Cyc.No.\n")
        #===============================================================================================
        # If there is a device - named arduino - talking to the PC, clear memory and run the
        # looper function for data acquisition
        #===============================================================================================
        arduino = self.frame_esquerdo.conexao_serial
        if self.is_connected_callback and self.is_connected_callback():

            SEND_BYTES = b'\x33\x01\x00\x00\x00\x00'   #bytes for running a CV
            self.frame_esquerdo.conexao_serial.write(SEND_BYTES)
            time.sleep(3)
            Starter = self.frame_esquerdo.conexao_serial.readline().strip()#[:-2]
            while Starter != b'10101010':          # proceed only, if Arduino tells that conditioning-loop is done by sending b'101010'
                time.sleep(0.001)                  # Wait for one millisecond before trying again
                Starter = self.frame_esquerdo.conexao_serial.readline()[:-2]  # read again and enter while loop again (if not fulfilled)

            CVAQB.CLEAR_STORAGE()
            CVAQB.DEVICE  = arduino
            CVAQB.gui = self
            CVAQB.running = True
            time.sleep(1)
            CVAQB.Looper_ON = True
            self.Serial_Looper(ax1, ax2, canvas)
            # Após a medição, chamar load_file com a instância da GUI
            LF.load_file(self)
        else:
            messagebox.showwarning(title="Nenhum dispositivo listado!",
                                   message="No device selected. Initialize serial communication before\running an experiment!")

    ####################################################################################################
    def Stop_CV(self):
        if CVAQB.running == False:
            messagebox.showwarning(title="Nenhuma medição ativa no momento!",
                                   message="Não hà nenhuma medição a ser parada !")
        else:
            if CVAQB.running == True:
                PCVWR.WRITE_TEXT_OUTPUT(self.Output_text, "\n Status: Medição foi parada pelo usuário manualmente.\n")
            CVAQB.StopMeasure = True
            CVAQB.Looper_ON = False
            if self.is_connected_callback and self.is_connected_callback():
                # Limpa os buffers antes de fechar
                self.frame_esquerdo.conexao_serial.reset_input_buffer()
                self.frame_esquerdo.conexao_serial.reset_output_buffer()
                self.frame_esquerdo.conexao_serial.close()



    ####################################################################################################
    def _quit():
        thread_1.join()
        root.quit()
        root.destroy()
    ####################################################################################################

    def Serial_Looper(self, ax1, ax2, canvas):
        # Atualiza gráficos e janela de saída serial continuamente.
        if not CVAQB.Looper_ON:
            # Se Looper_ON é False, tenta plotar os dados finais antes de encerrar
            if CVAQB.Storage_Array.shape[0] > 1:
                try:
                    ax1.clear()
                    ax2.clear()
                    self.InputArray = CVAQB.ARRAYCONDENSER(ARRAY=CVAQB.Storage_Array[1::, ::])
                    if self.InputArray.size > 0 and self.InputArray.shape[0] >= 3:
                        conversion_factor = -0.000249
                        current_conversion = -0.12452
                        # Gráfico 1: E vs I
                        ax1.plot(
                            conversion_factor * (self.InputArray[2::, 1] - Zero_IDX_E),
                            current_conversion * (self.InputArray[2::, 2] - Zero_IDX_I) / 120,  #PCVWR.ReadResist ,  Alterado
                            linestyle="--",
                        )
                        ax1.set(title="E em Volts x I em mA", xlabel="$E$ vs. RE em (Volts)", ylabel="$I$ em (mA)")
                        ax1.grid(which='both', linestyle='--')
                        ax1.tick_params(direction='in', length=4, width=0.5, colors='k', labelsize=13)
                        # Gráfico 2: E vs Tempo
                        ax2.plot(
                            (1e-6) * self.InputArray[2::, 0],
                            conversion_factor * (self.InputArray[2::, 1] - Zero_IDX_E),
                            linestyle="--",
                        )
                        ax2.set(title="E em Volts x Tempo em Segundos", xlabel="Tempo em $(s)$",
                                ylabel="$E$ vs. RE em (Volts)")
                        ax2.grid(which='both', linestyle='--')
                        ax2.tick_params(direction='in', length=4, width=0.5, colors='b', labelsize=13)
                        canvas.draw()
                        self.master.update()  # Força atualização do Tkinter
                    else:
                        print("Serial_Looper: InputArray vazio ou insuficiente para plotagem")
                except Exception as e:
                    print(f"Erro na Serial_Looper (final): {e}")
                return  # Encerra se Looper estiver desligado

        try:
            # Atualiza os gráficos
            ax1.clear()
            ax2.clear()

            self.InputArray = CVAQB.ARRAYCONDENSER(ARRAY=CVAQB.Storage_Array[1::, ::])
            print(f"Serial_Looper: InputArray shape = {self.InputArray.shape}")  # Depuração

            if self.InputArray.size > 0 and self.InputArray.shape[0] >= 3:  # Verifica se há dados suficientes
                conversion_factor = -0.000249
                current_conversion = -0.12452

                # Gráfico 1: E vs I
                ax1.plot(
                    conversion_factor * (self.InputArray[2::, 1] - Zero_IDX_E),
                    current_conversion * (self.InputArray[2::, 2] - Zero_IDX_I) / 120, #PCVWR.ReadResist,  # Alterado
                    linestyle="--",
                )
                ax1.set(title="E em Volts x I em mA", xlabel="$E$ vs. RE em (Volts)", ylabel="$I$ em (mA)")
                ax1.grid(which='both', linestyle='--')
                ax1.tick_params(direction='in', length=4, width=0.5, colors='k', labelsize=13)

                # Gráfico 2: E vs Tempo
                ax2.plot(
                    (1e-6) * self.InputArray[2::, 0],
                    conversion_factor * (self.InputArray[2::, 1] - Zero_IDX_E),
                    linestyle="--",
                )
                ax2.set(title="E em Volts x Tempo em Segundos", xlabel="Tempo em $(s)$", ylabel="$E$ vs. RE em (Volts)")
                ax2.grid(which='both', linestyle='--')
                ax2.tick_params(direction='in', length=4, width=0.5, colors='b', labelsize=13)

                canvas.draw()
                self.master.update()  # Força atualização do Tkinter
            else:
                print("Serial_Looper: InputArray vazio ou insuficiente para plotagem")

            # Atualiza a janela de saída serial
            PCVWR.WRITE_DATA_OUTPUT(self.Output_text,
                                    self.InputArray[UpCounter::, ::])  # Corrigido para chamar a função diretamente
            self.Output_text.see(tk.END)
            self.UpCounter = len(self.InputArray[::, 0])

        except Exception as e:
            print(f"Erro na Serial_Looper: {e}")

        # Rechama a função
        self.master.after(45, self.Serial_Looper, ax1, ax2, canvas)


    # def Serial_Looper(self, ax1, ax2, canvas):
    #
    # #    Atualiza gráficos e janela de saída serial continuamente.
    #     if not CVAQB.Looper_ON:
    #         return  # Encerra se o Looper estiver desligado
    #     try:
    #         # Atualiza os gráficos
    #         ax1.clear()
    #         ax2.clear()
    #
    #         self.InputArray = CVAQB.ARRAYCONDENSER(ARRAY=CVAQB.Storage_Array[1::, ::])
    #
    #         conversion_factor = -0.000249  # Constante de conversão
    #         current_conversion = -0.12452  # Outra constante de conversão
    #
    #         # Gráfico 1: E vs I
    #         ax1.plot(
    #             conversion_factor * (self.InputArray[2::, 1] - Zero_IDX_E),
    #             current_conversion * (self.InputArray[2::, 2] - Zero_IDX_I) / ReadResist,
    #             linestyle="--",
    #         )
    #         ax1.set(title="E em Volts x I em mA", xlabel="$E$ vs. RE em (Volts)", ylabel="$I$ em (mA)")
    #         ax1.grid(which='both', linestyle='--')
    #         ax1.tick_params(direction='in', length=4, width=0.5, colors='k', labelsize=13)
    #
    #         # Gráfico 2: E vs Tempo
    #         ax2.plot(
    #             (1e-6) * self.InputArray[2::, 0],
    #             conversion_factor * (self.InputArray[2::, 1] - Zero_IDX_E),
    #             linestyle="--",
    #         )
    #         ax2.set(title="E em Volts x Tempo em Segundos", xlabel="Tempo em $(s)$", ylabel="$E$ vs. RE em (Volts)")
    #         ax2.grid(which='both', linestyle='--')
    #         ax2.tick_params(direction='in', length=4, width=0.5, colors='b', labelsize=13)
    #
    #         canvas.draw()
    #
    #         # Atualiza a janela de saída serial
    #         self.Output_text.insert(tk.END, PCVWR.WRITE_DATA_OUTPUT(self.InputArray[UpCounter::, ::]))
    #         self.Output_text.see(tk.END)
    #         self.UpCounter = len(self.InputArray[::, 0])
    #
    #     except Exception as e:
    #         print(f"Erro na Serial_Looper: {e}")
    #
    #
    #     # Rechama a função
    #     self.master.after(50, self.Serial_Looper, ax1, ax2, canvas)

    ####################################################################################################
    # Start the conditional data-acquisition on its own thread, that the GUI does not freeze
    # if data collection is busy
    ####################################################################################################

    thread_1 = Thread(target=CVAQB.LINE_READER_FOR_THREAD)
    thread_1.start()

    def validate_and_send(self, motor_index, value):
        if self.is_connected_callback and self.is_connected_callback():
            if value.isdigit():
                self.Output_text.insert(tk.END, f"Valor enviado para Motor {motor_index + 1}: {value}\n")
                self.frame_esquerdo.conexao_serial.write(value.encode())
                print(f"Valor enviado para Motor {motor_index + 1}: {value}")
            else:
                messagebox.showwarning("Entrada Inválida", "Por favor, insira somente valores numéricos.")
        else:
            messagebox.showwarning("Erro de Conexão", "Nenhuma conexão serial estabelecida.")

    # Funções para os botões
    def configurar(self):
        print("Configuração acionada.")
    def iniciar_cv(self):
        print("Iniciar CV acionado.")
    def verificar(self):
        print("Verificar acionado.")
    def parar_cv(self):
        print("Parar CV acionado.")

# Executando a aplicação
if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()  # Janela principal
    root.title("Potenciostato")
    # Instanciando a classe FrameDireito
    frame_direito = Medir_CV_GUI(root)
    frame_direito.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    # Configurando layout da janela principal
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.mainloop()
