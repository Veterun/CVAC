import Tkinter as tk
import sys
import os
import subprocess
import inspect

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.root = master
        self.grid()
        label = tk.Label(self, text = "EasyCV requires numpy")
        label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        label = tk.Label(self, text = "Install numpy?")
        label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        f = tk.Frame(self, pady=5)
        f.grid(row=2)
        okbutton = tk.Button(f, text="Yes", bg="light blue", width=6,
                           command=self.runOK)
        okbutton.grid(row=0, column=0, padx=5, pady=5)
        quitbutton = tk.Button(f, text="No", bg="light blue", width=6,
                           command=self.quit)
        quitbutton.grid(row=0, column=1, padx=5, pady=5)
        plabel = tk.Label(self, text = "Enter password to install.")
        plabel.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.passwrd = tk.Entry(self, bd = 3, show="*")
        self.passwrd.grid(row=4, column=0, padx=5, pady=5, sticky="w")

    def runOK(self):
        # Determine path to 3rdparty directory
        scriptfname = inspect.getfile(inspect.currentframe())
        scriptpath  = os.path.dirname(os.path.abspath( scriptfname ))
        installpath = os.path.abspath(scriptpath+'/../Resources')
        # since virtualenv ships with a pip that does not understand
        # wheels we have to upgrade it.  We can change this
        # by starting virtualenv with --extra-search and path to new pip
        # But for now lets just upgrade on the fly
        activate_this = installpath + '/virt/bin/activate_this.py'
        execfile(activate_this, dict(__file__=activate_this))
        #subprocess.call(['pip', 'install', '--upgrade', 'pip'])
        #subprocess.call(['pip', 'install', 'wheel'])
        # now install numpy
        numpystr = '/3rdparty/numpy-1.8.1-cp27-none-any.whl'
        subprocess.call(['pip', 'install', installpath + numpystr])
        self.root.destroy()

def testInstall():
    scriptfname = inspect.getfile(inspect.currentframe())
    scriptpath  = os.path.dirname(os.path.abspath( scriptfname ))
    installpath = os.path.abspath(scriptpath+'/../Resources')
    if os.path.exists(installpath+'/virt/lib/python2.7/site-packages/numpy'):
        return True
    else:
        return False
    #sys.path.insert(1,installpath+'/virt/lib/python2.7/site-packages')
    #try:
    #    print ("Trying to import numpy")
    #    print ("Using python " + sys.executable)
    #    import numpy
    #    print ("numpy imported")
    #    return True
    #except ImportError as ex:
    #    print ("numpy needs to be install")
    #    return False
    #return False

def doInstall(silent=False):
    root = tk.Tk()
    root.geometry('190x190+20+20')
    root.tk_setPalette(background='light grey')
    app = Application( master=root )
    app.master.title('EasyCV Install Python')
    if silent == True:
        app.runOK()
    else:
        app.mainloop()


if __name__ == '__main__' :
    if testInstall() == False:
        print("Installing numpy")
        doInstall(silent=True)

