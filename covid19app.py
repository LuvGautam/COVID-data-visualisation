#PROJECT: COVID19 Statstics\Visualisation

import tkinter as tk
from tkinter.font import Font
from tkinter import ttk

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import matplotlib.animation as animation

import numpy as np
import time
from sqlalchemy import create_engine
import pandas as pd
from datetime import date
import locale
import math
import itertools as it
import platform

#This module is imported to supress the warning raised by matplotlib as it
#is a known bug in mpl.
import warnings
warnings.filterwarnings("ignore")

#This import statement runs the module and download the data files from
#internet and write them to database
import covid19data

#Setting directory of database(data.db)
if platform.system() == 'Windows':
    directory = 'data\\'
else:
    directory = 'data/'


#Setting locale for seperating of digits of a number using (,)
locale.setlocale(locale.LC_ALL, 'English_India')

#Setting pandas options for debugging\output to shell
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

#Reading Data from Database file and creating neccessary DataFrames
engine = create_engine(f'sqlite:///{directory}data.db', echo=False)

in_tot_df = pd.read_sql('india_total', con=engine, index_col='ID')
in_tot_df.index.name = None

in_daily_df = pd.read_sql('india_daily', con=engine, index_col='ID')
in_daily_df.index.name = None

global_df = pd.read_sql('global', con=engine, index_col='ID')
global_df.index.name = None


#Creating Master Tk window and defining associated functions
def quit_me():
    print('quit')
    window.quit()
    window.destroy()

window = tk.Tk()
window.protocol("WM_DELETE_WINDOW", quit_me)#To destroy window when
                                            #window close button is pressed 
window.title('COVID19 Data Visualiser')
window.state('zoomed')
window['bg'] = 'white'

#Defining fonts for different texts(heading and everything else part of GUI) 
head_font = Font(family="Segoe UI",size=14)#,weight="bold"
opt_lbl_font = Font(family="Segoe UI",size=12)

#Setting font of all Combobox that are associated with our GUI window
window.option_add("*TCombobox*Listbox*Font", opt_lbl_font)

#Getting screen width and height(in pixels) to calculte dimensions
#of various Frames
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

#Frame widget which contains line plot, table and info
plot_frm = tk.Frame(master = window,
                    bg = 'white',
                    borderwidth = 0,
                    width=int((2/3)*screen_width),
                    height=screen_height)
plot_frm.pack(side='left')
plot_frm.pack_propagate(False)#Frame does not resize according to
                              #containin widgets

#Frame widget which contains all buttons, options and bar plot
opt_frm = tk.Frame(master = window,
                   bg = 'white',
                   width=int((1/3)*screen_width),
                   height=screen_height)
opt_frm.pack(side='right')
opt_frm.pack_propagate(False)

#Dividing opt_frm into 2 equal Frames vertically
#One for bar plot and One for options
opt_frms = {}

for i in range(1,3):
    opt_frms[i] = tk.Frame(master = opt_frm,
                           bg = 'white',
                           borderwidth = 1,
                           width=int((1/3)*screen_width),
                           height=int((1/2)*screen_height))
    opt_frms[i].pack()
    opt_frms[i].pack_propagate(False)
    opt_frms[i].grid_propagate(False)

#Setting Frame containing options and buttons
opt_frms[2]['bg'] = 'azure'
opt_frms[2]['relief'] = tk.RIDGE
opt_frms[2]['borderwidth'] = 4


#Label to display the title(heading) of options frame
opt_lbl = tk.Label(
    master = opt_frms[2],
    text="Options",
    font = head_font,
    bg='azure',
    height=2)
opt_lbl.grid(row=0,column=0,columnspan=2,sticky='ew')

#Padding between different options
pady = 12


#Creating Country label and Country Combobox 
country_lbl = tk.Label(
    master = opt_frms[2],
    text="Country :  ",
    font = opt_lbl_font,
    #fg="white",
    bg='azure',
    #width=10,
    #height=2
)
country_lbl.grid(row=1, column=0, pady=pady, sticky='w')

#Funtion to activate/deactivate other options based on value selected
#in Country_cbx
def country_opt(event):
    active = "normal" if country_cbx.get() == "India" else "disabled"
    state_cbx.configure(state=active)

    if country_cbx.get() != 'India':
        state_cbx.set('(Aggregate)')

    state_opt("<<ComboboxSelected>>")

country = tk.StringVar() 
country_cbx = ttk.Combobox(opt_frms[2],
                           width=43,
                           textvariable=country,
                           font=opt_lbl_font)
                           #command=country_opt)

# Adding combobox drop down list
all_countries = list(global_df['country'].unique())
all_countries.remove('World')
all_countries.sort()
all_countries.insert(0, 'World')
country_cbx['values'] = all_countries 
  
country_cbx.grid(row=1, column=1, pady=15) 
country_cbx.current(0)
country_cbx.bind("<<ComboboxSelected>>", country_opt)

#Creating State label and State ComboBox 
state_lbl = tk.Label(master = opt_frms[2],
                     text="State/UT :  ",
                     font = opt_lbl_font,
                     bg='azure')
state_lbl.grid(row=2, column=0, pady=pady, sticky='w')

#Funtion to change plot combobox list based on value selected
#in state_cbx
def state_opt(event):
    state = state_cbx.get()

    if state == '(Aggregate)':
        plot_cbx['values'] = ['Confirmed (Aggregate)',
                              'Deceased (Aggregate)',
                              'Confirmed, Deceased (Aggregate)']
        plot_cbx.current(0)
    else:
        plot_cbx['values'] = ['Confirmed (Daily)',
                              'Deceased (Daily)',
                              'Recovered(Daily)',
                              'Confirmed, Recovered, Deceased (Daily)']
        plot_cbx.current(0)

state = tk.StringVar() 
state_cbx = ttk.Combobox(opt_frms[2],
                         width=43,
                         textvariable=state,
                         height=7,
                         font=opt_lbl_font) 

# Adding combobox drop down list
all_states = list(in_tot_df['state'].unique())
all_states.remove('Total')
all_states.sort()
all_states.insert(0, '(Aggregate)')
state_cbx['values'] = all_states
  
state_cbx.grid(row=2, column=1, pady=pady) 
state_cbx.current(0)
state_cbx.bind("<<ComboboxSelected>>", state_opt)
state_cbx.configure(state='disabled')


#Function to scroll the combobox list to the value according
#the character keypress
#Applied to country_cbx and state_cbx
def popup_key_pressed(event, obj):
    values = obj.cget("values")
    for i in it.chain(range(obj.current() + 1,len(values)),range(0,obj.current())):
        if event.char.lower() == values[i][0].lower():
            obj.current(i)
            obj.icursor(i)
            obj.tk.eval(event.widget + ' selection clear 0 end') #clear current selection
            obj.tk.eval(event.widget + ' selection set ' + str(i)) #select new element
            obj.tk.eval(event.widget + ' see ' + str(i)) #spin combobox popdown for selected element will be visible
            return

pd = country_cbx.tk.call('ttk::combobox::PopdownWindow', country_cbx) #get popdownWindow reference 
lb = pd + '.f.l' #get popdown listbox
country_cbx._bind(('bind', lb),"<KeyPress>",
                  lambda event, obj=country_cbx: popup_key_pressed(event, obj),None)

pd2 = state_cbx.tk.call('ttk::combobox::PopdownWindow', state_cbx) #get popdownWindow reference 
lb2 = pd2 + '.f.l' #get popdown listbox
state_cbx._bind(('bind', lb2),"<KeyPress>",
                lambda event, obj=state_cbx: popup_key_pressed(event, obj),None)


#Creating Plot label and Plot ComboBox 
plot_lbl = tk.Label(
    master = opt_frms[2],
    text="Plot :  ",
    font = opt_lbl_font,
    bg='azure')
plot_lbl.grid(row=3, column=0, pady=pady, sticky='w')

plot_type = tk.StringVar() 
plot_cbx = ttk.Combobox(opt_frms[2],
                         width=43,
                         textvariable=plot_type,
                         font=opt_lbl_font) 

# Adding combobox drop down list
plot_types1 = [
    'Confirmed (Aggregate)',
    'Deceased (Aggregate)',
    'Confirmed, Deceased (Aggregate)']
plot_cbx['values'] = plot_types1
  
plot_cbx.grid(row=3, column=1, pady=pady) 
plot_cbx.current(0)


#Creating Radio buttons for selection of prefered numeral system
#Indian or International
ttk.Style().configure("TButton", padding=6, relief="flat",
   background="#ccc", font = head_font)

rdbtn_style = ttk.Style()
rdbtn_style.configure('my.TRadiobutton',
                      background='azure',
                      font=opt_lbl_font)

unit_type = tk.StringVar()
int_rdbtn = ttk.Radiobutton(opt_frms[2],
                            text='International Numeral System',
                            value='US',
                            variable=unit_type,
                            style='my.TRadiobutton',
                            width=25)
int_rdbtn.grid(row=4, column=0, columnspan=2, pady=pady, padx=20, sticky='w')
int_rdbtn.invoke()

ind_rdbtn = ttk.Radiobutton(opt_frms[2],
                            text='Indian Numeral System',
                            value='IN',
                            variable=unit_type,
                            style='my.TRadiobutton',
                            width=20)
ind_rdbtn.grid(row=4, column=0, columnspan=2, pady=pady, sticky='e')

#Function to return a string or list of strings formatted from numbers with
#commas as seperator according to units 
def seperator(val, unit):
    if isinstance(val, (int, float)):
        if unit == 'IN':
            return f'{val:n}'
        elif unit == 'US':
            return f'{val:,}'
        else:
            raise Exception('Unsupporetd unit type.')

    elif isinstance(val, list):
        if unit == 'IN':
            return [f'{num:n}' for num in val]
        elif unit == 'US':
            return [f'{num:,}' for num in val]
        else:
            raise Exception('Unsupporetd unit type.')

    else:
        raise Exception('Unsupporetd value type. Only int and list\
                            of ints supported.')

#Function to round up a int or float to int according to nth place
def roundup(x,n):
	return (int(math.ceil(x / 10**n)) * 10**n)


global ani
global anib

#Plot/Refresh Button command function
#This function contains all the functions and code to plot/refesh the
#matplotlib plots and table(create and configure objects)
def button_press():
    global ani
    global anib
    plot_flag = True
    plot_flag_bar = True
    
    #Getting the chosen options
    country = country_cbx.get()
    state = state_cbx.get()
    plot = plot_cbx.get()

    #Figure containing line plot, table and info. It is contained in
    #corresponding Frame
    fig = Figure(figsize=(10, 8.6))
    #Figure containing bar plot
    small_fig = Figure(figsize=(5, 4.3))

    #Removing any previous plots from figures so that figures can be
    #refreshed with new plots
    for ax in fig.axes:
        ax.remove()
    for ax in small_fig.axes:
        ax.remove()

    #Creating DataFrames and objects which will be used to draw and configure
    #the plots according to chosen options
    if ((country != 'India') or
        (country == 'India' and state == '(Aggregate)')):

        #Creating df for line plot
        df = global_df[global_df['country']==country].copy()
        df.rename(columns={'total_cases':'confirmed', 'total_deaths':'deceased'},
                  inplace=True)

        #Creating df for bar plot
        date_max = global_df['date'].max().strftime('%Y-%m-%d')
        bar_df = global_df[global_df['date']==date_max].copy()
        bar_df = bar_df.sort_values(by='total_cases', ascending=False).head(6)
        bar_df.rename(columns={'total_cases':'confirmed',
                               'total_deaths':'deceased'},inplace=True)
        bar_df.reset_index(drop=True, inplace=True)
        bar_df.drop(index=0, inplace=True)
        bar_loc = bar_df['country'].values
        bar_val = bar_df['confirmed'].values
        bar_anim_val = []
        for val in bar_val:
            bar_anim_val.append(np.linspace(0,val,100))
        bar_title = 'Top 5 countries with \nmost confirmed cases'

        #Creating text for info
        if country == 'India':
            txt_str = ' '*41 + df['date'].max().strftime('%d-%b-%Y')\
                      + '\n' + country\
                      + '\nTotal Cases Confirmed : '\
                      + seperator(int(df['confirmed'].max()), unit_type.get())\
                      + '\nTotal Cases Active : '\
                      + seperator(int(in_tot_df[in_tot_df.state=='Total']['active'].max()), unit_type.get())\
                      + '\nTotal Infected Recovered : '\
                      + seperator(int(in_tot_df[in_tot_df.state=='Total']['recovered'].max()), unit_type.get())\
                      + '\nTotal Infected Deceased : '\
                      + seperator(int(in_tot_df[in_tot_df.state=='Total']['deaths'].max()), unit_type.get())

        else:
            txt_str = ' '*41 + df['date'].max().strftime('%d-%b-%Y')\
                      + '\n' + country\
                      + '\nTotal Cases Confirmed : '\
                      + seperator(int(df['confirmed'].max()), unit_type.get())\
                      + '\nTotal Infected Deceased : '\
                      + seperator(int(df['deceased'].max()), unit_type.get())
        
        if plot == 'Confirmed (Aggregate)':
            df = df[['date', 'confirmed']]
            line_colors = ['b']
        elif plot == 'Deceased (Aggregate)':
            df = df[['date', 'deceased']]
            line_colors = ['r']
        elif plot == 'Confirmed, Deceased (Aggregate)':
            df = df[['date', 'confirmed', 'deceased']]
            line_colors = ['b']

    elif country == 'India' and state != '(Aggregate)':

        #Creating df for line plot
        df = in_daily_df[in_daily_df['state']==state].copy()

        #Creating df for bar plot
        bar_df = in_tot_df.sort_values(by='confirmed', ascending=False).copy()
        bar_df = bar_df.head(6)
        bar_df.reset_index(drop=True, inplace=True)
        bar_df.drop(index=0, inplace=True)
        bar_loc = bar_df['state'].values
        bar_val = bar_df['confirmed'].values
        bar_anim_val = []
        for val in bar_val:
            bar_anim_val.append(np.linspace(0,val,100))
        bar_title = 'Top 5 states with \nmost confirmed cases'

        #Creating df and text for info
        df2 = in_tot_df[in_tot_df['state']==state].copy()
        txt_str = ' '*41 + df2['lastupdatedtime'].max().strftime('%d-%b-%Y')\
          + '\n' + state\
          + '\nTotal Cases Confirmed : '\
          + seperator(int(df2['confirmed'].max()), unit_type.get())\
          + '\nTotal Cases Active : '\
          + seperator(int(df2['active'].max()), unit_type.get())\
          + '\nTotal Infected Recovered : '\
          + seperator(int(df2['recovered'].max()), unit_type.get())\
          + '\nTotal Infected Deceased : '\
          + seperator(int(df2['deaths'].max()), unit_type.get())

        if plot == 'Confirmed (Daily)':
            df = df[['date', 'confirmed']]
            line_colors = ['b']
        elif plot == 'Deceased (Daily)':
            df = df[['date', 'deceased']]
            line_colors = ['r']
        elif plot == 'Recovered(Daily)':
            df = df[['date', 'recovered']]
            line_colors = ['#0bdb00']
        elif plot == 'Confirmed, Recovered, Deceased (Daily)':
            df = df[['date', 'confirmed', 'recovered', 'deceased']]
            line_colors = ['b','#0bdb00']


    #Creating line plot and setting axes properties
    x_axis = list(df.columns)[0]
    y_axis = list(df.columns)[1:]
    
    ax1 = fig.add_subplot(2,2,(1,2), label='ax1')

    y_plots = y_axis[:] if len(y_axis)==1 else y_axis[:-1]

    for y,color in zip(y_plots, line_colors):
        line, = ax1.plot(df[x_axis], df[y], color,
                         label=y.replace('_',' '))

    #Creating twin axis plot
    if len(df.columns) > 2:
        ax11 = ax1.twinx()
        ax11.plot(df[x_axis], df[y_axis[-1]], 'r', label='deceased')
        ax11.set_ylabel(y_axis[-1].replace('_', ' ').title())
        ax11.ticklabel_format(axis='y', style='plain')

    #Storing all line objects in single list
    lines = ax1.lines + ax11.lines if len(df.columns) > 2 else ax1.lines

    if state == '(Aggregate)':
        ax1.set_title(country+'\n'+plot, zorder=0.5)
    else:
        ax1.set_title(state+'\n'+plot, zorder=0.5)
    ax1.set_xlabel(x_axis.title(), size=11)
    ax1.ticklabel_format(axis='y', style='plain')

    if len(y_axis) <= 2:
        ylabel = y_axis[0].replace('_', ' ').title() 
    else:
        ylabel = y_axis[0]+', '+y_axis[1]
        ylabel = ylabel.replace('_', ' ').title()
    ax1.set_ylabel(ylabel)
    
    pos_ax1 = ax1.get_position()#Bbox(x0=0.125, y0=0.53, x1=0.8999999999999999, y1=0.88)
    pos_ax1.y1 = 0.92
    pos_ax1.x1 = 0.90
    pos_ax1.x0 = 0.125
    ax1.set_position(pos_ax1)
    
    #Setting legend for line plot
    lines1, labels1 = ax1.get_legend_handles_labels()
    labels1 = [s.title() for s in labels1]
    lines11, labels11 = [], []
    if len(df.columns) > 2:
        lines11, labels11 = ax11.get_legend_handles_labels()
        labels11 = [s.title() for s in labels11]
    ax1.legend(lines1 + lines11, labels1 + labels11, loc='upper left')

    top_ylim = roundup(ax1.get_ylim()[1], len(str(int(ax1.get_ylim()[1])))-2)
    ax1.set_ylim(top=top_ylim)

    if len(df.columns) > 2:
        top_ylim = roundup(ax11.get_ylim()[1], len(str(int(ax11.get_ylim()[1])))-2)
        ax11.set_ylim(top=top_ylim)

    #Formatting x axis tick labels (Date type)
    date_form = DateFormatter("%b")
    ax1.xaxis.set_major_formatter(date_form)


    #Creating for data table and setting its properties
    ax2 = fig.add_subplot(2, 2, (3,4), label='ax2')
    pos_ax2 = ax2.get_position()#Bbox(x0=0.125, y0=0.10999999999999999, x1=0.8999999999999999, y1=0.46)
    pos_ax2.x0 = 0.02
    pos_ax2.x1 = 0.98
    pos_ax2.y1 = 0.36
    ax2.set_position(pos_ax2)

    table_df = df.copy()
    table_df.loc[:,'date'] = table_df['date'].dt.strftime('%d-%b-%Y')
    for col in table_df.columns[1:]:
        table_df.loc[:, col] = seperator(list(df[col].values), unit_type.get())
    colLabels = [s.replace('_', ' ').title() for s in table_df.columns]
    cellColours = [['#DFF6FF' if row%2!=0 else 'w' for i in range(len(table_df.columns))]
                  for row in range(1,6)]
    data_table = ax2.table(cellText=table_df.tail(5).values,
                           colLabels=colLabels,
                           colWidths=[.15]*len(df.columns),
                           cellColours=cellColours,
                           loc='lower left')

    if state == '(Aggregate)':
        ax2.set_title(country+'\'s Latest Dataset')
    else:
        ax2.set_title(state+'\'s Latest Dataset')

    cellDict = data_table.get_celld()
    for i in range(0,len(df.columns)):
        cellDict[(0,i)].set_height(.15)
        for j in range(1,len(df.tail(5).values)+1):
            cellDict[(j,i)].set_height(.14)
    
    data_table.set_fontsize(12)
    #ax2.axis('tight')
    ax2.axis('off')

    #Creating text info
    text = ax2.text(0.65, 0.82,
                    txt_str,
                    verticalalignment='top',
                    linespacing=1.8,
                    #style='italic',
                    fontsize=12)
    
    #Creating box around text info
    ax2.add_patch(patches.Rectangle((0.64, 0.02), 0.355, 0.85,
                                    #color='b',
                                    fill=False,
                                    transform=ax2.transAxes))


    #Creating bar plot and setting its properties
    ax_bar = small_fig.add_subplot(111, label='ax_bar')

    for i,s in enumerate(bar_loc):
        bar_loc[i] = s.replace(' ','\n')
        
    bars = ax_bar.bar(bar_loc, bar_val)
    ax_bar.set_title(bar_title, zorder=0.5)
    ax_bar.set_ylabel('Confirmed')
    ax_bar.set_xticklabels(bar_loc, rotation=20,
                           #ha='right', rotation_mode='anchor',
                           fontsize=9.5)
    pos_ax_bar = ax_bar.get_position()#Bbox(x0=0.125, y0=0.10999999999999999, x1=0.9, y1=0.88)
    #print(ax_bar.get_position())
    pos_ax_bar.x0 = 0.20
    pos_ax_bar.x1 = 0.95
    pos_ax_bar.y0 = 0.15
    ax_bar.set_position(pos_ax_bar)
    ax_bar.ticklabel_format(axis='y', style='plain')

    for line in lines:
        line.set_ydata([np.nan] * len(df['date']))
        
    #Embedding matplotlib figures into tkinter canvas widget
    canvas = FigureCanvasTkAgg(fig, master=plot_frm)
    canvas.draw()

    #Setting y tick labels for line plot 
    l = []
    for t in ax1.get_yticklabels():
        s = t.get_text().replace('−','-')
        if '.' in s:
            l.append(float(s))
        else:
            l.append(int(s))
            
    ax1.set_yticklabels(seperator(l, unit_type.get()))

    if len(df.columns) > 2:
        l = []
        for t in ax11.get_yticklabels():
            s = t.get_text().replace('−','-')
            if '.' in s:
                l.append(float(s))
            else:
                l.append(int(s))
                
        ax11.set_yticklabels(seperator(l, unit_type.get()))
        
    '''
    ax1.set_yticklabels(
        seperator([int(t.get_text().replace('−','-')) for t in ax1.get_yticklabels()],
                   unit_type.get())
        )
    '''
    
    canvas.get_tk_widget().grid(row=0, column=0)
    
    canvas2 = FigureCanvasTkAgg(small_fig, master=opt_frms[1])
    canvas2.draw()
    
    ax_bar.set_yticklabels(
        seperator([int(t.get_text().replace('−','-')) for t in ax_bar.get_yticklabels()],
                   unit_type.get())
        )
    
    canvas2.get_tk_widget().grid(row=0, column=0)
    
    


    #Annotating the line plot according to the hovering of mouse pointer on
    #the line
    if len(df.columns) == 2:
        annot = ax1.annotate("", xy=(0,0), xytext=(-20,20),
                             textcoords="offset points",
                             bbox=dict(boxstyle="round", fc="w"))#,arrowprops=dict(arrowstyle="->")
        annot.set_visible(False)

        #marker, = ax1.plot(df.iat[0,0],0,line_colors[0]+'o', label='marker')
        #marker, = ax1.plot(df.iat[0,0], df.iat[0, 1],
         #                  line_colors[0]+'o', label='marker')
        #marker.set_visible(False)

        def update_annot(ind, marker):
            x,y = lines[0].get_data()
            x = x.values
            y = y.values
            table_df.reset_index(drop=True,inplace=True)
            #print(x,y)
            annot.xy = (x[ind["ind"][0]], y[ind["ind"][0]])
            text = "{} | {}".format(table_df.iloc[ind["ind"][0],1], #y[ind["ind"][0]]
                                   table_df.iloc[ind["ind"][0],0])#x[ind["ind"][0]] 
            #text = "{}, {}".format(" ".join(list(map(str,ind["ind"]))), 
             #                      " ".join([names[n] for n in ind["ind"]]))
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.9)

            marker.set_data(x[ind["ind"][0]], y[ind["ind"][0]])
            return marker
            #print(marker.get_data())
            
        def hover(event):
            nonlocal plot_flag
            if plot_flag:
                for y,color in zip(y_plots, line_colors):
                    ax1.plot(df[x_axis], df[y], color,
                             label=y.replace('_',' '))
                plot_flag ^= True
                    
            for line in ax1.lines:
                if line.get_label() == 'marker':
                    line.remove()
            
            marker, = ax1.plot(df.iat[0,0], df.iat[0,1],
                               'o', c=line_colors[0], label='marker',
                               visible=False)
   
            vis = annot.get_visible()
            if event.inaxes == ax1:
                cont, ind = lines[0].contains(event)
                if cont:
                    #print(ind)
                    marker1 = update_annot(ind, marker)
                    annot.set_visible(True)
                    marker1.set_visible(True)
                    canvas.draw_idle()
                else:
                    #marker.remove()
                    if vis:
                        annot.set_visible(False)
                    canvas.draw_idle()
            else:
                #marker.remove()
                annot.set_visible(False)
                canvas.draw_idle()

        #canvas.mpl_connect("motion_notify_event", hover)#lambda event: hover(event, plot_flag)


    #Adding animation to line plot
    #print(df)
    def init():  # only required for blitting to give a clean slate.
        for line in lines:
            if line.get_label() != 'marker':
                line.set_ydata([np.nan] * len(df['date']))
        canvas.draw()
        return lines

    def animate(i):
        for line in lines:
            if line.get_label() != 'marker':
                line.set_xdata(df['date'][:i])
                line.set_ydata(df[line.get_label()][:i])
        '''
        nonlocal plot_flag
        if plot_flag == False:
            ax1.lines.pop(0)
            plot_flag = True
        '''
        if i == len(df['date']) and len(df.columns) == 2:
            canvas.mpl_connect("motion_notify_event", hover)
        return lines

    ani = animation.FuncAnimation(
        fig, animate, init_func=init, frames=range(1, len(df['date'])+1),
        interval=0, blit=True, repeat=False)#, repeat=False, save_count=50
    

    #Adding animation to bar plot
    def initb():
        for bar in bars:
            bar.set_height(0)
        canvas.draw()
        return bars

    def animateb(i):
        for j, bar in enumerate(bars):
            bar.set_height(bar_anim_val[j][i])
        return bars

    anib = animation.FuncAnimation(
         fig, animateb, init_func=initb, frames=range(1,100),
         interval=0, blit=True, repeat=False)#, repeat=False, save_count=50

    #Annotating the bar plot according to the hovering of mouse pointer on
    #the bar
    annot_bar = ax_bar.annotate("", xy=(0,0), xytext=(0,12),
                                ha='center',
                                textcoords="offset points")
                                #bbox=dict(boxstyle="round", fc="black", ec="b", lw=2),
                                #arrowprops=dict(arrowstyle="->"))
    annot_bar.set_visible(False)

    def update_annot_bar(bar):
        x = bar.get_x()+bar.get_width()/2.
        y = bar.get_height()
        annot_bar.xy = (x,y)
        text = "{}".format(seperator(int(bar.get_height()), unit_type.get()))
        annot_bar.set_text(text)
        #annot.get_bbox_patch().set_alpha(0.4)

    def hover_bar(event):
        nonlocal plot_flag_bar
        if plot_flag_bar:
            ax_bar.bar(bar_loc, bar_val, color='#1f77b4')
            plot_flag_bar ^= True
            
        vis = annot_bar.get_visible()
        if event.inaxes == ax_bar:
            for bar in bars:
                cont, ind = bar.contains(event)
                if cont:
                    update_annot_bar(bar)
                    annot_bar.set_visible(True)
                    canvas2.draw_idle()
                    return
                else:
                    annot_bar.set_visible(False)
                    canvas2.draw_idle()
        else:
            annot_bar.set_visible(False)
            canvas2.draw_idle()

    canvas2.mpl_connect("motion_notify_event", hover_bar)


#Creating Plot/Refresh button
plot_btn = ttk.Button(master = opt_frms[2],
                      text = 'Plot / Refresh',
                      command = button_press)

plot_btn.grid(row=5, column=0, columnspan=2, padx=120, pady=30, sticky='w')

#Creating Quit button
quit_btn = ttk.Button(master = opt_frms[2],
                      text = 'Quit',
                      command = quit_me)

quit_btn.grid(row=5, column=0, columnspan=2, padx=70, pady=30, sticky='e')

window.mainloop()


