systemctl --user disable container-binalerter.service
systemctl --user stop    container-binalerter.timer
systemctl --user disable container-binalerter.timer
systemctl --user start   container-binalerter.timer
