if not FileExist("bin")
    FileCreateDir, bin

SetWorkingDir, bin

try {
    if not FileExist("dpedit_gui.py") {
        UrlDownloadToFile, https://raw.githubusercontent.com/programmer2514/DPEdit-GUI/main/dpedit_gui.py, dpedit_gui.py
        UrlDownloadToFile, https://raw.githubusercontent.com/programmer2514/DPEdit-GUI/main/dpedit.ico, dpedit.ico
        
        RunWait, pyw -3 -m pip install requests,, UseErrorLevel
    }
    
    RunWait, pyw -3 dpedit_gui.py,, UseErrorLevel
    
    if not FileExist("run")
        Throw Exception("Run failed!")
    
} catch {
    MsgBox, 0x10, Error, Failed to launch DPEdit!`nAre you sure Python 3 is installed and added to PATH?
}