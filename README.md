# The Armoire

The Armoire is a project that displays fit clothing using AI.

## Setup

Make sure you are in the project folder.

Optional: Make sure your virtual environment is activated. Then type the following command to install the required modules:

```bash
pip3 install -r requirements.txt
```

Get API keys from [SerpAPI](https://serpapi.com) and [OpenWeather](https://openweathermap.org). The free tier should be enough. Then, make an environment file:

```bash
touch .env && open .env
```

In your .env file:
```
serpapi_key={your SerpAPI key}
openweather_key={your OpenWeatherMap key}
```

Occasionally, updates may change how tables are stored in armoire.db. In case the project stops working appropriately, delete armoire.db. When the program is run next time, a new database file will appear. Just make sure you don't mind deleting information such as login information, shopping carts, and the wardrobe.

## Usage

In the project folder, type the following to start the program (or run app.py in some other manner):

```bash
python3 app.py
```

Click on the localhost link that appears in the terminal.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change or fix.
