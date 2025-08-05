import os
import threading

from PyQt6.QtGui import QTextFrame
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse

from Macro import Record,Keys,Play

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox, QWidget, QLayout, QVBoxLayout, \
    QBoxLayout, QLabel, QListWidget, QLineEdit
from PyQt6.QtCore import QTimer,pyqtSignal



class Macro_UI(QWidget) :
    """Creates a window containing a ListBox with all the recordings and Buttons for playing or recording"""

    #Signals for the buttons
    startRecordingSignal = pyqtSignal()
    stop_signal = pyqtSignal()
    play_signal = pyqtSignal()
    pause_signal = pyqtSignal()
    resume_signal = pyqtSignal()

    def __init__ (self) :
        super().__init__()
        #Declaring everything that's important for the key recording
        self.start_recording_key        = "Key.f7"
        self.start_play_key             = "Key.f8"
        self.pause_resume_key           = "Key.f9"
        self.stop_key                   = "Key.f10"
        self.pause_key_pressed          = False     # this is used to know if the program will be paused or resumed when it is running
        self.recording                  = None      # the recording class instance
        self.play_instance              = None      # the playing class instance
        self.milisecunde                = 0         # the miliseconds,this is just cosmetic
        self.timer                      = QTimer()  # updates the milisecond
        self.mouse_is_pressed           = False     # this is used to know if the mouse moves should be stored(True) or not(False)
        self.option                     = False     # True for recording     False for playing
        self.listener                   = pynput_keyboard.Listener(
                                                                    on_release= self.release_verifier
                                                                  )
        self.listener.start()

        #Declaring stuff that's important for the playing of the Macro
        self.current_file = ""

        self.timer.timeout.connect(self.timer_tick)

        #Connecting the listeners threads to the Main thread
        self.startRecordingSignal.connect(self.recordPushed)
        self.stop_signal.connect(self.stopPushed)
        self.play_signal.connect(self.play_start)
        self.pause_signal.connect(self.pause_pushed)
        self.resume_signal.connect(self.resume_pushed)

        #Sets the title , location , width and height for the window
        self.setGeometry(660, 280, 600, 600)
        self.setWindowTitle("MacroProgram")

        self.layout = QVBoxLayout() #Initiates the layout for the window

        #This label will show the value of self.milisecunde
        self.label  = QLabel()
        self.label.setGeometry(50,260,200,50)
        self.layout.addWidget(self.label)

        #Ads the list with all the macro files
        self.list = QListWidget()
        fileNames = os.listdir("Macros")
        self.list.addItems(fileNames)
        self.list.currentItemChanged.connect(self.current_file_changed)
        self.layout.addWidget(self.list)

        #Ads a text box for the naming of the macro file
        self.tbox = QLineEdit()
        self.layout.addWidget(self.tbox)

        #Creating the buttons
        self.recordButton = QPushButton("Record", self,clicked= self.recordPushed)
        self.recordButton.setGeometry(50, 50, 200, 50)
        self.layout.addWidget(self.recordButton)

        self.stopButton   = QPushButton("Stop", self,clicked= self.stopPushed)
        self.stopButton.setEnabled(False)
        self.stopButton.setGeometry(50, 120, 200, 50)
        self.layout.addWidget(self.stopButton)

        self.playButton   = QPushButton("Play", self,clicked= self.play_start)
        self.playButton.setGeometry(50, 190, 200, 50)
        self.layout.addWidget(self.playButton)

        self.helpButton   = QPushButton("Help", self,clicked= self.helpPushed)
        self.helpButton.setGeometry(50, 260, 200, 50)
        self.layout.addWidget(self.helpButton)
        #/Creating the buttons

        self.setLayout(self.layout) #sets the layout
        self.show() #opening the window



    def helpPushed(self):
        """Opens a MessageBox containing info for most of the stuff, such ass:\n
            - Start Key
            - Stop  Key
            - Resumes what every button does"""
        msg = QMessageBox()
        msg.setWindowTitle("Help")
        msg.setText("Type the name of the macro file you want to record in the textbox between the list and the Record button\n"
                    "The Play and Record Buttons will change to Pause after being pressed,then to Resume and so on \n"
                    "The stop button will safely close all the instances of Recording or Playing by clearing all the variables and timers first\n"
                    f"The start key for recording is {self.start_recording_key} \n"
                    f"The start key for playing is {self.start_play_key} \n"
                    f"The pause key for both pausing and resuming the macro is {self.pause_resume_key}\n"
                    f"The stop key for both recording and playing is  {self.stop_key} \n"
                   )
        msg.exec()


    def pause_pushed(self):
        """Pauses the program"""
        if self.timer.isActive():   #if the timer is running it will be stopped
            self.timer.stop()

        if self.option == False:        #Pausing behaviour for playing
            self.playButton.setText("Resume")
            self.playButton.clicked.disconnect(self.pause_pushed)
            self.playButton.clicked.connect(self.resume_pushed)
            self.play_instance.timer.stop()
        else:
            if self.listener.is_alive() and self.mouselistener.is_alive(): #Pausing behaviour for recording
                self.listener.stop()
                self.mouselistener.stop()
            self.recordButton.setText("Resume")
            self.recordButton.clicked.disconnect(self.pause_pushed)
            self.recordButton.clicked.connect(self.resume_pushed)

        self.layout.update() #updates the layout

        self.pause_key_pressed = True  #this boolean is used for knowing if the program is paused or running

    def resume_pushed(self):
        """Resumes the program from where it remained"""
        self.timer.start(1)

        if self.option == False:    #Resuming behaviour for playing
            self.playButton.setText("Pause")
            self.playButton.clicked.disconnect(self.resume_pushed)
            self.playButton.clicked.connect(self.pause_pushed)
            self.play_instance.timer.start(1)
        else:
            self.listener = pynput_keyboard.Listener( #Resuming behaviour for recording
                on_press=self.press_verifier,
                on_release=self.release_verifier
            )                                         #Sets the on_press and on_release functions for the keyboard listener
            self.listener.start()
            self.mouselistener = pynput_mouse.Listener(
                on_move=self.mouse_moving,
                on_click=self.mouse_press
            )                                         #Sets the on_move and on_click functions for the mouse listener
            self.mouselistener.start()

            self.recordButton.setText("Pause")
            self.recordButton.clicked.disconnect(self.resume_pushed)
            self.recordButton.clicked.connect(self.pause_pushed)

        self.layout.update() #updates the layout

        self.pause_key_pressed = False


    def stopPushed(self):
        """Stops the record timer"""
        self.timer.stop()
        self.milisecunde = 0
        self.label.setText("0")

        if self.option:
            self.stop_for_record()
        else:
            self.stop_for_play()

        self.option = False
        self.layout.update()

    def release_verifier(self, key):
        """Verifies what action should be done"""
        if str(key) == self.start_recording_key and self.recordButton.isEnabled():
            self.startRecordingSignal.emit()                                                # starts the Recording by emmiting the signal from the listener's thread to the main one
        elif str(key) == self.stop_key and self.stopButton.isEnabled():
            self.stop_signal.emit()                                                         # stops the Recording or the Playing by emmiting a signal the listener's thread to the main one
        elif str(key) == self.start_play_key and self.playButton.isEnabled():
            self.play_signal.emit()                                                         # starts the Recording by emmiting the signal from the listener's thread to the main one
        elif str(key) == self.pause_resume_key and not self.pause_key_pressed:
            self.pause_signal.emit()                                                        # pauses the program if the button is pressed
        elif str(key) == self.pause_resume_key and self.pause_key_pressed:
            self.resume_signal.emit()                                                       # resumes the program if it is paused
        elif self.milisecunde > 0 and self.option:
            self.recording.key_released(key, self.milisecunde)                              # gives the key that was pressed and the time when it was pressed if the recording is enabled to the Record class


    #Record stuff

    def recordPushed(self):
        """Starts the recording of the keys"""
        self.option        = True
        self.stopButton.setEnabled(True)
        self.playButton.setEnabled(False)
        self.recordButton.setText("Pause")                      #   updates the record button for the pause button behaviour
        self.recordButton.clicked.disconnect(self.recordPushed) #
        self.recordButton.clicked.connect(self.pause_pushed)    #
        self.layout.update()
        if self.recording == None:                                                                          # sees if the recording variable exists
            self.recording          = Record(self.tbox.text(),self.stop_key,self.pause_resume_key)          # if it doesn't exist it initializes the Record class from the Macro.py
        else:
            self.recording.create_file(self.tbox.text())                                                    # if it exists then it will change the name of the file where the instructions will be written

        if self.listener.is_alive():                                                            #
            self.listener.stop()                                                                #
        self.listener      = pynput_keyboard.Listener(                                          #
                                                        on_press  = self.press_verifier,        #   Resets the behaviour for the listener
                                                        on_release= self.release_verifier       #
                                                     )                                          #
        self.mouselistener = pynput_mouse.Listener(                                 #
                                                    on_move=self.mouse_moving,      #
                                                    on_click = self.mouse_press     #   Initializes the mouse listener for mouse activities !!Doesn't include the scrolling
                                                  )                                 #
        self.mouselistener.start()  #
        self.listener.start()       # Starts the listeners
        self.timer.start(1)
        print("The recording of the keyboard has started")

    def timer_tick(self):
        """Is runned trough every tick and updates the current millisecond"""
        self.milisecunde += 1
        self.label.setText(str(self.milisecunde))
        self.layout.update()

    #Mouse Stuff
    def mouse_press(self,x,y,button,pressed,injected):
        if       pressed:
                self.recording.mouse_pressed(x,y,button,self.milisecunde)   # Sends the button that was pressed with the coordinates of the mouse and the current time
                self.mouse_is_pressed = True
        elif not pressed:
                self.recording.mouse_released(x,y,button,self.milisecunde)  # Sends the button that was released with the coordinates of the mouse and the current time
                self.mouse_is_pressed = False

    def mouse_moving(self,x,y):
        if self.mouse_is_pressed:                      # If the mouse is pressed then the moving behaviour is sent (coordinates to where it was moved and the current time)
            self.recording.mouse_moved(x,y,self.milisecunde)
    #/Mouse Stuff

    #Keyboard Stuff
    def press_verifier(self,key):
        """Verifies if the key that was pressed isn't related to any button"""
        if not (key == self.stop_key or key == self.start_recording_key or key == self.start_play_key or key == self.pause_resume_key) and self.milisecunde > 0:
            self.recording.key_pressed(key,self.milisecunde)


    def stop_for_record(self):
        """Safely clears all the things that the Record class needed and puts the program in a neutral state"""
        print("The recording of the keyboard has stopped")
        if self.listener.is_alive() and self.mouselistener.is_alive():
            self.listener.stop()
            self.mouselistener.stop()
        self.listener = pynput_keyboard.Listener(                                   #
                                                 on_release=self.release_verifier   # Puts the listener in a neutral state
                                                )                                   #
        self.listener.start()
        self.recordButton.setText("Record")
        try:
            self.recordButton.clicked.disconnect(self.pause_pushed)
        except TypeError:
            pass

        try:
            self.recordButton.clicked.disconnect(self.resume_pushed)
        except TypeError:
            pass
        self.list.clear()       #Clears the list so there are no duplicate macro files
        self.list.addItems(os.listdir("Macros"))    # Updates the ListBox with the newly made macro file
        self.recordButton.clicked.connect(self.recordPushed)
        self.recording.clear()                 #Clears everything that was used inside the Record class
        self.playButton.setEnabled(True)    #
        self.stopButton.setEnabled(False)   #   Neutral state
        #/Keyboard Stuff

    #/Record stuff

    #Play stuff

    def play_start(self):
        if self.current_file != "":
            if self.play_instance == None:  #verifies if the play_instance was initialized      if not it initializes it else it remains the same
                self.play_instance = Play(self.current_file)
            else:
                self.play_instance.fill_list("Macros/" + self.current_file)
                self.play_instance.timer.start(1)
            self.timer.start(1)
            self.stopButton.setEnabled(True)
            self.recordButton.setEnabled(False)
            self.playButton.setText("Pause")                        #
            self.playButton.clicked.disconnect(self.play_start)     #   Sets the behaviour for the Pause button
            self.playButton.clicked.connect(self.pause_pushed)      #
            self.layout.update()
            print("The Macro has started")
        else:       #if the there was no file selected then raises an error message
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Please select one of the files that are in the list")
            msg.exec()

    def current_file_changed(self,current,previous):
        if current:
            self.current_file = current.text()

    def stop_for_play(self):
        """Safely clears all the things that the Play class needed and puts the program in a neutral state"""
        self.recordButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.playButton.setText("Play")
        try:
            self.playButton.clicked.disconnect(self.pause_pushed)
        except TypeError:
            pass

        try:
            self.playButton.clicked.disconnect(self.resume_pushed)
        except TypeError:
            pass
        self.playButton.clicked.connect(self.play_start)
        self.play_instance.clear()      #Clears all the things that were used inside the Play class

    #/Play stuff

