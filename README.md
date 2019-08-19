# wiki-en-to-simple


Um das Programm zu starten muss Docker installiert sein. 

Die Container werden mit `docker-compose build` gebuildet, dies kann eine Weile dauern. 
Danach können diese mit `docker-compose up` gestartet werden.
Jetzt kann über http://localhost darauf zugegriffen werden.

Falls beim build process der Fehler: 
`ERROR: Service 'flask' failed to build: The command '/bin/sh -c pip install -r requirements.txt' returned a non-zero code: 137`
kommt, dann sollte Docker mehr RAM zur Verfügung gestellt werden.

Falls alles richtig gestartet ist und das Programm läuft, dann kann mit Hilfe von Admire über http://localhost:8080 zugegriffen werden.
Per default hat der Server den Namen `db`. Username und Passwort sind beides `root`. Das `Datenbank` Feld kann freigelassen werden. Anschließend findet man in der `matchings_wiki` Datenbank alle Matches, Scores und Benutzerbewertungen.

Falls man sich mit einem Tool außerhalb von Docker auf die MySQL Datenbank connecten möchte, dann erfolgt dies über http://localhost:3308
