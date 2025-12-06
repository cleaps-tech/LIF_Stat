# coding: utf-8
# =======================================================================================================================
from tkinter import *
from tkinter.filedialog import askopenfilename
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from scipy.interpolate import interp1d
from scipy.interpolate import InterpolatedUnivariateSpline
from scipy.optimize import curve_fit
from scipy.optimize import nnls
from scipy.linalg import toeplitz
from scipy.special import kv, iv, gamma
from scipy.integrate import quad
from cmath import *
from math import ceil, floor
from scipy.optimize import fsolve
from scipy.signal import savgol_filter
import mpmath as mp
import os
import datetime

mp.dps = 25;
mp.pretty = True

global F
global R
global File_Was_Loaded
F = 96485.0
R = 8.314
File_Was_Loaded = 0

def cot(phi):
    return 1.0 / tan(phi)
def csc(phi):
    return 1.0 / sin(phi)
def coth(x):
    return 1 / tanh(x)
def Get_CV_Data():
    Fenster = Toplevel()
    Fenster.title("Voltametria cíclica")
    Fenster.geometry("400x270")
    def PolArStat_CV_Call():
        Get_CV_Data_PolArStat()
        Fenster.destroy()

    PolArStatCV = Button(Fenster, text="Condense CV data from \nPolArStat", command=PolArStat_CV_Call, width=20,
                         height=5)
    PolArStatCV.place(x=210, y=25)
def Get_CV_Data_PolArStat():
    Open_CV_File_PolArStat()
def Open_CV_File_PolArStat():
    root = Toplevel()
    root.title("Your Data")
    root.geometry("500x500")
    def Arraycondenser(ARRAY):
        NLB = 0
        Out = np.zeros(len(ARRAY[0, 1::]))
        for i in range(len(ARRAY[::, 0]) - 1):
            if ARRAY[i + 1, 0] != ARRAY[i, 0]:
                B = np.mean(ARRAY[NLB:i + 1, 1::], axis=0)
                B[0] = ARRAY[i, 1]
                Out = np.vstack([Out, B])
                NLB = i + 1
        return Out[1::, ::]

    Path = askopenfilename()
    data = np.genfromtxt(Path, skip_header=14, skip_footer=1)
    data_condensed = Arraycondenser(data[1::, ::])

    # Determina automaticamente o número máximo de ciclos baseado na quinta coluna (índice 4)
    max_cycle = int(np.max(data[:, 4]))

    # ============================================================================
    # Plotting of loaded file
    # ============================================================================
    f = Figure(figsize=(5, 5), tight_layout=True)
    b = f.add_subplot(111)
    # ============================================================================
    global Potenzial
    global Strom
    # Usa o último ciclo (max_cycle) como padrão
    times_of_exp = data_condensed[data_condensed[::, 3] == max_cycle, 0]
    Potenzial = data_condensed[data_condensed[::, 3] == max_cycle, 1]
    Strom = data_condensed[data_condensed[::, 3] == max_cycle, 2]

    PotenzialRAW = data[data[::, 4] == max_cycle, 2]
    StromRAW = data[data[::, 4] == max_cycle, 3]

    # Aplica o filtro Savitzky-Golay para encontrar o pico
    Strom_filtered = savgol_filter(Strom, window_length=11, polyorder=2)
    peak_current_idx = np.argmax(Strom_filtered)  # Pico positivo
    peak_current = Strom_filtered[peak_current_idx]  # Corrente em mA
    peak_voltage = Potenzial[peak_current_idx]  # Tensão em V

    # Plota os dados
    b.plot(PotenzialRAW, StromRAW, linestyle='-', marker='', color='lightgrey', label="raw data")
    b.plot(Potenzial, Strom, linestyle='-', marker='', color='k', label=f"step-average (cycle {max_cycle})")

    # Plota o pico como um ponto vermelho com anotação
    b.plot(peak_voltage, peak_current, 'ro', markersize=8, label='Peak')
    b.annotate(f'Peak: ({peak_voltage:.3f} V, {peak_current:.3f} mA)',
               xy=(peak_voltage, peak_current), xytext=(5, 5),
               textcoords='offset points', fontsize=10, color='red')

    b.legend(frameon=False, fontsize=12)
    b.set_xlabel('E vs. Ref. / V', fontsize=12)
    b.set_ylabel('I / mA', fontsize=12)
    for axis in ['top', 'bottom', 'left', 'right']:
        b.spines[axis].set_linewidth(2)
        b.spines[axis].set_color('k')
    b.tick_params(tickdir='in', width=2, length=6, labelsize=12)
    canvas = FigureCanvasTkAgg(f, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)

    # Cria a pasta "Condensergraph" se ela não existir
    output_dir = "Condensergraph"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Define o caminho fixo para salvar o arquivo condenser.txt
    txt_filename = os.path.join(output_dir, "condenser.txt")

    # Salva o arquivo condenser.txt automaticamente
    outfile_CV_Data = open(txt_filename, 'w')
    outfile_CV_Data.write("E_vs_Ref_in_V")
    outfile_CV_Data.write("\t")
    outfile_CV_Data.write("I_in_microampere")
    outfile_CV_Data.write("\n")
    for i in range(len(Potenzial)):
        outfile_CV_Data.write(str(Potenzial[i]))
        outfile_CV_Data.write("\t")
        outfile_CV_Data.write(str(1000 * Strom[i]))
        outfile_CV_Data.write("\n")
    outfile_CV_Data.close()

    # Chama a função para processar os dados e calcular a concentração
    Process_Nitrate_Concentration(Potenzial, Strom)

def Process_Nitrate_Concentration(Potenzial, Strom):
    # Aplica o filtro Savitzky-Golay na corrente (Strom)
    Strom_filtered = savgol_filter(Strom, window_length=11, polyorder=2)  # Parâmetros ajustáveis

    # Encontra o pico de corrente (máximo positivo) e a tensão correspondente
    peak_current_idx = np.argmax(Strom_filtered)  # Considera apenas valores positivos
    peak_current = Strom_filtered[peak_current_idx]  # Corrente em mA
    peak_voltage = Potenzial[peak_current_idx]  # Tensão em V

    # Calcula a "area" como o produto do pico de corrente pela tensão, garantindo valor positivo
    area = abs(peak_current * peak_voltage)  # Usa abs para garantir que area seja positiva

    # Calcula a concentração de nitrato (c) usando a nova equação ajustada: area = 2.315e-5 * c + 0.00441941757811
    c = (area + 7.6458e-7)/6.16973e-8
    #c = (area - 0.00441941757811) / 2.315e-5
    # y = ax+ b --> y = 6.16973e^-8*x -7.6458e^-7, sendo x = concentração.

    # Adiciona impressões para depuração
    print(f"Peak Current (mA): {peak_current}")
    print(f"Peak Voltage (V): {peak_voltage}")
    print(f"Area: {area}")
    print(f"Concentration (c): {c}")

    # Cria a pasta "concentracaonitrato" se ela não existir
    output_dir = "concentracaonitrato"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Obtém a data e hora atuais
    current_time = datetime.datetime.now()
    date_str = current_time.strftime("Data %d/%m/%Y Hora %H:%M")

    # Define o caminho fixo para salvar o arquivo concentracao.txt
    txt_filename = os.path.join(output_dir, "concentracao.txt")

    # Salva o arquivo concentracao.txt com os dados solicitados
    with open(txt_filename, 'w') as outfile:
        outfile.write(f"Maniport RJ {date_str} concentracao {c:.4f}\n")

def main():
    root = Tk()
    root.withdraw()  # Esconde a janela principal
    Get_CV_Data()  # Inicia a interface automaticamente
    root.mainloop()


if __name__ == "__main__":
    main()
"""
# coding: utf-8
#=======================================================================================================================
from tkinter                           import *
from tkinter.filedialog                import askopenfilename
from tkinter.filedialog                import asksaveasfilename
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.backend_bases          import key_press_handler
from matplotlib.figure                 import Figure
from scipy.interpolate                 import interp1d
from scipy.interpolate                 import InterpolatedUnivariateSpline
from scipy.optimize                    import curve_fit
from scipy.optimize                    import nnls
from scipy.linalg                      import toeplitz
from scipy.special                     import kv, iv, gamma
from scipy.integrate                   import quad
from cmath                             import *
from math                              import ceil,floor
from scipy.optimize                    import fsolve

import mpmath as mp
mp.dps = 25
mp.pretty = True

global F
global R
global File_Was_Loaded
F = 96485.0
R = 8.314
File_Was_Loaded = 0
def cot(phi):
    return 1.0/tan(phi)
def csc(phi):
    return 1.0/sin(phi)
def coth(x):
    return 1/tanh(x)


def Get_CV_Data():
    Fenster = Toplevel()
    Fenster.title("Get CV Data")
    Fenster.geometry("400x270")

    def PolArStat_CV_Call():
        Get_CV_Data_PolArStat()

        def quit():
            Fenster.destroy()
        quit()

    PolArStatCV = Button(Fenster, text="Condense CV data from \nPolArStat",command=PolArStat_CV_Call, width = 20, height = 5)
    PolArStatCV.place(x = 210, y = 25)


def Get_CV_Data_PolArStat():
    Fenster = Toplevel()
    Fenster.title("Get Data")
    Fenster.geometry("400x270")

    Cycle_to_analyze_label = Label(Fenster, text="Cycle to export")
    Cycle_to_analyze_label.place(x=35, y=80)
    Cycle_to_analyze_Eingabe = Entry(Fenster)
    Cycle_to_analyze_Eingabe.insert(END, 1)
    Cycle_to_analyze_Eingabe.place(x=155, y=80, width=175, height=22)

    def NextCVPolArStat():
        global Cycle_to_analyze
        Cycle_to_analyze = (int(Cycle_to_analyze_Eingabe.get()))
        Open_CV_File_PolArStat()

        def quit():
            Fenster.destroy()
        quit()

    Next = Button(Fenster, text="Next", command=NextCVPolArStat)
    Next.place(x=155, y=120, width=175, height=35)

def Open_CV_File_PolArStat():
    root = Toplevel()
    root.title("Your Data")
    root.geometry("500x500")

    def Arraycondenser(ARRAY):
        NLB = 0
        Out = np.zeros(len(ARRAY[0, 1::]))
        for i in range(len(ARRAY[::, 0]) - 1):
            if ARRAY[i + 1, 0] != ARRAY[i, 0]:
                B = np.mean(ARRAY[NLB:i + 1, 1::], axis=0)
                B[0] = ARRAY[i, 1]
                Out = np.vstack([Out, B])
                NLB = i + 1
        return Out[1::, ::]

    Path = askopenfilename()
    data = np.genfromtxt(Path, skip_header=14, skip_footer=1)
    data_condensed = Arraycondenser(data[1::, ::])

    # ============================================================================
    # Plotting of loaded file
    # ============================================================================
    f = Figure(figsize=(5, 5), tight_layout=True)
    b = f.add_subplot(111)
    # ============================================================================
    global Potenzial
    global Strom
    times_of_exp = data_condensed[data_condensed[::, 3] == Cycle_to_analyze, 0]
    Potenzial = data_condensed[data_condensed[::, 3] == Cycle_to_analyze, 1]
    Strom = data_condensed[data_condensed[::, 3] == Cycle_to_analyze, 2]

    PotenzialRAW = data[data[::, 4] == Cycle_to_analyze, 2]
    StromRAW = data[data[::, 4] == Cycle_to_analyze, 3]

    b.plot(PotenzialRAW, StromRAW, linestyle='-', marker='', color='lightgrey', label="raw data")
    b.plot(Potenzial, Strom, linestyle='-', marker='', color='k', label="step-average")
    b.legend(frameon=False, fontsize=12)
    b.set_xlabel('E vs. Ref. / V', fontsize=12)
    b.set_ylabel('I / mA', fontsize=12)
    for axis in ['top', 'bottom', 'left', 'right']:
        b.spines[axis].set_linewidth(2)
        b.spines[axis].set_color('k')
    b.tick_params(tickdir='in', width=2, length=6, labelsize=12)
    canvas = FigureCanvasTkAgg(f, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)

    txt_filename = asksaveasfilename(defaultextension='.txt')
    outfile_CV_Data = open(txt_filename, 'w')
    outfile_CV_Data.write("E_vs_Ref_in_V")
    outfile_CV_Data.write("\t")
    outfile_CV_Data.write("I_in_microampere")
    outfile_CV_Data.write("\n")
    for i in range(len(Potenzial)):
        outfile_CV_Data.write(str(Potenzial[i]))
        outfile_CV_Data.write("\t")
        outfile_CV_Data.write(str(1000 * Strom[i]))
        outfile_CV_Data.write("\n")
    outfile_CV_Data.close()

"""



