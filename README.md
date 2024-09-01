1. Create & activate the python virtual-environment (The `python3-venv` dependency may be required, see: <https://docs.python.org/3/library/venv.html> for more details.)

```
python3 -m venv venv
source venv/bin/activate
```

2. Install the dependencies. If errors occur, try removing the version numbers in the requirements.txt.

```
pip install -r requirements.txt
```

3. Edit Gemini.py in text editor of your choice and replace YOUR_API_KEY with the API key from https://aistudio.google.com

4. Replace the model_name field with a valid language model to use. See https://ai.google.dev/gemini-api/docs/models/gemini

5. Launch the Gemini app.

```
python3 gemini.py
```

6. Usage:

Type "Hello" and the model should respond.

Type voice mode and you can chat with the language model with your voice.

Say "Exit Mode" and the voice mode should exit. Type "Exit Mode" to leave the chat.

