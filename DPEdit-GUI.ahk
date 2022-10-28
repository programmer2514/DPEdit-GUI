if not FileExist("bin")
    FileCreateDir, bin

SetWorkingDir, bin

if not FileExist("dpedit_gui.py") {
    UrlDownloadToFile, https://raw.githubusercontent.com/programmer2514/DPEdit-GUI/main/dpedit_gui.py, dpedit_gui.py
    UrlDownloadToFile, https://raw.githubusercontent.com/programmer2514/DPEdit-GUI/main/dpedit.ico, dpedit.ico
}

try {
    RunWait, pyw -3 dpedit_gui.py
} catch e {
    MsgBox, % e.Message
}