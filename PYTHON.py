
from tkinter import *
from tkinter.ttk import *
import os.path
from ThreadTest import *
from difflib import Differ
from time import sleep
import json
import os
import csv
import smtplib
from email.mime.text import MIMEText
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

########### DEFAULTS
switches = ["SW0", "SW1", "SW2", "SW3", "SW4", "SW5", "SW6", "SW7"]
routers = ["ISP", "Border", "R2", "R1", "R3"]
pcs = ["PC1", "PC2", "PC3", "PC4", "NetworkAutomation", "Toolbox-1", "DNS-1"]
header = ['name', 'ipv4 interface(s)', 'ipv6 interfaces', 'vlan(SWITCH)', 'arp']

commands = {
    'reload': "reload",
    'get_config': "show running-config",
    'configure': "conf t",
    'interface': "interface"
}

sPath = "to_set.txt"
gPath = "hostname.txt"
csvF = "stats.csv"
sender = 'sender@example.com'
receiver = 'receiver@example.com'
valide = []


#################### glob check


########################### CLASSES


def show_diff(dpath1, dpath2):
    to_return = []
    with open(dpath1, 'r') as file_1, open(dpath2, 'r') as file_2:
        differ = Differ()
        for line in differ.compare(file_1.readlines(), file_2.readlines()):
            to_return.append(line)
    return to_return


def is_diff(dpath1, dpath2):
    d = 0
    with open(dpath1, 'r') as file_1, open(dpath2, 'r') as file_2:
        differ = Differ()
        for line in differ.compare(file_1.readlines(), file_2.readlines()):
            d += 1
        if d > 0:
            return True
        return False


class Device:
    def __init__(self, dct, name, cf_path):
        self.name = name
        self.device_type = dct['device_type']
        self.host = dct['host']
        self.username = dct['username']
        self.password = dct['password']
        self.secret = dct['secret']
        self.cf_path = cf_path

    def get_dct(self):
        return {'device_type': self.device_type, 'host': self.host, 'username': self.username,
                'password': self.password, 'secret': self.secret}

    def get_name(self):
        return self.name

    def get_cfpath(self):
        return self.cf_path


devices = [Device( {'device_type' : " ",
                        'host' : " ",
                        'username' : " ",
                        'password' : " ",
                        'secret' : " "}, " " , " ")]
devices.pop(0)


class connection_handler(Device):
    def __init__(self, dct, name, cf_path):
        super().__init__(dct, name, cf_path)
        self.connection = ""

    def connect(self):
        try:
            self.connection = ConnectHandler(**super().get_dct())
            print(self.connection.find_prompt())
            self.output = self.connection.find_prompt()
        except Exception as e:
            print(e)
            self.output = "ERROR : COULD NOT ESTABLISH CONNECTION"

    def reload(self):
        try:
            self.connection.enable()
            self.connection.send_command(commands['reload'])
        except Exception as e:
            print(e)

    def get_config(self, hosts):
        try:
            self.connection.enable()
            output = self.connection.send_command(commands['get_config'])
            with open(hosts, "w+") as f:
                f.write(self.name)
                f.write("____________________")
                f.write(output)
            f.close()
        except Exception as e:
            print(e)

    def set_config(self, cf_path):
        try:
            self.connection.enable()
            self.connection.send_config_from_file(cf_path)
            self.connection.save_config()
        except Exception as e:
            print(e)

    def send_command(self, comm):
        try:
            self.connection.enable()
            self.connection.send_command(comm)
        except Exception as e:
            print(e)

    def export_CSV(self, pCsv):
        try:
            self.connection.enable()
            with open(pCsv, 'a', encoding='UTF8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                if self.name in switches:
                    output1 = self.connection.send_command("show ip interface brief")
                    print(output1)

                    output2 = self.connection.send_command("show ipv6 interface brief")

                    output3 = self.connection.send_command("show vlan")

                    output4 = self.connection.send_command("show arp")

                    writer.writerow([output1, output2, output3, output4])

                if self.name in routers:
                    output1 = self.connection.send_command("show ip interface brief")
                    print(output1)

                    output2 = self.connection.send_command("show ipv6 interface brief")

                    output3 = self.connection.send_command("show ip arp")

                    writer.writerow([output1, output2, output3])

                if self.name in pcs:
                    output = self.connection.send_command("show ip")
                    print(output)
                    writer.writerow(output)

            f.close()

        except Exception as e:
            print(e)

    def enable_email_alert(self, send, rece, usr, passwd, time):

        try:
            self.connection.enable()
            sleep(time)
            cond = False

            while not cond and time != 0:
                self.get_config("test1.txt")
                sleep(time / 2)
                time -= time / 2
                self.get_config("test2.txt")
                if is_diff("test1.txt", "test2.txt"):
                    cond = True

            msg = MIMEText('There have been config changes')

            msg['Subject'] = 'CONFIG CHANGES'
            msg['From'] = send
            msg['To'] = rece

            user = usr
            password = passwd

            with smtplib.SMTP("smtp.mailtrap.io", 2525) as mail_server:
                mail_server.login(user, password)
                mail_server.sendmail(send, rece, msg.as_string())
                print("mail successfully sent")

            if os.path.exists("test1.txt"):
                os.remove("test1.txt")
            if os.path.exists("test2.txt"):
                os.remove("test2.txt")


        except Exception as e:
            print(e)


connected_devices = [connection_handler(
    {'device_type': ' ', 'host': ' ', 'username': ' ', 'password': ' ', 'secret': ' '}, " ", " ")]
#############################


nr_of_submits = 0


def randomColor():
    randomRed = ("00" + hex(random.randint(0, 255))[2:])[-2]
    randomGreen = ("00" + hex(random.randint(0, 255))[2:])[-2]
    randomBlue = ("00" + hex(random.randint(0, 255))[2:])[-2]
    # red 153
    # green 238
    # blue 204
    # return "#{}{}{}".format(randomRed, randomGreen, randomBlue)
    return '#9FE2BF'


def open_popup(str):
    top = Toplevel(root)
    top.geometry("250x125")
    top.title("Error2")
    Label(top, text=str, font=('Helvetica 12 bold')).place(x=50, y=35)


class RandomColorNestedFramesApp:

    def __init__(self, master):
        self.cur = connection_handler(
            {'device_type': ' ', 'host': ' ', 'username': ' ', 'password': ' ', 'secret': ' '}, " ", " ")
        self.DEVICE = " "
        self.master = master
        self.master.geometry("1000x600")
        self.master.title('NETWORK CONFIGURATOR')
        self.MeniuFrame = Frame(self.master, width=1200, height=60, relief=SUNKEN, )

        self.MeniuFrame.pack(in_=self.master, side=TOP)

        self.DEVICElabel = Label(self.master, font=('aria', 16, 'bold'), text="Enter Device Name",
                                 foreground="steel blue",
                                 anchor='ce')

        self.DEVICElabel.pack(side=TOP, pady=1, padx=100)

        self.DEVICEtext = StringVar()
        self.DEVICEtexter = Entry(self.master, font=('courier', 15, 'bold'),
                                  textvar=self.DEVICEtext)  # .grid(row = 0 ,column = 1, padx = 100)

        self.DEVICEtexter.pack(side=TOP, pady=1, padx=100, after=self.DEVICElabel)

        # BUTTONS

        self.f1 = Frame(self.master, width=600, height=300, relief=SUNKEN, borderwidth=1, style='Frame1.TFrame')
        self.f1.pack(side=TOP, pady=20, after=self.DEVICEtexter)

        self.canvas = Canvas(self.f1, width=1000, height=750, bg="SpringGreen2")

        self.SenderFrame = Frame(self.master, width=1200, height=200)
        self.SenderFrame.pack(after=self.f1)

        self.btn2 = Button(self.SenderFrame, text=' Connect ',
                           command=lambda: self.DEVconn())  # lambda: self.start_submit_thread()
        self.btn2.grid(row=1, column=1, padx=20)

        self.btn3 = Button(self.SenderFrame, text=' Verify Ping ',
                           command=lambda: self.GVPing())  # lambda: self.start_submit_thread()
        self.btn3.grid(row=1, column=2, padx=20)

        self.btn4 = Button(self.SenderFrame, text=' Clear Pane ',
                           command=lambda: self.do_nothing())  # lambda: self.start_submit_thread()
        self.btn4.grid(row=1, column=3, padx=20)

        self.btn5 = Button(self.SenderFrame, text=' Compare ',
                           command=lambda: self.DevComp())  # lambda: self.start_submit_thread()
        self.btn5.grid(row=2, column=1, padx=20, pady=10)

        self.DEVICEtext2 = StringVar()
        self.DEVICEtexter2 = Entry(self.SenderFrame, font=('courier', 15, 'bold'),
                                   textvar=self.DEVICEtext2, width=20)  # .grid(row = 0 ,column = 1, padx = 100)
        self.DEVICEtexter2.grid(row=2, column=2)

        # P BARS

        self.ProgFrame = Frame(self.f1, style='Frame1.TFrame', width=100, height=60, relief=SUNKEN)
        self.ProgFrame.place(relx=0.35, rely=0.5, relwidth=0.3, relheight=0.05)

        self.progressbar = Progressbar(self.ProgFrame, mode='indeterminate')
        self.progressbar.place(relx=0, rely=0, relwidth=1)

        self.blank = Frame(self.ProgFrame, width=100, height=60, style='Frame1.TFrame')
        self.blank.place(relx=0, rely=0, relwidth=1)

        self.progressbar.pack_forget()

        self.progressbar.winfo_x()
        self.progressbar2 = Progressbar(self.master, mode='indeterminate')

        self.progressbar2.place(x=self.progressbar.winfo_x(), y=self.progressbar.winfo_y(),
                                width=self.progressbar.winfo_width(), height=self.progressbar.winfo_height())

        self.progressbar2.pack_forget()

        self.addFrameButton = Button(self.MeniuFrame, text=" ≡ ", style="meniu.TButton",
                                     command=lambda: self.addDaughterFrame(relx=0.5, rely=0.5, relwidth=0.5,
                                                                           relheight=0.5))
        self.addFrameButton.place(relx=0, rely=0, relwidth=0.10, relheight=1)

        self.frameList = []

    def addDaughterFrame(self, relx, rely, relwidth, relheight):
        Mframe = MeniuFrame(self, relx, rely, relwidth, relheight)

    def Wrapper(self):
        # Get Url list
        ###
        pass

    def submit(self):
        if nr_of_submits > 1:
            self.progressbar2.tkraise()
            self.progressbar2.start()
        else:
            self.progressbar.tkraise()
            self.progressbar.start()
        return self.Wrapper()

    def check_submit_thread(event):
        if submit_thread.is_alive():
            root.after(20, event.check_submit_thread)
        else:
            pass

    def start_submit_thread(event):

        global nr_of_submits
        nr_of_submits += 1
        ## THREAD STUFF
        global submit_thread
        submit_thread = threading.Thread(target=event.submit)
        submit_thread.daemon = True
        submit_thread.start()
        root.after(20, event.check_submit_thread)

    def do_nothing(self):
        self.start_submit_thread()

    def DEVconn(self):
        self.DEVICE = self.DEVICEtexter.get()

        if len(valide) != 0:
            if self.DEVICE in valide:
                for dev in devices:
                    if dev.get_name() == self.DEVICE:
                        c = connection_handler(dev.get_dct(),
                                               dev.get_name(),
                                               dev.get_cfpath())

                        self.paint(c.output)
                        self.cur = c

            else:
                open_popup("Dispozitiv invalid")
        else:
            open_popup("Nu exista disp. valide")

    def paint(self, output):
        self.canvas.create_text(300, 50, text=str(output), fill="black", font=('Helvetica 15 bold'))
        self.canvas.pack()

    def GVPing(self):
        pass

    def DevComp(self):
        d1 = self.cur
        dev2 = self.DEVICEtexter2.get()
        d2 = ""
        for dev in devices:
            if dev.get_name() == dev2:
                d2 = connection_handler(dev.get_dct(),
                                        dev.get_name(),
                                        dev.get_cfpath())
        try:
            self.paint(show_diff(d1.cf_path, d2.cf_path))
        except Exception as e:
            open_popup("second device is invalid")


############################################################LEFT MENIU
class MeniuFrame:

    def __init__(self, master, relx, rely, relwidth, relheight):
        self.master = master.master

        self.bgFrame = Frame(self.master, style="Frame1.TFrame", relief=SUNKEN)
        self.bgFrame.place(relx=0, rely=0, relwidth=0.45, relheight=0.84)

        self.addFrameButton = Button(self.bgFrame, style="exitMeniu.TButton", text="exit",
                                     command=self.exitMeniuFrame)
        self.addFrameButton.place(rely=1 - (0.10), relwidth=0.2, relx=(0.5 - (0.2 / 2)), relheight=0.10)

        ### CONTENTS

        self.btn2 = Button(self.bgFrame, text=' Import IP File ',
                           command=lambda: self.IMPORT())  # lambda: self.start_submit_thread()
        self.btn2.pack(side=TOP, pady=20)

        self.btn3 = Button(self.bgFrame, text=' Export Global Config',
                           command=lambda: self.GEXPORT())  # lambda: self.start_submit_thread()
        self.btn3.pack(after=self.btn2, pady=20)

        self.btn31 = Button(self.bgFrame, text=' Apply Global Config',
                            command=lambda: self.GAPPLY())  # lambda: self.start_submit_thread()
        self.btn31.pack(after=self.btn3, pady=20)

        self.btn4 = Button(self.bgFrame, text='Export CSV',
                           command=lambda: self.GCSV())  # lambda: self.start_submit_thread()
        self.btn4.pack(after=self.btn31, pady=20)

        self.btn5 = Button(self.bgFrame, text=' Enable Email',
                           command=lambda: self.GEMAIL())  # lambda: self.start_submit_thread()
        self.btn5.pack(after=self.btn4, pady=20)

    def onValidate(self, value_if_allowed):
        try:
            if (str.isdigit(value_if_allowed) or value_if_allowed == '') and value_if_allowed != '0':
                return True
            else:
                return False
        except ValueError:
            return False

    def exitMeniuFrame(self):

        self.addFrameButton.place_forget()
        self.addFrameButton.destroy()
        self.bgFrame.place_forget()
        self.bgFrame.destroy()

    def do_nothing(self):
        pass

    def Wrapper(self):
        pass

    def IMPORT(self):

        for device in switches + routers + pcs:
            with open(device + "_conf.txt", 'w') as conf:
                conf.seek(0)
        conf.close()

        with open('data.json') as json_file:
            try:
                data = json.load(json_file)

            except Exception as e:
                print(e)

            print("Fisierul a putut fi deschis !")

            for device in data:
                for line in data[device]:
                    devices.append(Device(data[device], device, device + "_conf.txt"))
                    devices.append(device)

            for device in devices:
                connected_devices.append(connection_handler(device.get_dct(),
                                                            device.get_name(),
                                                            device.get_cfpath()))

            for con in connected_devices:
                con.connect()
                valide.append(con.get_name())

    def GEXPORT(self):

        for device in devices:
            connected_devices.append(connection_handler(device.get_dct(),
                                                        device.get_name(),
                                                        device.get_cfpath()))

        for con in connected_devices:
            con.connect()
            con.get_config(gPath)

    def GAPPLY(self):

        for device in devices:
            connected_devices.append(connection_handler(device.get_dct(),
                                                        device.get_name(),
                                                        device.get_cfpath()))

        for con in connected_devices:
            con.connect()
            con.set_config(sPath)

    def GCSV(self):
        for device in devices:
            connected_devices.append(connection_handler(device.get_dct(),
                                                        device.get_name(),
                                                        device.get_cfpath()))

        for con in connected_devices:
            con.connect()
            con.export_CSV(csvF)

    def GEMAIL(self):

        for device in devices:
            connected_devices.append(connection_handler(device.get_dct(),
                                                        device.get_name(),
                                                        device.get_cfpath()))

        for con in connected_devices:
            con.connect()
            con.export_CSV(csvF)


if __name__ == "__main__":
    root = Tk()
    style = Style()
    styleFrame = Style()
    styleTextBox = Style()
    styleTextWidget = Style()

    style.configure('TButton', font=
    ('calibri', 20, 'bold'),
                    borderwidth='4')
    styleFrame.configure(
        'Frame1.TFrame',
        background=randomColor(),
    )

    styleTextBox.configure('TEntry', foreground="green")
    styleTextWidget.configure('TText', foreground="green")

    # Changes will be reflected
    # by the movement of mouse.
    style.map('TButton', foreground=[('active', '!disabled', 'green')],
              background=[('active', 'black')])

    styleMeniuButton = Style()
    styleMeniuButton.configure('meniu.TButton', font=('Helvetica', 25))

    styleExitMeniuButton = Style()
    styleExitMeniuButton.configure('exitMeniu.Tbutton', font=('Helvetica', 12))
    style.map('meniu.TButton', foreground=[('active', '!disabled', 'green')],
              background=[('active', 'black')])

    theApp = RandomColorNestedFramesApp(root)
    root.mainloop()
