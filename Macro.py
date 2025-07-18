import os
import io
import threading
import time
import queue

from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse
from pynput.keyboard import Key
from pynput.mouse import Button
from pynput.mouse import Controller as mouse_controller
from pynput.keyboard import Controller as keyboard_controller

from PyQt6.QtCore import QTimer



class Keys:
    """Stores: \n
        - The keyname
        - The time when the key was pressed
        - The time when the key was released
       for every key"""
       #0       1           2                  3
    #keyboard, name, time_when_pressed, time_when_released
    def __init__(self, name, time_when_pressed=0):
        self.name = name
        self.time_when_pressed = time_when_pressed
        self.time_when_released = 0

    def set_released_time(self, time_when_released=0):
        """ Sets the time when the key was released"""
        self.time_when_released = time_when_released

    def key_to_string(self) -> str:
        """Returns the key name to a string"""
        if str(self.name) != "'.'":
            name = str(self.name).split(".")
            return name[len(name) - 1]
        else:
            return str(self.name)

    def key_file_format(self) -> str:
        return "keyboard:" + str(self.name) + ":" + str(self.time_when_pressed) + ":" + str(self.time_when_released) + "\n"

class Mouse:
    # 0     1           2             3    4        5               6    7
    #mouse,button,time_when_pressed,in_x,in_y,time_when_released,fin_x,fin_y
    def __init__(self,button,time_when_pressed=0,x=0,y=0):
        self.button             = button
        self.time_when_pressed  = time_when_pressed
        self.init_x             = x
        self.init_y             = y
        self.time_when_released = 0
        self.fin_x              = 0
        self.fin_y              = 0

    def released(self,time_when_released=0,fin_x=0,fin_y=0):
        self.time_when_released = time_when_released
        self.fin_x              = fin_x
        self.fin_y              = fin_y

    def mouse_file_format(self) -> str:
        return "mouse_click:" + str(self.button) + ":" + str(self.time_when_pressed) + ":" + str(self.init_x) + ":" + str(self.init_y) + ":" + str(self.time_when_released) + ":" + str(self.fin_x) + ":" + str(self.fin_y) + "\n"


class Record:
    """ Records every key and mouse event. \n
        Arranges the events by the time that they were pressed and then upload them to the file """

    def __init__(self, txtFile,stop_key = "",pause_resume_key = ""):
        """
        Initializes the Record class and it's key components
        """
        self.stop_key = stop_key                    #
        self.pause_resume_key = pause_resume_key    #   The keys that should be ignored (already did that in the Ui.py file but I'm to lazy to delete everything,this program took to long to finish)
        self.keyList = []         # Stores every Keys object
        self.mouse_list = []      # Stores every Mouse object
        self.mouse_buffer = []    # Stores all the movements of the mouse while it is being pressed
        self.txtFile = ""         # The file wich contains all the Macros
        self.number_of_folder = 0 # The number of the current "non-named" folder

        if txtFile == "":                                #Creating the folder with the given name in the Label
            print(True)
            fileNames = os.listdir("Macros")    #   fileNames is a list that will contain all the names of the files that are in the Macros folder
            for fileName in fileNames:
                if "Macro" in fileName:
                    self.number_of_folder += 1
            self.txtFile = f"Macros/Macro{self.number_of_folder + 1}.txt"
            open(self.txtFile, "a").close()                 #this is used to create the file and leaving it empty for future writing
        else:
            print(False)
            fileNames = os.listdir("Macros")  # fileNames is a list that will contain all the names of the files that are in the Macros folder
            for fileName in fileNames:
                if txtFile in fileName:
                    self.number_of_folder += 1
            print(str(self.number_of_folder))
            self.txtFile = f"Macros/{txtFile}{self.number_of_folder}.txt" if self.number_of_folder > 0 else f"Macros/{txtFile}.txt"
            open(self.txtFile, "a").close()                                 #/Creating the folder with the given name in the Label


        #Keyboard related stuff

    def key_pressed(self, key=None, milisecunde=0):
        """
        Puts all the keys that are pressed in the key list as a Keys object
        :param key: The Key that was pressed
        :param milisecunde: The time(current milisecond) when the key was pressed
        :return: nan
        """
        if str(key) != self.stop_key and str(key) != self.pause_resume_key:
            for k in reversed(self.keyList):
                if k.name == key and k.time_when_released == 0:
                    return
            self.keyList.append(Keys(key, milisecunde))
            print("A fost apasata tasta " + str(key) + " la milisecunda " + str(milisecunde))

    def key_released(self, key=None, milisecunde=0):
        """
        Looks in the key list for the object with the same name that wasn't released,then it sets it's ".time_when_released"
        :param key: The key that was released
        :param milisecunde: The time when the key was released
        :return: nan
        """
        for k in reversed(self.keyList):
            if k.name == key and k.time_when_released == 0:
                k.set_released_time(milisecunde)
                print("A fost lasata tasta " + str(key) + " la milisecunda " + str(milisecunde))
                break


    #/Keyboard related stuff

    #Mouse related stuff

    def mouse_pressed(self,x=0,y=0,button=None,time_when_pressed=0):
        """Adds the mouse event to the mouse list as a Mouse class object"""
        print("a fost apasat butonul MOUSE ULUI " + str(button) + " la milisecunda " + str(time_when_pressed))
        for m in reversed(self.mouse_list):
            if m.button == button and m.time_when_released == 0:
                return
        self.mouse_list.append(Mouse(button,time_when_pressed,x,y))

    def mouse_moved(self,x=0,y=0,milisecond=0):
        """Adds the mouse event to the mouse buffer list"""
        print("Mouse ul s a miscat la coordonatele " + str(x) + " " + str(y) + " la milisecunda " + str(milisecond))
        self.mouse_buffer.append("mouse_move" + ":" + str(milisecond) + ":" + str(x) + ":" + str(y) + "\n")

    def mouse_released(self,x=0,y=0,button=None,time_when_released=0):
        """Updates the button from the mouse list with the coordinates and the time when it was released"""
        print("a fost lasat butonul MOUSE ULUI " + str(button) + " la milisecunda " + str(time_when_released) + "la coordonatele " + str(x) + " " + str(y))
        for m in reversed(self.mouse_list):
            if m.button == button and m.time_when_released == 0:
                m.released(time_when_released,x,y)

    #/Mouse related stuff

    def write_to_file(self):
        """Arranges the events by the time when they were done and then writes all of them to the macro file"""
        evenimente = []
        for event in self.mouse_list:
            evenimente.append(("mouse_click" , event.time_when_pressed , event))
        for event in self.keyList:
            evenimente.append(("key" , event.time_when_pressed , event))
        for event in self.mouse_buffer:
            evenimente.append(("mouse_move" , int(event.split(":")[1]) , event))

        evenimente.sort(key = lambda x : x[1])

        for event in evenimente:
            with open(self.txtFile,"a") as file:
                if event[0] == "mouse_click":
                    file.write(event[2].mouse_file_format())
                elif event[0] == "mouse_move":
                    file.write(event[2])
                elif event[0] == "key":
                    file.write(event[2].key_file_format())
            pass

    def clear(self):
        """
         Resets every object within the object instance
        """
        self.write_to_file()
        self.keyList.clear()
        self.mouse_list.clear()
        self.number_of_folder += 1
        self.txtFile           = f"Macros/Macro{self.number_of_folder + 1}.txt"






class Play:
    """Plays the recording that was selected in the ListBox from the UI.py \n
       The way this works is by holding the key from the .txt file for the time it says in the file"""
    def __init__(self,file = ""):
        self.timer       = QTimer()             #
        self.timer.timeout.connect(self.tick)   #   Initializes everything for the timer
        self.m_controller = mouse_controller        #
        self.k_controller = keyboard_controller     #   Controllers for the pressing and moving for both keys and the mouse
        self.milisecunde = 0
        self.file = f"Macros/{file}"    # File that was selected in the UI.py ListBox
        self.key_list = []  # List with all the instructions from the file
        self.fill_list(self.file)       #fills the list with all the instructions from the file
        self.indice = 0     # the current instruction that should be done by the program
        self.timer.start(1) # Starts the timer

    def tick(self):
        self.milisecunde += 1
        self.play()


    def play(self):
        """Verifies the name and if an action should be done"""
        current_object = []
        current_object = self.key_list[self.indice].split(":")

        if current_object[0] == "keyboard":
            if self.milisecunde == int(current_object[2]):
                print("keyboard")
                key = self.convert_to_key(current_object[1])
                t = threading.Thread(target=self.k_press,args=(key,
                                                               int(current_object[3]) - int(current_object[2])))
                t.start()           # creates a thread so that other keys cand be pressed in paralel
                print(str(self.indice)) # number of the current instruction
                if self.indice < len(self.key_list) - 1:
                    self.indice = self.indice + 1                   #if the index of the current instruction equals to the index of the last instruction in the file, the index will go back to 0,thus making a loop
                else:
                    t.join()
                    self.indice = 0
                    self.milisecunde = 0
                    print("AM TERMINAT!!!!")

        elif current_object[0] == "mouse_move":
            if self.milisecunde == int(current_object[1]):
                print("mouse_move")
                dx = int(current_object[2]) - self.m_controller().position[0]   # sets the distance that the mouse should go on the x axis by subtracting the position from the file with the current x position of the mouse
                dy = int(current_object[3]) - self.m_controller().position[1]   # sets the distance that the mouse should go on the y axis by subtracting the position from the file with the current y position of the mouse
                t = threading.Thread(target=self.m_move, args=(dx,  # Move the mouse to the position
                                                               dy))
                t.start()
                print(str(self.indice)) # number of the current instruction
                if self.indice < len(self.key_list) - 1:
                    self.indice = self.indice + 1                   #if the index of the current instruction equals to the index of the last instruction in the file, the index will go back to 0,thus making a loop
                else:
                    self.indice = 0
                    self.milisecunde = 0
        elif current_object[0] == "mouse_click":
            if self.milisecunde == int(current_object[2]):
                print("mouse_click")
                #print(current_object[1])
                button = getattr(Button,current_object[1].split(".")[1])            # getting the button atribute from the string in the file
                dx = int(current_object[3]) - self.m_controller().position[0]       # sets the distance that the mouse should go on the x axis by subtracting the position from the file with the current position of the mouse
                dy = int(current_object[4]) - self.m_controller().position[1]       # sets the distance that the mouse should go on the y axis by subtracting the position from the file with the current position of the mouse
                t_move = threading.Thread(target=self.m_move, args=(dx,
                                                                    dy))
                t_move.start()  #Creates a thread for repositioning the mouse for the pressing of the respective button
                t_move.join()   #"Pauses" the program so that the button is not pressed while the cursor is being "moved"(the position before it was moved)
                t = threading.Thread(target=self.m_press,args=(button ,
                                                               int(current_object[5]) - int(current_object[2])))            # creates a thread where the mouse button will be pressed(the thread will run in paralel with the program and other threads that may be active or activated in the future)
                t.start()
                print(str(self.indice)) # number of the current instruction
                if self.indice < len(self.key_list) - 1:
                    self.indice = self.indice + 1                   #if the index of the current instruction equals to the index of the last instruction in the file, the index will go back to 0,thus making a loop
                else:
                    t.join()
                    self.indice = 0
                    self.milisecunde = 0

    def convert_to_key(self,key_name = ""):
        """Converts the given string to a Key object"""
        key_name = key_name.strip("'\"") # Strips all the quotation marks
        if key_name[0] == "K":      #this condition might seem strange but if the first letter is a K then the string should look like "Key." so I know that whatever is after the dot is what I'm searching for
            return getattr(Key,key_name.split(".")[1])
        return key_name             #this variant exists because the pynput.keyboard also accepts simple letters like 'a' or 'k',and the

    def fill_list(self,file_name = ""):
        """Fills the list with all the instructions from the file_name"""
        with open(file_name,"r") as reader:
            for line in reader:
                self.key_list.append(line.split("\n")[0]) if line != "" else None       #if it isn't the end of the file it will append the instruction to the list
            print("Am umplut lista aceasta are lungimea de " + str(len(self.key_list)))
        return

    def k_press(self,key,timelapse=0):
        """This will be called as a thread and will press the key for the given timelapse"""
        print("numele meu este thread ul " + str(threading.current_thread()))
        k_controller = keyboard_controller()
        k_controller.press(key)
        print("Am apasat tasta " + str(key) + " la milisecunda " + str(self.milisecunde))

        time.sleep(timelapse / 1000)

        k_controller.release(key)
        print("Am lasat tasta " + str(key) + " la milisecunda " + str(self.milisecunde))



    def m_press(self, button, timelapse=0):
        """This will be called as a thread and will press the button for the given timelapse"""
        print("numele meu este thread ul " + str(threading.current_thread()))
        m_controller = mouse_controller()
        m_controller.press(button)

        print("Am apasat butonul " + str(button) + " la milisecunda " + str(self.milisecunde))

        time.sleep(timelapse / 1000)

        m_controller.release(button)
        print("Am lasat butonul " + str(button) + " la milisecunda " + str(self.milisecunde))

    def m_move(self,x=0,y=0):
        """This will be called as a thread and will move the mouse by x points on the x axis and y points on the y axis"""
        print("numele meu este thread ul " + str(threading.current_thread()))
        try:
            m_controller = mouse_controller()
            m_controller.move(x,y)
        except Exception as exec:
            print(exec)
        print(f"Am mutat mouse ul cu {x} pixeli pe orizontala si cu {y} pe verticala")

    def clear(self):
        """Clears all the variables from the current instance of the class(this is necesarry only if u want to)"""
        self.timer.stop()
        self.indice = 0
        self.key_list.clear()
        self.file = ""
        self.milisecunde = 0


