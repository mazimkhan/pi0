copy service
sudo cp autonomous.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable autonomous.service
sudo systemctl start autonomous.service
