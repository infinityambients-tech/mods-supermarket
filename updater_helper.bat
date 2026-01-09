@echo off
setlocal
set LOG_FILE=c:\Users\igorz\OneDrive\1251019185526-Desktop\Desktop\MODS TO SUPERMARKET\Money_mods\logs\updater_log.txt
echo [%DATE% %TIME%] --- BATCH UPDATE STARTED --- >> "%LOG_FILE%"
echo [%DATE% %TIME%] Launching finalizer... >> "%LOG_FILE%"
"c:\Users\igorz\AppData\Local\Programs\Python\Python313\python.exe" "c:/Users/igorz/OneDrive/1251019185526-Desktop/Desktop/MODS TO SUPERMARKET/Money_mods/finalize_update.py" --pid 17056 --content_dir "c:\Users\igorz\OneDrive\1251019185526-Desktop\Desktop\MODS TO SUPERMARKET\Money_mods" --lock_file "c:\Users\igorz\OneDrive\1251019185526-Desktop\Desktop\MODS TO SUPERMARKET\Money_mods\update.lock" --update_id "7ce30900-60f6-4a91-96d6-21b4aa81f2f6" --log "c:\Users\igorz\OneDrive\1251019185526-Desktop\Desktop\MODS TO SUPERMARKET\Money_mods\logs\updater_log.txt"
echo [%DATE% %TIME%] Finalizer executed. >> "%LOG_FILE%"
echo [%DATE% %TIME%] Restarting application... >> "%LOG_FILE%"
start "" "c:\Users\igorz\AppData\Local\Programs\Python\Python313\python.exe" money_mods.py >> "%LOG_FILE%" 2>&1
echo [%DATE% %TIME%] Update completed. >> "%LOG_FILE%"
del "%~f0"
