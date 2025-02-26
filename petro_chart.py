import re
import json
import math
import os
import random
import time
from tkinter import *
from tkinter import filedialog, ttk

import lasio
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
import graph_modules

BASE_DIR = os.path.dirname(__file__)


class Chart:
    def __init__(self, dots, **kwargs):
        self.dots = dots
        self.parameters = {'color': 'black', 'type': 'line', 'name': None, 'unit': None, 'borders_color': ['b'],
                           'fill_side': 'right', 'min_border': float('nan'), 'max_border': float('nan'),
                           'borders': {}}

        for key, value in kwargs.items():
            if key in self.parameters:
                if value is not None:
                    self.parameters[key] = value

        self.type_line = StringVar(value=self.parameters.get('type'))
        self.fill_side = StringVar(value=self.parameters.get('fill_side'))
        self.min_border = StringVar(value=self.parameters.get('min_border'))
        self.max_border = StringVar(value=self.parameters.get('max_border'))
        self.parameters['borders'] = {-math.inf, math.inf}.union(self.parameters.get('borders'))

    def get_dots_with_border(self):
        border_dots = self.dots.copy()

        min_border = float(self.get_min_border())
        max_border = float(self.get_max_border())

        if self.get_max_border() is not None:
            for i in range(len(border_dots)):
                border_dots[i] = max_border if border_dots[i] > max_border else border_dots[i]

        if self.get_min_border() is not None:
            for i in range(len(border_dots)):
                border_dots[i] = min_border if border_dots[i] < min_border else border_dots[i]

        return border_dots

    def get_type_line(self):
        if self.type_line is None:
            return self.parameters.get('type')
        return self.type_line.get()

    def get_fill_side(self):
        if self.fill_side is None:
            return self.parameters.get('fill_side')
        return self.fill_side.get()

    def get_min_border(self):
        if self.min_border is not None:
            value = self.min_border.get()
        elif self.parameters.get('min_border') is not None:
            value = self.parameters.get('min_border')
        if str(value).isdigit():
            return float(value)
        return float(-math.inf)

    def get_max_border(self):
        if self.max_border is not None:
            value = self.max_border.get()
        elif self.parameters.get('max_border') is not None:
            value = self.parameters.get('max_border')
        if str(value).isdigit():
            return float(value)
        return float(math.inf)


class Cell:
    def __init__(self, window, null, name, lineColor, leftValue, measure, rightValue):
        self.cell_frame = Frame(window, background='gray', highlightbackground='black', highlightthickness=1)
        self.cell_frame.pack(side=TOP, fill='both')
        if not null:
            self.cell_frame.grid_columnconfigure(0, weight=1)

            title = Label(self.cell_frame, bg='gray', text=name)
            title.place(height=20)
            title.grid(row=0, column=0, columnspan=3, sticky=E + W + S + N)

            line = Frame(self.cell_frame, width=self.cell_frame.winfo_width(), height=1, bg=lineColor)
            line.grid(row=1, column=0, columnspa=3, sticky=W + E)

            leftV = Label(self.cell_frame, bg='gray', text=leftValue)
            leftV.place(height=20)
            leftV.grid(row=2, column=0, sticky=W)

            measure = Label(self.cell_frame, bg='gray', text=measure)
            measure.place(height=20)
            measure.grid(row=2, column=0)

            label_4 = Label(self.cell_frame, bg='gray', text=rightValue)
            label_4.place(height=20)
            label_4.grid(row=2, column=2, sticky=E)

    def destroy(self):
        self.cell_frame.pack_forget()

    def pack(self):
        self.cell_frame.pack(fill='both', side=TOP)


class Pad:
    def __init__(self, frame):
        self.log = BooleanVar(frame, value=0)

        self.border_scale_fixed = BooleanVar(frame, value=0)

        self.type = StringVar(frame, value='line')

        self.width = IntVar(frame, value=3)

        self.line_quantity = StringVar(frame, value=5)
        self.charts = []

    def add_chart(self, chart):
        self.charts.append(chart)


class PadFrame:
    height = 8

    def __init__(self, pads_frame, width=None):
        self.cell = []
        self.width = IntVar(value=3) if width is None else width
        self.fig, self.chart = plt.subplots(nrows=1, ncols=1, figsize=(self.width.get(), self.height))
        self.fig.subplots_adjust(left=-0.003, bottom=0, right=1, top=1, wspace=0, hspace=0)

        self.pad_frame = Frame(pads_frame)
        self.pad_frame.pack(side=LEFT, fill='both')

        self.cell_frame = Frame(self.pad_frame)  # , text='cell_frame')
        self.cell_frame.pack(side=TOP, fill='both')

        self.pad_menu_frame = Frame(self.pad_frame)  # , text='pad_menu_frame')
        self.pad_menu_frame.pack(side=BOTTOM, fill='both')

        self.canvas_frame = Frame(self.pad_frame)
        self.canvas_frame.pack(side=TOP, fill='both')

        self.canvas = FigureCanvasTkAgg(self.fig, self.canvas_frame)
        self.canvas_tk_widget = self.canvas.get_tk_widget()
        self.canvas_tk_widget.pack(side=BOTTOM)

    i = 1
    def update_chart(self):
        self.i += 1
        if self.width.get() != int(self.fig.get_figwidth()):
            plt.close(self.canvas.figure)
            self.canvas_tk_widget.destroy()
            self.fig.set_size_inches(self.width.get(), self.height)
            self.canvas = FigureCanvasTkAgg(self.fig, self.canvas_frame)
            self.canvas_tk_widget = self.canvas.get_tk_widget()
            self.canvas_tk_widget.pack()
        self.canvas.draw()

    def add_empty_cell(self, quntity_empty_cell):
        for x in range(quntity_empty_cell):
            new_cell_frame = Cell(self.cell_frame, False, '', 'grey', '', '', '')
            self.cell.append(new_cell_frame)

    def reset(self):
        self.chart.clear()
        for child in self.cell:
            child.destroy()


class App:
    def __init__(self, root):
        self.pad_frames = []
        self.min_y = None
        self.max_y = None
        self.start = None
        self.end = None
        self.pads = []
        self.max_pad = 5

        self.first_show_pad = 0
        self.filenames = []
        self.filenames_url = []
        self.curves = {}
        self.depth_dots = []

        self.root = root

        well_name = 'Планшеты'
        self.pads_frame = LabelFrame(self.root, text=well_name)
        self.pads_frame.pack(side=LEFT)

        # try:
        #    DATE = las.sections.get('Well').__getattr__('DATE').__getitem__('value')
        #    COUNTRY = las.sections.get('Well').__getattr__('COUNTRY').__getitem__('value')
        #    ORIGINALWELLNAME = las.sections.get('Well').__getattr__('ORIGINALWELLNAME').__getitem__('value')
        #    FLD = las.sections.get('Well').__getattr__('FLD').__getitem__('value')
        #    well_name = DATE + '  ' + COUNTRY + '   ' + FLD + '   ' + ORIGINALWELLNAME
        # except:
        #    well_name = 'Планшеты'

    def add_curves_from_file(self, filename):
        las = lasio.read(filename, encoding='utf-8')
        match = re.findall(r'\w*.las', filename)
        short_filename = match[0].replace('.las', '')

        if short_filename in self.filenames:
            self.open_error_window('Файл:' + match[0] + ' уже добавлен')
            return

        self.filenames.append(short_filename)
        self.filenames_url.append(filename)

        self.depth_dots.append(las.items()[0][1])

        self.start = self.min_y = min(las.items()[0][1])
        self.end = self.max_y = max(las.items()[0][1])

        for item in las.items():
            self.curves['\'' + str(item[0]) + '\' ' + short_filename] = {
                'unit': las.sections.get('Curves').__getitem__(item[0]).__getitem__('unit'),
                'dots': item[1],
            }

    def get_or_create_pad_frame(self, pad_number):
        if pad_number >= len(self.pad_frames):
            self.pad_frames.append(PadFrame(self.pads_frame, width=self.pads[pad_number].width))
            return self.pad_frames[-1]
        return self.pad_frames[pad_number]

    def set_first_show_pad(self, new_first_show_pad):
        if len(self.pads) < new_first_show_pad:
            self.first_show_pad = len(self.pads) - 1
            return

        if new_first_show_pad < 0:
            self.first_show_pad = 0
            return

        self.first_show_pad = new_first_show_pad

    def open_error_window(self, message):
        error_window = Toplevel(self.root)
        label_error = Label(text=message, master=error_window, fg='red', font='Arial 32')
        label_error.pack()

    def zoom_scale(self, middle_y):
        scale = (self.end - self.start) / 4
        self.set_new_border(middle_y - scale, middle_y + scale)

    def reduce_scale(self):
        scale = (self.end - self.start)
        middle_y = self.start + scale / 2
        self.set_new_border(middle_y - scale, middle_y + scale)

    def set_new_border(self, new_start, new_end):
        if abs(new_end - new_start) < 10 or (self.start == new_start and self.end == new_end):
            return False

        if new_end < self.max_y:
            self.end = new_end
        else:
            self.end = self.max_y

        if new_start > self.min_y:
            self.start = new_start
        else:
            self.start = self.min_y
            self.start = self.min_y

        return True

    def scale_move(self, orientation):
        delta = abs(self.start - self.end) / 2

        if orientation == 'up':
            if self.start - delta < self.min_y:
                delta = abs(self.min_y - self.start)
            return self.set_new_border(self.start - delta, self.end - delta)
        else:
            if self.end + delta > self.max_y:
                delta = abs(self.max_y - self.end)
            return self.set_new_border(self.start + delta, self.end + delta)

    def add_pad(self):
        pad = Pad(self.root)
        self.pads.append(pad)
        return pad

    def add_chart(self, pad_number, chart_name):
        self.pads[pad_number].add_chart(Chart(self.curves[chart_name].get('dots'),
                                              name=chart_name,
                                              unit=self.curves.get(chart_name).get('unit')))

    def max_pads_cells(self):
        max_len = 0
        for pad in self.pads:
            max_len = max(len(pad.charts), max_len)
        return max_len

    def delete_pad(self, pad_number):
        self.pads.pop(pad_number)

    def dots_range(self, dots):
        new_y = []
        new_x = []
        depth_dots_number = 0

        for i in range(len(self.depth_dots)):
            if len(self.depth_dots[i]) == len(dots):
                depth_dots_number = i

        for i in range(len(self.depth_dots[depth_dots_number])):
            if self.start < self.depth_dots[depth_dots_number][i]:
                if self.depth_dots[depth_dots_number][i] < self.end:
                    new_y.append(self.depth_dots[depth_dots_number][i])
                    new_x.append(dots[i])
                else:
                    return new_x, new_y
        return new_x, new_y

    def n_round(self, z):
        n = -2
        while z // (10 ** (-n)) == 0:
            n += 1
            if n > 6:
                return 10
        return n + 2


class Window:
    plt_colors = ['#ffbb78', '#ff9896', '#ff7f0e', '#f7b6d2', '#e377c2', '#dbdb8d', '#d62728', '#c7c7c7', '#c5b0d5',
                  '#c49c94', '#bcbd22', '#aec7e8', '#9edae5', '#98df8a', '#9467bd', '#8c564b', '#7f7f7f', '#2ca02c',
                  '#1f77b4', '#17becf']

    def __init__(self, root_widget, template=''):
        self.init_dir_and_file()

        self.template = template if os.path.isfile(template) else None
        # self.template = '/home/dev/PycharmProjects/petro_chart/Files/linux_test.json'
        self.i = 0
        self.time_event_mouse_scroll = 0
        self.root = root_widget
        self.head_frame = Frame(self.root)
        self.head_frame.pack(side=BOTTOM)

        self.main_scale_frame = LabelFrame(self.root, text='Масштаб')
        self.main_scale_frame.pack(side=LEFT)

        self.app = App(self.root)
        self.pad_choose = StringVar(self.root)

        self.draw_pad_choose_menu()
        self.draw_scale_pad()
        self.draw_pads()
        self.debug()

    def init_dir_and_file(self):
        self.files_dir = os.getcwd() + '/Files'
        if not os.path.isdir(self.files_dir):
            os.mkdir(self.files_dir)

    def debug(self):
        self.progress_bar_start()

        if self.template is None:
            self.template = 'Files/rezultaty_kalibrovki(shablon).json'
            self.load_template(self.template)

        self.progress_bar_stop()

        self.draw_pad_choose_menu()
        self.draw_pads()

    def add_las_file(self):
        self.progress_bar_start()

        filenames = filedialog.askopenfilename(title='Открыть файл', initialdir=self.files_dir,
                                               filetypes=[('las files', '.las')], multiple=True)

        for filename in filenames:
            self.app.add_curves_from_file(filename)
            self.draw_pad_choose_menu()

        self.progress_bar_stop()

    def get_template_file(self):
        self.progress_bar_start()
        filename = filedialog.askopenfilename(title='Открыть файл', initialdir=self.files_dir,
                                              filetypes=[('JSON files', '.json')])

        self.load_template(filename)

        self.progress_bar_stop()

        self.draw_pad_choose_menu()
        self.draw_pads()

    @staticmethod
    def is_file_json(filename):
        try:
            with open(filename) as f:
                json_object = json.load(f)
        except ValueError as e:
            return False
        except:
            return False
        return True

    def load_template(self, filename):
        if not Window.is_file_json(filename):
            return
        with open(filename) as f:
            template = json.load(f)
            for file in template['files']:
                self.app.add_curves_from_file(file)

            for pad in template['pads']:
                new_pad = self.app.add_pad()
                new_pad.log.set(pad.get('log'))
                new_pad.type.set(pad.get('type'))
                new_pad.border_scale_fixed.set(pad.get('border_scale_fixed'))
                new_pad.line_quantity.set(pad.get('line_quantity'))
                new_pad.width.set(pad.get('width'))
                for chart in pad['charts']:
                    new_chart = Chart(self.app.curves[chart['name']].get('dots'),
                                      name=chart.get('name'),
                                      color=chart.get('color'),
                                      type=chart.get('type'),
                                      min_border=chart.get('min_border'),
                                      max_border=chart.get('max_border'),
                                      borders=set(chart.get('borders')),
                                      borders_color=chart.get('borders_color'),
                                      fill_side=chart.get('fill_side'),
                                      unit=self.app.curves.get(chart.get('name')).get('unit'))

                    new_pad.add_chart(new_chart)
            self.template = filename

    def save_template(self):
        for i in range(len(self.app.filenames_url)):
            self.app.filenames_url[i] = 'Files/'+os.path.basename(self.app.filenames_url[i])

        filename = filedialog.asksaveasfilename(defaultextension='.json', initialfile=os.path.basename(self.template),
                                                initialdir=self.files_dir, title='Select file',
                                                filetypes=(('json files', '*.json'), ("All files", "*.")))

        if filename is None or filename == '':  # asksaveasfile return `None` if dialog closed with 'cancel'.
            return

        main_json = {'files': self.app.filenames_url, 'pads': []}

        for pad in self.app.pads:
            pad_info = {'log': pad.log.get(), 'type': pad.type.get(), 'border_scale_fixed': pad.border_scale_fixed.get(),
                        'line_quantity': pad.line_quantity.get(), 'charts': [], 'width': pad.width.get()}

            for chart in pad.charts:
                parameters = {'name': chart.parameters.get('name'), 'color': chart.parameters.get('color'),
                              'type': chart.get_type_line(), 'borders': list(chart.parameters.get('borders')),
                              'min_border': chart.get_min_border(),
                              'max_border': chart.get_max_border(),
                              'borders_color': chart.parameters.get('borders_color'),
                              'fill_side': chart.get_fill_side()}

                pad_info['charts'].append(parameters)

            main_json['pads'].append(pad_info)

        if os.path.isfile(filename):
            os.remove(filename)

        jsonFile = open(filename, mode='x')
        json.dump(main_json, jsonFile)
        jsonFile.close()

    def progress_bar_start(self):
        self.progress_bar.pack()

    def progress_bar_stop(self):
        self.progress_bar.pack_forget()

    def draw_pad_choose_menu(self):
        for children in self.head_frame.winfo_children():
            children.destroy()

        progress_bar_frame = Frame(self.head_frame)
        progress_bar_frame.pack(padx=10, side=LEFT)

        self.progress_bar = ttk.Progressbar(progress_bar_frame, orient='horizontal', mode='determinate')
        self.progress_bar.start()

        move_frame = Frame(self.head_frame)
        move_frame.pack(padx=10, side=LEFT)
        Button(move_frame, text='Сохранить шаблон', command=self.save_template).pack(side=RIGHT)
        Button(move_frame, text='Загрузить шаблон', command=self.get_template_file).pack(side=RIGHT)
        Button(move_frame, text='Добавить las файл', command=self.add_las_file).pack(side=RIGHT)

        if self.app.curves != {}:
            move_frame = Frame(self.head_frame)
            move_frame.pack(padx=10, side=RIGHT)
            Button(move_frame, text='->', command=self.pads_scroll_right).pack(side=RIGHT)
            Button(move_frame, text='<-', command=self.pads_scroll_left).pack(side=RIGHT)

            add_pad_frame = Frame(self.head_frame)
            add_pad_frame.pack(padx=10, side=RIGHT)
            self.pad_choose.set(list(self.app.curves.keys())[1])  # default value
            OptionMenu(add_pad_frame, self.pad_choose, *list(self.app.curves.keys())).pack(side=LEFT)
            Button(add_pad_frame, text='+', command=self.add_pad).pack(side=LEFT)

    def pads_scroll_right(self):
        self.app.set_first_show_pad(self.app.first_show_pad + 1)
        self.draw_pads()

    def pads_scroll_left(self):
        self.app.set_first_show_pad(self.app.first_show_pad - 1)
        self.draw_pads()

    def pad_move_left(self, pad_number):
        if pad_number not in range(1, len(self.app.pads)):
            return
        self.app.pads[pad_number - 1], self.app.pads[pad_number] = self.app.pads[pad_number], self.app.pads[
            pad_number - 1]
        self.draw_pads()

    def pad_move_right(self, pad_number):
        if pad_number not in range(0, len(self.app.pads) - 1):
            return
        self.app.pads[pad_number + 1], self.app.pads[pad_number] = self.app.pads[pad_number], self.app.pads[
            pad_number + 1]
        self.draw_pads()

    def draw_scale_pad(self):
        self.scale_cell_frame = Frame(self.main_scale_frame)  # , text='pad_menu_frame')
        self.scale_cell_frame.pack(side=TOP, fill='both')

        scale_menu_frame = Frame(self.main_scale_frame)  # , text='pad_menu_frame')
        scale_menu_frame.pack(side=BOTTOM, fill='both')

        button_reset_border = Button(scale_menu_frame, text='Сброс', command=self.reset_border)
        button_reset_border.pack(side=TOP, fill='both')

        scale_fig, self.scale_charts = plt.subplots(nrows=1, ncols=1, figsize=(1, 8))
        scale_fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
        self.scale_charts.spines['left'].set_position('center')
        self.scale_charts.xaxis.set_visible(False)
        self.scale_charts.set_ylim(self.app.end, self.app.start)

        self.canvas_scale = FigureCanvasTkAgg(scale_fig, self.main_scale_frame)
        self.canvas_scale.callbacks.connect('button_press_event', self.change_scale)
        self.canvas_scale.callbacks.connect('scroll_event', self.move_scale)

        self.canvas_scale.get_tk_widget().pack(side=BOTTOM)
        self.canvas_scale.draw()

    def move_scale(self, event):
        if abs(self.time_event_mouse_scroll - time.time()) > 1:
            self.time_event_mouse_scroll = time.time()
            if self.app.scale_move(event.button):
                self.draw_pads()

    def change_scale_pad(self):
        for child in self.scale_cell_frame.winfo_children():
            child.destroy()

        Cell(self.scale_cell_frame, False, 'MD', 'black', '', 'meters', '')
        for i in range(self.app.max_pads_cells() - 1):
            Cell(self.scale_cell_frame, False, '', 'grey', '', '', '')

        self.canvas_scale.get_tk_widget().pack_forget()
        self.canvas_scale.get_tk_widget().pack(side=BOTTOM)
        self.scale_charts.set_ylim(self.app.end, self.app.start)
        self.canvas_scale.draw()

    def reset_border(self):
        self.app.set_new_border(0, 99999)
        self.draw_pads()

    def change_scale(self, event):
        if event.button == 1:
            self.app.zoom_scale(event.ydata)
        if event.button == 3:
            self.app.reduce_scale()
        self.draw_pads()

    def add_pad(self):
        self.app.add_pad()
        self.app.add_chart(len(self.app.pads) - 1, self.pad_choose.get())

        self.draw_pads()

    def delete_pad(self, pad_number):
        self.app.delete_pad(pad_number)
        self.draw_pads()

    def draw_pads(self):
        for frame in self.app.pad_frames:
            frame.pad_frame.pack_forget()


        for pad_number in range(self.app.first_show_pad, len(self.app.pads)):
            pad_frame = self.app.get_or_create_pad_frame(pad_number)

            if len(pad_frame.pad_menu_frame.winfo_children()) == 0:
                self.create_pad_menu(pad_frame.pad_menu_frame, pad_number)

            pad_frame.reset()

            if self.app.pads[pad_number].type.get() == 'line':
                self.draw_chart_in_pad(pad_number, pad_frame)

            if self.app.pads[pad_number].type.get() == 'row':
                self.draw_row_in_pad(pad_number, pad_frame)

            # перерисовка плота(графика) при добавлении новых линий
            self.app.pad_frames[pad_number].update_chart()

        self.change_scale_pad()

    def draw_chart_in_pad(self, pad_number, pad_frame):
        if self.app.pads[pad_number].log.get():
            pad_frame.chart.set_xscale('log')

        main_min = 10**10
        main_max = -main_min

        for chart in self.app.pads[pad_number].charts:
            x, y = self.app.dots_range(chart.get_dots_with_border())

            main_min = np.nanmin(x + [main_min])
            main_max = np.nanmax(x + [main_max])

            if self.app.pads[pad_number].border_scale_fixed.get():
                new_min = chart.get_min_border()
                main_min = main_min if math.isinf(new_min) or math.isnan(new_min) else new_min

                new_max = chart.get_max_border()
                main_max = main_max if math.isinf(new_max) or math.isnan(new_min) else new_max

            chart_line = pad_frame.chart.plot(x, y, color=chart.parameters['color'])

            new_x = np.ma.masked_where(x > np.float64(chart.get_min_border()), x)
            pad_frame.chart.plot(new_x, y, linestyle=':',
                                 linewidth=2,
                                 color='white', clip_on=True)


            new_x = np.ma.masked_where(x < np.float64(chart.get_max_border()), x)
            pad_frame.chart.plot(new_x, y, linestyle=':',
                                 linewidth=2,
                                 color='white', clip_on=True)

            if chart.get_type_line() == 'fill':
                xx, yy = self.split_mass_nan(x, y)
                for i in range(len(xx)):
                    side_fill = main_min if chart.get_fill_side() == 'left' else main_max
                    xx[i].append(side_fill)
                    yy[i].append(yy[i][-1])

                    pad_frame.chart.fill_between(xx[i], yy[i], y2=min(yy[i]), color=chart_line[0].get_color(),
                                                 alpha=0.5)

            medium = abs(main_min - main_max)
            n_round = self.app.n_round(medium)

            new_cell_frame = Cell(pad_frame.cell_frame, False,
                                  chart.parameters.get('name'),
                                  chart_line[0].get_color(),
                                  str(round(main_min, n_round)),
                                  chart.parameters.get('unit'),
                                  str(round(main_max, n_round)))

            chart.parameters['color'] = chart_line[0].get_color()

            pad_frame.cell.append(new_cell_frame)

            pad_frame.chart.set_ylim(self.app.end, self.app.start)

        chart_border = abs(main_min - main_max) * 0.02

        if main_min == main_max:
            pad_frame.chart.set_xlim(main_min - 1, main_max + 1)
        else:
            pad_frame.chart.set_xlim(main_min - chart_border, main_max + chart_border)

        pad_frame.add_empty_cell(self.app.max_pads_cells() - len(self.app.pads[pad_number].charts))
        pad_frame.pad_frame.pack(side=LEFT)

        line_quantity = int(self.app.pads[pad_number].line_quantity.get())
        medium = abs(pad_frame.chart.get_xlim()[0] - pad_frame.chart.get_xlim()[1])
        step = medium / (line_quantity + 1)

        for x in range(1, line_quantity + 1):
            x1 = pad_frame.chart.get_xlim()[0] + step * x
            pad_frame.chart.plot(
                [x1, x1],
                [self.app.end, self.app.start],
                color='black',
                linewidth=0.5)

    def draw_row_in_pad(self, pad_number, pad_frame):
        if len(self.app.pads[pad_number].charts) == 0:
            return

        chart = self.app.pads[pad_number].charts[0]
        x, y = self.app.dots_range(chart.get_dots_with_border())
        main_min, main_max = np.nanmin(x + [10**10]), np.nanmax(x + [-(10**10)])

        borders = chart.parameters['borders'].copy()
        if len(chart.parameters['borders_color']) + 1 < len(borders):
            borders_color = []
            for i in borders:
                borders_color.append(self.plt_colors[random.randrange(len(self.plt_colors))])
            chart.parameters['borders_color'] = borders_color

        fig = pad_frame.fig
        ax = pad_frame.chart

        a = graph_modules.StolbGraph(2, x, y, chart.parameters['borders_color'],
                                     borders, fig=fig, ax=ax)

        a.draw()

        medium = abs(main_min - main_max)
        n_round = self.app.n_round(medium)
        new_cell_frame = Cell(pad_frame.cell_frame, False,
                              chart.parameters.get('name'),
                              'blue',
                              str(round(main_min, n_round)),
                              chart.parameters.get('unit'),
                              str(round(main_max, n_round)))
        
        chart.parameters['color'] = 'blue'
        pad_frame.cell.append(new_cell_frame)
        pad_frame.pad_frame.pack(side=LEFT)

        pad_frame.chart.set_ylim(self.app.end, self.app.start)

        pad_frame.chart.set_xlim(0, 1)

        pad_frame.add_empty_cell(self.app.max_pads_cells() - 1)

    def create_pad_menu(self, frame, pad_number):
        # frame.grid_columnconfigure(1, weight=3)

        btn1 = Button(frame, text='Изменить!', command=lambda pn=pad_number: self.show_pad_edit_window(pn))
        btn2 = Button(frame, text='X', command=lambda pn=pad_number: self.delete_pad(pn))

        nav_frame = Frame(frame)
        Button(nav_frame, text='◀', command=lambda pn=pad_number: self.pad_move_left(pn)).pack(side=LEFT)
        Button(nav_frame, text='▶', command=lambda pn=pad_number: self.pad_move_right(pn)).pack(side=LEFT)

        btn1.grid(row=0, column=0)
        nav_frame.grid(row=0, column=1)
        btn2.grid(row=0, column=2)

    def delete_pad(self, pad_number):
        self.app.delete_pad(pad_number)
        self.draw_pads()

    def pre_destroy(self, widget):
        widget.destroy()
        self.draw_pads()

    def add_chart_to_pad(self, pad_number):
        self.app.add_chart(pad_number, self.pad_choose.get())
        self.update_pad_edit_window(pad_number)

    def pop_chart_from_pad(self, pad_number, chart):
        self.app.pads[pad_number].charts.remove(chart)
        self.update_pad_edit_window(pad_number)

    def pop_border_from_pad(self, pad_number, value):
        self.app.pads[pad_number].charts[0].parameters['borders'].remove(value)
        self.show_pad_settings_window(pad_number)
        self.update_pad_edit_window(pad_number)

    def add_pad_border(self, pad_number, value):
        try:
            border_value = float(value.get().replace(',', '.'))
        except ValueError:
            self.app.open_error_window(value.get() + ' - не является числом!')
            return

        if len(self.app.pads[pad_number].charts) == 0:
            self.app.open_error_window('Не указана линия!')
            return

        self.app.pads[pad_number].charts[0].parameters['borders'].add(border_value)
        self.app.pads[pad_number].charts[0].parameters['borders'] = \
            set(sorted(self.app.pads[pad_number].charts[0].parameters['borders']))

        self.show_pad_settings_window(pad_number)
        self.update_pad_edit_window(pad_number)

    def show_pad_edit_window(self, pad_number):
        if hasattr(self, 'pad_edit_window'):
            self.pad_edit_window.destroy()

        self.pad_edit_window = Toplevel(self.root)
        self.pad_edit_window.title('Настройки планшета: ' + str(pad_number + 1))
        # self.pad_edit_window.wm_geometry('400x400')
        self.pad_edit_window.protocol('WM_DELETE_WINDOW', lambda pew=self.pad_edit_window: self.pre_destroy(pew))

        self.update_pad_edit_window(pad_number)

    def show_choose_color_window(self, chart, pad_number):
        if hasattr(self, 'pad_edit_windowchoose_color_window'):
            self.choose_color_window.destroy()

        self.choose_color_window = Toplevel(self.root)
        self.choose_color_window.title('Выбор Цвета')
        for color in self.plt_colors:
            Button(self.choose_color_window, bg=color,
                   command=lambda с=color, ch=chart, pn=pad_number: self.set_new_color_chart(с, ch, pn)).pack(side=LEFT)
        self.choose_color_window.protocol('WM_DELETE_WINDOW',
                                          lambda ccw=self.choose_color_window: self.pre_destroy(ccw))

    def set_new_color_chart(self, color, chart, pad_number):
        chart.parameters['color'] = color
        self.update_pad_edit_window(pad_number)

    def update_pad_edit_window(self, pad_number):
        for widget in self.pad_edit_window.winfo_children():
            widget.destroy()

        chart_edit = Frame(self.pad_edit_window)
        chart_edit.pack(side=TOP, padx=5, pady=10)

        chart_add = Frame(chart_edit)
        chart_add.pack(side=TOP, fill='both')

        OptionMenu(chart_add, self.pad_choose, *list(self.app.curves.keys())).pack(side=LEFT, padx=1)
        Button(chart_add, text='+', command=lambda pn=pad_number: self.add_chart_to_pad(pn)).pack(side=LEFT)
        Button(chart_add, text='⚙', command=lambda pn=pad_number: self.show_pad_settings_window(pn)).pack(side=RIGHT)

        for chart in self.app.pads[pad_number].charts:
            chart_delete = Frame(chart_edit)
            chart_delete.pack(side=TOP, fill='both')

            Button(chart_delete, bg=chart.parameters.get('color'),
                   command=lambda ch=chart, pn=pad_number: self.show_choose_color_window(ch, pn)).pack(side=LEFT,
                                                                                                       padx=3)
            Button(chart_delete, text='⚙',
                   command=lambda pn=pad_number, ch=chart: self.show_edit_chart_window(pn, ch)).pack(side=LEFT)
            Label(chart_delete, text=chart.parameters.get('name')).pack(side=LEFT)

            Button(chart_delete, text='X', command=lambda pn=pad_number, ch=chart: self.pop_chart_from_pad(pn, ch)) \
                .pack(side=RIGHT)

        Button(chart_edit, text='Применить', command=self.draw_pads).pack(side=BOTTOM)

    def show_edit_chart_window(self, pad_number, chart):
        if hasattr(self, 'edit_chart_window'):
            self.edit_chart_window.destroy()

        self.edit_chart_window = Toplevel(self.root)
        self.edit_chart_window.title('Настройки кривой планшета: ' + str(int(pad_number + 1)))
        self.edit_chart_window.wm_geometry('400x400+100+100')
        self.edit_chart_window.protocol('WM_DELETE_WINDOW', lambda ecw=self.edit_chart_window: self.pre_destroy(ecw))

        frame_1 = Frame(self.edit_chart_window)
        frame_1.pack(fill='both')

        Label(frame_1, text='Тип линии:').pack(side=LEFT)
        OptionMenu(frame_1, chart.type_line, *list(['line', 'fill'])).pack(side=RIGHT)

        frame_2 = Frame(self.edit_chart_window)
        frame_2.pack(fill='both')

        Label(frame_2, text='Сторона заливки:').pack(side=LEFT)
        OptionMenu(frame_2, chart.fill_side, *list(['left', 'right'])).pack(side=RIGHT)

        frame_3 = Frame(self.edit_chart_window)
        frame_3.pack(fill='both')

        Label(frame_3, text='Нижняя граница').pack(side=LEFT)
        Entry(frame_3, textvariable=chart.min_border).pack(side=RIGHT)

        frame_4 = Frame(self.edit_chart_window)
        frame_4.pack(fill='both')

        Label(frame_4, text='Верхняя граница').pack(side=LEFT)
        Entry(frame_4, textvariable=chart.max_border).pack(side=RIGHT)

        Button(self.edit_chart_window, text='Готово',
               command=lambda ecw=self.edit_chart_window: self.pre_destroy(ecw)).pack(side=BOTTOM)

        self.update_pad_edit_window(pad_number)

    def show_pad_settings_window(self,  pad_number: int):
        if hasattr(self, 'pad_settings_window'):
            self.pad_settings_window.destroy()

        self.pad_settings_window = Toplevel(self.root)
        self.pad_settings_window.title('Настройки отрисовки планшета:{current_pad_number}'.format(current_pad_number=int(pad_number) + 1))
        self.pad_settings_window.wm_geometry('400x400+100+100')
        self.pad_settings_window.protocol('WM_DELETE_WINDOW',
                                          lambda psw=self.pad_settings_window: self.pre_destroy(psw))

        chart_styles = Frame(self.pad_settings_window)
        chart_styles.pack(side=TOP)

        pad_log = Frame(chart_styles)
        pad_log.pack(side=TOP)

        Label(pad_log, text='Логарифмическая шкала').pack(side=LEFT)
        Checkbutton(pad_log, variable=self.app.pads[pad_number].log).pack(side=LEFT)

        pad_border = Frame(chart_styles)
        pad_border.pack(side=TOP)

        Label(pad_border, text='Фиксированные границы').pack(side=LEFT)
        Checkbutton(pad_border, variable=self.app.pads[pad_number].border_scale_fixed).pack(side=LEFT)

        pad_grid = Frame(chart_styles)
        pad_grid.pack(side=TOP)

        Label(pad_grid, text='Количество линий').pack(side=LEFT)
        OptionMenu(pad_grid, self.app.pads[pad_number].line_quantity, *list(range(11))).pack(side=LEFT)

        pad_width = Frame(chart_styles)
        pad_width.pack(side=TOP)

        Label(pad_width, text='Ширина планшета').pack(side=LEFT)
        OptionMenu(pad_width, self.app.pad_frames[pad_number].width, *list(range(1, 20))).pack(side=LEFT)

        pad_type = Frame(chart_styles)
        pad_type.pack(side=TOP)

        if self.app.pads[pad_number].type._tclCommands is None:
            self.app.pads[pad_number].type.trace('w', lambda *args, pn=pad_number: self.edit_window_on_change(pn, args))

        Label(pad_type, text='Тип кривой').pack(side=LEFT)
        OptionMenu(pad_type, self.app.pads[pad_number].type, *list(['line', 'row'])).pack(side=LEFT)

        if len(self.app.pads[pad_number].charts) == 0:
            return

        if self.app.pads[pad_number].type.get() == 'row':
            pad_border = LabelFrame(chart_styles, text='Добавление границ')
            pad_border.pack(side=TOP)
            border_value = StringVar(value=0)

            add_pad_border = Frame(pad_border)
            add_pad_border.pack(side=TOP)

            Entry(add_pad_border, textvariable=border_value).pack(side=LEFT)
            Button(add_pad_border, text='+', command=lambda pn=pad_number, bv=border_value: self.add_pad_border(pn, bv))\
                .pack(side=RIGHT)

            borders = set(self.app.pads[pad_number].charts[0].parameters['borders'].copy())
            borders.discard(-math.inf)
            borders.discard(math.inf)
            for border in borders:
                pad_border_delete = Frame(pad_border)
                pad_border_delete.pack(side=BOTTOM, fill='both')

                Label(pad_border_delete, text=border).pack(side=LEFT)
                Button(pad_border_delete, text='X',
                       command=lambda pn=pad_number, b=border: self.pop_border_from_pad(pn, b)).pack(side=RIGHT)
        self.update_pad_edit_window(pad_number)

    def edit_window_on_change(self, p_n, *args):
        self.show_pad_settings_window(p_n)
        self.update_pad_edit_window(p_n)

    def split_mass_nan(self, x, y):
        z = True
        xx = []
        yy = []

        for s in range(min(len(x), len(y))):
            if np.isnan(x[s]):
                z = True
            else:
                if z is True:
                    z = False
                    xx.append([])
                    yy.append([])
                xx[-1].append(x[s])
                yy[-1].append(y[s])

        return xx, yy


if __name__ == '__main__':
    root = Tk()
    root.geometry('1920x800+1920+0')
    # root.geometry('1920x800+-10+0')
    window = Window(root)
    window.root.mainloop()
