# English to Simple English Wikipedia

## Install
To start the programm Docker is required.

Build the containers with `docker-compose build`. 
Start them by typing `docker-compose up`.
Navigate to http://localhost via your favorite web browser.

## Usage

When you first open the tool you will see a search bar. Type in any topic you want annotate sentences for.
![Searchbar Demo](gif/search-bar.gif)

After you confirm your search you will get a list with all the topics related to your search term. The tool only shows topics that are available in _English_ __and__ _Simple English_. Click on the one you are interested in. 
![List Demo](gif/list.gif)

Now you can select any sentence in the _English_ article (left side). The tool automatically matches your selected sentence based on semantic similarity to one or more sentence(s) in the _Simple English_ article. Now you can either rate the matched sentence with the slider on the left side (0 - 3) or manually select/deselect sentences in the _Simple English_ article. By clicking the ___Rate___ button under the slider you create a new entry in the database. An entry consists of the user score, algorithm score and the sentence pair. You can change between the three algorithms in the top left corner via the dropdown menu.
![Main Demo](gif/main.gif)

## Connecting to the Database

The database can be accessed via Adminer http://localhost:8080 - just navigate to this adress in your web browser.
Per default the server name is `db` and username and passwort are both `root`. You can find your annotations in the `matchings_wiki` database.

If you want to connect to the database via an external tool you can do it with the following adress: http://localhost:3308

## Known Errors
If you encounter this error: 
`ERROR: Service 'flask' failed to build: The command '/bin/sh -c pip install -r requirements.txt' returned a non-zero code: 137`
then you have to allocate more RAM to Docker.
