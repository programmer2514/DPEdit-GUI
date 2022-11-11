#NoTrayIcon

If Not FileExist("bin")
    FileCreateDir, bin

SetWorkingDir, bin

GoSub RunApp
ExitApp

RunApp:
    Try {
        If Not FileExist("dpedit_gui.py") {
            UrlDownloadToFile, https://raw.githubusercontent.com/programmer2514/DPEdit-GUI/main/dpedit_gui.py, dpedit_gui.py
            UrlDownloadToFile, https://raw.githubusercontent.com/programmer2514/DPEdit-GUI/main/dpedit.ico, dpedit.ico
            
            RunWait, pyw -3 -m pip install requests,, UseErrorLevel
        }
        
        RunWait, pyw -3 dpedit_gui.py,, UseErrorLevel
        
        If Not FileExist("run")
            Throw Exception("Run failed!")
        
    } Catch {
        MsgBox, 0x34, Warning, Python 3 installation not detected!`nWould you like DPEdit-GUI to download and install it now?
        IfMsgBox No
            MsgBox, 0x10, Error, Failed to launch DPEdit!`n`nAre you sure Python 3 and the py launcher are installed and added to PATH?`n`nIf this issue persists, try uninstalling "Python Launcher" and "Python 3.x.x" and running the Python installer again.`n`nMake sure to select both "Use admin privileges when installing py.exe" and "Add python.exe to PATH" when reinstalling.
        
        IfMsgBox Yes
        {
            UrlDownloadToFile, https://www.python.org/downloads/, pyver.tmp
            FileRead, rawData, pyver.tmp

            Loop, Parse, rawData, `n
            {
                If RegExMatch(A_LoopField, "<a class=""button"" href=""(.+)\.exe"">Download Python [.0-9]+<\/a>")
                    RegExMatch(A_LoopField, "<a class=""button"" href="".+\.exe"">Download Python [.0-9]+<\/a>", foundLine)
            }

            RegExMatch(foundLine, "https:.+exe", downloadURL)

            SetTimer, InstallPython, -1000
            MsgBox,, Installing, Installing Python 3...

            FileDelete, pyver.tmp
            FileDelete, python-setup.exe
            
            GoSub RunApp
        }
    }
Return

InstallPython:
    Try {
        UrlDownloadToFile, %downloadURL%, python-setup.exe
        RunWait, python-setup.exe /quiet,, UseErrorLevel
        WinClose, Installing ahk_class #32770
        MsgBox,, Success, Python 3 installed successfully!
    } Catch {
        MsgBox, 0x10, Error, Failed to install Python 3!
    }
Return
