docker run -it --network host -d -e DMXIP='192.168.0.112' --log-opt max-size=10m --log-opt max-file=3 --restart unless-stopped --name wifidmx wifidmx-app
